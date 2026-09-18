# Problem detail bodies

Load when writing error responses.

## Contents

- [The base shape](#the-base-shape)
- [Corrective extensions](#corrective-extensions)
- [Field-level failures](#field-level-failures)
- [Rate limit bodies](#rate-limit-bodies)
- [Idempotency conflict bodies](#idempotency-conflict-bodies)
- [What never goes in](#what-never-goes-in)

## The base shape

Content type `application/problem+json`.

```json
{
  "type": "https://api.example.com/problems/invalid-parameter",
  "title": "Invalid parameter",
  "status": 400,
  "detail": "The `since` parameter must be an ISO-8601 timestamp.",
  "instance": "/custody-events?since=yesterday"
}
```

`type` is a URI identifying the **class**, not the occurrence. It does not have to resolve,
but it should — a page describing the problem class is the cheapest documentation you will
ever write.

`title` is stable for a given `type`. Do not vary it per occurrence; that is what `detail` is
for.

`status` duplicates the HTTP status and is advisory. Keep them consistent.

**Never ship `about:blank` as the type on anything a client could correct.** It is the
specified default, which means a lazily-constructed problem body degrades to "no information
beyond the status code" and nobody notices. Treat an absent `type` on a client-correctable
error as a defect in review.

## Corrective extensions

`detail` is prose the consumer is explicitly told **not to parse**. So anything the client
must act on programmatically has to live in extension members — and clients are required to
ignore extensions they do not recognise, which is what makes this safe to extend later.

The specification says how to describe what went wrong. It never says to describe **what a
correct request would look like**, and that is what the client actually needs:

```json
{
  "type": "https://api.example.com/problems/invalid-parameter",
  "title": "Invalid parameter",
  "status": 400,
  "detail": "The `since` parameter must be an ISO-8601 timestamp.",
  "instance": "/custody-events?since=yesterday",

  "parameter": "since",
  "received": "yesterday",
  "expected": "ISO-8601 timestamp",
  "example": "2026-08-18T00:00:00Z",
  "retry_safe": true
}
```

`retry_safe` is worth standardising across every error you emit. It answers the only question
an automated client really has: *should I try again, and does anything need to change first?*

Use a consistent extension vocabulary across the whole API. Three endpoints inventing three
names for "the field that was wrong" is the same problem as three tools with overlapping
descriptions.

## Field-level failures

For validation across multiple fields, use an `errors` array whose entries point at the
offending location. This appears only as a non-normative example in the specification but has
become the de facto convention — adopt it deliberately rather than inventing a fourth shape.

```json
{
  "type": "https://api.example.com/problems/validation-failed",
  "title": "Validation failed",
  "status": 422,
  "detail": "The request body failed validation. See `errors`.",
  "errors": [
    {
      "pointer": "/transfer/to_partner",
      "detail": "Unknown partner id.",
      "expected": "one of the partner ids returned by GET /partners"
    },
    {
      "pointer": "/transfer/occurred_at",
      "detail": "Timestamp is in the future.",
      "expected": "a timestamp at or before the server's current time"
    }
  ]
}
```

Report **all** failing fields, not just the first. A client fixing one at a time across
successive round trips is a bad experience and, for a retrying client, an expensive one.

The guidance for multiple simultaneous problems — "represent the most relevant or urgent" —
is not implementable as stated. The `errors` array is the practical answer.

## Rate limit bodies

Put the same numbers in the body as in the headers. Nothing guarantees a client reads both,
and whichever it reads should be sufficient on its own.

```json
{
  "type": "https://api.example.com/problems/rate-limited",
  "title": "Rate limited",
  "status": 429,
  "detail": "Quota exhausted for this partner.",
  "retry_after_seconds": 37,
  "retry_safe": true
}
```

**Relative seconds, never an absolute timestamp.** The whole point is to remove any dependency
on the client's clock agreeing with yours.

## Idempotency conflict bodies

The in-flight case, where the client needs to know this is a conflict it can wait out rather
than an error it should escalate:

```json
{
  "type": "https://api.example.com/problems/request-in-flight",
  "title": "An identical request is still being processed",
  "status": 409,
  "detail": "A request with this idempotency key is currently in progress.",
  "idempotency_key": "3f9a...",
  "retry_after_seconds": 5,
  "retry_safe": true
}
```

And the mismatch case, which is emphatically **not** retry-safe:

```json
{
  "type": "https://api.example.com/problems/idempotency-key-reused",
  "title": "Idempotency key reused with a different payload",
  "status": 422,
  "detail": "This idempotency key was already used for a different request body.",
  "idempotency_key": "3f9a...",
  "retry_safe": false,
  "remedy": "Generate a new idempotency key for a different request."
}
```

The `remedy` field carries what the client should do. Prose in `detail` cannot be parsed;
this can be surfaced directly.

## What never goes in

Problem details describe **the HTTP interface**, not your implementation:

- no stack traces or exception class names
- no SQL, no query text
- no internal hostnames, service names, or filesystem paths
- no credentials, tokens, or request URLs to upstream services
- no internal primary keys the client has no other way to see

Vet what a new problem type exposes before publishing it. A type URI that resolves to a page
describing internal architecture is an information leak with good documentation.

Genuinely generic conditions are better left as a bare status code than dressed up in a
problem body that adds nothing.
