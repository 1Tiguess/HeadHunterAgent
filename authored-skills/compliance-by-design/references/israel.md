# Israel

**As of 2026-09.**

> **Every claim in this file is REPORTED. Zero Israeli primary text was reachable.**
>
> `gov.il` (all hosts), `fs.knesset.gov.il`, `sii.org.il` (the IS 5568 standard PDFs),
> `kolzchut.org.il` and `aisrael.org` were all blocked. The Service Accessibility Regulations,
> IS 5568 Parts 1 and 2, the Privacy Protection Law, Amendment 13, and the Consumer Protection Law
> were **never read**.
>
> The picture below is coherent and cross-corroborated on its main points. It is not a reading of
> the law.

**The one independent corroboration:** the W3C per-jurisdiction dataset entry for Israel was FETCHED
and records `scope: "Public sector, Private sector"`, `wcagver: WCAG 2.0`, with a linked document
annotated *"WCAG 2.0 Level AA is required"*. That confirms the sector scope and the standard from a
second source. **It also carries `last_updated: 2017-04-04`** — nine years stale, against the same
dataset's EU entry at 2025-07-23.

## Contents
- [Why Israel matters disproportionately](#why-israel-matters-disproportionately)
- [Accessibility](#accessibility)
- [Privacy](#privacy)
- [Marketing messages](#marketing-messages)
- [Consumer](#consumer)
- [The unresolved list](#the-unresolved-list)
- [The widget question](#the-widget-question)
- [A follow-up route](#a-follow-up-route)

## Why Israel matters disproportionately

**Israel is the outlier in this whole skill, and the reason is one word: private.**

The EU Web Accessibility Directive binds public bodies. The European Accessibility Act reached
private services only in June 2025, with a microenterprise carve-out. US Title II binds state and
local government, and private-sector US web accessibility has **no adopted technical standard** at
all.

**Israel has had both sectors in scope for years.** So a product with Israeli users can owe a
mandatory accessibility declaration, a named coordinator, and a homepage cancellation link where the
same product in the EU or US would owe none of them.

It is also the jurisdiction with the **least reachable primary material**, which is an uncomfortable
combination and the reason this file is structured around what is *not* known as much as what is.

## Accessibility

**The duty.** Accessibility adjustments are required for websites and applications that provide a
public service or information about one, under **Chapter 5, Part C of the Equal Rights for Persons
with Disabilities (Service Accessibility Adjustments) Regulations, 5773-2013**, implemented via
**Israeli Standard 5568**, described as based on **WCAG 2.0 Level AA**.

**The obligation reaches the private sector.** *(Corroborated by the FETCHED W3C dataset.)*

**The declaration (הצהרת נגישות).** Published on the site, detailing the accessibility arrangements
made, and:

- **stating the extent to which the service meets IS 5568 Part 1 (web content) and Part 2 (digital
  documents)** — note these are reported **separately**, which no other regime here requires
- including the **details of the appointed accessibility coordinator**
- including **contact information for reporting accessibility problems**

Two further points from the same sources, both worth carrying:

- **The Commission issues no certification mark.** The model is **self-declaration against the
  standard.** There is nobody to certify you and no badge to display.
- **Publishing a declaration does not immunise you.** The Commission or a third party can still test
  the site and litigate.

**The coordinator (רכז נגישות).** A body providing a service to the public that **employs at least
25 people** must appoint an accessibility coordinator **from among its employees**, and the obligated
body must **publish to the public** the coordinator's **name, office location and contact routes**.
Reported statutory basis: section 19מב of the Equal Rights Law, 5758-1998.

**Standard currency.** **IS 5568 Parts 1 and 2 were republished in September 2023**, and the same
sources still describe the standard as based on **WCAG 2.0 at level AA**. See the unresolved list.

## Privacy

**Amendment 13 to the Privacy Protection Law, 5784-2024 — in force 14 August 2025.**

This is recent enough that most training data predates it, and it changed the shape of the regime:

- **Abolished the general database-registration duty**, leaving registration only for specific
  database types named in the law
- **Replaced it with a duty to notify the Privacy Protection Authority about large and sensitive
  databases.** The notification must include **the privacy protection officer's details, contact
  routes and appointment date** where such an officer exists, and a copy of the **database
  definitions document** required under the Data Security Regulations must be transmitted
- Databases registered before the amendment **stay on the register** unless the controller notifies
  the Authority that no registration duty applies
- Introduced a **"data of special sensitivity"** category, which drives financial sanction levels,
  the **DPO appointment trigger**, and the large/sensitive-database notification trigger

**The duty to notify (חובת יידוע) — section 11.** A request to a person for personal data for
processing in a database must be accompanied by notice of:

1. whether there is a **legal obligation** to provide the data, or whether provision depends on
   consent
2. **the purpose** of the use
3. **to whom the data will be transferred**

**Amendment 13 extended this** to also require telling the person:

4. **the consequences of refusing** to provide the data
5. **that rights of access and correction exist** — access under section 13, correction under section
   14

**Points 4 and 5 are the newest and the most likely to be missing from an existing product**, since
they postdate most privacy-notice boilerplate.

## Marketing messages

**Communications (Telecommunications and Broadcasts) Law, section 30A.** An advertiser sending
advertising material must:

- indicate **clearly and prominently** that it is advertising, with **the word "פרסומת" at the
  beginning of the message** — and, **for electronic messages, in the message header**
- **identify itself**
- give a **simple and reasonable way to send a refusal notice**, with a **valid email address**
  provided for that purpose where the message is electronic

Reported penalties: up to **₪202,000** for breaches of 30A(b)/(c) and up to **₪67,300** for 30A(e),
plus civil and class-action exposure.

**The header requirement is the distinctive one.** No other regime here requires a specific literal
word in a specific position. CAN-SPAM requires identification as an advertisement but does not
prescribe the word or its placement.

## Consumer

**Distance selling, section 14C.** The trader must disclose:

- **the trader's name, ID number, and address in and outside Israel**
- the **main characteristics** of the product or service
- the **price**
- the **payment terms**
- the **timing and method of delivery**

**Cancellation runs 14 days** from the transaction, from receipt of the product, or **from receipt of
the document containing the s.14C(b) information — whichever is later.** No reason need be given.

**The "whichever is later" rule is the trap.** A trader who never sends the disclosure document has
not started the clock, so the cancellation window does not close.

**Continuing transactions (עסקה מתמשכת).** The trader must **publish on its website the ways to
cancel**, together with address, telephone, fax and email for the disconnection notice. Cancellation
must be accepted by **telephone, fax, email, in person at the business, or registered mail**, and
supply and charging must stop from the date the consumer specifies.

And the requirement with no equivalent anywhere else in this skill:

> **Where the transaction can also be performed on the website, the cancellation information must
> appear on the main page next to a link that performs the cancellation.**

**An explicit homepage-placement requirement for a cancellation control.** This is the strongest
single instance of the parity-and-proximity pattern, and it is the one most likely to be missed by a
product built for another market.

## The unresolved list

**Given equal prominence deliberately. Do not guess any of these.**

### 1. Exemption thresholds

An **undue burden exemption exists**, turnover is one of the factors, and there is an application
route to the Commission for exemption.

**No numeric turnover threshold below which a website is exempt could be sourced.** Several such
figures circulate in secondary material; **none could be traced to a regulator.**

**Do not hard-code a turnover number.** If a client wants to rely on an exemption, that is a counsel
question with an application attached, not a threshold lookup.

### 2. The declaration's enumerated legal field list

What exists here is the **regulator's prose summary** — extent of conformance to Parts 1 and 2,
coordinator details, contact for reports. **Not an enumerated legal field list** comparable to the
EU model statement's Annex.

The union schema in `references/statement-schema.md` covers these three items as fields, but it is
built from the EU and W3C structures with the Israeli items added. **It is not a transcription of an
Israeli legal requirement**, because no such text was reachable.

### 3. A statutory response deadline for access and correction

Section 13 (access) and section 14 (correction) rights exist and must now be disclosed at collection.
**No statutory response deadline could be confirmed from a government source.**

Do not assume the GDPR one-month or the CCPA 45-day figure transfers.

### 4. The statutory citation for the homepage cancellation link

The requirement is stated in consumer-regulator guidance. **The underlying statutory provision and
amendment number could not be identified.** The requirement is well-corroborated as *guidance*; its
citation is not.

### 5. IS 5568's WCAG version — a direct conflict

| Source | Claim |
|---|---|
| `gov.il` sources, and the **September 2023 republication** of Parts 1 and 2 | **WCAG 2.0 AA** |
| The FETCHED W3C dataset entry (last updated **2017**) | **WCAG 2.0** |
| A GitHub search result | "IS 5568:2020 aligns with **WCAG 2.1 AA**" |

**The third was rejected as evidence.** Its provenance was a **hobbyist pull request** on an
unrelated repository, in a search whose other results were commercial accessibility-overlay vendors.

**Treat the version question as open and lawyer-verifiable.** Do not hard-code a WCAG version for
Israel. If you need to pick one for a build, **building to WCAG 2.1 AA or 2.2 AA satisfies 2.0 AA**,
so building higher is the safe direction — but *claiming* a version is a different act from building
to one, and the claim is what needs verifying.

## The widget question

GitHub searches for IS 5568 surface a large number of **"all-in-one accessibility" overlay widgets**
marketed as Israeli accessibility compliance. Several commercial vendor repositories appeared in the
same searches.

> **Nothing in any regulator source found requires a widget.**

What the regulator requires is: **conformance to the standard**, **the declaration**, and **the
coordinator**. A widget is none of those three.

Overlays are **contested in the accessibility field** and **can themselves introduce barriers** — by
interfering with assistive technology the user already has configured.

**Treat "install a widget" as market convention, not a legal artefact.** If a client has one, it does
not discharge the duty; if they do not, its absence is not a finding.

## A follow-up route

The most promising unexplored route, for a later attempt when rate limits allow:

**GitHub code search** was rate-limited during this research and is the fastest route to national
reproductions of regulatory schemas. For Israel specifically, look for Israeli government or
municipal repositories carrying accessibility-statement templates or generators, in the way HMRC's
service encodes the UK field list as YAML. That would convert several REPORTED items here into
FETCHED ones — most valuably the declaration's field list.

Israeli primary law will likely remain unreachable while `gov.il` and the Knesset site are blocked.
**That is a permanent caveat on this file, not a temporary one.**
