# The union statement schema

**As of 2026-09.**

**Nobody publishes this.** The W3C's accessibility statement generator and the EU model statement are
different artefacts — **the W3C page warns that the Directive's requirements differ from its own
best-practice set, and then does not reconcile them.** A field set satisfying the EU model, the W3C
set and Israel's declaration **at once** did not exist anywhere that could be found.

This is that reconciliation.

**Every template, generator and schema found was public-sector-shaped**, yet the EAA pushed private
services into scope in June 2025 and Israel has had them in scope for years. **This schema is the
private-product-shaped version.**

## Contents
- [Design decisions inherited](#design-decisions-inherited)
- [The schema](#the-schema)
- [The limitation record](#the-limitation-record)
- [Rendering order](#rendering-order)
- [Craft rules](#craft-rules)
- [Which regime each field serves](#which-regime-each-field-serves)
- [Worked example](#worked-example)

## Design decisions inherited

Three, from a **production government service that renders every statement from YAML** (FETCHED):

**1. Scope is per service, not per domain.** With an explicit disclaimer pointing at the parent
site's own statement. A single statement covering "our website" is unfalsifiable; one covering a
named service can be tested.

**2. Milestones are first-class dated data.** Description plus target fix date. This makes the
statement **double as a remediation tracker**, and — the real benefit — it **goes stale visibly
rather than silently.** A milestone with a date in the past is a visible problem; a prose paragraph
saying "we are working on it" never expires.

**3. Statements are never deleted, only archived.** `statementVisibility: public | draft | archived`.

## The schema

```yaml
# ── identity ────────────────────────────────────────────────────────────
serviceName:              string    # required
serviceDescription:       string    # required
serviceUrl:               string    # required
serviceDomain:            string    # required — for the scope disclaimer
parentStatementUrl:       string    # optional — "this covers X, not all of Y"

# ── status ──────────────────────────────────────────────────────────────
complianceStatus:         enum      # required: full | partial | noncompliant
standard:                 string    # required: e.g. "WCAG 2.2 AA"
                                    # Israel: also is5568Part1/Part2 below
additionalRequirements:   string[]  # optional — anything applied beyond the standard

# ── the conformance claim's five components (WCAG, FETCHED) ─────────────
claimDate:                date      # required
claimScope:               string    # required — which pages/URLs, or complete processes
claimLevel:               enum      # required: A | AA | AAA
technologiesReliedUpon:   string[]  # required
technologiesUsedNotReliedUpon: string[]   # required

# ── dates ───────────────────────────────────────────────────────────────
statementCreatedDate:     date      # required
statementLastUpdatedDate: date      # required
serviceLastTestedDate:    date      # required for full/partial; OMITTED for noncompliant
statementVisibility:      enum      # public | draft | archived

# ── assessment ──────────────────────────────────────────────────────────
assessmentMethod:         enum      # required: self | third-party
evaluationReportUrl:      string    # optional
automatedTestingOnly:     boolean   # optional — declare it if true
automatedTestingDetails:  string    # required if automatedTestingOnly

# ── non-accessible content — the EU three-way split ─────────────────────
nonAccessibleContent:
  - reason:  enum                   # non-compliance | disproportionate-burden | out-of-scope
    contentPart:      string
    issue:            string        # in USER-FACING terms, not criterion numbers
    whyItOccurs:      string
    whatWeAreDoing:   string
    whatToDoMeanwhile: string

milestones:
  - description: string
    targetDate:  date

# ── routes the user must be able to reach ───────────────────────────────
feedback:
  description:         string       # required — EU requires description AND link
  link:                string       # required
  contact:             {}           # phone, email, postal, visitor address
  typicalResponseTime: string       # W3C generator field
  handlesExcludedContentRequests: boolean   # EU: feedback also requests excluded content

enforcement:
  description: string               # required — EU requires description AND link
  link:        string               # required
  bodyContact: {}                   # the enforcement body's contact details

# ── organisational ──────────────────────────────────────────────────────
organisationalMeasures: string[]    # mission statement, policies, procurement,
                                    # accessibility officer, training, goals, QA
approver:
  name:     string
  function: string
complaintsProcedure: string         # description of the formal procedure

# ── compatibility ───────────────────────────────────────────────────────
compatibleEnvironments:   string[]  # browser x AT x OS
incompatibleEnvironments: string[]
technicalPrerequisites:   string[]

# ── Israel ──────────────────────────────────────────────────────────────
is5568Part1Conformance:   string    # web content — extent of conformance
is5568Part2Conformance:   string    # digital documents — reported SEPARATELY
accessibilityCoordinator:
  name:          string             # required where the body employs >=25 people
  office:        string
  contactRoutes: {}

# ── EAA (private-sector services) ───────────────────────────────────────
howServiceMeetsRequirements: string # Annex V — must also be available in ORAL form
oralFormAvailability:        string # how to obtain it spoken
retentionCommitment:         string # retained for the life of the service
```

## The limitation record

The five-field shape, from the W3C generator (FETCHED). **This is the reusable part**, and it is
better than prose because each field answers a question the reader actually has:

| Field | The question it answers |
|---|---|
| `contentPart` | Where is this? |
| `issue` | What is wrong? |
| `whyItOccurs` | Is this negligence or a constraint? |
| `whatWeAreDoing` | Will it be fixed? |
| `whatToDoMeanwhile` | **What do I do right now?** |

**The last field is the one most statements omit and the one a blocked user most needs.**

## Rendering order

From a complete worked example (FETCHED):

```
commitment
  → organisational measures
  → conformance status
  → additional considerations
  → feedback
  → browser / AT compatibility
  → technical specifications
  → limitations and alternatives
  → assessment approach
  → evaluation report links
  → formal approval
  → formal complaints
  → creation and last-updated dates
```

A production government service orders it slightly differently, leading with a **scope note** —
*"this covers the service, not the whole of the parent site"* — which is worth adopting, because a
reader's first question is what the statement applies to.

## Craft rules

**FETCHED, from the W3C generator's own guidance:**

**1. Describe barriers in user-facing terms, not criterion numbers.**

> *"Videos do not have captions"* — **not** *"SC 1.2.2 was not met"*

The statement is for people who hit the barrier, not for auditors. Criterion numbers can go in the
evaluation report.

**2. Link the statement from several places** — footer, help menu, sitemap, about page — **using a
consistent link name** across web and mobile. Someone looking for it should find the same words
wherever they look.

**3. The statement must itself be accessible**, and where appropriate **machine-readable** (EU
2018/1523, REPORTED). A statement about accessibility that fails accessibility is the most easily
avoided finding available.

**4. Compliance status is an enum, not prose.** `full | partial | noncompliant`. Prose invites
hedging; an enum does not.

**5. `serviceLastTestedDate` is omitted for `noncompliant`.** Deliberate: claiming a test date
alongside non-compliance implies a rigour the status contradicts.

## Which regime each field serves

| Field group | EU 2018/1523 | W3C best practice | Israel | EAA |
|---|---|---|---|---|
| Identity, scope | ✓ | ✓ | ✓ | ✓ |
| `complianceStatus` enum | **✓ required** | ✓ | ✓ (per IS 5568 part) | |
| Five-component claim | | | | *(WCAG itself)* |
| `nonAccessibleContent` **split by reason** | **✓ required** | ✓ (unsplit) | | |
| Preparation date + method + last review | **✓ required** | ✓ | | |
| `feedback` with **description AND link** | **✓ required** | ✓ | ✓ (reporting contact) | |
| `enforcement` with **description AND link** | **✓ required** | | | |
| `milestones` | | | | |
| `organisationalMeasures` | | ✓ | | |
| `compatibleEnvironments` | | ✓ | | |
| `approver`, `complaintsProcedure` | | ✓ | | |
| `is5568Part1/Part2` separately | | | **✓ required** | |
| `accessibilityCoordinator` | | | **✓ ≥25 employees** | |
| `howServiceMeetsRequirements` + **oral form** + retention | | | | **✓ required** |

**Blank does not mean forbidden.** It means that regime does not require it. Including everything
satisfies all four; **the EU's mandatory set is the narrowest and the most specific**, and the two
"description AND link" requirements are the ones most often half-implemented — a contact email with
no description, or a description with no link.

## Worked example

```yaml
serviceName: Invoice Manager
serviceDescription: Create, send and track invoices
serviceUrl: https://app.example.com/invoices
serviceDomain: app.example.com
parentStatementUrl: https://example.com/accessibility

complianceStatus: partial
standard: WCAG 2.2 AA

claimDate: 2026-09-15
claimScope: All pages under /invoices, including the complete create-and-send process
claimLevel: AA
technologiesReliedUpon: [HTML, CSS, JavaScript, WAI-ARIA]
technologiesUsedNotReliedUpon: [SVG]

statementCreatedDate: 2026-03-01
statementLastUpdatedDate: 2026-09-15
serviceLastTestedDate: 2026-09-10
statementVisibility: public

assessmentMethod: third-party
evaluationReportUrl: https://example.com/a11y/invoice-manager-2026-09.pdf
automatedTestingOnly: false

nonAccessibleContent:
  - reason: non-compliance
    contentPart: The invoice PDF preview
    issue: Screen readers cannot read the preview
    whyItOccurs: It renders to a canvas element with no text alternative
    whatWeAreDoing: Replacing the preview with accessible HTML
    whatToDoMeanwhile: Use "Download invoice" to get a tagged PDF, which is accessible

milestones:
  - description: Replace the canvas invoice preview with accessible HTML
    targetDate: 2027-01-31

feedback:
  description: Tell us about any accessibility problem, or ask for content in another format
  link: https://example.com/accessibility/report
  contact: { email: access@example.com, phone: "+972-3-000-0000" }
  typicalResponseTime: 2 working days
  handlesExcludedContentRequests: true

enforcement:
  description: If you are not happy with our response, you can escalate
  link: https://example.com/accessibility/escalate
  bodyContact: { name: "<the applicable enforcement body>" }

approver: { name: "<name>", function: Head of Engineering }
complaintsProcedure: https://example.com/complaints

is5568Part1Conformance: Substantially conformant; see non-accessible content
is5568Part2Conformance: Conformant for generated PDFs; historical documents not assessed
accessibilityCoordinator:
  name: "<name>"
  office: "<address>"
  contactRoutes: { email: access@example.com, phone: "+972-3-000-0000" }
```

Note what the example does: **the limitation names a concrete workaround the user can act on today**,
and **the milestone carries a date that will visibly expire.** Those two properties are what separate
a statement that is useful from one that is decorative.
