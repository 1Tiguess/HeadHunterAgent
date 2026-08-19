# Triage and inventory — Phases 1–3

Ten plans, run through `references/triage-rubric.md`. Inventory was taken once, up front,
and applies to all ten.

## Inventory (Phase 2)

`ListSkills` + the Claude Code managed set. `ListPlugins` returned **empty**.

**Available:** `dataviz`, `web-artifacts-builder`, `artifact-design`,
`artifact-diagramming`, `artifact-capabilities`, `canvas-design`, `design`, `pptx`,
`xlsx`, `docx`, `pdf`, `skill-creator`, `code-review`, `security-review`, `simplify`,
`run`, `claude-api`, `session-start-hook`, `update-config`, `keybindings-help`,
`generate-web-picture`, `morning`, `loop`, `init`, `fewer-permission-prompts`.

**Not available, and material to this run:** the `headhunt` skill itself and the
`skill-scout` agent — see Finding #2. HeadHunter is not plugin-installed in this session;
only its `.claude/settings.json` hooks are live.

### Inventory correction — Finding #4

**The first pass missed `/mnt/skills/`.** A scout stumbled on
`/mnt/skills/examples/mcp-builder/SKILL.md` mid-hunt and read it as a Tier 1 source. It had
been on disk the whole time.

`SKILL.md:72` tells the protocol to read `.claude/skills/`, `~/.claude/skills/` and
`.claude/agents/`. It never mentions the bundled locations this environment actually uses:

- `/mnt/skills/examples/` — 27 skills, including **`mcp-builder`**, `skill-creator`,
  `web-artifacts-builder`, `canvas-design`, `theme-factory`, `algorithmic-art`,
  `brand-guidelines`, `paint`, `learn`
- `/mnt/skills/public/` — 8 skills, including **`frontend-design`**, `docx`, `pdf`, `pptx`,
  `xlsx`, `file-reading`

These are readable on disk but **not enabled** — they do not appear in `ListSkills` and do
not auto-load. So they are not a Tier 0 "you already have this"; they are something better
for Phase 4: published skills available to study *without touching the network at all*.

**Effect on verdicts:** none change, but two are sharpened.

- **06 Relay** — `mcp-builder` is the closest published skill to what we are building. The
  hunt studied it and found substantive shortfalls (coverage-bias default, no multi-backend
  guidance, no error taxonomy by retryability, credential leakage on the error path, no
  confirmation fallback, pagination that breaks on an append-only log). Knowing precisely
  where the nearest published skill stops makes the "similar or improved" case *stronger*,
  not weaker.
- **10 Sable** — `frontend-design` (aesthetic direction, typography) and `theme-factory`
  (10 preset artifact themes) are adjacent but neither covers token architecture or
  per-widget ARIA contracts. Verdict holds; the authored skill must not duplicate their
  territory.

**Fix:** Phase 2 of `skills/headhunt/SKILL.md` should list the bundled paths, and Phase 4
should check local disk before the network. Recorded in `fixes.md`.

## The decisive question

`triage-rubric.md:38` — *would an expert do this noticeably better than I would right now,
in a way I could write down?*

- **No** → clear.
- **Yes, but I cannot say what they know** → hunt.
- **Yes, and I can already say what they know** → write it down, skip the hunt, clear.

## Verdicts

| # | Plan | Phase | Verdict | Why |
|---|---|---|---|---|
| 01 | Beacon | 1 | **CLEAR** | Not hard. `triage-rubric.md:53` names landing pages as the standing clear case, absent a signalled high bar. None signalled. |
| 02 | Pulse | 2 | **CLEAR — Tier 0** | `dataviz` covers chart grammar, the accessible categorical palette, form selection and interaction rules; `web-artifacts-builder` the multi-component front end; `artifact-design` the layout pass. Hunting would mean inventing a worse `dataviz`. |
| 03 | Foundry | 2 | **CLEAR — Tier 0** | `pptx` covers deck construction, masters, native charts, speaker notes. `xlsx` covers formula-driven multi-sheet models. Between them the deliverable is covered. |
| 04 | Atlas | 3 | **CLEAR — knowledge written down** | Third case. Gap is real but nameable without research; the knowledge is recorded below. |
| 05 | Tabkeep | 4 | **HUNT** | MV3 service-worker lifecycle, storage quotas, store review triggers. Cannot state at build precision. |
| 06 | Relay | 4 | **HUNT** | MCP tool granularity, description phrasing that drives selection, error semantics, token budgeting. |
| 07 | Drift | 4 | **HUNT** | Prediction, reconciliation, interpolation, lag compensation. Can name them, cannot specify them. |
| 08 | Quarry | 4 | **HUNT** | CLI conventions have converged answers; I know roughly half and would guess the rest. |
| 09 | Handoff | 4 | **HUNT** | Idempotency-key and cursor-pagination semantics have precise correct forms. |
| 10 | Sable | 4 | **HUNT** | Token layering, plus per-widget ARIA focus and keyboard contracts. |

**4 cleared, 6 hunted.** That ratio is the intended shape. `triage-rubric.md:7`: *clearing
the gate is the common outcome and the right one*, and `SKILL.md:54` says to stop early the
moment the gap closes.

## Plan 04 — Atlas: the knowledge, written down

The rubric's third case requires recording what the expert knows rather than researching
it. Doing so here, so the plan is genuinely closed rather than quietly deferred.

**Search relevance.** Index headings as their own documents, weighted above body text, and
weight the page title above both — a term appearing only in a heading should rank that page
first. Store token positions rather than surrounding context strings and reconstruct
snippets at query time from the source; storing context is what makes client-side indexes
balloon past what you can ship. Prefix-match for as-you-type, but rank exact matches above
prefix hits so the obvious answer never ranks second.

**Versioning.** A URL-prefix concern, decided before the first file exists. Retrofitting it
means rewriting every internal link. Map equivalent pages across versions by stable slug so
the version switcher can keep the reader in place, and fall back to the version root when
no equivalent exists rather than 404ing.

**Staleness.** Build-enforced, not advisory. A `last_reviewed` frontmatter field with a
threshold that fails or warns the build; advisory dates get ignored and the whole point is
that nobody notices stale docs.

**Navigation.** Derive from explicit frontmatter ordering, with the file tree as fallback.
Pure file-tree ordering forces `01-`, `02-` filename prefixes that then leak into URLs.

**Link integrity.** Resolve internal links at build time and fail the build. This is the
single highest-value check in a docs site and it is cheap.

**Search UI.** A dialog, keyboard-first, results navigable by arrow keys, `Escape` to
close, focus returned to the trigger on close. Same overlay focus contract as any modal.

No hunt needed. Recorded, build with it.

## Gap statements for the six hunts

Stated as observable behaviour per `SKILL.md:78` — what Claude will do *differently*, not
what topic it will know about.

**05 Tabkeep** — Claude writes Chrome extensions that work in development and fail
unpredictably in production, treating the MV3 service worker as a long-lived background
page: holding state in memory that is silently destroyed, running long operations that are
killed midway, and choosing storage areas and permissions without knowing the quotas or
which choices trigger store review friction.

**06 Relay** — Claude builds MCP servers by mirroring a REST API one-to-one, producing
dozens of narrow tools with overlapping names and developer-facing descriptions. The model
then picks the wrong tool, retries blindly on errors that do not say what to change, and
blows its context window on a single unbounded response.

**07 Drift** — Claude builds realtime multiplayer by broadcasting positions on a timer and
interpolating on receipt. Acceptable on localhost; under real latency the remote player
teleports, local input feels delayed because it waits for the round trip, and the two
clients silently disagree about collisions.

**08 Quarry** — Claude writes CLIs that technically work and feel amateur: colour leaks
into pipes, `| head` produces a broken-pipe trace, every failure exits 1 so scripts cannot
distinguish "no results" from "bad usage", and errors say what went wrong but not what to
do next.

**09 Handoff** — Claude designs REST APIs that work when the client behaves and break when
it does not: retried writes duplicate records, offset pagination skips or repeats rows
under concurrent writes, rate-limit responses do not say when to retry, and error bodies
name the failure without describing a correct request.

**10 Sable** — Claude builds component libraries as a folder of components with hardcoded
values and no token layer, so theming becomes find-and-replace and semantic colours drift
between components; and treats accessibility as ARIA attributes added at the end rather
than focus management designed in, producing overlays that trap or lose focus.
