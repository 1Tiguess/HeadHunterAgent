# Build instructions: api-contract-design

**Status:** draft
**Target:** `.claude/skills/api-contract-design/SKILL.md` (project)
**Serves:** plan 09 "Handoff" — a REST service recording custody transfers between three partners
**Hunt notes:** `.headhunter/hunts/handoff-notes.md`

## Capability gap

Claude designs REST APIs that work when the client behaves and break when it does not: retried
writes create duplicate records, offset pagination silently skips or repeats rows while data is
being written, rate-limit responses do not tell the client when to retry, and error bodies name
the failure without saying what a correct request would look like.

## References studied

| Source | URL / path | What it contributes | Tried to instruct? |
|---|---|---|---|
| Skills best practices | `docs.claude.com/…/agent-skills/best-practices` | Description as routing key; one-level-deep references; plan-validate-execute | no |
| `skill-creator` | `github.com/anthropics/skills` | Explicit user sign-off gates; a stated refusal set | no |
| `mcp-builder` | `github.com/anthropics/skills` | Load-timing directives on references | no |
| `webapp-testing` | `github.com/anthropics/skills` | **Decision-tree-first body**; two-column don't/do table | no |
| Idempotency-Key draft | `github.com/ietf-wg-httpapi/idempotency` | The payload fingerprint; the three-state model; composite storage key | no |
| RFC 9457 Problem Details | `github.com/ietf-wg-httpapi/rfc7807bis` | `type`/`title`/`detail`/`instance`; **do not parse `detail`**; extensions are the safe evolution seam | no |
| RateLimit headers draft | `github.com/ietf-wg-httpapi/ratelimit-headers` | Relative window not absolute timestamp; `Retry-After` wins; thundering-herd jitter | no |
| Deprecation header | `github.com/ietf-wg-httpapi/deprecation-header` | Sunset must not precede Deprecation; the two differing serialisations | no |
| RFC 9110 §9.2.2, RFC 9421, Stripe | via search / named exception | Retry ambiguity rationale; nonce cache; replay windows and ID cursors | no |

Read-only. Nothing downloaded, cloned, or installed. **Every canonical host here was
egress-blocked**; the IETF material was read at the HTTPAPI Working Group's own editing
repositories — the authoritative sources the published RFCs are generated from, same authorship.
Three items were reachable only via search extraction and are marked lower-confidence below.

## Improvements over the references

- **Pin the idempotency scope, which the draft explicitly declines to define.** For three partners
  writing to one custody log this is a **security boundary**, not a nicety — a globally scoped key
  lets partner A collide with or replay partner B. We prescribe scope = (authenticated partner
  principal, operation, key), stated in the response so the client can reason about it.
- **Fix the 409-on-concurrent rule, which is hostile to an aggressive retrier.** The draft's answer
  to a retry arriving mid-flight is a bare error, which a retrying client simply retries, tightening
  the loop. We require the 409 to carry `Retry-After`, or to be replaced by 202 with a status
  location.
- **Distinguish definitive from indeterminate failures — the named exception teaches the wrong
  habit here.** Stripe caches 500s under the key, so a client that hit a transient fault can never
  succeed with that key again. For an append-only legal record that is unacceptable. Validation
  rejections are definitive and safe to store and replay; timeouts, 5xx and mid-write crashes are
  **indeterminate and must not be cached**, because the client's retry is the only path to a correct
  record.
- **Derive retention from the retry horizon, not from a payments default.** The draft says only
  "publish a policy". Under normal partitions between logistics partners a retry may arrive later
  than 24 hours, and a pruned key silently converts a replay into a duplicate write.
- **Supply the pagination design the standards track omits entirely.** No IETF document touches it,
  and the only reachable reference paginates reverse-chronologically with an object-ID cursor that
  works only because those IDs happen to be sortable — an undocumented assumption that shatters with
  UUIDv4. We specify a **server-assigned monotonic sequence** as the cursor (never partner-supplied
  timestamps, given disagreeing clocks) and an explicit split between a **stable snapshot read and a
  live forward tail**, which need different cursor semantics.
- **A status-code decision table.** The sources collectively offer 409, 422, 412, 428 and 429 and
  reconcile none of them; the draft's choice of 422 for same-key-different-body is asserted without
  argument. We give the table with reasoning attached.
- **Model the corrective information RFC 9457 never mentions.** The spec tells consumers not to
  parse `detail`, so "what a correct request looks like" cannot live there — it has to be extension
  members. That construction is ours to invent, and it is exactly what the capability gap names.
- **Ban `about:blank` on client-correctable errors.** The spec makes it the default, so a lazily
  built problem detail degrades to "nothing beyond the status code" without anyone noticing.
- **Close the webhook/idempotency loop nobody connects.** Signed delivery with retry is
  at-least-once, so the **receiver** needs the same duplicate suppression the sender's write path
  has — a stable delivery ID and receiver-side deduplication.
- **Deliberately left out: authentication scheme selection and transport security.** Adjacent, well
  covered elsewhere, and including them would blur the trigger.

## The skill to build

### Frontmatter
- `name:` api-contract-design
- `description:` Designs HTTP API contracts that survive misbehaving clients — idempotent writes
  that do not duplicate under retry, pagination that stays correct while data is being written,
  rate-limit and error responses a client can act on programmatically, and versioning that can be
  retired safely. Use when designing or reviewing a REST API, adding write endpoints, choosing
  status codes, paginating a collection, signing webhooks, or when retries are creating duplicate
  records.
- `allowed-tools:` Read, Write, Edit, Glob, Grep, Bash

### Body structure
1. **Decision tree** — routes to the section that matters, before any prose
2. **Idempotency has three states** — and the third is the whole problem
3. **Pagination under concurrent writes** — snapshot vs tail
4. **Errors the client can act on** — extensions, not prose
5. **Rate limits and backoff** — a shared contract, not a server-side control
6. **Webhooks** — signing, replay windows, and the receiver's duty
7. **Versioning and retirement** — signalling, and the serialisation trap
8. **Status code decision table**

### The technique it encodes

**Idempotency.** The justification to lead with: after a connection failure a client genuinely
cannot distinguish "never applied" from "applied, response lost", and it may only safely auto-retry
methods that are already idempotent. The whole mechanism exists to collapse that ambiguity
server-side.

Three states, not two. **Unseen** → process normally. **Completed** → return the stored outcome.
**In-flight** → this is the state most implementations omit, and omitting it is why concurrent
retries duplicate. Store, beside the key, a **fingerprint of the request payload**; a key replayed
with a different fingerprint is a client bug and must be rejected, not silently processed. Build the
storage lookup key as a **composite of (authenticated principal, operation, client key)** so keys
cannot collide or be replayed across partners, and require high-entropy client keys so one cannot be
guessed.

For the in-flight case, return 409 **with `Retry-After`**, or 202 with a status location — never a
bare error, which an aggressive retrier will simply retry harder.

Cache **definitive** outcomes only. A validation rejection is definitive: store and replay it. A
timeout, 5xx, or mid-write crash is **indeterminate**: do not store it, because the client's retry is
the only path to a correct record. Set retention from the partner's worst-case retry horizon, publish
it, and state what happens after expiry.

**Pagination.** Offset pagination is unstable under concurrent writes — rows shift between requests,
so a walker skips or repeats. Use a cursor over a **server-assigned monotonic sequence**. Never order
by a partner-supplied timestamp: their clocks disagree, and this is an append-only legal record.
Distinguish two reads explicitly: a **stable snapshot** (cursor pinned to a sequence ceiling captured
at first request, so the page set does not grow underneath the reader) and a **live forward tail**
(cursor advances into newly appended events). They are different endpoints or an explicit mode, never
the same call with different behaviour.

**Errors.** Use `application/problem+json`. `type` is a URI naming the *class*; **never leave it
`about:blank` on anything a client could correct**. `title` is stable per type. `detail` is prose the
consumer is told **not to parse**, so it must not be the only place actionable information lives.
Everything machine-actionable goes in **extension members**, which clients are required to ignore when
unrecognised — that is what makes the error contract safe to evolve in place. Model corrective
information as extensions: which field was wrong, what values are acceptable, and where applicable the
stored idempotency key and the retry-safe next step. For field-level failures use an `errors` array
whose entries carry a pointer at the offending field.

**Rate limits.** Advertise policy and state separately. Express the window as **relative seconds, not
an absolute reset timestamp**, so client and server clock disagreement cannot corrupt it. If
`Retry-After` is also present it **wins**. Treat the numbers as hints, not an SLA — say so in the docs,
because a compliant client may still be refused. **Add jitter to the advertised window**: a quota that
resets at a fixed wall-clock moment brings every client back simultaneously. Require full-jitter
exponential backoff on the client side, and put the same numbers in a problem-detail body as in the
headers, since nothing guarantees a client reads both.

**Webhooks.** Sign over a timestamp concatenated with the raw body, compare in constant time, and
enforce a tolerance window with a verifier-side replay cache sized to that window. Note honestly that
the standards-track answer is heavy and rarely what producers ship; borrow its ideas — explicit
creation time, explicit expiry, a nonce — rather than its full canonicalisation. Retry on a documented
backoff schedule. And because signed retry means **at-least-once delivery, the receiver needs the same
duplicate suppression the write path has**: a stable delivery ID and receiver-side deduplication.

**Versioning.** Signal retirement with `Deprecation` and `Sunset`. **The Sunset instant must not
precede the Deprecation instant.** Watch the trap: the two headers use different serialisations for
the same kind of value — one a structured-field date, the other an HTTP-date string — in headers meant
to be used together. Publish the deprecation window ahead of time and point a link relation at human
documentation.

**Status codes.** Give the table with reasoning: 409 for an in-flight duplicate (a concurrency
conflict, resolvable by waiting); 422 for a key reused with a different payload (the request is
well-formed but semantically contradictory); 400 for a missing required key (malformed request); 412
for a failed precondition; 429 for rate limiting. The point is not that these are the only defensible
choices — it is that the API picks one, documents it, and never varies.

### Reference files
- `references/idempotency.md` — the three-state algorithm, fingerprinting, retention derivation, and
  the definitive-vs-indeterminate rule. Load when adding any write endpoint.
- `references/error-bodies.md` — problem-detail shapes with worked corrective extensions. Load when
  writing error responses.

## How to tell it worked

- [ ] The same write request replayed ten times concurrently produces exactly one record
- [ ] A key replayed with a different body is rejected, not processed
- [ ] A retry arriving while the original is in flight receives a response that tells it when to
      come back
- [ ] An indeterminate failure (timeout) does not poison the key — a later retry can still succeed
- [ ] Paginating an event log while events are being appended neither skips nor repeats
- [ ] Snapshot reads and tail reads are separately addressable and documented
- [ ] Every 4xx body carries a non-`about:blank` `type` and machine-readable corrective extensions
- [ ] A rate-limited client can compute its retry time from the response alone, without a clock
      shared with the server
- [ ] A webhook receiver given the same delivery twice records it once

## Risk review

**None adversarial.** Every page behaved as ordinary technical documentation.

Three items worth recording:

1. **All canonical Tier 2 hosts were egress-blocked** — `rfc-editor.org`, `datatracker.ietf.org`,
   `httpwg.org`, `developer.mozilla.org`, `stripe.com`, `anthropic.com`. IETF material was read at
   the HTTPAPI Working Group's own editing repositories, which are the sources the published
   documents are generated from.
2. **Three claims are lower-confidence, obtained via search extraction rather than direct read**: RFC
   9110 §9.2.2's retry rule, RFC 9421's nonce-cache requirement, and Stripe's replay-window and cursor
   details. **Re-verify before relying on the specific numbers.**
3. **Search listings surfaced several non-allowlisted domains** — third-party mirrors of the Anthropic
   skills repo, a USPTO patent, an NCBI article, repackaged guides. **None was opened**; none
   contributed. Also, the Anthropic docs URL 302s to `platform.claude.com`; the redirect was followed
   manually after confirming the target host, since a redirect target is server-supplied.

## Originality attestation

- [x] Nothing was downloaded, cloned, or installed
- [x] No code or prose was copied verbatim from a source
- [x] Every technique is restated in my own words
- [x] Sources are listed above as references, credited where their idea is distinctive
- [x] Any injection attempt is recorded in the Risk review

## Build steps

1. Create `.claude/skills/api-contract-design/SKILL.md`
2. Write frontmatter as specified
3. Write the decision tree first, then sections 2–8, body under 500 lines
4. Create `references/idempotency.md` and `references/error-bodies.md`, one level deep, each with a
   table of contents if over 100 lines
5. Mark the three lower-confidence claims as pending primary-source verification
6. Read the authored file back into context
