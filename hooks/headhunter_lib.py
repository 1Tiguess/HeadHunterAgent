"""Shared state and I/O helpers for the HeadHunter gate hooks.

Design rules that the rest of the gate depends on:

1.  **Fail open, always.** A gate that crashes must never brick a session. Every
    entry point wraps its work in a broad ``except`` and exits 0 silently.

2.  **Never emit ``permissionDecision: "allow"``.** "Allow" means *skip the normal
    permission prompt*, which would make the gate an auto-approver — the opposite
    of its job. The gate has exactly two outputs: ``deny``, or silence. Silence
    means "no opinion, run the normal permission flow".

3.  **State lives outside the project tree.** ``$CLAUDE_PROJECT_DIR`` is the user's
    git working tree; dropping runtime files there makes sibling hooks (like a
    stop-hook git check) demand a commit for our scratch data. State goes to
    ``$CLAUDE_PLUGIN_DATA`` when present, else ``~/.headhunter``.

4.  **State is keyed by session id.** Clearance granted in one session must not
    silently authorize another.
"""

from __future__ import annotations

import json
import os
import re
import sys
import time
from pathlib import Path

# The gate's three live states, in the order they are reached.
ARMED = "armed"  # build detected, no clearance: build writes denied
EQUIPPING = "equipping"  # spec approved, authoring skills: skill writes allowed
CLEARED = "cleared"  # permit issued: gate stands down

ACTIVE_STATES = (ARMED, EQUIPPING)

WRITE_TOOLS = ("Write", "Edit", "NotebookEdit")


# --------------------------------------------------------------------------
# Locations
# --------------------------------------------------------------------------


def state_dir() -> Path:
    """Directory holding per-session gate state. Never inside the project tree."""
    base = os.environ.get("CLAUDE_PLUGIN_DATA", "").strip()
    if not base:
        base = os.path.join(os.path.expanduser("~"), ".headhunter")
    return Path(base) / "state"


def state_path(session_id: str) -> Path:
    safe = re.sub(r"[^A-Za-z0-9_.-]", "_", session_id or "unknown")
    return state_dir() / f"{safe}.json"


def spec_dir(cwd: str) -> Path:
    """Where specs and hunt notes are written. Inside the project, on purpose:
    specs are a deliverable the user reviews and may want to commit."""
    return Path(cwd or os.getcwd()) / ".headhunter"


# --------------------------------------------------------------------------
# State I/O
# --------------------------------------------------------------------------


def read_state(session_id: str) -> dict | None:
    """Return the state dict, or None if absent/unreadable.

    Unreadable is deliberately indistinguishable from absent: a corrupt state
    file must open the gate, not wedge it shut.
    """
    try:
        raw = state_path(session_id).read_text(encoding="utf-8")
        data = json.loads(raw)
        if not isinstance(data, dict):
            return None
        if data.get("status") not in (ARMED, EQUIPPING, CLEARED):
            return None
        return data
    except Exception:
        return None


def write_state(session_id: str, status: str, **fields) -> dict:
    """Persist state atomically. Returns the written dict."""
    data = read_state(session_id) or {}
    data.update(fields)
    data["status"] = status
    data["session_id"] = session_id
    data["updated_at"] = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())

    path = state_path(session_id)
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(".json.tmp")
    tmp.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")
    tmp.replace(path)
    return data


def clear_state(session_id: str) -> None:
    try:
        state_path(session_id).unlink()
    except Exception:
        pass


# --------------------------------------------------------------------------
# Hook I/O
# --------------------------------------------------------------------------

# Claude Code truncates hook output at 10,000 characters.
MAX_OUTPUT = 9_500


def read_payload() -> dict:
    try:
        data = json.loads(sys.stdin.read() or "{}")
        return data if isinstance(data, dict) else {}
    except Exception:
        return {}


def _emit(obj: dict) -> None:
    text = json.dumps(obj)
    if len(text) > MAX_OUTPUT:
        text = text[:MAX_OUTPUT]
    sys.stdout.write(text)
    sys.stdout.flush()


def emit_deny(reason: str) -> None:
    """Deny a tool call. ``permissionDecisionReason`` is the only field on a deny
    that Claude itself sees, so all of the gate's reasoning goes there."""
    _emit(
        {
            "hookSpecificOutput": {
                "hookEventName": "PreToolUse",
                "permissionDecision": "deny",
                "permissionDecisionReason": reason[:MAX_OUTPUT],
            }
        }
    )


def emit_context(context: str) -> None:
    """Inject context alongside a UserPromptSubmit.

    Phrased as factual statements by every caller — imperative text framed as an
    out-of-band system instruction trips Claude's prompt-injection defenses and
    gets surfaced to the user instead of used as context.
    """
    _emit(
        {
            "hookSpecificOutput": {
                "hookEventName": "UserPromptSubmit",
                "additionalContext": context[:MAX_OUTPUT],
            }
        }
    )


def bail_open() -> None:
    """Exit without an opinion. The normal permission flow proceeds."""
    sys.exit(0)


# --------------------------------------------------------------------------
# Path classification
# --------------------------------------------------------------------------


def _norm(p: str) -> str:
    try:
        return os.path.normpath(os.path.abspath(os.path.expanduser(p)))
    except Exception:
        return p or ""


def is_within(path: str, parent: str) -> bool:
    path_n, parent_n = _norm(path), _norm(parent)
    return path_n == parent_n or path_n.startswith(parent_n.rstrip("/") + os.sep)


def is_spec_path(path: str, cwd: str) -> bool:
    """HeadHunter's own working area — always writable, in every state. This is
    the door left open so the gate can never trap itself."""
    if not path:
        return False
    if is_within(path, str(spec_dir(cwd))):
        return True
    # Also honour a .headhunter directory anywhere up the tree.
    return f"{os.sep}.headhunter{os.sep}" in _norm(path) + os.sep


# Claude Code's plan-mode scratch area. A plan is the agent writing down what it
# intends to do, which is the opposite of building — so it stays writable in every
# state, for the same reason ``.headhunter/`` does: the gate must never block the
# deliberation it exists to force. Without this the gate also cannot be repaired
# from inside the armed state it creates, since ``hooks/`` is ordinary source.
_PLANS_DIR = re.compile(r"[/\\]\.claude[/\\]plans[/\\]")


def is_plan_path(path: str) -> bool:
    """Claude Code's own plan file. Always writable, like ``.headhunter/``."""
    if not path:
        return False
    return bool(_PLANS_DIR.search(_norm(path)))


SKILL_DIR_PATTERNS = (
    re.compile(r"[/\\]\.claude[/\\]skills[/\\]"),
    re.compile(r"[/\\]\.claude[/\\]agents[/\\]"),
    re.compile(r"[/\\]skills[/\\][^/\\]+[/\\]"),
    re.compile(r"[/\\]agents[/\\]"),
)


def is_skill_path(path: str) -> bool:
    """A skill or agent definition — writable only while ``equipping``, because
    authoring those is precisely the sanctioned work of that phase."""
    if not path:
        return False
    n = _norm(path)
    return any(p.search(n) for p in SKILL_DIR_PATTERNS)


# --------------------------------------------------------------------------
# Command classification
# --------------------------------------------------------------------------

# Split a shell command the way Claude Code's permission matcher does, so a
# payload hidden after && or | is classified on its own merits.
_SEPARATORS = re.compile(r"\|\||&&|\||;|&|\n")

# Quoted spans are *data*, not commands. Blanking them is what stops the gate
# firing on a command that merely mentions an install — writing docs about
# `claude plugin install`, or piping a JSON payload that contains the phrase.
_QUOTED = re.compile(r"'[^']*'|\"[^\"]*\"", re.S)

# A heredoc body is data handed to a command on stdin — the same category as a
# quoted span, and blanked for the same reason. Without this, writing prose or
# source by heredoc trips the gate on its own content: a markdown blockquote
# (`> text`), a literal `>>`, a Rust `->`, a JS `=>`, a generic `List<T>` or a
# regex named group all read as shell redirects, because _REDIRECT's lookbehind
# only excludes `[0-9<>]`. Matches <<TAG, <<'TAG', <<"TAG" and the <<-TAG
# indented form, up to the tag alone on its own line.
#
# Known limit: an *unterminated* heredoc does not match and its body is still
# scanned. Such a command is malformed shell anyway, and failing to blank
# produces a spurious denial rather than a missed one — the safe direction.
_HEREDOC = re.compile(
    r"<<-?[ \t]*(['\"]?)(?P<tag>[A-Za-z_][A-Za-z0-9_]*)\1"
    r"(?P<body>.*?)"
    r"^[ \t]*(?P=tag)[ \t]*$",
    re.S | re.M,
)

# ...except when the quoted span is handed to a shell, in which case it very
# much is a command. Pulled out and classified on its own before blanking.
_NESTED_EXEC = re.compile(
    r"\b(?:(?:ba|z|k|da)?sh|eval)\b\s*(?:-[a-zA-Z]+\s*)*(?P<q>['\"])(?P<body>.*?)(?P=q)",
    re.S,
)

# Prefixes that stand in front of the real command without being it.
_WRAPPER = re.compile(
    r"^\s*(?:(?:sudo|env|time|nohup|command|nice|stdbuf|setsid)\s+(?:-\S+\s+|\w+=\S+\s+)*)*"
)

# Acquiring a *discovered skill* by download is denied in every state, cleared
# included. Approval cannot authorize it either: HeadHunter studies published
# skills and writes build instructions for an equivalent, never installs one.
#
# Anchored at ^ because these are matched against a single subcommand with its
# wrappers stripped — a command name occupies the head position, and anything
# later in the string is an argument, not an invocation.
_SKILL_ACQUISITION_PATTERNS = (
    re.compile(r"^claude\s+plugin\s+(install|add)\b"),
    re.compile(r"^claude\s+plugin\s+marketplace\s+add\b"),
    re.compile(r"^git\s+clone\b.*\b(skill|plugin|agent)s?\b", re.I),
    re.compile(r"^(curl|wget|aria2c)\b.*\bSKILL\.md\b", re.I),
    re.compile(r"^(curl|wget|aria2c)\b.*\.claude[/\\](skills|agents|plugins)\b", re.I),
    re.compile(r"^cp\b.*\b(downloads?|tmp)\b.*\.claude[/\\](skills|agents)\b", re.I),
)

_INSTALL_PATTERNS = (
    re.compile(r"^git\s+clone\b"),
    re.compile(r"^(npm|pnpm|yarn|bun)\s+(i|install|add|create)\b"),
    re.compile(r"^npx\b"),
    re.compile(r"^(pip|pip3)\s+install\b"),
    re.compile(r"^uv\s+(pip\s+install|add|tool\s+install)\b"),
    re.compile(r"^poetry\s+add\b"),
    re.compile(r"^cargo\s+install\b"),
    re.compile(r"^go\s+(get|install)\b"),
    re.compile(r"^gem\s+install\b"),
    re.compile(r"^brew\s+(install|tap)\b"),
    re.compile(r"^(apt|apt-get|yum|dnf|apk|pacman)\s+(install|add)\b"),
    re.compile(r"^composer\s+require\b"),
    re.compile(r"^(curl|wget|aria2c)\b"),
    re.compile(r"^(iwr|Invoke-WebRequest|iex)\b"),
)

# Shell forms that create or overwrite files, i.e. a Write in disguise.
_REDIRECT = re.compile(r"(?<![0-9<>])>{1,2}\s*(?P<path>[^\s;&|]+)")
_TEE = re.compile(r"\btee\s+(?:-a\s+)?(?P<path>[^\s;&|]+)")


def _executable_fragments(command: str, depth: int = 0) -> list[str]:
    """Every span of text this command would actually execute.

    The command itself with quoted data blanked out, plus the bodies of any
    ``sh -c "…"`` / ``eval "…"`` — which are quoted, but are still commands.
    Recursion is bounded because each nested body is strictly shorter.

    Heredoc bodies are blanked first, ahead of both the nested-exec scan and the
    quote blanking, so a heredoc body can neither contribute a phantom redirect
    nor smuggle a fake ``sh -c "…"`` back into classification.
    """
    command = _HEREDOC.sub(" ", command or "")
    frags: list[str] = []
    if depth < 4:
        for m in _NESTED_EXEC.finditer(command or ""):
            body = m.group("body")
            if body.strip():
                frags.extend(_executable_fragments(body, depth + 1))
    frags.append(_QUOTED.sub(" ", command or ""))
    return frags


def subcommands(command: str) -> list[str]:
    """The command split into individually-classifiable invocations, each with
    its wrapper prefixes (``sudo``, ``env FOO=1``, …) stripped so that the real
    command name sits at the head of the string."""
    out: list[str] = []
    for frag in _executable_fragments(command):
        for part in _SEPARATORS.split(frag):
            head = _WRAPPER.sub("", part.strip()).strip()
            if head:
                out.append(head)
    return out


def install_hit(command: str) -> str | None:
    """Return the offending subcommand if any part is a download/install.

    Only consulted while a hunt is active — ordinary dependency installs for the
    project you are building are none of the gate's business once cleared.
    """
    for sub in subcommands(command):
        for pat in _INSTALL_PATTERNS:
            if pat.search(sub):
                return sub
    return None


def skill_acquisition_hit(command: str) -> str | None:
    """Return the offending subcommand if any part downloads a skill or plugin.

    Consulted in *every* state, including ``cleared`` and with no state file at
    all. This is the one prohibition approval cannot lift.
    """
    for sub in subcommands(command):
        for pat in _SKILL_ACQUISITION_PATTERNS:
            if pat.search(sub):
                return sub
    return None


def redirect_targets(command: str) -> list[str]:
    """Paths this command would create or overwrite via shell redirection."""
    out = []
    for sub in subcommands(command):
        for pat in (_REDIRECT, _TEE):
            for m in pat.finditer(sub):
                target = m.group("path").strip("\"'")
                if target and not target.startswith("/dev/"):
                    out.append(target)
    return out
