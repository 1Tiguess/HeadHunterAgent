---
description: Stand the HeadHunter gate down for this session
argument-hint: "[reason]"
---

The user is standing the gate down. Reason, if given: $ARGUMENTS

Run:

```bash
python3 hooks/set-state.py cleared --rationale "released by user: ${ARGUMENTS:-no reason given}"
```

Then confirm in one line that build writes are unblocked for the rest of the session.

Two things to get right:

- Do not argue, and do not re-run the protocol. The user's call is the whole point of
  having an escape hatch — a gate you cannot open is a broken gate.
- Say that the prohibition on downloading skills, plugins, and agents is unaffected.
  Release lifts the build gate; it does not lift the charter. If the user then asks you
  to install a discovered skill, say plainly that HeadHunter's design excludes it and
  offer to study the skill and author an equivalent locally instead.
