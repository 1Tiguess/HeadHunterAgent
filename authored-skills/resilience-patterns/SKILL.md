---
name: resilience-patterns
description: Makes systems survive dependencies that are slow, absent or lying — explicit timeouts everywhere, retries that distinguish retryable from unknown, jittered backoff, retry budgets that stop amplification, bounded concurrency, circuit breakers, load shedding, ranked degradation, and checkpointed work that resumes instead of restarting. Use when building or reviewing anything that calls a network service, database, queue, subprocess or model API; when one slow dependency takes everything down; when retries are hammering a service; when a long job restarts from the beginning after a crash; when something hangs forever; or when choosing timeouts, backoff, circuit-breaker thresholds or rate limits.
allowed-tools: Read, Write, Edit, Glob, Grep, Bash
---

# Resilience patterns

Systems that work when every dependency is healthy are easy. This skill is about the other case.

## One question, asked nine times

Every technique here is a **bound**, and every bug is an **unbounded quantity**.

| Missing bound | What becomes unbounded |
|---|---|
| No timeout | Waiting |
| Retries without a budget | Amplification |
| Unbounded queue | Latency — worse than rejection, because the client gave up before you answered |
| No concurrency ceiling | Resource consumption |
| No progress timeout | Time a dead worker holds a job |
| No dead-letter path | Retry budget consumed by one poisoned item |

So the review question is never "does this retry?" It is:

> **What quantity here has no upper bound?**

Ask it of every outbound call, every subprocess, every lock acquisition, every polling loop. Most
resilience bugs answer it immediately.

## 1. Timeouts

**Set one on everything.** This is the most common omission and the most damaging.

With no deadline, resources are held for every in-flight request and each one drifts toward the
language default — which is usually "forever" or "two minutes", neither chosen by you. The failure
is not one slow call. It is the caller's connection pool, threads and memory consumed by requests
whose answers nobody is waiting for any more.

**Choosing the value.** Take the dependency's *successful-response* latency distribution, pick an
acceptable false-timeout rate, and read off the corresponding percentile. Successful responses only
— including failures in the distribution biases it toward the thing you are trying to cut off.

Then apply the constraint that matters more: **set the client's deadline where the answer stops
being useful to the client**, not where the server gives up. Those two points differ, and the
client's is smaller. A response that arrives after the user navigated away is not a success.

**A deadline is absolute; a timeout is a duration.** That single distinction is why deadlines
propagate across hops and durations do not — a duration silently resets the clock at every
boundary, so five hops of "30 seconds" is two and a half minutes.

Propagate the deadline. Each hop gets what is left, not a fresh allowance.

## 2. Retries

Three questions, in this order:

1. **Is this error retryable at all?**
2. **Is the operation safe to repeat?**
3. **Can I afford it?**

Most code answers only the first, and answers it wrong.

**Retryability is the error plus a known-safe operation — never the error alone.** A 503 on a
non-idempotent POST is not retryable just because 503 is in the retryable set.

**Classify ternary, not binary:** retryable / not-retryable / **unknown**. Unknown *defers* rather
than defaulting either way. Most hand-rolled retry code has no unknown state, which means it
silently retries everything it does not recognise — including the things that already succeeded.

Specifics worth stating outright:

- `connect-failure` **never reached the server** and is always safe to retry.
- **502, 503 and 504 are retryable. 500 usually is not** — a 500 generally means the server *did*
  process your request and failed doing it. Retrying re-runs the failure, and if the operation had
  side effects, re-runs those too.
- **409 is the one retryable 4xx.**
- A temporary DNS failure is retryable; **NXDOMAIN is not**.
- A **cancelled** request is not retryable. The caller already gave up.

**Backoff: exponential, capped, with jitter — always.**

And frame jitter correctly, because the usual framing hides its real scope: **jitter is about
desynchronisation, not about retries.** Any periodic action taken by many independent actors
synchronises unless you prevent it. So the same reasoning applies to cron schedules, cache
expiry, health checks, token refreshes and every polling probe. If a thousand clients all refresh
on the hour, you built a stampede without writing a single retry.

**The deadline spans all attempts.** Without this, "3 retries × 30 seconds" quietly becomes 120
seconds of user-visible latency. Give each attempt its own per-try timeout, strictly smaller than
the overall budget, and stop when the budget is spent regardless of attempts remaining.

## 3. Retry budgets

Three layers each retrying three times is **27 requests**, and no single layer did anything
unreasonable. This is why per-call attempt counts do not control amplification.

**Cap retries as a share of live traffic**, held as shared state. A token bucket is a counter and a
timestamp:

- debit the bucket on a retry
- credit it on a first-attempt success
- **stop retrying entirely below a threshold**

Now a dependency that is broadly failing stops receiving retries, because there are no successes
crediting the bucket. That is the behaviour you want and an attempt count cannot express it.

**Price a timeout-triggered retry higher than an ordinary one.** When you time out, the upstream
work is probably still running — so your retry is *additive* load, not replacement load. Charge it
more.

**Designate exactly one layer to retry at.** Every other layer fails fast. The budget and the
designated layer are two halves of one control; neither works alone.

## 4. Bounded concurrency — reach for this first

A ceiling on in-flight work per dependency, rejecting immediately once exceeded, **is a circuit
breaker** — with no state machine to misconfigure, no thresholds to tune, and no window to get
wrong. It fails fast and pushes backpressure to the earliest and cheapest point.

**Prefer it.** Most systems that need "a circuit breaker" actually need this.

Derive the limit from **Little's Law**:

```
limit ≈ average RPS × average latency
```

Or adapt it from measured latency, because **latency is the observable proxy for a forming queue**
and it moves before resources are exhausted. Rising latency at flat throughput means a queue is
building somewhere; that is your warning, and it arrives earlier than any error rate.

## 5. Failure-rate circuit breakers — the specialised tool

Reach for this when bounded concurrency is not enough. The shape is invariant even though the
numbers are not:

- a **failure ratio** over a sampling window
- gated by a **minimum throughput** — without it, a low-traffic dependency trips on two failures out
  of two requests
- **opens** for a break duration
- then **probes**

**One probe** recovers fast and is noisy. **Several probes** are slower but will not re-close on one
lucky request. Choose deliberately.

**Add a fourth state: manually isolated.** A human deciding to stop calling something is a
different fact from the breaker deciding it, and conflating them makes incidents worse — you cannot
tell whether the thing recovered or whether someone is holding it open on purpose.

Reference implementations disagree on the defaults. Use the reasoning, not a number:

- **break duration** scales with expected recovery time
- **trip threshold** scales with the collateral damage of a false trip
- **minimum-throughput gating** matters more the lower your traffic

`references/numbers.md` has the two reference defaults side by side.

## 6. Slow is not down

**A failure-rate breaker never trips on a dependency that answers everything, slowly.** Nothing
fails. The ratio stays at zero. Meanwhile the caller's concurrency drains and the real failure lands
on the caller, which looks like the caller's fault.

This needs its own signal:

- a **slow-call rate threshold** — calls over a latency bound counted as failures
- a **latency gradient** against a measured baseline
- or a heartbeat

And the second-order effect, which is easy to miss: **a timeout on a slow dependency converts a
latency problem into a load problem.** You abandon the request; the upstream work continues. Every
timeout you fire adds load to something already struggling. This is precisely why timeout-triggered
retries are priced higher.

## 7. Shedding and degradation

**Reject at the earliest, cheapest point.** A request rejected at the edge costs almost nothing; the
same request rejected after three service hops and a database query cost you everything except the
response.

**Prefer a scaled response to a binary one.** Interpolate between a *scaling* threshold and a
*saturation* threshold, so the system progressively tightens rather than flipping from fine to
refusing. Binary shedding oscillates; scaled shedding settles.

**Write the degradation plan before the incident**, as a ranked list:

- what is dropped **first**
- what is dropped **last**
- what is **never** dropped

Order by cost and by user value. Two rules cover most cases:

> **Degrade before refusing. When refusing, refuse the expensive things first.**

Recommendations, personalisation, analytics, prefetch and "people also liked" go early. Checkout and
authentication go never. Writing this list during an incident is how the wrong thing gets dropped.

## 8. Work already started

Long-running work needs **four distinct timeouts**, because they detect four different failures:

| Timeout | Detects |
|---|---|
| Queue wait | Work that will never start in time. **Must not be retryable** — retrying adds to the same backed-up queue |
| Single attempt | One bad execution |
| Whole thing, across attempts | Runaway total cost |
| **Gap between progress signals** | **A worker that died halfway through** |

Only the last one detects the dead worker. Nothing else will: the job is not queued, not failed, and
not finished.

**Make the progress signal carry the checkpoint.** The next attempt resumes from it. The checkpoint
rides on the liveness signal you already needed, so it costs nothing extra — and it converts "start
the six-hour job again" into "continue from item 40,000".

**Resumption must be idempotent.** Derive a stable key per item and check before acting. At-least-once
delivery is what every queue actually gives you; idempotency is what makes that acceptable.

**Dead letters.** A permanently-failing item needs somewhere to go, or it consumes retry budget
forever and starves everything behind it.

**Bulkheads.** Separate resource pools per dependency, so one sick dependency cannot consume the
pool serving the healthy ones. **For a modest application with a single shared connection pool,
this matters more than any circuit breaker** — the pool is the thing that actually fails.

## 9. Observing failure

**Do not record a retried-then-succeeded operation as an error.** The operation completed. Counting
it makes your error rate report failures no user experienced, and corrupts any error budget computed
from it. Record the retry; do not record a failure.

**Record the failure *class* as a low-cardinality field.** A class, never a message. This is the
difference between telemetry you can alert on and telemetry you can only read afterwards — an
unbounded label set is the same unbounded-quantity bug as a missing timeout, applied to your metrics
backend.

**Do not log the same exception at four layers.** Log it where it is handled, and carry context
upward rather than re-logging.

All of this works with plain structured logging. A tracing stack is a convenience, not a
prerequisite.

## 10. It is not only HTTP

The same bounds apply everywhere:

- subprocess → `timeout=`
- file lock and advisory lock → acquisition timeout
- database transaction → statement and lock timeouts
- model inference call → deadline and a retry classification
- polling loop → an iteration cap or a deadline

> **An unbounded `while` waiting on a condition is the same bug as a missing HTTP timeout.**

## Review checklist

- [ ] Every outbound call, subprocess, lock acquisition and polling loop has an explicit bound
- [ ] Retry classification is ternary, and 500 is treated differently from 503
- [ ] Backoff is jittered — and the jitter reasoning is applied to periodic work too
- [ ] Total time across all attempts is bounded independently of the attempt count
- [ ] Retries are capped as a share of traffic, and exactly one layer is designated to retry
- [ ] A dependency that is slow but not failing triggers a response
- [ ] A ranked degradation list exists before the incident
- [ ] A long job killed midway resumes from a checkpoint without duplicating work
- [ ] A permanently-failing item lands in a dead-letter path
- [ ] A retried-then-succeeded operation is not counted as an error

## References

- `references/retry-classification.md` — the ternary classifier and the full per-protocol taxonomy
- `references/numbers.md` — every concrete constant, attributed, with the reasoning that moves you
  within the range
- `references/patterns.md` — token bucket, breaker, bulkhead, checkpoint and dead-letter as small
  implementations in plain code, no framework
