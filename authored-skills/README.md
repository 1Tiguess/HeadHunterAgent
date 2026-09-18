# Authored skills

Skills produced by headhunt runs. **These are outputs of the protocol, not part of the gate.**

They live here rather than in `skills/` because `plugin.json` declares `skills/` as
HeadHunter's own — shipping unrelated design and engineering skills inside a pre-flight gate
would conflate two different things. Installing HeadHunter should not install these, and
installing these should not install HeadHunter.

Every one was written from an approved spec in a `.headhunter/specs/` file, in Claude's own
words, from read-only study of published sources. **Nothing here was downloaded.**

## Install

```bash
bash ../install-skills.sh --dry-run    # see what would happen
bash ../install-skills.sh              # install into ~/.claude/skills/
bash ../install-skills.sh --force      # overwrite same-named skills
bash ../install-skills.sh cli-ergonomics app-interface-design   # just these
```

They go to `${CLAUDE_CONFIG_DIR:-$HOME/.claude}/skills/`, which loads in **every project**.
Copy an individual directory into a project's `.claude/skills/` instead if you want it scoped
to one repo.

## What's here

| Skill | Closes the gap where Claude… |
|---|---|
| `app-interface-design` | designs apps as a stack of landing pages — six screens for a one-screen task, navigation that changes between sections, uniform density, missing states |
| `api-contract-design` | writes APIs that break when clients retry — duplicate records, pagination that skips rows, errors that don't say what a correct request looks like |
| `cli-ergonomics` | writes CLIs that feel amateur — colour in pipes, stack traces from `\| head`, every failure exiting 1 |
| `design-token-systems` | hardcodes values with no token layer, and bolts ARIA on at the end instead of designing focus in |
| `mcp-tool-design` | mirrors a REST API one-to-one into dozens of tools a model picks between badly |
| `mv3-extension-lifecycle` | treats the MV3 service worker as a long-lived background page, losing state and dying mid-operation |
| `realtime-netcode` | broadcasts positions on a timer and lerps — fine on localhost, teleporting under real latency |
| `application-security` | writes authentication and authorization fluently, from guidance that has since been reversed — expiry policies, composition rules, minimum-8, `localStorage` tokens |
| `compliance-by-design` | ships products missing features the law requires — no cookie refusal path, a "Do Not Sell" link wired to nothing, a dead ODR link, no Israeli accessibility declaration |
| `production-data-layer` | writes schemas and migrations that work at demo scale — constraints that pass on null, migrations that lock a live table, jobs that assume exactly-once |
| `resilience-patterns` | builds systems that work only when every dependency is healthy — no timeouts, unjittered retries, no degradation plan, jobs that restart from zero |
| `rtl-hebrew-i18n` | mirrors the layout and calls it RTL — correct columns, broken sentences — and assumes Hebrew behaves like Arabic |
| `ux-journey-design` | designs screens rather than journeys — fields nobody can justify, answers lost on interruption, errors that say what is wrong but not how to escape |

Six came from the [August 2026 test run](../examples/test-run-2026-08/README.md);
`app-interface-design` came from a later run in the same session. The six added in September 2026
came from a single batched run covering engineering craft and the regulatory layer.

## Provenance

Each skill's spec records the sources studied, what each contributed, and — importantly — where
the sources were **weak, unreachable, or absent**, since that is where the skill had to reason
rather than cite.

Two sections carry explicit "reasoned from primitives" markers because no canonical source
covers them at all: the per-screen density taxonomy and the web application surfaces, both in
`app-interface-design`. Where a claim came through a degraded channel — a summarising search
layer rather than a direct read — the spec says so.

The September 2026 batch ran under a near-total blockade of regulator, vendor and standards-body
websites, and the provenance varies sharply as a result. **`application-security` and
`rtl-hebrew-i18n` read every primary source**, because their canonical text lives as files in Git
repositories — NIST publishes SP 800-63B-4 in its own GitHub organisation, and CLDR ships as data
files. **`compliance-by-design` reached twelve primary sources and no regulator at all**, so it
marks every claim as FETCHED or REPORTED and refuses to say whether a regime applies. Its Israeli
layer rests entirely on REPORTED material and carries a list of five things it declines to guess.
**`production-data-layer` names two under-evidenced sections** — job queues and caching — rather
than filling them from secondary sources.

That asymmetry is the clearest finding of the run: **domains whose canonical knowledge lives as
code or specifications on GitHub survived the blockade; domains whose knowledge lives in regulator
prose did not.**

That discipline exists because a skill that cannot tell you which of its claims have a source
behind them is a skill you cannot maintain.

## Editing

Edits are picked up live — Claude Code re-reads a `SKILL.md` without a restart. If you change
one here, re-run `install-skills.sh --force` to push it to your user config; if you change the
installed copy, copy it back here so it survives.
