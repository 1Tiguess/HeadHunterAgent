# Hunt notes — 09 Handoff (REST API contract design)

Scout report, reported speech. Read-only. Nothing downloaded, cloned, or installed.

## Access note

`rfc-editor.org`, `datatracker.ietf.org`, `ietf.org`, `httpwg.org`,
`developer.mozilla.org`, `stripe.com`/`docs.stripe.com` and `anthropic.com` are all
**egress-blocked**. Where a Tier 2 document was unreachable at its canonical host, the scout
read the **IETF HTTPAPI Working Group's own editing repositories on GitHub** — the
authoritative sources the published drafts and RFCs are generated from, same authorship, not
an aggregator. Two items were obtainable only second-hand through search extraction of
primary text; those are marked lower confidence and **must be re-verified before relying**.

## Tier 1 — skill construction

**`docs.claude.com/…/agent-skills/best-practices`** (302s to `platform.claude.com`).
Only `name` and `description` are resident at startup; everything else is read on demand. So
the description is **not documentation, it is a routing key**. Third person (first/second
person degrades discovery because it clashes with the surrounding system-prompt voice), both
capability and triggering conditions, carrying the literal vocabulary a user would type.
`name` ≤ 64 chars, lowercase/hyphens, cannot contain "claude" or "anthropic"; `description`
≤ 1024 chars.

Structural rules for a dense technical skill: body under ~500 lines; every reference
**exactly one level deep** from SKILL.md, because when Claude follows a reference-from-a-
reference it previews with `head -100` and silently gets partial information; any reference
over 100 lines gets a table of contents at the top.

The most transferable idea is calibrating **degrees of freedom** — a narrow bridge with
cliffs gets an exact command and an instruction not to deviate; an open field gets a
direction and trust. Fragile, sequence-dependent, consistency-critical operations get low
freedom; context-dependent judgement gets high freedom.

Body patterns named: copyable progress checklists; validate-fix-repeat loops where the
"validator" can be a script *or* a reference document Claude checks against; conditional
routing; and plan-validate-execute, where Claude emits a structured intermediate artifact
that a script checks before anything is applied. Anti-patterns: time-sensitive statements,
inconsistent terminology, four libraries instead of one default plus an escape hatch.
Evaluation-first authoring — three evals against observed baseline failures *before* prose.

**`skill-creator/SKILL.md`.** Named phases with fixed sub-step counts. Two standouts:
explicit **user sign-off gates** written into the procedure (the user decides whether test
cases are warranted, signs off on trigger queries, signals when iteration ends), and a stated
**refusal set**.

**`mcp-builder/SKILL.md`.** Four numbered phases with decimal sub-steps. Distinguishing move:
**load-timing directives** — SKILL.md states which phase each reference should be read
during. Judgement stays in SKILL.md; language-specific code lives in per-language references
never loaded together. Explicitly declines to reproduce SDK source.

**`webapp-testing/SKILL.md`.** Opens with an ASCII **decision tree** that routes before any
prose. Two-column don't/do table for the few load-bearing rules. Treats bundled scripts as
black boxes — run `--help`, do *not* read the source, a deliberate context-conservation move.

## Tier 2 — the craft

**Idempotency-Key header** (`github.com/ietf-wg-httpapi/idempotency`, published -07).
A Structured Field Item holding a string; UUIDs suggested. The draft deliberately does **not
define the uniqueness scope** — left to the resource owner to define and publish. It
introduces an **idempotency fingerprint**: a server-computed digest of the request payload
stored beside the key, used to detect a client reusing a key while changing what it asks for.

Three branches: unseen key → process normally; key seen and original finished → return the
stored outcome **including if that outcome was an error**; key seen and original still
running → **409 Conflict**. Key reused with a different fingerprint → **422**. Missing
required key → **400**. Retention left open — the resource *may* use time-bounded keys and
*must* publish its expiry policy. Applies to POST and PATCH, since GET/PUT/DELETE already
carry idempotent semantics under RFC 9110. Recommends RFC 9457 problem details for errors.
Security: validate key format, require high-entropy keys so an attacker cannot guess another
client's, and build the storage lookup key as a **composite** of the client key plus
server-known caller attributes.

**RFC 9457 Problem Details** (`github.com/ietf-wg-httpapi/rfc7807bis`).
`application/problem+json`. Five standard members. `type` is a URI naming the *class* of
problem, defaulting to `about:blank`, which explicitly means "nothing beyond the status
code". `status` duplicates the HTTP status, advisory. `title` is a stable human summary that
should not vary between occurrences except for localisation. `detail` is occurrence-specific
— and critically, **consumers are told not to parse `detail`**; machine-readable specifics
belong in extension members. `instance` identifies the occurrence.

Extension members are the extensibility mechanism and clients **must ignore unrecognised
ones**, which is what makes it safe to evolve an error contract in place. Defining a new
problem type obliges you to document the type URI, a short title, and the paired status code.
Multi-problem guidance is thin — "represent the most relevant or urgent one" — but the
document's own validation example demonstrates an `errors` extension array whose entries
carry a `detail` and a JSON Pointer at the offending field. Emphatic that problem details are
about the HTTP interface, not a debugging channel into the implementation; don't surface
stack traces.

**RateLimit / RateLimit-Policy** (`github.com/ietf-wg-httpapi/ratelimit-headers`, -11, dated
23 May 2026). Two Structured Field lists. `RateLimit-Policy` advertises policies — quota `q`,
window `w` in seconds, optional quota unit `qu` (requests / content-bytes /
concurrent-requests), optional partition key `pk`. `RateLimit` reports state against a named
policy: `r` remaining, `t` effective window, `pk`. Multiple policies listed comma-separated;
the server reports on whichever is closest to biting.

The design decision most relevant here: **`t` is a relative number of seconds, not an
absolute reset timestamp**, chosen specifically so the mechanism does not depend on client
and server clocks agreeing. The client is forbidden from assuming full quota restoration when
it expires. If both `RateLimit` and `Retry-After` are present, **`Retry-After` wins**. The
fields are hints only — not an SLA; the server may lower them arbitrarily under saturation,
may refuse despite advertised headroom, and may pair them with any status code (429 is an
example, not a mandate). Malformed fields must be ignored rather than guessed at. Explicit
warning about the **thundering herd** where a quota resets at a fixed wall-clock time and
every client returns simultaneously — recommends jitter on the advertised window. Privacy:
quota values leak infrastructure capacity, error responses that consume quota let an attacker
probe another user's traffic, and partition keys can leak identity.

**Deprecation header** (`github.com/ietf-wg-httpapi/deprecation-header`, published as RFC
9745). A Structured Field Item carrying a Date serialised as `@<epoch-seconds>`, which may
name a past or future moment. Purely informational — deprecating a resource does not alter
its behaviour. Pairs with `Sunset` (RFC 8594), and there is a hard ordering constraint: **the
Sunset instant must not precede the Deprecation instant.** A `deprecation` link relation
points at human documentation.

**Lower confidence, second-hand — re-verify:**
- **RFC 9110 §9.2.2** — the retry rule underpinning the whole problem: a client may
  automatically repeat an *idempotent* request when the connection failed before a response
  arrived, but **must not** automatically repeat a non-idempotent one unless it has an
  independent guarantee of idempotent semantics or a way to detect the original was never
  applied. §13 / If-Match: preconditions compared with the strong comparison function,
  failure yields 412; If-Match on a state-changing method is the named remedy for lost
  updates.
- **RFC 9421 HTTP Message Signatures** — signature parameters include `created` and `expires`
  as integer UNIX timestamps (no sub-second precision) and a `nonce`; verifiers are required
  to keep a nonce cache covering the validity window and should reject a repeated nonce from
  the same peer.
- **Stripe — NAMED EXCEPTION, invoked explicitly.** Stores the status code and body of the
  first request under a key and replays it verbatim, **including failures such as 500s**;
  reusing a key with different parameters is rejected as a mismatch; replay window 24 hours on
  v1, 30 days on v2, scoped to the same account and API; keys pruned after expiry cause the
  next request to be treated as new. Pagination is ID-cursor based: `starting_after` /
  `ending_before` take an existing object ID, are mutually exclusive, return
  reverse-chronologically, and the page carries `data` plus `has_more` rather than a total.

## Synthesis

**1. Idempotency has three states, not two, and the ambiguous one is the whole problem.**
Unseen, completed, and **in-flight**. Most implementations model only the first two, which is
why concurrent retries produce duplicates. The draft's answer is a stored payload fingerprint
alongside the key, a composite storage key folding in server-known caller identity, and a
distinct rejection for the in-flight case. RFC 9110 §9.2.2 supplies the justification to lead
with: after a connection failure the client genuinely cannot distinguish "never applied" from
"applied, response lost", and the entire mechanism exists to collapse that ambiguity
server-side.

**2. Every value the client must act on has to be machine-readable and clock-independent.**
RFC 9457 says explicitly not to parse `detail` and guarantees unknown extension members are
safely ignored — so extensions are the only correct place for actionable data. The RateLimit
draft independently reaches the same conclusion in the time domain by making its window
relative seconds rather than an absolute timestamp, precisely so clock disagreement cannot
corrupt it. For three partners whose clocks disagree, that principle generalises: **relative
durations in responses, server-assigned ordering in the data.**

**3. The advertised limit is a hint; the client's own discipline is the real control.** The
RateLimit draft is unusually blunt that quota values are not an SLA, that the server may
throttle a compliant client anyway, that `Retry-After` outranks the advertised window, and
that synchronised reset boundaries create thundering herds unless jitter is added.

## Improvement openings

1. **Idempotency scope is the single most important decision and no source makes it.** The
   draft delegates it to the resource owner and moves on. For three partners writing to one
   custody log, scope is a **security boundary** — a globally-scoped key lets partner A
   collide with or replay partner B. The security section gestures at a composite cache key
   without prescribing it. Pin it: scope = (authenticated partner principal, operation, key),
   stated in the response so the client can reason about it.
2. **The 409-on-concurrent rule is actively hostile to an aggressive retrier.** The draft's
   answer to a retry arriving mid-flight is an error — which a retrying client simply retries,
   tightening the loop. No backoff hint, no `Retry-After` on that 409, no alternative. Real
   opening: pair the 409 with `Retry-After`, or return 202 with a status location, or briefly
   wait and return the original result. Any beats the spec's bare answer.
3. **Caching failures is wrong for an append-only legal record, and the named exception is
   the source of the bad habit.** Stripe caches 500s under the key, so a client that hit a
   transient fault can never succeed with that key again. For immutable custody events the
   skill needs a distinction the sources do not draw: **definitively failed** outcomes
   (validation rejections) are safe to store and replay; **indeterminate** outcomes (timeouts,
   5xx, crashes mid-write) must not be, because the client's retry is the only path to a
   correct record.
4. **Retention windows are unaddressed for this failure profile.** The draft says "publish a
   policy"; Stripe says 24 hours. Under normal partitions between logistics partners, a
   partner may not retry for longer than that. Derive retention from the partner's worst-case
   retry horizon rather than copying a payments default, and say what happens after expiry —
   a pruned key silently converts a replay into a duplicate write.
5. **Pagination is completely absent from the standards track.** No IETF document touches it.
   The only reachable reference is Stripe's, a poor fit twice over: its cursor is an object ID
   that only works because those IDs happen to be sortable (an undocumented assumption that
   shatters with UUIDv4), and it paginates reverse-chronologically, the wrong direction for
   tailing an append-only log forward. Two further uncovered gaps: ordering must be by a
   **server-assigned monotonic sequence**, never partner-supplied timestamps, given
   disagreeing clocks; and the API needs an explicit distinction between a **stable snapshot
   read and a live forward tail**, which want different cursor semantics. **Largest single
   opening.**
6. **Nothing arbitrates the ambiguous status codes.** Across the sources: 409, 422, 412, 428,
   429 — and no document reconciles them. Same-key-different-body could defensibly be 409, 422
   or 400, and the draft's choice of 422 is asserted without argument. A decision table with
   the reasoning attached is exactly the artefact missing from the literature.
7. **RFC 9457's multi-error guidance is the weakest part of an otherwise crisp spec.**
   "Represent the most relevant problem" is not implementable. The `errors` array with JSON
   Pointers appears only in a non-normative example yet has become de facto convention. And
   note the gap the capability statement names directly: **9457 never says the error should
   describe what a *correct* request looks like** — `detail` is prose you are told not to
   parse, so corrective information has to be modelled as extension members. That construction
   is ours to invent.
8. **Ban `about:blank` for actionable errors.** The spec makes it the default, so a lazily
   constructed problem detail degrades to "no information beyond the status code" without
   anyone noticing. Treat an absent `type` on any client-correctable error as a defect.
9. **Webhook signing is the biggest genuine hole in the allowlist.** RFC 9421 is the only
   standards-track answer, it is heavy, and it is essentially never what webhook producers
   ship. The field practice (HMAC over timestamp concatenated with raw body, tolerance window,
   constant-time comparison) has **no reachable authoritative source at all**. Say so honestly
   and borrow only 9421's ideas: explicit `created`, explicit expiry, a nonce, and a
   verifier-side replay cache sized to the tolerance window.
10. **No source connects webhooks back to idempotency.** Signed delivery with retry means
    at-least-once delivery, so the **receiver** needs the same duplicate suppression the
    sender's write path has — a stable delivery ID plus receiver-side deduplication. Obvious
    once stated; appears in none of the sources.
11. **Versioning strategy is unsourced.** Deprecation and Sunset say how to *signal* a
    retirement; nothing takes a position on URL-path vs media-type vs header versioning. Also a
    real implementation trap: **`Deprecation` is a Structured Field Date (`@epoch`) while
    `Sunset` is an HTTP-date string** — two serialisations for the same kind of value, in
    headers meant to be used together, with a MUST-NOT-precede constraint between them.
12. **Rate-limit jitter is buried where nobody reads it.** The thundering-herd warning sits in
    considerations material, not the normative body. For aggressive retriers promote it to a
    hard rule — full-jitter exponential backoff client-side, jittered windows server-side —
    alongside a requirement that a 429 body be a 9457 problem detail carrying the same numbers
    as the headers, since nothing guarantees a client reads both.

## Injection attempts

**None.** Every page behaved as ordinary technical documentation. Two hygiene notes rather
than attacks: search listings surfaced several non-allowlisted domains (third-party mirrors
of the Anthropic skills repo, a USPTO patent, an NCBI article, repackaged guides) — **none
was opened** and none contributed. And the Anthropic best-practices URL returns a 302 to
`platform.claude.com`, followed manually after confirming the target host, since a redirect
target is server-supplied and unverified.
