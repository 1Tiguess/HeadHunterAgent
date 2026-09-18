# Observability for a data layer

## Contents
- [Instrument selection](#instrument-selection)
- [The cardinality budget](#the-cardinality-budget)
- [Delta versus cumulative](#delta-versus-cumulative)
- [A default metric set](#a-default-metric-set)
- [Alerting on symptoms](#alerting-on-symptoms)
- [What to log instead](#what-to-log-instead)

## Instrument selection

A decision tree, not a style preference. Picking wrong makes the data harder to consume downstream
and sometimes impossible to aggregate correctly.

| The value is... | Instrument |
|---|---|
| A count that only goes up | **Counter** |
| A count that goes up and down (queue depth, in-flight requests) | **UpDownCounter** |
| A timing, or anything you want percentiles from | **Histogram** |
| An absolute reading, non-additive (pool utilisation %) | **Asynchronous Gauge** |
| Additive and monotonic, read periodically | Asynchronous Counter |
| Additive, non-monotonic, read periodically | Asynchronous UpDownCounter |

**The common mistake is a Gauge where a Histogram belongs.** A gauge of "current query latency"
samples one value per collection interval and discards the distribution — you cannot recover a p99
from it, ever. Latency is always a histogram.

**The second mistake is a Counter for a quantity that can decrease.** A monotonic counter that goes
backwards produces a spurious wrap-around spike in every rate calculation over it.

## The cardinality budget

**Cardinality** is the number of unique attribute combinations reported for a metric. It is a hard
budget, not a soft concern.

The canonical worked example: a long-running service collecting metrics with **7 attributes, each
taking 30 values**, must eventually remember

```
30^7 = 21,870,000,000 combinations
```

Every one of which is state the SDK holds in memory.

**The default limit is 2,000 unique attribute combinations per metric stream.** Past it, data points
are dropped or combined — so exceeding the budget does not produce an error, it produces **quietly
wrong data**.

**Never put these on a metric:**

- user ID, account ID, tenant ID (unless the tenant count is small and fixed)
- a raw URL path containing IDs — template it: `/orders/{id}`, not `/orders/48213`
- an exception message
- a SQL statement
- a customer-supplied string of any kind

**Safe attributes** are bounded sets you control: operation name, table name, status class, error
*class*, pool name, database name.

> This is the same unbounded-quantity bug as a missing timeout, applied to your metrics backend.

## Delta versus cumulative

A memory decision, and the reason cardinality bites harder in some setups than others.

- **Delta** (synchronous instruments): the SDK tracks only what happened since the last export, then
  discards it. Bounded memory.
- **Cumulative** (asynchronous instruments): the SDK tracks everything since process start — *"in the
  worst case, the SDK will have to remember what has happened since the beginning of the process"*.
  This is what turns high cardinality into unbounded memory growth rather than merely noisy data.

If you are near a cardinality ceiling, delta temporality buys headroom. It does not fix a bad
attribute choice.

## A default metric set

The specifications define instruments and conventions; neither states what a backend should actually
emit. This is a defensible starting set.

**Database client:**

| Metric | Type | Attributes |
|---|---|---|
| `db.client.operation.duration` | Histogram | operation, table, status class |
| `db.client.connection.count` | UpDownCounter | pool name, state (idle/used) |
| `db.client.connection.max` | Gauge | pool name |
| connection acquisition wait | Histogram | pool name |

`db.client.operation.duration` is a **required** metric in the conventions, and *"when reported
alongside a database operation span, the metric value SHOULD be the same as the database operation
span duration."* Its specified explicit bucket boundaries:

```
[0.001, 0.005, 0.01, 0.05, 0.1, 0.5, 1, 5, 10]
```

**Use those boundaries.** Default exponential buckets put almost all database operations in one or
two buckets, which makes the percentiles meaningless.

*`db.client.connection.count` and `db.client.connection.max` were not stable at the time of writing;
`db.client.operation.duration` was. (Metric names here are search-extracted — the semantic-convention
files were not reachable directly.)*

**Connection pool** — the metrics that predict an outage rather than report one:

- **acquisition wait time** (histogram) — this rises *before* errors appear and is the single best
  early warning
- connections in use versus max
- acquisition timeouts (counter)

**Migrations:**

- duration per migration (histogram)
- lock wait time (histogram)
- **invalid index count** (gauge) — catches the `CONCURRENTLY` failure mode that otherwise leaves no
  trace

**Background jobs:**

- queue depth (UpDownCounter)
- **queue age of the oldest pending item** (gauge) — depth alone lies; a queue of 10 items where the
  oldest is 4 hours old is broken, and a queue of 10,000 draining in seconds is not
- execution duration (histogram)
- attempts, by terminal outcome (counter)
- dead-letter count (counter)

## Alerting on symptoms

The governing rule:

> **Alert on symptoms, have good consoles to allow pinpointing causes, and avoid having pages where
> there is nothing to do.**

Applied:

- **Page on latency at one point** in the stack, not several. A latency alert at each layer produces
  four pages for one incident and no extra information.
- **Alert on user-visible errors.** Suppress downstream failures unless they independently require
  intervention. A failing replica that the application routed around is a console line, not a page.
- **Allow slack for small blips.** An alert that fires on a single scrape is an alert people learn to
  ignore.
- **For batch jobs, page when the job "has not succeeded recently enough" to affect users**, with at
  least **two cycles** of buffer — 10 hours for a 4-hour job. Alerting on a single failed run pages
  for something that will self-heal on the next cycle.
- **Metamonitor.** Test the alerting pipeline end to end rather than the health of its components. An
  alerting system that is up but not delivering is indistinguishable from silence.

> Each alert should guide responders toward root cause; irrelevant alerts breed fatigue and erode
> trust in monitoring systems.

**For a data layer specifically, the symptom alerts worth having are:**

1. Request latency p99 above a threshold at the service edge
2. Error rate, user-visible errors only
3. Connection acquisition wait rising — the earliest signal available
4. Oldest pending job age
5. Replication lag, where reads go to replicas

**Not** worth paging on: individual slow queries, CPU, connection count on its own, cache hit rate,
or a single failed background job.

## What to log instead

Everything excluded from metrics by the cardinality budget belongs somewhere — usually structured
logs or spans, where high cardinality is fine.

- **The query** — on the span, or in a slow-query log, never as a metric label
- **User and tenant IDs** — span attributes, log fields
- **The exception message and stack** — logged once, **where it is handled**, not re-logged at each
  layer it passes through
- **The failure class** — this one goes on **both**: a low-cardinality class as a metric attribute so
  you can alert on it, and the full detail in the log so you can diagnose it

That split is the practical rule: **a bounded class on the metric, the unbounded detail in the log.**
