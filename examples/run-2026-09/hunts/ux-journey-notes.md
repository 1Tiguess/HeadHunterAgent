# Hunt notes — UX journeys, forms and recovery

**Gap.** Claude designs screens, not journeys. Individual pages are fine;
the path through them is not. Symptoms: a step asks for information the user
does not have yet; abandoning mid-flow loses everything; errors say what is
wrong but not how to escape; onboarding demands everything up front.

**Source reach: complete.** All GitHub/raw routes worked. Twenty-two sources.
GOV.UK proper was not attempted (known blocked); `baymard.com` was
`EGRESS_BLOCKED`, so its inline-validation study is second-hand and flagged.

**The find that shapes the whole skill: several of GDS's most-repeated positions
are convention, and GDS says so itself.** That is the seam an authored skill
exploits — not by contradicting GDS, but by being honest about which rules are
evidenced and which are house style, and giving a decision rule where the
sources give a blanket one.

---

## GOV.UK Design System — the spine

### Question pages
Fixed skeleton: back link, heading, single question, continue button. **The
heading *is* the question**, not the section name; section context goes in a
caption above. Optional fields get "(optional)" appended to the label or legend;
**asterisks are banned outright**, no exception offered.

Two journey-level rules that matter more than the layout: **never ask the same
thing twice** (pre-populate or carry forward), and **allow "I don't know" as a
real answer** rather than forcing a guess.

Progress indicators are **opt-out by default** — added only after research shows
users need one.

The page names the **question protocol** as the upstream gate on whether a field
exists at all.

**Combining questions is permitted** where research supports it, and the stated
case is internal/caseworker tools where the operator switches tasks fast and
wants density. That is the "when one-thing-per-page does not apply" answer, and
it is narrower than most people assume.

### Validation — the strongest statement, and the most honest about its evidence
Do not validate when the user leaves a field. **Wait for submit.** As-you-type is
allowed only where research justifies it, and the one blessed example is a
**character counter**, on the rationale that the user is about to waste effort
they cannot recover. On-blur gets no separate treatment — lumped in with
as-you-type. The stated reason is that early validation **hurts slow typists**.

On failure: error summary at the top, **keyboard focus moved to it**, inline
messages beside each bad field, and **`Error: ` prefixed onto the `<title>`** so
a screen reader announces the failure first. **Everything the user typed comes
back** — so they can see what went wrong, edit rather than retype, and not lose
work.

Implementation posture: server-side validation always, client-side never
trusted; **`novalidate` on the form and no `required` attribute**, so the
browser's native bubbles don't pre-empt the designed error experience.

**The disclaimer is the find.** The justification offered is that the approach
has been used on a number of services over a long period — and the page
**explicitly asks for more research**, specifically on whether client-side
validation is needed at all and on how screen readers behave when `required` is
absent. GDS is flagging its own flagship guidance as convention.

### Error messages — a wording system, not a style rule
Every message does two jobs: **what happened, and how to get out.**

Banned vocabulary, specific and worth keeping: no jargon ("form post error",
"unspecified error"), no blame or legal register ("forbidden", "illegal",
"prohibited", "you forgot"), **no "please"** (implies the fix is optional),
**no "sorry"** (doesn't help), **no "valid"/"invalid"** (carries no
information), no jokes.

**The grammatical rule is the sharp part: an empty field gets an *instruction*,
a constraint violation gets a *description*.** "Enter your first name" versus
"First name must be 35 characters or less." Different failure modes on the same
field need different messages — empty, too long, wrong format, illegal
characters are **four messages, not one**.

Summary text and inline text must be **word-for-word identical**; the reason
given is cognitive cost. The authoring test: read it aloud and ask whether you'd
say it.

### Error summary
Top of `main`, below back link and breadcrumbs, **above the `<h1>`**. Heading
"There is a problem". One link per erroneous answer, in question order.

Link-target rules, the non-obvious content: single control → the control; a
**composite answer** spread over several inputs (a date, an address) → the
**first input containing an error**, falling back to the first input; **radios or
checkboxes → the first option in the group, never the fieldset**. Focus moves to
the summary on render.

*Boundary:* per-field wiring (`aria-describedby`, error id association, focus
styling) belongs to `design-token-systems`. What belongs here is the page-level
choreography — summary exists, focus lands there, links resolve correctly, title
announces.

### Check your answers
A pre-commit review immediately before submission for small/medium transactions;
for long multi-section ones, a check page at the end of **each section**, and the
stated trigger for that split is **when different people complete different
sections**.

**The return loop is the valuable mechanic.** A "Change" link per row carrying
visually-hidden text naming what it changes. Clicking returns the user to the
original question page, **pre-populated and looking the same as before** — and
continue then sends them **straight back to the check page**, not back through
the intervening steps. If the change opens new follow-up questions, those are
asked first, then back to the check page. Skipped optional answers render as
**"Not provided"**, not blank.

Copy: state explicitly that **nothing is submitted until they confirm**;
re-phrase questions into statements for scanning; hide inapplicable sections; the
submit button names the actual consequence.

### Complete multiple tasks (the renamed task-list pattern)
The interruption-and-return pattern, scoped to long transactions spanning
**multiple sessions**. The page opens by telling you to **simplify first** — if
you can cut tasks or steps, you may not need this at all.

The status vocabulary is designed, not decorative: **Completed** (plain black,
*no tag* — deliberately de-emphasised so attention goes to what's left),
**Not yet started**, **In progress**, **Cannot start yet** (grey and **unlinked**,
for genuine prerequisites), and **There is a problem** (red, **reserved
exclusively for errors** so the colour keeps its meaning). Statuses are
adjectives in sentence case, not verbs.

**The task list is shown at the start of the transaction and at the start of
every returning session** — that is the resume mechanism.

Two details beyond the obvious: task names **start with verbs** and summarise a
group of activities rather than naming a screen; and where a section is long or
largely optional, end it by asking **"Have you completed this section?"** with a
"No, I'll come back later" option — **letting the user declare their own
completion state** rather than inferring it from field counts. Tasks completable
in any order where possible.

### Create accounts
**Accounts are a cost, not a feature.** Two named harms: a drop-out barrier, and
an ongoing build/maintenance burden. Justified when users need to return
regularly to access or update their data — not otherwise. **Let people use as
much of the service as possible before requiring registration.**

**The alternative to an account is a reference number** paired with a name or
email for status lookups — and because reference numbers are hard to remember,
you **email or SMS them** rather than displaying them once.

Also: **no CAPTCHAs or cognitive puzzles** (WCAG 2.2 cited for the accessible
alternative), "Create an account" as fixed terminology, account creation visually
distinct from sign-in, no duplicate data entry, nothing distracting on the
registration screen, and **never a national ID number as an identity check**.

### Confirmation pages
Required: reference number, **what happens next and when**, contact details,
onward links, a feedback link, and a way to save a record (PDF).

**The sharpest observation: users bookmark confirmation pages and treat them as
receipts.** So the page must behave when revisited — either serve the real thing
again, or serve links for tracking an application, starting a new one, and who to
contact if something is wrong.

**GDS flags its own research gap here**: how to confirm a transaction that is one
step inside a larger user task, where "what's next" matters more than "you're
done", is unresolved.

### Start using a service
Just enough to judge "is this the right thing for me", with an action-worded
button. List what you need to have to hand — but **explicitly not things people
know from memory**, a nice anti-bloat rule. Carries sign-in, resume, update and
non-digital routes.

**Eligibility does not go on the start page.** Complex eligibility rules move
*inside* the service as questions. That is the direct answer to "onboarding
demands everything up front": **the start page's job is orientation, not
qualification.**

### Navigate a service
If the service has a clear end-to-end journey, **do not add navigation links** —
use a task list, because what the user needs is not "where can I go" but which
tasks exist, in what order, and which are done. Navigation is for services used
repeatedly, containing several tasks, with no fixed sequence. **Don't inherit the
site-wide topic menu into a transaction.**

### Interruption pages
A deliberate full-stop: panel with heading, description, and a button you must
press to continue. Legitimate triggers: about to do something unusual that is
probably a mistake; something irreversible; something that contradicts
information already held. Gate is strict — evidence the pause is needed **and**
no other way to convey it. **The decay warning is the useful bit: they get less
effective the more often users see them.**

---

## U.S. Web Design System — a different frame

### Complex form / progress easily — trauma-informed design
The premise is that the person filling this in may be in crisis, and the design
consequence is explicit: **people under stress have poor recall, make more
errors, and do not notice the errors they make.** That last clause is a direct
argument for review steps and for error prominence, grounded in the SAMHSA
trauma-informed framework rather than UX convention.

Order questions simple → complex; one micro-topic at a time; allow user-chosen
order where possible, **but warn when a change invalidates earlier answers**.

**Save and resume is a requirement, not a nicety — and you tell the user up front
that it exists**, because the anticipated situations are a phone, a public place,
or a question too painful to answer right now. **Knowing you can stop changes
whether you start.**

Plus human escape hatches (phone, chat) reachable from inside the flow.

### Complex form / keep a record
A print-optimised summary containing site name, URL, submission date,
confirmation, **every question and the answer given**, and any case/reference ID.
Sensitive values partially masked (last four digits). PDF for mobile.

**The rule with teeth: do not cherry-pick which questions appear in the record.**
Include everything asked, because the record's purpose is to be **evidence of
what you told them**.

Print craft: points not pixels, serif at 12pt, links underlined with URLs spelled
out, table headers repeated per page, widow/orphan control, half-inch margins,
test across printers.

### Create a profile — a counter-example
Nine profile fields with per-field entry guidance, framed around identity and
eligibility. **It contains no guidance on progressive profiling, phased
onboarding, or deferring collection.** It optimises *accurate* entry, not
*minimal* entry. Useful here as a counter-example.

---

## W3C WAI forms tutorial (repo archived July 2024; markdown still readable)

Error identification at page level: overall feedback in the heading **and** in
the `<title>`; errors listed at the top with `role="alert"`; each entry linked to
its control; **focus moves to the first control in error**. Inline feedback sits
next to the control and pairs a visual cue with text — **never colour alone**.

**The live-region rule is the accessibility-layer restatement of "don't punish
people mid-entry":** `aria-live="polite"` for anything non-urgent (their example
is an async username-availability check), `assertive` only when interrupting is
justified — and it names **on-focus validation as an assertive case**. Polite
waits for a pause; assertive cuts in.

Success confirmation gets equal billing with errors.

Validation page: mark required fields **in the visible label** as well as
programmatically. HTML5 input types do double duty — validation plus the right
mobile keyboard and native pickers. Client-side never replaces server-side. And
the principle that prevents a whole class of errors: **be forgiving of input
formats** rather than rejecting and asking again.

---

## The underlying craft

### The question protocol (Caroline Jarrett) — search-extracted
The method GDS points at but does not reproduce. A table, one row per question,
with columns for: **who inside the organisation actually uses this answer**,
**what decision they make with it**, whether it is required or optional, and —
the column that does the work — **what happens if the user types any old thing
just to get past it.**

That last column converts "we need this" into a testable claim, because **a field
people routinely garbage-fill is worse than no field.** The discipline is to
track down the specific humans who use the data in their actual work rather than
accepting a department's assertion. Once you know which decision the data drives,
you can price the decision against the cost of collecting it.

### Validation timing evidence — search-extracted, and it runs against GDS
Inline validation is reported to **cut correction time**, because the input and
its context are still in working memory when the error surfaces, and progressive
confirmation builds confidence. But the failure mode is specific and matches
GDS's worry: **validating on every keystroke punishes people from the first
character**, because you generally cannot judge a field until entry is finished.

The reconciliation on offer is Konjević's **"reward early, punish late"**: a field
**currently in error** is re-validated immediately on edit, so the error clears
the instant it is fixed; a field **currently valid** is not re-judged until the
user leaves it. **The asymmetry is the whole idea — fast with good news, slow
with bad news.**

*Baymard's own study page is egress-blocked. Treat the specific numbers as
unverified.*

### Card sorting — archived GOV.UK service design manual (2016)
Open sort (users make and name their own groups) tells you how people think and
gives you the labels; closed sort validates a structure you already have. **~50
cards maximum. 15–30 participants**, 15 giving usable confidence, above 30
diminishing returns. Limitations stated plainly: if groupings don't converge,
analysis stalls; a large heterogeneous estate blows past 50 cards.

*The current service manual has no markdown repo and is not available via GitHub
at all. This is the only IA method reachable, and it is nine years old.*

### Sample size (NN/g) — search-extracted
Nielsen–Landauer, built from 11 studies: five participants ≈ **85%** of an
interface's usability problems, each additional person surfacing less. The
argument is ROI, not completeness.

**The caveats matter as much as the headline, and NN/g publishes them itself:**
this holds for **qualitative, formative** testing aimed at finding problems;
quantitative work needs 30+; and large-scale evaluations have found five
participants surfacing **as little as 35%** of problems on complex sites. So
"five users" is a defensible floor for "does this flow work", **not a
general-purpose evidence standard**.

---

## Synthesis — three load-bearing conclusions

**1. The journey's unit of work is the question, not the screen — and the
question must be justified before it is designed.** The question protocol sits
upstream of everything: which fields exist, hence how many steps, hence whether
you need a task list, an account, or a progress indicator. One-thing-per-page,
"never ask twice", "allow I don't know" and the optional-field policy are all
downstream consequences of having audited the questions first. **The symptom "a
task asks for information the user does not have yet" is a question-protocol
failure showing up late**, and the protocol's garbage-fill column is its
diagnostic.

**2. Failure is a designed path with a fixed choreography, not an exception
branch.** GDS and WAI converge independently: preserve everything typed; summary
above the `h1`; focus moves there; `Error: ` in the title; summary text identical
to inline text; every summary link resolves to a *specific* input with defined
rules for composite fields and radio groups; empty gets an instruction,
constraint-violation gets a description. **That is a complete, checkable
procedure** — the most cleanly answerable part of the gap.

**3. Interruption is the normal case, and the sources answer it with three
mechanisms that are usually conflated.** Save-and-resume (USWDS: it exists, and
you *say so up front*). Session-level re-entry (GDS: the task list on every
returning session, statuses carrying the memory, users declaring their own
completion). Post-completion re-entry (GDS: bookmarked confirmation pages must
still behave; USWDS: a complete unedited printable record). **Mid-flow, between
sessions, and after the fact are three different returns, and a journey needs all
three.**

---

## Improvement openings

- **The validation contradiction is live and nobody resolves it.** GDS says never
  on blur. USWDS says use inline validation. The practitioner literature says
  reward early, punish late. Three authoritative sources, three answers, **no
  cross-references.** A decision rule **keyed to field type** would be genuinely
  new: a format-constrained field the browser can judge (postcode shape, card
  length) behaves differently from free text whose validity is unknowable until
  you stop typing, which behaves differently from a field only the server can
  judge (is this username taken). **GDS's own blessed exception — the character
  counter — is exactly the "irrecoverable wasted effort" case, and they did not
  generalise it.**
- **Progress indicators are a second unresolved contradiction.** GDS defaults
  them off, citing Carer's Allowance *removing* a 12-step indicator with no harm;
  USWDS says use a step indicator. Same widget, same kind of flow.
- **Everything assumes a government transaction** — linear, logged-out, one-off,
  mandatory, with a start page you don't control. Nothing on returning-user
  journeys in a consumer product, exploratory rather than transactional flows,
  multi-device handoff, or a journey whose goal isn't "submit this and leave".
- **Short flows fall between the patterns.** Task lists are scoped to long
  multi-session transactions. **Nothing addresses the person who abandons step 3
  of 5 and returns in ten minutes** — no autosave guidance, no draft state, no
  "we kept your answers" affordance. That is the most common real interruption
  and it is unowned.
- **Deferred account creation is asserted, not mechanised.** GDS says let people
  get as far as possible first and offers reference-number lookup. It never
  describes **the conversion moment** — guest-completes-then-optionally-creates,
  what carries over, when to ask. USWDS has none at all.
- **The IA material is thin and dated**, and card sorting answers "how would you
  group this", which is **not the question the gap asks**. **Tree testing** — can
  a person find the thing in a structure you already built — is the actual test
  for whether labels work, and **it appears in none of these sources**.
- **Non-validation failures are entirely absent.** Every error source is about
  "the user typed something wrong". Nothing covers the server dying at step 4, an
  expired session eating the form, a payment timing out, or a third-party lookup
  being down mid-flow. GDS ships "problem with the service" and "service
  unavailable" pages but treats them as standalone destinations, **not as
  recoveries that preserve a journey in progress**. The gap's "errors say what is
  wrong but not how to escape" bites hardest here.
- **"Evidence rather than opinion" needs a floor the sources don't give.** Five
  users is defensible and cheap; NN/g's own caveats cap it. GDS's 15–30 for card
  sorting assumes recruitment a small team lacks. **Nobody describes the lightest
  honest check** — reading a flow aloud to one person who has never seen it, or
  auditing every question against the protocol table, which costs nothing and
  needs no participants.

---

## Evidence strength — carried into the skill

**Backed by research or case study:** Carer's Allowance removing a 12-step
progress indicator with no measurable harm (real service data, and note it argues
*against* an assumed good practice) · check-your-answers (Carer's Allowance
write-up) · stress impairs recall and error-detection (SAMHSA framework, applied
by analogy) · Nielsen–Landauer five users / 85% (real model, **contested**, as low
as 35% elsewhere, qualitative only) · inline validation reduces correction time
(Wroblewski, reached second-hand only) · error-message wording (GDS reports
comprehension and recovery; **no numbers, no study linked**).

**Asserted as convention, no research offered:** **validate on submit, never on
blur** (the most-cited GDS position and the least evidenced — the page asks for
the research itself) · **one thing per page** (asserted forcefully; the nearby
evidence is about progress indicators, not page-splitting) · "(optional)" not
asterisks · error summary placement and focus · summary link targets for
composite fields and radio groups · avoid nav in linear journeys · the addresses
pattern (no citations at all) · confirmation pages (gap flagged by GDS) ·
task-list status vocabulary ("cross-government collaboration") · card sorting's
15–30.

*Partial exception: the names pattern cites W3C's "Personal names around the
world", Baymard on split fields, and the falsehoods-programmers-believe-about-
names literature — external but real.*

## Injection attempts

**None.** One access failure recorded, not an injection: `baymard.com` returned
`EGRESS_BLOCKED`. Two 404s were path changes, not adversarial.
