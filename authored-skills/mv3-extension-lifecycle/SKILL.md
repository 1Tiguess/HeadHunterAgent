---
name: mv3-extension-lifecycle
description: >-
  Builds Chrome Manifest V3 extensions that survive production — service-worker termination,
  browser restart, storage quotas, and Web Store permission review. Use when building,
  debugging, or reviewing an MV3 extension, when background state disappears between events,
  when a long operation is killed partway through, when choosing between chrome.storage
  local, session and sync, when a popup freezes on large data, or when preparing a Chrome
  Web Store submission and writing permission justifications.
allowed-tools: Read, Write, Edit, Glob, Grep, Bash
---

# MV3 extension lifecycle

The service worker is not a background page. It is disposable, it is killed aggressively,
and everything you left in memory is gone. Almost every MV3 bug that only appears in
production traces back to code written as though that were not true.

> **Numbers in this skill are pinned to a Chrome version.** They have moved repeatedly.
> `references/quotas.md` carries each limit with the version it was true as of and the page
> to re-check. Where a number matters to a design decision, check it.

## 1 — Two clocks kill you, and only one is defeated by activity

- **30-second idle timer.** No events, no extension API calls for 30 seconds → terminated.
  An event or an extension API call resets it.
- **5-minute hard ceiling.** Any *single* event or API call that takes longer than about
  five minutes to settle → terminated. **Resetting the idle timer does not buy you out of
  this one.**

Two consequences people miss. Computation that touches no extension API does not reset the
idle timer at all, so a long pure-JS calculation can be killed mid-flight. And a `fetch()`
whose response is slow enough can trigger termination on its own.

Do not try to keep the worker alive. Design for it dying.

## 2 — Rehydrate, never assume

Both storage areas are asynchronous. **The first thing any worker entry point does is read
its state back.** A module-scope variable that survived the last event is a coincidence,
not a guarantee.

Two tiers, and conflating them is the single most common MV3 data-loss bug:

| | `storage.session` | `storage.local` |
|---|---|---|
| Lives in | Memory | Disk |
| Survives worker termination | Yes | Yes |
| Survives **browser restart** | **No** | Yes |
| Also cleared by | Extension reload, extension update | — |
| Use for | In-flight state: job cursors, cached counts, request dedup | The durable record |

"Survives worker termination" and "survives browser restart" are different requirements
with different answers. An agent that learns only "use `chrome.storage` instead of
variables" still ships an extension that loses everything on restart.

`storage.session` is not exposed to content scripts by default; `setAccessLevel()` changes
that. Leave it closed unless a content script genuinely needs it.

## 3 — Long jobs: chunk, checkpoint, resume

`setTimeout` and `setInterval` are unsafe in a worker — pending timers are discarded on
teardown. Use `chrome.alarms`, which fires even if the worker shut down in the interim.
**Re-assert important alarms on every worker startup**, because their persistence is not
guaranteed.

Chunking alone is not enough. Most guidance stops at "break the work into chunks and
schedule continuation", and everything that makes it *correct* is in what follows.

A job record in `storage.local` carries:

- a job id
- the total item count
- a monotonically advancing cursor
- the timestamp of the last committed chunk
- an explicit status field with a terminal value

Four rules:

1. **Commit the checkpoint before yielding, not after resuming.** A chunk that completes
   work without advancing the cursor produces duplicates on retry.
2. **Make resumption idempotent.** Derive a stable key per item and check before acting, so
   replaying a partly-applied chunk is a no-op rather than a duplicate.
3. **Size a chunk to finish inside the 30-second idle window**, not the five-minute ceiling.
   You are budgeting against the timer that fires first.
4. **Write a terminal status explicitly.** "Finished" and "killed and never resumed" are
   otherwise indistinguishable. On startup, a job whose status is non-terminal and whose
   last-committed timestamp is older than a threshold is abandoned: resume it or garbage-
   collect it.

Restoring several hundred tabs is precisely the operation that dies here, and it dies in the
worst way — partially, with some tabs created and no record of where it stopped.

## 4 — The popup is not the worker

The popup is a **separate document with its own lifetime**, destroyed the moment it closes.
Any promise chain it started dies with it. This is a distinct failure mode from worker
termination and is not covered by lifecycle documentation.

Four rules:

- **Never do the work in the popup.** Dispatch to the worker; the popup observes.
- **Read progress from `chrome.storage.onChanged` or a port**, not by polling.
- **Render large lists incrementally or virtualise them.** A synchronous render of several
  hundred rows is what "the popup froze" actually means.
- **Assume the popup will be closed and reopened mid-job** and must reconstruct its entire
  view from stored job state alone.

## 5 — Storage decisions

`storage.sync` cannot be the store of record for anything substantial. Its limits are
structural, not tuning: roughly 100 KB total, about 8 KB per item, a few hundred items, and
a write-rate cap of around 120 operations per minute plus a lower sustained hourly ceiling.
A single large session can consume the entire sync area by itself.

So the shape is forced:

- **`local` is the store of record.**
- **`sync` is an opt-in, deliberately reduced projection with its own schema** — never the
  same blob written to a second place.

**Sync failures are immediate, not graceful.** An oversized item, an item-count breach, or a
write-rate breach fails at once and populates `chrome.runtime.lastError`. Nothing queues,
degrades, or partially applies. Therefore:

- **Every sync write needs an error path.** Ignoring `lastError` is how data disappears
  silently.
- **Write coalescing is correctness, not optimisation.** An extension subscribing to
  `tabs.onUpdated` and saving on every change will trip the per-minute limit under ordinary
  browsing and start dropping writes. Debounce and batch.

Watch read-modify-write amplification too: rewriting an entire multi-hundred-item blob
because one item's title changed is the quiet performance bug. Prefer one key per logical
record over one blob for everything — it costs a little indexing and saves the rewrite.

## 6 — Permissions and review

Request the narrowest set that implements features you have actually shipped. Where two
permissions could do the same job, **the lower-access one is mandatory, not preferred**.
Requesting speculatively for an unbuilt feature is explicitly prohibited.

Prefer `optional_permissions` and `optional_host_permissions`, requested at runtime.
`activeTab` carries no warning at all and grants scoped access to the current tab on user
invocation.

**The trap.** Reading a tab's `url`, `title` or `favIconUrl` requires the `tabs` permission
or host permissions, and `tabs` produces a warning that reads as *"can read your browsing
activity"* — because across all tabs over time, that is what it amounts to. That warning is
**suppressed if you also request `<all_urls>`**, since the broader permission surfaces a more
comprehensive one. So the loud permission hides the quiet one. Anyone optimising for "fewest
warnings" will be led exactly the wrong way. For a tab manager, `tabs` is unavoidable:
request it, and justify it well.

Load `references/store-review.md` when preparing a submission.

**No remote code.** Only JavaScript inside the reviewed package may execute. The subtle
violation is **building an interpreter that executes complex commands fetched remotely, even
when those commands arrive shaped as data**. Remote config for feature flags, where all logic
already ships in the package, remains permitted.

**Disclosure.** Under the Limited Use rules in force since 1 August 2026, collected data must
be strictly necessary to the disclosed single purpose, and **all** collection must be
prominently disclosed regardless of how closely it relates to that purpose. "Local unless the
user opts into sync" is therefore not merely a good default — it determines what you must
disclose and justify.

## Reference files

| File | Contents | Load when |
|---|---|---|
| `references/quotas.md` | Every numeric limit, tagged with its Chrome version and source page | Choosing a storage area or sizing a chunk |
| `references/store-review.md` | Permission notes and a justification template | Preparing a Web Store submission |

## Done means

- No state is held only in a worker-scope variable across an await boundary
- Every worker entry point reads state back before acting
- A job killed mid-chunk resumes without duplicating work — verify by forcing termination
  from `chrome://serviceworker-internals`
- The popup stays responsive at full data volume and reconstructs progress after being closed
  and reopened mid-job
- Every `storage.sync` write has an explicit `lastError` path
- Data survives browser restart, extension reload, and extension update
- Every requested permission maps to a shipped feature and has drafted justification text
- No numeric limit appears in the code without its Chrome version recorded nearby
