# Reverse index: feature → artefacts owed

**As of 2026-09.** The primary working surface — find what you just built, read what it owes.

**FETCHED** = primary text read. **REPORTED** = domain-pinned search summary; page not read.
**Nothing here says a regime applies to you.** See `boundaries.md`.

## Contents
- [Cookies, analytics, any non-essential storage](#cookies-analytics-any-non-essential-storage)
- [Signup or any personal-data collection](#signup-or-any-personal-data-collection)
- [Login and accounts](#login-and-accounts)
- [Checkout, one-off purchase](#checkout-one-off-purchase)
- [Subscription or recurring billing](#subscription-or-recurring-billing)
- [Email or SMS marketing](#email-or-sms-marketing)
- [An AI feature](#an-ai-feature)
- [User-generated content or a marketplace](#user-generated-content-or-a-marketplace)
- [A recommender or personalised feed](#a-recommender-or-personalised-feed)
- [Delete account or data export](#delete-account-or-data-export)
- [Shipping any user interface](#shipping-any-user-interface)
- [Selling or sharing data with third parties](#selling-or-sharing-data-with-third-parties)

## Cookies, analytics, any non-essential storage

| Owed | Basis | Class |
|---|---|---|
| Information about **the purposes**, before consent | ePrivacy Art 5(3) | REPORTED |
| **A refusal path** — the opportunity to refuse storage | ePrivacy Art 5(3) + recitals | REPORTED |
| A cookie/tracking policy covering the above | ePrivacy | REPORTED |
| `/.well-known/gpc.json` if you honour GPC | GPC spec | **FETCHED** |
| Honour `Sec-GPC: 1` and `navigator.globalPrivacyControl` where you claim to | CCPA, peer states | FETCHED (spec) |

**Exempt from consent:** storage solely to carry out transmission, or **strictly necessary** for a
service the user explicitly requested. Analytics is not strictly necessary.

**Not answerable from here:** reject-all parity, banner design, consent lifetime, granularity. All
from national DPA guidance, unreachable. **Counsel question.**

## Signup or any personal-data collection

| Owed | Basis | Class |
|---|---|---|
| **Notice at or before the point of collection** | CCPA | REPORTED |
| Purposes, recipients, rights, how to exercise — clear plain language, **free of charge** | GDPR Arts 12–14 | REPORTED |
| A route to exercise access, rectification, erasure, portability, objection — **actively facilitated** | GDPR Arts 12(2), 15–22 | REPORTED |
| **Israel, five items:** legal obligation vs consent · the purpose · to whom it is transferred · **the consequences of refusing** · **that access and correction rights exist** | Israel s.11, extended by Amendment 13 | REPORTED |

**The last two Israeli items postdate most privacy-notice boilerplate** (Amendment 13, in force 14
Aug 2025) and are the ones most likely to be missing.

## Login and accounts

No artefact requirements specific to authentication in the regimes covered here — but two adjacent
ones bite:

- **No CAPTCHAs or cognitive puzzles without an accessible alternative** — WCAG 2.2. See the
  `ux-journey-design` skill, which treats accounts as a cost to be justified
- **Never a national ID number as an identity check** — a design convention with obvious privacy
  consequences

For the security of the mechanism itself, see the `application-security` skill.

## Checkout, one-off purchase

| Owed | Basis | Class |
|---|---|---|
| **Order button labelled *only* with words meaning obligation to pay** | EU CRD Art 8(2) | REPORTED |
| Pre-contract disclosure: identity, main characteristics, price, payment terms, delivery timing and method | EU CRD Art 6 | REPORTED |
| **Israel:** trader name, **ID number**, address **in and outside Israel**, characteristics, price, payment terms, delivery | Israel s.14C | REPORTED |
| **14-day withdrawal** + model withdrawal form | EU CRD Art 9 + Annex I | REPORTED |
| **Israel: 14 days from the transaction, from receipt, or from receipt of the disclosure document — whichever is later** | Israel s.14C | REPORTED |
| Legal notice / Impressum reachable | e-Commerce Art 5 | REPORTED |
| **No ODR platform link** | Reg. 2024/3228 | REPORTED |

**The button label is the most commonly wrong item on this page.** "Complete purchase", "Place
order", "Confirm" — the requirement as reported is *"order with obligation to pay"* or an equally
unambiguous formulation, and "equally unambiguous" is doing specific work: the words must convey
payment obligation, not merely finality.

## Subscription or recurring billing

Everything from checkout, plus:

| Owed | Basis | Class |
|---|---|---|
| **Israel:** publish on the site **the ways to cancel**, with address, telephone, fax and email | Israel, continuing transactions | REPORTED |
| Accept cancellation by **telephone, fax, email, in person, or registered mail** | " | REPORTED |
| Stop supply and charging **from the date the consumer specifies** | " | REPORTED |
| **Where the transaction can be performed on the website: cancellation information on the main page, next to a link that performs the cancellation** | " | REPORTED *(statutory citation unconfirmed)* |

**And the cross-regime rule: parity and proximity.** The exit must be as reachable as the entrance.
See the SKILL body §2.

## Email or SMS marketing

| Owed | Basis | Class |
|---|---|---|
| Clear and conspicuous **identification as an advertisement** | CAN-SPAM | REPORTED |
| Clear and conspicuous **notice of the opportunity to opt out** | CAN-SPAM | REPORTED |
| A **valid physical postal address** | CAN-SPAM | REPORTED |
| Opt-out mechanism live **≥30 days** after send | CAN-SPAM | REPORTED |
| Requests honoured within **10 business days** | CAN-SPAM | REPORTED |
| **No fee, no data beyond an email address, no more than a single web page** | CAN-SPAM | REPORTED |
| After opt-out, **do not sell or transfer the address** | CAN-SPAM | REPORTED |
| **Israel:** the word **פרסומת** at the beginning **and, for electronic messages, in the header** | s.30A | REPORTED |
| **Israel:** the advertiser identifies itself | s.30A | REPORTED |
| **Israel:** a simple and reasonable refusal route, with **a valid email address for that purpose** | s.30A | REPORTED |

**The "single web page" cap is the one most often breached** by unsubscribe flows that ask for a
reason, offer alternatives, then require a login.

**Commercial vs transactional classification changes which rules apply** — see boundaries flag 9.

## An AI feature

| Owed | Basis | Class |
|---|---|---|
| **Inform people they are interacting with an AI**, where the system is designed to interact with them | AI Act Art 50 | REPORTED |
| **Mark generative output as AI-generated in machine-readable form** | AI Act Art 50 | REPORTED |
| **Visibly label deepfakes**, and text published to inform the public on matters of public interest | AI Act Art 50 | REPORTED |
| Inform individuals subject to Annex III high-risk decisioning | AI Act Art 50 | REPORTED |

**Machine-readable and visible are two separate obligations** covering different output types, and a
watermark in the pixels does not discharge the machine-readable one.

## User-generated content or a marketplace

**All REPORTED, and this is the weakest extraction in the skill** — see boundaries flag 7. Re-verify
at article level before building.

| Owed | Basis |
|---|---|
| Terms and conditions with content requirements | DSA Art 14 |
| **Notice-and-action mechanism** for any person to report illegal content | DSA Art 16 |
| **Statement of reasons** for restriction decisions | DSA Art 17 |
| **Internal complaint-handling system** — easy to access, user-friendly, facilitating sufficiently precise complaints, handled in a timely, non-discriminatory, diligent and non-arbitrary manner, open **≥6 months** from notification of the decision | DSA Art 20 |
| Interface design constraints (dark patterns) | DSA Art 25 |
| Advertising transparency | DSA Art 26 |

**Which duties apply depends on whether you are a hosting service, an online platform, a marketplace
or a VLOP — four different obligation sets.** That determination is a counsel question.

## A recommender or personalised feed

| Owed | Basis | Class |
|---|---|---|
| Recommender system transparency — the main parameters | DSA Art 27 | REPORTED *(weak)* |
| **At least one option not based on profiling** | DSA Art 27, VLOPs/VLOSEs | REPORTED *(weak)* |

**Watch:** the Digital Fairness Act proposal targets addictive design and unfair personalisation
exploiting vulnerabilities. **A proposal, not law.**

## Delete account or data export

| Owed | Basis | Class |
|---|---|---|
| Erasure without undue delay | GDPR Art 17 | REPORTED |
| Portability — the data in a usable form | GDPR Art 20 | REPORTED |
| Respond **within one month**, free of charge | GDPR Art 12 | REPORTED |
| Respond **within 45 days, extendable to 90 with notice** | CCPA | REPORTED |
| Right-to-delete intake | CCPA/CPRA | REPORTED |
| **Israel:** access under s.13, correction under s.14 | Israel | REPORTED *(no confirmed deadline)* |

**Parity and proximity applies hardest here.** The enforcement pattern is against controls that
exist and do not work.

## Shipping any user interface

| Owed | Basis | Class |
|---|---|---|
| Accessibility statement where one is owed | EU WAD / UK PSBAR / **Israel incl. private sector** | REPORTED (FETCHED for the UK schema and the Israeli sector scope) |
| Information on how the service meets accessibility requirements, **written and oral**, itself accessible, retained for the life of the service | EAA Annex V | REPORTED |
| A conformance claim with **all five components**, or no claim at all | WCAG | **FETCHED** |
| Legal notice / Impressum | e-Commerce Art 5 | REPORTED |
| **Israel:** the declaration, stating conformance to **IS 5568 Part 1 and Part 2 separately**, the coordinator's details, and a reporting contact | Israel | REPORTED |
| **Israel:** published accessibility coordinator where the body employs **≥25 people** | Israel | REPORTED |

**Remember the complete-processes rule:** a conformant page inside a non-conformant flow claims
nothing. Scope your claim to complete journeys, not to individual screens.

## Selling or sharing data with third parties

| Owed | Basis | Class |
|---|---|---|
| **"Do Not Sell or Share My Personal Information"** link, clear and conspicuous, **also in the privacy policy** | CCPA/CPRA | REPORTED |
| **"Limit the Use of My Sensitive Personal Information"** route, also in the privacy policy | CCPA/CPRA | REPORTED |
| Honour **opt-out preference signals** (GPC) | CCPA and peer states | REPORTED |
| Disclose recipients in the privacy notice | GDPR Arts 13–14 | REPORTED |
| **Israel:** disclose to whom data will be transferred, at collection | Israel s.11 | REPORTED |

**The link is the easy part. Wiring it to something that actually stops the sale is the
requirement**, and it is what the September 2025 joint CA/CO/CT sweep pursued.

**CCPA has applicability thresholds** — revenue, consumer volume, share of revenue from selling data
— **that were not extracted.** Whether you are a covered "business" is a counsel question.
