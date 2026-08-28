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

Six came from the [August 2026 test run](../examples/test-run-2026-08/README.md);
`app-interface-design` came from a later run in the same session.

## Provenance

Each skill's spec records the sources studied, what each contributed, and — importantly — where
the sources were **weak, unreachable, or absent**, since that is where the skill had to reason
rather than cite.

Two sections carry explicit "reasoned from primitives" markers because no canonical source
covers them at all: the per-screen density taxonomy and the web application surfaces, both in
`app-interface-design`. Where a claim came through a degraded channel — a summarising search
layer rather than a direct read — the spec says so.

That discipline exists because a skill that cannot tell you which of its claims have a source
behind them is a skill you cannot maintain.

## Editing

Edits are picked up live — Claude Code re-reads a `SKILL.md` without a restart. If you change
one here, re-run `install-skills.sh --force` to push it to your user config; if you change the
installed copy, copy it back here so it survives.
