---
name: cli-ergonomics
description: >-
  Makes command-line tools behave correctly in pipelines, scripts and CI — exit codes that
  distinguish failure modes, colour and progress that disappear when output is piped, clean
  handling of broken pipes and Ctrl-C, stable machine-readable output, and errors that say
  what to do next. Use when building or reviewing a CLI, when output looks wrong piped or
  redirected or in CI logs, when piping to head produces a stack trace, when a script cannot
  tell "no results" from "bad usage", or when choosing flags, subcommands, exit codes or
  config file locations.
allowed-tools: Read, Write, Edit, Glob, Grep, Bash
---

# CLI ergonomics

The gap between a tool people adopt and one they abandon is almost entirely in behaviour
they never consciously notice — until it breaks. Colour codes in a log file. A stack trace
from `| head`. Every failure exiting 1, so no script can branch on the outcome.

These have converged answers. The reason they keep getting violated is not ignorance of the
rules; it is that each check gets written ad hoc in a different place, so each one is wrong
somewhere different.

## 1 — One decision: is a human reading this?

Compute it **once**, at startup, per stream. Store it. Never re-derive it inline.

```
stdout_is_human   stderr_is_human   stdin_is_human
```

Resolution order for each, highest priority first:

1. An explicit flag (`--color`/`--no-color`, `--progress`/`--no-progress`)
2. An environment variable
3. Whether that stream is a TTY

Evaluate the streams **independently**. Piping stdout does not mean stderr should lose its
colour — progress on stderr while stdout is piped is legitimate and useful.

Then consult those three values everywhere:

| Behaviour | Gate |
|---|---|
| Colour on stdout | `stdout_is_human` and no suppressor |
| Progress, spinners, animation | `stdout_is_human` |
| Interactive prompts | `stdin_is_human` |
| Paging | `stdout_is_human` |
| Width-dependent layout | `stdout_is_human` |

**Colour is suppressed by any one of six triggers:** the stream is not a TTY; `NO_COLOR` is
set; `TERM` is `dumb`; `--no-color` was passed; a tool-specific override is set; or `CI` is
set. That last one matters because some CI runners allocate a pseudo-terminal, so the TTY
check passes and the animation still corrupts the log.

*One caveat worth carrying: `NO_COLOR`'s canonical rule is "set and non-empty", but there is
a genuine discrepancy in the wild about whether `NO_COLOR=` (empty) should count. If it
matters to you, check the primary source rather than trusting either behaviour.*

**Width belongs to this decision too**, and it is the one people forget. If stdout is not a
terminal there is no width — emit a fixed layout rather than falling back to `COLUMNS` or a
default of 80. Otherwise your output silently varies with the window size of whoever launched
the job, which makes it unparseable and undiffable.

## 2 — Exit codes

The conventional advice is "map non-zero codes to failure modes", which stops exactly where
it becomes useful. Use a table and document it in `--help`:

| Code | Means |
|---|---|
| 0 | Success, and matched something |
| 1 | Ran correctly, matched nothing |
| 2 | Usage error — unknown flag, missing argument, bad combination |
| 3 | Input error — malformed data that aborted the run |
| 4 | I/O or permission failure |
| 5 | Interrupted |

**The 0/1 distinction is the important one for any tool that filters.** "Found nothing" is a
successful run with an empty result, not an error — but a script must be able to tell it from
"you typed the flag wrong". A CI pipeline gating on this tool cannot function otherwise.

A broken pipe exits **0**. So does Ctrl-C in a follow mode. Both are normal terminations of
that mode, not failures.

`references/exit-codes.md` carries the rationale and the per-runtime SIGPIPE remedy.

## 3 — Streams and signals

**stdout** carries primary output and anything machine-consumable, because that is what a
pipe captures. **stderr** carries diagnostics, logs, progress and errors, so that inside a
pipeline they reach the human instead of being fed to the next process.

Do not treat stderr as a logfile by default: no severity prefixes, no timestamps, no
contextual noise unless the user asked for verbose.

### SIGPIPE

Writing to a pipe whose read ends are all closed raises SIGPIPE, whose default disposition is
to terminate the process. **If your runtime ignores or handles it, the write returns `EPIPE`
instead and it becomes your job to notice and exit quietly.**

That is the entire mechanism behind `yourtool … | head` producing a stack trace, and it is
runtime-specific in a way no design document covers. The per-language remedies are in
`references/exit-codes.md`.

### SIGINT

- Acknowledge **before** starting cleanup, so the user knows the signal landed.
- Put a timeout on cleanup so it cannot hang.
- Treat a second Ctrl-C during cleanup as permission to skip cleanup entirely.

Better still, prefer **crash-only design**: assume the previous run died without cleaning up,
handle that at startup, and let exit be immediate. Cleanup you can skip is cleanup that can
never hang.

## 4 — Flags, arguments, subcommands

Prefer flags over positional arguments. More typing, but self-documenting and far easier to
evolve. Multiple positionals are fine when they are a homogeneous list; two positionals
meaning *different* things is a design smell.

Every flag gets a long form. Ration short forms to genuinely frequent ones. Honour the
conventional names where one exists — `-h/--help` reserved exclusively for help,
`-n/--dry-run`, `-o/--output`, `-q/--quiet`, `-f/--force`, `-a/--all`, `--version`, `--json`,
`--no-input` — and disambiguate `-v` deliberately, since it means both verbose and version in
the wild.

`--` terminates option parsing; everything after it is an operand even if it starts with `-`.
A utility that takes no options at all must still accept and discard a leading `--`.

For subcommands: keep flag names and output formats consistent across them, prefer
`noun verb` ordering, refuse arbitrary prefix abbreviation (it permanently reserves the
namespace), and **never add a catch-all default subcommand** — it blocks you from ever adding
a new one without breaking existing scripts.

## 5 — Help

`-h` and `--help` work anywhere, including after a subcommand, and ignore all other
arguments.

Invoked with no arguments where arguments are required, print a **short** help — a
description, an example or two, and a pointer to `--help`. Not the wall.

**Lead with examples.** That is what people actually read.

Paginate only when the output is long *and* the stream is interactive, and use a pager
invocation that does not page short output and does not clear the screen on exit. If your tool
expects piped input and stdin is a terminal, print help and exit rather than blocking silently
the way bare `cat` does.

## 6 — Machine-readable output

State the contract explicitly, in the docs:

- **The human format carries no compatibility promise.** It may change in any release.
- **`--json` and `--csv` do.** They are the API.
- The human format never varies with anything the caller cannot observe.

That last clause is what makes the first one safe. Changing human output freely is only
defensible when a stable machine mode exists and users know to use it.

**For a streaming tool, `--json` means line-delimited JSON** — one object per line, flushed
per record. Not a buffered array. An array cannot terminate in a follow mode, and buffering to
close the bracket defeats streaming entirely. Line-delimited output also lets `head` truncate
safely.

Version the schema. Treat field addition as additive-only, and say what a consumer should do
with unknown fields.

If the tool aggregates as well as filters, decide and document whether a grouped result is the
same output mode as a record stream. They are usually different shapes, and quietly returning
one where the caller expected the other is a bug they will find at 3am.

## 7 — Config and environment

Precedence, highest first:

1. Command-line flags
2. Environment variables
3. Project-level config
4. User-level config
5. System-level config

An explicit `--config <path>` replaces the discovered user config and sits directly below
flags. Say whether project config is discovered by walking up from the working directory.

Locations are per-platform; `references/config-paths.md` has them worked through, including
the XDG rule people get wrong — the defaults apply when a variable is **unset or empty**, and
a relative value is invalid and must be ignored rather than resolved.

Honour the general-purpose environment variables: `NO_COLOR`, `DEBUG`, `EDITOR`, `PAGER`,
`TERM`, `TMPDIR`, `HTTP_PROXY`.

**Never accept secrets via flags** — they leak into `ps` output and shell history — nor via
environment variables. Read them from a file or a credential helper.

## 8 — Errors

Catch expected failures and rewrite them conversationally, naming **the remedy** and not just
the fault. A permission error should give the command that would fix it.

Put the most important line **last**, because that is where the eye lands when output stops.

Signal-to-noise is the governing metric: irrelevant output costs the reader time directly.

A malformed input record warns on stderr and does **not** abort the run — one bad line in ten
million should not lose the other nine.

For genuinely unexpected failures, give a traceback plus a low-friction bug-report path, and
consider writing the verbose detail to a file rather than the terminal.

## 9 — Follow mode inverts several rules

A mode that never completes plays by different rules, and this is consistently unaddressed:

- **No progress indicator is meaningful** without a known total. Do not fake one.
- **SIGINT is the normal exit path, not an abort — so exit 0.** This contradicts the usual
  convention and is correct here.
- **Flush per record**, or the follow appears frozen while a buffer fills.
- **Line-delimited output only.** A JSON array cannot close.

## Reference files

| File | Contents | Load when |
|---|---|---|
| `references/exit-codes.md` | The table's rationale, and the per-runtime SIGPIPE remedy | Wiring the top-level error handler |
| `references/config-paths.md` | Per-platform locations and precedence worked through | Adding configuration |

## Done means

- `tool … | head -5` exits cleanly, no stack trace, no interpreter shutdown noise
- Colour and progress vanish when piped, when `NO_COLOR` is set, and when `CI` is set
- `--json` output is byte-identical at 80 and 200 columns
- A run matching nothing exits 1; a bad flag exits 2; a script can branch on the difference
- A malformed input record warns and the run continues
- Every error message names a next action
- Follow mode exits 0 on Ctrl-C and flushes per record
- `--help` fits one screen and leads with examples
