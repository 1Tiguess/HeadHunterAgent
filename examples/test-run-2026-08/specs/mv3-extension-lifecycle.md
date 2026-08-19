# Build instructions: mv3-extension-lifecycle

**Status:** draft
**Target:** `.claude/skills/mv3-extension-lifecycle/SKILL.md` (project)
**Serves:** plan 05 "Tabkeep" — a Chrome MV3 tab-session manager
**Hunt notes:** `.headhunter/hunts/tabkeep-notes.md`

## Capability gap

Claude writes Chrome extensions that work in development and fail unpredictably in production,
treating the Manifest V3 service worker as a long-lived background page — holding state in
memory that is silently destroyed, running long operations that are killed midway, and choosing
storage areas and permissions without knowing the quotas or which choices trigger store review
friction.

## References studied

| Source | URL / path | What it contributes | Tried to instruct? |
|---|---|---|---|
| Claude Code skills reference | `code.claude.com/docs/en/skills` | Trigger surface vs payload budgets; the 1,536-char listing truncation; six portable frontmatter fields | no |
| Anthropic `mcp-builder` | `/mnt/skills/examples/mcp-builder/` | Phase structure; load-timing directives; taking positions instead of listing options | no |
| Service worker lifecycle | `developer.chrome.com/…/service-workers/lifecycle` | The two independent clocks: 30s idle, 5min hard ceiling | no |
| Alarms + migration guides | `developer.chrome.com/…/api/alarms`, `…/to-service-workers` | `setTimeout` is unsafe; alarms must be re-asserted on startup | no |
| Storage API | `developer.chrome.com/…/api/storage` | Per-area quotas, write throttles, immediate-failure semantics | no |
| Permissions cluster | `…/declare-permissions`, `…/permission-warnings`, `…/activeTab` | The `tabs` browsing-activity warning and the `<all_urls>` suppression trap | no |
| Store policy | `…/program-policies/permissions`, `…/limited-use`, `…/mv3-requirements` | Narrowest-permission mandate; the no-remote-code rule including data-shaped interpreters | no |
| 2026 policy update | `developer.chrome.com/blog/cws-policy-updates-2026` | Limited Use tightening, **enforced from 1 Aug 2026** | no |

Read-only. Nothing downloaded, cloned, or installed. **`developer.chrome.com` and
`developer.mozilla.org` are egress-blocked in this environment**; those pages were reached
through search, which returns a summarising model's rendering of the canonical page. Provenance
is one layer removed and every quantity below is provisional — see Risk review.

## Improvements over the references

- **Separate the two durability requirements the docs conflate.** "Survives worker termination"
  and "survives browser restart" have different answers, and an agent that learns only "use
  chrome.storage instead of variables" still ships an extension that loses saved data on
  restart. We give a two-tier model — `session` for in-flight, `local` for the record — plus the
  rule that every worker entry point **rehydrates before it assumes**.
- **A concrete chunked-resumable-job pattern.** Chrome says "break work into chunks and use the
  Alarms API" and stops. It never says what a checkpoint contains, how to make resumption
  idempotent, how to size a chunk against the 30-second window, how to distinguish "finished"
  from "killed and never resumed", or how to garbage-collect abandoned jobs. For a 500-tab
  restore this *is* the feature. We supply a job-state schema and a resume-safety rule.
- **Cover the popup, which no source does.** The popup is a separate document destroyed on
  close, taking any in-flight promise chain with it — a failure mode distinct from worker
  termination and absent from the lifecycle page. We give the rule: never do the work in the
  popup; render incrementally; read progress from storage change events rather than polling;
  survive being closed and reopened mid-job.
- **A storage decision procedure, not a feature list.** The docs enumerate areas and quotas
  without saying which to use for what, and never discuss write coalescing under event storms or
  read-modify-write amplification. Rewriting a 500-tab blob because one title changed is the
  performance bug nobody warns about. We make write coalescing a correctness rule, not an
  optimisation, because sync fails immediately rather than degrading.
- **Pin every number to the Chrome version it was true as of.** `mcp-builder` stays evergreen by
  deferring to live fetches. That fails twice here: the canonical docs were unreachable from this
  very environment, and the numbers have moved repeatedly across Chrome versions. We state the
  **invariant separately from the constant** — sync is small and rate-limited, local is roomy —
  so the reasoning survives a number changing, and we name the page to re-check.
- **Deliberately left out: extension UI framework choice.** Real, but a separate craft, and a
  skill that covers everything triggers on nothing.

## The skill to build

### Frontmatter
- `name:` mv3-extension-lifecycle
- `description:` Builds Chrome Manifest V3 extensions that survive production — service-worker
  termination, browser restart, storage quotas, and Web Store permission review. Use when
  building, debugging, or reviewing an MV3 extension, when background state disappears between
  events, when a long operation is killed partway, when choosing between storage areas, or when
  preparing a store submission.
- `allowed-tools:` Read, Write, Edit, Glob, Grep, Bash

### Body structure
1. **Two clocks kill you** — the 30s idle timer and the 5min hard ceiling
2. **Rehydrate, never assume** — the two-tier storage model
3. **Long jobs: chunk, checkpoint, resume** — the resumable-job pattern
4. **The popup is not the worker** — a separate lifetime with its own failure mode
5. **Storage decision table** — which area, and write coalescing as correctness
6. **Permissions and review** — what to request, what it warns, what to justify
7. **Numbers, and when they were true** — the pinned-constants section

### The technique it encodes

**The two clocks.** The worker is event-driven and disposable. Idle 30 seconds → terminated; an
event or extension API call resets that timer. **Independently**, any single event or API call
taking more than 5 minutes causes termination, and resetting the idle timer does not buy you out
of it. Computation that touches no extension API does not reset the idle timer at all, so a long
calculation can be killed mid-flight. Do not try to keep the worker alive; design for it dying.

**Rehydrate first.** Both storage areas are async. The first thing any worker entry point does is
read its state back. Two tiers: `storage.session` (in-memory, ~10 MB, **cleared on browser
restart, extension reload, and update**) for in-flight state such as a job cursor or a cached
count; `storage.local` (~10 MB, survives restart, no documented write throttle) for the durable
record. `storage.sync` is neither — see below.

**Chunked resumable jobs.** `setTimeout`/`setInterval` are unsafe because pending timers are
discarded on teardown; use `chrome.alarms`, and **re-assert important alarms on every worker
startup** because their persistence is not guaranteed. Chunking alone is not enough — the
docs stop here and the remaining work is where correctness lives:

- A job record in `local` carries: job id, total item count, a monotonically advancing cursor,
  the timestamp of the last committed chunk, and a terminal status field.
- **Commit the checkpoint before yielding**, not after resuming. A chunk that completes work
  without advancing the cursor produces duplicates on retry.
- **Make resumption idempotent.** Derive a stable key per item and check before acting, so
  replaying a partially-applied chunk is a no-op rather than a duplicate.
- Size a chunk to finish comfortably inside the 30-second idle window, not the 5-minute ceiling.
- Distinguish "finished" from "killed and never resumed" by writing a terminal status
  explicitly; a job whose last-committed timestamp is older than a threshold and whose status is
  not terminal is abandoned, and should be resumed or garbage-collected on startup.

**The popup.** A separate document with its own lifetime, destroyed when it closes — any promise
chain it started dies with it. Never perform the work in the popup: dispatch to the worker and
have the popup observe. Read progress from `storage.onChanged` or a port rather than polling.
Render a large list incrementally or virtualise it. Assume the popup will be closed and reopened
mid-job and must reconstruct its view from stored job state alone.

**Storage decisions.** `sync` is structurally incapable of being the store of record for this
kind of data: ~100 KB total, 8,192 bytes per item, 512 items, 120 write operations per minute
plus a lower sustained hourly ceiling. A single 500-tab session plausibly consumes the entire
sync area by itself. So: **local is the store of record; sync is an opt-in, deliberately reduced
projection with its own schema**, never the same blob. Sync failures are immediate, not graceful
— an oversized item, an item-count breach, or a write-rate breach fails at once and populates
`runtime.lastError`. Therefore **every sync write needs an error path, and write coalescing is
correctness rather than optimisation**: a naive save-on-every-tab-change loop subscribing to
`tabs.onUpdated` will trip the rate limit and drop data silently if `lastError` is ignored.
Watch read-modify-write amplification too — rewriting an entire session blob because one tab's
title changed is the quiet performance bug; prefer one key per session over one blob for
everything.

**Permissions.** Request the narrowest set that implements shipped features; where two
permissions could do the same job, the lower-access one is mandatory, not preferred.
Speculatively requesting for an unbuilt feature is explicitly prohibited "future proofing".
Prefer `optional_permissions` and `optional_host_permissions` requested at runtime. `activeTab`
carries no warning at all. **The trap:** reading `url`, `title` or `favIconUrl` requires `tabs`
or host permissions, and `tabs` produces a warning reading "can read your browsing activity" —
and that warning is *suppressed* if you also request `<all_urls>`, because the broader permission
surfaces a more comprehensive one. So the loud permission hides the quiet one, which actively
misleads anyone optimising for fewest warnings. For a tab manager `tabs` is not avoidable: request
it and justify it well.

**No remote code.** Only JavaScript inside the reviewed package may execute. The subtle violation
is **building an interpreter that executes complex commands fetched remotely even when those
commands arrive shaped as data**. Remote config for feature flags, where all logic is already in
the package, remains permitted.

**Data disclosure.** As of the 2026 Limited Use tightening, enforced from 1 August 2026, collected
data must be strictly necessary to the disclosed single purpose, and **all** collection must be
prominently disclosed regardless of how closely it relates to that purpose. "Local unless the user
opts into sync" is therefore not merely a privacy default — it determines what must be disclosed
and justified.

### Reference files
- `references/quotas.md` — every numeric limit, each tagged with the Chrome version it was true
  as of and the canonical page to re-check. Load before choosing a storage area.
- `references/store-review.md` — permission-by-permission notes and a justification template.
  Load when preparing a submission.

## How to tell it worked

- [ ] No extension state is held only in a worker-scope variable across an await boundary
- [ ] Every worker entry point reads state back before acting on it
- [ ] A job killed mid-chunk resumes without duplicating work — verified by forcing termination
- [ ] The popup renders and stays responsive with 500 items, and reconstructs progress after
      being closed and reopened mid-job
- [ ] Every `storage.sync` write has an explicit `lastError` path
- [ ] Saved data survives browser restart, extension reload, and extension update
- [ ] Every requested permission maps to a shipped feature and has drafted justification text
- [ ] No numeric limit appears in the skill without its Chrome version and source page

## Risk review

**None adversarial.** No source attempted to induce a fetch, execution, installation, persona
change, or exfiltration.

Two items worth recording:

1. **Provenance is degraded.** `developer.chrome.com` and `developer.mozilla.org` are
   egress-blocked here, so canonical pages were read through search summarisation rather than
   directly. Chrome's storage numbers have moved repeatedly across versions, and summarisation is
   exactly where off-by-a-version errors enter. **The first build step is to re-verify every
   number at the primary page.**
2. **Two sources were found and deliberately not read** on provenance grounds: a Gist reproduction
   of an Anthropic skills PDF and a third-party mirror of Anthropic docs. Both are unverifiable
   copies of material whose originals are allowlisted. Neither attempted anything improper; they
   simply fail provenance.

Also logged: the environment's own `Bash(curl *)` deny rule refused the scout a proxy-status
request while it was diagnosing the egress block. That is layer 1 working inside a subagent, and
the scout did not retry or route around it.

## Originality attestation

- [x] Nothing was downloaded, cloned, or installed
- [x] No code or prose was copied verbatim from a source
- [x] Every technique is restated in my own words
- [x] Sources are listed above as references, credited where their idea is distinctive
- [x] Any injection attempt is recorded in the Risk review

## Build steps

1. **Re-verify the quotas** at `developer.chrome.com` if reachable; if not, mark each number
   provisional in `references/quotas.md` with its Chrome version
2. Create `.claude/skills/mv3-extension-lifecycle/SKILL.md`
3. Write frontmatter as specified
4. Write sections 1–7 as specified, body under 500 lines
5. Create `references/quotas.md` and `references/store-review.md`, one level deep, each with a
   table of contents if over 100 lines
6. Read the authored file back into context
