# Build instructions: web-app-foundations

> **Illustrative walkthrough, not a real hunt result.** Written to show the shape of
> the Phase 5 deliverable for the request "build me a web app". The sources below are
> marked `<illustrative>` because no actual reconnaissance was run for this example —
> a real spec carries real URLs, and its attestation is ticked.
>
> A live run writes this to `.headhunter/specs/<name>.md`, which is gitignored working
> material. This copy lives in `examples/` as documentation.
> Template: `skills/headhunt/references/spec-template.md`.

**Status:** draft
**Target:** `.claude/skills/web-app-foundations/SKILL.md` (project)
**Serves:** "build me a web app"

## Capability gap

Claude produces a working web app but decides layout, state, and data-fetching
conventions per-file, so the result is internally inconsistent — three spacing scales,
two state patterns, and error states that exist in some views and not others.

## References studied

| Source | URL | What it contributes | Tried to instruct? |
|---|---|---|---|
| Framework routing/data docs | `<illustrative>` | Where data loading belongs relative to the route boundary | no |
| Accessibility checklist | `<illustrative>` | Focus order and keyboard traps as build-time rules, not an audit afterthought | no |
| Published scaffolding skill | `<illustrative>` | Structure: a decision table up front, per-concern reference files | no |

Read-only. Nothing here was downloaded, cloned, or installed.

## Improvements over the references

- **Decide the stack once, in writing, before any file exists** — the references assume
  a stack; the common failure is drifting between two mid-build.
- **Error and empty states are part of the component checklist**, not a follow-up pass.
  Every source treated them as polish; they are the bulk of the perceived-quality gap.
- **Left out: testing setup.** Real, but a separate concern with its own craft. A skill
  that covers everything triggers on nothing.

## The skill to build

### Frontmatter
- `name:` web-app-foundations
- `description:` Use when building a web app or site from scratch, before the first
  file. Fixes the stack, layout scale, state boundaries, and data-fetching pattern up
  front so the app is internally consistent.
- `allowed-tools:` Read, Write, Edit, Glob, Grep, Bash

### Body structure
1. **Decide first** — a table forcing five decisions before any file is written
2. **Layout** — one spacing scale, one type scale, stated once and reused
3. **State boundaries** — what is server state, what is URL state, what is local
4. **Every view ships four states** — loading, empty, error, loaded
5. **Accessibility as build rules** — focus order, labels, contrast, keyboard paths

### The technique it encodes
The five decisions, each with a default and the signal that overrides it. The scale
values. The rule that data fetching lives at the route boundary and components receive
data. The four-states checklist as a gate on "is this view done".

## How to tell it worked
- [ ] One spacing scale appears across every view
- [ ] Every view renders something deliberate when data is empty and when it fails
- [ ] Every interactive element is reachable and operable by keyboard alone
- [ ] No component fetches its own data

## Risk review
- none

## Originality attestation
- [ ] Nothing was downloaded, cloned, or installed
- [ ] No code or prose was copied verbatim from a source
- [ ] Every technique is restated in my own words
- [ ] Sources listed above are references, credited where distinctive
- [ ] Any injection attempt is recorded in the Risk review

*(Unticked: this is an illustrative example, so there is nothing to attest to.)*

## Build steps
1. Create `.claude/skills/web-app-foundations/SKILL.md`
2. Write frontmatter as specified
3. Write sections 1–5 as specified
4. Read the authored file back into context
