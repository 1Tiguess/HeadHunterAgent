# The question protocol

The method that sits upstream of every other decision in a journey. It costs nothing, needs no
participants, and removes more bad design than any usability test.

## Contents
- [The table](#the-table)
- [The column that does the work](#the-column-that-does-the-work)
- [Worked: a support ticket form](#worked-a-support-ticket-form)
- [What the audit killed, and why](#what-the-audit-killed-and-why)
- [Running it on someone else's form](#running-it-on-someone-elses-form)
- [The four outcomes](#the-four-outcomes)
- [Sequencing, once the set is settled](#sequencing-once-the-set-is-settled)

## The table

One row per question. Five columns:

| Question | Who uses the answer | What decision it drives | Required or optional | What happens if they type anything to get past it |
|---|---|---|---|---|

**"Who"** must be a specific role doing specific work — "the fulfilment team, to decide which
warehouse picks it". **Not** "the business", "compliance", "our records", or "analytics". If nobody
can name the human, the field has no owner and no defender.

**"What decision"** must be an actual branch. "We segment on it" is not a decision unless someone can
say what changes as a result.

## The column that does the work

**What happens if they type anything to get past it?**

This converts an assertion into a testable claim. Three answers, and each means something different:

| Answer | Meaning |
|---|---|
| "Nothing — we would not notice" | **The field is decoration. Remove it.** |
| "We would act on wrong data" | **Worse than no field.** Either make it optional with an honest "I don't know", or find another source |
| "It would fail validation" | Fine — but check the validation is real and not merely a format check |

**A field people routinely garbage-fill is worse than no field**, because you now hold data that
looks real, is wrong, and someone downstream will trust it. An empty column is honest. A column full
of "n/a", "-", "1 January 1900" and "test" is a trap with a delay fuse.

## Worked: a support ticket form

Eleven fields as originally specified.

| Question | Who uses it | Decision it drives | Req? | If they type anything? |
|---|---|---|---|---|
| Email | Support agent | Where the reply goes | Req | **Reply never arrives.** Real field, and validation must be real |
| Full name | Support agent | How to address the reply | Opt | Agent says "Hello" instead. **Harmless — make it optional** |
| **Company** | *nobody could name* | *"segmentation"* | Req | **Nothing.** Nobody would notice |
| Product area | Triage | Which queue it enters | Req | **Misrouted; adds a day.** Real — but see below |
| Severity | Triage | Queue priority | Req | **Everyone picks Critical.** The data is already worthless |
| Description | Agent | Everything | Req | Ticket cannot be actioned; agent replies asking. **Real** |
| Steps to reproduce | Engineer, when escalated | Whether it can be investigated | Opt | Escalation bounces back. **Real, but only for the ~8% escalated** |
| **Browser version** | Engineer, sometimes | Sometimes nothing | Req | **Wrong data worse than none** — and it is detectable automatically |
| **Account number** | Billing, for billing tickets only | Which account | Req | Wrong account looked up. **Real for billing, irrelevant for the other 80%** |
| **How did you hear about us** | Marketing | *"reporting"* | Opt | **Nothing.** Wrong place entirely |
| **Phone number** | *"in case we need to call"* | — | Req | **Nothing — we have never called** |

### After the audit

| Removed | Why |
|---|---|
| Company | No named user, no decision |
| How did you hear about us | Marketing research in a support flow. Wrong place |
| Phone number | A capability nobody uses, collected from everyone |
| Browser version | **Detected automatically.** Never ask for something you can observe |

| Changed | How |
|---|---|
| Full name | Required → **optional** |
| Severity | Free choice → **behavioural descriptions** ("I can't work at all" / "There's a workaround" / "It's annoying"). Asking someone to rate their own urgency produces one answer |
| Account number | **Conditional** — only on the billing branch |
| Steps to reproduce | **Deferred** to the escalation step, where it is actually needed |

**Eleven fields to six on the main path**, and the six that remain each have a named user and a real
decision. Nothing was made prettier; the flow got shorter because most of it should not have
existed.

## What the audit killed, and why

Four recurring patterns, each worth recognising by name:

**1. The unnamed stakeholder.** "Company" existed because it has always existed. Ask for the human.
If nobody can be produced, the field has nobody to defend it.

**2. The observable fact.** Browser version, referrer, locale, timezone, device. **Never ask for
something you can detect.** A typed answer is less accurate than the one you already have.

**3. The self-rating.** Severity, urgency, importance. Everyone picks the top value, so the field
carries no signal. **Replace with behavioural descriptions** that map to your categories — the user
describes their situation; you infer the rating.

**4. The wrong-context question.** "How did you hear about us" is a real marketing question asked in
a place where the person is annoyed and wants help. Right question, wrong journey.

## Running it on someone else's form

You will not always control the requirements. Run the audit anyway and bring the table, not an
opinion. Three things make the conversation work:

- **Ask for the name, not the reason.** "Who reads this?" is answerable or it is not. "Why do we need
  this?" invites a justification, and every field can be justified.
- **Lead with the garbage-fill column.** "About a third of these will be 'n/a' — is that usable?" is
  a question about data quality, which is someone's job, rather than a question about design, which
  is yours.
- **Offer conditional and deferred, not just deletion.** "Only on the billing branch" and "at
  escalation, where it is actually used" both keep the data and shorten the flow. Most resistance is
  to losing the field, not to moving it.

## The four outcomes

Every question ends in one of these:

| Outcome | When |
|---|---|
| **Keep** | Named user, real decision, garbage-fill has consequences |
| **Make optional** | Named user, real decision, **garbage-fill is harmless** |
| **Make conditional** | Real for one branch, irrelevant for the others |
| **Defer** | Needed later in the process, not at this step |
| **Remove** | No named user, or no decision, or the answer is observable |

**"Defer" is the outcome that fixes the symptom "a task asks for information the user does not have
yet."** The field is legitimate; asking for it now is not. Move it to the point where the user has
the information or the system actually needs it.

## Sequencing, once the set is settled

The audit tells you which questions exist. Then:

1. **Simple before complex.** Early questions build momentum.
2. **Group by what the user has to hand**, not by your data model. All the questions answerable from
   a passport should be adjacent, because the passport comes out once.
3. **Cheap before expensive.** Do not make someone find a document before you have established they
   are eligible.
4. **Branching questions as early as they can be answered**, so irrelevant branches never appear.
5. **Deferred questions at the point of need**, and say why you are asking now.

That ordering falls out of the audit almost mechanically. The audit is the work; the sequence is the
consequence.
