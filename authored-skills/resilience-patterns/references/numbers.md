# Concrete numbers, and what moves them

Every figure here is attributed. **Use the reasoning, not the number** — the reference
implementations disagree with each other, which is itself the most useful fact in this file.

## Contents
- [Circuit breaker defaults, side by side](#circuit-breaker-defaults-side-by-side)
- [What moves each value](#what-moves-each-value)
- [Timeouts](#timeouts)
- [Backoff](#backoff)
- [Concurrency limits](#concurrency-limits)
- [Retry budgets](#retry-budgets)
- [Provenance](#provenance)

## Circuit breaker defaults, side by side

Two widely-used reference implementations, as read from their own source and documentation:

| Parameter | Implementation A | Implementation B |
|---|---|---|
| Failure-rate threshold | 50% | 50% |
| Sampling window | Count-based, 100 calls | Time-based, 10 seconds |
| Minimum throughput before the ratio is evaluated | 100 calls | 20 calls |
| Break duration | 60 seconds | 5 seconds |
| Probe calls in half-open | 10 permitted | 1 |
| Slow-call threshold | 60 seconds, counted as failure at 100% rate | not present by default |

**They agree on the threshold and disagree on everything else by an order of magnitude.** A 5-second
break and a 60-second break are different products. This is why copying a default is not a decision.

## What moves each value

**Break duration** scales with **expected recovery time**. A dependency that recovers when a pod
restarts wants seconds. One that recovers when a human is paged wants minutes. Too short and you
hammer something mid-recovery; too long and you stay down after it came back.

**Trip threshold** scales with **the collateral damage of a false trip**. If opening the breaker
degrades a recommendation carousel, trip eagerly. If it blocks checkout, trip reluctantly and lean
on bounded concurrency instead.

**Minimum throughput** matters **more the lower your traffic**. At 2 requests per minute, a
count-based window of 100 calls spans nearly an hour — the breaker is effectively disabled. At 2,000
requests per second it fills in 50 milliseconds. Pick the window shape to match your traffic, then
set the minimum so a handful of failures cannot trip it.

**Probe count**: one probe recovers fastest and is noisiest; several probes are slower and will not
re-close on a single lucky request. Choose by how expensive a premature re-close is.

## Timeouts

There is no default worth copying. The method:

1. Take the dependency's **successful-response** latency distribution. Successes only.
2. Choose an acceptable false-timeout rate — the share of healthy requests you are willing to cut
   off.
3. Read off the corresponding percentile.
4. Then apply the ceiling: **the point where the answer stops being useful to the client.** Take the
   smaller of the two.

Step 4 usually wins, and it is the step people skip.

*The percentile method is search-extracted; treat it as reasoning rather than citation.*

**Per-attempt vs total.** The per-attempt timeout must be strictly smaller than the total budget,
with room for the backoff intervals:

```
total_budget > (attempts * per_attempt_timeout) + sum(backoff_intervals)
```

If that inequality does not hold, the attempt count is a lie — the budget will cut you off first.

## Backoff

Exponential with a cap and jitter:

```
delay = min(cap, base * 2**attempt)
sleep(jitter(delay))
```

`base` is typically the dependency's median latency; `cap` is typically a few seconds for
interactive work and much longer for background work.

**The jitter variant matters less than having any jitter at all.** Full jitter (`random(0, delay)`)
desynchronises most aggressively and is the safe default. Equal jitter
(`delay/2 + random(0, delay/2)`) preserves more of the backoff shape. Decorrelated jitter feeds the
previous delay forward.

*The formal distinction between these variants could not be verified from a primary source. Jitter
is mandatory; this file does not claim authority on which variant is optimal.*

**Apply the same reasoning to anything periodic**: cron schedules, cache TTLs, health checks, token
refreshes, metric flushes. A thousand actors doing the same thing on the same schedule is a
stampede, whether or not a retry is involved.

## Concurrency limits

**Little's Law** gives the starting point:

```
limit ~= average RPS * average latency (seconds)
```

500 RPS at 40ms gives about 20 concurrent. Set the limit somewhat above that so normal variance does
not reject, and well below the point where the dependency degrades.

**Adaptive** is better where you can manage it: raise the limit while latency is flat, lower it when
latency rises at constant throughput. **Rising latency at flat throughput is a forming queue**, and
it is observable before any error appears.

## Retry budgets

Express the cap as a **percentage of live traffic**, not an attempt count. A 10% retry budget means
retries may not exceed one tenth of first-attempt requests.

Token bucket, as a counter and a timestamp:

- **debit** on each retry
- **credit** on each first-attempt success
- **stop retrying** below a threshold

**Price a timeout-triggered retry higher** — the upstream work is probably still running, so the
retry is additive load. Charging it 2–3x an ordinary retry reflects that.

The emergent behaviour is the point: when a dependency is broadly failing there are no successes to
credit the bucket, so retries stop automatically. An attempt count cannot express that.

## Provenance

- Circuit breaker parameters: read from two reference implementations' own source and docs.
- Little's Law: standard queueing theory.
- The timeout-percentile method, error-budget framing, criticality levels and adaptive throttling:
  **search-extracted.** The canonical write-ups have no upstream repository and were unreachable
  behind the egress proxy. They are presented as reasoning, not citation.
- Jitter variants: named in many places, verified in none reachable. Jitter itself is
  non-negotiable.
- **As of 2026-09.** Defaults in these libraries move between major versions; re-read the source
  before quoting a number in a design document.
