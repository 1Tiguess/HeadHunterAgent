# Exit codes and broken pipes

Load when wiring the top-level error handler.

## Contents

- [The table](#the-table)
- [Why "no results" is not an error](#why-no-results-is-not-an-error)
- [SIGPIPE: the mechanism](#sigpipe-the-mechanism)
- [SIGPIPE: per-runtime remedy](#sigpipe-per-runtime-remedy)
- [SIGINT](#sigint)

## The table

| Code | Means | Example |
|---|---|---|
| 0 | Success, matched something | Found and printed 12 records |
| 1 | Ran correctly, matched nothing | Valid query, zero results |
| 2 | Usage error | Unknown flag, missing required argument, mutually exclusive options |
| 3 | Input error | Input was unparseable enough to abort |
| 4 | I/O or permission failure | Cannot open the input, cannot write the output |
| 5 | Interrupted | Ctrl-C during a bounded run |

Neither the design literature nor POSIX assigns actual numbers — POSIX requires only "non-zero
with a diagnostic to stderr". The table above follows the widely-copied grep convention for
0/1/2 and extends it. What matters far more than the specific integers is that they are
**distinct, documented, and stable**. Put them in `--help`.

Two codes that are **not** failures:

- **Broken pipe → 0.** The consumer stopped reading; that is a normal end.
- **Ctrl-C in follow mode → 0.** Interrupting is how you leave a mode that never ends.

## Why "no results" is not an error

For anything that filters, this is the highest-value distinction in the whole table.

A script needs to branch three ways: it worked and found things, it worked and found nothing,
or it did not work. Collapsing the middle case into either neighbour breaks real pipelines:

```sh
if tool --since 1h --level error; then
    echo "errors found"          # exit 0
elif [ $? -eq 1 ]; then
    echo "clean"                 # exit 1 — no matches, not a failure
else
    echo "tool failed" >&2       # exit 2+
    exit 1
fi
```

If every failure exits 1, that middle branch is unreachable and the caller cannot tell a
clean run from a typo. Pick a side, document it, never vary it.

## SIGPIPE: the mechanism

Worth understanding rather than memorising, because the remedy differs per runtime.

A write to a pipe whose read ends are all closed raises **SIGPIPE**. Its default disposition
is to terminate the process — which is exactly what you want, and why `yes | head` works.

But if the process **ignores or handles** SIGPIPE, the signal no longer kills it. The write
syscall returns **`EPIPE`** instead, and it becomes the program's responsibility to notice
and exit quietly.

Many language runtimes install a SIGPIPE handler for you, precisely so that a write error
does not silently kill a server. The consequence for a CLI is that a broken pipe surfaces as
an ordinary I/O error, which an unguarded writer turns into an unhandled exception and a
stack trace.

That is the whole explanation for `| head` producing a traceback. The best CLI design
document available does not mention SIGPIPE once.

## SIGPIPE: per-runtime remedy

**Python.** The interpreter installs a handler, so writes raise `BrokenPipeError`. Catching it
is necessary but not sufficient — the interpreter flushes stdout at shutdown, and if that
flush also fails you get `Exception ignored in: <_io.TextIOWrapper …>` on stderr after your
clean exit. Deal with stdout before exiting:

```python
import os, sys

try:
    main()
except BrokenPipeError:
    # Redirect stdout to devnull so the interpreter's shutdown flush cannot fail.
    devnull = os.open(os.devnull, os.O_WRONLY)
    os.dup2(devnull, sys.stdout.fileno())
    sys.exit(0)
```

**Rust.** `main` ignores SIGPIPE by default, so writes return `Err` with
`ErrorKind::BrokenPipe`. Either restore the default disposition early in `main`, or match on
the error kind and exit 0.

**Go.** The runtime lets SIGPIPE kill the process for file descriptors 1 and 2, which is the
behaviour you want, but returns `EPIPE` on any other descriptor. If you write through a
wrapper that is not literally stdout, check for it.

**Node.** The stream emits an `error` event with `code === 'EPIPE'`. An unhandled `error`
event on a stream throws, so attach a handler on `process.stdout`.

Whatever the runtime: **exiting on a broken pipe is success.** Do not log a warning about it.
The user piped to `head` on purpose.

## SIGINT

Bounded runs: acknowledge before cleanup so the user sees the signal landed, put a timeout on
cleanup, and let a second Ctrl-C skip cleanup entirely. Exit 5.

Follow mode: **exit 0.** Ctrl-C is how the user leaves a mode with no natural end, and
treating it as an error means every wrapper script has to special-case it.

Prefer crash-only design where you can. If startup already handles the case where the previous
run died mid-write, exit can always be immediate and there is nothing to hang.
