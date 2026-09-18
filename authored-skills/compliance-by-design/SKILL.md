---
name: compliance-by-design
description: Names the product features that regulation requires — pages that must exist, controls a user must be able to reach, disclosures that must appear, and mechanisms that must work — across EU, US and Israeli regimes, indexed by the feature you just built rather than by statute. Covers accessibility statements and WCAG conformance claims, privacy notices and data-subject request routes, cookie refusal, Do Not Sell and Global Privacy Control, obligation-to-pay ordering, cancellation parity, email opt-out, AI disclosure, and Israel's declaration, coordinator and homepage cancellation duties. Use when adding a cookie banner, signup, checkout, subscription, analytics, email marketing, an AI feature or a delete-account flow, or when asked what a page legally needs. States what sources say a regime requires; never asserts that a regime applies or that a product is compliant.
allowed-tools: Read, Write, Edit, Glob, Grep
---

# Compliance by design

## What this gives you, and what it does not

**This is an artefact checklist.** Pages that must exist. Controls a user must be able to reach.
Disclosures that must appear. Mechanisms that must work. Each paired with the regime that supplies
the basis.

**This is not a compliance opinion.** It never tells you whether a regime applies to you, never
asserts a product *is* compliant, and never substitutes for counsel.

The distinction is not decorative:

> *"The EU model accessibility statement requires a feedback mechanism with a description and a
> link"* is a fact about a document.
> *"You need an accessibility statement"* is a legal conclusion.

**This skill states the first kind and refuses the second.** Read `references/boundaries.md` before
relying on anything here — it lists fourteen boundary flags and the questions to escalate.

## Evidence classes — how to read every claim

Every regulator and government domain was blocked when this was built. **Twelve sources were read;
everything else is a domain-pinned search summary.** So each claim carries a class:

| Class | Meaning | Reads as |
|---|---|---|
| **FETCHED** | Primary text read | *"WCAG requires five components in a conformance claim"* |
| **REPORTED** | Regulator's canonical URL and a summary; **page not read** | *"the source reports that Art 8(2) requires…"* |

**Keep the classes distinct when you pass anything on.** A recollection presented as a citation is
the failure mode that matters here.

**FETCHED:** the W3C per-jurisdiction policy dataset · the W3C statement generator's field list ·
HMRC's production statement schema · WCAG conformance requirements · the GPC specification.

**REPORTED:** everything on GDPR, ePrivacy, the EAA, 2018/1523, e-Commerce, Consumer Rights, DSA,
the AI Act, ADA Title II, CCPA, CAN-SPAM — **and every Israeli item.**

**As of 2026-09.**

## 1. Triggered by what you just built

The primary working surface. Find what you added; read what it owes.

### You added a cookie, an analytics tag, or any non-essential storage

- **Information about the purposes, before consent.** REPORTED: ePrivacy Art 5(3) conditions consent
  on *"clear and comprehensive information about the purposes"*
- **A refusal path.** REPORTED: users must have the opportunity to **refuse** storage
- **`/.well-known/gpc.json`** if you honour Global Privacy Control — FETCHED: optional `gpc` boolean
  and `lastUpdate` RFC3339 date; absent or invalid means "unknown"
- **Honour `Sec-GPC: 1`** and `navigator.globalPrivacyControl` where you claim to

*Exempt from consent: storage solely to carry out transmission, or **strictly necessary** for a
service the user explicitly requested.*

**Not covered here:** reject-all parity, banner design, consent lifetime, granularity. Those come
from national DPA guidance, which was unreachable. See boundary flag 11.

### You added a signup or any personal-data collection

- **Notice at or before the point of collection.** REPORTED: CCPA, typically linked from the homepage
  and from any page where personal information is entered
- **Purposes, recipients, rights, and how to exercise them**, in clear plain language and **free of
  charge**. REPORTED: GDPR Arts 12–14
- **For Israel** — REPORTED, and note this is broader than the EU equivalent:
  - whether providing the data is a **legal obligation** or depends on consent
  - **the purpose**
  - **to whom it will be transferred**
  - **the consequences of refusing** *(added by Amendment 13)*
  - **that rights of access and correction exist** *(added by Amendment 13)*

### You added a paid subscription or checkout

- **An order button labelled with words meaning obligation to pay.** REPORTED: Consumer Rights
  Directive Art 8(2) requires the button be *"labelled legibly with only the words 'order with
  obligation to pay' or an equally unambiguous formulation"*. **"Complete purchase" is not that.**
- **14-day withdrawal** plus the model withdrawal form. REPORTED: CRD Art 9 + Annex I
- **Pre-contract disclosure** — trader identity, main characteristics, price, payment terms, delivery
  timing and method. REPORTED: Israel s.14C; parallel CRD Art 6
- **Israel's cancellation window runs from the transaction, from receipt of the product, or from
  receipt of the disclosure document — whichever is later.** REPORTED
- **For a continuing transaction sold online in Israel** — REPORTED, and unique among these regimes:
  cancellation information published on the site, **and the cancellation information must appear on
  the main page next to a link that performs the cancellation**

### You added email marketing

REPORTED throughout.

- **CAN-SPAM**, three disclosures per message: identification **as an advertisement** · notice of the
  **opportunity to opt out** · a **valid physical postal address**
- Opt-out mechanism live **≥30 days** after send · honoured within **10 business days** · no fee · no
  data beyond an email address · **no more than a single web page**
- After opt-out, the address may not be sold or transferred
- **Israel, Communications Law s.30A**: the word **פרסומת** ("advertisement") at the beginning of the
  message and, **for electronic messages, in the header** · the advertiser identifies itself · a
  simple and reasonable refusal route with **a valid email address for that purpose**

### You added an AI feature

REPORTED: AI Act Art 50.

- A system designed to interact with people must **inform them they are interacting with an AI**
- Generative output must be **marked as AI-generated in machine-readable form**
- **Deepfakes and text published to inform the public on matters of public interest** must be
  **visibly labelled**
- Deployers of Annex III high-risk systems making or assisting decisions about individuals must
  **inform those individuals**

### You shipped a user interface at all

- **An accessibility statement** where one is owed — see §3
- **A legal notice / Impressum** in the EU. REPORTED: e-Commerce Directive Art 5 — identity,
  geographic address, **an e-mail address allowing rapid, direct and effective contact**, trade
  register and number, supervisory authority where applicable, professional rules for regulated
  professions, **VAT number**
- **For Israel**: the accessibility declaration, and the published **accessibility coordinator**
  where the body serving the public employs **≥25 people**

### You added a delete-account or unsubscribe flow

See §2 — this is where parity and proximity applies, and where enforcement is currently focused.

## 2. Parity and proximity

**The cross-regime rule that the sources imply and none of them states.**

> **The exit must be as reachable as the entrance.**

Three regimes converge on it from different directions:

- **Enforcement follows the mechanism, not the link.** REPORTED: a September 2025 joint CA/CO/CT
  investigative sweep specifically targeted businesses **refusing to honour opt-out requests** — i.e.
  whether the control *works*, not whether it exists
- **Israel** requires a **cancellation link on the homepage** for continuing transactions sold online
- **CAN-SPAM** caps unsubscribe at **a single web page**, and forbids demanding data beyond an email
  address

Applied:

| If signing up is… | Then cancelling must be… |
|---|---|
| One click | Not four emails |
| A button | A button of comparable weight |
| Self-service | Self-service |
| Instant | Not "within 30 days" |
| On the homepage | Reachable from the homepage |

**A "Do Not Sell or Share My Personal Information" link that does not stop the sale is the failure
being enforced against.** The link is the easy part; wiring it to something is the requirement.

## 3. The accessibility conformance claim

FETCHED — and this section corrects a near-universal error.

> **"We are WCAG 2.2 AA compliant" is not a conformance claim.**

A conformance claim has **five components**:

1. **Date**
2. **Scope** — which pages or URLs
3. **Level** — A, AA or AAA
4. **Technologies relied upon**
5. **Technologies used but not relied upon**

And two rules that invalidate most informal claims:

- **Full pages only.** Conformance cannot be claimed with parts excluded.
- **Complete processes.** Every page in a multi-step flow must conform. **A conformant checkout page
  inside a non-conformant checkout flow claims nothing.**

Also FETCHED: only accessibility-supported ways of using technologies may be relied upon; and
**non-interference** — non-conforming technology must not block the rest of the page, with four
criteria applying regardless (audio control, no keyboard trap, flashing, pause/stop/hide).

A **statement of partial conformance** is the defined route for uncontrolled third-party content.

### Which version applies where

FETCHED, from the W3C per-jurisdiction dataset:

| Regime | Standard | Sector |
|---|---|---|
| EU Web Accessibility Directive | WCAG 2.1 via EN 301 549 | Public sector |
| **EU Accessibility Act** | WCAG 2.2 | **Public and private** |
| ADA Title II rule (2024) | WCAG 2.1 AA | US state and local government |
| Section 508 | WCAG 2.0 | US federal |
| ADA (general) | **no standard named** | Public and private |
| **Israel** | **WCAG 2.0 AA via IS 5568** | **Public sector, Private sector** |

**The dataset is unevenly maintained and you should surface that rather than hide it.** Its Israel
entry was last updated **2017-04-04**; its EU entry **2025-07-23**. Nine years apart, in the same
file.

## 4. The statement, as data

The best structural model available is a **production government service that renders every statement
from a per-service YAML file** (FETCHED). Two of its design choices generalise:

- **Statement scope is per service, not per domain**, with an explicit disclaimer pointing at the
  parent site's own statement
- **Milestones are first-class dated data** — description plus target fix date — so the statement
  doubles as a remediation tracker and **goes stale visibly rather than silently**

Statements are **never deleted, only archived.**

### The union schema

**Nobody publishes this.** The W3C generator and the EU model statement are different artefacts — the
W3C page says so and then does not reconcile them. This field set is built to satisfy the EU model,
the W3C best-practice set, and Israel's declaration **at once**. Full field list with types and
conditionality in `references/statement-schema.md`.

Core:

```yaml
serviceName, serviceDescription, serviceUrl
complianceStatus:      full | partial | noncompliant
standard:              e.g. "WCAG 2.2 AA"
statementCreatedDate, statementLastUpdatedDate
serviceLastTestedDate          # required for full/partial, omitted for noncompliant
assessmentMethod:      self | third-party
nonAccessibleContent:          # the EU three-way split
  - reason: non-compliance | disproportionate-burden | out-of-scope
    contentPart, issue, whyItOccurs, whatWeAreDoing, whatToDoMeanwhile
milestones:            [{ description, targetDate }]
feedback:              { description, link, contact, typicalResponseTime }
enforcement:           { description, link, bodyContact }
approver:              { name, function }
complaintsProcedure
# Israel adds:
is5568Part1Conformance, is5568Part2Conformance
accessibilityCoordinator: { name, office, contactRoutes }
```

**The limitation record's five-field shape** — content part → the issue → why it occurs → what we are
doing → what to do in the meantime — is the reusable part, and it comes from the W3C generator
(FETCHED).

**Craft rules, also FETCHED:**

- **Describe barriers in user-facing terms, not criterion numbers.** *"Videos do not have captions"*,
  not *"SC 1.2.2 was not met"*
- **Link the statement from several places** — footer, help menu, sitemap, about page — with a
  **consistent link name** across web and mobile

**Every template, generator and schema found is public-sector-shaped**, yet the EAA pushed private
services into scope in June 2025 and **Israel has had the private sector in scope for years.** The
schema above is the private-product-shaped version.

## 5. Israel

**Every Israeli claim in this skill is REPORTED. Zero Israeli primary text was reachable** — not
`gov.il`, not the Knesset, not the standards institute. The picture below is coherent and
cross-corroborated on its main points, and it is not a reading of the law.

- **Accessibility duty reaches the private sector.** Corroborated independently by the FETCHED W3C
  dataset recording scope as *"Public sector, Private sector"*
- **Accessibility declaration** must state the **extent of conformance to IS 5568 Part 1 (web
  content) and Part 2 (digital documents) separately**, include the **accessibility coordinator's
  details**, and give a contact route for reporting problems
- **No certification mark exists.** The model is self-declaration — and publishing a declaration
  confers no immunity
- **Accessibility coordinator** required where a body serving the public employs **≥25 people**, with
  the name, office location and contact routes **published**
- **Privacy Amendment 13**, in force **14 August 2025**: abolished general database registration;
  replaced it with a **duty to notify the Privacy Protection Authority about large and sensitive
  databases**, including the privacy protection officer's details and appointment date
- **Duty to notify** — see §1, signup
- **s.30A spam** and **s.14C distance selling** — see §1
- **Continuing transactions: the homepage cancellation link** — see §1

**Five things are unresolved and must not be guessed.** Exemption thresholds · the declaration's
enumerated legal field list · s.13/s.14 response deadlines · the statutory citation for the homepage
cancellation link · **IS 5568's WCAG version**. Details in `references/israel.md`.

## 6. Delete if present

> **The EU ODR platform link.**

REPORTED: Regulation (EU) 2024/3228 discontinued the platform — complaint submission ceased **20
March 2025**, repeal effective **20 July 2025** — and directs removal of references from the acts
that required them.

**The long-standing "link to the ODR platform in your terms" artefact is now wrong.** Any template,
boilerplate or checklist still requiring it is out of date. This is the clearest illustration of why
a compliance checklist needs an as-of date.

## 7. As of, and what is moving

**This skill is as of 2026-09.** Dated-artefact risk here is real and asymmetric — things become
*wrong*, not merely incomplete.

**Recently changed:**

| When | What |
|---|---|
| Jun 2025 | EAA applies to private-sector services |
| Jul 2025 | **ODR platform repealed** — delete the link |
| Aug 2025 | Israel's Amendment 13 in force |
| Apr 2026 | **ADA Title II dates extended to 2027/2028** |

**In motion, do not build to it:**

- **The Digital Fairness Act** (proposal) — dark patterns, addictive design, influencer practices,
  unfair personalisation
- EAA national enforcement practice, still settling
- US state privacy laws, still being added
- GPC's recognition, expanding state by state

**If more than about six months have passed since 2026-09, re-verify before relying on any dated
item here.**

## Review checklist

- [ ] Cookie or analytics addition produces a **refusal path**, not just a banner
- [ ] "Do Not Sell or Share" is wired to something that actually stops the sale
- [ ] `Sec-GPC: 1` honoured where claimed; `/.well-known/gpc.json` reflects reality
- [ ] A paid flow's confirm button carries obligation-to-pay wording
- [ ] **Cancellation is as reachable as signup** — and on the homepage where Israel requires it
- [ ] Marketing email carries all three CAN-SPAM disclosures, and the Hebrew header word where relevant
- [ ] An AI feature discloses itself and marks generative output
- [ ] Any accessibility claim carries **all five components**, or is not made
- [ ] **No ODR platform link anywhere**
- [ ] Every legal statement passed on is marked **FETCHED** or **REPORTED**
- [ ] **Applicability questions were escalated, not answered**
- [ ] The as-of date is stated wherever this list is reproduced

## References

- `references/artefacts.md` — the four tables in full, every row with regime, basis and evidence class
- `references/reverse-index.md` — feature → artefacts owed, expanded
- `references/israel.md` — the Israeli picture, **with the unresolved list given equal prominence**
- `references/statement-schema.md` — the union schema, field by field
- `references/boundaries.md` — **read first**; the fourteen flags and what to escalate
