# The artefact tables

**As of 2026-09.** Every row carries its evidence class. **FETCHED** = primary text read.
**REPORTED** = domain-pinned search returned the regulator's canonical URL and a summary; the page
was not read.

## Contents
- [Pages and documents that must exist](#pages-and-documents-that-must-exist)
- [Controls a user must be able to reach](#controls-a-user-must-be-able-to-reach)
- [Disclosures that must appear](#disclosures-that-must-appear)
- [Mechanisms that must work](#mechanisms-that-must-work)
- [Delete if present](#delete-if-present)
- [What is moving](#what-is-moving)

## Pages and documents that must exist

| Artefact | Regime | Class |
|---|---|---|
| Accessibility statement / declaration, published and linked | EU WAD 2016/2102 + Impl. Dec. 2018/1523 (public sector) | REPORTED |
| " | UK PSBAR 2018 (per a production government service's own copy) | FETCHED |
| " | **Israel — including private sector** | REPORTED *(sector scope corroborated FETCHED)* |
| Information on **how the service meets accessibility requirements**, in **written and oral form**, itself accessible, **retained for the life of the service** | EU EAA 2019/882 Annex V — private services incl. e-commerce | REPORTED |
| Legal notice / Impressum | EU e-Commerce Directive 2000/31 Art 5 | REPORTED |
| Privacy notice — purposes, recipients, rights, how to exercise, clear plain language, **free of charge** | GDPR Arts 12–14 | REPORTED |
| " | CCPA privacy policy | REPORTED |
| " | Israel s.11 duty to notify, as extended by Amendment 13 | REPORTED |
| Cookie / tracking information — the *"clear and comprehensive information about the purposes"* consent is conditioned on | ePrivacy Art 5(3) | REPORTED |
| Terms and conditions with content requirements | DSA Art 14 | REPORTED *(weakest extraction — see boundaries flag 7)* |
| **Notice at collection**, at or before the point of collection | CCPA | REPORTED |
| **`/.well-known/gpc.json`** — optional `gpc` boolean, optional `lastUpdate` RFC3339; absent or invalid ⇒ "unknown" | GPC spec; recognised as an opt-out signal by CCPA and peer states | **FETCHED** |
| Published **accessibility coordinator** name, office and contact routes | Israel — bodies serving the public with **≥25 employees** | REPORTED |

## Controls a user must be able to reach

| Control | Regime | Class |
|---|---|---|
| **Accessibility feedback mechanism** — to report failures **and request excluded content** — with **a description *and* a link** | EU 2018/1523 | REPORTED |
| **Escalation route to the named enforcement body**, with a description, a link and the body's contact, for when the feedback response is unsatisfactory | EU 2018/1523 | REPORTED |
| " — in the UK, the equality commission, with dissatisfied complainants routed to the advisory service (or the NI equivalent) | UK PSBAR 2018 | FETCHED |
| **Data subject request intake** — access, rectification, erasure, portability, objection — which the controller must actively ***facilitate*** | GDPR Arts 12(2), 15–22 | REPORTED |
| **Consent withdrawal, as easy as giving consent** | GDPR Art 7(3) | REPORTED *(widely cited; article text not extracted directly)* |
| **Cookie refusal** — users must have the opportunity to refuse storage | ePrivacy Art 5(3) + recitals | REPORTED |
| **Honouring `Sec-GPC: 1`** and `navigator.globalPrivacyControl` as an opt-out | CCPA and peer state laws | **FETCHED** (spec) / REPORTED (legal effect) |
| **"Do Not Sell or Share My Personal Information"** link, clear and conspicuous, also in the privacy policy | CCPA/CPRA | REPORTED |
| **"Limit the Use of My Sensitive Personal Information"** route | CCPA/CPRA (right effective 1 Jan 2023) | REPORTED |
| Right-to-know / delete / correct request intake | CCPA/CPRA | REPORTED |
| **Order button labelled *only* "order with obligation to pay"** or an equally unambiguous formulation | EU CRD Art 8(2) | REPORTED |
| **14-day withdrawal** + the model withdrawal form | EU CRD Art 9 + Annex I | REPORTED *(Annex I field list not retrieved)* |
| **14-day cancellation, "whichever is later"** rule | Israel s.14C | REPORTED |
| **Cancellation link on the homepage**, next to the cancellation information, for continuing transactions sold online | Israel, consumer regulator guidance | REPORTED *(statutory citation unconfirmed)* |
| **Email opt-out** — live **≥30 days** after send, honoured within **10 business days**, no fee, no data beyond an email address, **no more than a single web page** | US CAN-SPAM | REPORTED |
| **Refusal route for advertising messages**, with a valid email address for the purpose | Israel Communications Law s.30A | REPORTED |
| **Notice-and-action intake** for illegal content | EU DSA Art 16 | REPORTED *(weak)* |
| **Internal complaint-handling system**, easy to access, user-friendly, timely, non-discriminatory, diligent, non-arbitrary, open **≥6 months** from notification | EU DSA Art 20 | REPORTED *(weak)* |
| **At least one recommender option not based on profiling** | EU DSA Art 27 (VLOPs/VLOSEs) | REPORTED *(weak)* |

## Disclosures that must appear

| Disclosure | Regime | Class |
|---|---|---|
| **Compliance status as fully / partially / non-compliant**, plus enumerated non-accessible content **split by reason** — non-compliance, disproportionate burden, out of scope | EU 2018/1523 | REPORTED |
| " mirrored as a three-value enum in a production government schema | UK | FETCHED |
| **The WCAG conformance claim's five components** — date, scope, level, technologies relied upon, technologies used but not relied upon | WCAG | **FETCHED** |
| **"This is an advertisement"** + a **valid physical postal address** in commercial email | CAN-SPAM | REPORTED |
| **The literal word "פרסומת"** at the start of the message and, for electronic messages, **in the header** | Israel s.30A | REPORTED |
| Pre-contract: trader identity and ID, address **in and outside Israel**, main characteristics, price, payment terms, delivery timing and method | Israel s.14C | REPORTED |
| " parallel obligation | EU CRD Art 6 | REPORTED |
| **"You are interacting with an AI"** | EU AI Act Art 50 | REPORTED |
| **Machine-readable marking of generative output** | EU AI Act Art 50 | REPORTED |
| **Visible labelling of deepfakes** and of text published to inform the public on matters of public interest | EU AI Act Art 50 | REPORTED |
| Notice to individuals subject to Annex III high-risk decisioning | EU AI Act Art 50 | REPORTED |
| Advertising transparency; recommender parameters | EU DSA Arts 26, 27 | REPORTED *(weak)* |

## Mechanisms that must work

Process rather than UI. **These are the ones enforcement actually tests**, because a link that
exists and does nothing is the pattern being pursued.

| Mechanism | Regime | Class |
|---|---|---|
| Respond to data subject requests **within one month**, **free of charge** | GDPR Art 12 | REPORTED |
| Respond **within 45 days, extendable by 45 (90 total) with notice** | CCPA | REPORTED |
| **Breach: notify the supervisory authority without undue delay and where feasible within 72 hours**, with reasons required if late | GDPR Art 33 | REPORTED |
| **Notify individuals without undue delay where the breach is high risk**, in clear and plain language, describing the nature of the breach | GDPR Art 34 | REPORTED |
| **Notify the Israeli PPA about large and sensitive databases**, including the privacy protection officer's details and appointment date; transmit the **database definitions document** | Israel Amendment 13 (in force 14 Aug 2025) | REPORTED |
| Appoint a DPO where the trigger is met | GDPR Art 37; Israel Amendment 13 | REPORTED |
| **Keep the accessibility statement reviewed**, with a recorded last-review date and an assessment method | EU 2018/1523 | REPORTED |
| " modelled as `statementLastUpdatedDate` + `serviceLastTestedDate` + **dated milestones** | UK production service | **FETCHED** |
| **Opt-outs must actually be honoured** — a Sept 2025 joint CA/CO/CT investigative sweep targeted businesses refusing to honour them | CCPA and peer states | REPORTED |

## Delete if present

| Artefact | Why | Class |
|---|---|---|
| **The EU ODR platform link** | Regulation (EU) 2024/3228 discontinued the platform — submissions ceased **20 March 2025**, repeal effective **20 July 2025** — and directs removal of references from the acts that required it | REPORTED |

**Any template, boilerplate or vendor checklist still requiring an ODR link is out of date.** This is
the clearest single illustration of why a compliance checklist without an as-of date is a liability.

## What is moving

**Recently changed — verify anything written before these dates:**

| When | What | Consequence |
|---|---|---|
| **28 Jun 2025** | EAA applies to private-sector services | Private products newly in scope, with a microenterprise carve-out |
| **20 Jul 2025** | ODR platform repealed | **Delete the link** |
| **14 Aug 2025** | Israel's Amendment 13 in force | Registration → notification; new DPO trigger; extended duty-to-notify content |
| **Sep 2025** | CA/CO/CT joint sweep announced | Enforcement focus on whether opt-outs *work* |
| **20 Apr 2026** | ADA Title II Interim Final Rule | Dates extended to **26 Apr 2027** (pop. ≥50,000) and **26 Apr 2028** (<50,000 and special districts) |

**In motion — watch, do not build to:**

- **The Digital Fairness Act** (COM(2025) 848, a **proposal**) — dark patterns, **addictive design**,
  influencer practices, unfair personalisation exploiting vulnerabilities
- EAA national enforcement practice, still settling
- US state privacy laws, still being added
- GPC's statutory recognition, expanding state by state

**The maintenance rule for this file:** if more than about six months have passed since **2026-09**,
re-verify every dated row before relying on it. Compliance checklists do not degrade gracefully —
individual entries become *wrong*, not merely incomplete, and a wrong entry is worse than a missing
one because it will be acted on.
