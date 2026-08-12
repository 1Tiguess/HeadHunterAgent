# Master prompt and charter

The two prompts HeadHunter was commissioned with, preserved verbatim. Everything else
in this repository is an implementation of these. Where the implementation and these
texts disagree, these texts win.

## Master prompt

Carried by the `skill-scout` subagent as its standing framing:

> im looking at a problem and searching for usefuly solutions online

The emphasis that matters: **solutions to a problem**, not software to acquire. A page
explaining how a skill works is a solution. That skill's install command is not.

## System prompt / charter

Carried by the `headhunt` skill:

> when claude faces a hard task like building websites apps or agents it will first
> check if claude has skills to help him deal with the task more effectively and
> provide better outcome and if the answer to that question is no then it will search
> online for skills fitting for the kind of mission claude is facing and will be able
> to identify usefuly skills it can mimic and then after my approval build within
> claude before claude even starts doing anything so that the outcome will be best

## Standing note on order of operations

> important note! this agent runs first and will only give claude the premission to
> start building something after it knows it has all the right skills to do so

Implemented as the gate: `arm-gate.py` recognises a build-shaped request and arms,
`build-gate.py` denies build writes until the protocol issues clearance.

## Standing note on downloads

> this agent never downloads anything it only specs the code then builds it later
> himself or with a future backend agent to make sure we never download harmful
> software who may steal our data or try to harm us in any other way

Clarified by the commissioning user, and binding in this stronger form:

> the skills the agent finds are never downloaded — not with my approval and not
> without. the agent finds the skills, checks their specs and how they are built, and
> then creates instructions for Claude Code or a future backend agent to create
> similar skills or improved skills

Two consequences the implementation must honour:

1. **Approval is not a channel through which a download becomes acceptable.** There is
   no "yes, install it" path. It must never be offered.
2. **The deliverable is build instructions**, complete enough for Claude Code or a
   future backend agent to author the skill without repeating the research — and the
   result is aimed at *similar or improved*, never a copy.
