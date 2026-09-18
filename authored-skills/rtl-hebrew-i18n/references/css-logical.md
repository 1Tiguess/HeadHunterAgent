# CSS logical properties

## Contents
- [The complete mapping](#the-complete-mapping)
- [Border radius: the two-axis scheme](#border-radius-the-two-axis-scheme)
- [Flow-relative keywords](#flow-relative-keywords)
- [The five gaps](#the-five-gaps)
- [:dir() versus attribute selectors](#dir-versus-attribute-selectors)
- [Migration order](#migration-order)

## The complete mapping

Two axes: **block** (the direction lines stack) and **inline** (the direction text flows). In a
horizontal RTL page, block is top-to-bottom and inline is right-to-left.

### Sizing

| Physical | Logical |
|---|---|
| `width` | `inline-size` |
| `height` | `block-size` |
| `min-width` | `min-inline-size` |
| `max-width` | `max-inline-size` |
| `min-height` | `min-block-size` |
| `max-height` | `max-block-size` |

### Margin, padding, inset

| Physical (LTR) | Logical |
|---|---|
| `margin-left` | `margin-inline-start` |
| `margin-right` | `margin-inline-end` |
| `margin-top` | `margin-block-start` |
| `margin-bottom` | `margin-block-end` |
| `padding-left` | `padding-inline-start` |
| `padding-right` | `padding-inline-end` |
| `left` | `inset-inline-start` |
| `right` | `inset-inline-end` |
| `top` | `inset-block-start` |
| `bottom` | `inset-block-end` |

Shorthands: `margin-inline: <start> <end>`, `margin-block:`, `padding-inline:`, `padding-block:`,
`inset-inline:`, `inset-block:`, and `inset:` for all four.

### Borders

All three sub-properties follow the same scheme:

| Physical (LTR) | Logical |
|---|---|
| `border-left` | `border-inline-start` |
| `border-left-width` | `border-inline-start-width` |
| `border-left-style` | `border-inline-start-style` |
| `border-left-color` | `border-inline-start-color` |
| `border-top` | `border-block-start` |

## Border radius: the two-axis scheme

**This is the one people get wrong**, because it does **not** use start/end the way everything else
does.

| Logical | Physical (LTR) | Physical (RTL) |
|---|---|---|
| `border-start-start-radius` | top-left | top-**right** |
| `border-start-end-radius` | top-right | top-**left** |
| `border-end-start-radius` | bottom-left | bottom-**right** |
| `border-end-end-radius` | bottom-right | bottom-**left** |

**Read it as: `border-<block>-<inline>-radius`.** First word is the block axis (start = top), second
is the inline axis (start = left in LTR, right in RTL).

**The mistake is reading the first `start` as "left".** That produces a corner in the wrong place in
*both* directions, which is worse than not converting at all — at least the physical version was
right in LTR.

```css
/* a card with rounded leading corners, correct in both directions */
.card {
  border-start-start-radius: 8px;   /* top-leading */
  border-end-start-radius:   8px;   /* bottom-leading */
}
```

## Flow-relative keywords

Some properties take logical **values** rather than having logical property names:

| Property | Logical values |
|---|---|
| `text-align` | `start`, `end` (instead of `left`, `right`) |
| `float` | `inline-start`, `inline-end` |
| `clear` | `inline-start`, `inline-end` |
| `caption-side` | `inline-start`, `inline-end` |
| `resize` | `block`, `inline` |

**`text-align: start` is the single highest-value one-line change** in most stylesheets. A physical
`text-align: left` is the most common RTL bug, and it is trivially fixable.

Flexbox and Grid are already flow-relative — `flex-start`, `flex-end`, `justify-content`,
`align-items` and grid line placement all follow direction automatically. **Anything built on Flexbox
or Grid is largely RTL-safe for free**, which is why the remaining bugs cluster in older
float-and-position code and in the five gaps below.

## The five gaps

**There is no logical form for these.** Naming the gap is more useful than implying logical
properties are total:

| Property | Why there is no logical form |
|---|---|
| `background-position` | Takes a physical coordinate pair |
| `box-shadow` offsets | Physical x/y offsets |
| `transform: translateX()` | Physical axis |
| Gradient angles (`linear-gradient(45deg, …)`) | Physical angle |
| `clip-path` | Physical coordinates |

Each needs an explicit override:

```css
.card {
  box-shadow: 4px 4px 12px rgb(0 0 0 / 0.15);
}
.card:dir(rtl) {
  box-shadow: -4px 4px 12px rgb(0 0 0 / 0.15);
}

.hero {
  background-position: left center;
}
.hero:dir(rtl) {
  background-position: right center;
}

.slide-in {
  transform: translateX(-100%);
}
.slide-in:dir(rtl) {
  transform: translateX(100%);
}

.banner {
  background: linear-gradient(90deg, var(--from), var(--to));
}
.banner:dir(rtl) {
  background: linear-gradient(270deg, var(--from), var(--to));
}
```

**A custom property makes the sign flip systematic** rather than per-rule:

```css
:root      { --dir: 1; }
:root:dir(rtl) { --dir: -1; }

.card { box-shadow: calc(4px * var(--dir)) 4px 12px rgb(0 0 0 / 0.15); }
.slide-in { transform: translateX(calc(-100% * var(--dir))); }
```

That scales better than an override per rule, and it means a new shadow written by someone who has
never thought about RTL is correct by default.

**The usual failure is a team converting everything to logical properties, believing they are
finished, and shipping a shadow that falls the wrong way.** Audit for these five specifically.

## :dir() versus attribute selectors

```css
.card:dir(rtl)      { }   /* prefer */
.card[dir="rtl"]    { }   /* fallback */
[dir="rtl"] .card   { }   /* common, and the most fragile */
```

**`:dir()` follows the computed direction**, including direction inherited from an ancestor and
direction resolved by `dir="auto"`. An attribute selector matches only elements that literally carry
the attribute, so:

- `[dir="rtl"] .card` fails when the card is inside an LTR island inside an RTL page
- Neither attribute form sees a direction resolved by `dir="auto"` on user-generated content
- `[dir="rtl"] .card` has higher specificity than `.card`, which creates override ordering problems
  as the stylesheet grows

Where `:dir()` support is insufficient, use the attribute form **on the element itself**
(`.card[dir="rtl"]`) rather than as an ancestor selector, so specificity stays predictable.

## Migration order

Converting an existing stylesheet, highest value first:

1. **`text-align: left|right` → `start|end`.** Most common bug, one-line fix.
2. **`margin-left|right`, `padding-left|right` → inline start/end.** Mechanical, and safe to
   automate.
3. **`left`/`right` on positioned elements → `inset-inline-start|end`.** Watch for elements that are
   genuinely physical, like a scroll-to-top button pinned to a fixed corner.
4. **`float`/`clear` → `inline-start|end`.**
5. **`border-left|right` → `border-inline-start|end`.**
6. **Border radius → the two-axis names.** Do this deliberately, not with find-and-replace — the
   mapping is not a rename.
7. **The five gaps → `:dir(rtl)` overrides or a `--dir` multiplier.** Manual. This is where the
   remaining bugs live once steps 1–6 are done.

**Steps 1–5 are safely automatable. Steps 6 and 7 are not**, and that is where to spend review time.
