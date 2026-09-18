# Testing RTL and Hebrew

Two families of check exist in the published tooling and **neither knows about the other**: structural
invariants give geometry with no content stress; pseudo-locales give content stress with no geometry.
This is the combined recipe.

## Contents
- [Structural invariants](#structural-invariants)
- [The gating rule](#the-gating-rule)
- [Content stress with pseudo-locales](#content-stress-with-pseudo-locales)
- [What never to assert](#what-never-to-assert)
- [What to assert instead](#what-to-assert-instead)
- [Manual checks](#manual-checks)
- [A minimum viable suite](#a-minimum-viable-suite)

## Structural invariants

Automatable checks, each catching a real class of bug:

| Invariant | Catches |
|---|---|
| No computed `text-align: left` or `right` on text-bearing elements under RTL | The most common RTL bug |
| No one-sided border — a `border-left` with no RTL counterpart | Physical borders that did not get converted |
| No one-sided padding or margin asymmetry that does not flip | Physical spacing |
| Directional icons carry `scaleX(-1)` under RTL | Unmirrored arrows and chevrons |
| **Anchored popups stay inside the viewport after the anchor side flips** | Menus and tooltips clipping off-screen |
| No horizontal scroll at any tested width | Overflow from a flipped layout |
| Focus order matches visual order | Tab sequence following DOM rather than reading order |

**The popup one is the most valuable and the least obvious.** A dropdown anchored to the right edge
of its trigger in LTR is anchored to the left edge in RTL — and if the positioning logic was written
with a physical assumption, it opens off the side of the screen. It only shows up at particular
viewport widths, so it survives casual manual testing.

## The gating rule

> **Gate every check on elements containing Hebrew or Arabic characters.**

Without this, every check fires on the **intentional** LTR islands — code blocks, URLs, phone
numbers, version strings, product names — and the noise makes the suite unusable within a week.

```js
const RTL_CHARS = /[֐-׿؀-ۿ܀-ݏހ-޿]/;

function shouldCheck(el) {
  const text = el.textContent ?? '';
  return RTL_CHARS.test(text);
}
```

An element whose text is entirely Latin inside an RTL page is either an intentional island or an
untranslated string. **Both are worth knowing about, but they are a different report** — flagging
them as direction bugs buries the real ones.

## Content stress with pseudo-locales

A generated locale that transforms every string without needing a translation. Three transformations,
each catching something different:

| Transformation | Catches |
|---|---|
| **Wrap in RLM…RLM** or force RTL | Direction bugs, without needing Hebrew content |
| **Pad length by 30–40%** | Truncation, overflow, fixed-width containers |
| **Add accents or brackets** (`[!!! Ĥéļļö !!!]`) | **Hardcoded strings that escaped translation** |

The third is the one that pays for the whole exercise: **any string still rendering in plain English
was never externalised.** Nothing else finds those as reliably.

```js
function pseudo(s) {
  const padded = s + '·'.repeat(Math.ceil(s.length * 0.35));
  return '‏[' + padded + ']‏';
}
```

Run the app under the pseudo-locale and screenshot every screen. Truncation, overflow and untranslated
strings are all visible at a glance.

## What never to assert

> **Never assert an exact formatted string.**

`Intl.PluralRules`, `Intl.NumberFormat` and `Intl.DateTimeFormat` output for `he` and `ar` depends on
**the ICU version in the runtime**, which differs between Node versions, browsers, CI images and
production. It moves without your involvement.

```js
// BRITTLE — breaks on an ICU upgrade nobody made deliberately
expect(fmt.format(1234.5)).toBe('1,234.5 ₪');
expect(dateFmt.format(d)).toBe('17.9.2026');
expect(pr.select(10)).toBe('other');          // Hebrew's `many` was removed; older ICU says otherwise
```

Also never assert:

- The presence or absence of a specific invisible control character in formatted output — the
  currency pattern's RLM placement is ICU's business
- Month or day names — they are translated data
- The exact set of plural categories a locale has

## What to assert instead

**Structure, round-trips and invariants:**

```js
// the category the runtime actually has, not one you hardcoded
const cats = new Intl.PluralRules('he').resolvedOptions().pluralCategories;
expect(cats).toContain('two');                 // Hebrew has `two`; this is stable
expect(catalogKeysFor('he')).toEqual(expect.arrayContaining(cats));

// round-trip rather than exact output
const formatted = fmt.format(1234.5);
expect(parseLocaleNumber(formatted, 'he')).toBeCloseTo(1234.5);

// the fact that matters, not its rendering
expect(getWeekStart('IL')).toBe('sun');
expect(getWeekend('IL')).toEqual(['fri', 'sat']);

// digits, without asserting the whole string
expect(fmt.format(5)).toMatch(/[0-9]/);        // Hebrew uses latn
expect(fmt.format(5)).not.toMatch(/[٠-٩]/);

// isolation is present at plain-text boundaries
expect(buildTitle('דוח', 'report-v2.pdf')).toContain('⁨');
```

**Catalog completeness** is the highest-value assertion in this list: for every locale, the catalog
must have an entry for every plural category the runtime reports. That single test catches both the
missing-`two` bug and the stale-`many` bug, and it keeps working across ICU upgrades because it reads
the categories rather than hardcoding them.

## Manual checks

Some things are faster to eyeball than to automate.

**Force RTL without changing the language:**

- Firefox: `about:config` → `intl.uidirection` = `1`
- Or set `<html dir="rtl">` in devtools with the language unchanged

That separates *direction* bugs from *translation* bugs, which is otherwise hard — a Hebrew build
shows both at once and you cannot tell which you are looking at.

**The five-minute pass, in order:**

1. Force RTL. Does anything overflow horizontally?
2. Open every dropdown, menu and tooltip near the **right** edge. Anything clipped?
3. Tab through a form. Does focus move in reading order?
4. Find a string with an interpolated name, URL or number. Is it isolated?
5. Open a date picker. **Does the week start on Sunday, with Friday and Saturday marked as the
   weekend?**
6. Check a password field and a phone number field. Are they LTR?
7. Print or export one page. Does the export preserve direction?

**Step 5 is the fastest Hebrew-specific check available** and it fails more often than any other item
on the list, because date pickers are usually third-party and usually assume a Monday-or-Sunday
binary.

## A minimum viable suite

If you do nothing else:

1. **A catalog-completeness test** — every plural category the runtime reports has an entry, for every
   locale. Catches missing `two` and stale `many`.
2. **A pseudo-locale screenshot pass** over the main screens. Catches truncation and unexternalised
   strings.
3. **A structural check for physical `text-align`** under RTL. Catches the most common bug.
4. **A manual five-minute pass** per release, following the list above.

Those four take an afternoon to set up and catch the overwhelming majority of what actually ships
broken.
