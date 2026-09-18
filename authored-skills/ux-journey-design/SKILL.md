---
name: ux-journey-design
description: Designs the path between screens rather than the screens themselves — justifying every question before designing it, choosing validation timing per field type instead of applying one blanket rule, the fixed choreography a failed submission must follow, recovery from server and session failures mid-flow, the three different kinds of return (mid-flow, between sessions, after completion), deferring account creation, and how much research evidence a claim actually needs. Use when designing or reviewing a signup, checkout, onboarding, application form, wizard or multi-step flow; when users drop off partway, lose their answers, face too many fields, cannot tell what to do next, or get errors that say what is wrong but not how to escape.
allowed-tools: Read, Write, Edit, Glob, Grep
---

# UX journey design

This is about **what happens between screens**. Individual pages are usually fine; the path through
them is where flows fail.

**Boundaries with the rest of the shelf** — keep these separate or the three skills fight each other:

| Skill | Owns |
|---|---|
| `app-interface-design` | Layout, navigation architecture, per-screen density |
| `design-token-systems` | Per-field wiring: `aria-describedby`, error id association, focus styling |
| **this skill** | Which questions exist, in what order, what survives an interruption, what the failure path looks like |

**A note on evidence, because it shapes how to read everything below.** The government design systems
that dominate this space are excellent and openly convention-driven in places — the most-cited rule
of all, "never validate on blur", carries a note from its own authors **asking for the research they
do not have**. This skill marks which positions are evidenced and which are house style, because
presenting house style as evidence is the failure it exists to prevent. See
`references/evidence.md`.

## 1. Before designing anything: the question protocol

**The journey's unit of work is the question, not the screen.** How many questions exist determines
how many steps exist, which determines whether you need a task list, an account, or a progress
indicator. Everything downstream is a consequence of this audit.

Build a table. One row per question:

| Question | Who uses the answer | What decision it drives | Required? | **What if they type anything to get past it?** |
|---|---|---|---|---|

**The last column does the work.** It converts "we need this" into a testable claim, because **a
field people routinely garbage-fill is worse than no field** — you now have data that looks real,
is wrong, and someone downstream will trust.

The discipline is to find **the specific humans who use the answer in their actual work**, not to
accept a department's assertion that it is needed. Once you know which decision the data drives, you
can price that decision against the cost of collecting it.

**This is also the diagnostic for the symptom "a task asks for information the user does not have
yet."** That is a question-protocol failure surfacing late. If nobody could name who uses the answer,
the field should not exist. If someone can, the question is *when* to ask — which is a sequencing
problem, not a field problem.

## 2. One thing per page, and when it does not apply

The default: **one question per page.** Back link, heading, the question, continue.

- **The heading *is* the question**, not the section name. Section context goes in a caption above.
- Optional fields get **"(optional)"** appended to the label or legend. **Never asterisks** — nothing
  tells a first-time user what an asterisk means, and screen readers announce it as "star".
- **Never ask the same thing twice.** Pre-populate or carry forward.
- **Allow "I don't know" as a real answer** rather than forcing a guess. A guess enters your data as
  fact.

**When it does not apply**, and this is narrower than most people assume: **internal and caseworker
tools, where the operator switches tasks rapidly and wants density.** Combining questions is
legitimate there, and legitimate elsewhere only with research behind it.

**Progress indicators are opt-out by default.** Add one only after research shows users need it. The
strongest piece of real service data available runs *against* the assumption: a government service
**removed a 12-step progress indicator with no measurable harm** to completion rates or times.

## 3. Order and dependency

- **Simple before complex.** Early questions build momentum; a hard one first costs you the people
  who would have finished.
- **One micro-topic at a time.**
- **Let people complete in the order they choose** where the domain allows it — **but warn when a
  change invalidates earlier answers.** Silently discarding work is worse than refusing the change.
- **Eligibility does not go on the start page.** Complex eligibility rules move *inside* the flow as
  questions. The start page's job is **orientation, not qualification**.
- List what people need **to hand** — but **not things they know from memory.** "You'll need your
  name" is noise that trains people to skip the list that also says "you'll need your policy number".

## 4. Validation timing

Three authoritative sources give three different answers here and none cites the others. **The
resolution is that the question is wrong: timing is not one decision, it is a decision per field
type.**

| Field type | When to validate | Why |
|---|---|---|
| **Format-constrained, browser-judgeable** (postcode shape, card length, date parts) | **On submit** — but a live counter is warranted where effort would otherwise be **irrecoverable** | You *can* judge it early, but judging it at character 3 of 8 is just noise |
| **Free text** (name, address line, description) | **On submit only** | You cannot know if it is valid until entry ends. Early judgement punishes slow typists |
| **Server-judgeable** (is this username taken, does this reference exist) | **Async, `aria-live="polite"`** | The answer is not local. Polite waits for a pause; assertive cuts in mid-word |

**The character counter is the generalisable case.** It is the one live-feedback example the sources
bless, and the stated reason is that **the user is about to waste effort they cannot recover**. That
principle generalises: live feedback is warranted exactly when the alternative is unrecoverable
wasted work. It was never generalised upstream; it is the rule.

**Then the asymmetry that unifies all three rows:**

> **A field currently in error re-validates immediately on edit, so the error clears the instant it
> is fixed. A field currently valid is not re-judged until the user leaves it.**
>
> Fast with good news, slow with bad news.

**Implementation posture:** server-side validation **always**; client-side never trusted. Use
`novalidate` on the form and do not rely on the `required` attribute for the user-facing experience,
so the browser's native bubbles do not pre-empt your designed errors. *(Note: whether removing
`required` harms screen-reader users is explicitly flagged as unresearched by the source that
recommends it. Mark required fields in the visible label as well as programmatically.)*

**Be forgiving of input formats.** Accept spaces in card numbers, any separator in dates, mixed case
in postcodes. Rejecting a correct answer because of its punctuation is a self-inflicted error.

## 5. The failure choreography

When a submission fails, this sequence is fixed. It is the most cleanly checkable part of the skill.

1. **Preserve everything the user typed.** They should be able to see what went wrong, edit rather
   than retype, and not lose work.
2. **Error summary** at the top of `main`, below the back link and breadcrumbs, **above the `<h1>`**.
   Heading: "There is a problem".
3. **Move keyboard focus to the summary.**
4. **Prefix `Error: ` onto the `<title>`**, so a screen reader announces the failure before anything
   else.
5. **Inline message beside each bad field**, pairing a visual cue with text — **never colour alone**.
6. **Summary text and inline text are word-for-word identical.** A user who reads one and then the
   other should not have to re-parse.

**Summary link targets** — one link per erroneous answer, in question order, each resolving to a
*specific* input:

| Field shape | Link to |
|---|---|
| Single control | The control |
| **Composite** (a date, an address) | The **first input containing an error**; the first input if you cannot tell |
| **Radios or checkboxes** | The **first option** in the group — **never the fieldset** |

### The wording system

Every message does two jobs: **what happened, and how to get out.**

**Banned:** jargon ("form post error", "unspecified error") · blame and legal register ("forbidden",
"illegal", "prohibited", "you forgot") · **"please"** (implies the fix is optional) · **"sorry"**
(does not help) · **"valid" / "invalid"** (carries no information) · jokes.

**The grammatical rule, which is the sharp part:**

> **An empty field gets an instruction. A constraint violation gets a description.**
>
> "Enter your first name" — vs — "First name must be 35 characters or less."

**Different failure modes on the same field need different messages.** Empty, too long, wrong format
and illegal characters are **four messages, not one**.

**The authoring test:** read it aloud and ask whether you would say it to someone.

## 6. Non-validation failures

Every error source covers "the user typed something wrong". **Almost nothing covers the server dying
at step 4** — and that is where "the error says what is wrong but not how to escape" bites hardest.

Design these as **recoveries that preserve a journey in progress**, not as standalone destination
pages:

| Failure | What the user needs |
|---|---|
| **Server error mid-flow** | Their answers are safe; a way back in; what to do if it repeats |
| **Session expired** | Say so plainly, **do not lose the form**, and return them to the step they were on after re-auth |
| **Payment timeout** | Whether they were charged. This is the only question they have |
| **Third-party lookup down** | A manual path — let them type what the lookup would have found |
| **Rate limited** | When to try again, concretely |

**The session-expiry case is the most common and the most damaging.** An expired session that
discards a half-filled form converts a minor annoyance into total abandonment. Persist the draft
before authentication is checked, not after.

**Warn before the session expires**, with a way to extend without leaving the page.

## 7. The three returns

Sources conflate these. They are three different mechanisms and a real flow needs all three.

### Mid-flow — save and resume

**Save and resume is a requirement, not a nicety.** And the part usually missed:

> **Tell the user up front that it exists.**

The anticipated situations are a phone, a public place, or a question too painful to answer right
now. **Knowing you can stop changes whether you start.** A resume capability nobody knows about does
not do the job it was built for.

**The short-flow gap.** Task lists are scoped to long transactions spanning multiple sessions.
Nothing upstream addresses the person who abandons step 3 of 5 and comes back in ten minutes — which
is the most common real interruption. For those:

- **autosave per step**, not per session
- a visible **"we've kept your answers"** affordance on return
- a **draft state with an explicit lifetime**, and say what it is
- a **resume entry point that is not the start page**

### Between sessions — the task list

For long transactions spanning multiple sessions. **Simplify first** — if you can cut tasks or steps,
you may not need one at all.

**Shown at the start of the transaction and at the start of every returning session.** That is the
resume mechanism.

The status vocabulary is designed, not decorative:

| Status | Treatment | Why |
|---|---|---|
| **Completed** | Plain, **no tag** | Deliberately de-emphasised so attention goes to what is left |
| **Not yet started** | Tag | |
| **In progress** | Tag | |
| **Cannot start yet** | Grey, **unlinked** | For genuine prerequisites only |
| **There is a problem** | **Red — reserved exclusively for errors** | So the colour keeps its meaning |

Statuses are **adjectives in sentence case**, not verbs. Task names **start with verbs** and summarise
a group of activities rather than naming a screen. Tasks completable in any order where possible.

**Let the user declare their own completion.** Where a section is long or largely optional, end it
with "Have you completed this section?" and a **"No, I'll come back later"** option — rather than
inferring completion from field counts, which is always wrong for optional fields.

### After the fact — the receipt

**Users bookmark confirmation pages and treat them as receipts.** So that URL must still behave weeks
later — either serve the real thing again, or serve links for tracking the application, starting a
new one, and who to contact if something is wrong.

A confirmation page carries: **reference number · what happens next and when · contact details ·
onward links · a feedback link · a way to save a record.**

**The printable record** must contain **every question and the answer given**.

> **Do not cherry-pick which questions appear.** The record's purpose is to be evidence of what you
> told them.

Mask sensitive values partially (last four digits). Print craft: points not pixels, links underlined
with URLs spelled out, table headers repeated per page.

*One open question the sources name themselves: how to confirm a transaction that is one step inside
a larger task, where "what happens next" matters more than "you're done", is unresolved. If that is
your case, you are past the guidance.*

## 8. Review before commit

A check-your-answers page immediately before submission. For long multi-section flows, one at the end
of **each section** — and the trigger for splitting is **when different people complete different
sections.**

**The return loop is the valuable mechanic**, and it is usually built wrong:

- A **"Change" link per row**, each with visually-hidden text naming what it changes ("Change *date
  of birth*")
- It returns to the original question page, **pre-populated and looking the same as before**
- **Continue then goes straight back to the check page** — not forward through the intervening steps
- If the change opens new follow-up questions, **those are asked first**, then back to the check page
- Skipped optional answers render **"Not provided"**, not blank

Copy rules: **state explicitly that nothing is submitted until they confirm** · re-phrase questions
into statements for scanning · hide sections that do not apply · **the submit button names the actual
consequence**, not "Submit".

## 9. Accounts

**An account is a cost, not a feature.** Two named harms: a drop-out barrier, and an ongoing build
and maintenance burden.

**Justified when** users need to return regularly to access or update their data. Not otherwise.

**Defer as long as possible** — let people use as much of the service as they can before registering.

**The substitute for a one-off transaction is a reference number**, paired with a name or email for
status lookups. And because reference numbers are hard to remember: **email or text it**, do not
display it once and hope.

Also: **no CAPTCHAs or cognitive puzzles** · "Create an account" as fixed terminology · account
creation visually distinct from sign-in · no duplicate data entry · nothing distracting on the
registration screen · **never a national ID number as an identity check**.

**The conversion moment**, which the sources assert should exist and never describe:

```
guest completes the task
        │
        ▼
confirmation page — the value is now concrete
        │
        ├─ "Create an account to track this and skip these questions next time"
        │
        ▼
account created, submitted data carried forward, nothing re-asked
```

Ask **after** the value is delivered, not before. At that point the offer is about the next time, and
the answer to "why should I?" is visible on the screen.

## 10. How much evidence is enough

Claims about what users want need a method attached. The methods, and what each actually answers:

| Method | Answers | Sample |
|---|---|---|
| **The question protocol** | Should this field exist? | **Zero participants** |
| Reading the flow aloud to one person | Does this make sense? | **One** |
| Usability testing, qualitative | Where does this break? | ~5 finds ≈85% of problems |
| **Open card sort** | How do people group this, and what do they call it? | 15–30, ~50 cards max |
| **Closed card sort** | Does my structure match theirs? | 15–30 |
| **Tree testing** | **Can someone find the thing in the structure I built?** | 15+ |
| Quantitative testing | How much better is A than B? | **30+** |

**The five-users figure is real, contested, and narrower than it is quoted.** It comes from a model
built on 11 studies and holds for **qualitative, formative** testing aimed at finding problems. Its
own authors publish the caveats: quantitative work needs 30+, and large-scale evaluations have found
five participants surfacing **as little as 35%** of problems on complex sites. Five is a defensible
**floor** for "does this flow work", not a general-purpose evidence standard.

**Card sorting answers the wrong question** for most label problems. It tells you how people *would*
group things. **Tree testing tells you whether they can find something in the structure you already
built** — which is the question you actually have. It appears in none of the major design-system
sources.

**The zero-participant floor**, for when you have no recruitment capacity at all: audit every
question against the protocol table, and read the flow aloud to one person who has never seen it.
Both cost nothing and both catch real problems.

## Where this guidance stops

Every source behind this skill assumes a **government transaction**: linear, logged-out, one-off,
mandatory, with a start page you do not control and a content team signing off copy.

**Not covered anywhere, so treat as unmapped:** returning-user journeys in a consumer product ·
exploratory rather than transactional flows · multi-device handoff mid-journey · journeys whose goal
is not "submit this and leave".

## Review checklist

- [ ] Every field can name the decision it drives
- [ ] Validation timing chosen per field type, with a reason
- [ ] A field in error re-validates on edit; a valid field waits for blur
- [ ] Errors preserve input, focus the summary, prefix the title, match summary to inline
- [ ] Empty-field and constraint messages are grammatically different
- [ ] Summary links resolve to a specific input; radio groups point at the first option
- [ ] Abandoning and returning does not lose answers, at any flow length
- [ ] Save-and-resume, where it exists, is announced before the user starts
- [ ] Server, session and third-party failures have designed recoveries
- [ ] Account creation is deferred, or justified by a return-to-your-data need
- [ ] The confirmation page works when revisited from a bookmark
- [ ] The printable record contains every question asked
- [ ] Claims about users are traceable to a method, with its limits stated

## References

- `references/question-protocol.md` — the table worked on a real form, and the fields it kills
- `references/failure-paths.md` — the choreography as a checklist, a message bank, and the
  non-validation failures
- `references/interruption.md` — the three returns, status vocabulary, short-flow autosave, the record
- `references/evidence.md` — **the convention-vs-evidence table**, and what each method answers
