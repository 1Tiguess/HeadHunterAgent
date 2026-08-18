# Hunt notes — 05 Tabkeep (Chrome MV3 extension)

Scout report, reported speech. Read-only. Nothing downloaded, cloned, or installed.

## Read-channel caveat — affects how far the numbers can be trusted

Direct fetch of `developer.chrome.com` and `developer.mozilla.org` is **blocked by this
environment's egress proxy**. The scout could not read those canonical pages as documents.
It reached them through the search tool, which returns a summarising model's rendering of
those exact pages. The URLs are canonical and allowlisted; the *fidelity* is one layer
removed. It did not substitute an aggregator to route around the block — it flagged the
weakness instead, and lists re-verification as the first improvement opening.

**Every quantity below is therefore provisional.** The authored skill must pin numbers with
the Chrome version they were true as of, and name the page to re-check.

## Tier 1 — skill construction

**`code.claude.com/docs/en/skills`** — Claude Code's skill authoring reference.

The page says the trigger surface and the payload are two different things with two
different budgets. Only `name` + `description` sit in context at all times; the body loads
on demand. Front-load the `description` with the primary use case, because `description`
and `when_to_use` are concatenated and truncated at 1,536 characters in the listing — put
anything late in the description and it may never be seen at trigger time. Once a skill
loads, its content persists across turns, so every line is a *recurring* token cost, not a
one-time one. State what to do rather than narrating how or why. Ceiling: SKILL.md under
500 lines, detail pushed to sibling files. Supporting files only work if SKILL.md says what
each contains and when to load it — a referenced file the parent doesn't characterise won't
be loaded at the right moment.

Portability constraint: if a skill is ever uploaded to claude.ai, used via the Skills API,
or packaged with `package_skill.py`, only six frontmatter fields validate — `name`,
`description`, `license`, `compatibility`, `metadata`, `allowed-tools`. Anything else
hard-errors on those paths. Claude Code accepts all six, so spec-conformant frontmatter is
the portable choice.

**`/mnt/skills/examples/mcp-builder/SKILL.md`** — read on local disk (see Finding #4).
Studied purely as a worked specimen of the closest structural analogue: a skill teaching an
agent to build software against an external platform spec with non-obvious failure modes.

Its `description` is two sentences doing two jobs — the first states artifact and quality
bar together, the second is pure trigger surface, naming the situation and then enumerating
concrete stacks so a prompt mentioning the SDK matches even when it never says "MCP
server". The body is ~236 lines, four numbered phases with two-level decimal subsections.
Reference files are named inline at point of use *and* again in a consolidated library at
the end with a summary of each — so a reader arriving mid-document and one arriving at the
end both get routed. Directory shape: SKILL.md + `reference/` (volume: code patterns,
per-language checklists) + `scripts/` (things to run rather than read).

Two moves worth lifting: it **takes positions instead of listing options** (names a
recommended language and transport, reasoning compressed to a parenthetical) and says so
explicitly where it genuinely cannot decide; and its final phase is **verification, not
construction** — the job is not done when the code exists.

Its notable weakness, and it matters here: it delegates the actual spec to live fetches
rather than pinning facts in the skill.

## Tier 2 — the craft

**Service worker lifecycle** (`developer.chrome.com/.../service-workers/lifecycle`).
The worker is event-driven and disposable. Idle 30 seconds → killed; an event or an
extension API call resets that timer. **Separately and independently**, any single event or
API call taking longer than 5 minutes to settle causes termination — a hard ceiling that
resetting the idle timer does not buy you out of. A `fetch()` whose response takes over 30
seconds can also trigger termination. Computation that does not touch an extension API does
not reset the idle timer, so a long calculation can be killed mid-flight.

Documented life-extending exceptions: an active WebSocket (sending/receiving resets the
idle timer), an active `chrome.debugger` session, and a specific set of user-prompting APIs
permitted past the 5-minute cap — `desktopCapture.chooseDesktopMedia()`,
`identity.launchWebAuthFlow()`, `management.uninstall()`, `permissions.request()`. The
docs' posture is that you should not try to keep the worker alive indefinitely.

**Alarms** (`.../reference/api/alarms`, `.../migrate/to-service-workers`).
`setTimeout`/`setInterval` are unsafe in a worker because pending timers are discarded on
teardown. `chrome.alarms` is the documented replacement — it fires even if the worker shut
down, waking it. The docs caution that alarms may not persist reliably and recommend
re-asserting important alarms on every worker startup. General instruction for work that
outlives a worker: persist state, chunk the work, schedule continuation via alarms.

**Storage** (`.../reference/api/storage`) — where the numbers live.

| Area | Size | Persistence | Notes |
|---|---|---|---|
| `local` | ~10 MB (5 MB pre-Chrome 114) | survives restart | raisable via `unlimitedStorage`; **no documented write-rate throttle** |
| `session` | ~10 MB (~1 MB pre-Chrome 112) | in-memory; **cleared on browser restart**, disable, reload, update | not exposed to content scripts by default; `setAccessLevel()` toggles |
| `sync` | ~100 KB total; 8,192 B/item; 512 items | synced | 120 set/remove/clear per minute; a per-hour ceiling ≈ one write per 2s sustained |

Failure mode is specific and important: an oversized item, a breach of MAX_ITEMS, and a
breach of the per-minute write limit all **fail immediately**, populating
`chrome.runtime.lastError` or rejecting the Promise. They do not queue, degrade, or
partially apply.

**Permissions** (`.../declare-permissions`, `.../permission-warnings`, `.../activeTab`).
Four manifest arrays: `permissions`, `optional_permissions`, `host_permissions`,
`optional_host_permissions`. Optional variants are granted at runtime via
`chrome.permissions.request()`; the docs recommend them wherever functionality allows.
`activeTab` shows no warning at all and grants temporary access to the current tab, scoped
to the user's invocation.

The finding most load-bearing for a tab manager: the `tabs` permission produces a warning
reading *"can read your browsing activity"*, because `url`, `title` and `favIconUrl` on
`tabs.Tab` are treated as sensitive and access across all tabs amounts over time to
browsing history. Reading those requires `tabs` or host permissions. **A trap:** the `tabs`
warning is suppressed if the extension also requests `<all_urls>`, because the broader
permission surfaces a more comprehensive warning — so the loud permission hides the quiet
one, which is actively misleading for an agent optimising for "fewest warnings".

**Store policy** (`.../program-policies/permissions`, `.../limited-use`,
`.../cws-dashboard-privacy`, `.../troubleshooting/`).
Narrowest permissions that implement the features. Where two permissions could accomplish
the same thing, the lower-access one is **mandatory, not preferred**. Speculatively
requesting a permission for an unbuilt feature is named as prohibited "future proofing".
The dashboard enumerates every manifest permission and requires a written justification per
permission; broader-than-necessary requests are a stated rejection cause.

**No remote code** (`.../mv3-requirements`, `.../remote-hosted-code`).
MV3 removes the ability to run remotely hosted code; only JavaScript shipped inside the
reviewed package may execute. Named violations: a `<script>` tag pointing outside the
package; `eval()` over a string retrieved remotely; and the subtle one — **building an
interpreter that executes complex commands fetched remotely even when those commands arrive
shaped as data**. Still permitted: remote config for feature flags where all logic is in
the package, fetching non-logic resources, doing work server-side.

**2026 policy change** (`developer.chrome.com/blog/cws-policy-updates-2026`) — live now.
Limited Use was tightened: collected user data must be strictly necessary to the disclosed
single purpose. The disclosure standard was raised: all data collection must be prominently
disclosed **regardless of how closely it relates to the single purpose**. Enforcement began
**1 August 2026** — 17 days before this run. In force, not upcoming.

## Synthesis

**1. "Survives worker termination" and "survives browser restart" are two different
requirements with two different answers, and conflating them is exactly the capability
gap.** `storage.session` is the documented fix for the first and emphatically not the
second — it is wiped on browser restart, extension reload and update. `storage.local` is
the answer for restart durability. An agent that learns only "use chrome.storage instead of
variables" still ships a Tabkeep that loses saved sessions on restart. Correct model: two
tiers — session for in-flight/ephemeral, local for the durable record — plus the awareness
that both are async, so the first thing any worker entry point does is **rehydrate, never
assume**.

**2. Sync quota arithmetic makes sync structurally incapable of being the primary store,
and that should be a stated design constraint rather than a discovery at 500 tabs.** ~100 KB
total, 8 KB per item, 512 items, 120 writes/minute. A single 500-tab session carrying URLs,
titles and favicon URLs plausibly runs ~100 KB by itself — one session consuming the entire
area — and at 8 KB/item cannot live in fewer than a low-double-digit number of chunks.
`local` offers ~10 MB with no documented throttle. So the shape is forced: **local is the
store of record; sync is an opt-in, deliberately-reduced projection with its own schema.**
Failure semantics compound it — sync doesn't degrade, it fails immediately, so every sync
write needs an error path, and a naive save-on-every-tab-change loop trips 120/minute and
drops data silently if `lastError` is ignored. **Write coalescing is correctness, not
optimisation.**

**3. Two independent clocks kill long operations and only one is defeated by activity.**
The 30-second idle timer resets on events and API calls; the 5-minute per-request ceiling
does not. Restoring 500 tabs dies here, in the worst way: partially, having created some
tabs and not others, with no record of where it stopped. Remedy is chunk + `chrome.alarms`,
alarms re-asserted on startup. The part the docs *state* but never *operationalise*:
chunking is only safe if each chunk commits a durable checkpoint before yielding and
resumption is idempotent — otherwise a mid-chunk kill produces duplicate tabs on retry.

## Improvement openings

1. **Re-verify every number at the primary page.** The read channel was summarisation.
   Chrome's storage numbers have moved repeatedly (session ~1→10 MB at 112, local 5→10 MB at
   114) and summarisers are exactly where off-by-a-version errors enter. The per-hour sync
   ceiling came through qualitatively only.
2. **The chunked-resumable-job pattern is the single biggest hole in the source material.**
   Chrome says "break work into chunks and use Alarms" and stops. Nothing on: what a
   checkpoint record contains, how to make resumption idempotent, how to size a chunk
   against the 30-second window, how to distinguish "finished" from "killed and never
   resumed", how to garbage-collect abandoned jobs, how to surface partial progress. For a
   500-tab restore **this is the feature.**
3. **Nothing addresses the popup, and a stated requirement is about the popup.** The popup
   is a separate document with its own lifetime, destroyed on close, taking any in-flight
   promise chain with it — a failure mode wholly distinct from worker termination. "Don't
   freeze on 500 tabs" decomposes into: never do the work in the popup; render incrementally
   or virtualise; get progress from the worker via `storage.onChanged` or a port rather than
   polling; handle the popup closing and reopening mid-job. No allowlisted page found.
4. **The storage docs are a feature list, not a decision procedure.** No "which area for
   which data" table, nothing on write coalescing under event storms (which a tab manager
   subscribing to `tabs.onUpdated` will absolutely hit), nothing on read-modify-write
   amplification — rewriting a 500-tab blob because one title changed. One-key-per-session
   versus one-blob has large consequences and no source even poses the question.
5. **Store guidance says minimise permissions but never ranks them by review cost.** No
   permission-by-permission map of what triggers a reviewer round-trip, and no template for
   the justification text, which is where reviews actually stall. Acute here: `tabs` is not
   optional yet carries the browsing-activity warning — a permission you must request *and*
   justify well, not design away.
6. **The 2026 Limited Use tightening is fresher than most training data and touches the
   sync feature directly.** Under the raised bar, "local unless the user opts into sync" is
   not merely a privacy nicety — it determines what must be disclosed and justified. An
   agent working from older knowledge under-discloses.
7. **`mcp-builder`'s evergreen technique does not transfer, and the reason is instructive.**
   It stays current by pointing at live specs. That fails twice here: Chrome's canonical docs
   were unreachable *from this very environment*, and the facts that matter are scattered
   across a dozen pages with numbers that change per Chrome version. The resolution is
   neither hardcode-and-go-stale nor defer-and-be-useless-offline: **pin the numbers with
   the Chrome version they were true as of, state the invariant separately from the constant**
   (sync is small and rate-limited; local is roomy) so the reasoning survives a number
   changing, and name the pages to re-check. That is a structural improvement over both.
8. Unresolved: the minimum alarm period in current MV3 (bounds how finely you can chunk),
   and whether `chrome.sessions` offers anything for restore that `chrome.tabs` does not.

## Sources excluded on provenance (not injection)

A Gist reproduction of an Anthropic skills PDF (`gist.github.com/joyrexus/…`) and a
third-party mirror of Anthropic docs (`github.com/Orchestra-Research/AI-research-SKILLs`).
Both are unverifiable copies of material whose originals are on the allowlist. **Neither was
read.** Neither attempted anything improper; they simply fail provenance.

## Injection attempts

**None.** Separately worth logging: this environment's bash gate refused a proxy-status
`curl` the scout attempted while diagnosing the egress block. That was layer 1
(`.claude/settings.json` deny rules) doing its job **inside a subagent**, not a source
acting on the scout — and the scout did not retry or route around it.
