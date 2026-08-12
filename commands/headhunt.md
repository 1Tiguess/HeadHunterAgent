---
description: Run the HeadHunter pre-flight protocol for the current task
argument-hint: "[what you are about to build]"
---

Run the HeadHunter protocol before building: $ARGUMENTS

Follow the `headhunt` skill. Work the phases in order, stopping early the moment the
capability gap closes:

1. **Triage** — is this actually hard? Consult the triage rubric. If not, clear the
   gate and say why.
2. **Inventory** — `ListSkills`, `SearchSkills`, `ListPlugins`, and read the skill
   directories. If something already covers it, name it and stop.
3. **Gap** — state the missing capability as an observable behavior, in one sentence.
4. **Hunt** — delegate to `skill-scout`. Read-only, tiered, sources reported as
   reported speech.
5. **Instructions** — write build instructions to `.headhunter/specs/<name>.md` using
   the template, including the required "Improvements over the references" section.
6. **Approval** — `AskUserQuestion`: build it? and project or global?
7. **Author and clear** — write the skill, read it back into context, issue the permit.

Nothing is downloaded at any point, with approval or without it.
