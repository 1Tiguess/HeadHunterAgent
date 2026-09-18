# MV3 numeric limits

Load when choosing a storage area or sizing a chunk.

**Every number here is provisional.** These were gathered in August 2026 through a
summarising search layer rather than by direct read of the canonical pages, which were
unreachable from the authoring environment. Chrome's storage limits in particular have moved
across versions. Re-verify anything you are about to hardcode.

## Contents

- [How to use this file](#how-to-use-this-file)
- [Service worker timing](#service-worker-timing)
- [Storage areas](#storage-areas)
- [Sync failure semantics](#sync-failure-semantics)
- [Pages to re-check](#pages-to-re-check)

## How to use this file

**Separate the invariant from the constant.** The constants change with Chrome versions; the
invariants have held throughout and are what your design should rest on:

- Sync is small, item-capped, and rate-limited. It cannot be a store of record.
- Local is roomy and has no documented write-rate cap.
- Session is memory-backed and does not survive a browser restart.
- Two independent timers can kill the worker, and only the idle one is reset by activity.

If a number below turns out to be stale, the invariant it supports almost certainly still
holds. Design against the invariant; use the constant for sizing.

## Service worker timing

| Limit | Value | Notes |
|---|---|---|
| Idle timeout | ~30 seconds | Reset by an event or an extension API call. **Not** reset by computation that touches no extension API. |
| Hard ceiling per event or API call | ~5 minutes | Absolute. Resetting the idle timer does not extend it. |
| Slow `fetch` | ~30 seconds | A response slow enough can itself trigger termination. |

Documented life-extenders, which extend rather than defeat the rules: an active WebSocket
(sending or receiving resets the idle timer), an active `chrome.debugger` session, and a
small set of APIs that raise a user prompt — desktop capture chooser, web auth flow,
`management.uninstall()`, `permissions.request()`.

Chrome's own guidance is not to try to keep the worker alive indefinitely, and to test that
you are not doing so by accident.

**Chunk sizing.** Budget against the 30-second timer, not the 5-minute one. Aim for a chunk
that completes in a few seconds so that a slow machine still finishes inside the window.

## Storage areas

| Area | Size | Per-item | Item count | Write rate | Survives restart |
|---|---|---|---|---|---|
| `local` | ~10 MB (was 5 MB before Chrome 114) | — | — | none documented | Yes |
| `session` | ~10 MB (was ~1 MB before Chrome 112) | — | — | none documented | **No** |
| `sync` | ~100 KB | 8,192 bytes | 512 | ~120 ops/min, plus a lower sustained hourly ceiling | Yes |

Notes:

- `local` can be raised with the `unlimitedStorage` permission. Whether that draws additional
  review scrutiny is unconfirmed.
- `sync`'s per-item size is measured as the JSON stringification of the value **plus the key
  length** — long keys eat the budget.
- `session` is cleared on browser restart, extension disable, extension reload, and extension
  update. All four.
- The sustained hourly sync ceiling was described qualitatively (roughly one write every two
  seconds sustained) rather than as a named constant. Treat it as approximate.

**Sizing worked through.** A record carrying a URL, a title and a favicon URL runs on the
order of a few hundred bytes. Several hundred such records therefore approach or exceed the
entire ~100 KB sync area, and at 8 KB per item cannot fit in fewer than a low-double-digit
number of chunked items regardless of how you serialise them. This is why sync is a
projection, not a mirror.

## Sync failure semantics

This is the part that causes silent data loss, and it is not a quota detail so much as a
control-flow one.

An oversized item, a write that would breach the item count, and a write that would breach
the per-minute rate **all fail immediately**. They do not queue. They do not degrade. They do
not partially apply. The callback receives `chrome.runtime.lastError`, or the Promise
rejects.

So:

- Every sync write needs an error path. A fire-and-forget sync write is a bug.
- Coalesce writes. An extension subscribing to tab events and saving on each one will exceed
  120 operations per minute during ordinary browsing.
- On a rate-limit failure, back off and retry — do not drop the write silently, and do not
  retry immediately.

## Pages to re-check

- Service worker lifecycle: `developer.chrome.com/docs/extensions/develop/concepts/service-workers/lifecycle`
- Alarms API: `developer.chrome.com/docs/extensions/reference/api/alarms`
- Storage API: `developer.chrome.com/docs/extensions/reference/api/storage`
- Migration guidance: `developer.chrome.com/docs/extensions/develop/migrate/to-service-workers`

Two things were not confirmed at all and are worth resolving before they matter: the minimum
alarm period in current MV3, which bounds how finely you can chunk; and whether
`chrome.sessions` offers anything for restore that `chrome.tabs` does not.
