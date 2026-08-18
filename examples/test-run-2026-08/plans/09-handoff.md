# 09 — Handoff

**REST service for transferring custody of physical shipments between carriers.**

## Problem

Three logistics partners currently reconcile handovers by email and spreadsheet. Disputes
about who had the package when take days to resolve. They want an API each partner's system
can call, producing one authoritative timeline.

## Who it's for

Integration engineers at three partner companies, working from the docs, in different time
zones, who will call the API wrongly at first and need the errors to teach them.

## Scope

- Resources: shipments, custody events, partners, disputes
- Custody transfer as an append-only event log; current holder is derived, never edited
- Authentication per partner, with scoped permissions
- Idempotent writes — a retried transfer must not create a second event
- Cursor pagination over event history
- Filtering and sorting on the collection endpoints
- Webhooks for custody change, with signed payloads and retry with backoff
- Explicit API versioning, and a documented deprecation policy
- Rate limiting with headers that tell the client what to do
- OpenAPI document generated from the implementation, not maintained beside it

## Out of scope

A UI, billing, a mobile app, real-time tracking, route optimisation.

## Constraints

Partners retry aggressively and their clocks disagree. Network partitions are normal.
Event history is legally significant and immutable once written. p99 under 200ms for reads.

## Success criteria

- The same transfer request replayed ten times produces exactly one custody event
- Pagination is stable while new events arrive during the walk
- A rate-limited client can compute exactly when to retry from headers alone
- Every 4xx response says what was wrong and what a correct request looks like
- Webhook signatures verify, and a failing receiver is retried on a documented schedule
- The OpenAPI document never disagrees with the implementation

## The hard part

API contract design under retry and partition. Idempotency keys have a specific correct
implementation — scope, storage duration, what happens when the same key arrives with a
different body, what to return on replay — and most implementations get at least one of
those wrong. Cursor pagination has to stay stable under concurrent writes, which offset
pagination cannot do. Webhook signing, replay-window handling, and retry schedules are
security-relevant and easy to do subtly wrong. Versioning and deprecation policy are
decisions that are expensive to revisit once partners depend on them.

## Predicted verdict

**HUNT.** Squarely `triage-rubric.md:35`: an API with more than a couple of endpoints, in a
domain with established craft. The idempotency and pagination semantics in particular have
converged answers I can gesture at but not specify precisely.

**Verified sources for the hunt:** `datatracker.ietf.org` (RFC 9110 HTTP semantics, RFC
9457 problem details for HTTP APIs, the draft idempotency-key header specification),
`stripe.com/docs` on idempotency keys and cursor pagination — the canonical production
implementation that the draft RFC itself descends from, admissible as a named primary
source rather than an aggregator.
