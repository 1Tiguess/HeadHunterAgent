# WCAG thresholds

Load when setting token values or building the contrast validator.

**Cite the normative success-criterion text, not the Understanding pages.** The Understanding
documents are explanatory and their cross-references between related criteria read
ambiguously — during authoring they produced two wrong conformance levels that had to be
corrected against the normative source.

## Contents

- [Conformance levels at a glance](#conformance-levels-at-a-glance)
- [Text contrast](#text-contrast)
- [Non-text contrast](#non-text-contrast)
- [Focus not obscured](#focus-not-obscured)
- [Focus appearance](#focus-appearance)
- [Target size](#target-size)
- [What the two focus criteria measure differently](#what-the-two-focus-criteria-measure-differently)

## Conformance levels at a glance

| Criterion | Name | Level |
|---|---|---|
| 1.4.3 | Contrast (Minimum) | AA |
| 1.4.6 | Contrast (Enhanced) | AAA |
| 1.4.11 | Non-text Contrast | AA |
| 2.4.11 | Focus Not Obscured (Minimum) | **AA** |
| 2.4.12 | Focus Not Obscured (Enhanced) | AAA |
| 2.4.13 | Focus Appearance | **AAA** |
| 2.5.8 | Target Size (Minimum) | **AA** |

The three in bold are the ones commonly misreported. Target Size (Minimum) is **AA**, not AAA.

## Text contrast

**1.4.3, AA.** 4.5:1 for normal text. 3:1 for large text, where large means 18pt or 14pt bold
— roughly 24px and 18.66px at default sizing.

Exempt: incidental or decorative text, logotypes, and **user interface components that are not
available for interaction** (disabled controls).

The Understanding material notes that very thin or unusual typefaces may need more than the
nominal ratio to be equally legible. If your type scale includes a light weight at small
sizes, treat the nominal ratio as a floor rather than a target.

**1.4.6, AAA** raises normal text to 7:1 and large text to 4.5:1. Your high-contrast theme
should target this.

## Non-text contrast

**1.4.11, AA.** 3:1 for:

1. Visual information required to identify a **user interface component and its states**
2. Graphical objects required to understand the content

**This is the criterion that catches design systems**, because it covers exactly the parts
people treat as decoration:

- input and select borders
- checkbox ticks and boxes
- switch tracks and thumbs
- radio rings and dots
- focus indicators
- icon-only button glyphs
- the boundary of a card or menu, where that boundary is what makes it identifiable

**Values must not be rounded. 2.999:1 fails.** Build this into your validator; do not compute
a ratio, round to one decimal, and compare.

Exempt: disabled components, and indicators the author has not modified from the browser
default. Hover states are treated as supplemental and do not independently need 3:1 — *unless*
hovering destroys contrast that was present.

## Focus not obscured

**2.4.11, AA.** When a component receives keyboard focus it must not be **entirely** hidden by
author-created content.

Named failure modes, all common in component libraries:

- sticky headers and footers
- non-modal overlays and popovers
- cookie and consent banners

Passing strategies: `scroll-padding` sized to the sticky region so scroll-into-view accounts
for it; layouts that displace content rather than overlaying it; making overlays dismissible
with Escape.

**2.4.12, AAA** requires that **no part** be obscured.

## Focus appearance

**2.4.13, AAA.** Two requirements together:

1. The focus indicator has an area **at least equal to a 2 CSS px thick perimeter of the
   unfocused component**.
2. There is a **3:1 contrast ratio between the same pixels in the focused and unfocused
   states**.

Exempt when the indicator is determined by the user agent and not adjustable by the author, or
when neither the indicator nor its background has been modified. Note that changing the
background colour re-arms the requirement.

## Target size

**2.5.8, AA.** 24×24 CSS px, with five exceptions: Spacing, Equivalent, Inline, User Agent
Control, Essential.

**The spacing exception has a precise test:** draw a 24px-diameter circle centred on the
bounding box of each undersized target. It passes if that circle intersects neither another
target nor another undersized target's circle. This is what permits dense toolbars of small
icons provided they are adequately separated — but "adequately" is this test, not judgement.

## What the two focus criteria measure differently

Worth being explicit, because conflating them produces a focus ring that passes one and fails
the other while everyone assumes it is fine.

| | Non-text contrast (1.4.11) | Focus appearance (2.4.13) |
|---|---|---|
| Compares | The indicator against **adjacent colours** | The **same pixels** in focused vs unfocused states |
| Question | Can I see the ring against its surroundings? | Can I tell that something changed? |
| Fails when | The ring is low-contrast against the background | The ring is similar to whatever it replaced |

Both can apply at once. A ring that is high-contrast against the page but nearly identical to
the component's resting border passes the first and fails the second.

**This is why the focus ring is a relationship between two token values, not a single token** —
and why it must be validated per theme. A ring derived from the same primitive as the resting
border will tend to fail the second test in whichever theme brings those two values closest
together.
