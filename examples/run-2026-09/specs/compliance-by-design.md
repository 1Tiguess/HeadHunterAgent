# Build instructions: compliance-by-design

**Status:** draft
**Target:** `~/.claude/skills/compliance-by-design/` (global — usable in every project)
**Serves:** "built by Israeli and international regulations" — reframed, on the user's own
instruction, as **must-have-by-law product features**
**Hunt notes:** `.headhunter/hunts/legal-product-features-notes.md`

## What this skill is, and what it is not

The user's instruction was to research what Israeli and international regulation requires **as
product features**, and to build that into the skills rather than leave it out. That framing is what
makes this buildable and is the skill's entire scope discipline:

**It is an artefact checklist.** Pages that must exist. Controls a user must be able to reach.
Disclosures that must appear. Mechanisms that must work. Each entry paired with the regime that
supplies the basis, and with its evidence class.

**It is not a compliance opinion.** It never tells anyone whether a regime applies to them, never
asserts that a product *is* compliant, and never substitutes for counsel. The distinction is not
decorative — it is the difference between a useful build artefact and a confidently wrong legal
claim, and it must be enforced in the skill's own language, not just in a disclaimer at the top.

**Why the two can coexist.** "The EU model accessibility statement requires a feedback mechanism
with a description *and a link*" is a fact about a document. "You need an accessibility statement"
is a legal conclusion. The skill states the first kind and refuses the second.

## Capability gap

Claude builds products that are missing legally-required features and does not know it. No cookie
refusal path. A "Do Not Sell" link that is present but does not actually stop anything. An order
button labelled "Complete purchase" where the law requires words meaning *obligation to pay*. No
accessibility statement. An ODR-platform link that became wrong in July 2025. And — the Israeli
case, which almost nothing in training data covers — a private-sector product with Israeli users
owing an accessibility declaration, a named coordinator, and a **cancellation link on the homepage**.

## References studied

| Source | What it contributes | Evidence class |
|---|---|---|
| `w3c/wai-policies-prototype` | Machine-readable, jurisdiction-indexed WCAG version/level/sector per regime, 45 jurisdictions | **Fetched** |
| `w3c/wai-statements` | The generator's full field list; the four-field limitation record; the craft rules | **Fetched** |
| `hmrc/accessibility-statement-frontend` | A production government service rendering the mandated artefact from YAML — the best structural model anywhere | **Fetched** |
| `w3c/wcag` `understanding/conformance.html` | The five conformance requirements and the claim's fixed five-field shape | **Fetched** |
| `privacycg/gpc-spec` | `Sec-GPC`, `navigator.globalPrivacyControl`, `/.well-known/gpc.json` | **Fetched** |
| EU: 2018/1523, EAA, GDPR, ePrivacy, e-Commerce, CRD, DSA, 2024/3228, AI Act | The artefact requirements | **Search-extracted**, official domains pinned |
| US: ADA Title II rule, CCPA/CPRA, CAN-SPAM | ditto | **Search-extracted** |
| Israel: accessibility regs + IS 5568, declaration, coordinator, Amendment 13, duty to notify, s.30A, s.14C, continuing transactions | ditto | **Search-extracted; zero Israeli primary text was reachable** |

## The evidence problem, and how the skill handles it

**Every regulator and government domain was blocked.** Not a subset — `ada.gov`, `oag.ca.gov`,
`cppa.ca.gov`, `ftc.gov`, `eur-lex.europa.eu`, `ico.org.uk`, `legislation.gov.uk`, `cnil.fr`,
`dataprotection.ie`, `etsi.org`, `w3.org`, `w3c.github.io`, `gov.il` (all hosts),
`fs.knesset.gov.il`, `sii.org.il`. The entire primary-fetch surface was `github.com` and
`raw.githubusercontent.com`. **Twelve sources were genuinely read; everything else is domain-pinned
search.**

This is the reason the GitHub-first instruction was the right lever and also the reason it has a
ceiling: **domains whose canonical knowledge lives as code or specs on GitHub survived; domains
whose knowledge lives in regulator prose did not.**

**The mechanism that makes the skill honest: every claim carries its evidence class.** Fetched, or
search-extracted. They are rendered differently and never merged. A search-extracted claim is
written as *"the source reports that X requires Y"*, never as *"Y is required"*. This is not
hedging — it is the difference between a citation and a recollection, and in this domain a
recollection presented as a citation is the failure mode that matters.

## Improvements over the references

1. **Publish the union schema nobody publishes.** The W3C generator and the EU model statement are
   different artefacts — the W3C page says so and then does not reconcile them. **A field set that
   satisfies WAD/2018/1523, the W3C best-practice set and Israel's declaration at once does not
   exist anywhere.** Closing that is the single most valuable thing in this hunt.
2. **Build a private-product-shaped statement.** Every template, generator and schema found is
   public-sector-shaped, yet the EAA pushed private services into scope in June 2025 and **Israel
   has had the private sector in scope for years.**
3. **State the cross-regime rule the sources imply but never state: parity and proximity.**
   Cancelling must be as reachable as signing up. The CA/CO/CT sweep targets opt-outs that *don't
   work*; Israel requires a cancellation link **on the homepage**; CAN-SPAM caps unsubscribe at a
   single page. Three regimes, one principle, stated by none of them.
4. **Carry an as-of date and a what-is-moving list.** Dated-artefact risk here is real and
   asymmetric: the ODR link became wrong in July 2025, ADA Title II dates moved in April 2026,
   Israel's Amendment 13 landed August 2025. A checklist without an as-of date is a liability.
5. **Surface staleness rather than hiding it.** The W3C dataset's Israel entry was last touched
   **2017**; its EU entry **July 2025**. Anything built on it must show `last_updated` rather than
   present entries as current fact.
6. **Take the HMRC structural lessons and drop the HMRC shape.** Statement scope **per service, not
   per domain**, with an explicit pointer to the parent site's statement; **milestones as
   first-class dated data** so the artefact doubles as a remediation tracker and **goes stale
   visibly rather than silently**; never delete, only archive. The reusable core is about ten
   fields; the rest is organisational.
7. **Say plainly that the Israeli accessibility widget is not law.** GitHub surfaced many
   "all-in-one accessibility" overlays marketed as IS 5568 compliance. **Nothing in any regulator
   source requires a widget.** The regulator requires conformance to the standard, the declaration,
   and the coordinator. Overlays are contested and can themselves introduce barriers.

## The skill to build

### Frontmatter
- `name:` compliance-by-design
- `description:` third person, under 1024 chars. Trigger on build moments where an artefact is owed
  — adding a cookie banner, a signup, a checkout, a subscription, a contact form, analytics, email
  marketing, an AI feature, a delete-my-account flow; launching in the EU, the US or Israel; writing
  a privacy policy, terms, or an accessibility statement. **And on the symptom: "what do we legally
  need on this page".**
- `allowed-tools:` Read, Write, Edit, Glob, Grep

### Body structure
1. **What this gives you and what it does not** — stated first, in the skill's own voice
2. **How to read the evidence classes** — fetched vs reported, and why it changes what you may claim
3. **The artefact checklist** — four tables: pages, controls, disclosures, mechanisms
4. **Triggered by what you just built** — a reverse index from feature → artefacts owed
5. **Parity and proximity** — the cross-regime rule
6. **Israel specifically** — including what could not be sourced
7. **The accessibility conformance claim** — the five fields, and why "WCAG 2.2 AA compliant" is not one
8. **Statement schema** — the union field set, as data
9. **Delete if present** — artefacts that became wrong
10. **As of, and what is moving**

### The technique it encodes

**The reverse index is the skill's most useful shape**, because it matches how a build actually
proceeds. *You added a cookie or analytics tag* → information about purposes before consent, a
refusal path as easy as acceptance, `/.well-known/gpc.json` if you honour GPC. *You added a signup*
→ notice at or before collection; purpose, recipients, rights and how to exercise them; for Israel,
**whether provision is legally obligatory or consensual, the consequences of refusing, and that
access and correction rights exist**. *You added a paid subscription* → an order button labelled
with words meaning obligation to pay; 14-day withdrawal; the model withdrawal form; and if it sells
online in Israel, **cancellation information plus a cancellation link on the main page**. *You added
email marketing* → identification as advertising, opt-out notice, physical postal address; opt-out
live ≥30 days, honoured within 10 business days, **no more than one page**; for Israel, the literal
word **פרסומת** in the header and a valid email for refusals. *You added an AI feature* → tell people
they are interacting with an AI; mark generative output machine-readably; label deepfakes visibly.
*You shipped at all* → an accessibility statement where one is owed, and an Impressum-class legal
notice in the EU.

**The conformance claim, stated as a correction.** "We are WCAG 2.2 AA compliant" is **not** a
conformance claim. A claim has five components: **date, scope, level, technologies relied upon,
technologies used but not relied upon.** And the rule that invalidates most informal claims:
conformance is for **full pages only** and for **complete processes** — **a conformant checkout page
inside a non-conformant checkout flow claims nothing.** A statement of partial conformance is the
defined route for uncontrolled third-party content.

**The limitation record's four-field shape**, lifted from the W3C generator because it is the
reusable part: **content part → the issue → why it occurs → what we are doing about it → what to do
in the meantime.** Paired with the craft rule: describe barriers in **user-facing terms**, not
criterion numbers — "videos do not have captions", not "SC 1.2.2 was not met".

**The union statement schema**, expressed as data the way HMRC does it: service name, description,
domain, URL; compliance status as an enum (full / partial / noncompliant); visibility (public /
draft / archived); created and last-updated dates; last-tested date, required for full and partial
and omitted for noncompliant; the standard and version applied; non-accessible content split by
reason (**non-compliance, disproportionate burden, out of scope** — the EU split); dated milestones;
feedback route **with a description and a link**; enforcement/escalation route **with a description,
a link and the body's contact**; assessment method; approver; complaints procedure. Plus the Israeli
additions: **extent of conformance to IS 5568 Part 1 and Part 2 separately**, and the **accessibility
coordinator's name, office and contact routes**.

**Parity and proximity**, stated once and applied throughout: **the exit must be as reachable as the
entrance.** If signup is one click, cancellation is not four emails. If consent is a button, refusal
is a button of equal weight. This is the rule that the CA/CO/CT enforcement sweep, the Israeli
homepage requirement and CAN-SPAM's one-page cap are all instances of.

### Reference files
One level deep; table of contents where over 100 lines.

- `references/artefacts.md` — the four tables in full, every row carrying regime, basis and evidence
  class, with the as-of date at the top
- `references/reverse-index.md` — feature → artefacts owed, the primary working surface
- `references/israel.md` — the Israeli picture assembled, **with the unresolved list given equal
  prominence**: exemption thresholds, the declaration's enumerated legal field list, s.13/s.14
  response deadlines, the homepage cancellation-link citation, and the **IS 5568 WCAG version
  conflict** (gov.il and the September 2023 republication say WCAG 2.0 AA; a hobbyist GitHub source
  claimed 2.1 AA and was rejected as evidence)
- `references/statement-schema.md` — the union schema as a field list with types, conditionality and
  which regime each field serves
- `references/boundaries.md` — the fourteen legal-boundary flags, verbatim from the hunt notes

## How to tell it worked

- [ ] A cookie or analytics addition produces a refusal path, not just a banner
- [ ] A "Do Not Sell or Share" link is wired to something that actually stops the sale
- [ ] `Sec-GPC: 1` is honoured where the product claims to honour it, and `/.well-known/gpc.json`
      reflects reality
- [ ] A paid flow's confirm button carries obligation-to-pay wording
- [ ] Cancellation is as reachable as signup, and on the homepage where Israel requires it
- [ ] Marketing email carries all three CAN-SPAM disclosures, and the Hebrew header word where relevant
- [ ] An AI feature discloses itself and marks generative output
- [ ] Any accessibility claim carries all five components, or is not made
- [ ] No ODR platform link exists anywhere
- [ ] Every legal statement in generated output is marked fetched or reported
- [ ] **The skill declines to say whether a regime applies, every time it is asked**
- [ ] The as-of date is present and the what-is-moving list is current

## Risk review

**No injection attempts.** One source-quality rejection is recorded: a GitHub-pinned search returned
an answer synthesised from hobbyist repositories and a single pull request asserting "IS 5568:2020
aligns with WCAG 2.1 AA" and describing overlay widgets as compliance. **Not used as evidence.**
Commercial overlay-vendor repositories surfaced in the same search were not mined.

**The substantive risk in this skill is not adversarial — it is the risk of being confidently
wrong.** Four mitigations, all load-bearing:

1. **Evidence classes are rendered, not footnoted.** A search-extracted claim reads "the source
   reports that…" everywhere it appears.
2. **The unresolved list is given equal prominence to the resolved one**, especially for Israel,
   where **zero primary text was reachable**. Named holes: exemption thresholds (figures circulate;
   none traced to a regulator — **do not hard-code one**), the declaration's legal field list,
   s.13/s.14 deadlines, the homepage cancellation citation, and the IS 5568 version.
3. **The skill never answers an applicability question.** Applicability turns on where users are,
   where the business is established, sector, org size, turnover and public-vs-private status. The
   biggest fork is **public vs private sector**: EU WAD binds public bodies, the EAA binds private
   services with a microenterprise carve-out (<10 people **and** ≤€2m), and **Israel has both in
   scope**. A product with Israeli users can owe a mandatory declaration where the same product in
   the EU would not. **That comparison is stated as a fact about the regimes; the conclusion is left
   to counsel.**
4. **Weak extractions are marked as weak.** The **DSA** extraction is the weakest in the hunt and
   must be flagged at article level before anything is built on it; which duties apply depends on
   whether you are a hosting service, a platform, a marketplace or a VLOP — four different obligation
   sets. **Cookie-consent specifics** — reject-all parity, banner design, consent lifetime,
   granularity — come from national DPA guidance, **all of which was unreachable**; Art 5(3) alone
   gives only "consent after clear and comprehensive information" plus the strictly-necessary
   exemption. **ADA Title II dates moved in April 2026** and most training data says otherwise.
   **US private-sector web accessibility has no adopted technical standard** — a legal grey zone,
   not a spec gap. The **Digital Fairness Act is a proposal, not law.** **Sectoral regimes are
   entirely absent**: health, finance, payments, children's services, employment, telecoms, NIS2,
   DORA.

**I am not a lawyer and this skill does not make me one.** I raised that concern; the user's
instruction was to build the legal layer in as product features rather than leave it out, and that
is their call. The skill honours it by being maximally precise about *what a source says a regime
requires* and maximally clear that it says nothing about any particular product.

## Originality attestation

- [x] Nothing was downloaded, cloned, or installed
- [x] No code or prose was copied verbatim from a source
- [x] Every technique is restated in my own words
- [x] Sources are listed above as references, credited where their idea is distinctive
- [x] Any injection attempt is recorded in the Risk review

## Build steps

1. Create `~/.claude/skills/compliance-by-design/SKILL.md`, under 500 lines, opening with the
   scope statement and the evidence-class key **before any artefact content**.
2. Write the five reference files with tables of contents. `artefacts.md` and `reverse-index.md`
   carry the as-of date **2026-09** in their first line.
3. Write `references/boundaries.md` first, so the body's confidence language is constrained by it.
4. Read the authored `SKILL.md` back to confirm it is on disk and the frontmatter parses.
5. Mirror into `authored-skills/compliance-by-design/`.

## Follow-up hunt, when egress or rate limits allow

Retry **GitHub code search** (rate-limited this run) for national transpositions of the 2018/1523
model statement — Italy's `italia` org, Dutch and Nordic government orgs are the likely carriers —
and for further government accessibility-statement *services* in the `hmrc`/`alphagov` mould, since
those encode the legal field list as an executable schema and are reliably fetchable. That is the
route to replacing search-extracted EU rows with fetched ones.
