# Retry classification

## Contents
- [The ternary classifier](#the-ternary-classifier)
- [Why unknown must exist](#why-unknown-must-exist)
- [HTTP](#http)
- [gRPC](#grpc)
- [DNS](#dns)
- [Databases](#databases)
- [Queues and messaging](#queues-and-messaging)
- [Subprocesses and the filesystem](#subprocesses-and-the-filesystem)
- [Idempotency: the second half of the answer](#idempotency-the-second-half-of-the-answer)

## The ternary classifier

```
classify(error, operation) -> RETRYABLE | NOT_RETRYABLE | UNKNOWN
```

Two inputs, not one. **The error alone never decides.** A 503 on an idempotent GET is retryable; the
same 503 on a non-idempotent POST is not, unless the operation carries an idempotency key.

```python
def classify(error, operation):
    if not operation.safe_to_repeat:
        return NOT_RETRYABLE          # regardless of the error
    if error.code in KNOWN_RETRYABLE:
        return RETRYABLE
    if error.code in KNOWN_FATAL:
        return NOT_RETRYABLE
    return UNKNOWN                     # defer; do not guess
```

`UNKNOWN` should surface — log it with the code, and treat it as not-retryable *for this call* while
flagging that the classifier needs extending. That is different from silently defaulting, because it
tells you the table is incomplete.

## Why unknown must exist

A binary classifier has to pick a default, and both defaults are wrong:

- **Default retryable** — you retry operations that already succeeded and re-run their side effects.
- **Default not-retryable** — a transient error you did not enumerate becomes a user-visible failure.

Ternary lets the classifier be honestly incomplete. Most hand-rolled retry code is binary and
defaults to retryable, which is the more damaging of the two.

## HTTP

| Condition | Class | Why |
|---|---|---|
| Connection refused / connect failure | **Retryable** | Never reached the server; no side effect is possible |
| TLS handshake failure | Retryable | Same — nothing was processed |
| Read timeout | **Unknown** | The server may have processed it. Retryable **only** with an idempotency key |
| 408 Request Timeout | Retryable | The server says it did not get a complete request |
| 409 Conflict | **Retryable** | The one retryable 4xx — the state may have settled |
| 425 Too Early | Retryable | Explicitly a "try again" |
| 429 Too Many Requests | Retryable — **honour `Retry-After`** | Backoff is being dictated to you |
| **500 Internal Server Error** | **Usually not** | The server processed and failed. Retrying re-runs the failure and any side effects |
| 501 Not Implemented | Not retryable | Will never work |
| **502 Bad Gateway** | **Retryable** | An intermediary failed; the origin may be fine |
| **503 Service Unavailable** | **Retryable** — honour `Retry-After` | Explicitly temporary |
| **504 Gateway Timeout** | **Retryable** | An intermediary timed out |
| 400, 401, 403, 404, 405, 422 | Not retryable | The request is wrong; repeating it changes nothing |
| Request cancelled by caller | **Not retryable** | The caller already gave up. Retrying serves nobody |

**The 500/503 distinction is the one most code gets wrong.** They look adjacent and behave
oppositely.

## gRPC

| Code | Class |
|---|---|
| `UNAVAILABLE` | Retryable |
| `DEADLINE_EXCEEDED` | Unknown — the server may still be working |
| `RESOURCE_EXHAUSTED` | Retryable with backoff |
| `ABORTED` | Retryable |
| `INTERNAL`, `UNKNOWN`, `DATA_LOSS` | Not retryable |
| `INVALID_ARGUMENT`, `NOT_FOUND`, `PERMISSION_DENIED`, `UNAUTHENTICATED`, `FAILED_PRECONDITION` | Not retryable |
| `CANCELLED` | Not retryable |

## DNS

| Condition | Class |
|---|---|
| `SERVFAIL`, timeout, no reachable resolver | **Retryable** |
| `NXDOMAIN` | **Not retryable** — the name does not exist |
| `NODATA` | Not retryable for that record type |

Retrying NXDOMAIN is a common and pointless source of load.

## Databases

| Condition | Class | Note |
|---|---|---|
| Connection failure before the statement | Retryable | Nothing executed |
| **Deadlock detected** | **Retryable** | The engine aborted one transaction *specifically so* it could be retried |
| Serialization failure | Retryable | Same reasoning |
| Lock timeout | Retryable with backoff | Contention may clear |
| Statement timeout | **Unknown** | The statement may have partially applied unless it was in a transaction |
| Constraint violation | Not retryable | Deterministic |
| Syntax or permission error | Not retryable | Deterministic |

Deadlock is the case people wrongly treat as fatal. It is the engine's designed signal to retry.

## Queues and messaging

| Condition | Class |
|---|---|
| Broker unreachable on publish | Retryable |
| Publish acknowledgement timeout | **Unknown** — may have been accepted. Requires a dedup key |
| Consumer handler failure | Depends on the handler; classify per failure, not per handler |
| Message repeatedly failing | **Not retryable after N — dead-letter it** |

## Subprocesses and the filesystem

| Condition | Class |
|---|---|
| `ETIMEDOUT`, `EAGAIN`, `EWOULDBLOCK` | Retryable |
| `ECONNRESET`, `EPIPE` | Retryable if the operation is safe to repeat |
| `ENOSPC`, `EACCES`, `ENOENT` | Not retryable without intervention |
| Non-zero exit with no classification | **Unknown** — do not guess from the exit code alone |
| Killed by signal (OOM) | Not retryable unchanged — it will be killed again |

## Idempotency: the second half of the answer

Every `UNKNOWN` above becomes `RETRYABLE` the moment the operation carries a stable idempotency key
that the server honours. That is the highest-leverage change available: it converts the largest
class of un-retryable failures into retryable ones.

Three ways to get there:

1. **Client-generated idempotency key**, sent as a header, stored server-side with the response, and
   replayed rather than re-executed on a repeat.
2. **Natural idempotency** — `PUT` of a full representation, `DELETE`, or any write whose effect is
   "set to this value" rather than "add this much".
3. **A deterministic key derived from the work item**, checked before acting. This is what makes
   checkpointed resumption safe.

Absent all three, a read timeout on a write is genuinely unknown and must not be retried.
