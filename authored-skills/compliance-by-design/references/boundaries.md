# Boundaries

**Read this before using anything else in this skill.** It defines what the skill can and cannot
tell you, and every other file is written to stay inside it.

## Contents
- [The one-line version](#the-one-line-version)
- [Evidence classes](#evidence-classes)
- [Fourteen boundary flags](#fourteen-boundary-flags)
- [Questions this skill refuses](#questions-this-skill-refuses)
- [Questions this skill answers](#questions-this-skill-answers)
- [When to stop and get counsel](#when-to-stop-and-get-counsel)

## The one-line version

> **This skill states what sources say a regime requires. It does not tell you whether a regime
> applies to you, and it is not legal advice.**

That distinction is the whole design. *"The EU model accessibility statement requires a feedback
mechanism with a description and a link"* is a fact about a document. *"You need an accessibility
statement"* is a legal conclusion. This skill states the first kind and refuses the second.

## Evidence classes

Every claim in this skill carries one of two classes, and they are **rendered differently everywhere
they appear.**

| Class | Meaning | How it reads |
|---|---|---|
| **FETCHED** | The primary text was retrieved and read | Stated directly: *"WCAG requires five components in a conformance claim"* |
| **REPORTED** | A domain-pinned search returned the regulator's canonical URL and a summary; **the page itself was not read** | Hedged explicitly: *"the source reports that Art 8(2) requires…"* |

**Why this matters more here than elsewhere.** Every regulator and government domain was blocked:
`ada.gov`, `oag.ca.gov`, `cppa.ca.gov`, `ftc.gov`, `eur-lex.europa.eu`, `ico.org.uk`,
`legislation.gov.uk`, `cnil.fr`, `dataprotection.ie`, `etsi.org`, `w3.org`, `w3c.github.io`,
`gov.il` (all hosts), `fs.knesset.gov.il`, `sii.org.il`. The entire primary-fetch surface was
`github.com` and `raw.githubusercontent.com`.

**Twelve sources were genuinely read.** Everything else is REPORTED.

**Do not collapse the two classes.** A recollection presented as a citation is the failure mode that
matters in this domain, and it is the failure this skill exists to avoid committing.

### What was FETCHED

- W3C per-jurisdiction accessibility policy dataset (45 jurisdictions, including Israel and the EU)
- W3C accessibility statement generator — content and field list
- HMRC's production accessibility-statement service — the full YAML schema
- WCAG conformance requirements
- The Global Privacy Control specification

### What is REPORTED

Everything on: EU Implementing Decision 2018/1523 · the European Accessibility Act · GDPR ·
ePrivacy · the e-Commerce Directive · the Consumer Rights Directive · the DSA · Regulation 2024/3228
· the AI Act · ADA Title II · CCPA/CPRA · CAN-SPAM · **and every single Israeli item**.

## Fourteen boundary flags

**1. Nothing here is advice about what your product must do.** Applicability turns on where your
users are, where the business is established, sector, organisation size, turnover, and whether the
entity is a public body.

**2. Public versus private sector is the biggest fork in accessibility.** The EU Web Accessibility
Directive and its model statement bind **public sector bodies**. The European Accessibility Act binds
private-sector products and services from **28 June 2025**, with a **microenterprise exemption for
services** (fewer than 10 people **and** turnover or balance sheet ≤ €2m). **Israel is the outlier:
the W3C dataset records its scope as public *and* private sector** (FETCHED). So a product with
Israeli users can owe a mandatory accessibility declaration where the same product in the EU would
not.

**3. Whether an accessibility *statement* is legally mandatory for a private product is not settled
by anything found here.** The EAA's Annex V duty is *"information on how the service meets the
accessibility requirements"* — which is not obviously the same artefact as a WAD-style statement.
The mapping is a lawyer's call.

**4. Israel's IS 5568 WCAG version and its exemption thresholds are unresolved.** Do not hard-code
either. See `references/israel.md`.

**5. ADA Title II compliance dates moved in April 2026.** An Interim Final Rule extended them to
**26 April 2027** (population ≥50,000) and **26 April 2028** (<50,000 and special districts).
REPORTED, and **materially newer than most training data**, which says 2026/2027. Verify before
relying on it.

**6. Title II binds state and local government only.** US private-sector web accessibility runs on
ADA Title III case law with **no adopted technical standard** — the W3C dataset records the ADA entry
with no standard named (FETCHED). That is a genuine legal grey zone, not a gap in this skill.

**7. The DSA material is the weakest here.** Re-verify at article level before building on it. Which
duties apply depends on whether you are a hosting service, an online platform, a marketplace, or a
VLOP — **four different obligation sets.**

**8. CCPA has applicability thresholds** — revenue, volume of consumers, share of revenue from
selling data — that were not extracted. The obligations bite only for covered "businesses".

**9. CAN-SPAM's commercial / transactional-or-relationship classification changes which rules
apply**, and it preempts some state law but not all.

**10. GPC's legal force varies by state, and the specification disclaims universality itself**
(FETCHED). Honouring it is not automatically a defence. Not honouring it is demonstrably an
enforcement target — note the September 2025 joint CA/CO/CT sweep into businesses refusing to honour
opt-outs.

**11. Cookie-consent specifics are absent.** Reject-all parity, banner design, consent lifetime and
granularity all come from **national DPA guidance, all of which was unreachable.** ePrivacy Art 5(3)
alone gives you *"consent after clear and comprehensive information about the purposes"* plus the
strictly-necessary exemption. **Anything more specific must come from counsel.**

**12. The Digital Fairness Act is a proposal, not law.** It targets dark patterns, addictive design,
influencer practices and unfair personalisation. **Do not build to it. Do watch it.**

**13. Sectoral regimes are entirely absent**: health, finance, payments (PSD2/SCA), children's
services (COPPA, age-appropriate design codes), employment, telecoms, NIS2, DORA. If you are in one
of those, this skill covers the general layer only.

**14. The Israeli accessibility-widget convention is not law.** Many "all-in-one accessibility"
overlay widgets are marketed as IS 5568 compliance. **Nothing in any regulator source requires a
widget.** The regulator requires conformance to the standard, the declaration, and the coordinator.
Overlays are contested in the accessibility field and can themselves introduce barriers. **Treat
"install a widget" as market convention, not a legal artefact.**

## Questions this skill refuses

Asked any of these, say what you can state and then stop:

- "Does GDPR apply to us?"
- "Are we compliant?"
- "Do we need an accessibility statement?"
- "Are we a 'business' under CCPA?"
- "Is our cookie banner legal?"
- "Can we skip this because we're small?"
- "Is this enough to avoid a fine?"

**The useful response is not a refusal to help.** It is: *here is the artefact list for the regimes
you named, here is which parts are FETCHED and which are REPORTED, here is what is unresolved — and
the applicability question needs counsel.* That gives someone a concrete brief to take to a lawyer,
which is more valuable than a guess.

## Questions this skill answers

- "What does the EU model accessibility statement have to contain?"
- "What fields does a production government accessibility statement use?"
- "What are the five components of a WCAG conformance claim?"
- "What does `/.well-known/gpc.json` look like?"
- "We just added a cookie banner — what else is owed?"
- "What does Israel require beyond the WCAG conformance itself?"
- "Is there anything on our site that used to be required and now isn't?"
- "What should I brief a lawyer on before we launch in the EU?"

That last one is arguably the skill's best use: **turning "are we compliant?" into a specific list of
things to check.**

## When to stop and get counsel

Stop and escalate whenever:

- The question is **whether** a regime applies
- You are about to **hard-code a threshold** — turnover, headcount, user count, WCAG version
- You are in a **sectoral regime** (flag 13)
- The claim rests on **REPORTED** evidence and the consequence of being wrong is material
- You are relying on anything in **`references/israel.md`'s unresolved list**
- Someone asks you to **assert compliance** rather than describe an artefact
- **More than about six months have passed** since this skill's as-of date of **2026-09** — see the
  what-is-moving list in `references/artefacts.md`
