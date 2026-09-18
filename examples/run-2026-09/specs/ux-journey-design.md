# Build instructions: ux-journey-design

**Status:** draft
**Target:** `~/.claude/skills/ux-journey-design/` (global — usable in every project)
**Serves:** the "best UX" half of the request — the path between screens, not the screens
**Hunt notes:** `.headhunter/hunts/ux-journey-notes.md`

## Capability gap

Claude designs screens, not journeys. The individual pages are fine; the path through them is not.
Four symptoms, all path-level: a step asks for information the user does not have yet; abandoning
mid-flow loses everything; errors say what is wrong but not how to escape; onboarding demands
everything up front.

**Boundary with the existing shelf.** `app-interface-design` covers layout, navigation architecture
and per-screen density. `design-token-systems` covers per-field accessibility wiring —
`aria-describedby`, error id association, focus styling. This skill covers **what happens between
screens**: which questions exist at all, in what order, what survives an interruption, and what the
failure path looks like. The three must not overlap, and the seam is stated in each.

## References studied

| Source | What it contributes | Fetched or search-extracted? |
|---|---|---|
| GOV.UK Design System — 9 patterns + 2 components | The spine: question pages, validation, error messages and summary, check answers, task lists, accounts, confirmation, start, navigation, interruption | **Fetched**, `alphagov/govuk-design-system` |
| U.S. Web Design System — complex form, create a profile | Trauma-informed framing; save-and-resume as a requirement; the printable record | **Fetched**, `uswds/uswds-site` |
| W3C WAI forms tutorial | Page-level error identification; the polite/assertive live-region rule; forgiving input formats | **Fetched**, `w3c/wai-tutorials` |
| Archived GOV.UK service design manual | Card sorting method and its sample sizes | **Fetched** (2016, archived) |
| Caroline Jarrett — the question protocol | The upstream method: justify every field before designing it | Search-extracted |
| Validation-timing literature | "Reward early, punish late"; inline validation reduces correction time | Search-extracted; `baymard.com` was `EGRESS_BLOCKED` |
| NN/g sample-size articles | Five users ≈ 85%, and the caveats NN/g publishes itself | Search-extracted |

## Improvements over the references

**The organising find: several of GDS's most-repeated positions are convention, and GDS says so
itself.** The validation page states its justification is long use across many services and then
*explicitly asks for the research it does not have*. That is the seam. This skill does not
contradict GDS; it is **honest about which rules are evidenced and which are house style**, and
gives a decision rule where the sources give a blanket one.

1. **Resolve the validation contradiction with a rule keyed to field type.** GDS says never on blur.
   USWDS says use inline validation. The practitioner literature says reward early, punish late.
   Three authoritative sources, three answers, no cross-references. The new rule: a
   **format-constrained field the browser can judge** (postcode shape, card length) behaves
   differently from **free text whose validity is unknowable until you stop typing**, which behaves
   differently from **a field only the server can judge** (is this username taken). **GDS's own
   blessed exception — the character counter — is exactly the "irrecoverable wasted effort" case,
   and they did not generalise it.** This skill does.
2. **Separate the three returns that sources conflate.** Mid-flow (save and resume, and *say it
   exists up front*), between sessions (the task list on every re-entry, statuses carrying the
   memory), and after the fact (bookmarked confirmation pages behaving weeks later, the complete
   printable record). Three different mechanisms; a journey needs all three.
3. **Own the short flow.** Task lists are explicitly scoped to long multi-session transactions.
   **Nothing addresses the person who abandons step 3 of 5 and returns in ten minutes** — no
   autosave guidance, no draft state, no "we kept your answers" affordance. That is the most common
   real interruption and it is unowned.
4. **Mechanise deferred account creation.** GDS asserts "let people get as far as possible first"
   and offers reference-number lookup, but never describes **the conversion moment** — guest
   completes, then optionally creates an account; what carries over; when to ask. USWDS's profile
   pattern has no progressive-profiling guidance at all.
5. **Cover non-validation failures.** Every error source is about "the user typed something wrong".
   Nothing covers the server dying at step 4, an expired session eating the form, a payment timing
   out, or a third-party lookup being down mid-flow. GDS ships "problem with the service" pages but
   treats them as standalone destinations, **not as recoveries that preserve a journey in
   progress**. The symptom "errors say what is wrong but not how to escape" bites hardest here.
6. **Add tree testing.** Card sorting answers "how would you group this", which is not the question.
   **Tree testing — can a person find the thing in the structure you already built — is the actual
   test for whether labels work, and appears in none of these sources.**
7. **Give an evidence floor the sources don't.** Five users is defensible and cheap; NN/g's own
   caveats cap it; GDS's 15–30 for card sorting assumes recruitment a small team lacks. **Nobody
   describes the lightest honest check** — reading the flow aloud to one person who has never seen
   it, or auditing every question against the protocol table, which costs nothing and needs no
   participants.
8. **Note that all of it assumes a government transaction** — linear, logged-out, one-off,
   mandatory. Say where the guidance stops applying: returning users in a consumer product,
   exploratory rather than transactional flows, multi-device handoff.

## The skill to build

### Frontmatter
- `name:` ux-journey-design
- `description:` third person, under 1024 chars. Trigger on journey language and on symptoms —
  designing a signup, checkout, onboarding, application form, multi-step flow or wizard; and:
  "users drop off at step 3", "they lose their answers", "the form is too long", "people don't know
  what to do next", "the error doesn't help", "too many fields", "should this be one page or
  several", "do we need an account for this".
- `allowed-tools:` Read, Write, Edit, Glob, Grep

### Body structure
1. **Before designing anything: the question protocol** — the upstream gate
2. **One thing per page, and when it doesn't apply**
3. **Order and dependency** — never ask twice, allow "I don't know", simple before complex
4. **Validation timing** — the decision rule keyed to field type
5. **The failure choreography** — the fixed procedure, and the wording system
6. **Non-validation failures** — the server died, the session expired, the lookup is down
7. **The three returns** — mid-flow, between sessions, after the fact
8. **Review before commit** — check-your-answers and its return loop
9. **Accounts** — a cost, not a feature; the reference-number alternative; the conversion moment
10. **Confirmation and the record** — receipts people bookmark
11. **How much evidence is enough** — the floor, and what each method actually answers

### The technique it encodes

**The question protocol as the opening move.** A table, one row per question, with columns for: who
inside the organisation actually uses this answer, what decision they make with it, required or
optional, and — the column that does the work — **what happens if the user types any old thing just
to get past it.** That converts "we need this" into a testable claim, because **a field people
routinely garbage-fill is worse than no field.** The symptom *"a task asks for information the user
does not have yet"* is a question-protocol failure surfacing late, and the garbage-fill column is
its diagnostic.

**The validation decision rule** (the skill's distinctive contribution), stated as three cases:
*format-constrained and browser-judgeable* → validate on submit, but a live counter is warranted
where effort would be irrecoverable; *free text* → submit only, because you cannot judge it until
entry ends and early judgement punishes slow typists; *server-judgeable* → asynchronous check with
`aria-live="polite"`, never `assertive`, because polite waits for a pause and assertive cuts in.
Then the asymmetry that unifies them: **a field currently in error re-validates immediately on edit
so the error clears the instant it is fixed; a field currently valid is not re-judged until the
user leaves it. Fast with good news, slow with bad news.**

**The failure choreography as a checkable procedure.** Preserve everything typed. Error summary at
the top of `main`, below back link and breadcrumbs, **above the `<h1>`**, headed "There is a
problem". **Keyboard focus moves to it.** `Error: ` prefixed onto the `<title>`. Summary text and
inline text **word-for-word identical**. One link per erroneous answer in question order, resolving
to a *specific* input: single control → the control; composite answer (a date, an address) → the
first input containing an error; **radios or checkboxes → the first option, never the fieldset.**

**The wording system.** Every message does two jobs: what happened, and how to get out. Banned:
jargon, blame and legal register ("forbidden", "illegal", "you forgot"), **"please"** (implies the
fix is optional), **"sorry"** (doesn't help), **"valid"/"invalid"** (carries no information), jokes.
**The grammatical rule: an empty field gets an *instruction*, a constraint violation gets a
*description*.** "Enter your first name" vs "First name must be 35 characters or less." Empty, too
long, wrong format and illegal characters are **four messages, not one**. Test by reading it aloud.

**The three returns.** Mid-flow: save and resume exists, **and you tell the user up front that it
does** — because the anticipated situations are a phone, a public place, or a question too painful
to answer now, and *knowing you can stop changes whether you start*. Between sessions: the task list
on every returning session, with the designed status vocabulary — **Completed carries no tag** so
attention goes to what is left; **Cannot start yet is grey and unlinked**; **There is a problem is
red and reserved exclusively for errors** so the colour keeps its meaning; and the user may
**declare their own completion** ("Have you completed this section?" / "No, I'll come back later")
rather than having it inferred from field counts. After the fact: **confirmation pages get
bookmarked and treated as receipts**, so that URL must still behave weeks later, and the printable
record must contain **every question and the answer given** — *do not cherry-pick*, because the
record's purpose is to be evidence of what you told them.

**The short-flow gap, filled.** For a flow too short to warrant a task list: autosave per step, a
visible "we kept your answers" affordance on return, a draft state with an explicit lifetime, and a
resume entry point that is not the start page.

**Check-your-answers' return loop.** A "Change" link per row with visually-hidden text naming what
it changes; it returns to the original question page **pre-populated and looking the same**, and
continue sends the user **straight back to the check page**, not through the intervening steps. New
follow-up questions are asked first. Skipped optional answers render **"Not provided"**, not blank.
State explicitly that nothing is submitted until they confirm.

**Accounts.** A cost with two named harms: a drop-out barrier and an ongoing maintenance burden.
Justified only when users must return regularly to access or update their data. Defer registration
as long as possible; the substitute is a **reference number emailed or texted**, not displayed once.
No CAPTCHAs or cognitive puzzles. Never a national ID number as an identity check. Then the
conversion moment the sources omit: complete as guest → offer the account at the confirmation step,
where the value is concrete → carry the submitted data forward → never re-ask anything.

**Eligibility does not go on the start page.** Complex rules move inside as questions. The start
page orients; it does not qualify. And list what people need to have to hand — **but not things
they know from memory**.

**Evidence, with the floor stated.** Five users ≈ 85% of usability problems, qualitative and
formative only; quantitative needs 30+; complex sites have shown as low as 35%. Card sorting: open
for labels, closed to validate, ~50 cards, 15–30 participants. **Tree testing for whether the labels
work.** And the zero-participant floor: audit every question against the protocol table, and read
the flow aloud to one person who has not seen it.

### Reference files
One level deep; table of contents where over 100 lines.

- `references/question-protocol.md` — the table, worked on a real form, with the garbage-fill column
  as the diagnostic and examples of fields it kills
- `references/failure-paths.md` — the validation choreography as a checklist, the wording system with
  a before/after bank, the summary link-target rules, and the non-validation failures the sources
  omit
- `references/interruption.md` — the three returns, the task-list status vocabulary, the short-flow
  autosave pattern, the printable record's contents
- `references/evidence.md` — what each research method actually answers, sample sizes with their
  caveats, and the honest floor; plus the **convention-vs-evidence table** marking which GDS
  positions are which

## How to tell it worked

- [ ] Every field in a generated form can name the decision it drives
- [ ] Validation timing is chosen per field type, with a stated reason, not applied blanket
- [ ] A field in error re-validates on edit; a valid field is not re-judged until blur
- [ ] Errors preserve input, focus the summary, prefix the title, and match summary to inline text
- [ ] Empty-field and constraint-violation messages are grammatically different
- [ ] Summary links resolve to a specific input, with radio groups pointing at the first option
- [ ] Abandoning mid-flow and returning does not lose answers, at any flow length
- [ ] Save-and-resume, where it exists, is announced before the user starts
- [ ] A server or third-party failure mid-flow has a designed recovery, not just an error page
- [ ] Account creation is deferred, or justified by a return-to-your-data need
- [ ] The confirmation page still works when revisited from a bookmark
- [ ] Claims about what users want are traceable to a method, and the method's limits are stated

## Risk review

**None adversarial.** No source attempted to induce a fetch, execution, installation, credential
read, exfiltration or persona change.

Provenance items:

1. **`baymard.com` was `EGRESS_BLOCKED`**, so the inline-validation study reaches this skill
   second-hand. The skill must present "inline validation reduces correction time" as reported
   rather than cited, and **must not quote a number.**
2. **The IA material is nine years old** and from an archived repository; the current GOV.UK service
   manual has no markdown repo and is not reachable via GitHub at all. Tree testing — the method the
   skill actually recommends — came from no primary source and is presented as reasoning.
3. **The convention-vs-evidence table is the integrity mechanism of this skill.** Validate-on-submit,
   one-thing-per-page, "(optional)" not asterisks, summary placement and focus, summary link targets,
   the task-list status vocabulary and card sorting's 15–30 are all **asserted as convention with no
   research offered** — and one of them, validate-on-submit, is the most-cited GDS position of all.
   The skill must mark them, because presenting house style as evidence is the exact failure it
   exists to prevent.
4. **All of it assumes a government transaction.** The skill must say where the guidance stops.

## Originality attestation

- [x] Nothing was downloaded, cloned, or installed
- [x] No code or prose was copied verbatim from a source
- [x] Every technique is restated in my own words
- [x] Sources are listed above as references, credited where their idea is distinctive
- [x] Any injection attempt is recorded in the Risk review

## Build steps

1. Create `~/.claude/skills/ux-journey-design/SKILL.md`, under 500 lines, opening with the boundary
   statement against `app-interface-design` and `design-token-systems`.
2. Write the four reference files with tables of contents.
3. Build the convention-vs-evidence table in `references/evidence.md` before writing the body, so
   the body's confidence language is constrained by it.
4. Read the authored `SKILL.md` back to confirm it is on disk and the frontmatter parses.
5. Mirror into `authored-skills/ux-journey-design/`.
