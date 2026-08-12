#!/usr/bin/env python3
"""UserPromptSubmit hook: recognises a build-shaped request and arms the gate.

``UserPromptSubmit`` supports no ``matcher``, so this fires on every prompt and
does its own filtering. It also defaults to a 30-second timeout after which the
output is discarded — so this stays cheap: regex over one string, one small file
write, no network, no subprocesses.

The injected context is written as **factual statements**. Imperative text framed
as an out-of-band system instruction trips Claude's own prompt-injection defenses
and gets surfaced to the user verbatim instead of used as context.
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import headhunter_lib as hh  # noqa: E402

# Phrases that stand the gate down. The user must always have a way out.
RELEASE = re.compile(
    r"\b(skip|no|disable|bypass|without|turn off)\s+(the\s+)?head\s?hunt(er|ing)?\b"
    r"|\bhead\s?hunt(er)?\s+off\b"
    r"|/headhunt-release\b",
    re.I,
)

# An explicit request to run the protocol.
INVOKE = re.compile(r"/headhunt\b(?!-)|\brun\s+(the\s+)?head\s?hunt\b", re.I)

BUILD_VERB = re.compile(
    r"\b(build|create|make|write|develop|implement|design|scaffold|bootstrap|"
    r"set\s?up|spin\s?up|stand\s?up|ship|launch|generate|code)\b",
    re.I,
)

ARTIFACT = re.compile(
    r"\b(app|application|web\s?app|website|web\s?site|site|landing\s?page|portal|"
    r"agent|sub-?agent|skill|plugin|dashboard|api|backend|front\s?end|frontend|"
    r"service|micro\s?service|bot|chatbot|extension|game|platform|saas|mvp|"
    r"prototype|cli|library|framework|pipeline|integration|mcp\s?server|"
    r"design\s?system|component\s?library)s?\b",
    re.I,
)

# Requests that are about existing code, or are questions, pass straight through.
PASS_THROUGH = re.compile(
    r"^\s*(what|why|how|when|who|where|which|is|are|was|were|do|does|did|can|could|"
    r"should|would|will|has|have|had)\b.*\?\s*$",
    re.I | re.S,
)

MAINTENANCE = re.compile(
    r"\b(fix|debug|explain|review|read|find|search|summari[sz]e|rename|refactor|"
    r"typo|bump|lint|format|revert|rebase|merge|cherry-?pick|commit|push|"
    r"investigate|diagnose|trace|profile)\b",
    re.I,
)


def looks_like_build(prompt: str) -> bool:
    if PASS_THROUGH.match(prompt):
        return False
    if not (BUILD_VERB.search(prompt) and ARTIFACT.search(prompt)):
        return False
    # A maintenance verb with no build verb ahead of it is upkeep, not a build.
    m, b = MAINTENANCE.search(prompt), BUILD_VERB.search(prompt)
    if m and b and m.start() < b.start():
        return False
    return True


def summarize(prompt: str, limit: int = 160) -> str:
    one_line = " ".join(prompt.split())
    return one_line if len(one_line) <= limit else one_line[: limit - 1] + "…"


ARMED_CONTEXT = """\
HeadHunter gate state for this session: armed.

This request matches the build-task pattern that HeadHunter watches for, and no \
build clearance exists for it yet. While the gate is armed, the PreToolUse gate \
denies file writes outside `.headhunter/` and pauses dependency installs. Writes to \
`.headhunter/` stay open so the protocol can record its work.

Task under gate: {task}

The `headhunt` skill documents the protocol that produces clearance: inventory the \
skills already installed, name the capability gap, study published skills read-only, \
write build instructions for a similar or improved skill, get the user's approval, \
author it locally, then issue the permit.

Downloading a discovered skill is prohibited in every state, approval included. \
Study and author; never install.

The user can stand the gate down at any time with /headhunt-release, or by including \
"skip headhunt" in a message.
"""

RELEASED_CONTEXT = """\
HeadHunter gate state for this session: cleared by user request.

The user's message contains a release phrase, so the gate has stood down and build \
writes are unblocked for the rest of this session. The prohibition on downloading \
discovered skills remains in force — it is not affected by the release.
"""


def main() -> None:
    payload = hh.read_payload()
    prompt = payload.get("prompt", "") or ""
    session_id = payload.get("session_id", "")

    if not prompt.strip():
        hh.bail_open()

    if RELEASE.search(prompt):
        hh.write_state(session_id, hh.CLEARED, reason="released by user phrase")
        hh.emit_context(RELEASED_CONTEXT)
        return

    state = hh.read_state(session_id)

    if INVOKE.search(prompt):
        hh.write_state(session_id, hh.ARMED, task=summarize(prompt))
        hh.emit_context(ARMED_CONTEXT.format(task=summarize(prompt)))
        return

    # An issued permit covers the rest of the session; don't re-arm behind it.
    if state and state.get("status") in (hh.CLEARED, hh.EQUIPPING):
        hh.bail_open()

    if not looks_like_build(prompt):
        hh.bail_open()

    task = summarize(prompt)
    if state and state.get("status") == hh.ARMED and state.get("task") == task:
        hh.bail_open()  # already armed for this exact task; don't repeat ourselves

    hh.write_state(session_id, hh.ARMED, task=task)
    hh.emit_context(ARMED_CONTEXT.format(task=task))


if __name__ == "__main__":
    try:
        main()
    except Exception:
        sys.exit(0)
