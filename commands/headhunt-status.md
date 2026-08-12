---
description: Show the HeadHunter gate state for this session
---

Report the current gate state.

Run the status command from the plugin root (`${CLAUDE_PLUGIN_ROOT}` when installed as
a plugin, the repo root when working in HeadHunter itself):

```bash
python3 hooks/set-state.py status
```

Then summarize for the user in a couple of lines:

- **dormant** — no build task detected; nothing is blocked
- **armed** — a build was detected and the protocol has not run; build writes denied,
  `.headhunter/` writable
- **equipping** — instructions approved, skills being authored; skill directories also
  writable
- **cleared** — permit issued; build writes unblocked

If a spec or rationale is recorded, mention it. If any specs exist under
`.headhunter/specs/`, list them with their status line.

Note that the prohibition on downloading skills applies in every state, including
`cleared` and `dormant`.
