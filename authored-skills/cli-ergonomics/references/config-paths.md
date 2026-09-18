# Config locations and precedence

Load when adding configuration.

## Contents

- [Precedence](#precedence)
- [Per-platform locations](#per-platform-locations)
- [The XDG rules people get wrong](#the-xdg-rules-people-get-wrong)
- [Which directory for which data](#which-directory-for-which-data)
- [Project-level config](#project-level-config)
- [Secrets](#secrets)

## Precedence

Highest priority first. Later entries are defaults for earlier ones; nothing merges silently
across levels except within a single config file's own structure.

1. **Command-line flags**
2. **`--config <path>`**, which replaces the discovered user config
3. **Environment variables**
4. **Project-level config** (discovered from the working directory)
5. **User-level config**
6. **System-level config**

Document this order. A user who cannot predict which of two settings wins will stop using
configuration entirely.

Merge semantics need stating too: does a project config *replace* the user config or *layer
over* it key by key? Layering is usually what people expect; replacement is easier to reason
about. Either is defensible, silence is not.

## Per-platform locations

XDG is Unix-only. Most guidance points at it and stops, which leaves two platforms
undefined.

| | Config | State (history, cursors) | Cache |
|---|---|---|---|
| **Linux / BSD** | `$XDG_CONFIG_HOME` → `~/.config/tool/` | `$XDG_STATE_HOME` → `~/.local/state/tool/` | `$XDG_CACHE_HOME` → `~/.cache/tool/` |
| **macOS** | `~/Library/Application Support/tool/` | same | `~/Library/Caches/tool/` |
| **Windows** | `%APPDATA%\tool\` | `%LOCALAPPDATA%\tool\` | `%LOCALAPPDATA%\tool\Cache\` |

macOS note: many cross-platform CLIs use the XDG layout on macOS too, on the grounds that
their users live in a terminal and expect `~/.config`. Both are defensible — pick one, and
if you pick `~/Library`, still honour `XDG_CONFIG_HOME` when it is explicitly set.

System-level config on Unix is `/etc/xdg/tool/` via `$XDG_CONFIG_DIRS`, or `/etc/tool/`.

## The XDG rules people get wrong

Three of them, all of which cause real bugs:

1. **The default applies when the variable is unset *or set to the empty string*.** Code that
   checks only for unset will resolve `XDG_CONFIG_HOME=""` to the empty path and then build
   `/tool/config.toml` at the filesystem root. Check both.
2. **All values must be absolute.** A relative entry is **invalid and must be ignored**, not
   resolved against the working directory. Silently resolving it produces config files
   scattered wherever the tool happened to be run.
3. **The list variables are colon-separated and ordered.** `XDG_CONFIG_DIRS` defaults to
   `/etc/xdg`; `XDG_DATA_DIRS` defaults to `/usr/local/share:/usr/share`. Search them in
   order, first hit wins.

## Which directory for which data

The distinction that gets collapsed most often is state versus config versus cache.

- **Config** — user-authored, hand-editable, safe to check into dotfiles. Your tool never
  writes it without being asked.
- **State** — persists across runs, but the tool wrote it and the user did not author it:
  command history, last-position markers, resume cursors, logs. **Losing it is annoying but
  not destructive.** This is the directory people forget exists, and its contents usually end
  up wrongly in config or cache.
- **Cache** — regenerable. **Deleting it at any moment must be harmless.** If deleting it
  loses information, it was state.

Test: if a user runs `rm -rf` on the directory, what breaks? Nothing → cache. Some
convenience → state. Their settings → config.

## Project-level config

If you support it, answer these explicitly in the docs:

- **Discovery**: exact filename, and whether you walk up from the working directory to a
  repository root or stop at the first directory.
- **Stopping condition**: most tools stop at a `.git` directory or the filesystem root.
  Walking to `/` unbounded is surprising and slow on network filesystems.
- **Multiple hits**: if there are configs at several levels of the walk, does the nearest win
  outright, or do they layer?

## Secrets

**Never accept a secret via a command-line flag.** Flags appear in `ps` output for every user
on the machine and land in shell history.

**Prefer not to accept them via environment variables either.** They leak into child
processes, crash dumps, and CI logs that print the environment.

Do instead:

- read from a file whose path is given by a flag, with a permissions check
- read from stdin when it is not a TTY
- shell out to a credential helper
- accept an interactive prompt when `stdin_is_human`

If you must support an environment variable for CI convenience, name it distinctly, document
the risk, and never echo its value — including in verbose or debug output, which is exactly
where it tends to escape.
