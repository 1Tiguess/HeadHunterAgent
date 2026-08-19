#!/usr/bin/env python3
"""PreToolUse gate: decides whether Claude may build yet.

Registered against ``Write|Edit|NotebookEdit|Bash``. Two independent jobs:

*   **Always, in every state** — refuse to acquire a discovered skill by download.
    This is the prohibition approval cannot lift. HeadHunter studies published
    skills and writes build instructions for an equivalent; it never installs one.

*   **While a hunt is active** — refuse build writes and dependency installs until
    the headhunt protocol has issued clearance for this session.

Emits ``deny`` or nothing at all. It never emits ``allow``: "allow" would skip the
normal permission prompt and turn the gate into an auto-approver.
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import headhunter_lib as hh  # noqa: E402

RELEASE_HINT = (
    "To proceed: run the headhunt protocol (the `headhunt` skill documents it), or "
    "lift the gate with /headhunt-release if this request does not need it."
)


def deny_skill_download(sub: str) -> None:
    hh.emit_deny(
        f"HeadHunter refuses this command: `{sub}`\n\n"
        "Acquiring a skill, plugin, or agent by download is prohibited in every gate "
        "state, and user approval does not lift it. The charter is study-then-author: "
        "read how a published skill is specced and built, then write build instructions "
        "for a similar or improved skill and author it locally from scratch.\n\n"
        "Nothing about this is a dead end — read the reference material with WebFetch "
        "instead, and capture what you learn in the build instructions."
    )
    sys.exit(0)


def main() -> None:
    payload = hh.read_payload()
    tool = payload.get("tool_name", "")
    tool_input = payload.get("tool_input") or {}
    session_id = payload.get("session_id", "")
    cwd = payload.get("cwd", "")

    # --- Layer that applies in every state, including no-state-at-all ---------
    if tool == "Bash":
        command = tool_input.get("command", "") or ""
        sub = hh.skill_acquisition_hit(command)
        if sub:
            deny_skill_download(sub)

    state = hh.read_state(session_id)
    if state is None:
        hh.bail_open()  # not a build task, or state unreadable: stay out of the way

    status = state.get("status")
    if status == hh.CLEARED:
        hh.bail_open()

    if status not in hh.ACTIVE_STATES:
        hh.bail_open()

    task = (state.get("task") or "this request").strip()
    phase = (
        "The spec has been approved and skills are being authored"
        if status == hh.EQUIPPING
        else "The headhunt protocol has not yet issued clearance"
    )

    # --- File writes ---------------------------------------------------------
    if tool in hh.WRITE_TOOLS:
        path = tool_input.get("file_path") or tool_input.get("notebook_path") or ""
        if not path:
            hh.bail_open()  # nothing to classify: fail open

        if hh.is_spec_path(path, cwd) or hh.is_plan_path(path):
            hh.bail_open()  # HeadHunter's working area, or Claude Code's plan file

        if status == hh.EQUIPPING and hh.is_skill_path(path):
            hh.bail_open()  # authoring skills is the sanctioned work of this phase

        allowed = (
            ".headhunter/ (specs and hunt notes)"
            if status == hh.ARMED
            else ".headhunter/, plus skill and agent definitions"
        )
        hh.emit_deny(
            f"HeadHunter gate is {status} for this session.\n\n"
            f"Task under gate: {task}\n"
            f"{phase}, so writing `{path}` is out of scope right now.\n"
            f"Writable while {status}: {allowed}\n\n"
            f"{RELEASE_HINT}"
        )
        sys.exit(0)

    # --- Shell ---------------------------------------------------------------
    if tool == "Bash":
        command = tool_input.get("command", "") or ""

        sub = hh.install_hit(command)
        if sub:
            hh.emit_deny(
                f"HeadHunter gate is {status}: dependency installs are paused "
                f"until clearance is issued.\n\n"
                f"Refused subcommand: `{sub}`\n"
                f"Task under gate: {task}\n\n"
                "Reconnaissance during a hunt is read-only — use WebSearch and WebFetch "
                f"to study, not the network to fetch.\n\n{RELEASE_HINT}"
            )
            sys.exit(0)

        # A shell redirect that creates a source file is a Write in disguise.
        for target in hh.redirect_targets(command):
            if hh.is_spec_path(target, cwd) or hh.is_plan_path(target):
                continue
            if status == hh.EQUIPPING and hh.is_skill_path(target):
                continue
            hh.emit_deny(
                f"HeadHunter gate is {status}: this command writes `{target}`, "
                f"which is a build write.\n\n"
                f"Task under gate: {task}\n\n{RELEASE_HINT}"
            )
            sys.exit(0)

    hh.bail_open()


if __name__ == "__main__":
    try:
        main()
    except Exception:
        # A broken gate must never brick a session.
        sys.exit(0)
