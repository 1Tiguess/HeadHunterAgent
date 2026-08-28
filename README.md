# HeadHunter

A pre-flight gate for Claude Code. It runs **before** Claude starts a hard build,
makes it confirm it actually has the skills to do the job well, and — when it doesn't —
studies published skills read-only, writes build instructions for a similar or improved
skill, gets your approval, and authors it locally from scratch.

**Equip, then build.**

## Why

Claude dives straight into hard builds with whatever capability happens to be lying
around, and the output is mediocre because nobody checked whether better technique was
available first. HeadHunter inverts the order.

The second reason is safety. Skills sourced from the internet are software, and
installing software you found in a search result is how machines get compromised.
HeadHunter is built so that never happens: **it downloads nothing.**

## The one rule that never bends

Nothing is ever downloaded. Not a skill, not a plugin, not an agent, not a repo.
**Not with your approval and not without it** — approval is not a channel through which
a download becomes acceptable, and HeadHunter will never offer you one.

What it does instead:

1. **Studies** how a published skill is specced and built — read-only, over the web
2. **Writes build instructions** for a *similar or improved* skill
3. **Asks you** to approve those instructions
4. **Authors the skill locally**, from scratch, in its own words

The instructions are the deliverable. They're written to be executable by Claude Code
now, or by a future backend agent later, without repeating the research.

## How the gate works

```
you: "build me a dashboard app"
  │
  ├─ arm-gate.py sees a build-shaped request → gate armed
  │
  ├─ Claude tries to write src/App.tsx → build-gate.py denies it
  │
  ├─ the headhunt protocol runs
  │     1 triage      is this actually hard?
  │     2 inventory   what skills does Claude already have?
  │     3 gap         name the missing capability
  │     4 hunt        skill-scout studies, read-only
  │     5 instruct    write .headhunter/specs/<name>.md
  │     6 approval    you approve; you pick project or global
  │     7 author      write the skill, read it back, issue the permit
  │
  └─ Claude builds — now actually equipped
```

Most tasks stop at phase 1 or 2. A gate that fires on everything is a gate people
disable; triage is deliberately quick to clear.

### States

State lives in `$CLAUDE_PLUGIN_DATA/state/<session-id>.json`, outside your git tree, one
file per session so clearance never leaks between them.

| State | Writes allowed |
|---|---|
| *dormant* | everything — not a build task |
| `armed` | `.headhunter/` only |
| `equipping` | `.headhunter/` + skill and agent definitions |
| `cleared` | everything |

`.headhunter/` stays writable in every state. That's the door left open so the gate can
never trap itself.

## Three layers of enforcement

The Claude Code docs are explicit that hooks fail open and are the wrong tool for hard
enforcement. So the guarantee doesn't rest on one mechanism:

1. **Permission rules** (`.claude/settings.json`) — the documented hard-enforcement
   mechanism. Denies `curl`, `wget`, `git clone`, `claude plugin install` outright.
2. **The gate hooks** — state-dependent denials that a static rule can't express.
   Discipline, not security: they fail open by design.
3. **Tool starvation** — `skill-scout` declares `tools: WebSearch, WebFetch, Read,
   Grep, Glob`. No `Write`, no `Edit`, no `Bash`. It is structurally incapable of
   fetching a file to disk, whatever a web page tells it. This is the strongest layer,
   because a tool that is absent cannot be talked into existing.

**This is not a sandbox.** It's three independent layers so no single failure unlocks a
download. A determined adversary who controls the prompt is out of scope.

## Install

```bash
git clone https://github.com/1Tiguess/HeadHunterAgent
cd HeadHunterAgent
bash install.sh --dry-run   # see what it does
bash install.sh             # copy the skill, agent and commands into ~/.claude/
```

`install.sh` copies the pieces and then **prints** the hooks block for you to merge into
`~/.claude/settings.json`. It does not edit that file itself — merging JSON into a config you
may already have tuned is not something a script should do behind your back.

Three things about a global install that are easy to get wrong:

- **Use absolute paths in user-level config, never `${CLAUDE_PROJECT_DIR}`.** That variable
  resolves to whichever project is currently open, not to this checkout, so the hooks silently
  never run. `install.sh` fills the path in for you.
- **Don't take the network deny rules global.** See below.
- **`claude plugin install` will not work**, because HeadHunter refuses it — see the note
  under the deny list.

For one project only, copy `skills/headhunt/`, `agents/skill-scout.md` and `hooks/` into that
project's `.claude/`, and merge `.claude/settings.json` — remembering that the hook paths then
need the extra `.claude/` segment.

### Relaxing the permission rules

The shipped deny list blocks `curl`, `wget`, `git clone` and the PowerShell fetch verbs, which
is the strict reading and the right default **for one repo**. Globally it is disproportionate —
it breaks ordinary work in every project you own. `install.sh` therefore proposes only the three
`claude plugin install` rules for user-level config, which are the ones that matter for skill
acquisition and never interfere with normal work. Add the network rules per-project where a repo
warrants them.

You are not losing much by that split: `build-gate.py` refuses skill downloads independently in
every state, and `skill-scout` has no `Bash` at all. Layers 2 and 3 stay intact.

> **HeadHunter refuses its own plugin installation.** `claude plugin install` is matched
> source-agnostically, so running it from inside a checkout where the hooks are already live
> blocks the install. Use `install.sh`, which needs no plugin command at all.

### Skills the protocol has authored

Runs produce skills, and those are kept separately in [`authored-skills/`](authored-skills/) —
they are outputs of the gate, not part of it. Install them with `bash install-skills.sh`.

### Relaxing the permission rules

The shipped deny list blocks `curl`, `wget`, and `git clone` everywhere, which is the
strict reading and the safe default. If a project genuinely needs them for ordinary
work, drop those three lines from `permissions.deny` in `.claude/settings.json`. Leave
the `claude plugin install` rules — those are the ones that matter for skill
acquisition, and layer 2 keeps enforcing them regardless.

## Usage

Mostly you don't. It arms itself when you ask for a build.

| Command | Does |
|---|---|
| `/headhunt [what you're building]` | Run the protocol on demand |
| `/headhunt-status` | Show the gate state and any specs |
| `/headhunt-release` | Stand the gate down for this session |

Saying "skip headhunt" in any message also stands it down. Release lifts the build
gate; it does not lift the no-download charter.

## Layout

```
.claude-plugin/plugin.json     manifest
MASTER_PROMPT.md               the commissioning prompts, verbatim — the source of truth
skills/headhunt/
  SKILL.md                     the protocol
  references/
    safety-charter.md          the no-download rules and injection handling
    hunt-protocol.md           how phase 4 is run
    spec-template.md           the build-instructions template
    triage-rubric.md           what counts as hard
agents/skill-scout.md          read-only recon subagent
commands/                      /headhunt, /headhunt-status, /headhunt-release
authored-skills/               skills the protocol has produced — outputs, not part of the gate
examples/
  web-app-foundations.spec.md  a worked build-instructions spec, for shape
  test-run-2026-08/            the first end-to-end run: plans, hunts, specs, findings
hooks/
  headhunter_lib.py            state, path and command classification
  arm-gate.py                  UserPromptSubmit — triage and arm
  build-gate.py                PreToolUse — allow or deny
  set-state.py                 advance the gate; how clearance is granted
install.sh                     install the gate into ~/.claude/
install-skills.sh              install authored-skills/ into ~/.claude/skills/
tests/run-tests.sh             77 behaviour tests over the hooks
```

## Tests

```bash
bash tests/run-tests.sh
```

Pipes payloads at the hooks and asserts the decisions — including that corrupt state
fails open, that clearance can't leak across sessions, that skill downloads are refused
in every state including `cleared`, and that a command *mentioning* an install isn't
mistaken for one that performs it.

## Limits

- Hooks only inspect commands they can parse. Layer 1 is the real boundary.
- Shell writes are detected through redirection (`>`, `>>`, `tee`) only. `cp`, `mv`,
  `install`, `rsync` and `sed -i` write files without being classified as build writes, so a
  determined agent can route around the gate with any of them. Enumerating every
  file-writing command is a losing game; this is a discipline mechanism, not a sandbox.
- Command classification blanks quoted spans so that quoting an install in docs or a
  payload doesn't trip the gate, while still unwrapping `sh -c` and `eval` bodies. It is
  a good heuristic, not a shell parser.
- `set-state.py` targets the most recently updated session by default, because Claude
  Code doesn't export a session id to Bash. Pass `--session` when several sessions run
  against the same machine.
- Newly authored skills and agents **were** picked up mid-session on Claude Code for the
  web, without a restart — an earlier version of this list claimed the opposite. Phase 7
  still reads the authored file back, because it is cheap and this may not hold on every
  surface, but treat it as a safety net rather than the mechanism that makes the skill
  available.
- Triage is a keyword heuristic with a judgement pass on top. It will occasionally arm
  on something small — clear it and move on.

## License

MIT
