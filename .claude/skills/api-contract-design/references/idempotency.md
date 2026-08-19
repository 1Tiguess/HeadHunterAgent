# Idempotency

Load when adding any write endpoint.

## Contents

- [The algorithm](#the-algorithm)
- [Fingerprinting](#fingerprinting)
- [Key scope](#key-scope)
- [Definitive vs indeterminate outcomes](#definitive-vs-indeterminate-outcomes)
- [Retention](#retention)
- [The in-flight race](#the-in-flight-race)

## The algorithm

On a write carrying an idempotency key:

1. Compute the payload fingerprint.
2. Atomically insert a record `(scope, key)` with status `in_flight` and the fingerprint —
   **conditional on it not already existing**.
3. **Insert succeeded** → this is the first attempt. Process the request. On completion,
   store the outcome and set status `completed`. Return the outcome.
4. **Insert failed, existing record is `completed`** → compare fingerprints. Match → return
   the stored outcome. Mismatch → 422.
5. **Insert failed, existing record is `in_flight`** → compare fingerprints. Mismatch → 422.
   Match → 409 with `Retry-After`, or 202 with a status location.

The conditional insert in step 2 is the load-bearing part. A read-then-write
check-if-exists-then-create is not equivalent: two concurrent retries both read "not found"
and both proceed. Use a unique constraint, a conditional put, or a lock — whatever your store
offers that makes step 2 a single atomic operation.

## Fingerprinting

Hash the request body plus any headers that change the semantics of the operation. Exclude
anything that varies between identical retries — the key itself, tracing headers, timestamps
the client generated per attempt.

Canonicalise before hashing: if a client re-serialises the same object with different key
ordering or whitespace, that must not read as a different request. Either canonicalise the
parsed structure, or hash the raw bytes and document that clients must send byte-identical
retries. The first is friendlier; the second is simpler and easier to defend.

Store the fingerprint, not the payload. You need to detect a difference, not reproduce the
original.

## Key scope

Scope is `(authenticated principal, operation, client key)`.

Each part earns its place:

- **Principal** — without it, one client's key can collide with another's. Where several
  parties write to a shared resource this is a security boundary: a guessed or leaked key
  would let one party replay or block another's write.
- **Operation** — without it, a client reusing a key across two different endpoints gets the
  first endpoint's cached response from the second.
- **Client key** — the part the client controls.

Require high entropy. A UUID is the obvious choice. Validate the format on arrival and reject
malformed keys with 400 rather than treating them as novel — a client sending `retry-1` as a
key has misunderstood the mechanism, and telling them early is kinder than deduplicating
against a namespace everyone is guessing.

Document the scope. A client that does not know whether keys are global or per-endpoint cannot
reason about reuse.

## Definitive vs indeterminate outcomes

**Store definitive outcomes. Never store indeterminate ones.**

| Outcome | Class | Store? |
|---|---|---|
| Success | Definitive | Yes |
| Validation rejection (4xx from your own logic) | Definitive | Yes |
| Business-rule refusal | Definitive | Yes |
| Upstream timeout | **Indeterminate** | **No** |
| 5xx from a dependency | **Indeterminate** | **No** |
| Crash between write and response | **Indeterminate** | **No** |

The reasoning: a definitive outcome will be the same every time, so replaying it is
truthful and saves work. An indeterminate outcome means *you do not know whether the write
landed* — and caching that uncertainty under the key means the client can never resolve it,
because every retry returns the cached failure instead of attempting the operation.

A widely-copied production implementation caches 5xx responses under the key. For a payments
API where a duplicate charge is worse than a stuck one, that is a defensible trade. For an
append-only record where the client's retry is the only path to a correct log, it is the
wrong one.

Practically: on an indeterminate failure, **delete the in-flight record** rather than marking
it completed, so the next retry is treated as a first attempt.

## Retention

Derive it from the client's worst-case retry horizon, not from a copied default.

Ask: how long could a client legitimately wait before retrying? A mobile client retrying on
next app launch might be hours. A partner system recovering from a network partition might be
a day or more. A batch process might retry on its next scheduled run.

Then set retention comfortably beyond that. **A key pruned too early silently converts a
replay into a duplicate write** — the exact failure the mechanism exists to prevent, arriving
later and harder to diagnose.

Publish the window, and say what happens after expiry: the key is forgotten and a request
carrying it is treated as new.

If storage cost makes a long window painful, store the fingerprint and outcome *reference*
rather than the full response body, and let the retention window be generous.

## The in-flight race

Worth being explicit about the timing, because this is the state most implementations skip.

Two identical requests arrive within milliseconds. Request A inserts the in-flight record and
begins work. Request B's conditional insert fails, it reads the record, and finds status
`in_flight`.

B must not:

- proceed with the write (that is the duplicate)
- wait indefinitely for A (that ties up a connection and may outlive A's own timeout)
- return a bare error (an aggressive retrier hot-spins on it)

B should return **409 with `Retry-After`** set to something slightly longer than the
operation's typical duration, or **202 with a status location** the client can poll.

Also handle the case where the in-flight record is stale — A crashed without completing. Give
in-flight records a lease: if the record's timestamp is older than the maximum plausible
operation duration, treat it as abandoned and take it over. Without that, a single crash makes
a key permanently unusable.
