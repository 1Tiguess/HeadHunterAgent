---
name: api-contract-design
description: >-
  Designs HTTP API contracts that survive misbehaving clients — idempotent writes that do
  not duplicate under retry, pagination that stays correct while data is being written,
  rate-limit and error responses a client can act on programmatically, signed webhooks, and
  versioning that can be retired safely. Use when designing or reviewing a REST API, adding
  write endpoints, choosing status codes, paginating a collection or an event log, sending
  or receiving webhooks, or when retries are creating duplicate records and clients cannot
  tell what went wrong.
allowed-tools: Read, Write, Edit, Glob, Grep, Bash
---

# API contract design

An API that works when the client behaves is not finished. Clients retry aggressively, their
clocks disagree with yours, connections drop after the write lands but before the response
returns, and they walk a collection while it is being written to. The contract is what
happens then.

## Where to start

```
Adding a write endpoint?          → §1 Idempotency
Returning a list or a log?        → §2 Pagination
Writing an error response?        → §3 Errors
Throttling anyone?                → §4 Rate limits
Sending or receiving webhooks?    → §5 Webhooks
Changing or retiring an endpoint? → §6 Versioning
Unsure which status code?         → §7 Decision table
```

## 1 — Idempotency has three states, and the third is the problem

Lead with the reason, because it justifies everything else: **after a connection failure a
client genuinely cannot distinguish "never applied" from "applied, response lost."** It may
safely auto-retry only methods that are already idempotent. For anything else, the server has
to collapse that ambiguity — that is the entire purpose of the mechanism.

Accept an idempotency key on POST and PATCH. Then:

| State | Condition | Response |
|---|---|---|
| **Unseen** | No record of this key | Process normally, store the outcome |
| **Completed** | Key seen, original finished | Return the stored outcome |
| **In-flight** | Key seen, original still running | 409 **with `Retry-After`**, or 202 with a status location |

**The in-flight state is the one most implementations omit, and omitting it is exactly why
concurrent retries produce duplicates.** Two copies of the same request racing each other
both find no completed record and both proceed.

Store a **fingerprint of the request payload** alongside the key. A key replayed with a
different fingerprint is a client bug — reject it rather than silently processing it.

**Scope the key as a composite of (authenticated principal, operation, client key).** Published
guidance deliberately leaves scope to the implementer, but when several partners write to one
resource, scope is a *security boundary*: a globally-scoped key lets one partner collide with
or replay another's writes. Require high-entropy keys so one cannot be guessed, and state the
scope in your documentation so clients can reason about it.

**Never return a bare error for the in-flight case.** An aggressive retrier will simply retry
it, tightening the loop into a hot spin.

**Cache definitive outcomes only.** This is where the most-copied production implementation
teaches the wrong habit:

- A **validation rejection** is definitive. Store and replay it — the request will never
  succeed as written.
- A **timeout, 5xx, or mid-write crash is indeterminate.** Do **not** store it. The client's
  retry is the only path to a correct record, and caching the failure permanently poisons the
  key.

For an append-only or legally significant record, that distinction is not optional.

**Set retention from the client's worst-case retry horizon**, not from a payments default.
Under a real network partition a partner may not retry for longer than 24 hours, and a pruned
key silently converts a replay into a duplicate write. Publish the window and say what happens
after expiry.

`references/idempotency.md` has the algorithm, fingerprinting and worked retention reasoning.

## 2 — Pagination under concurrent writes

**Offset pagination is wrong for anything being written to.** Rows shift between requests, so
a walker skips or repeats and nothing in the response reveals it happened.

Use a cursor over a **server-assigned monotonic sequence**. Never order by a client-supplied
timestamp — clocks disagree, and for an ordered record that disagreement is a correctness
problem, not a cosmetic one. Do not assume your ids are sortable unless you chose them to be;
the well-known cursor implementations work only because theirs happen to be.

**Distinguish two reads explicitly:**

- **Stable snapshot** — pin a sequence ceiling at the first request so the page set does not
  grow underneath the reader. Right for "show me everything that happened during the incident".
- **Live forward tail** — the cursor advances into newly appended records. Right for "is it
  still happening?".

These want different cursor semantics. Make them separate endpoints or a required mode
parameter — never the same call quietly behaving differently.

Return `has_more` as a boolean the client can branch on without arithmetic.

## 3 — Errors the client can act on

Use `application/problem+json`.

| Member | Rule |
|---|---|
| `type` | URI naming the *class* of problem. **Never leave it `about:blank` on anything a client could correct** — the default degrades to "nothing beyond the status code" without anyone noticing |
| `title` | Stable human summary of the type. Does not vary between occurrences |
| `detail` | Occurrence-specific prose. **Consumers are told not to parse it** |
| `instance` | Identifies this occurrence |

Because `detail` must not be parsed, **everything machine-actionable goes in extension
members**. Clients are required to ignore extensions they do not recognise, which is precisely
what makes the error contract safe to evolve in place.

The specification says how to describe a failure. It never says to describe **what a correct
request would look like** — and that is the thing a client actually needs. Model it as
extensions:

- which field was wrong, and what values are acceptable
- the retry-safe next step
- where relevant, the stored idempotency key and what state it is in

For field-level failures use an `errors` array whose entries carry a pointer at the offending
field. This appears only as a non-normative example in the spec but has become the de facto
convention; adopt it deliberately rather than inventing a third shape.

Problem details describe the HTTP interface, not your implementation. No stack traces, no
internal identifiers.

`references/error-bodies.md` has worked shapes.

## 4 — Rate limits are a shared contract

Advertise **policy** and **state** separately: the quota and window you enforce, and the
client's current standing against it.

**Express the window as relative seconds, not an absolute reset timestamp.** This is
deliberate — it removes any dependency on client and server clocks agreeing, which is exactly
the failure you cannot debug remotely.

If you also send `Retry-After`, **it wins**. Say so.

Treat the numbers as **hints, not an SLA**, and document that: you may throttle a compliant
client under saturation, and quota may be lowered without notice.

**Add jitter to the advertised window.** A quota that resets at a fixed wall-clock moment
brings every client back simultaneously — you have built a thundering herd into your own
contract. Require full-jitter exponential backoff on the client side too.

Put the same numbers in a problem-detail body as in the headers. Nothing guarantees a client
reads both, and the one it reads should be sufficient.

Watch what the numbers leak: quota values expose infrastructure capacity, and error responses
that consume quota let an attacker probe another tenant's traffic.

## 5 — Webhooks

Sign over a **timestamp concatenated with the raw body**, compare in **constant time**, and
enforce a **tolerance window** backed by a verifier-side replay cache sized to that window.

Be honest about provenance here: the standards-track answer is heavy and is essentially never
what webhook producers ship, and the field-standard HMAC pattern has no authoritative
specification. Borrow the standard's *ideas* — an explicit creation time, an explicit expiry,
a nonce, a replay cache — rather than its full canonicalisation.

Retry on a documented backoff schedule.

**And close the loop nobody mentions:** signed delivery with retry is **at-least-once**
delivery. So the *receiver* needs the same duplicate suppression your write path has — a
stable delivery id and receiver-side deduplication. If you publish webhooks, document the
delivery id and tell consumers to dedupe on it.

## 6 — Versioning and retirement

Signal deprecation with the `Deprecation` header and the retirement date with `Sunset`, and
point a link relation at human documentation.

**The Sunset instant must not precede the Deprecation instant.**

**The trap:** these two headers use *different serialisations for the same kind of value* —
one a structured-field date, the other an HTTP-date string — despite being designed to be used
together. Getting this wrong produces headers that parse individually and contradict each
other in aggregate.

Publish the deprecation window ahead of time. Nothing in the standards mandates a minimum, so
state yours.

## 7 — Status code decision table

The specifications collectively offer several plausible codes for the same situations and
reconcile none of them. Pick from this table, document your choice, and never vary it — the
consistency matters more than which defensible option you chose.

| Situation | Code | Why |
|---|---|---|
| Retry arrives while original is in flight | 409 | A concurrency conflict, resolvable by waiting. Send `Retry-After` |
| Key reused with a different payload | 422 | Well-formed but semantically contradictory |
| Required idempotency key missing | 400 | The request itself is malformed |
| Precondition (`If-Match`) failed | 412 | The specified precondition semantics |
| Rate limited | 429 | Conventional, though not mandated by the header spec |
| Authenticated but not permitted | 403 | Distinguish from 401 — retrying with the same credential will not help |

## Reference files

| File | Contents | Load when |
|---|---|---|
| `references/idempotency.md` | Three-state algorithm, fingerprinting, retention, definitive vs indeterminate | Adding any write endpoint |
| `references/error-bodies.md` | Problem-detail shapes with worked corrective extensions | Writing error responses |

## Done means

- The same write replayed ten times *concurrently* produces exactly one record
- A key replayed with a different body is rejected, not processed
- A retry arriving mid-flight gets told when to come back
- A timeout does not poison the key — a later retry can still succeed
- Paginating a log while it is being appended to neither skips nor repeats
- Snapshot and tail reads are separately addressable and documented
- Every 4xx body carries a non-`about:blank` `type` and machine-readable corrective extensions
- A rate-limited client can compute its retry time without a clock shared with the server
- A webhook receiver given the same delivery twice records it once
