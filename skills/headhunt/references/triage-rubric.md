# Triage rubric

Phase 1. Deciding whether a request is hard enough to earn a hunt.

The gate arms on a keyword pattern, which is deliberately generous — it would rather
arm on something small than miss a real build. Your job in Phase 1 is the judgement the
regex cannot make. **Clearing the gate is the common outcome and the right one.**

## Clear immediately

Not builds. Clear and get to work:

```bash
hooks/set-state.py cleared --rationale "not a build task: <why>"
```

- Questions — "how would I build an app like this?" is a question, not a commission
- Fixes, debugging, investigating a failure
- Reading, explaining, reviewing, summarizing existing code
- Renames, formatting, lint, dependency bumps, config edits
- Single-file scripts and one-off utilities
- Adding a feature to something that already exists and already works
- Anything the user has already told you how to do
- Anything under roughly an hour of work

## Hunt

Genuinely hard, and the technique matters as much as the code:

- A website or web app built from nothing
- An agent, subagent, skill, or plugin
- A dashboard or data visualization of any real complexity
- A design system or component library
- An API or service with more than a couple of endpoints
- A game
- A CLI with real ergonomics
- Anything in a domain with established craft you cannot currently name

## The test that actually decides it

Ask: **would an expert do this noticeably better than I would right now, in a way I
could write down?**

- **No** → clear the gate. You already have what you need.
- **Yes, but I cannot say what they know** → that is exactly the gap. Hunt.
- **Yes, and I can already say what they know** → write it down, skip the hunt, clear
  the gate, and build with it in mind. The point was the knowledge, not the ceremony.

That last case is common and worth taking. The protocol exists to close a gap, not to
be performed.

## Borderline calls

**"Build me a landing page"** — usually clear. Simple, well-trodden, and Claude is
already decent at it. Hunt only if the user signals a high bar: brand-critical, a
conversion target, an unusual aesthetic.

**"Build me an agent"** — usually hunt. Agent design has real craft in it — tool
budgets, delegation boundaries, context discipline — and the failure modes are not
obvious from the outside.

**"Build me a dashboard"** — hunt if it involves data visualization. Chart design has
a large body of technique and the naive version is reliably poor.

**A rebuild of something that exists** — clear if you can read the original. The
existing code is better evidence than anything you would find online.

## Do not hunt twice

Once clearance is issued for a session, the gate stands down and stays down. Do not
re-run the protocol for follow-up work on the same build. If a genuinely new capability
gap opens mid-build, name it, hunt for that one thing, and carry on — do not restart
from Phase 1.
