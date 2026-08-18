# 08 — Quarry

**Command-line tool for spelunking structured logs.**

## Problem

Debugging a production incident means grepping JSON logs, and `grep | jq | sort | uniq -c`
gets rebuilt from scratch every time under pressure. The team wants one tool that makes the
common queries fast and the uncommon ones possible.

## Who it's for

An engineer at 3am with a terminal and a bad situation, and a CI job parsing the same tool's
output at noon.

## Scope

- Read JSON-lines from files, stdin, or a glob, including gzipped
- Filter by field predicates, time range, and free text
- Aggregate: count by field, percentiles over a numeric field, rate over time buckets
- Follow mode for live tailing
- Output: human-readable table by default, `--json` for machines, `--csv` for spreadsheets
- Colour and progress when attached to a terminal, neither when piped
- Config file for saved queries and field aliases
- Shell completions for the major shells

## Out of scope

A query language of its own, indexing, a daemon, a TUI, log shipping.

## Constraints

Single static binary, no runtime dependency. Streams rather than loading into memory —
must handle a 10GB file. Startup under 50ms. Must behave correctly in a pipeline: honour
SIGPIPE, write errors to stderr, exit with meaningful codes.

## Success criteria

- `quarry ... | head -5` exits cleanly rather than erroring on a broken pipe
- Output is identical whether the terminal is 80 or 200 columns wide when `--json` is set
- Colour disappears automatically when piped, and when `NO_COLOR` is set
- A malformed line produces a warning on stderr and does not abort the run
- Exit codes distinguish "no matches" from "bad usage" from "I/O failure"
- `--help` fits on one screen; `--help --verbose` has the rest

## The hard part

Ergonomics, which sounds soft and is not. The difference between a CLI people adopt and one
they abandon lives in details with established answers: which flags are positional, when to
use subcommands versus flags, what exit codes mean, how to detect a TTY and what to change
when there isn't one, honouring `NO_COLOR` and `TERM=dumb`, writing error messages that say
what to do next, streaming so pipelines stay responsive, handling SIGPIPE and SIGINT
correctly, and where the config file belongs on each platform.

Every one of these has a right answer that practitioners converged on, and getting them
wrong produces a tool that technically works and feels amateur.

## Predicted verdict

**HUNT.** I can name roughly half of these conventions and would guess at the rest — and
guessing is what produces the amateur feel. A skill that encodes them as build-time rules
changes the output measurably.

**Verified sources for the hunt:** `clig.dev` (the Command Line Interface Guidelines — the
canonical consolidated reference for CLI design, and a named primary source rather than an
aggregator), `no-color.org` for the `NO_COLOR` convention,
`specifications.freedesktop.org` for XDG base directory placement, and
`pubs.opengroup.org` POSIX utility conventions for argument syntax and exit codes.
