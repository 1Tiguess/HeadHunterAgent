# Hunt notes — RTL, bidi and Hebrew locale correctness

Scout report, reported speech. Read-only. Nothing downloaded, cloned, or installed.

## Access note

`www.unicode.org` was **refused by the egress proxy** (not by the site), so the normative UAX #9
text — the Bidirectional Algorithm itself — was unreachable. `github.com` and
`raw.githubusercontent.com` worked for everything else. Two GitHub paths 404'd and were re-routed.

**Everything below is fetched from source unless explicitly marked search-extracted.** This is the
highest-provenance hunt of the whole effort: real spec sources, real CLDR data files, real code
points read from the repositories that generate the published pages.

## Sources

**`w3c/i18n-drafts` — `articles/inline-bidi-markup/uba-basics.en.html`** (fetched).
The mental model that makes every downstream fix make sense. Characters carry one of three
directional strengths: Latin letters are strongly LTR, Hebrew and Arabic strongly RTL, and spaces,
punctuation and symbols are **neutral** because they occur in both scripts. Digits are **weak**,
behaving differently again. The algorithm groups adjacent same-strength characters into runs, then
orders those runs by a single **base direction** inherited from the containing paragraph.

**Neutrals between two runs of the same direction absorb that direction; neutrals between two runs
of opposite direction fall back to the base direction** — which is exactly where things break. The
worked failures are the Hebrew cases that matter: a Hebrew restaurant name followed by `- 5 reviews`
reorders so the digit jumps to the wrong side of the dash; a Hebrew name inside an English list
swallows the separating comma into the RTL run so items visually merge. **The algorithm cannot infer
authorial intent — the boundary has to be declared.**

**`w3c/i18n-drafts` — `questions/qa-bidi-unicode-controls.en.html`** (fetched).
The full control-character inventory, plus the architectural distinction that matters: the
1990s-era **embedding** and **override** characters set a direction but still let content interact
across the boundary, so spillover still occurs. The **isolate** characters added later both set
direction *and seal the run off in both directions*.

Decision rule: **markup wins wherever markup exists**, because control characters cannot express
inheritance or scoping through a document tree and cannot cross block boundaries — they are
inline-only. Control characters are for the places markup cannot reach: `<title>` text,
`title=`/`alt=`/`placeholder` attribute values, WebVTT, CSV, log lines, JSON consumed as plain text.

**`mdn/content` — `html/reference/elements/bdi`** (fetched).
`<bdi>` is the markup form of first-strong isolation: it behaves as if `dir="auto"` were set even
with no `dir` present, so it both detects the embedded string's direction and isolates it. Two
design points worth carrying: `<bdi>` is preferable to `<span dir="auto">` not because rendering
differs (it does not) but because it **declares intent**; and `unicode-bidi: isolate` in CSS is
explicitly **not** an acceptable substitute, because a user agent may drop CSS and **directionality
is semantic, not decorative**. Canonical demo: a leaderboard of user-supplied names next to ranks,
where the RTL name drags the hyphen and rank out of place, fixed by wrapping only the name.

**`mdn/content` — `html/reference/global_attributes/dir`** (fetched).
`dir="auto"` is specified as **first strong character wins**, and the scan explicitly skips
`<bdi>`, `<script>`, `<style>`, `<textarea>` and any descendant already carrying a valid `dir`. For
`<textarea>` and `<pre>` it runs **per paragraph** rather than once per element. `<input type="tel">`
is forced LTR regardless. `dir` on an `<img>` governs how `title` and `alt` render. `dir="rtl"` on a
`<table>` reverses column order. Guidance: `auto` is a heuristic of last resort — use an explicit
direction whenever you know it — and prefer `dir` over the CSS `direction`/`unicode-bidi` pair.

**`w3c/i18n-drafts` — `questions/qa-html-dir.en.html`** (fetched).
Placement discipline. Base direction belongs on `<html lang="he" dir="rtl">`; adding `dir` further
down is justified only when genuinely *changing* direction for that subtree, and over-applying it is
itself a bug. Direction lives in markup rather than CSS as a **semantics** argument, not a
progressive-enhancement one: direction changes meaning, so it belongs to the content layer.

**The piece most teams miss: `dirname`.** `<input name="comment" dirname="commentdir" dir="auto">`
submits the browser-computed direction alongside the value, so the server can **store direction per
record** instead of re-guessing at render time. And the `dir="auto"` failure mode is named
precisely: in a chat log, a Hebrew message that happens to begin with a Latin brand name, a URL or
an emoji-adjacent neutral gets typed LTR — right-alignment lost, punctuation on the wrong end.

**`w3c/csswg-drafts` — `css-writing-modes-4/Overview.bs`** (fetched).
The normative home of `direction` and `unicode-bidi`. All six values and what separates them:
`normal` opens no embedding level; `embed` opens one but still allows interaction across the edge;
`isolate` makes the box opaque to the outside, which sees it as a single object-replacement
placeholder; `bidi-override` discards the implicit algorithm; `isolate-override` is opaque outside
and overridden inside; `plaintext` isolates but derives its own base direction by first-strong
heuristic. **The spec itself tells HTML authors not to use these properties and to use `dir`/`<bdo>`
instead.**

It also supplies the vocabulary needed to be rigorous: physical directions, **flow-relative**
(`block-start`/`block-end`/`inline-start`/`inline-end`), and **line-relative** (`line-left`/
`line-right`). `inline-start` equals line-left under `ltr` and line-right under `rtl` — **that
three-way distinction is what people collapse when they say "just flip it."**

**`w3c/csswg-drafts` — `css-logical-1/Overview.bs`** (fetched).
The complete mapping, plus two facts that change how the skill must be written. First, the mapping
depends on the **used** values of `writing-mode`, `direction` *and* `text-orientation` together —
not `direction` alone — and those must resolve before logical and physical declarations cascade
against each other, which makes mixing them for the same box **a genuine ordering hazard, not a
style preference**. Second, the honest limitation: Level 1 deliberately scopes itself to CSS2-era
features and states future modules are expected to ship flow-relative coordinates themselves. **That
is the spec admitting there is no logical vocabulary for `background-position`, `box-shadow`
offsets, `transform` translations, or gradient angles.**

**`ItielMaN/rtl-guidelines`** (fetched). An Israeli-maintained open-source RTL guidelines repo,
Mozilla-adjacent lineage. The only source here with a defensible **icon mirroring rule set** —
see Concrete specifics. Also prescribes logical properties as primary with the `:dir(rtl)` selector
as the escape hatch, and lists content classes that must stay LTR *inside* an RTL page. Gives **no
Hebrew-specific typography or bidi guidance** — that gap is ours to fill.

**`karan68/rtl-verify`** (fetched). The answer to "how do you verify RTL without eyeballing a
screenshot." Two modes: **zero-golden** reads computed styles and geometry and asserts logical
invariants with no reference image; **differential** renders the same page LTR and RTL and looks for
things that failed to change (or changed when they shouldn't). Its false-positive control is the
interesting bit — checks fire **only on elements actually containing Hebrew or Arabic characters**,
so legitimate LTR islands inside an RTL page don't trip it. Reported bug distribution from its mined
corpus: physical inset/offset properties dominate, then margins, then text-align, then
border-radius. Stated limits: misses inline-margin and float-based bugs, icon mirroring needs manual
annotation, benchmark is researcher-authored reconstructions.

**CLDR data — `unicode-org/cldr` and `unicode-org/cldr-json`** (fetched, five files).
All the locale numbers below are read from source. **The single most interesting structural
observation: CLDR's Hebrew number patterns have bidi control characters baked into the data.** The
`he` minus sign is an LRM followed by a hyphen; the currency pattern begins with an RLM and carries
another before the currency placeholder. CLDR is **pre-solving the bidi problem inside the format
string** — which means a hand-rolled formatter (`${amount} ₪`) does not merely lose locale niceties,
it loses the invisible marks that put the sign on the correct side.

*Scout's own inference, flagged as such:* this also means `Intl.NumberFormat` output contains
invisible characters, so **equality assertions in tests against naively typed expected strings will
fail confusingly.**

**`mdn/content` — `Intl.Locale.prototype.getTextInfo()`** (fetched). A platform-native way to derive
direction from a locale tag rather than hardcoding a list. Historical note: it shipped first as a
`textInfo` accessor, then became a method because the accessor minted a fresh object per access and
broke identity comparisons — older runtimes may expose the property form.

**Pseudo-localisation — search-extracted only, not fetched.** The standard pseudo-locale pair:
`en-XA` accents and expands strings (~40%+, more for short ones), pads with non-Latin glyphs to
smoke out font coverage, and wraps each string in sentinel delimiters so hardcoded English is
visually obvious. **`en-XB`** (and the ICU/Android sibling `ar-XB`) is the **bidi/RTL mirror
pseudo-locale**, exercising mirroring and bidi handling without real translations. CI pattern: build
per pseudo-locale, drive key screens, fail on truncation, on any string still rendering as plain
English, or on broken mirroring. **Treat the numbers as search-extracted.**

## Tier 1 — an existing skill in this territory

**`menashsoffer/learnAI` PR #4** (fetched). A PR adding Claude skills including **`hebrew-i18n`** and
**`hebrew-rtl-best-practices`** (MIT, attributed to "Skills IL/Yootech", 2026).

Structure: each ships a `SKILL.md` plus a parallel **`SKILL_HE.md` Hebrew-language copy**, a
`references/` split (`bidi.md`, `pluralization.md` / `css-logical-properties.md`), a
`scripts/generate_i18n.py`, and metadata JSON.

The instructive part is the split: bidi and pluralisation are large enough to earn their own
reference files, and CSS logical properties is treated as **lookup-table material** — exactly the
kind of long enumerated mapping you do not want inline. **The dual-language SKILL.md is a curiosity
rather than a model: it doubles the body a model must read for no behavioural gain.** Frontmatter
`description` strings could not be extracted from the PR diff view.

## Synthesis

**1. Mirroring the layout is the easy 20%; bidi isolation of *strings* is the 80% that gets
skipped.** Every mangled Hebrew interface has correct-looking columns and broken sentences. The
failure is mechanical and predictable: any neutral character — space, hyphen, comma, colon, slash,
parenthesis, `@` — sitting between a Hebrew run and a Latin run resolves to the **base** direction,
not to either neighbour. So a Hebrew label followed by a Latin product name, a version number, a
URL, a phone number, an email, a file path or a bare integer **will** reorder, and the more
interpolation slots a template has, the more boundaries there are to break. The fix is
per-interpolation-slot isolation: `<bdi>` in HTML, FSI…PDI in plain text, **never a blanket `dir` on
the container.** A skill that teaches "wrap every dynamic value whose direction you do not control"
closes most of the gap on its own.

**2. Direction is content-layer state with three distinct owners, and conflating them is the
second-largest bug source.** Document base direction → `<html dir>`. Per-string direction of
**user-generated** content → the data, captured at input via `dirname`, persisted, re-emitted, with
`dir="auto"` as a fallback known to guess wrong. Layout responsiveness → CSS logical properties,
which must **never** be the thing carrying direction. Three owners, three mechanisms; the common
failure is making one do all three jobs.

**3. Hebrew is not "Arabic that reads the same way," and the CLDR data proves it.** Hebrew uses
**Western digits** by default, a dot decimal separator and comma group separator — identical to
English — so the "Arabic-Indic numerals" instinct is **actively wrong** for Hebrew. Hebrew has a
`two` plural category English lacks and **lost its `many` category** in recent CLDR, so both under-
and over-provisioning message catalogs are live failure modes. Israel's week starts **Sunday** and
its weekend is **Friday–Saturday**, which breaks every date picker built on a Monday-or-Sunday
binary. Hebrew dates use `d.M.y` with dots, 24-hour time, and a `ב` prefix before month names.
**Getting these right is what distinguishes this from a generic RTL skill.**

## Improvement openings

1. **Every source except the CLDR data treats RTL as one undifferentiated thing.**
   `rtl-guidelines` returned nothing Hebrew-specific; W3C's bidi articles use Arabic examples almost
   exclusively — and Arabic has cursive joining, its own digits and different plural arity, all of
   which **mislead if generalised to Hebrew**. The Hebrew-specific layer exists only as raw locale
   data nobody has assembled into guidance. **That assembly is the whole opportunity.**
2. **The normative bidi source was unreachable.** Everything about the algorithm comes from W3C's
   explainer and the CSS spec — excellent, but non-normative on UAX #9's rule numbering (P2/P3,
   W1–W7, N0–N2, X1–X10, L1–L4). If the skill cites rules by number, that needs another route.
3. **Nobody connects bidi to the places markup cannot go.** All HTML-level advice assumes a DOM. The
   real-world Hebrew breakage points are `document.title`, `aria-label`, `title=`, `placeholder`,
   toast strings, `alt` text, clipboard, CSV/PDF export, email subjects, push payloads and log output
   — every one needing **control characters, not `<bdi>`**. **The single biggest unserved area across
   all twelve sources.**
4. **The logical-properties story has a documented hole nobody fills.** No logical form for
   `background-position`, `box-shadow` offsets, `transform: translateX`, gradient angles, `clip-path`.
   A skill that **names the gap and prescribes the `:dir(rtl)` override pattern for exactly those
   cases** is more useful than one implying logical properties are total.
5. **Testing guidance is split across two sources that do not know about each other.** `rtl-verify`
   gives structural invariants but is research-grade with no icon-mirroring automation; pseudo-locales
   give content stress but say nothing about geometry. **A combined recipe does not exist anywhere.**
6. **The one existing Hebrew skill pair is thin and duplicative.** Dual-language body for no
   behavioural benefit; its reference split omits mirroring, numerals, calendar, Israel week
   conventions and testing entirely. **Easy to beat on coverage.**
7. **Version skew is a real, teachable failure mode nobody documents as such.** `Intl.PluralRules`
   and `Intl.NumberFormat` output for `he`/`ar` depends on the ICU version in the runtime, and
   pinned-CLDR libraries are demonstrably wrong. Guidance should be defensive about categories and
   **never assert exact formatted strings in tests.**

## Concrete specifics

**Bidi control characters with code points:**
- Isolates (preferred): LRI `U+2066`, RLI `U+2067`, **FSI `U+2068`** (first strong), PDI `U+2069`
  (pops any of the three)
- Legacy embeddings/overrides: LRE `U+202A`, RLE `U+202B`, LRO `U+202D`, RLO `U+202E`, PDF `U+202C`.
  **These leak across the boundary — that is why isolates exist.**
- Single marks: LRM `U+200E`, RLM `U+200F` — invisible strong characters, used to nudge one neutral
- Markup equivalents: `<bdi>` ≈ FSI…PDI; `<bdo dir>` ≈ LRO/RLO…PDF

**`unicode-bidi` values:** `normal`, `embed`, `isolate`, `bidi-override`, `isolate-override`,
`plaintext`. `plaintext` = `isolate` + first-strong self-determination.

**`dir` values:** `ltr`, `rtl`, `auto`. Companion: `dirname`.

**Logical ↔ physical mapping** (complete for CSS Logical 1's scope): sizes `block-size`/`inline-size`
+ min/max; margins/padding/insets `block-start`/`block-end`/`inline-start`/`inline-end`; borders all
three sub-properties. **Border radius uses a two-axis scheme, not start/end:**
`border-start-start-radius` ↔ `border-top-left-radius`, `border-start-end-radius` ↔
`border-top-right-radius`, `border-end-start-radius` ↔ `border-bottom-left-radius`,
`border-end-end-radius` ↔ `border-bottom-right-radius`. **This is the one people get wrong.**
Flow-relative keywords: `float`/`clear` take `inline-start`/`inline-end`; `text-align` takes
`start`/`end`; `caption-side` takes `inline-start`/`inline-end`.

**Hebrew CLDR plural rules (`he`) — three categories only:**
- `one`: `i = 1 and v = 0 or i = 0 and v != 0` — integer 1; **and fractional values with integer part
  zero (0.5, 0.25) are `one` in Hebrew**
- `two`: `i = 2 and v = 0` — integer 2
- `other`: 0, 3–17, 100, 1000, …

**No `few`, no `many`, no `zero`.** The `many` category **used to exist** for Hebrew (multiples of
ten) and was removed; libraries pinned to old CLDR still emit it (`golang.org/x/text` generated from
CLDR 32 against current CLDR 48 still returns `Many` at multiples of ten — *search-extracted*).
Catalogs should **tolerate a stray `many` without crashing** while not requiring translators to
author it.

**Arabic CLDR plural rules (`ar`) — all six:** `zero` (n=0), `one` (n=1), `two` (n=2), `few`
(n%100 = 3..10), `many` (n%100 = 11..99), `other`. **Arabic is the maximal case; Hebrew is not.**

**Numbering systems:** `latn` digits `0123456789`; `arab` `٠١٢٣٤٥٦٧٨٩`; `arabext`
`۰۱۲۳۴۵۶۷۸۹`; **`hebr` is algorithmic** — letter-based numerals (א, ב, …), not digits.

**Hebrew numbers (`he/numbers.json`):** `defaultNumberingSystem` = **`latn`**. Decimal `.`, group
`,`. **Minus sign is LRM + hyphen.** Currency standard and accounting both
`‏#,##0.00 ‏¤;‏-#,##0.00 ‏¤` — note the **RLM `U+200F`** before the number and again before `¤`.
Shekel `₪` `U+20AA`.

**Arabic numbers:** current CLDR `main` reports `defaultNumberingSystem` = `latn` —
**verify against the ICU version your runtime ships**, since it differs across releases and directly
changes `Intl.NumberFormat("ar")` output. Arabic-specific symbols under `arab`: decimal `٫`, group
`٬`, minus preceded by ALM `؜` `U+061C`.

**Hebrew Gregorian formats:** full `EEEE, d בMMMM y`, long `d בMMMM y`, medium `d בMMM y`, short
**`d.M.y`**. Times full `H:mm:ss zzzz` … short `H:mm` — **24-hour, capital `H`, no leading zero**.
All four dateTime combinators `{1}, {0}`. Abbreviated months use the **Hebrew geresh `׳` `U+05F3`**
(e.g. `ינו׳`), *not* an ASCII apostrophe. Day periods are literally `AM`/`PM` — Hebrew does not
localise them, itself a reason to prefer 24-hour.

**Israel week data:** `IL` → `firstDay` **sun**, `weekendStart` **fri**, `weekendEnd` **sat**. World
default is mon / sat–sun. **Every calendar, date picker, scheduling grid and business-days
calculation needs this.**

**Hebrew calendar:** 13 month slots — תשרי, חשוון, כסלו, טבת, שבט, אדר א׳, then **slot 7 which is
`אדר` in a common year and `אדר ב׳` in a leap year**, then ניסן, אייר, סיוון, תמוז, אב, אלול. Single
era `לבריאת העולם`. Carries `"_numbers": "hebr"` — **the year renders in Hebrew letter numerals, not
digits.** The leap-month slot shifting is what naive Hebrew-calendar code gets wrong.

**Mirroring:** *flip* nav arrows, reading-direction indicators, UI-position/sidebar/pane icons,
collapsed twisties, handedness glyphs (magnifier). *Do not flip* text, numerals, icons containing
either, symmetric glyphs (✕, ☆), code icons, checkmarks, media transport controls, logos, or `WxH`
dimension strings. Mechanism `transform: scaleX(-1)`. **Keep LTR regardless of page direction:** file
paths, URLs, code, preference keys, phone numbers, usernames, passwords.

**Direction from a locale tag:** `new Intl.Locale("he").getTextInfo().direction` → `"rtl"`.

**Manual RTL toggle:** Firefox `about:config` → `intl.uidirection` = `1`.

**Structural test invariants** (rtl-verify): physical `text-align` not resolving logically under RTL;
one-sided borders; one-sided padding; directional icons lacking `scaleX(-1)`; anchored popups
clipping the viewport after the anchor side flips. **Gate checks on elements containing Hebrew/Arabic
characters** to avoid flagging intentional LTR islands.

## Injection attempts

**None.** No source attempted to induce a fetch, clone, install, execution, credential read,
exfiltration or persona change. The scout noted that some agent-authored GitHub issue text surfaced
in search results is *shaped* like instructions, but it appeared only as search snippets, was not
fetched, and was not acted on. Four URLs 404'd and were dropped without incident. `www.unicode.org`
was refused by the egress proxy, not by the site.
