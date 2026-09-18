# Error taxonomy and scrubbing

Load when writing error paths for an MCP tool.

## Contents

- [The three classes](#the-three-classes)
- [Message templates](#message-templates)
- [Choosing a class](#choosing-a-class)
- [Scrubbing outbound error text](#scrubbing-outbound-error-text)
- [Where errors travel](#where-errors-travel)

## The three classes

Every failure a tool can produce belongs to exactly one. The message must make the class
unambiguous, because the model's next action depends entirely on it.

| Class | The model should | Typical causes |
|---|---|---|
| `fix-arguments` | Re-issue with different input | Validation failure, unknown id, out-of-range value, mutually exclusive options, missing required field |
| `retry-after-delay` | Re-issue the same call later | Upstream timeout, rate limit, service starting, lock contention |
| `stop-and-escalate` | Stop and tell the user | Auth failure, permission denied, backend unreachable, misconfiguration, unsupported operation |

The classes are about **who can fix it**: the model, time, or a human. Nothing else.

## Message templates

Keep them short. The model reads these under context pressure.

**fix-arguments** — name the parameter, say what was wrong, give a valid example.

    Invalid `since`: expected an ISO-8601 timestamp, got "yesterday".
    Example: "2026-08-18T00:00:00Z". Re-issue with a corrected value.

    Unknown service "meda". Known services: media, backups, monitoring.
    Re-issue with one of those.

**retry-after-delay** — give a concrete duration, never "later".

    The monitoring backend did not respond within 5s. This is usually transient.
    Retry the same call in about 30 seconds.

**stop-and-escalate** — say plainly that retrying will not help.

    The backups backend refused the request: the configured credential is not
    accepted. Retrying will not help — this needs the server's configuration
    corrected by a human. Report this to the user rather than retrying.

Note what the last one does *not* say: it does not name the credential, the header it was
sent in, or the URL it was sent to.

## Choosing a class

Ambiguous cases, resolved:

- **HTTP 401/403 from a backend** → `stop-and-escalate`. The model cannot mint credentials.
- **HTTP 404 for a user-supplied id** → `fix-arguments`. The model chose the id.
- **HTTP 404 for a path the server constructed** → `stop-and-escalate`. Server misconfiguration.
- **HTTP 429** → `retry-after-delay`, using the upstream's retry hint if it gave one.
- **HTTP 5xx** → `retry-after-delay` on first occurrence; `stop-and-escalate` if the server
  has already seen it fail repeatedly within a short window. Track this server-side; the
  model has no memory across calls it can rely on for this.
- **Connection refused** → `stop-and-escalate`. The service is down, not slow.
- **Response too large** → **not an error at all.** Truncate, return the data, and say what
  to narrow. See `pagination.md`.

## Scrubbing outbound error text

The rule is a whitelist. Build the error message from fields you explicitly chose; never
interpolate an exception, a URL, or a response body wholesale.

**Never emit:**

- the outbound request URL or any part of its query string
- request headers, in any form
- raw exception text or stack traces from the HTTP client
- the response body of an auth failure
- environment variable names or values
- filesystem paths internal to the server

**Safe to emit:** the backend's logical name, the HTTP status class, a duration, the
parameter the caller supplied, and your own message text.

The specific hazard: many self-hosted and home-lab APIs authenticate by query parameter
rather than header. An upstream failure echoed with its request URL therefore leaks the
credential straight into the model's transcript — and from there into logs, and possibly
into a user-visible reply. Storing the key in an environment variable does nothing to
prevent this, because the leak happens on the way out, not at rest.

Implement it as a single function every error path routes through:

    make_error(class, backend_name, message, parameter=None)

If a code path can construct an error message any other way, that path is the bug.

## Where errors travel

Failures **inside a working tool** are returned as a successful result carrying an error
flag and human-readable text. Malformed requests — unknown tool name, invalid JSON-RPC —
are protocol errors.

The distinction matters because a result reaches the model and a protocol error generally
does not. Putting a recoverable failure on the transport channel makes it invisible exactly
when visibility is the point.

So: schema-invalid input is a protocol error; semantically wrong input that your handler
detected is a `fix-arguments` result. When in doubt, prefer the result — an error the model
can read is always more useful than one it cannot.
