# Finding #7 — relative write paths are misclassified after `cd`

**Found:** 2026-09-18, authoring `resilience-patterns` reference files under an `equipping` gate.

## What happened

```
cd ~/.claude/skills/resilience-patterns/references && cat > retry-classification.md <<'EOF' ...
```

Denied, with: *"this command writes `retry-classification.md`, which is a build write."*

The policy was correct to allow it — `equipping` permits writes to `.claude/skills/`. The
**classifier** was wrong: it saw the bare string `retry-classification.md` and had no way to know
the shell had changed directory, so it resolved the target against the project cwd
(`/home/user/HeadHunterAgent`) and concluded the write was landing in the repository root.

## Why it happens

`is_skill_path()` matches on the path containing `.claude/skills/` or `.claude/agents/`. A relative
path emitted after a `cd` contains neither, so it falls through to "build write". The gate never
sees the `cd` because `_executable_fragments` extracts redirect targets lexically — it is a
heuristic over the command string, not a shell.

## Blast radius

Any `cd <dir> && cat > file` or `cd <dir> && tee file` where `<dir>` is a permitted destination.
That includes the gate's own intended workflow: authoring a skill's reference files by changing into
the references directory first, which is the natural way to write several files at once.

## Workaround

**Use absolute paths in redirect targets.** `cat > /root/.claude/skills/<name>/references/<file>`
is classified correctly and the write succeeds.

## Same family as Finding #6

Finding #6 recorded that `cp`, `mv` and `sed -i` write files without being classified as build
writes — the classifier under-detects. This is the mirror: the classifier over-detects when the
path is relative. Both come from the same root cause, which is that command classification is a
lexical heuristic and not a shell, and both are documented rather than chased.

**Possible fix if it is ever worth it:** track a `cd` prefix in `_executable_fragments` and resolve
relative redirect targets against it. That handles the single-`cd` case, which is the common one. It
does not handle `pushd`, a `cd` inside a subshell, or a path built from a variable — so it would
narrow the problem rather than close it, which is the honest framing for any change here.

## Note also

`SKILL.md` hot-loaded the moment it was written — `resilience-patterns` appeared in the
available-skills list with no restart. That is a third confirmation of Finding #5, and the first on
a freshly authored skill in this container.
