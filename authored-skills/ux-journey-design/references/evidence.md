# Evidence

**Read this before the rest of the skill.** It constrains how confidently anything else may be
stated.

## Contents
- [Why this file exists](#why-this-file-exists)
- [The convention-vs-evidence table](#the-convention-vs-evidence-table)
- [The contradictions nobody resolves](#the-contradictions-nobody-resolves)
- [What each method answers](#what-each-method-answers)
- [Sample sizes, with the caveats the sources publish themselves](#sample-sizes-with-the-caveats-the-sources-publish-themselves)
- [The zero-participant floor](#the-zero-participant-floor)
- [How to cite this in a decision](#how-to-cite-this-in-a-decision)

## Why this file exists

The government design systems that dominate journey design are genuinely excellent, and they are
**openly convention-driven in places**. The validation page — the source of the most-repeated rule in
the field — states that its justification is long use across many services, and then **explicitly
asks for the research it does not have**, naming two open questions: whether client-side validation is
needed at all, and how screen readers behave when the `required` attribute is absent.

That honesty is admirable and it is also the seam this skill works in. **Presenting house style as
evidence is the failure this skill exists to prevent**, so it cannot commit that failure itself.

Neither column below means "wrong". A convention refined across hundreds of public services is
better than an invention. It just cannot be cited as a finding, and it can be departed from with
reasons rather than requiring counter-evidence.

## The convention-vs-evidence table

### Backed by research or a case study

| Claim | Evidence | Strength |
|---|---|---|
| **A 12-step progress indicator was removed from a live service with no measurable harm to completion rates or times** | Real service data | **Strongest single finding here** — and note it argues *against* an assumed good practice |
| Check-your-answers works | A service write-up | Moderate — a case study, not a controlled comparison |
| **People under stress have poor recall, make more errors, and do not notice the errors they make** | Clinical trauma-informed framework, applied by analogy | Moderate — real literature, analogical application |
| Five users find ≈85% of usability problems | A model built from 11 studies | Real, **and contested** — see below |
| Inline validation reduces correction time | Usability research | **Reached second-hand only.** The primary study page was unreachable. **Do not quote a number** |
| Error-message wording aids comprehension and recovery | Reported testing | Weak-to-moderate — no numbers, no study linked |

### Asserted as convention, no research offered

| Claim | Note |
|---|---|
| **Validate on submit, never on blur** | **The most-cited position in the field and the least evidenced.** The page asks for the research itself |
| **One thing per page** | Asserted forcefully. The evidence attached nearby is about progress indicators, not page-splitting. Its reputation outruns its citations |
| "(optional)" in labels, never asterisks | Convention |
| Error summary placement and focus behaviour | Accessibility reasoning, no research cited |
| Summary link targets for composite fields and radio groups | Reasoned, not tested |
| Avoid navigation in linear journeys | No research; defers to open discussion |
| The addresses pattern | The page carries no research citations at all |
| Confirmation page contents | The source **explicitly flags its own research gap** |
| Task-list status vocabulary | "Cross-government collaboration"; findings held elsewhere |
| Card sorting's 15–30 participants | Methodological convention |

*Partial exception: the personal-names guidance cites external sources — W3C's "Personal names around
the world", published research on split name fields, and the falsehoods-programmers-believe
literature. External and real, though not the design system's own testing.*

## The contradictions nobody resolves

Two live disagreements between authoritative sources, neither of which cross-references the other.

### Validation timing

| Source | Position |
|---|---|
| Government design system A | **Never on blur.** Wait for submit. As-you-type only with research |
| Government design system B | **Use inline validation** with actionable messages |
| Practitioner literature | **"Reward early, punish late"** — re-validate an errored field on edit, leave a valid field alone until blur |

Three authorities, three answers, no cross-references. **The resolution this skill adopts** — a rule
keyed to *field type*, plus the reward-early/punish-late asymmetry — is **synthesis, not citation.**
It is reasoned from the blessed exception (the character counter, justified by irrecoverable wasted
effort) and from the accessibility live-region rule (polite vs assertive). Present it as reasoning.

### Progress indicators

| Source | Position |
|---|---|
| A | **Default off.** Cites a real service removing a 12-step indicator with no harm |
| B | **Use a step indicator** so users know where they are |

Same widget, same kind of flow, opposite defaults. A has the data; B has the intuition most people
share. This skill follows A and says why.

## What each method answers

The most common research mistake is not sample size. It is **running a method that answers a
different question than the one you have.**

| Method | The question it answers | The question it does NOT answer |
|---|---|---|
| **Question protocol** | Should this field exist at all? | Is the wording clear? |
| Reading a flow aloud | Does the sequence make sense? | Will people complete it? |
| **Qualitative usability testing** | Where does this break, and why? | How often, or how much better than the alternative |
| **Open card sort** | How do people group this, and what words do they use? | Can they find things in my structure? |
| **Closed card sort** | Does my structure match their mental model? | Same — still not findability |
| **Tree testing** | **Can a person find X in the structure I built?** | Why they failed |
| Quantitative A/B | Is A measurably better than B? | Why |
| Analytics | Where do people drop off? | Why they dropped |

**Card sorting is the most commonly misapplied.** It answers "how would you group these", which is a
generative question. If your problem is "our labels might be wrong", the test is **tree testing** —
give someone a task and a bare structure, see whether they land in the right place. It appears in
none of the major design-system sources, which is why it is easy to skip.

## Sample sizes, with the caveats the sources publish themselves

**Five users ≈ 85% of usability problems.** From a model built on 11 studies. The argument is
**return on investment**, not completeness — the fifth user finds less than the first, so a second
round of five on a revised design beats one round of ten.

**The caveats, published by the same source:**

- Holds for **qualitative, formative** testing aimed at *finding* problems
- **Quantitative work needs 30+**
- **Large-scale evaluations have found five participants surfacing as little as 35%** of problems on
  complex sites

So: **five is a defensible floor for "does this flow work". It is not an evidence standard**, and it
does not support a claim that a design is good.

**Card sorting: 15–30 participants**, ~50 cards maximum. 15 gives usable confidence; above 30 the
returns diminish. Stated limitations: if groupings do not converge, the analysis stalls and you have
nothing; and a large heterogeneous content estate blows past 50 cards, so you can only ever sample
it. *(This guidance is from an archived source last updated nine years ago — the only IA method
reachable. Treat the numbers as convention.)*

## The zero-participant floor

For teams with no recruitment capacity — which is most small teams, and the case the sources never
address:

1. **Audit every question against the protocol table.** Costs nothing, needs nobody, and kills more
   bad fields than any test.
2. **Read the flow aloud to one person who has never seen it.** Not a usability test — you are
   listening for where *you* stumble explaining it. The place you add a clarifying sentence out loud
   is the place the interface is missing one.
3. **Walk the failure paths.** Submit the form empty. Submit it with one bad field. Kill your network
   mid-step. Let the session expire. Come back after an hour. Four of these usually break.

That is a real evidence floor. It is far better than asserting a preference, and it is available on a
Tuesday afternoon with no budget.

## How to cite this in a decision

When writing up a design decision, say which of these it rests on:

- **"Evidenced"** — a study or real service data. Name it.
- **"Convention"** — established practice, well-tested by use, not by measurement. Say so; it is a
  legitimate basis.
- **"Reasoned"** — synthesis from adjacent evidence, like the validation-timing rule in this skill.
  Name the reasoning so someone can disagree with it.
- **"Preference"** — nothing behind it yet. Legitimate to hold, not legitimate to defend as though it
  were one of the other three.

Most design arguments are two people in different rows of that list, unaware of it.
