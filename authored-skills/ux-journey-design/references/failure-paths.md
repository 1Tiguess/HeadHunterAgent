# Failure paths

## Contents
- [The choreography, as a checklist](#the-choreography-as-a-checklist)
- [Summary link targets](#summary-link-targets)
- [The message bank](#the-message-bank)
- [Four messages, not one](#four-messages-not-one)
- [Non-validation failures](#non-validation-failures)
- [Session expiry](#session-expiry)
- [The accessibility layer](#the-accessibility-layer)

## The choreography, as a checklist

When a submission fails, in order:

- [ ] **Every value the user typed is returned to the form.** They see what went wrong, edit rather
      than retype, and lose nothing
- [ ] **Error summary** rendered at the top of `main`, below back link and breadcrumbs, **above the
      `<h1>`**
- [ ] Summary heading is **"There is a problem"**
- [ ] **Keyboard focus moves to the summary** on render
- [ ] **`<title>` is prefixed with `Error: `**
- [ ] One summary link **per erroneous answer**, in the order the questions appear
- [ ] Each link **resolves to a specific input** (see below)
- [ ] **Inline message beside each bad field**
- [ ] Inline message pairs a **visual cue with text** — never colour alone
- [ ] **Summary text and inline text are word-for-word identical**
- [ ] The page does not scroll the user somewhere they did not ask to go, beyond the focus move

**Why focus moves to the summary rather than the first bad field:** the summary tells you *how many*
things are wrong and lets you choose where to start. Jumping straight to the first field hides the
scope of the problem.

**Why the title changes:** a screen reader announces the document title on page load, before any
content. Without the prefix, the first thing announced after a failed submission is the same title as
before, and nothing signals that the submission failed.

## Summary link targets

| Field shape | Link target |
|---|---|
| Single input, select, textarea | The control itself |
| **Composite** — a date split into day/month/year, an address across several lines | **The first input containing an error.** If you cannot determine which, the first input of the group |
| **Radio group or checkbox group** | **The first option in the group** — never the fieldset, never the legend |

The radio rule exists because a fieldset is not focusable in a useful way; focusing it announces the
legend and leaves the user without a landing point they can act on. The first option is both
focusable and adjacent to the legend, so the context is still announced.

The composite rule matters more than it looks: linking to "the date field" when only the year is
wrong makes the user re-check three inputs to find the one at fault.

## The message bank

**Every message does two jobs: what happened, and how to get out.**

### Banned

| Banned | Why |
|---|---|
| Jargon — "form post error", "unspecified error", "validation failed" | Names a system state, not a user problem |
| Blame — "you forgot", "you failed to" | Puts the fault on the person |
| Legal register — "forbidden", "illegal", "prohibited", "not permitted" | Alarming out of proportion |
| **"Please"** | Implies the fix is optional |
| **"Sorry"** | Does not help them fix it |
| **"Valid" / "invalid"** | **Carries no information.** "Invalid date" does not say what is wrong |
| Jokes | Not funny on the third attempt |
| "Oops", "Whoops", "Uh oh" | Same |

### The grammatical rule

> **An empty field gets an instruction. A constraint violation gets a description.**

| Failure | Message | Form |
|---|---|---|
| Empty | "Enter your first name" | **Instruction** — imperative verb |
| Too long | "First name must be 35 characters or less" | **Description** — states the rule |
| Wrong format | "Enter a date in the format DD MM YYYY" | Instruction, with the format |
| Out of range | "Date of birth must be in the past" | Description |
| Nothing selected | "Select whether you have a driving licence" | Instruction |
| Not ticked | "Confirm you agree to the terms" | Instruction |
| Not unique | "This email address is already registered. Sign in instead" | Description **plus a route out** |

The distinction is not stylistic. An empty field needs the user to *do* something, so an imperative
is the shortest path. A constraint violation needs them to *understand* a rule before they can act,
so a description is.

### Before and after

| Before | After |
|---|---|
| "Invalid input" | "Enter your postcode" |
| "Error: field required" | "Enter your date of birth" |
| "Please enter a valid email address" | "Enter an email address in the correct format, like name@example.com" |
| "Password does not meet requirements" | "Password must be 15 characters or more" |
| "Sorry, something went wrong" | "Your answers are saved. Try again in a few minutes" |
| "Invalid date" | "Date of birth must be in the past" |
| "Forbidden" | "You do not have access to this. Contact your administrator" |

**The authoring test:** read it aloud and ask whether you would say it to someone sitting next to
you. "Please enter a valid email address" fails the test — nobody speaks that way.

## Four messages, not one

The same field has different failure modes and each needs its own message. A single "Enter a valid
email address" covering all of them tells the user nothing about which problem they have.

```
Email address
├─ empty            → "Enter an email address"
├─ no @             → "Enter an email address in the correct format, like name@example.com"
├─ too long         → "Email address must be 254 characters or less"
└─ already in use   → "This email address is already registered. Sign in instead"
```

```
Date of birth
├─ empty            → "Enter your date of birth"
├─ partial          → "Date of birth must include a month"        ← names the missing part
├─ non-numeric      → "Date of birth must be a real date"
├─ in the future    → "Date of birth must be in the past"
└─ implausible      → "Date of birth must be after 1900"
```

The partial-date case is the one most often collapsed, and it is the most useful to separate:
**naming the missing part** turns a re-check of three inputs into a single correction.

## Non-validation failures

Every published error guidance covers "the user typed something wrong". Almost none covers the
server dying at step 4 — and that is where **"the error says what is wrong but not how to escape"**
bites hardest.

Design these as **recoveries that preserve a journey in progress**, not as standalone destination
pages that end it.

| Failure | The user needs | The trap |
|---|---|---|
| **Server error mid-flow** | Their answers are safe · a way back in · what to do if it repeats | A generic 500 page that loses the form |
| **Session expired** | Plain statement · **form preserved** · return to the same step after re-auth | Redirecting to login and discarding everything |
| **Payment timeout** | **Whether they were charged.** That is the only question | "Something went wrong" — now they try again and fear a double charge |
| **Third-party lookup down** | A manual path — let them type what the lookup would have returned | Blocking the flow on a dependency the user did not choose |
| **Rate limited** | When to try again, **concretely** | "Too many requests" |
| **Upload failed** | Which file · whether the others survived · the size or type limit | "Upload failed" with the whole set discarded |
| **Validation passed, business rule failed** | What rule, and what they can do instead | Presenting it as a form error next to a field that is fine |

**The payment case deserves emphasis.** A user who does not know whether they were charged will
either abandon or retry, and both are bad. Say what you know: "We have not taken a payment. You can
safely try again" or "Your payment went through but we could not confirm your order — do not try
again, we will email you within an hour."

## Session expiry

The most common non-validation failure and the most damaging, because it converts a minor annoyance
into total abandonment.

**Three rules:**

1. **Warn before it happens**, with a way to extend **without leaving the page**. A modal with "Stay
   signed in" is enough.
2. **Persist the draft before authentication is checked**, not after. If the check happens first, the
   answers are gone by the time you know you needed them.
3. **Return to the step they were on** after re-authentication, with the form repopulated. Not the
   start page, not the dashboard.

The mechanism costs one draft record keyed by session or by a resume token. The alternative is losing
the user entirely, having already got most of the way through.

## The accessibility layer

Where this skill hands off to `design-token-systems`:

| Belongs here | Belongs to `design-token-systems` |
|---|---|
| The summary exists, and where | `aria-describedby` wiring per field |
| Focus lands on the summary | Focus ring styling and visibility |
| Links resolve to the right target | Error id association markup |
| `Error: ` in the title | Colour contrast of the error state |
| What the message says | How the message is announced structurally |

**The live-region rule**, which is the accessibility restatement of "do not punish people mid-entry":

- **`aria-live="polite"`** — for anything non-urgent. **Waits for a pause and does not interrupt what
  the user is doing.** This is correct for an async username-availability check.
- **`aria-live="assertive"`** — interrupts immediately. Justified only when interrupting is. **On-focus
  validation is named as an assertive case**, which is precisely why on-focus validation is hostile:
  it cuts into what someone is doing, mid-word.

**Success confirmation gets equal billing with errors.** A form that announces every failure and
nothing on success leaves screen-reader users unsure whether anything happened.

**Mark required fields in the visible label**, not only programmatically — the attribute alone does
not reach everyone.
