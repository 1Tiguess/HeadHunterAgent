---
name: design-token-systems
description: >-
  Builds component libraries on a token architecture that survives growth and theming, with
  keyboard and focus contracts designed in rather than retrofitted. Use when starting a
  design system or component library, adding a themeable component, introducing dark or
  high-contrast mode, refactoring hardcoded colours and spacing into tokens, or when a
  semantic colour has drifted between components, a modal or popover or menu mishandles
  focus, keyboard navigation is broken in a composite widget, or contrast passes in one
  theme and fails in another.
allowed-tools: Read, Write, Edit, Glob, Grep, Bash
---

# Design token systems

Two failures travel together and have the same root: values chosen where they are used
rather than where they are defined.

A component library with hardcoded values has no theming story, so theming becomes
find-and-replace and "danger" drifts to three different reds. A component with ARIA added at
the end has no keyboard story, so overlays trap or lose focus and widgets read correctly to a
screen reader while behaving wrongly.

Decide both architectures before the first component exists.

*Scope note: chart colour and chart accessibility belong to `dataviz`; aesthetic direction and
typographic voice belong to `frontend-design`. This skill is the structural layer beneath
both.*

## 1 — Token architecture

Three namespaces, dependency direction **strictly one-way**:

```
primitives  →  semantics  →  components
```

- **Primitives** — raw values. A colour ramp, a spacing scale, a type scale. **Nothing in the
  UI references these directly.**
- **Semantics** — roles. `danger`, `danger-container`, `on-danger`, `surface`, `outline`.
  This is the layer components speak.
- **Components** — per-component values that no semantic token expresses.

Nothing skips a level. Nothing points sideways. **A component reaching past its semantic layer
to a primitive is exactly the "colour drifted" bug**, and §7 shows how to detect it
mechanically.

**A component token is justified only when it carries a genuine per-component value** — a
control's specific inset, a component-only elevation. A component token that merely passes
through to a semantic token is overhead: it doubles the indirection and adds a name to
remember for no expressive gain. Published systems ship a full component layer because they
have hundreds of components; at a dozen, the pass-through tax likely exceeds the benefit. Add
component tokens where they earn it, not uniformly.

**Make names computed, not remembered.** Keep the axes orthogonal:

| Axis | Values |
|---|---|
| Role | `primary`, `danger`, `success`, `warning`, `neutral` |
| Prominence | `base`, `container`, `subtle` |
| Pairing | `on-` prefix for the foreground bound to a background role |
| State | `hover`, `active`, `disabled`, `focus` |

`--color-danger-container` and `--color-on-danger-container` are then *derivable* rather than
looked up — which is what "survives growth" actually means. Published systems that enumerate
48 flat names conflate role, prominence and pairing in one namespace and give no rule for
generating the next one.

**Every background-role token ships with its bound foreground.** This makes "what colour is
text here" a lookup rather than a judgement, and — see §7 — it is what makes contrast checking
enumerable rather than requiring a rendered page.

**For multiple brands, brand varies the primitive layer only.** Semantics and components must
not know which brand is active.

Emit each token as a custom property with the resolved value as its fallback, so an unthemed
page still renders.

> Sharp edge: if you register a custom property with `@property` using a non-universal syntax
> and an initial value, then an invalid computed value substitutes **that registered initial
> and the `var()` fallback is never consulted**. Registration changes your failure mode, not
> just animatability. Know which you want.

## 2 — Theming is a function swap

Light, dark and high-contrast are **the same key set produced by different mappings** from the
same primitives. The component layer is untouched by theme. If a theme change requires editing
a component, the architecture has already failed.

**High-contrast is not "dark with more contrast".** It has different structure:

- It **collapses the surface-elevation stack.** Elevation expressed as tint stops being
  distinguishable once every surface must clear a higher ratio against its foreground. Graded
  surface tokens lose their meaning.
- It **forces explicit borders** onto components that relied on fill contrast alone to be
  identifiable.

Plan for that rather than generating it from the dark palette.

**Say what happens under `forced-colors`.** That is the fourth theme, and you do not control
it — the OS replaces your colours entirely and your token layer is bypassed. At minimum,
ensure nothing becomes invisible and that borders you rely on are actual borders rather than
background tricks.

## 3 — Cascade layers

Layers are evaluated **before specificity** in the cascade. A one-class selector in a higher
layer beats a five-class selector in a lower one; specificity only arbitrates *within* a
layer. This is what makes specificity wars structurally impossible rather than merely
discouraged.

Two traps, and teaching layers without them teaches half a mechanism:

1. **Unlayered rules sort after all layered rules.** Anything a consuming team writes outside
   a layer beats everything your system ships, regardless of specificity. For a shared system
   across several products this is a *feature* — product overrides need no `!important` — but
   only if you **state it as a contract** rather than let teams discover it.
2. **`!important` inverts the entire ordering.** Important declarations in *earlier* layers
   win over later ones, and unlayered important declarations *lose* to layered ones. Anyone
   reaching for `!important` to force an override will get the opposite of what they expect.

Import with `layer()` so layer order is fixed even if a stylesheet fails to load. Use anonymous
layers for internals you do not want consumers targeting, and named layers for the slots you
intend them to use.

## 4 — The keyboard contract is a state machine

**A composite widget contributes exactly one stop to the tab sequence.** Tab moves *between*
components; arrows, Home/End and typeahead move *within* one. Tabs, listbox, radio group, menu
and grid are all instances of this.

Two implementations:

| | Roving tabindex | `aria-activedescendant` |
|---|---|---|
| Focus | Genuinely moves between children | Stays on the container |
| Mechanism | One child `tabindex="0"`, siblings `-1`; flip on arrow and call `.focus()` | Container points at the active child's id |
| Scroll into view | Free — the browser does it | **You must do it yourself** |

**Never use a positive `tabindex`.** Reorder the DOM instead — DOM order is also screen-reader
reading order, so fixing one fixes both.

**ARIA attributes report a state machine you have already built.** That is exactly why adding
them last produces widgets that read correctly and behave wrongly: the attributes describe
focus behaviour that was never implemented.

**Initial focus is a decision, not "the first focusable thing":**

- Content that is a list, table or prose → put `tabindex="-1"` on a static element at the start
  so the user lands *before* the content.
- Focusing the first control would scroll the container → focus a static element such as the
  title.
- **Destructive confirmation → focus the least destructive action.**
- Otherwise → the most-used control.

On close, return focus to the invoking element, unless it no longer exists or workflow
dictates otherwise.

## 5 — Per-widget contracts

Routed to reference files so the body stays scannable. Load the one you need:

| File | Covers |
|---|---|
| `references/patterns-overlay.md` | Dialog, popover, tooltip |
| `references/patterns-selection.md` | Listbox, combobox, tabs |
| `references/patterns-input.md` | Checkbox, switch, form field |
| `references/wcag-thresholds.md` | The criteria, with exact scope and exclusions |

## 6 — The visual contract

Where tokens and accessibility actually meet.

- **Text**: 4.5:1, or 3:1 at large sizes (18pt, or 14pt bold).
- **Non-text**: 3:1 on the visual information identifying a component **and its states** —
  input borders, checkbox ticks, switch tracks, focus rings, icon-only buttons. **Values are
  not rounded: 2.999:1 fails.**
- **Focus must not be entirely obscured** by sticky headers, popovers or banners.
- **Focus appearance** is measured as 3:1 between the **same pixels in focused and unfocused
  states** — a change-of-state ratio, not adjacency. This is a *different test* from non-text
  contrast, and an indicator can pass one while failing the other.
- **Targets**: 24×24 CSS px, or the spacing exception.

The consequence worth internalising: **the focus ring is not one token but a relationship
between two token values**, and that relationship must hold in every theme independently.

## 7 — Validate

Three checks, run as a loop until clean. Do not advance while any fails.

1. **`var()` chain lint.** Resolve every custom-property chain in the emitted CSS. **Fail any
   component-layer declaration whose chain terminates in a primitive.** This catches the
   drift bug structurally rather than by review.
2. **Token-graph contrast.** Enumerate every background/foreground token pair in every theme
   and assert the applicable ratio. Because pairing is encoded in the token names, this is a
   pure data check — **cheap, exhaustive across all themes, and it runs before any component
   exists**. Rendered-page checking cannot give you that.
3. **Generated keyboard tests.** The per-widget contracts are precise enough to be a test
   oracle. Send Tab and assert `document.activeElement`; send Escape and assert focus returned
   to the invoker; send ArrowRight and assert exactly one `tabindex="0"` remains in the
   composite.

**Know what standard tooling does not check.** Three traps:

- The enhanced-contrast rule is **disabled by default**. A run that "passes" has not checked
  the higher threshold at all.
- Contrast checks return **incomplete** — neither pass nor fail — on gradients, background
  images, and overlapping stacking contexts. **A CI gate asserting only on violations silently
  passes every one of them.** Fail on incomplete too.
- There is **no rule for non-text contrast, focus appearance, or focus obscuring** — precisely
  the criteria a design system lives or dies by. Check 1 and 2 above, plus screenshot
  comparison for focus appearance, are what cover them.

## 8 — Refusals

- **Refuse to build a tooltip containing focusable content.** A tooltip can never receive
  focus. If it needs a link or a button it is a non-modal dialog. (The tooltip pattern itself
  is explicitly not settled guidance — treat anything built on it as provisional.)
- **Refuse to mark a dialog modal** unless code actually prevents interaction outside it
  **and** styling visually obscures the outside. Both, not either.
- **Refuse to ship a theme** whose token pairs have not passed the contrast enumeration.

## Done means

- Changing one semantic token updates everything that should change and nothing else
- No component-layer declaration resolves to a primitive — verified by the chain lint
- Every background/foreground pair passes its ratio in all themes — verified by enumeration
- The focus ring passes both the non-text-contrast and focused-vs-unfocused tests, per theme
- Every interactive component is keyboard operable, and each composite occupies one tab stop
- Modal and popover return focus to the invoker on close
- Adding a component requires touching no existing component
- The CI gate fails on incomplete results, not only on violations
