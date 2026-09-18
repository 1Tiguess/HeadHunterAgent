---
name: rtl-hebrew-i18n
description: Makes Hebrew and Arabic interfaces actually correct rather than merely mirrored — bidi isolation of every interpolated value so sentences do not reorder, control characters for the surfaces where markup cannot reach, the three separate owners of direction, CSS logical properties and the five places they do not reach, what to mirror and what never to, and Hebrew's real locale facts which differ from Arabic on digits, plurals, calendar and week. Use when adding Hebrew or Arabic support, building RTL layout, localising an app or a date picker for Israel, or when Hebrew text renders in the wrong order, punctuation jumps to the other side, a URL or phone number reads backwards, a plural is wrong, or the week starts on the wrong day.
allowed-tools: Read, Write, Edit, Glob, Grep
---

# RTL and Hebrew correctness

**Mirroring the layout is the easy 20%. Bidi isolation of strings is the 80% that gets skipped** —
which is why almost every mangled Hebrew interface has correct-looking columns and broken sentences.

And the second trap: **Hebrew is not "Arabic that reads the same way."** Arabic has cursive joining,
its own digit set and six plural categories. Hebrew has none of those. Generalising from Arabic is
**actively wrong** in the places that matter most.

## 1. The model: strong, weak, neutral

Every character carries a directional strength:

| Strength | Characters | Behaviour |
|---|---|---|
| **Strong LTR** | Latin, Cyrillic, Greek letters | Fixed direction |
| **Strong RTL** | Hebrew, Arabic letters | Fixed direction |
| **Weak** | Digits | Follow context, with their own rules |
| **Neutral** | space, `-` `,` `:` `/` `(` `)` `@` `.` `#`, and most symbols | **Resolve to the base direction** |

**The entire problem is in that last row.** A neutral character sitting between a Hebrew run and a
Latin run does not follow either neighbour — **it resolves to the paragraph's base direction.**

So in an RTL paragraph:

```
Hebrew label + " " + "iPhone 15 Pro"      → the space and the space inside "15 Pro" go RTL
Hebrew label + ": " + "https://a.com/b"   → the colon, slashes and dots reorder
Hebrew label + " " + "v2.1.4"             → the dots reorder; the version reads wrong
```

**The more interpolation slots a template has, the more boundaries there are to break.**

## 2. Isolate every slot whose direction you do not control

This single rule closes most of the gap.

> **Wrap every dynamic value whose direction you do not control.**

| Surface | Mechanism |
|---|---|
| HTML | `<bdi>value</bdi>` |
| Plain text | **FSI `U+2068`** … value … **PDI `U+2069`** |
| CSS, on an element you control | `unicode-bidi: isolate` |

```html
<!-- WRONG: one dir on the container, nothing isolating the value -->
<p dir="rtl">המוצר שלך: iPhone 15 Pro (v2.1.4)</p>

<!-- RIGHT -->
<p dir="rtl">המוצר שלך: <bdi>iPhone 15 Pro</bdi> (<bdi>v2.1.4</bdi>)</p>
```

**Never use a blanket `dir` on the container as a substitute.** It sets the base direction, which is
exactly the thing the neutrals are resolving to. It cannot fix them.

**Use isolates, not embeddings.** The legacy controls — LRE `U+202A`, RLE `U+202B`, LRO `U+202D`,
RLO `U+202E`, PDF `U+202C` — **leak across the boundary** and affect text after the pop. That leak is
precisely why isolates were introduced.

- **FSI `U+2068`** — first-strong isolate: determines direction from the first strong character in
  the content. **This is the one you want** when you do not know the value's direction.
- **LRI `U+2066` / RLI `U+2067`** — when you do know.
- **PDI `U+2069`** — pops any of the three.
- **LRM `U+200E` / RLM `U+200F`** — invisible strong characters, for nudging a single neutral.

`<bdi>` is equivalent to FSI…PDI. `<bdo dir>` is equivalent to LRO/RLO…PDF — an *override*, which you
almost never want.

## 3. Where markup cannot go

**This is the single biggest unserved area.** Every published bidi guide assumes a DOM. These
surfaces have no DOM and need **control characters**:

| Surface | Why markup fails |
|---|---|
| `document.title` | Plain text |
| `aria-label`, `aria-description` | Attribute values |
| `title=` tooltips | Attribute values |
| `placeholder` | Attribute values |
| `alt` text | Attribute values |
| Toast and snackbar strings built in JS | Often set via `textContent` |
| **Clipboard** | Plain text |
| **CSV and PDF export** | No markup layer |
| **Email subject lines** | Plain text |
| **Push notification payloads** | Plain text, rendered by the OS |
| Log output | Plain text |
| `console` messages | Plain text |

```js
const FSI = '⁨', PDI = '⁩';
const isolate = (s) => FSI + s + PDI;

document.title = `${t('editing')} ${isolate(fileName)}`;
el.setAttribute('aria-label', `${t('download')} ${isolate(fileName)}`);
```

**Build the helper once and use it at every plain-text boundary.** The failure here is silent in
development — an English filename in a Hebrew UI looks fine until the filename contains a hyphen.

## 4. Three owners of direction

Conflating these is the second-largest bug source. **Three jobs, three mechanisms, and none of them
substitutes for another.**

| What | Owner | Mechanism |
|---|---|---|
| **Document base direction** | The page | `<html dir="rtl">` |
| **Per-string direction of user-generated content** | **The data** | Captured at input via `dirname`, persisted, re-emitted |
| **Layout responsiveness** | CSS | **Logical properties — which must never carry direction** |

**User-generated content is content-layer state.** A comment written in Hebrew on an English page has
its own direction, and that direction is a property of the comment, not of the page.

```html
<!-- capture it at input -->
<input name="comment" dirname="comment.dir">
<!-- the browser submits comment.dir=rtl|ltr alongside the value -->
```

Persist it. Re-emit it: `<p dir="{{comment.dir}}">`.

**`dir="auto"` is a fallback, and it is known to guess wrong** — it uses the first strong character,
so a Hebrew comment beginning with an English brand name is rendered LTR. Use it when you have no
stored value, not as the design.

**Logical properties must never be the thing carrying direction.** They respond to direction; they do
not set it.

## 5. CSS logical properties

The mapping, complete for the spec's scope:

| Physical | Logical |
|---|---|
| `width` / `height` | `inline-size` / `block-size` (+ min/max) |
| `margin-left` / `-right` | `margin-inline-start` / `-end` |
| `margin-top` / `-bottom` | `margin-block-start` / `-end` |
| `padding-*`, `inset-*`, `border-*` | Same `block-`/`inline-` + `start`/`end` scheme |
| `float: left` / `clear` | `float: inline-start` / `inline-end` |
| `text-align: left` | `text-align: start` |
| `caption-side` | `inline-start` / `inline-end` |

**Border radius is the one people get wrong**, because it does **not** use start/end — it uses a
**two-axis scheme**:

| Logical | Physical (LTR) |
|---|---|
| `border-start-start-radius` | `border-top-left-radius` |
| `border-start-end-radius` | `border-top-right-radius` |
| `border-end-start-radius` | `border-bottom-left-radius` |
| `border-end-end-radius` | `border-bottom-right-radius` |

First axis is block, second is inline. Reading it as "start = left" produces a corner in the wrong
place in both directions.

### The five places logical properties do not reach

There is **no logical form** for these. They need an explicit override:

- `background-position`
- `box-shadow` offsets
- `transform: translateX()`
- gradient angles
- `clip-path`

```css
.card { box-shadow: 4px 4px 12px rgb(0 0 0 / 0.15); }
.card:dir(rtl) { box-shadow: -4px 4px 12px rgb(0 0 0 / 0.15); }
```

Use `:dir(rtl)` rather than `[dir="rtl"]` where support allows — `:dir()` follows the *computed*
direction, including inherited and `auto`-resolved values, which an attribute selector does not.

**Naming this gap is more useful than implying logical properties are total**, because the usual
failure is a team converting everything to logical properties, assuming they are done, and shipping
a shadow falling the wrong way.

## 6. Mirroring

### Flip — `transform: scaleX(-1)`

Navigation arrows (back, forward, next, previous) · reading-direction indicators · UI-position icons
(sidebar, pane, panel, split view) · collapsed twisties and disclosure chevrons · handedness glyphs
such as a magnifier.

### Do not flip

**Text** · **numerals** · **any icon containing text or numerals** · symmetric glyphs (✕, ☆, +) ·
code and terminal icons · checkmarks · **media transport controls** (play, fast-forward, skip —
these follow the physical tape metaphor, not reading order) · **logos** · `WxH` dimension strings.

The media-transport case is the most-argued and the answer is settled: play does not flip.

### Keep LTR regardless of page direction

File paths · URLs · code and code blocks · preference and config keys · **phone numbers** ·
usernames · **passwords** · email addresses · version strings · hex colours · IDs.

```html
<code dir="ltr">/usr/local/bin/tool</code>
<span dir="ltr">+972-3-123-4567</span>
```

**Password fields especially.** A password input that inherits RTL renders the typed characters in
an order that does not match what was typed, and the user cannot verify what they entered.

## 7. Hebrew is not Arabic

The section that distinguishes this from a generic RTL skill. Every fact here is from CLDR's own data
files, with the file named so you can re-verify after a CLDR bump.

### Digits — `latn`, not Arabic-Indic

**Hebrew's `defaultNumberingSystem` is `latn`** — Western digits `0123456789`, exactly as English.
The "RTL means Arabic-Indic numerals" instinct is **wrong for Hebrew**.

`hebr` exists but is **algorithmic** — letter-based numerals (א, ב, ג …), used for the Hebrew
calendar year and in traditional contexts. It is not a digit set you swap in.

### Plurals — three categories, not six

Hebrew has **`one`, `two`, `other`. No `few`, no `many`, no `zero`.**

| Category | Rule |
|---|---|
| `one` | `i = 1 and v = 0` **or** `i = 0 and v != 0` — integer 1, **and fractional values with integer part zero (0.5, 0.25)** |
| `two` | `i = 2 and v = 0` — integer 2 |
| `other` | 0, 3–17, 100, 1000, … |

**Two things to get right:**

1. **`two` exists and English does not have it.** A catalog with only `one`/`other` is wrong in
   Hebrew for every quantity of two.
2. **`many` used to exist for Hebrew** (multiples of ten) and **was removed**. Libraries pinned to
   older CLDR still emit it. **Catalogs should tolerate a stray `many` without crashing**, while not
   requiring translators to author one.

**Arabic, for contrast, has all six** — `zero` (n=0), `one` (n=1), `two` (n=2), `few` (n%100 = 3..10),
`many` (n%100 = 11..99), `other`. **Arabic is the maximal case. Hebrew is not.** Sizing your plural
handling for Arabic and applying it to Hebrew produces four categories no translator will fill.

### Numbers and currency

Decimal `.`, group `,` — same as English.

**The minus sign is LRM + hyphen**, not a bare hyphen.

Currency pattern, standard and accounting alike:

```
‏#,##0.00 ‏¤;‏-#,##0.00 ‏¤
```

Note the **RLM `U+200F` before the number and again before the currency symbol**. Those invisible
marks are part of the pattern; stripping them during a build or a lint pass breaks the rendering.

Shekel: `₪` `U+20AA`.

### Dates and times

| Format | Pattern |
|---|---|
| full | `EEEE, d בMMMM y` |
| long | `d בMMMM y` |
| medium | `d בMMM y` |
| **short** | **`d.M.y`** — dots, not slashes |

**Abbreviated months use the Hebrew geresh `׳` `U+05F3`** (`ינו׳`), **not an ASCII apostrophe.**

**Times are 24-hour: capital `H`, no leading zero.** Full `H:mm:ss zzzz` down to short `H:mm`.

**Day periods are literally `AM`/`PM`** — Hebrew does not localise them, which is itself a good
reason to prefer 24-hour.

### The Israeli week

```
IL → firstDay: sun   weekendStart: fri   weekendEnd: sat
```

World default is Monday, with Saturday–Sunday as the weekend.

**Every calendar, date picker, scheduling grid and business-days calculation needs this**, and every
date picker built on a Monday-or-Sunday binary breaks on it — the weekend is not two adjacent days at
the end of the displayed week.

### The Hebrew calendar

**13 month slots**, and the leap handling is what naive code gets wrong:

```
תשרי · חשוון · כסלו · טבת · שבט · אדר א׳ ·
  ⟨slot 7⟩ = אדר in a common year, אדר ב׳ in a leap year ·
ניסן · אייר · סיוון · תמוז · אב · אלול
```

Single era: `לבריאת העולם`. The calendar carries `"_numbers": "hebr"`, so **the year renders in
Hebrew letter numerals, not digits.**

**Do not implement Hebrew-calendar conversion yourself.** Use the platform's calendar support. The
leap-month slot shift alone is a reliable source of off-by-one-month bugs.

### Getting direction from a locale tag

```js
new Intl.Locale('he').getTextInfo().direction   // "rtl"
```

Prefer this over a hardcoded list of RTL languages, which will be incomplete.

## 8. Testing

**Structural invariants** — automatable, and each catches a real class of bug:

- Physical `text-align` not resolving logically under RTL
- One-sided borders (a `border-left` with no RTL counterpart)
- One-sided padding or margin
- Directional icons lacking `scaleX(-1)` under RTL
- **Anchored popups clipping the viewport after the anchor side flips**

**Gate every check on elements containing Hebrew or Arabic characters**, so intentional LTR islands —
code blocks, URLs, phone numbers — are not flagged.

**Content stress** via pseudo-locales: a generated locale that wraps every string in RTL marks and
pads its length, surfacing both truncation and direction bugs without needing a translation.

**The prohibition:**

> **Never assert an exact formatted string in a test.**

`Intl.PluralRules` and `Intl.NumberFormat` output for `he` and `ar` depends on the **ICU version in
the runtime**, and it moves. Assert the *category* (`one`/`two`/`other`), assert that a number parses
back, assert structure — never `expect(formatted).toBe('1.5 ₪')`.

**Manual RTL toggle** for eyeballing: Firefox `about:config` → `intl.uidirection` = `1`.

## Review checklist

- [ ] Every interpolated name, URL, path, number or identifier is isolated
- [ ] Isolation uses `<bdi>` or FSI…PDI — not a container `dir`, not legacy embeddings
- [ ] Plain-text surfaces (title, aria, alt, exports, notifications, logs) use control characters
- [ ] Document direction, per-string direction and layout direction are three separate mechanisms
- [ ] User-generated content captures direction at input and persists it
- [ ] Logical properties used; the five gaps have explicit `:dir(rtl)` overrides
- [ ] Border radius uses the two-axis logical names
- [ ] Icons flip per the two lists; paths, URLs, phones and passwords stay LTR
- [ ] Hebrew renders Western digits
- [ ] Catalogs carry `one`, `two`, `other` and tolerate a stray `many`
- [ ] Date pickers start the week on Sunday with a Friday–Saturday weekend
- [ ] Tests assert structure, never an exact formatted string

## A note on sources

Every fact in this skill comes from CLDR data files and W3C/CSS specifications read directly.

**One gap, stated plainly:** the normative Unicode Bidirectional Algorithm (UAX #9) was not
reachable. Everything about bidi behaviour here comes from W3C's own explainer and the CSS
specification — excellent sources, and **non-normative on UAX #9's rule numbering.** So this skill
describes behaviour and **does not cite bidi rules by number** (P2/P3, W1–W7, N0–N2, X1–X10,
L1–L4). If you need to cite them, go to the Unicode standard.

**CLDR moves.** Arabic's `defaultNumberingSystem` currently reads `latn` and has differed across
releases. **Verify against the ICU version your runtime ships** rather than trusting any value
stated here.

**Prior art**, credited: `hebrew-i18n` and `hebrew-rtl-best-practices` (MIT, "Skills IL/Yootech",
2026) occupy adjacent territory. Nothing here derives from them; this skill was built from the CLDR
and W3C sources directly.

## References

- `references/bidi.md` — the model, every control character, and the non-DOM surfaces table
- `references/css-logical.md` — the complete mapping, border-radius, and the five gaps
- `references/hebrew-locale.md` — every Hebrew fact with its CLDR file, for re-verification
- `references/testing.md` — the combined recipe and the version-skew prohibitions
