#!/usr/bin/env python3
"""Advance the HeadHunter gate. This is how clearance is granted.

Claude drives the gate through this script rather than by editing a file, so the
transition never depends on a `Write` the gate itself might deny. Running it is
plain Bash and is never blocked.

    hooks/set-state.py status
    hooks/set-state.py equipping --spec .headhunter/specs/react-dashboards.md
    hooks/set-state.py cleared   --rationale "authored react-dashboards skill"
    hooks/set-state.py release

Session targeting: Claude Code does not export a session id to Bash, so by default
this acts on the most recently updated state file — which, right after the gate
arms, is the current session. Pass ``--session <id>`` to be explicit when several
sessions are running against the same machine.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import headhunter_lib as hh  # noqa: E402


def latest_session() -> str | None:
    try:
        files = sorted(
            hh.state_dir().glob("*.json"),
            key=lambda p: p.stat().st_mtime,
            reverse=True,
        )
        return files[0].stem if files else None
    except Exception:
        return None


def main() -> int:
    ap = argparse.ArgumentParser(description="Advance the HeadHunter gate.")
    ap.add_argument(
        "action",
        choices=["status", "armed", "equipping", "cleared", "release"],
        help="status prints state; release deletes it; the rest set it",
    )
    ap.add_argument("--session", help="session id (default: most recently updated)")
    ap.add_argument("--spec", help="path to the approved build instructions")
    ap.add_argument("--task", help="the task under gate")
    ap.add_argument("--rationale", help="why clearance is warranted")
    args = ap.parse_args()

    session = args.session or latest_session()
    if not session:
        if args.action == "status":
            print("HeadHunter gate: dormant (no state for any session).")
            return 0
        print(
            "No gate state found, so there is nothing to advance. The gate arms "
            "itself when a build-shaped request arrives.",
            file=sys.stderr,
        )
        return 1

    if args.action == "status":
        state = hh.read_state(session)
        if not state:
            print(f"HeadHunter gate: dormant (session {session}).")
            return 0
        print(json.dumps(state, indent=2))
        return 0

    if args.action == "release":
        hh.clear_state(session)
        print(f"HeadHunter gate released for session {session}.")
        return 0

    fields = {}
    if args.spec:
        fields["spec"] = args.spec
    if args.task:
        fields["task"] = args.task
    if args.rationale:
        fields["rationale"] = args.rationale

    if args.action == hh.CLEARED and not (args.rationale or args.spec):
        print(
            "Clearance needs a reason: pass --rationale describing what was "
            "authored, or --spec pointing at the approved build instructions.",
            file=sys.stderr,
        )
        return 1

    state = hh.write_state(session, args.action, **fields)
    print(f"HeadHunter gate → {state['status']} (session {session})")
    if args.action == hh.CLEARED:
        print("Build writes are unblocked. Skill downloads remain prohibited.")
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception as exc:  # pragma: no cover - operator feedback only
        print(f"set-state failed: {exc}", file=sys.stderr)
        sys.exit(1)
