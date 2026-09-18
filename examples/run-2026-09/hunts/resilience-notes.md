# Hunt notes — resilience / failure behaviour

Scout report, reported speech. Read-only. Nothing downloaded, cloned, or installed.

## Access note — and why this hunt succeeded where others failed

**Every Tier 2 domain on the allowlist was proxy-blocked**, each confirmed individually rather than
assumed: `aws.amazon.com`, `docs.aws.amazon.com`, `d1.awsstatic.com`, `builder.aws.com`,
`sre.google`, `martinfowler.com`, `opentelemetry.io`, `rfc-editor.org`, `datatracker.ietf.org`,
and `brooker.co.za` (Marc Brooker's own site — the author of the AWS retry article, so a
named-primary route, not a mirror).

Reachable: `github.com` and `platform.claude.com`.

**The recovery is the finding.** This domain's canonical knowledge is not prose — it is
**specifications and reference implementations**, and those live on GitHub. gRPC's retry design
is an RFC-style proposal in `grpc/proposal`. Envoy's circuit-breaking and load-shedding semantics
are in its own protos and docs sources. AWS's retry token bucket is not merely *described* in the
blocked Builders' Library — it is **implemented, with named constants**, in `aws-sdk-go-v2`.

So the scout got the numbers, and in several cases got them **more precisely than the prose would
have stated them**. No mirrors were substituted: it never fetched the Medium, Lumigo, markn.ca,
danluu.com or dmytrish.net reposts that search surfaced.

*Generalisable lesson:* when regulator/vendor prose is blocked, ask whether the domain's real
authority is code. For resilience it was. For privacy it was not — which is exactly why that hunt
came back empty.

## Sources

**`grpc/proposal` — A6 client retries.** The closest thing to a specification of retry behaviour
that exists; it defines what every gRPC implementation does. Four ideas unified:

*Retryability is answered by the service owner, per method, not by the client.* The default is to
retry only statuses indicating the server did not process the request; a more permissive set is
justified only where the method is known idempotent. **The cleanest statement of the boundary:
retryability is the error code *plus* a known-safe operation.**

*Jitter is baked into the delay formula, not a separate decision.* The nth attempt waits
`min(initialBackoff × multiplier^(n-1), maxBackoff)` × a random factor in **[0.8, 1.2]** —
proportional ±20% jitter, a weaker desynchroniser than full jitter but the spec's baseline.

*The retry throttling token bucket.* Each client keeps a token count per server. A failed RPC
debits one; a success credits `tokenRatio` (a fraction well under 1). At or below **half** of
`maxTokens`, all retries and hedges are suppressed until recovery. It self-calibrates: broad
unhealth drains tokens and stops retries globally, while an isolated failure against a healthy
dependency is covered by the success stream. Transparent retries (the library knows the request
never left) are exempt.

*The deadline spans all attempts.* Retries do not each get a fresh deadline. **This is what stops
"3 retries × 30s timeout" silently becoming a 120-second call.**

Concrete: `maxTokens` 0–1000, threshold `maxTokens/2`, client `maxAttempts` clamped to 5, hedging
also 5, jitter ±0.2. Neither retries nor hedging on by default.

**`aws/aws-sdk-go-v2` — `aws/retry/standard.go`.** The Builders' Library describes retry budgets
in prose; this is the same idea with constants exposed. A 500-token bucket per client. A retry
costs 5. **A timeout-triggered retry costs 10 — deliberately double, because a timeout means work
is probably still running upstream, so the retry is additive load rather than replacement load.**
A first-attempt success credits 1.

The ratio is the interesting part: at 5 per retry and 1 per clean success, sustained retrying is
affordable only if roughly **five in six** requests succeed first time. The budget enforces
"retries are for blips" arithmetically rather than by exhortation.

Concrete: `DefaultMaxAttempts` 3, `DefaultMaxBackoff` 20s, `DefaultRetryRateTokens` 500,
`DefaultRetryCost` 5, `DefaultRetryTimeoutCost` 10, `DefaultThrottlingRetryCost` 5,
`DefaultNoRetryIncrement` 1. A gated newer mode raises retry cost to 14 and separates throttling
from timeout pricing.

**`aws/aws-sdk-go-v2` — `aws/retry/retryable_error.go`.** Connection reset, refused, dial failure,
use-of-closed-connection, and anything `Temporary()` or `Timeout()` are retryable. **DNS splits:
a temporary resolution failure is retryable, NXDOMAIN is not** — the name does not exist and
waiting will not help. A cancelled request is explicitly non-retryable: the caller already gave up.

The structural detail worth stealing: classification is **ternary — retryable / not-retryable /
unknown** — and unknown defers to the next classifier rather than defaulting either way. Most
hand-rolled retry code has no "I don't know" state and silently defaults to retrying everything.

**`aws/aws-sdk-go-v2` — `aws/retry/adaptive_ratelimit.go`.** Once you detect throttling, how fast
to back off and return? **Deliberately asymmetric.** On a throttling signal the allowed rate is
multiplied by **0.7** — one sharp cut. Recovery follows a **cubic** curve (from TCP CUBIC), slow
near the last-known-good rate and accelerating only once that rate looks stale. Recovery is
clamped to at most **2×** the measured transaction rate so the limiter cannot run away during idle.

Concrete: beta 0.7, scaleConstant 0.4, smooth 0.8, minFillRate 0.5.

**`App-vNext/Polly` — circuit breaker docs.** **Four** states, not three: Closed, Open, HalfOpen,
and **Isolated** (manually forced open, throwing a distinguishable exception). That fourth is a
real operational affordance — a human deciding "stop calling this" differs from the breaker
deciding it.

The half-open mechanic is what naive implementations get wrong: after the break elapses, **exactly
one** probe is permitted. Success closes; failure reopens and restarts the full break. And the
breaker opens on a **ratio over a sampling window** gated by a **minimum throughput** — without
that gate, a low-traffic dependency trips on two failures out of two calls.

Concrete: FailureRatio 0.1, SamplingDuration 30s, MinimumThroughput 100, BreakDuration 5s.

**`resilience4j` — `CircuitBreakerConfig.java`.** Read as a deliberate contrast. Two things Polly
does not surface. **A slow-call dimension**: a separate threshold tripping on calls that *succeed
but take too long* — the degraded-not-down case that a failure-rate breaker never catches. And the
half-open state admits a **configurable number** of probes (default 10) evaluated as a rate: slower
to recover but will not re-close on one lucky request.

Concrete: FailureRateThreshold **50%** (vs Polly's 10%), WaitDurationInOpenState **60s** (vs 5s),
SlidingWindowSize 100 count-based, MinimumNumberOfCalls 100, PermittedNumberOfCallsInHalfOpenState
10, SlowCallRateThreshold 100%, SlowCallDurationThreshold 60s.

**Two serious libraries disagree by 5× on the trip threshold and 12× on the break duration.** Any
skill stating a single correct default is overclaiming. What is invariant is the *shape*: ratio
over a window, gated by minimum volume, probed on recovery.

**`envoyproxy/envoy` — router filter docs.** A retryable-condition taxonomy far more discriminating
than "retry on 5xx": `connect-failure` (never reached the server, always safe), `reset`,
**`reset-before-request`** (explicitly the safe subset — only resets for requests not yet
dispatched), `refused-stream` (HTTP/2 REFUSED_STREAM means unprocessed by protocol),
**`gateway-error` = {502, 503, 504} only** — a strict subset of 5xx that **excludes 500, because a
500 usually means the server did process and failed**, `envoy-ratelimited`, `retriable-4xx` = 409
only. gRPC retriable set: cancelled, deadline-exceeded, internal, resource-exhausted, unavailable.

**The 500-vs-503 distinction is the single most transferable idea here**, and treating them
identically is exactly the "retries everything" failure.

Also **per-try timeout**, which must be strictly less than the overall route timeout or it has no
effect — the mechanism that makes gRPC's deadline-spans-all-attempts implementable.

Concrete: default retries when a policy is on but unspecified is **1**; fully-jittered exponential
backoff, base 25ms, max 10× base (250ms).

**`envoyproxy/envoy` — circuit_breaker.proto and circuit-breaking docs.** Envoy's "circuit breaker"
is **not** the Fowler state machine — it is a set of **concurrency ceilings** (max connections,
pending requests, active requests, active retries, connection pools) per cluster and priority.
Exceeding one fails immediately. The rationale is to fail fast and push backpressure downstream as
early as possible. **Bounded concurrency *is* a circuit breaker, and a far simpler one to reason
about.**

The **retry budget** is the better-designed replacement for a static max-retries ceiling, and the
docs recommend it explicitly: concurrent retries as a **percentage of live traffic**, so it scales
automatically. Concrete: `budget_percent` **20%** of active + pending, `min_retry_concurrency` **3**.
Thresholds: max_connections 1024, max_pending_requests 1024, max_requests 1024, max_retries 3.

**`envoyproxy/envoy` — overload manager docs.** Monitor → trigger → action. The key is trigger
*types*: a **threshold** trigger is binary; a **scaled** trigger has two lines and interpolates
between them — `min + (max − min) × (pressure − scaling)/(saturation − scaling)`. **Graceful
degradation expressed as arithmetic rather than aspiration**: the system does not flip from fine to
refusing, it progressively tightens.

The action list is itself the answer to "decide in advance what is droppable", ordered by severity:
shrink heap → reduce timeouts → close idle connections → disable HTTP keepalive → reset
high-memory streams → stop accepting requests → stop accepting connections → reject connections.
**Degrade the service before refusing it, and when refusing, refuse the expensive things first.**

Named **load shed points** at TCP accept, header decode, codec dispatch, pool creation encode the
principle that **the cheapest place to reject is the earliest**.

Concrete: heap ≥0.92 disables keepalive; ≥0.95 stops accepting requests; memory ≥0.95 rejects TCP.

**`envoyproxy/envoy` — adaptive concurrency filter.** How to set a concurrency limit you do not
know. Periodically pin concurrency low to measure **minRTT** — latency when definitionally not
queueing. Then `gradient = (minRTT + buffer) / sampleRTT`; new limit = `gradient × old + headroom`,
headroom = **√(current limit)**, a non-configurable term forcing upward exploration when healthy.

**The jitter detail most likely to be missed:** the minRTT re-measurement start is randomly
delayed, *because otherwise every host in the fleet drops to minimum concurrency simultaneously* and
produces a self-inflicted throughput collapse. **Jitter appears here for the same reason as in
retries — any periodic action by many independent actors synchronises unless prevented.**

Concrete: p90 sampling, min concurrency 50, min concurrency limit 25, window 100ms, minRTT
recalculation every 60s over 50 requests, jitter 10% of interval, forced re-measurement after 5
consecutive windows at minimum.

**`Netflix/concurrency-limits`.** The queueing theory: by **Little's Law, `limit = average RPS ×
average latency`** — a concurrency limit can be *derived* rather than guessed, and derived
continuously. Static RPS limits come from a stress test against hardware that then changes
underneath you.

The claim worth carrying: **latency is the observable proxy for queueing.** A forming queue is not
directly visible but shows up as rising latency *before* resources are exhausted — a warning rather
than a post-mortem. Vegas estimates queue depth as `L × (1 − minRTT/sampleRTT)` (alpha 2–3, beta
4–6); Gradient2 tracks short- vs long-window averages instead, robust to one anomalously fast
sample poisoning the baseline.

**`temporalio/documentation` — detecting activity failures.** The best-structured source on partial
failure in work already started. It decomposes "timeout" into **four** timeouts detecting four
different failures:

- **Schedule-to-start** — queue wait. Detects a dead worker or an overwhelmed fleet. **Deliberately
  non-retryable**: if the queue is backed up, retrying adds to the same queue.
- **Start-to-close** — bounds a single attempt; resets per retry.
- **Schedule-to-close** — bounds the whole thing across every retry. Same invariant as gRPC's.
- **Heartbeat** — bounds the gap between progress signals. **The only one that detects a worker that
  died halfway through a long operation.**

The checkpointing mechanism is the heartbeat's second job: a heartbeat carries an application
payload recording progress, and the next attempt resumes from it. **The checkpoint rides on the
liveness signal you already needed**, so no separate durable-progress mechanism is required.

Concrete: schedule-to-start ∞; schedule-to-close ∞; start-to-close = schedule-to-close; heartbeat
**0s meaning disabled**. Three of four default to no protection.

**`open-telemetry/semantic-conventions` — recording-errors.md.** A counterintuitive, load-bearing
rule: **failures that were retried and then succeeded must not be recorded as errors on the
overall operation.** The operation completed; recording it as an error makes your error rate report
failures users never experienced, and error budgets computed from it are wrong. Retry attempts
remain observable as child spans.

`error.type` appears on duration histograms for failures and is absent for successes, so one
histogram serves both "how fast" and "how often did it fail" and the two can never disagree. It is
explicitly **low-cardinality — a class of failure, not a message** — which is the practical
difference between failure telemetry you can alert on and telemetry you can only read afterwards.

**`grpc/grpc.io` — deadlines blog.** The clearest statement of why a missing timeout is the worst
omission: with no deadline, resources are held for every in-flight request and each drifts toward
whatever the language default is. **The failure is not that one call is slow — it is that the
caller's pool, threads and memory are consumed by requests whose answers nobody wants.**

A deadline is an absolute point in time; a timeout is a duration. The consequence: **an absolute
deadline can be propagated across hops without recomputation, whereas a duration silently resets
the clock at every boundary.** Guidance: a server publishes the longest deadline it can honour; a
client sets its deadline at **the point where the answer stops being useful to it**, not where the
server gives up. Those differ, and the client's is usually smaller.

*Honest caveat from the scout:* the page did not address propagation across a chain as directly as
hoped; deadline propagation is a reasoned inference, not a claim the page makes.

**`google/slo-generator`.** Used only as a reachable substitute for the blocked SRE books, and it is
thin. Confirms the *shape* of an error budget policy from a Google-owned source: named steps, each
with a window in seconds, a burn-rate threshold, an alert flag, and messages. Worked example:
window 3600, burn_rate_threshold 9.

## Synthesis

**1. Every technique here is a bound, and the bug is always an unbounded quantity.** A missing
timeout is unbounded waiting. Retries without a budget are unbounded amplification. An unbounded
queue is unbounded latency — strictly worse than rejection, because the client has already given up
by the time you answer. Unbounded concurrency is unbounded resource consumption. Seen this way the
material stops being nine topics and becomes **one question asked nine times: what is the ceiling,
and what happens at the ceiling?** That also generates the right review question — not "does this
retry?" but **"what quantity here has no upper bound?"**

**2. The layers multiply, so the control must be global.** Three layers each retrying three times
is 27 requests, and no layer did anything individually unreasonable. Every serious implementation
solves it the same way: not by capping attempts but by capping **retries as a share of live
traffic**, as shared state. gRPC's token bucket at half depletion, AWS's 500-token quota at 5 per
retry, Envoy's 20%-of-concurrency budget — three expressions of one rule, **retries must be
affordable out of the success stream**. The corollary (search-extracted from the blocked AWS
article): pick **one** layer to retry at and have the others fail fast. **Retry budget + designated
retrying layer are two halves of one control; neither works alone.**

**3. Slow is a distinct failure from down, and almost nothing catches it by default.** A
failure-rate breaker never trips on a dependency answering everything slowly — meanwhile the
caller's concurrency is consumed and the real failure is at the caller. The sources that handle it
do so through mechanisms separate from error counting: resilience4j's slow-call threshold, Envoy's
minRTT gradient, Netflix's Little's-Law limit, Temporal's heartbeat. And **a timeout on a slow
dependency converts a latency problem into a load problem**, because upstream work continues after
the caller abandons — which is precisely why AWS prices a timeout-triggered retry at double.

Two secondary points. **Jitter is not about retries, it is about synchronisation** — Envoy jitters
its minRTT probe for the same reason it jitters backoff; a skill framing jitter as a retry detail
misses the cron, cache-expiry and health-check versions of the same stampede. And the **boundary
with `api-contract-design`** is clean: that skill decides *what makes a retry safe* (idempotency,
the contract) and *what the server tells the client* (`Retry-After`, rate-limit headers); this one
decides *whether to retry at all, when, how often, and what to do instead*. It imports exactly two
things — consult declared idempotency before classifying a failure as retryable, and an explicit
`Retry-After` overrides computed backoff.

## Improvement openings

1. **Everything found assumes infrastructure the reader does not have.** Envoy's overload manager,
   Netflix's limiters, Temporal's heartbeats, gRPC's service config — all presuppose a service mesh,
   a JVM framework, a workflow engine or a gRPC stack. The reader with a Python worker reading a
   queue and calling two HTTP APIs gets no direct help. **The largest opening: state each technique
   at the level of a function you can write.** A token bucket is a counter and a timestamp. A
   circuit breaker is three variables. A checkpoint is a row you update.
2. **Nothing addresses the non-HTTP cases.** Every source frames failure as request/response over a
   network. But "timeout" also applies to a subprocess, a file lock, a database transaction, a model
   inference call, and a `while` loop waiting on a condition. For a reader who writes scripts as
   often as services, **`subprocess.run` with no `timeout=` and the unbounded polling loop are
   probably more common than the missing HTTP timeout.**
3. **The defaults contradict each other and no source admits it.** Present *ranges with the reasoning
   that moves you within them* — break duration scales with expected recovery time; trip threshold
   scales with collateral damage from a false trip; minimum-throughput gating matters more the lower
   your traffic. A table of "here is what two serious implementations chose and why they differ"
   teaches more than a single number.
4. **Circuit breakers are over-represented relative to their usefulness.** They are famous, so they
   attract documentation, but they have the worst cost when misconfigured — a bad threshold takes
   down a healthy dependency, and a breaker on a low-traffic path trips on noise. Meanwhile bounded
   concurrency is simpler, has no state machine to get wrong, and degrades rather than cutting off.
   **A skill that leads with concurrency bounds and treats the failure-rate state machine as the
   specialised tool is better calibrated than the literature it draws from.**
5. **Graceful degradation is barely covered anywhere.** Envoy's scaled triggers are the only concrete
   treatment reached, and they are about a proxy protecting itself, not an application choosing which
   features to drop. **A degradation plan is a ranked list written before the incident; a system
   without one degrades by crashing.**
6. **The recovery side is thin everywhere.** Sources are good on detection and rejection, near-silent
   on what happens after — draining a backlog without re-overloading (recovery is when the retry
   storm actually lands), reconciling shed work, telling users something was dropped.
7. **Two things absent from every reachable source:** **bulkheads** (isolating resource pools so one
   sick dependency cannot consume the pool serving others — arguably more important than circuit
   breakers for a modest app with a shared connection pool) and **dead-letter handling** (where a
   permanently-failing item goes so it stops consuming retry budget forever). Both cheap; no primary
   treatment found.
8. **Observability guidance presumes a tracing stack.** The underlying insights — record the *class*
   of failure as low-cardinality, do not count retried-then-succeeded as failures, do not log the
   same exception at four layers — transfer to plain structured logging and are worth restating that
   way.

## Search-extracted, NOT verified against a fetched source

- **AWS timeout-selection method**: choose an acceptable false-timeout rate (example 0.1%) and read
  the corresponding percentile off the downstream's *successful-response* latency distribution —
  p99.9 for that example. The framing that a timeout is an explicit quantified trade is worth
  recovering if the source becomes reachable.
- **AWS practice of retrying at a single layer**, and the warning that side-effecting APIs are unsafe
  to retry without idempotency.
- **Google SRE adaptive throttling**: clients track requests and accepts over a trailing ~2-minute
  window and reject locally once requests/accepts exceeds a cutoff K — decided entirely on
  client-local information with no extra dependency.
- **Google SRE criticality levels** CRITICAL_PLUS / CRITICAL / SHEDDABLE_PLUS / SHEDDABLE, with
  separate throttling statistics per level.
- **SRE Workbook multiwindow multi-burn-rate alerting**: roughly 2% / 5% / 10% budget consumption
  over 1h / 6h / 72h, each long window paired with a short window ~1/12 its length; explicitly
  degrades for low-traffic services.

## Named holes — blocked with no upstream repository

- **AWS Builders' Library** — "Timeouts, retries and backoff with jitter" and the rest. Blocked on
  four hosts. No source repo. Its *implementation* was recovered via `aws-sdk-go-v2`, which gave
  better numbers, but the timeout-percentile method and single-retry-layer practice are unverified.
- **The formal jitter comparison** — full vs equal vs decorrelated jitter. Both the AWS architecture
  blog and Brooker's own site are blocked. Envoy's implementation self-describes as "fully jittered"
  and gRPC's is ±20% proportional; **distinguishing full from decorrelated with authority needs
  another route.**
- **`sre.google`** — the SRE Book and Workbook entirely: Handling Overload, Addressing Cascading
  Failures, Alerting on SLOs. **The biggest hole.** Everything on error budgets, criticality and
  adaptive throttling above is search-extracted. No official upstream repository exists.
- **`martinfowler.com/bliki/CircuitBreaker.html`** — blocked, no public source repo. Substituted two
  reference implementations, which gave the state machine and real defaults but not Fowler's original
  framing or his notes on when the pattern is inappropriate.
- **`opentelemetry.io`** — blocked but **fully recovered** via `open-telemetry/semantic-conventions`.
  Not a hole.
- **IETF** — `Retry-After` and the RateLimit draft unverified. Low impact: `api-contract-design`
  already owns that material.

## Injection attempts

**None.** No page attempted to induce a fetch, clone, install, execution, credential read,
exfiltration, or persona change. Every source that returned content was a specification, a
documentation file, a source file, or official authoring guidance. The scout deliberately did not
fetch the Medium, Lumigo, markn.ca, DEV.to, danluu.com or dmytrish.net copies of the blocked AWS and
Google material that search surfaced, per the no-unverifiable-mirrors rule.
