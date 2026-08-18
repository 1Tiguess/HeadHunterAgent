# Hunt notes — 08 Quarry (CLI ergonomics)

Scout report, reported speech. Read-only. Nothing downloaded, cloned, or installed.
Six sources survived; nothing discarded for injection.

## Access note

`clig.dev`, `no-color.org`, `specifications.freedesktop.org`, `pubs.opengroup.org` and
`anthropic.com` are **egress-blocked** in this environment. Where a canonical document had a
reachable upstream source, the scout read it there and named the route; where it did not, it
flagged the gap rather than filling it from an unverified source.

**clig.dev was read at `github.com/cli-guidelines/cli-guidelines` (`content/_index.md`).**
Justified: that repository is not a mirror or a reposter — it is the repository that
*generates* clig.dev, by the same four authors. Same document, upstream of the site, no
third party in between.

## Tier 1 — skill construction

**`docs.claude.com/…/agent-skills/best-practices`** (302s to `platform.claude.com`).
The `description` is the only thing resident at startup, doing selection work against 100+
competing skills. Two distinct payloads — what the skill does, and the situational triggers
— written in **third person**, because it is spliced into the system prompt and a
first/second-person voice degrades discovery. Concrete-noun trigger terms matter more than
elegant phrasing.

Match instruction specificity to how fragile the task is: several legitimate approaches →
give direction and let the model route; brittle or order-dependent → give the exact
invocation and say not to vary it. The guide's framing is *a narrow bridge versus an open
field*.

Progressive disclosure is filesystem-shaped: bundled files cost zero context until read.
Body under ~500 lines. References must sit **one level deep** — a reference pointing at a
further reference tends to get partially read (the model previews with `head`) and the
instruction arrives truncated. Any reference over ~100 lines opens with its own table of
contents so a partial read still reveals full scope.

Complex procedures: a numbered sequence with a copyable progress checklist. Quality-critical
steps: a loop — run a validator, read the specific error, fix, re-run, advance only when
clean.

Named anti-patterns: a menu of equivalent options instead of one default plus a documented
escape hatch; drifting terminology (one word per concept, never synonymise); baked-in dates
or "as of version X" (put those in a collapsed "old patterns" section); and — directly
relevant here — **writing ALWAYS/NEVER in caps is usually a symptom that the reasoning was
omitted**, and stating *why* generalises better to edge cases than shouting the rule.

**`code.claude.com/docs/en/skills`.** Full frontmatter surface: `name`, `description`,
`allowed-tools`, `disallowed-tools`, `disable-model-invocation`, `argument-hint`,
`arguments`, `context`, `paths`, `metadata`, `license`, `compatibility`. Only six are
portable to claude.ai uploads and the Skills API — the rest hard-error there. For
personal/project skills the invocable command comes from the **directory name**, not
frontmatter `name`; `name` only sets the display label. `${CLAUDE_SKILL_DIR}` is the correct
way for a body to reference its own bundled scripts irrespective of cwd.

**`github.com/anthropics/skills/…/skill-creator/SKILL.md`.** Body is **hierarchical with
conditional branches**, not one linear script: a short workflow overview, then phase blocks,
then environment-conditional sections at the bottom ("if you're on claude.ai, skip the parts
needing subagents"). Capability-dependent degradation handled as an explicit late section
rather than caveats sprinkled through the steps. Where a run of steps must not be abandoned
midway, it says so **in-band**. Content split: deterministic repeatable work → `scripts/`
and *executed*; decision trees and rationale → SKILL.md; schemas → `references/`; subagent
roles → `agents/`. Carries explicit refusals (no malware or exfiltration tooling, don't
build deliberately misleading skills) *and* explicit capability refusals ("this step needs
the `claude` CLI, skip if unavailable"). ~7 named handback points, plus an exit criterion for
the iteration loop. It opens with a **flexibility clause** stating the whole documented
workflow is a default the user may wave off — that one sentence is what stops a prescriptive
skill becoming obnoxious.

## Tier 2 — the craft

**clig.dev (read at source repo).** The dense source; addresses most of the gap directly.

*Streams.* Primary output and anything machine-consumable → stdout, because that is what a
pipe captures. Diagnostics, logs, errors → stderr, so in a pipeline they reach the human
instead of being fed to the next process. Corollary stated separately: don't treat stderr as
a logfile by default — no severity prefixes, no timestamps, no contextual noise unless
verbose is on.

*TTY as the human-detection heuristic.* Whether a stream is a terminal is the test for
whether a human is reading. Check each stream **independently** — piping stdout doesn't mean
stderr shouldn't be coloured. When stdout isn't a TTY, animations stop (stated motivation:
progress bars turning CI logs into garbage). Prompts require **stdin** to be a TTY. Paging
requires an interactive terminal.

*Colour suppression* has five independent triggers, any of which disables it: stream isn't a
TTY; `NO_COLOR` set and non-empty; `TERM` = `dumb`; `--no-color` passed; optionally a
tool-specific `MYAPP_NO_COLOR`.

*SIGINT.* Acknowledge **before** starting cleanup so the user knows the signal landed; put a
timeout on cleanup so it can't hang; treat a second Ctrl-C during cleanup as permission to
skip cleanup entirely (cited example: Docker Compose's "press Ctrl+C again to force"). The
deeper principle is **crash-only design** — assume the previous run died without cleaning
up, defer cleanup to the next start, so exit can always be immediate.

*Args vs flags vs subcommands.* Prefer flags over positionals — more typing, but
self-documenting and evolvable. Multiple positionals are fine when homogeneous (many files);
two positionals meaning *different* things is a design smell. Subcommands: keep flag names
and output formats consistent across them, prefer `noun verb` ordering, refuse arbitrary
prefix abbreviation (it permanently reserves the namespace), and **never add a catch-all
default subcommand** — it blocks you from ever adding a new one without breaking scripts.

*Standard flag names*, treated as near-obligatory where a convention exists: `-a/--all`,
`-d/--debug`, `-f/--force`, `-h/--help` (reserved exclusively for help), `-n/--dry-run`,
`-o/--output`, `-p/--port`, `-q/--quiet`, `-u/--user`, `-v` (ambiguous between verbose and
version — disambiguate deliberately), `--version`, `--json`, `--no-input`. Every flag gets a
long form; short forms rationed to genuinely frequent ones.

*Help.* Full help on `-h`/`--help`, honoured anywhere including on subcommands, ignoring
other arguments. Invoked with no arguments but arguments required → print a **short** help
(description, an example or two, a pointer to `--help`), not the wall. Lead with examples,
because that is what people read. Paginate only when output is long *and* the stream is
interactive; suggests `less -FIRX` so short output isn't needlessly paged and stays on screen
after quitting. If the tool expects piped input and stdin is a terminal, print help and exit
rather than silently blocking like bare `cat`.

*Machine-readable output as a mode, not an afterthought.* `--json` for structured output; a
`--plain` tabular mode for when the pretty rendering would break `grep`/`awk`. The escape
valve this buys is explicit: **because** stable machine modes exist, you are permitted to
keep changing the human format.

*Config precedence*, highest to lowest: flags → environment variables → project config →
user config → system-wide. Config location follows XDG. General-purpose environment
variables a well-behaved tool honours: `NO_COLOR`, `DEBUG`, `EDITOR`, `PAGER`, `TERM`,
`TMPDIR`, `HOME`, `HTTP_PROXY`, `LINES`, `COLUMNS`. **Secrets must not come from flags**
(they leak into `ps` and shell history) nor from environment variables.

*Responsiveness.* Emit something within 100ms; print *before* a network call, not after. A
stalled progress bar is indistinguishable from a crash, so include an ETA or a moving
element. Parallel progress reporting is called out as disproportionately hard to get right
without interleaving corruption.

*Errors.* Catch expected failures and rewrite them conversationally, stating the **remedy** —
its illustration is a write failure that also gives the `chmod` command that would fix it.
Signal-to-noise is the governing metric. Put the most important line **last**, since that is
where the eye lands. For unexpected failures, provide traceback plus a low-friction
bug-report path, ideally a pre-populated URL, and consider writing verbose detail to a file
rather than the terminal.

*Compatibility.* Keep changes additive — new flags rather than repurposed ones — and warn
before non-additive changes.

*Exit codes.* Zero on success, non-zero on failure, and map distinct non-zero codes onto the
important failure modes. **That is the entirety of what it says.**

**man7 `signal.7` and `pipe.7`** — the mechanism clig.dev omits. SIGPIPE's default
disposition is process termination, raised when a write targets a pipe whose read ends are
all closed. The pivotal detail: if the process **ignores or handles** SIGPIPE, the write
doesn't kill it — the syscall returns `EPIPE` instead, and it becomes the program's job to
notice and exit quietly. This is exactly the mechanism behind `| head` producing a stack
trace: a runtime that masks SIGPIPE turns termination into an ordinary write error, which an
unguarded writer surfaces as an unhandled exception.

**XDG base directory spec** (via search; direct fetch blocked). Defaults apply when the
variable is **either unset or set to the empty string** — the empty case is the one
implementations routinely get wrong. `XDG_CONFIG_HOME` → `~/.config`, `XDG_DATA_HOME` →
`~/.local/share`, `XDG_STATE_HOME` → `~/.local/state`, `XDG_CACHE_HOME` → `~/.cache`,
`XDG_CONFIG_DIRS` → `/etc/xdg`, `XDG_DATA_DIRS` → `/usr/local/share:/usr/share`. All values
must be absolute; a relative entry is invalid and must be **ignored**, not resolved. The
**state** directory is the right home for things persisting across runs that aren't
user-authored config and aren't safely disposable like cache — logs, history, last-position
markers.

**POSIX Utility Conventions** (via search; direct fetch blocked). Options are `-`-prefixed
single characters; options without arguments may be grouped behind one `-`, with at most one
option-taking-an-argument permitted at the end of such a group. The first standalone `--`
terminates option parsing, and utilities taking no options at all are still required to
accept and discard a leading `--`. On an unrecognised option or missing option-argument the
standard requires a diagnostic to **stderr** and a **non-zero** exit — but does not name the
number.

## Synthesis

**1. "Is a human reading this?" is one decision made per-stream, computed once and consulted
everywhere.** Almost every symptom in the gap is the same bug: colour, progress animation,
prompting, paging, width-dependent column sizing and table borders are each written as an
independent ad-hoc check, and each gets it wrong somewhere different. The resolution order is
small — explicit flag beats environment variable beats stream-is-a-TTY — and stdout and
stderr must be evaluated separately, because progress on stderr stays legitimate while stdout
is piped. **Terminal width deserves the same treatment:** when stdout isn't a terminal there
is no width, so a fixed layout must be used rather than a `COLUMNS` fallback, otherwise
output silently varies with the window of whoever launched the job.

**2. Exit codes and stream discipline are the machine-facing API, and clig.dev
under-specifies exactly the part Quarry needs.** Consensus on shape is unambiguous; but for a
*filter*, the single most important distinction is "ran fine, matched nothing" versus "you
typed the flag wrong", and neither clig.dev nor POSIX assigns numbers to those. That is ours
to decide and state explicitly, because a CI pipeline gating on Quarry's result cannot
function without it.

**3. Streaming and machine-readability are in tension no source resolves.** clig.dev's
`--json` recommendation is "formatted JSON", which implicitly means a buffered document with
a closing bracket. A tool that streams 10GB and has a follow mode cannot produce that — a
follow-mode JSON array never terminates, and buffering to close it defeats the premise. The
reconciliation (line-delimited objects, flushed per record, so a consumer reads incrementally
and `head` can truncate safely) follows from the tool's nature, not from any source found.
Related: **SIGPIPE is the seam where streaming and composability meet, and clig.dev — the
best CLI-design document available — does not mention it once**, despite `| head` being the
single most common way a user interrupts a streaming tool.

## Improvement openings

1. **No exit-code numbering scheme anywhere.** clig.dev says "map non-zero codes to failure
   modes" and stops; POSIX says "non-zero" and stops. Neither names a value. The de facto
   conventions that would actually close the gap — grep's 0/1/2 split where **1 means *no
   matches found*** and 2 an actual error, GNU's habit of 2 for usage errors, BSD
   `sysexits.h` with `EX_USAGE=64` — appear in no allowlisted source. A skill that says only
   "use meaningful exit codes" reproduces the gap. **Naming a concrete table, and picking a
   side on the grep-style "empty result is not an error but is distinguishable" question, is
   the highest-value thing we can add.**
2. **SIGPIPE is entirely absent from clig.dev**, which covers SIGINT well. Worse, correct
   handling is language-specific in a way no design document captures: Python installs a
   SIGPIPE-ignoring handler and raises `BrokenPipeError` (and can *still* print "Exception
   ignored" noise at interpreter shutdown unless stdout is dealt with before exit), Rust
   ignores SIGPIPE by default in `main`, Go returns `EPIPE` on non-standard descriptors but
   lets the signal kill the process for fds 1 and 2, Node emits an `EPIPE` error event. The
   sources give the kernel mechanism and the design silence; **the runtime-specific remedy is
   unwritten and is exactly what makes `| head` produce a stack trace.**
3. **clig.dev's "changing output for humans is usually OK" is a hazard as stated.** Sound
   *only* if machine modes are genuinely stable and users know to use them. Paired with
   width-dependent formatting it reads as licence for output to be unstable. Better: state the
   contract explicitly — the human format carries no compatibility promise, `--json`/`--csv`
   do, and the human format never varies with anything unobservable to the caller.
4. **XDG is Unix-only, and the task says "per platform".** Nothing on `%APPDATA%` /
   `%LOCALAPPDATA%` or `~/Library/Application Support`; clig.dev points at XDG and moves on.
   Also unaddressed by both: how an explicit `--config <path>` slots into the five-level
   precedence list, and whether project config is discovered by walking up from cwd.
5. **TTY detection is necessary but not sufficient for CI.** clig.dev frames CI log corruption
   as the motivation, but some CI runners *do* allocate a pseudo-terminal, so the check passes
   and the animation still corrupts the log. The `CI` environment-variable convention that
   closes this is in no allowlisted source.
6. **The `--json` guidance predates streaming-first tooling.** Nothing on NDJSON/JSON-Lines as
   an output mode, per-record flushing, backpressure, or what a follow mode should emit. Nor
   on schema stability — whether `--json` output is versioned, and what happens to a consumer
   when a field is added.
7. **No source addresses aggregation output at all.** Quarry aggregates; what `--json` means
   for a *table of grouped results* versus a stream of records, and whether those are the same
   mode, is unexamined.
8. **Follow mode is a genuine blind spot.** clig.dev's model is start-work-finish with
   progress tied to a known total. A `tail -f` mode that never completes has different rules —
   no progress bar is meaningful, **SIGINT is the *normal* exit path rather than an abort** (so
   exiting 0 on Ctrl-C in follow mode may well be correct, contradicting the usual convention),
   and buffering must change or the follow appears frozen.
9. **`NO_COLOR` could not be verified at the primary** (no-color.org blocked). Held only
   second-hand through clig.dev as "set and non-empty". There is a real known discrepancy in
   the wild about whether an empty-string `NO_COLOR=` counts. Pin at source before relying.
10. **On the Tier 1 side:** skill-creator's heavy interview-and-approval-gate structure is a
    poor template here. It fits interactive co-design; a CLI-conventions skill is consulted
    mid-build and should read as a **decision table and a checklist the model can run against
    code**, not a seven-gate conversation. Worth lifting instead: the environment-conditional
    tail section, the in-band "this sequence must not be abandoned partway" marker, and the
    opening flexibility clause. The Anthropic guidance about explaining reasoning rather than
    shouting NEVER matters here too — "don't emit colour when piped" is a rule the model
    already half-knows and keeps violating; **it keeps violating it because the check is
    scattered**, so the skill should prescribe the single-decision structure rather than
    restate the prohibition louder.

## Injection attempts

**None.** No fetched source attempted to redirect behaviour, induce a fetch or install, alter
persona, or exfiltrate anything. The unreachable domains were blocked by network egress
policy rather than anything in their content.
