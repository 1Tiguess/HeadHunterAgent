#!/usr/bin/env bash
# Install HeadHunter itself so the gate runs in every project, not only in this repo.
#
#   bash install.sh --dry-run    # show what would happen, change nothing
#   bash install.sh              # install globally
#
# What this does:
#   - copies the headhunt skill, the skill-scout agent, and the three commands into
#     your user-level Claude config
#   - prints the hooks block to merge into ~/.claude/settings.json, with the absolute
#     path already filled in
#
# What it deliberately does NOT do:
#   - edit your settings.json. Merging JSON into a file you may already have configured
#     is not something a script should do behind your back, so it prints and you paste.
#   - install via `claude plugin install`. HeadHunter refuses that command in every gate
#     state, source-agnostically, so it would block its own installation.

set -euo pipefail

HH="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
DEST="${CLAUDE_CONFIG_DIR:-$HOME/.claude}"
DRY=0

for arg in "$@"; do
  case "$arg" in
    --dry-run) DRY=1 ;;
    -h|--help) sed -n '2,18p' "${BASH_SOURCE[0]}" | sed 's/^# \{0,1\}//'; exit 0 ;;
    *)         printf 'unknown option: %s\n' "$arg" >&2; exit 2 ;;
  esac
done

copy() { # copy <src> <dest-dir> <label>
  if [[ $DRY -eq 1 ]]; then
    printf '  would copy  %s\n' "$3"
  else
    mkdir -p "$2"
    cp -R "$1" "$2"
    printf '  copied      %s\n' "$3"
  fi
}

printf 'Installing HeadHunter from %s\n\n' "$HH"

copy "$HH/skills/headhunt"        "$DEST/skills/"   "skills/headhunt -> $DEST/skills/"
copy "$HH/agents/skill-scout.md"  "$DEST/agents/"   "agents/skill-scout.md -> $DEST/agents/"
for c in "$HH/commands/"*.md; do
  copy "$c" "$DEST/commands/" "commands/$(basename "$c") -> $DEST/commands/"
done

cat <<SETTINGS

Now merge this into $DEST/settings.json.

The absolute paths matter: do NOT use \${CLAUDE_PROJECT_DIR} in user-level config.
It resolves to whichever project is currently open, not to this checkout, so the
hooks would silently fail to run.

{
  "hooks": {
    "UserPromptSubmit": [
      { "hooks": [ { "type": "command", "command": "python3",
          "args": ["$HH/hooks/arm-gate.py"],
          "timeout": 10, "statusMessage": "HeadHunter triage" } ] }
    ],
    "PreToolUse": [
      { "matcher": "Write|Edit|NotebookEdit|Bash",
        "hooks": [ { "type": "command", "command": "python3",
          "args": ["$HH/hooks/build-gate.py"],
          "timeout": 10, "statusMessage": "HeadHunter pre-flight gate" } ] }
    ]
  },
  "permissions": {
    "deny": [
      "Bash(claude plugin install *)",
      "Bash(claude plugin add *)",
      "Bash(claude plugin marketplace add *)"
    ]
  }
}

On the deny list: the three plugin-install rules are the ones that matter for skill
acquisition and they never interfere with ordinary work, so they are safe globally.
The repo's project-level settings.json also denies curl, wget, git clone, aria2c and
the PowerShell fetch verbs. Those are correct scoped to one repo and disproportionate
globally — they would break normal work in every project you own. Add them per-project
where a repo warrants it.

You are not losing the protection by leaving them out: build-gate.py refuses skill
downloads independently in every state, and skill-scout has no Bash at all.

SETTINGS

if [[ $DRY -eq 1 ]]; then
  printf 'dry run: nothing was changed.\n'
else
  printf 'Copied. Merge the block above to finish.\n'
fi
