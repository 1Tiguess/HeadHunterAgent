# Interruption and return

Three different returns, three different mechanisms. The sources conflate them; a real flow needs all
three.

## Contents
- [The three returns](#the-three-returns)
- [Mid-flow: save and resume](#mid-flow-save-and-resume)
- [The short-flow gap](#the-short-flow-gap)
- [Between sessions: the task list](#between-sessions-the-task-list)
- [The status vocabulary](#the-status-vocabulary)
- [Letting the user declare completion](#letting-the-user-declare-completion)
- [After the fact: the receipt](#after-the-fact-the-receipt)
- [The printable record](#the-printable-record)

## The three returns

| Return | When | Mechanism |
|---|---|---|
| **Mid-flow** | Minutes to hours. Phone rang, ran out of battery, needed a document | Autosave + an announced resume capability |
| **Between sessions** | Days to weeks. A long application with several parts | A task list shown on every re-entry, carrying state in its statuses |
| **After completion** | Weeks to months. "What did I actually submit?" | A confirmation URL that still works, plus a saved record |

Building one and calling it "resume" leaves the other two broken. The most commonly missing one is
the first.

## Mid-flow: save and resume

**Save and resume is a requirement, not a nicety.**

And the part almost always missed:

> **Tell the user up front that it exists.**

The situations anticipated are someone on a phone, in a public place, or facing a question too
painful or too complicated to answer right now. **Knowing you can stop changes whether you start.**
A resume capability nobody knows about does not do the job it was built for — the person who would
have used it already closed the tab.

Put it on the start page, in the words the user would use: *"You can save your answers and come back
later."* Not a feature list item. A permission.

**Also provide human escape hatches** — phone, chat — reachable **from inside the flow**, not only
from a contact page three clicks away. Someone stuck at step 4 will not go looking.

## The short-flow gap

Task lists are explicitly scoped to **long transactions spanning multiple sessions**. Nothing in the
published guidance addresses the person who abandons step 3 of 5 and returns in ten minutes.

**That is the most common real interruption, and it is unowned.** What it needs:

**Autosave per step, not per session.** Write on every continue, not on a timer and not on unload —
`beforeunload` is unreliable on mobile, which is where the interruption happens.

**A visible "we've kept your answers" affordance on return.** Silence is indistinguishable from data
loss, so the user starts over defensively even though they did not have to.

```
Welcome back
You last answered "Your address" about 10 minutes ago.
[ Continue where you left off ]    [ Start again ]
```

**"Start again" matters.** Someone returning may have changed their mind about something early on,
and a flow that only offers "continue" traps them.

**A draft state with an explicit lifetime, and say what it is.** "We'll keep your answers for 7
days." An unstated lifetime means the user cannot plan, and a silent expiry is a second, worse data
loss.

**A resume entry point that is not the start page.** A link in the confirmation email, a card on the
dashboard, or a cookie-based prompt. Making someone re-navigate the whole entry path is a second
chance to abandon.

**Do not require an account for this.** A signed resume token in a URL, emailed or texted, is enough
— and it is the same mechanism as the reference-number substitute for accounts.

## Between sessions: the task list

For long transactions spanning multiple sessions.

**Simplify first.** If you can cut tasks or steps, you may not need a task list at all — a task list
is a way of managing complexity you could not remove, not a feature to add.

**Shown at the start of the transaction, and at the start of every returning session.** That is the
resume mechanism: the user's memory of where they were is reconstructed from the statuses rather than
from their own recall.

**Task names start with verbs** — "Check your details", "Declare your income", "Report a change" —
and **summarise a group of activities** rather than naming a screen. A task called "Personal details
form" describes your architecture; "Tell us about yourself" describes their job.

**Tasks should be completable in any order** where the domain allows it. Where it does not, that is
what "Cannot start yet" is for.

## The status vocabulary

Designed, not decorative. Each choice carries a reason worth preserving.

| Status | Treatment | Reason |
|---|---|---|
| **Completed** | Plain text, **no tag** | **Deliberately de-emphasised.** Attention should go to what is left, not to a wall of green |
| **Not yet started** | Neutral tag | |
| **In progress** | Tag | |
| **Cannot start yet** | Grey, **and unlinked** | For genuine prerequisites only. Unlinked because a link that does nothing is worse than no link |
| **There is a problem** | **Red — reserved exclusively for errors** | So the colour keeps its meaning. Using red for "overdue" or "important" spends it |

**Statuses are adjectives in sentence case, not verbs.** "Completed", not "Complete this". The status
describes the state; the task name carries the action.

**The de-emphasis of "Completed" is the non-obvious one**, and it is right: a task list is a tool for
answering "what do I still have to do", and a prominent tag on every finished item competes with the
answer.

**"Cannot start yet" must be honest.** Use it only where a genuine dependency exists. If the real
reason is that your architecture prefers an order, fix the architecture or allow the order.

## Letting the user declare completion

Where a section is long, or largely optional, **inferring completion from field counts is always
wrong** — an optional field left blank is indistinguishable from an unfinished one.

End the section by asking:

> **Have you completed this section?**
> - Yes, I've completed this section
> - **No, I'll come back to it later**

The user knows whether they are finished. Your field-count heuristic does not, and it will either nag
someone who is done or mark someone complete who is not.

This also gives the task list something true to display, rather than a percentage that means nothing.

## After the fact: the receipt

**Users bookmark confirmation pages and treat them as receipts.** The URL will be revisited, weeks
later, from a different device, possibly without a session.

**So that page must behave when revisited.** Two acceptable designs:

1. **Serve the real thing again** — the full confirmation, with the reference number and status
2. **Serve a useful substitute** — links for tracking the application, starting a new one, and who to
   contact if something is wrong

**Not acceptable:** a 404, a redirect to the start page, or a session-expired login wall. All three
tell the user their record is gone.

### Contents of a confirmation page

- **Reference number**, prominent and selectable
- **What happens next, and when** — a date or a range, not "shortly"
- **Contact details** for this service
- **Onward links** to what they will likely need next
- **A feedback link**
- **A way to save a record** — print, PDF, or email

*Accessibility note: interactive elements inside a coloured confirmation panel need contrast and
focus adjustment to clear 3:1 against that background.*

*An open question the sources name themselves: confirming a transaction that is one step inside a
larger user task — where "what happens next" matters more than "you're done" — is unresolved. If that
is your case, you are past the published guidance.*

## The printable record

The artefact the user keeps. Treat it as evidence, because that is what it is for.

**Contents:**

- Site name and URL
- **Date and time of submission**
- Confirmation of submission
- **Every question asked, and the answer given**
- Any case or reference ID

> **Do not cherry-pick which questions appear in the record.**

Include everything asked — including questions they skipped, shown as "Not provided". The record's
purpose is to be **evidence of what you told them**, and a curated subset cannot serve that purpose.
If a dispute arises about what was declared, a partial record is worth nothing.

**Mask sensitive values partially** — last four digits of an account or card. Enough to identify,
not enough to leak if the page is printed and left somewhere.

**Print craft**, which is easy to get wrong because nobody tests it:

- **Points, not pixels.** Serif around 12pt
- **Links underlined with the URL spelled out** — a printed hyperlink with no URL is dead
- **Table headers repeated on each page**
- **Widow and orphan control**, so a question and its answer do not split across a page break
- Half-inch margins minimum
- **Generate a PDF for mobile**, where browser printing is unreliable
- Test across more than one printer

**Offer it at the confirmation step and by email.** The person who most needs the record is the one
who closed the tab.
