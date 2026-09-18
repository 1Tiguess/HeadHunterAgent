# Hunt notes — legally-required features of a digital product

**Framing.** The user's instruction was to research what Israeli and
international regulation requires *as product features*, and to fold that into
the skills rather than leave it out. That framing is the right one and it is
what makes this buildable: the deliverable is **an artefact checklist** — pages
that must exist, controls a user must be able to reach, disclosures that must
appear, mechanisms that must work — not a compliance opinion.

## Evidence quality — read this before using anything below

**Every regulator and government domain probed was blocked.** Not a subset:
`ada.gov`, `oag.ca.gov`, `cppa.ca.gov`, `ftc.gov`, `eur-lex.europa.eu`,
`ico.org.uk`, `legislation.gov.uk`, `cnil.fr`, `dataprotection.ie`, `etsi.org`,
`w3.org`, `w3c.github.io` (GitHub **Pages** is blocked even though `github.com`
is not), `gov.il` (all hosts), `fs.knesset.gov.il`, `sii.org.il`,
`kolzchut.org.il`, `aisrael.org`. Also `api.github.com` (403) and GitHub code
search (429, one-hour retry).

The entire primary-fetch surface was `github.com` HTML tree pages and
`raw.githubusercontent.com`. **Twelve sources were genuinely read.** Everything
else is `WebSearch` with `allowed_domains` pinned to the official domain — which
does return the regulator's own canonical URLs and an engine summary of the
official page, but is *not* reading the text.

**Consequence for the skill: every legal claim must carry its evidence class.**
Fetched-and-read, or search-extracted. They are not the same and must not be
presented as the same.

---

## Fetched and read (primary text)

### W3C per-jurisdiction accessibility policy dataset — `w3c/wai-policies-prototype`
The live source behind the W3C "Web Accessibility Laws & Policies" list. One
Markdown file per jurisdiction under `_policies/`, 45 jurisdictions, YAML front
matter carrying policy title, enactment date, `wcagver`, type, sector scope,
`webonly`, responsible ministries and linked documents. **Machine-readable,
jurisdiction-indexed, and fetchable** — the only such answer to "which WCAG
version does regime X actually reference."

- **Israel** (`_policies/israel.md`, read verbatim): *Equal Rights of Persons
  with Disabilities Act as amended*, 1998, `wcagver: WCAG 2.0`, scope
  **"Public sector, Private sector"**, `webonly: no`. Ministry of Justice +
  Commission for Equal Rights of Persons with Disabilities. A linked document is
  annotated "**WCAG 2.0 Level AA is required**". **`last_updated: 2017-04-04` —
  nine years stale.**
- **EU**: WAD 2016/2102 (public sector, WCAG 2.1, EN 301 549 incorporating WCAG
  2.1 AA verbatim for web content and WCAG 2.0 AA as interpreted by WCAG2ICT for
  non-web); EAA 2019/882, **"Public and private sectors"**, `wcagver: 2.2`,
  entry `last_updated: 2025-07-23` — current.
- **US**: Section 508 (WCAG 2.0); ADA (public + private, **no standard named**);
  **ADA Title II Rule 2024 — WCAG 2.1 AA, state and local government**; Section
  255; ACAA; CVAA.

**The unevenness is itself a finding.** Israel 2017 vs EU 2025 in the same
dataset. Anything built on it must surface `last_updated` rather than present
entries as current fact.

### W3C accessibility statement generator — `w3c/wai-statements`
Minimum content: commitment, the standard applied, contact for users who hit
problems. Recommended: known limitations, organisational measures, technical
prerequisites, tested environments, references to applicable law. It warns
explicitly that **the EU Directive's content requirements differ from this
generic best-practice set**.

Two craft rules worth lifting: describe barriers in **user-facing terms**, not
criterion numbers ("videos do not have captions", not "SC 1.2.2 was not met");
and link the statement from footer, help menu, sitemap and about page using a
**consistent link name** across web and mobile.

The limitations block is a repeating record with a fixed four-field shape —
**content part → the issue → why it occurs → what we are doing → what to do in
the meantime.** That shape is the reusable part.

### HMRC `accessibility-statement-frontend`
A production UK government service that renders every HMRC service's
legally-required statement **from a per-service YAML file**. The best worked
example anywhere of the mandated artefact treated as data.

Required: `serviceName`, `serviceDescription`, `serviceDomain`, `serviceUrl`,
`contactFrontendServiceId`, `complianceStatus` ∈ {full, partial, noncompliant},
`statementVisibility` ∈ {public, draft, archived}, `statementCreatedDate`,
`statementLastUpdatedDate`. Conditional: `serviceLastTestedDate` (required for
full/partial, omitted for noncompliant), `accessibilityProblems`, `milestones`
(description + target fix date).

Two design choices generalise: **statement scope is per service, not per
domain**, with an explicit disclaimer pointing at the parent site's statement;
and **milestones are first-class dated data**, so the statement doubles as a
remediation tracker and **goes stale visibly rather than silently**. Statements
are never deleted, only archived.

### WCAG conformance requirements — `w3c/wcag` `understanding/conformance.html`
Five requirements: satisfy all SC at the claimed level; **full pages only**, no
excluded parts; **complete processes** — every page in a multi-step flow must
conform; only accessibility-supported technologies relied upon; **non-
interference**, with four criteria applying regardless (audio control, no
keyboard trap, flashing, pause/stop/hide).

A conformance claim has a **fixed five-field shape: date, scope, level,
technologies relied upon, technologies used but not relied upon.**
"We are WCAG 2.2 AA compliant" is not a conformance claim. And under the
complete-processes rule, **a conformant checkout page inside a non-conformant
checkout flow claims nothing.**

### Global Privacy Control spec — `privacycg/gpc-spec`
Three surfaces: `Sec-GPC` request header, value exactly `1`, sent only when the
preference is on at navigation; `navigator.globalPrivacyControl`, read-only
boolean on `Navigator` and `WorkerNavigator`; and **`/.well-known/gpc.json`**
with optional `gpc` (boolean) and `lastUpdate` (RFC3339). Absent or invalid ⇒
"unknown". Intermediaries may not strip a valid header.

The spec is careful about its own legal reach: at least four US states have
identified GPC as a valid opt-out mechanism, it was designed around CCPA, and it
is "not necessarily intended to invoke every new privacy right in every
jurisdiction."

---

## Search-extracted (official domain pinned; page not read)

**EU accessibility.** Implementing Decision (EU) **2018/1523** establishes the
model accessibility statement: compliance status (fully/partially/non-compliant);
non-accessible content split into non-compliance, disproportionate burden, and
out-of-scope; preparation of the statement (date, method — self or third-party,
date of last review); **feedback mechanism with a description *and a link***,
usable both to report failures and to request excluded content; **enforcement
procedure with a description *and a link*** plus the enforcement body's contact,
for when the feedback response is unsatisfactory. The statement must itself be
accessible and, where appropriate, machine-readable.

**EAA 2019/882 Annex V.** Service providers must explain **how the service meets
the accessibility requirements**, publish it **in written and oral form and in a
form accessible to persons with disabilities**, and retain it for as long as the
service operates. **Microenterprise exemption for services: fewer than 10 people
*and* turnover or balance sheet ≤ €2m.** Covers e-commerce.

**GDPR.** Art 12: concise, transparent, intelligible, easily accessible, clear
plain language, **free of charge**; the controller must **facilitate** rights
exercise and respond **within one month**. Arts 33/34: notify the supervisory
authority **within 72 hours** where feasible with reasons if late; notify
individuals without undue delay where **high risk**, in clear and plain language.

**ePrivacy Art 5(3).** Storing or accessing information on terminal equipment
requires **consent after clear and comprehensive information about the
purposes**. Exempt: transmission-only, or **strictly necessary** for a service
the user explicitly requested. Users must have the opportunity to **refuse**.

**e-Commerce Directive Art 5** (the Impressum): identity, geographic address,
**an e-mail address allowing rapid, direct and effective contact**, trade
register + number, supervisory authority where applicable, professional rules
for regulated professions, **VAT number**.

**Consumer Rights Directive.** Art 8(2): the consumer must **explicitly
acknowledge that the order implies an obligation to pay**, and where a button is
used it must be **labelled legibly with only "order with obligation to pay" or
an equally unambiguous formulation**. Art 9: 14-day withdrawal. Annex I: model
withdrawal form (fields not retrieved).

**DSA** — *the weakest extraction in the hunt; re-verify before building.*
Art 14 T&Cs; Art 16 notice-and-action; Art 17 statement of reasons; Art 20
internal complaint handling, easy to access, user-friendly, timely,
non-discriminatory, diligent, non-arbitrary, **minimum six-month window** from
notification; Art 25 interface design / dark patterns; Art 26 ad transparency;
Art 27 recommender transparency, with VLOPs required to offer **at least one
recommender option not based on profiling**. Which duties apply depends on
whether you are a hosting service, a platform, a marketplace or a VLOP — four
different obligation sets.

**Regulation (EU) 2024/3228 — the ODR platform is dead.** Submissions ceased
20 March 2025, repeal effective **20 July 2025**, and references are to be
removed from the acts that required them. **The long-standing "link to the ODR
platform in your terms" artefact is now wrong.** Any template still requiring it
is out of date.

**AI Act Art 50.** A system designed to interact with people must **inform them
they are interacting with an AI**; generative output must be **marked as
AI-generated in machine-readable form**; deepfakes and public-interest text must
be **visibly labelled**; deployers of Annex III high-risk systems must inform
individuals subject to them.

**ADA Title II web rule** — *materially newer than training data.* Standard
WCAG 2.1 AA. An **Interim Final Rule published 20 April 2026 extended the
compliance dates**: population ≥50,000 → **26 April 2027**; <50,000 and special
districts → **26 April 2028**. **Verify against the IFR PDF before relying on
it.** Title II binds state and local government only; private-sector US web
accessibility runs on Title III case law with **no adopted technical standard**.

**CCPA/CPRA.** Notice at collection at or before the point of collection; a
clear and conspicuous **"Do Not Sell or Share My Personal Information"** link,
also in the privacy policy; a **"Limit the Use of My Sensitive Personal
Information"** route; honouring **opt-out preference signals** (GPC);
**45 days** to respond, extendable by 45 (90 total) with notice. Note the
September 2025 joint **CA/CO/CT investigative sweep into businesses refusing to
honour opt-outs** — the mechanism is being enforced on *whether it actually
works*, not whether the link exists.

**CAN-SPAM.** Three disclosures per commercial email: identification **as an
advertisement**, notice of the **opportunity to opt out**, and a **valid physical
postal address**. Opt-out live **≥30 days** after send, honoured within **10
business days**, no fee, no data beyond an email address, **no more than a single
web page**. After opt-out the address may not be sold or transferred.

---

## Israel — coherent, cross-corroborated, and entirely without primary text

Zero Israeli primary sources were reachable. What follows is `gov.il`-pinned
search extraction plus the one fetched W3C dataset entry, which corroborates the
sector scope independently.

- **Accessibility duty.** Websites and applications providing a public service
  or information about one must be made accessible under **Chapter 5, Part C of
  the Equal Rights for Persons with Disabilities (Service Accessibility
  Adjustments) Regulations, 5773-2013**, via **Israeli Standard 5568**, based on
  **WCAG 2.0 Level AA**. **The obligation reaches the private sector.**
- **Accessibility declaration (הצהרת נגישות).** Must be published on the site,
  detailing the arrangements made, **stating the extent of conformance to IS 5568
  Part 1 (web content) and Part 2 (digital documents)**, and including the
  **appointed accessibility coordinator's details** and a contact route for
  reporting problems. **The Commission issues no certification mark** — the model
  is self-declaration; and publishing a declaration confers no immunity.
- **Accessibility coordinator (רכז נגישות).** A body serving the public that
  **employs at least 25 people** must appoint one from among its employees and
  **publish the name, office location and contact routes**.
- **Privacy — Amendment 13**, in force **14 August 2025**. Abolished the general
  database-registration duty; replaced it with a **duty to notify the Privacy
  Protection Authority about large and sensitive databases**, including the
  **privacy protection officer's details, contact routes and appointment date**,
  with the **database definitions document** transmitted. Introduces a **"data of
  special sensitivity"** category driving sanction levels, the DPO trigger, and
  the notification trigger.
- **Duty to notify (חובת יידוע).** A request for personal data must be
  accompanied by notice of: whether there is a **legal obligation** to provide it
  or whether it depends on consent; **the purpose**; and **to whom it will be
  transferred**. Amendment 13 **extended this** to also require the
  **consequences of refusing**, and **that rights of access and correction
  exist**.
- **Spam — Communications Law s.30A.** An advertiser must indicate clearly and
  prominently that the message is advertising, with the word **"פרסומת" at the
  beginning of the message — and, for electronic messages, in the header**; must
  identify itself; and must give a **simple and reasonable refusal route** with a
  **valid email address** for the purpose.
- **Consumer — distance selling, s.14C.** Disclose trader name, ID number and
  address **in and outside Israel**, main characteristics, price, payment terms,
  and delivery timing and method. Cancellation **14 days** from the transaction,
  from receipt of the product, or from receipt of the s.14C(b) document —
  **whichever is later**.
- **Continuing transactions (עסקה מתמשכת).** The trader must **publish on its
  website the ways to cancel**, with address, telephone, fax and email. And
  **where the transaction can be performed on the website, the cancellation
  information must appear on the main page next to a link that performs the
  cancellation.** An explicit homepage-placement requirement for a cancellation
  control — no other regime in this hunt has one.

### Unresolved for Israel — do not guess these

- **Exemption thresholds.** An undue-burden exemption exists and turnover is a
  factor, with an application route to the Commission. **No numeric turnover
  threshold was sourced.** Figures circulate; none could be traced to a
  regulator.
- **The enumerated legal field list** of the Israeli accessibility declaration.
  Only the regulator's prose summary was reachable.
- **A statutory response deadline** for s.13 access and s.14 correction requests.
- **The statutory citation** for the homepage cancellation-link requirement.
- **IS 5568's WCAG version.** Direct conflict: `gov.il` sources and the
  **September 2023 republication of Parts 1 and 2** still describe it as
  **WCAG 2.0 AA**, while a low-quality GitHub result asserted "IS 5568:2020
  aligns with WCAG 2.1 AA". **The latter is a hobbyist pull request and was
  rejected as evidence.** Treat the version as open and lawyer-verifiable.

---

## The artefact list

### Pages and documents that must exist
| Artefact | Regime |
|---|---|
| Accessibility statement / declaration, published and linked | EU WAD + 2018/1523 (public); UK PSBAR 2018; **Israel — including private sector** |
| Information on how the service meets accessibility requirements, written *and oral*, itself accessible, retained for the life of the service | EU EAA Annex V (private services incl. e-commerce) |
| Legal notice / Impressum | EU e-Commerce Art 5 |
| Privacy notice — purposes, recipients, rights, how to exercise | GDPR 12–14; CCPA; Israel s.11 as extended |
| Cookie/tracking information — the basis consent is conditioned on | ePrivacy 5(3) |
| Terms and conditions with content requirements | DSA Art 14 |
| Notice at collection | CCPA |
| `/.well-known/gpc.json` | GPC spec; CCPA and peer states |
| Published accessibility coordinator name, office, contact | Israel, **≥25 employees** |

### Controls a user must be able to reach
Accessibility feedback route (report failures **and request excluded content**),
described and linked · escalation to the named enforcement body · DSR intake for
access/rectification/erasure/portability/objection, actively *facilitated* ·
consent withdrawal as easy as giving it · cookie **refusal** · honouring
`Sec-GPC: 1` · "Do Not Sell or Share" and "Limit the Use of My Sensitive
Personal Information" · order button labelled **only** "order with obligation to
pay" · 14-day withdrawal + model form · **cancellation link on the homepage**
(Israel, continuing transactions sold online) · email opt-out ≥30 days live, 10
business days to honour, ≤1 page · advertising refusal route with a valid email
(Israel s.30A) · DSA notice-and-action and a complaint system open ≥6 months ·
non-profiling recommender option (VLOPs).

### Disclosures that must appear
Compliance status as fully/partially/non-compliant plus enumerated
non-accessible content split by reason · the WCAG claim's five components ·
"this is an advertisement" + physical postal address (CAN-SPAM) / the literal
word **פרסומת** in the header (Israel) · pre-contract trader, characteristics,
price, payment, delivery · "you are interacting with an AI", machine-readable
marking of generative output, visible deepfake labelling, notice of Annex III
high-risk decisioning.

### Mechanisms that must work (process, not UI)
One month (GDPR) / 45 days extendable to 90 (CCPA) for DSRs, free of charge ·
72-hour breach notification with reasons if late, plus individual notice on high
risk · Israeli PPA notification for large and sensitive databases · DPO
appointment where triggered · statement review with a recorded last-review date,
assessment method and dated milestones.

### Actively delete if present
**The EU ODR platform link.**

---

## Legal-boundary flags — carried into the skill verbatim

1. Everything here is *what sources say a regime requires*. **None of it is
   advice about what any particular product must do.**
2. **Public vs private sector is the biggest fork in accessibility.** EU WAD
   binds public bodies; the EAA binds private services from 28 June 2025 with a
   microenterprise carve-out; **Israel has both sectors in scope.** A product
   with Israeli users can owe a mandatory declaration where the same product in
   the EU would not.
3. Whether an accessibility *statement* is legally mandatory for a **private**
   product is jurisdiction-specific and **not settled by anything found here**.
   The EAA's Annex V duty is "information on how the service meets the
   requirements" — not obviously the same artefact.
4. **IS 5568's version and Israel's exemption thresholds are unresolved.** Do not
   hard-code either.
5. **ADA Title II dates moved in April 2026**; most training data says 2026/2027.
6. **US private-sector web accessibility has no adopted technical standard.**
   That is a legal grey zone, not a spec gap.
7. **The DSA extraction is weak.** Re-verify at article level.
8. CCPA has applicability thresholds that were not extracted.
9. CAN-SPAM's commercial/transactional classification changes which rules apply.
10. **GPC's legal force varies by state** and the spec disclaims universality.
    Honouring it is not automatically a defence; not honouring it is
    demonstrably an enforcement target.
11. **Cookie-consent specifics — reject-all parity, banner design, consent
    lifetime, granularity — come from national DPA guidance, all unreachable.**
    Art 5(3) alone gives only "consent after clear and comprehensive information"
    plus the strictly-necessary exemption.
12. The **Digital Fairness Act** (COM(2025) 848, targeting dark patterns,
    addictive design, influencer practices and unfair personalisation) is a
    **proposal, not law**. Watch it; do not build to it.
13. **Sectoral regimes are entirely absent**: health, finance, payments
    (PSD2/SCA), children's services (COPPA, age-appropriate design), employment,
    telecoms, NIS2, DORA.
14. **The Israeli accessibility-widget convention is not law.** GitHub surfaced
    many "all-in-one accessibility" overlays marketed as IS 5568 compliance.
    **Nothing in any regulator source requires a widget.** The regulator requires
    conformance to the standard, the declaration, and the coordinator. Overlays
    are contested and can themselves introduce barriers. Market convention, not a
    legal artefact.

## Improvement openings

- **Nobody publishes the union schema.** The W3C generator and the EU model
  statement are different artefacts — the W3C page says so and then does not
  reconcile them. A field set satisfying WAD/2018/1523, the W3C best-practice
  set and Israel's declaration *at once* does not exist anywhere. **Closing that
  is the single most valuable thing here.**
- **Every statement artefact found is public-sector-shaped.** The EAA pushed
  private services into scope in June 2025 and Israel has had them in scope for
  years, yet every template, generator and schema is built for government.
- **Cancellation and deletion are under-specified in sources and heavily
  enforced.** The CA/CO/CT sweep targets opt-outs that don't work; Israel
  requires a homepage cancellation link; CAN-SPAM caps unsubscribe at one page.
  The cross-regime pattern is **parity and proximity — cancelling must be as
  reachable as signing up** — and no single source states it as a rule.
- **Dated-artefact risk is real and asymmetric.** The ODR link became wrong in
  July 2025; ADA Title II dates moved April 2026; Amendment 13 landed August
  2025. **Any artefact list needs an as-of date and a list of what is in
  motion.**

## Follow-up routes for a later hunt

Retry **GitHub code search** (rate-limited this run) for national transpositions
of the 2018/1523 model statement — Italy's `italia` org, Dutch and Nordic
government orgs are the likely carriers. And look for further government
accessibility-statement *services* in the `hmrc`/`alphagov` mould, since those
encode the legal field list as an executable schema and are reliably fetchable.

## Injection attempts

**None.** One source-quality rejection recorded: a GitHub-pinned search returned
an answer synthesised from hobbyist repositories and a single pull request
asserting "IS 5568:2020 aligns with WCAG 2.1 AA" and describing overlay widgets
as compliance. Not used as evidence. Commercial overlay-vendor repositories
surfaced in the same search were not mined.
