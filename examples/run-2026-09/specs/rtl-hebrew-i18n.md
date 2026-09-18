# Build instructions: rtl-hebrew-i18n

**Status:** draft
**Target:** `~/.claude/skills/rtl-hebrew-i18n/` (global — usable in every project)
**Serves:** the Israeli half of "built by Israeli and international regulations" at the product
layer — a Hebrew interface that is actually correct, not merely mirrored
**Hunt notes:** `.headhunter/hunts/rtl-hebrew-notes.md`

## Capability gap

Claude mirrors the layout and calls it RTL support. The columns come out right and the sentences
come out broken. It also treats Hebrew as "Arabic that reads the same way", which is **actively
wrong** in the places that matter most: digits, plural arity, calendar and week structure.

Two failures, precisely:

1. **Bidi isolation of strings is skipped.** Any neutral character — space, hyphen, comma, colon,
   slash, parenthesis, `@` — sitting between a Hebrew run and a Latin run resolves to the **base**
   direction, not to either neighbour. So a Hebrew label followed by a Latin product name, a version
   number, a URL, a phone number, an email, a file path or a bare integer **will** reorder. The more
   interpolation slots a template has, the more boundaries there are to break.
2. **Hebrew-specific locale facts are assumed from Arabic.** Hebrew uses **Western digits** by
   default. It has a `two` plural category English lacks and **no `many`** (it was removed from
   CLDR). Israel's week starts **Sunday**, weekend **Friday–Saturday**.

## References studied

| Source | What it contributes | Fetched or search-extracted? |
|---|---|---|
| `w3c/i18n-drafts` bidi articles | The strong/weak/neutral mental model; isolation over embedding | **Fetched** |
| CSS Logical Properties spec | The complete logical↔physical mapping, including border-radius's two-axis scheme | **Fetched** |
| CLDR `he/numbers.json`, `he/ca-gregorian.json`, `he/ca-hebrew.json`, `plurals.xml`, `weekData` | Every Hebrew-specific fact in this skill | **Fetched — raw data files** |
| CLDR `ar` equivalents | The contrast that shows Hebrew is not the Arabic case | **Fetched** |
| `rtl-verify`, pseudo-locale tooling | Structural test invariants; content stress | **Fetched** |
| `menashsoffer/learnAI` PR #4 — `hebrew-i18n`, `hebrew-rtl-best-practices` | Prior art on the shelf | **Fetched** |

**Provenance: this is the highest-confidence hunt of the whole effort.** Real spec sources, real
CLDR data files, real code points read from the repositories that generate the published pages.
**One hole: `www.unicode.org` was refused by the egress proxy**, so UAX #9 itself — the normative
Bidirectional Algorithm — was never read. Everything about the algorithm comes from W3C's
explainer and the CSS spec, which are excellent but **non-normative on UAX #9's rule numbering**.
**Consequence: the skill must not cite bidi rules by number** (P2/P3, W1–W7, N0–N2, X1–X10, L1–L4)
without another route to the normative text.

## Improvements over the references

1. **Assemble the Hebrew layer that exists only as raw data.** Every source except CLDR treats RTL
   as one undifferentiated thing; W3C's bidi articles use Arabic examples almost exclusively, and
   Arabic has cursive joining, its own digits and different plural arity — **all of which mislead if
   generalised to Hebrew.** Nobody has assembled the Hebrew-specific layer into guidance. That
   assembly is the whole opportunity.
2. **Cover the places markup cannot go.** All HTML-level advice assumes a DOM. The real breakage
   points are `document.title`, `aria-label`, `title=`, `placeholder`, toast strings, `alt` text,
   clipboard, CSV and PDF export, email subjects, push payloads and log output — every one needing
   **control characters, not `<bdi>`**. **This is the single biggest unserved area across all twelve
   sources.**
3. **Name the logical-properties hole and prescribe the override.** There is no logical form for
   `background-position`, `box-shadow` offsets, `transform: translateX`, gradient angles or
   `clip-path`. A skill that names exactly those cases and prescribes the `:dir(rtl)` override is
   more useful than one implying logical properties are total.
4. **Give a combined test recipe.** `rtl-verify` gives structural invariants with no icon-mirroring
   automation; pseudo-locales give content stress and say nothing about geometry. The two sources do
   not know about each other and **a combined recipe exists nowhere.**
5. **Teach version skew as a failure mode.** `Intl.PluralRules` and `Intl.NumberFormat` output for
   `he`/`ar` depends on the runtime's ICU version, and pinned-CLDR libraries are demonstrably wrong.
   Be defensive about categories; **never assert exact formatted strings in tests.**
6. **Beat the existing Hebrew skill pair on coverage.** It ships a dual-language `SKILL.md` —
   doubling the body a model must read for no behavioural gain — and its reference split omits
   mirroring, numerals, calendar, Israel week conventions and testing entirely.

## The skill to build

### Frontmatter
- `name:` rtl-hebrew-i18n
- `description:` third person, under 1024 chars. Trigger on both the task and the symptom — adding
  Hebrew or Arabic support, RTL layout, bidirectional text, localising an app, a date picker or
  calendar for Israel; and: "the Hebrew text is in the wrong order", "the punctuation jumped to the
  other side", "the URL renders backwards", "the plural is wrong in Hebrew", "the week starts on the
  wrong day", "it looks fine in English and broken in Hebrew".
- `allowed-tools:` Read, Write, Edit, Glob, Grep

### Body structure
1. **The model: strong, weak, neutral** — why neutrals between two scripts break
2. **Isolate every slot whose direction you do not control** — the single highest-value rule
3. **Where markup cannot go** — control characters for titles, aria, exports, logs, notifications
4. **Three owners of direction** — document, per-string data, layout — and never conflate them
5. **Logical properties** — the mapping, and the five places it does not reach
6. **Mirroring** — what flips, what must not, and what stays LTR regardless
7. **Hebrew is not Arabic** — digits, plurals, calendar, week
8. **Formatting** — numbers, currency, dates, times, with the invisible marks that belong in them
9. **Testing** — structural invariants plus content stress, and what never to assert

### The technique it encodes

**The isolation rule, stated so it generalises:** wrap every dynamic value whose direction you do
not control. `<bdi>` in HTML; **FSI `U+2068` … PDI `U+2069`** in plain text; **never a blanket `dir`
on the container.** Isolates exist because the legacy embeddings and overrides — LRE `U+202A`, RLE
`U+202B`, LRO `U+202D`, RLO `U+202E`, PDF `U+202C` — **leak across the boundary.** LRM `U+200E` and
RLM `U+200F` are invisible strong characters for nudging a single neutral. `<bdi>` ≈ FSI…PDI;
`<bdo dir>` ≈ LRO/RLO…PDF. `unicode-bidi: plaintext` = `isolate` + first-strong self-determination.

**Three owners, three mechanisms.** Document base direction → `<html dir>`. Per-string direction of
**user-generated** content → the data itself, captured at input via `dirname`, persisted,
re-emitted, with `dir="auto"` as a fallback **known to guess wrong**. Layout responsiveness → CSS
logical properties, which must **never** be the thing carrying direction. The common failure is
making one mechanism do all three jobs.

**The logical↔physical mapping, complete, with the trap called out.** Sizes `block-size`/
`inline-size` plus min/max; margins, padding and insets on `block-start`/`block-end`/`inline-start`/
`inline-end`; borders across all three sub-properties; `float`/`clear` taking `inline-start`/
`inline-end`; `text-align` taking `start`/`end`; `caption-side` taking `inline-start`/`inline-end`.
**Border radius uses a two-axis scheme, not start/end** — `border-start-start-radius` ↔
`border-top-left-radius`, `border-start-end-radius` ↔ `border-top-right-radius`,
`border-end-start-radius` ↔ `border-bottom-left-radius`, `border-end-end-radius` ↔
`border-bottom-right-radius`. **This is the one people get wrong.** Then the five holes, with
`:dir(rtl)` overrides.

**Mirroring, as two lists.** *Flip* (`transform: scaleX(-1)`): nav arrows, reading-direction
indicators, UI-position/sidebar/pane icons, collapsed twisties, handedness glyphs like a magnifier.
*Do not flip*: text, numerals, icons containing either, symmetric glyphs (✕, ☆), code icons,
checkmarks, media transport controls, logos, `WxH` dimension strings. **Keep LTR regardless of page
direction:** file paths, URLs, code, preference keys, phone numbers, usernames, passwords.

**Hebrew's actual locale facts** — the section that distinguishes this from a generic RTL skill:

- **Digits are `latn`.** `defaultNumberingSystem` for `he` is **Western digits**. The
  "Arabic-Indic numerals" instinct is wrong for Hebrew. (`hebr` exists but is **algorithmic** —
  letter numerals א, ב, … — not a digit set.)
- **Plurals: three categories only.** `one` (`i = 1 and v = 0 or i = 0 and v != 0` — note that
  **fractional values with integer part zero, 0.5 and 0.25, are `one` in Hebrew**), `two`
  (`i = 2 and v = 0`), `other`. **No `few`, no `many`, no `zero`.** `many` *used to exist* for
  multiples of ten and was removed; libraries pinned to old CLDR still emit it. **Catalogs should
  tolerate a stray `many` without crashing while not requiring translators to author one.**
  Contrast Arabic, which has all six — **Arabic is the maximal case; Hebrew is not.**
- **Numbers:** decimal `.`, group `,`. **The minus sign is LRM + hyphen.** Currency, standard and
  accounting alike, is `‏#,##0.00 ‏¤;‏-#,##0.00 ‏¤` — with an **RLM `U+200F` before the number and
  again before the currency symbol.** Shekel `₪` `U+20AA`.
- **Dates:** full `EEEE, d בMMMM y`, long `d בMMMM y`, medium `d בMMM y`, short **`d.M.y`**.
  Abbreviated months use the **Hebrew geresh `׳` `U+05F3`** (`ינו׳`), *not* an ASCII apostrophe.
- **Times: 24-hour, capital `H`, no leading zero.** Day periods are literally `AM`/`PM` — Hebrew
  does not localise them, which is itself a reason to prefer 24-hour.
- **Week: `IL` → `firstDay` sun, `weekendStart` fri, `weekendEnd` sat.** World default is mon /
  sat–sun. **Every calendar, date picker, scheduling grid and business-days calculation needs this**,
  and every date picker built on a Monday-or-Sunday binary breaks on it.
- **Hebrew calendar: 13 month slots**, where **slot 7 is `אדר` in a common year and `אדר ב׳` in a
  leap year** — the leap-month slot shift is what naive code gets wrong. Single era
  `לבריאת העולם`. Carries `"_numbers": "hebr"`, so **the year renders in Hebrew letter numerals, not
  digits.**
- Direction from a tag: `new Intl.Locale("he").getTextInfo().direction` → `"rtl"`.

**Testing, combined.** Structural invariants: physical `text-align` not resolving logically under
RTL; one-sided borders; one-sided padding; directional icons lacking `scaleX(-1)`; anchored popups
clipping the viewport after the anchor side flips. **Gate every check on elements containing
Hebrew or Arabic characters**, so intentional LTR islands are not flagged. Content stress via
pseudo-locales. And the prohibition: **never assert an exact formatted string**, because ICU
versions move.

### Reference files
One level deep; table of contents where over 100 lines.

- `references/bidi.md` — the strong/weak/neutral model, every control character with its code point,
  the isolate-vs-embedding distinction, and **the non-DOM surfaces table** (title, aria, alt,
  placeholder, toast, clipboard, CSV, PDF, email subject, push payload, logs) with the control-
  character recipe for each
- `references/css-logical.md` — the complete mapping as a lookup table, the border-radius two-axis
  scheme, the five properties with no logical form and their `:dir(rtl)` overrides
- `references/hebrew-locale.md` — plural rules with the fractional edge case, numbering systems,
  number and currency patterns with their invisible marks, date and time patterns, Israel week data,
  the Hebrew calendar's leap-month slot; each attributed to its CLDR file
- `references/testing.md` — the combined recipe, the gating rule, the pseudo-locale pass, and the
  version-skew prohibitions

## How to tell it worked

- [ ] Every interpolation slot carrying a name, URL, path, number or identifier is isolated
- [ ] Isolation uses `<bdi>`/FSI…PDI, not a container `dir` and not legacy embeddings
- [ ] Non-DOM strings — titles, aria labels, exports, notifications — use control characters
- [ ] Document direction, per-string direction and layout direction are three separate mechanisms
- [ ] User-generated content captures direction at input via `dirname` and persists it
- [ ] Logical properties are used, and the five gaps get explicit `:dir(rtl)` overrides
- [ ] Border radius uses the two-axis logical names correctly
- [ ] Icons flip or do not flip according to the two lists; paths, URLs and phone numbers stay LTR
- [ ] Hebrew renders Western digits
- [ ] Message catalogs carry `one`, `two`, `other` and tolerate a stray `many`
- [ ] Date pickers and business-day math start the week on Sunday with a Friday–Saturday weekend
- [ ] Tests assert structure, never an exact formatted string

## Risk review

**None adversarial.** No source attempted to induce a fetch, execution, installation, credential
read, exfiltration or persona change.

Provenance items:

1. **`www.unicode.org` was refused by the egress proxy**, so UAX #9 was never read. The skill must
   **not cite bidi rules by number**. The behaviour it teaches is sound — it comes from W3C's own
   explainer and the CSS specification — but the normative rule identifiers are out of reach.
2. **One search-extracted claim:** that `golang.org/x/text`, generated from CLDR 32, still returns
   `Many` for Hebrew at multiples of ten against current CLDR 48. It is presented as an illustration
   of version skew, not as a fact about that library's current state, and the skill should say so.
3. **CLDR data moves.** Arabic's `defaultNumberingSystem` currently reads `latn` in CLDR `main` and
   has differed across releases. The skill must tell the reader to verify against the ICU version
   their runtime ships rather than trusting the value stated.
4. **Prior art exists and is attributed.** `hebrew-i18n` and `hebrew-rtl-best-practices` (MIT,
   "Skills IL/Yootech", 2026) occupy adjacent territory. **Nothing from them is copied.** This skill
   is built from the CLDR and W3C sources directly; the PR was read to understand the shape of the
   space and is credited as prior art in the skill's own notes.

## Originality attestation

- [x] Nothing was downloaded, cloned, or installed
- [x] No code or prose was copied verbatim from a source
- [x] Every technique is restated in my own words
- [x] Sources are listed above as references, credited where their idea is distinctive
- [x] Any injection attempt is recorded in the Risk review

## Build steps

1. Create `~/.claude/skills/rtl-hebrew-i18n/SKILL.md`, under 500 lines. **Single language — English
   body only**, unlike the prior art.
2. Write the four reference files with tables of contents; `hebrew-locale.md` and `css-logical.md`
   are lookup tables and belong out of the body.
3. Attribute each Hebrew fact to its CLDR file inline, so a reader can re-verify after a CLDR bump.
4. Read the authored `SKILL.md` back to confirm it is on disk and the frontmatter parses.
5. Mirror into `authored-skills/rtl-hebrew-i18n/`.
