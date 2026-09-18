# HeadHunter run — September 2026

The second end-to-end run, and the first under a **near-total egress blockade**. Six skills
authored covering engineering craft and the regulatory layer.

**The finding that shaped everything: domains whose canonical knowledge lives as code or
specifications on GitHub survived the blockade. Domains whose knowledge lives in regulator or
vendor prose did not.** That asymmetry is not a footnote about this run — it is a property of
how technical knowledge is published, and it determines which skills can cite and which can
only report.

## What was run

| | |
|---|---|
| Session | `bdea28ff-8ec4-5211-9766-65c58482cac0` |
| Gate armed by | `arm-gate.py`, automatically |
| Hunts run | 7 attempted, **6 written up** |
| Skills authored | 6 `SKILL.md` + 24 reference files |
| Hook tests | 77, 0 failures |
| New gate defect found | **1** (Finding #7) |
| Anything downloaded | **Nothing** |

## The hunts

| Hunt | Primary sources reached | Outcome |
|---|---|---|
| Resilience | Reference implementations' own source | `resilience-patterns` |
| Application security | **All of them** | `application-security` |
| RTL / Hebrew | **All but one** | `rtl-hebrew-i18n` |
| Backend architecture | 22 of 29 fetches | `production-data-layer` — two sections under-evidenced |
| UX journeys | All 22 | `ux-journey-design` |
| Legal must-have features | **12, and no regulator at all** | `compliance-by-design` |
| Privacy | **Zero** | **Absorbed into `compliance-by-design`** |

**The privacy hunt reached zero primary sources** — every regulator domain was blocked. Rather
than author a skill with nothing behind it, the user redirected the effort into researching
what regulation requires **as product features**, which is a question GitHub-hosted schemas and
specifications can actually answer. That hunt became `compliance-by-design`, which subsumes the
privacy artefacts with far better evidence than a standalone privacy skill would have had.

**Seven skills were approved; six were built.** Shipping a seventh to meet the number would have
meant shipping the one with no sources.

## The egress picture

Blocked, in full: `ada.gov` · `oag.ca.gov` · `cppa.ca.gov` · `ftc.gov` · `eur-lex.europa.eu` ·
`ico.org.uk` · `legislation.gov.uk` · `cnil.fr` · `dataprotection.ie` · `etsi.org` · `w3.org` ·
**`w3c.github.io`** (GitHub *Pages* is blocked even though `github.com` is not) · `gov.il` (all
hosts) · `fs.knesset.gov.il` · `sii.org.il` · `kolzchut.org.il` · `aisrael.org` ·
`www.unicode.org` · `baymard.com` · `api.github.com` (403) · GitHub code search (429).

Reachable: **`github.com` HTML tree pages and `raw.githubusercontent.com`.** That was the entire
primary-fetch surface for three of the six hunts.

### The egress doctrine this produced

Developed during the run and now standing guidance to scouts:

1. **Route to the canonical source repository upstream of a blocked rendered site.** NIST
   publishes SP 800-63B-4 in its own GitHub organisation; `pages.nist.gov` was blocked and
   `raw.githubusercontent.com/usnistgov/800-63-4/...` was not. **That is the same document from
   its publisher, not a mirror.**
2. **Never substitute an unverifiable mirror.** A Medium repost of a blocked article is not the
   article.
3. **Flag search-extracted claims.** A domain-pinned search that returns the regulator's own URL
   and a summary is not a reading of the page.
4. **Name holes rather than filling them.** Every skill here states what it could not reach.

Rules 1 and 4 are what make the difference between `application-security` — which cites section
numbers because it read them — and `compliance-by-design`, which marks every claim FETCHED or
REPORTED because it could not.

## Evidence quality, by skill

| Skill | Provenance |
|---|---|
| `application-security` | **Every source read in full.** NIST SP 800-63B-4, OWASP ASVS 5.0, the Cheat Sheet Series, RFC 8725. Cites section numbers |
| `rtl-hebrew-i18n` | **Every source read but one.** CLDR data files and W3C/CSS specs. UAX #9 unreachable, so **the skill declines to cite bidi rules by number** |
| `ux-journey-design` | All 22 sources fetched. One study reached second-hand only, and marked as such |
| `resilience-patterns` | Reference implementations read directly; the canonical prose write-ups have no repository and are search-extracted |
| `production-data-layer` | Postgres, Django, Hibernate, PgBouncer and OTel read directly. **Job queues and caching named as under-evidenced** rather than filled from listicles |
| `compliance-by-design` | **12 sources read, zero regulators.** Every claim carries FETCHED or REPORTED. Israel is entirely REPORTED, with **five items it declines to guess** |

## The backend scout died and was salvaged

The backend-architecture scout hit a session rate limit and was terminated **before writing its
report**. Its 29 tool results were still in the transcript on disk, so they were extracted and
written up directly rather than re-running the hunt.

`hunts/backend-architecture-notes.md` states this at the top, because the distinction matters:
**the fetched content is the scout's; the organisation and the improvement openings are not.**

## Finding #7 — the gate caught a bug in itself

Documented in `finding-7-relative-paths.md`. In short: the gate classifies redirect targets as
**literal strings**, so

```
cd ~/.claude/skills/x/references && cat > notes.md
```

is denied even while `equipping` permits that directory — the classifier resolves `notes.md`
against the project directory and never sees the `cd`. A `$VAR` in the path fails the same way.

**This is the mirror of Finding #6.** That one was the classifier under-detecting (`cp`, `mv`,
`sed -i` write files without being caught); this is it over-detecting. Both follow from command
classification being a lexical heuristic rather than a shell, and both are documented in the
README's Limits rather than chased.

The workaround is a literal absolute path in the redirect.

Also confirmed, for the third time and the first on a freshly authored skill in a clean
container: **skills hot-load.** `resilience-patterns` appeared in the available-skills list the
moment its `SKILL.md` was written, with no restart.

## Layout

```
hunts/     six hunt write-ups, each with its own evidence-quality section
specs/     six approved build specifications
finding-7-relative-paths.md
```

The hunts are the research record; the specs are what was approved before anything was authored.
Both are preserved because **a skill that cannot tell you which of its claims have a source
behind them is a skill you cannot maintain** — and for `compliance-by-design` in particular, the
spec's risk review is the thing that justifies the skill existing at all.
