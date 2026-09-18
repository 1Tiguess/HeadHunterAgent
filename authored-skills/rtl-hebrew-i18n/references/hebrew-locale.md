# Hebrew locale facts

Every fact here is from a named CLDR data file, so it can be re-verified after a CLDR bump. **As of
CLDR 48 / 2026-09.**

## Contents
- [Numbering systems](#numbering-systems)
- [Plural rules](#plural-rules)
- [Number and currency formats](#number-and-currency-formats)
- [Date formats](#date-formats)
- [Time formats](#time-formats)
- [Week data](#week-data)
- [The Hebrew calendar](#the-hebrew-calendar)
- [Arabic, for contrast](#arabic-for-contrast)
- [Version skew](#version-skew)

## Numbering systems

**`he/numbers.json`: `defaultNumberingSystem` = `latn`.**

| System | Digits | Note |
|---|---|---|
| `latn` | `0123456789` | **Hebrew's default** |
| `arab` | `٠١٢٣٤٥٦٧٨٩` | Arabic-Indic |
| `arabext` | `۰۱۲۳۴۵۶۷۸۹` | Extended Arabic-Indic (Persian, Urdu) |
| `hebr` | א, ב, ג … | **Algorithmic** — letter numerals, not a digit set |

**Hebrew uses Western digits.** The instinct that "RTL means Arabic-Indic numerals" is wrong here and
produces an interface no Israeli user expects.

`hebr` appears in one place in ordinary use: **the Hebrew calendar year**, which renders in letter
numerals. It is not something you switch a UI to.

## Plural rules

**`plurals.xml`, locale `he` — three categories.**

| Category | Rule | Examples |
|---|---|---|
| `one` | `i = 1 and v = 0` **or** `i = 0 and v != 0` | 1; **and 0.5, 0.25, 0.9** |
| `two` | `i = 2 and v = 0` | 2 |
| `other` | everything else | 0, 3, 4, … 17, 100, 1000, 1.5, 2.5 |

*(`i` = integer part, `v` = number of visible fraction digits.)*

**Three things to get right:**

1. **`two` exists.** English does not have it, so a catalog generated from English source strings
   will be missing the Hebrew form for every quantity of two.
2. **Fractions with integer part zero are `one`.** 0.5 takes the `one` form in Hebrew. This is
   genuinely surprising and is a real source of wrong strings.
3. **`many` used to exist and was removed.** It covered multiples of ten. **Libraries pinned to older
   CLDR still emit it.**

**Practical rule for catalogs:** author `one`, `two`, `other`. **Tolerate a stray `many` without
crashing** — fall back to `other` — but do not ask translators to fill it.

```json
{
  "itemCount": {
    "one":   "פריט אחד",
    "two":   "שני פריטים",
    "other": "{count} פריטים"
  }
}
```

**Never hardcode the category list.** Read it from `Intl.PluralRules(locale).resolvedOptions()
.pluralCategories` and handle whatever comes back.

## Number and currency formats

**`he/numbers.json`:**

| Symbol | Value |
|---|---|
| Decimal separator | `.` |
| Group separator | `,` |
| **Minus sign** | **LRM + hyphen** |

Same separators as English. The minus sign is not a bare hyphen — the LRM keeps it on the correct
side of the digits.

**Currency pattern**, standard and accounting both:

```
‏#,##0.00 ‏¤;‏-#,##0.00 ‏¤
```

**The invisible characters are part of the pattern.** There is an **RLM `U+200F` before the number**
and another **before the `¤` currency placeholder**. A build step, a linter or a translation tool
that strips "invisible whitespace" will break currency rendering, and the breakage is hard to see in
a diff.

**Shekel: `₪` `U+20AA`.**

## Date formats

**`he/ca-gregorian.json`:**

| Format | Pattern | Example |
|---|---|---|
| full | `EEEE, d בMMMM y` | יום שני, 17 בספטמבר 2026 |
| long | `d בMMMM y` | 17 בספטמבר 2026 |
| medium | `d בMMM y` | 17 בספט׳ 2026 |
| **short** | **`d.M.y`** | 17.9.2026 |

**Short dates use dots**, not slashes. A Hebrew UI showing `17/9/2026` is using an English pattern.

**The `ב` prefix** ("in") attaches directly to the month name in long and full formats — `בספטמבר`,
not `ב ספטמבר`.

**Abbreviated months use the Hebrew geresh `׳` `U+05F3`** — `ינו׳`, `פבר׳`, `ספט׳. **Not** an ASCII
apostrophe `'` and **not** a right single quotation mark `’`. Three visually similar characters, one
correct.

All four dateTime combinators are `{1}, {0}` — date, comma, time.

## Time formats

**24-hour, capital `H`, no leading zero.**

| Format | Pattern |
|---|---|
| full | `H:mm:ss zzzz` |
| long | `H:mm:ss z` |
| medium | `H:mm:ss` |
| short | `H:mm` |

`H` rather than `HH` means **9:05, not 09:05**.

**Day periods are literally `AM` and `PM`** — Hebrew does not localise them. Which is itself a reason
to prefer 24-hour display: a 12-hour Hebrew clock renders an untranslated English abbreviation.

## Week data

**`weekData`, region `IL`:**

```
firstDay:      sun
weekendStart:  fri
weekendEnd:    sat
```

World default: `firstDay: mon`, weekend `sat`–`sun`.

**What this breaks if you get it wrong:**

- **Date pickers** — the columns are in the wrong order, and the weekend shading falls on the wrong
  days
- **Scheduling grids** — a week view starting Monday puts Sunday, a working day in Israel, at the far
  end
- **"This week" / "next week"** calculations — off by a day at the boundary
- **Business-days arithmetic** — "3 working days" spanning a Friday is wrong if you assumed the
  weekend was Saturday–Sunday
- **Weekly reports and cohorts** — week boundaries shift, so the numbers do not reconcile

**The weekend is Friday and Saturday**, and Friday is often a half day. Any picker built on a
"weekend is the last two columns" assumption breaks, because with a Sunday start, Friday and Saturday
*are* the last two — but with the world-default Monday start, they are not adjacent to the end.

## The Hebrew calendar

**`he/ca-hebrew.json`. Thirteen month slots:**

| Slot | Month |
|---|---|
| 1 | תשרי |
| 2 | חשוון |
| 3 | כסלו |
| 4 | טבת |
| 5 | שבט |
| 6 | אדר א׳ |
| **7** | **אדר** in a common year · **אדר ב׳** in a leap year |
| 8 | ניסן |
| 9 | אייר |
| 10 | סיוון |
| 11 | תמוז |
| 12 | אב |
| 13 | אלול |

**Slot 7 is the trap.** It is not a fixed month name — it changes with leap years, and the leap
pattern follows a 19-year Metonic cycle. Code that maps month index to name from a flat array is
wrong in 7 years out of every 19.

Single era: `לבריאת העולם`.

The calendar carries **`"_numbers": "hebr"`**, so **the year renders in Hebrew letter numerals**
(תשפ״ו), not digits.

**Do not implement conversion yourself.** Use `Intl.DateTimeFormat` with `calendar: 'hebrew'`, or the
platform's calendar support. The leap-month handling alone is not worth reimplementing, and the
religious-date calculations layered on top of it certainly are not.

## Arabic, for contrast

The reason "RTL" is not one thing:

| | Hebrew | Arabic |
|---|---|---|
| Plural categories | **3** — one, two, other | **6** — zero, one, two, few, many, other |
| Default digits | `latn` | `latn` in current CLDR — **verify against your ICU** |
| Script joining | None | **Cursive joining** — glyph shape depends on position |
| Decimal separator | `.` | `٫` `U+066B` under `arab` |
| Group separator | `,` | `٬` `U+066C` under `arab` |
| Minus | LRM + hyphen | Preceded by **ALM `؜` `U+061C`** under `arab` |
| Week start (primary region) | Sunday (IL) | Varies by country |

**Arabic plural rules:** `zero` (n=0), `one` (n=1), `two` (n=2), `few` (n%100 = 3..10), `many`
(n%100 = 11..99), `other`.

**Arabic is the maximal case; Hebrew is not.** Sizing plural handling for Arabic and applying it to
Hebrew produces four categories no translator will fill. Sizing it for Hebrew and applying it to
Arabic produces wrong strings.

## Version skew

**This is a real and teachable failure mode that nothing documents as such.**

`Intl.PluralRules` and `Intl.NumberFormat` output for `he` and `ar` **depends on the ICU version in
the runtime**. Node, browsers, and server JVMs all ship different ICU versions, and pinned-CLDR
libraries lag further.

A documented illustration: a widely used Go i18n package generated from **CLDR 32** still returns
`Many` for Hebrew at multiples of ten, against **CLDR 48** where that category no longer exists.
*(This specific claim is search-extracted and is offered as an illustration of skew, not as a
current statement about that library.)*

**Three defensive rules:**

1. **Never hardcode the plural category list.** Read it from the runtime.
2. **Tolerate unexpected categories.** Falling back to `other` for an unknown category is correct
   behaviour; throwing is not.
3. **Never assert an exact formatted string in a test.** Assert the category, assert the value round-
   trips, assert structure. `expect(fmt.format(1.5)).toBe('1.5 ₪')` will break on an ICU upgrade you
   did not make deliberately.

**Verify the numbering system against your runtime** rather than trusting any value written down:

```js
new Intl.NumberFormat('ar').resolvedOptions().numberingSystem
```
