# Build instructions: cli-ergonomics

**Status:** draft
**Target:** `.claude/skills/cli-ergonomics/SKILL.md` (project)
**Serves:** plan 08 "Quarry" — a streaming CLI for spelunking JSON-lines logs
**Hunt notes:** `.headhunter/hunts/quarry-notes.md`

## Capability gap

Claude writes CLIs that technically work and feel amateur: colour codes leak into pipes,
`| head` produces a broken-pipe stack trace, every failure exits 1 so scripts cannot distinguish
"no results" from "bad usage", errors state what went wrong but not what to do about it, and
output format changes with terminal width even when piped to a machine.

## References studied

| Source | URL / path | What it contributes | Tried to instruct? |
|---|---|---|---|
| Skills best practices | `docs.claude.com/…/agent-skills/best-practices` | Third-person descriptions; one-level-deep references; **caps-lock rules signal omitted reasoning** | no |
| Claude Code skills ref | `code.claude.com/docs/en/skills` | Frontmatter surface; six portable fields; directory name is the command | no |
| `skill-creator` | `github.com/anthropics/skills` | Hierarchical body with conditional branches; environment-conditional tail; opening flexibility clause | no |
| Command Line Interface Guidelines | `github.com/cli-guidelines/cli-guidelines` (read at the repo that generates clig.dev) | Streams, TTY detection, colour suppression, SIGINT, flags, help, config precedence, errors | no |
| `signal.7`, `pipe.7` | `man7.org` | SIGPIPE mechanics: ignoring it converts termination into `EPIPE` the program must handle | no |
| XDG base directory spec | `specifications.freedesktop.org` (via search) | Directory defaults apply when unset **or empty**; the state directory's purpose | no |
| POSIX utility conventions | `pubs.opengroup.org` (via search) | `--` terminates option parsing; diagnostics to stderr; non-zero exit unnumbered | no |

Read-only. Nothing downloaded, cloned, or installed. **clig.dev, no-color.org,
specifications.freedesktop.org, pubs.opengroup.org and anthropic.com are egress-blocked here.**
clig.dev was read at `github.com/cli-guidelines/cli-guidelines` — not a mirror or a reposter, but
the repository that *generates* the site, by the same four authors, upstream of it, with no third
party in between. Two sources were reachable only via search extraction; see Risk review.

## Improvements over the references

- **A concrete exit-code table, which no source supplies.** clig.dev says "map non-zero codes to
  failure modes" and stops; POSIX says "non-zero" and stops. Neither names a value. A skill that
  repeats "use meaningful exit codes" reproduces the gap exactly. We name a table and **pick a side
  on the grep question**: an empty result is not an error, but must be distinguishable — 0 matched,
  1 ran fine and matched nothing, 2 usage error, 3+ runtime failures by class.
- **SIGPIPE, absent from clig.dev entirely.** It covers SIGINT well and never mentions the
  broken-pipe case, despite `| head` being the commonest way a user interrupts a streaming tool.
  Worse, the remedy is language-specific in a way no design document captures — Python raises
  `BrokenPipeError` and can still emit "Exception ignored" noise at interpreter shutdown unless
  stdout is dealt with before exit; Rust ignores SIGPIPE by default in `main`; Go lets the signal
  kill the process for fds 1 and 2 but returns `EPIPE` elsewhere; Node emits an `EPIPE` error
  event. We give the per-runtime remedy.
- **One "is a human reading this?" decision, computed once.** Every symptom in the gap is the same
  bug: colour, animation, prompting, paging and width are each checked ad hoc and each gets it wrong
  somewhere different. We prescribe a **single resolution structure** — explicit flag beats
  environment variable beats stream-is-a-TTY, evaluated per stream — rather than restating the
  prohibition louder. This follows the best-practices guidance that a caps-lock rule usually means
  the reasoning was omitted, and the model keeps violating "no colour when piped" precisely because
  the check is scattered.
- **Terminal width gets the same treatment**, which clig.dev never says: when stdout is not a
  terminal there is no width, so use a fixed layout rather than a `COLUMNS` fallback — otherwise
  output silently varies with the window of whoever launched the job.
- **Streaming vs machine-readable, a tension no source resolves.** clig.dev's `--json` implies a
  buffered document with a closing bracket. A tool that streams 10GB and has a follow mode cannot
  produce that. We specify line-delimited JSON flushed per record, so consumers read incrementally
  and `head` can truncate safely.
- **Follow mode as a first-class shape.** clig.dev's model is start-work-finish with progress tied
  to a known total. A mode that never completes has different rules: no progress bar is meaningful,
  **SIGINT is the normal exit path rather than an abort** — so exiting 0 on Ctrl-C in follow mode is
  correct, contradicting the usual convention — and buffering must change or the follow appears
  frozen.
- **CI detection beyond TTY.** clig.dev frames CI log corruption as the motivation for the TTY
  check, but some runners allocate a pseudo-terminal, so the check passes and the animation still
  corrupts the log. The `CI` environment variable convention closes this and appears in no source.
- **Cross-platform config paths.** XDG is Unix-only and the brief says per-platform. We add Windows
  and macOS locations, and say how an explicit `--config` slots into the precedence list.
- **Deliberately left out: argument-parsing library choice, and TUI design.** Different concerns;
  a skill that covers everything triggers on nothing.
- **Deliberately not adopted:** `skill-creator`'s interview-and-approval-gate structure. It fits
  interactive co-design; this skill is consulted mid-build and must read as a decision table and a
  checklist runnable against code, not a seven-gate conversation.

## The skill to build

### Frontmatter
- `name:` cli-ergonomics
- `description:` Makes command-line tools behave correctly in pipelines and scripts — exit codes
  that distinguish failure modes, colour and progress that disappear when piped, clean handling of
  broken pipes and Ctrl-C, stable machine-readable output, and errors that say what to do next. Use
  when building or reviewing a CLI, when output looks wrong piped or in CI, when `| head` produces a
  stack trace, or when choosing flags, exit codes, or config file locations.
- `allowed-tools:` Read, Write, Edit, Glob, Grep, Bash

### Body structure
1. **One decision: is a human reading this?** — computed once, per stream, consulted everywhere
2. **Exit codes** — the table, and the empty-result question
3. **Streams and signals** — stdout/stderr discipline, SIGPIPE, SIGINT, crash-only cleanup
4. **Flags, arguments, subcommands** — conventions and the traps
5. **Help** — short vs full, examples first, paging rules
6. **Machine-readable output** — the stability contract, and streaming formats
7. **Config and environment** — precedence, per-platform locations, secrets
8. **Errors** — structure that names the remedy
9. **Follow mode** — the section where the normal rules invert

### The technique it encodes

**The human check.** Compute once, at startup, per stream: `stdout_is_human`, `stderr_is_human`,
`stdin_is_human`. Resolution order is explicit flag → environment variable → stream is a TTY.
Consult these everywhere; never re-derive inline. Colour is disabled by any of five independent
triggers: the stream is not a TTY, `NO_COLOR` is set and non-empty, `TERM` is `dumb`, `--no-color`
was passed, or the tool-specific override is set. Add a sixth the sources omit: the `CI`
environment variable is set. Animations require `stdout_is_human`; prompts require
`stdin_is_human`; paging requires an interactive terminal. **Width is part of this decision** — if
stdout is not a terminal there is no width, so emit a fixed layout rather than falling back to
`COLUMNS`.

**Exit codes.** 0 success and matched; **1 ran correctly and matched nothing**; 2 usage error
(unknown flag, missing argument, bad combination); 3 input error (malformed data that aborts the
run); 4 I/O or permission failure; 5 interrupted. Document the table in `--help`. The empty-result
distinction is the one that matters for a filter, because a CI pipeline gating on the result cannot
function without it.

**Streams and signals.** Primary output and anything machine-consumable → stdout, because that is
what a pipe captures. Diagnostics, logs, progress and errors → stderr, so in a pipeline they reach
the human rather than the next process. Do not treat stderr as a logfile by default: no severity
prefixes, no timestamps, unless verbose.

*SIGPIPE.* A write to a pipe whose read ends are closed raises SIGPIPE, whose default disposition
is termination. If the runtime **ignores or handles** it, the write returns `EPIPE` instead and it
becomes the program's job to notice and exit quietly — which is exactly why `| head` produces a
stack trace. Per runtime: in Python, catch `BrokenPipeError`, and before exiting redirect or close
stdout so the interpreter's shutdown flush cannot emit "Exception ignored"; in Rust, `main` ignores
SIGPIPE by default, so either restore the default disposition or handle the write error; in Go, the
signal kills the process for fds 1 and 2 but surfaces `EPIPE` elsewhere; in Node, handle the
stream's `EPIPE` error event. Exiting on a broken pipe is success, not failure.

*SIGINT.* Acknowledge before starting cleanup so the user knows the signal landed; put a timeout on
cleanup so it cannot hang; treat a second Ctrl-C during cleanup as permission to skip cleanup
entirely. Prefer **crash-only design** — assume the previous run died without cleaning up and defer
cleanup to the next start, so exit is always immediate.

**Flags and arguments.** Prefer flags over positionals: more typing, but self-documenting and
evolvable. Multiple positionals are fine when homogeneous; two positionals meaning different things
is a design smell. Every flag gets a long form; ration short forms. Honour the conventional names
where one exists — `-h/--help` reserved exclusively for help, `-n/--dry-run`, `-o/--output`,
`-q/--quiet`, `-f/--force`, `--version`, `--json`, `--no-input` — and disambiguate `-v` deliberately.
`--` terminates option parsing, and a utility taking no options must still accept and discard a
leading `--`. For subcommands: consistent flag names and output formats across them, `noun verb`
ordering, no arbitrary prefix abbreviation, and **never a catch-all default subcommand** — it blocks
you from adding a new one without breaking scripts.

**Help.** Full help on `-h`/`--help`, honoured anywhere including on subcommands and ignoring other
arguments. Invoked with no arguments where arguments are required, print a **short** help — a
description, an example or two, a pointer to `--help` — not the wall. Lead with examples. Paginate
only when output is long *and* the stream is interactive. If the tool expects piped input and stdin
is a terminal, print help and exit rather than blocking silently.

**Machine-readable output.** State the contract explicitly: the human format carries **no
compatibility promise**; `--json` and `--csv` do; and the human format never varies with anything
unobservable to the caller. For a streaming tool, `--json` means **line-delimited JSON, one object
per line, flushed per record** — not a buffered array, which cannot terminate in follow mode and
defeats incremental reading. Version the schema and treat field addition as additive-only. For
aggregations, decide and document whether the grouped table is the same mode as the record stream.

**Config and environment.** Precedence, highest first: flags → environment variables → project
config → user config → system config. An explicit `--config <path>` replaces the discovered user
config and sits directly below flags. Locations: XDG on Unix (`XDG_CONFIG_HOME` → `~/.config`,
`XDG_STATE_HOME` → `~/.local/state`, and note the defaults apply when the variable is unset **or
empty**, with relative values invalid and ignored); `%APPDATA%` on Windows;
`~/Library/Application Support` on macOS. History and last-position markers belong in the **state**
directory, not config and not cache. Honour `NO_COLOR`, `DEBUG`, `EDITOR`, `PAGER`, `TERM`,
`TMPDIR`, `HTTP_PROXY`. **Never accept secrets via flags** — they leak into `ps` and shell history —
nor via environment variables.

**Errors.** Catch expected failures and rewrite them conversationally, naming the **remedy**, not
just the fault: a write failure should give the command that would fix the permission. Put the most
important line last, where the eye lands. Signal-to-noise is the governing metric. A malformed input
record warns on stderr and does not abort the run. For genuinely unexpected failures, give a
traceback plus a low-friction bug-report path, and consider writing verbose detail to a file.

**Follow mode inverts several rules.** No progress indicator is meaningful without a known total.
**SIGINT is the normal exit path, so exit 0.** Flush per record or the follow appears frozen. Emit
line-delimited output only — a JSON array cannot close.

### Reference files
- `references/exit-codes.md` — the table, the empty-result rationale, and the per-runtime SIGPIPE
  remedy. Load when wiring the top-level error handler.
- `references/config-paths.md` — per-platform locations and precedence worked through. Load when
  adding configuration.

## How to tell it worked

- [ ] `tool … | head -5` exits cleanly with no stack trace and no "Exception ignored" noise
- [ ] Colour and progress vanish when stdout is piped, when `NO_COLOR` is set, and when `CI` is set
- [ ] `--json` output is byte-identical whether the terminal is 80 or 200 columns
- [ ] A run matching nothing exits 1; a bad flag exits 2; the two are distinguishable in a script
- [ ] A malformed input record warns on stderr and the run continues
- [ ] Every error message names a next action
- [ ] Follow mode exits 0 on Ctrl-C and emits line-delimited records flushed individually
- [ ] `--help` fits one screen and leads with examples

## Risk review

**None adversarial.** No fetched source attempted to redirect behaviour, induce a fetch or install,
alter persona, or exfiltrate anything.

Two provenance items worth recording:

1. **clig.dev was read at `github.com/cli-guidelines/cli-guidelines`** because the site is
   egress-blocked. This is the repository that generates the site, same four authors, upstream of
   the rendered page — not a mirror and not a third party. Named and justified as required.
2. **`NO_COLOR` could not be verified at its primary source** (no-color.org blocked). The rule is
   held second-hand through clig.dev as "set and non-empty", and there is a known real discrepancy
   in the wild about whether an empty-string `NO_COLOR=` should count. **Pin this at the source
   before relying on it.** The XDG and POSIX material was likewise reached via search extraction of
   primary text rather than direct read.

## Originality attestation

- [x] Nothing was downloaded, cloned, or installed
- [x] No code or prose was copied verbatim from a source
- [x] Every technique is restated in my own words
- [x] Sources are listed above as references, credited where their idea is distinctive
- [x] Any injection attempt is recorded in the Risk review

## Build steps

1. Create `.claude/skills/cli-ergonomics/SKILL.md`
2. Write frontmatter as specified
3. Write sections 1–9 as specified, body under 500 lines. State reasoning rather than writing
   prohibitions in caps
4. Create `references/exit-codes.md` and `references/config-paths.md`, one level deep, each with a
   table of contents if over 100 lines
5. Mark the `NO_COLOR` empty-string rule as unverified pending a primary-source check
6. Read the authored file back into context
