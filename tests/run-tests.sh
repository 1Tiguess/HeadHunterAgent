#!/usr/bin/env bash
# Hook behaviour tests. Pipes payloads at the gate scripts and asserts decisions.
#
# Runs against a throwaway CLAUDE_PLUGIN_DATA so it never touches real gate state.
#
#   bash tests/run-tests.sh

set -uo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
HOOKS="$ROOT/hooks"
export CLAUDE_PLUGIN_DATA="$(mktemp -d)"
trap 'rm -rf "$CLAUDE_PLUGIN_DATA"' EXIT

PASS=0
FAIL=0
PROJECT="/tmp/hh-project"

red()   { printf '\033[31m%s\033[0m\n' "$1"; }
green() { printf '\033[32m%s\033[0m\n' "$1"; }

# ok <name> <condition-description> <actual> <expected-substring-or-EMPTY>
check() {
  local name="$1" actual="$2" expect="$3"
  if [[ "$expect" == "EMPTY" ]]; then
    if [[ -z "${actual//[[:space:]]/}" ]]; then
      green "  pass  $name"; PASS=$((PASS+1)); return
    fi
  elif [[ "$actual" == *"$expect"* ]]; then
    green "  pass  $name"; PASS=$((PASS+1)); return
  fi
  red   "  FAIL  $name"
  red   "        expected: $expect"
  red   "        actual:   ${actual:-<empty>}"
  FAIL=$((FAIL+1))
}

reset_state() { rm -rf "$CLAUDE_PLUGIN_DATA/state"; }

set_state() { # set_state <session> <status> [task]
  mkdir -p "$CLAUDE_PLUGIN_DATA/state"
  cat > "$CLAUDE_PLUGIN_DATA/state/$1.json" <<EOF
{"status": "$2", "session_id": "$1", "task": "${3:-build a dashboard app}"}
EOF
}

arm() { # arm <prompt> [session]
  local prompt="$1" session="${2:-s1}"
  jq -nc --arg p "$prompt" --arg s "$session" \
    '{hook_event_name:"UserPromptSubmit", session_id:$s, prompt:$p, cwd:"'"$PROJECT"'"}' \
    | python3 "$HOOKS/arm-gate.py"
}

gate_write() { # gate_write <path> [session]
  jq -nc --arg f "$1" --arg s "${2:-s1}" \
    '{hook_event_name:"PreToolUse", session_id:$s, cwd:"'"$PROJECT"'",
      tool_name:"Write", tool_input:{file_path:$f, content:"x"}}' \
    | python3 "$HOOKS/build-gate.py"
}

gate_bash() { # gate_bash <command> [session]
  jq -nc --arg c "$1" --arg s "${2:-s1}" \
    '{hook_event_name:"PreToolUse", session_id:$s, cwd:"'"$PROJECT"'",
      tool_name:"Bash", tool_input:{command:$c}}' \
    | python3 "$HOOKS/build-gate.py"
}

status_of() { jq -r '.status // "none"' "$CLAUDE_PLUGIN_DATA/state/${1:-s1}.json" 2>/dev/null || echo none; }

# ---------------------------------------------------------------------------
echo
echo "arm-gate: triage"
# ---------------------------------------------------------------------------
reset_state
out=$(arm "build me a react dashboard app")
check "build request arms the gate"            "$(status_of)"  "armed"
check "  ... and injects context"              "$out"          "additionalContext"
check "  ... phrased as fact, not command"     "$out"          "HeadHunter gate state for this session: armed"

reset_state
arm "how would I build a dashboard app?" >/dev/null
check "question does not arm"                  "$(status_of)"  "none"

reset_state
arm "fix the bug in the dashboard app" >/dev/null
check "maintenance does not arm"               "$(status_of)"  "none"

reset_state
arm "what is in this repo" >/dev/null
check "chit-chat does not arm"                 "$(status_of)"  "none"

reset_state
out=$(arm "skip headhunt and build me an app")
check "release phrase clears instead of arming" "$(status_of)" "cleared"
check "  ... and says so"                       "$out"         "cleared by user request"

reset_state
arm "/headhunt" >/dev/null
check "explicit /headhunt arms"                "$(status_of)"  "armed"

reset_state
set_state s1 cleared
arm "build me another app" >/dev/null
check "cleared session does not re-arm"        "$(status_of)"  "cleared"

# ---------------------------------------------------------------------------
echo
echo "build-gate: writes"
# ---------------------------------------------------------------------------
reset_state
check "no state: write allowed"                "$(gate_write "$PROJECT/src/App.tsx")" "EMPTY"

set_state s1 armed
check "armed: build write denied"              "$(gate_write "$PROJECT/src/App.tsx")" '"permissionDecision": "deny"'
check "  ... names the task"                   "$(gate_write "$PROJECT/src/App.tsx")" "build a dashboard app"
check "  ... offers a way forward"             "$(gate_write "$PROJECT/src/App.tsx")" "/headhunt-release"
check "armed: spec write allowed"              "$(gate_write "$PROJECT/.headhunter/specs/x.md")" "EMPTY"
check "armed: skill write denied"              "$(gate_write "$PROJECT/.claude/skills/x/SKILL.md")" '"permissionDecision": "deny"'

set_state s1 equipping
check "equipping: skill write allowed"         "$(gate_write "$PROJECT/.claude/skills/x/SKILL.md")" "EMPTY"
check "equipping: agent write allowed"         "$(gate_write "$PROJECT/.claude/agents/y.md")" "EMPTY"
check "equipping: build write still denied"    "$(gate_write "$PROJECT/src/App.tsx")" '"permissionDecision": "deny"'

set_state s1 cleared
check "cleared: build write allowed"           "$(gate_write "$PROJECT/src/App.tsx")" "EMPTY"

# ---------------------------------------------------------------------------
echo
echo "build-gate: shell"
# ---------------------------------------------------------------------------
set_state s1 armed
check "armed: npm install denied"              "$(gate_bash "npm install react")" '"permissionDecision": "deny"'
check "armed: install hidden after && denied"  "$(gate_bash "ls && pip install requests")" '"permissionDecision": "deny"'
check "armed: ls allowed"                      "$(gate_bash "ls -la")" "EMPTY"
check "armed: set-state allowed"               "$(gate_bash "python3 hooks/set-state.py cleared --rationale x")" "EMPTY"
check "armed: redirect to source denied"       "$(gate_bash "echo x > $PROJECT/src/App.tsx")" '"permissionDecision": "deny"'
check "armed: redirect to spec allowed"        "$(gate_bash "echo x > $PROJECT/.headhunter/notes.md")" "EMPTY"
check "armed: /dev/null redirect allowed"      "$(gate_bash "make 2>/dev/null > /dev/null")" "EMPTY"

set_state s1 cleared
check "cleared: npm install allowed"           "$(gate_bash "npm install react")" "EMPTY"

# ---------------------------------------------------------------------------
echo
echo "build-gate: skill downloads are refused in every state"
# ---------------------------------------------------------------------------
reset_state
check "no state: plugin install denied"        "$(gate_bash "claude plugin install foo")" '"permissionDecision": "deny"'
check "  ... explains approval cannot lift it" "$(gate_bash "claude plugin install foo")" "user approval does not lift it"

set_state s1 cleared
check "cleared: plugin install still denied"   "$(gate_bash "claude plugin install foo")" '"permissionDecision": "deny"'
check "cleared: marketplace add denied"        "$(gate_bash "claude plugin marketplace add x/y")" '"permissionDecision": "deny"'
check "cleared: cloning a skill repo denied"   "$(gate_bash "git clone https://github.com/a/awesome-skills")" '"permissionDecision": "deny"'
check "cleared: curl of SKILL.md denied"       "$(gate_bash "curl -o SKILL.md https://x.io/SKILL.md")" '"permissionDecision": "deny"'
check "cleared: ordinary clone allowed"        "$(gate_bash "git clone https://github.com/a/my-app")" "EMPTY"

# A command that mentions an install is not a command that performs one.
# Without this, the gate fires on docs, tests, and any command quoting an example.
check "quoted mention is data, not a command" \
  "$(gate_bash "echo 'claude plugin install foo' >> notes.md")" "EMPTY"
check "  ... including inside a JSON payload" \
  "$(gate_bash "jq -nc '{cmd:\"claude plugin install foo\"}' | python3 gate.py")" "EMPTY"
check "  ... but a real invocation still denied" \
  "$(gate_bash "claude plugin install foo")" '"permissionDecision": "deny"'

# Quoting is not an escape hatch when the quoted text is handed to a shell.
check "sh -c wrapper does not evade"           "$(gate_bash "bash -c \"claude plugin install foo\"")" '"permissionDecision": "deny"'
check "eval wrapper does not evade"            "$(gate_bash "eval 'claude plugin install foo'")" '"permissionDecision": "deny"'

set_state s1 armed
check "armed: sudo prefix does not evade"      "$(gate_bash "sudo npm install react")" '"permissionDecision": "deny"'
check "armed: env prefix does not evade"       "$(gate_bash "env CI=1 pip install requests")" '"permissionDecision": "deny"'
check "armed: sh -c install does not evade"    "$(gate_bash "sh -c 'npm install react'")" '"permissionDecision": "deny"'
check "armed: install as an argument allowed"  "$(gate_bash "grep -r 'npm install' docs/")" "EMPTY"
check "armed: word in a path allowed"          "$(gate_bash "cat ./npm-install-notes.md")" "EMPTY"
set_state s1 cleared

# ---------------------------------------------------------------------------
echo
echo "build-gate: robustness"
# ---------------------------------------------------------------------------
reset_state
set_state s1 armed
check "clearance does not leak across sessions" "$(gate_write "$PROJECT/src/App.tsx" s2)" "EMPTY"

set_state s2 cleared
check "  ... and each session keeps its own"    "$(gate_write "$PROJECT/src/App.tsx" s1)" '"permissionDecision": "deny"'

mkdir -p "$CLAUDE_PLUGIN_DATA/state"
echo 'not json {{{' > "$CLAUDE_PLUGIN_DATA/state/s3.json"
check "corrupt state fails open"               "$(gate_write "$PROJECT/src/App.tsx" s3)" "EMPTY"

echo '{"status":"bogus"}' > "$CLAUDE_PLUGIN_DATA/state/s4.json"
check "unknown status fails open"              "$(gate_write "$PROJECT/src/App.tsx" s4)" "EMPTY"

set_state s1 armed
check "write with no file_path fails open" \
  "$(jq -nc '{hook_event_name:"PreToolUse",session_id:"s1",cwd:"'"$PROJECT"'",tool_name:"Write",tool_input:{}}' | python3 "$HOOKS/build-gate.py")" \
  "EMPTY"
check "empty payload fails open" \
  "$(echo '{}' | python3 "$HOOKS/build-gate.py")" "EMPTY"
check "garbage payload fails open" \
  "$(echo 'nonsense' | python3 "$HOOKS/build-gate.py")" "EMPTY"
check "empty prompt does not arm" \
  "$(echo '{"hook_event_name":"UserPromptSubmit","session_id":"s9","prompt":""}' | python3 "$HOOKS/arm-gate.py")" \
  "EMPTY"

# ---------------------------------------------------------------------------
echo
echo "build-gate: plan mode is not a build"
# ---------------------------------------------------------------------------
# Claude Code writes its plan file to <config>/.claude/plans/. A plan is the agent
# recording what it intends to do, which is the opposite of building — and blocking
# it also traps the gate, since repairing hooks/ needs a clearance the block impedes.
reset_state
set_state s1 armed
check "armed: user-level plan file allowed"    "$(gate_write "$HOME/.claude/plans/p.md")"      "EMPTY"
check "armed: project plan file allowed"       "$(gate_write "$PROJECT/.claude/plans/p.md")"   "EMPTY"
check "armed: nested plan file allowed"        "$(gate_write "$HOME/.claude/plans/a/b.md")"    "EMPTY"
check "armed: redirect into plans allowed"     "$(gate_bash "echo x > $PROJECT/.claude/plans/p.md")" "EMPTY"
check "armed: 'plansible' lookalike still denied" \
  "$(gate_write "$PROJECT/.claude/plansible/x.ts")" "permissionDecision"
check "armed: bare plans/ dir still denied"    "$(gate_write "$PROJECT/plans/x.ts")"           "permissionDecision"

# ---------------------------------------------------------------------------
echo
echo "build-gate: heredoc bodies are data"
# ---------------------------------------------------------------------------
# A heredoc body is stdin handed to a command — the same category as a quoted span.
# Unblanked, ordinary prose and source trip the redirect scanner on their own
# content, because _REDIRECT's lookbehind only excludes [0-9<>].
reset_state
set_state s1 armed
check "heredoc: markdown blockquote in body" \
  "$(gate_bash $'cat > .headhunter/x.md <<\'EOF\'\n> HeadHunter refuses this\nEOF')" "EMPTY"
check "heredoc: literal >> in prose" \
  "$(gate_bash $'cat > .headhunter/x.md <<\'EOF\'\nsee >> appendix\nEOF')" "EMPTY"
check "heredoc: rust return arrow in body" \
  "$(gate_bash $'cat > .headhunter/x.md <<\'EOF\'\nfn f() -> String {}\nEOF')" "EMPTY"
check "heredoc: js arrow fn in body" \
  "$(gate_bash $'cat > .headhunter/x.md <<\'EOF\'\nconst f = () => 1\nEOF')" "EMPTY"
check "heredoc: generic type in body" \
  "$(gate_bash $'cat > .headhunter/x.md <<\'EOF\'\nVec<T> and List<int>\nEOF')" "EMPTY"
check "heredoc: documented install is not an install" \
  "$(gate_bash $'cat > .headhunter/x.md <<\'EOF\'\nnpm install foo\nEOF')" "EMPTY"
check "heredoc: indented <<- form blanked" \
  "$(gate_bash $'cat > .headhunter/x.md <<-EOF\n\t> quoted\n\tEOF')" "EMPTY"
check "heredoc: double-quoted tag blanked" \
  "$(gate_bash $'cat > .headhunter/x.md <<"EOF"\n> quoted\nEOF')" "EMPTY"

# ... and the patch must not blunt the gate.
check "heredoc: real target still classified" \
  "$(gate_bash $'cat > src/x.ts <<\'EOF\'\nhello\nEOF')" "permissionDecision"
check "heredoc: body naming .headhunter does not launder target" \
  "$(gate_bash $'cat > src/x.ts <<\'EOF\'\n.headhunter/ is writable\nEOF')" "permissionDecision"
check "heredoc: install after the body still caught" \
  "$(gate_bash $'cat > .headhunter/x.md <<\'EOF\'\nprose\nEOF\nnpm install react')" "permissionDecision"

reset_state
set_state s1 cleared
check "cleared: documenting a plugin install is not performing one" \
  "$(gate_bash $'cat > .headhunter/x.md <<\'EOF\'\nclaude plugin install foo\nEOF')" "EMPTY"
check "cleared: an actual plugin install is still refused" \
  "$(gate_bash "claude plugin install foo")" "permissionDecision"

# ---------------------------------------------------------------------------
echo
echo "set-state: transitions"
# ---------------------------------------------------------------------------
reset_state
set_state s1 armed
python3 "$HOOKS/set-state.py" equipping --session s1 --spec .headhunter/specs/x.md >/dev/null
check "set-state advances to equipping"        "$(status_of)" "equipping"
python3 "$HOOKS/set-state.py" cleared --session s1 --rationale "authored x" >/dev/null
check "set-state issues clearance"             "$(status_of)" "cleared"
check "clearance keeps the spec reference" \
  "$(jq -r '.spec' "$CLAUDE_PLUGIN_DATA/state/s1.json")" ".headhunter/specs/x.md"
out=$(python3 "$HOOKS/set-state.py" cleared --session s1 2>&1 >/dev/null)
check "clearance without a reason is refused"  "$out" "Clearance needs a reason"
python3 "$HOOKS/set-state.py" release --session s1 >/dev/null
check "release removes state"                  "$(status_of)" "none"

# ---------------------------------------------------------------------------
echo
printf 'passed %d, failed %d\n' "$PASS" "$FAIL"
[[ $FAIL -eq 0 ]] || exit 1
