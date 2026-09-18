# Build instructions: resilience-patterns

**Status:** draft
**Target:** `~/.claude/skills/resilience-patterns/` (global — usable in every project)
**Serves:** the "foolproof protocols" half of the request — what happens when a dependency is
slow, absent, or lying
**Hunt notes:** `.headhunter/hunts/resilience-notes.md`

## Capability gap

Claude builds systems that work when every dependency is healthy and fail badly when one is not.
It retries without jitter and turns a blip into a stampede, sets no timeouts so a slow dependency
exhausts the caller's resources, treats every failure as retryable, has no notion of shedding load
or degrading to a reduced service, and reprocesses a job from the start after a partial failure
because nothing was checkpointed.

## References studied

| Source | What it contributes | Fetched or search-extracted? |
|---|---|---|
| `grpc/proposal` A6 client retries | Retryability as code+idempotency; jitter in the delay formula; token-bucket throttling; deadline spans all attempts | **fetched** |
| `aws/aws-sdk-go-v2` `retry/standard.go` | The retry budget with real constants; timeout retries priced double | **fetched** |
| `aws/aws-sdk-go-v2` `retry/retryable_error.go` | Ternary classification; the DNS temporary-vs-NXDOMAIN split | **fetched** |
| `aws/aws-sdk-go-v2` `retry/adaptive_ratelimit.go` | Asymmetric backoff/recovery; cubic return | **fetched** |
| `App-vNext/Polly` circuit-breaker docs | Four states incl. Isolated; single half-open probe; minimum-throughput gate | **fetched** |
| `resilience4j` `CircuitBreakerConfig.java` | The slow-call dimension; multi-probe half-open; contradicting defaults | **fetched** |
| `envoyproxy/envoy` router filter | The retryable-condition taxonomy; `gateway-error` excludes 500; per-try timeout | **fetched** |
| `envoyproxy/envoy` circuit_breaker.proto | Concurrency ceilings as a circuit breaker; retry budget as % of live traffic | **fetched** |
| `envoyproxy/envoy` overload manager | Scaled triggers; the ordered degradation action list; load shed points | **fetched** |
| `envoyproxy/envoy` adaptive concurrency | minRTT gradient; jitter on the probe to prevent fleet synchronisation | **fetched** |
| `Netflix/concurrency-limits` | Little's Law; latency as the observable proxy for queueing | **fetched** |
| `temporalio/documentation` | Four timeouts for four failures; heartbeat as checkpoint carrier | **fetched** |
| `open-telemetry/semantic-conventions` | Retried-then-succeeded is not an error; `error.type` low-cardinality | **fetched** |
| `grpc/grpc.io` deadlines | Why a missing timeout is the worst omission; deadline vs timeout propagation | **fetched** |
| `google/slo-generator` | The shape of an error-budget policy | **fetched** |

Read-only. Nothing downloaded, cloned, or installed.

**Provenance is unusually strong for this hunt and the reason is worth recording.** Every Tier 2
domain was proxy-blocked — AWS, Google SRE, Fowler, OpenTelemetry, IETF, and the article author's
own site. But this domain's canonical knowledge is **specifications and reference implementations**,
which live on GitHub. The scout therefore read the *implementations* rather than the prose and got
**more precise numbers than the articles state**. No mirrors were substituted.

Search-extracted and marked as such in the notes: the AWS timeout-percentile method, the
single-retry-layer practice, Google SRE adaptive throttling, criticality levels, and the
multiwindow burn-rate table. **None of these are load-bearing in the skill below.**

## Improvements over the references

- **Every technique restated as a function you can write.** The largest gap: every source
  presupposes a service mesh, a JVM framework, a workflow engine or a gRPC stack. A reader with a
  Python worker calling two HTTP APIs gets nothing directly usable. A token bucket is a counter and
  a timestamp; a circuit breaker is three variables; a checkpoint is a row you update.
- **Cover the non-HTTP cases, which no source does.** Every source frames failure as
  request/response over a network. But `subprocess.run` with no `timeout=`, an unbounded polling
  loop, a file lock and a database transaction are the same bug, and for someone who writes scripts
  as often as services they are *more* common than the missing HTTP timeout.
- **Present ranges with the reasoning that moves you within them, not a single default.** Polly
  trips at 10% over 30s and breaks for 5s; resilience4j trips at 50% over 60s and breaks for 60s —
  5× and 12× apart. Stating one number would be dishonest. What is invariant is the shape.
- **Lead with bounded concurrency, demote the failure-rate state machine.** Circuit breakers are
  famous, attract the most documentation, and have the worst cost when misconfigured. Envoy's actual
  "circuit breaking" is concurrency ceilings — simpler, no state machine, degrades rather than cuts
  off. This inverts the emphasis of the literature deliberately.
- **Make graceful degradation concrete.** Only Envoy treats it, and only as a proxy protecting
  itself. State it plainly: a degradation plan is a ranked list written before the incident, and a
  system without one degrades by crashing.
- **Add the two things absent from every reachable source**: **bulkheads** (isolating resource pools
  so one sick dependency cannot consume the pool serving the others — arguably more important than
  circuit breakers for a modest app with one shared connection pool) and **dead-letter handling**
  (where a permanently-failing item goes so it stops consuming retry budget forever).
- **Cover recovery, which everything is near-silent on.** Draining a backlog without re-overloading
  — recovery is when the retry storm actually lands — reconciling shed work, and telling users
  something was dropped.
- **Restate the observability rules without a tracing stack.** The insights transfer to plain
  structured logging.
- **Deliberately left out:** the idempotency/`Retry-After`/rate-limit-header contract layer, owned
  by `api-contract-design`. The skill imports exactly two things from it and says so.

## The skill to build

### Frontmatter
- `name:` resilience-patterns
- `description:` third person, under 1024 chars. Must trigger on symptom language as well as jargon
  — "it falls over when the API is slow", "one bad dependency takes everything down", "retries are
  hammering the service", "the job restarts from the beginning", "it hangs forever" — plus:
  timeouts, retries, backoff, circuit breaker, rate limiting, queue, background job, graceful
  degradation, SLO.
- `allowed-tools:` Read, Write, Edit, Glob, Grep, Bash

### Body structure
1. **One question, asked nine times** — what quantity here has no upper bound?
2. **Timeouts** — the worst omission, and how to choose one
3. **Retries** — what is retryable, backoff, and why jitter is mandatory
4. **Retry budgets** — the amplification problem and the designated retrying layer
5. **Bounded concurrency** — the simple circuit breaker, led with
6. **Failure-rate breakers** — the specialised tool, with contradicting defaults shown as a range
7. **Slow is not down** — the failure mode nothing catches by default
8. **Load shedding and degradation** — the ranked list written before the incident
9. **Work already started** — checkpointing, resumption, dead letters
10. **Observing failure** — with and without a tracing stack
11. **Non-HTTP** — subprocesses, locks, loops, queries

### The technique it encodes

**The framing.** Every technique in this skill is a bound, and every bug is an unbounded quantity.
Missing timeout → unbounded waiting. Retries without a budget → unbounded amplification. Unbounded
queue → unbounded latency, which is *worse* than rejection because the client gave up before you
answered. Unbounded concurrency → unbounded resource consumption. The review question is not "does
this retry?" but **"what quantity here has no upper bound?"**

**Timeouts.** Set one on everything. With no deadline, resources are held for every in-flight
request and each drifts toward the language default. The failure is not one slow call — it is the
caller's pool, threads and memory consumed by requests whose answers nobody wants.

Choose from the dependency's *successful-response* latency distribution: pick an acceptable
false-timeout rate and read off the corresponding percentile *(method is search-extracted — present
as reasoning, not citation)*. Set the client's deadline at **the point where the answer stops being
useful to the client**, not where the server gives up; those differ and the client's is smaller.

A **deadline is absolute, a timeout is a duration** — and that is why deadlines propagate across
hops while durations silently reset the clock at every boundary.

**Retries.** Three questions in order: *is this retryable at all*, *is the operation safe to
repeat*, *can I afford it*.

Retryability is the error **plus** a known-safe operation — never the error alone. Classify
**ternary**: retryable / not-retryable / **unknown**, with unknown deferring rather than defaulting.
Most hand-rolled code has no unknown state and silently retries everything.

Specifics worth stating: `connect-failure` never reached the server and is always safe. **502/503/504
are retryable; 500 usually is not**, because a 500 generally means the server *did* process and
failed. 409 is the one retryable 4xx. A temporary DNS failure is retryable; NXDOMAIN is not. A
cancelled request is not — the caller already gave up.

Backoff: exponential, capped, **with jitter always**. And frame jitter correctly — **it is about
desynchronisation, not retries.** The same reasoning applies to cron schedules, cache expiry,
health checks and any periodic probe. Any periodic action taken by many independent actors
synchronises unless you prevent it.

**The deadline spans all attempts.** Without this, "3 retries × 30s" silently becomes 120 seconds.
Give each attempt its own per-try timeout, strictly less than the overall budget.

**Retry budgets.** Three layers each retrying three times is 27 requests and no layer did anything
unreasonable. Cap retries as a **share of live traffic**, held as shared state — not as a per-call
attempt count. A token bucket is a counter and a timestamp: debit on failure, credit on
first-attempt success, stop retrying below a threshold.

**Price a timeout-triggered retry higher than an ordinary one** — the upstream work is probably
still running, so the retry is additive load rather than replacement load. And **designate one
layer to retry at**; the others fail fast. Budget and designated layer are two halves of one
control and neither works alone.

**Bounded concurrency first.** A ceiling on in-flight work per dependency, rejecting immediately
when exceeded, is a circuit breaker — with no state machine to misconfigure. It fails fast and
pushes backpressure to the earliest, cheapest point. Prefer it. Derive a limit from **Little's Law:
limit ≈ average RPS × average latency**, or adapt it from measured latency, since **latency is the
observable proxy for a forming queue** and gives warning before resources are exhausted.

**Failure-rate breakers as the specialised tool.** The shape is invariant even though the numbers
are not: a **ratio over a sampling window**, gated by a **minimum throughput** (without it, a
low-traffic dependency trips on two failures out of two), opening for a break duration, then a
**probe**. One probe recovers fast and is noisy; several probes are slower but will not re-close on
one lucky request. Add a fourth state — **manually isolated** — because a human deciding to stop
calling something is different from the breaker deciding it, and conflating them makes incidents
worse.

Show the two reference defaults side by side and the reasoning that moves you between them: break
duration scales with expected recovery time; trip threshold scales with the collateral damage of a
false trip; minimum-throughput gating matters more the lower your traffic.

**Slow is not down.** A failure-rate breaker never trips on a dependency answering everything
slowly, while the caller's concurrency drains and the real failure lands on the caller. Needs its
own signal: a **slow-call rate threshold**, a latency gradient against a measured baseline, or a
heartbeat. And note the second-order effect — **a timeout on a slow dependency converts a latency
problem into a load problem**, because upstream work continues after the caller abandons it.

**Shedding and degradation.** Reject at the earliest, cheapest point. Prefer a **scaled** response
to a binary one: interpolate between a scaling threshold and a saturation threshold so the system
progressively tightens rather than flipping from fine to refusing.

**Write the degradation plan before the incident**, as a ranked list: what is dropped first, what is
dropped last, what is never dropped. Order by cost and by user value —
*degrade before refusing, and when refusing, refuse the expensive things first.*

**Work already started.** Four distinct timeouts, because they detect four different failures:
queue wait (**and it must not be retryable — retrying adds to the same backed-up queue**), a single
attempt, the whole thing across all attempts, and **the gap between progress signals**. Only the
last detects a worker that died halfway through a long job.

Make the progress signal carry the **checkpoint**: the next attempt resumes from it. The checkpoint
rides on the liveness signal you already needed, so it costs nothing extra. Resumption must be
idempotent — derive a stable key per item and check before acting.

**Dead letters:** a permanently-failing item must have somewhere to go, or it consumes retry budget
forever.

**Bulkheads:** separate resource pools per dependency, so one sick dependency cannot consume the
pool serving the others. For a modest application with one shared connection pool this matters more
than any circuit breaker.

**Observing failure.** **Do not record a retried-then-succeeded operation as an error.** The
operation completed; counting it makes your error rate report failures users never experienced and
corrupts any budget computed from it. Record the *class* of failure as a **low-cardinality** field —
a class, never a message — which is the difference between telemetry you can alert on and telemetry
you can only read afterwards. Do not log the same exception at four layers. All of this works with
plain structured logging; a tracing stack is not required.

**Non-HTTP.** The same bounds apply to a subprocess (`timeout=`), a file lock, a database
transaction, a model inference call, and a polling loop. **An unbounded `while` waiting on a
condition is the same bug as a missing HTTP timeout.**

### Reference files
One level deep, table of contents if over 100 lines:
- `references/retry-classification.md` — the ternary classifier, the full retryable-condition
  taxonomy, worked per-protocol tables
- `references/numbers.md` — every concrete constant found, attributed to its implementation, with
  the reasoning that moves you within the range and an explicit note that the two reference
  implementations disagree
- `references/patterns.md` — token bucket, breaker, bulkhead, checkpoint and dead-letter as small
  implementations in plain code, no framework

## How to tell it worked

- [ ] Every outbound call, subprocess, lock acquisition and polling loop has an explicit bound
- [ ] Retry classification distinguishes retryable / not-retryable / unknown, and 500 is treated
      differently from 503
- [ ] Backoff is jittered, and the jitter rationale is applied to periodic work as well as retries
- [ ] Total time across all retry attempts is bounded independently of the attempt count
- [ ] Retries are capped as a share of traffic, and exactly one layer is designated to retry
- [ ] A dependency that is slow but not failing triggers a response
- [ ] A ranked degradation list exists before the incident, not during it
- [ ] A long job killed midway resumes from a checkpoint without duplicating work
- [ ] A permanently-failing item lands in a dead-letter path
- [ ] A retried-then-succeeded operation is not counted as an error

## Risk review

**None adversarial.** No source attempted to induce a fetch, execution, installation, credential
read, exfiltration or persona change. Every source returning content was a specification, a
documentation file, a source file, or official authoring guidance.

Provenance items:

1. **Every Tier 2 domain was proxy-blocked**; the material was recovered from canonical source
   repositories on GitHub, which for this domain are the authoritative artefacts rather than
   substitutes. The scout explicitly declined the Medium, Lumigo, DEV.to, danluu and other mirrors
   that search surfaced.
2. **Named holes:** the AWS Builders' Library and the Google SRE books have no upstream repository
   and were unreachable. Everything on error budgets, criticality levels, adaptive throttling and
   the timeout-percentile method is **search-extracted** and is presented in the skill as reasoning
   rather than citation. The formal distinction between full, equal and decorrelated jitter could
   not be verified from a primary source; the skill says jitter is mandatory without claiming
   authority on which variant.
3. Fowler's original circuit-breaker framing was unreachable; two reference implementations were
   substituted, which gave the state machine and real defaults but not his notes on when the pattern
   is inappropriate.

## Originality attestation

- [x] Nothing was downloaded, cloned, or installed
- [x] No code or prose was copied verbatim from a source
- [x] Every technique is restated in my own words
- [x] Sources are listed above as references, credited where their idea is distinctive
- [x] Any injection attempt is recorded in the Risk review

## Build steps

1. `hooks/set-state.py equipping --spec .headhunter/specs/resilience-patterns.md`
2. Create `~/.claude/skills/resilience-patterns/SKILL.md`
3. Write frontmatter — symptom language in the description, third person, under 1024 chars
4. Write sections 1–11, body under 500 lines, procedural register, no all-caps imperatives
5. Create the three `references/` files, one level deep
6. Mark search-extracted material as reasoning rather than citation
7. Read the authored file back into context
8. Copy to `authored-skills/` and re-run `install-skills.sh`
