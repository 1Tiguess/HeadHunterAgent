# Build instructions: design-token-systems

**Status:** draft
**Target:** `.claude/skills/design-token-systems/SKILL.md` (project)
**Serves:** plan 10 "Sable" — a design system and component library for four products
**Hunt notes:** `.headhunter/hunts/sable-notes.md`

## Capability gap

Claude builds component libraries as a folder of components with hardcoded values and no token
layer beneath them, so theming becomes find-and-replace and a semantic colour drifts between
components; and it treats accessibility as ARIA attributes added at the end rather than focus
management and keyboard contracts designed in, producing overlays that trap or lose focus and
widgets that pass a visual glance and fail a screen reader.

## References studied

| Source | URL / path | What it contributes | Tried to instruct? |
|---|---|---|---|
| Skills best practices | `docs.claude.com/…/agent-skills/best-practices` | Reference depth as a mechanical constraint; **checklists copied into the reply as visible working state**; validator loops | no |
| `frontend-design` | `/mnt/skills/public/frontend-design/` | Two-pass process (plan, then critique the plan before code); **naming its own failure mode concretely**; deference to the brief | no |
| `theme-factory` | `/mnt/skills/examples/theme-factory/` | Domain-partitioned references (one file per theme); a **named blocking confirmation step** | no |
| `mcp-builder`, `skill-creator` | `/mnt/skills/examples/` | Load-order-annotated reference index; directory contract; "Principle of Lack of Surprise" | no |
| Material Web shipped tokens | `github.com/material-components/material-web` `tokens/_md-sys-color.scss`, `_md-comp-filled-button.scss` | Three namespaces, strictly one-way; **theming as a function swap**; the `on-X` pairing convention | no |
| CSS Cascade 5 | `github.com/w3c/csswg-drafts` | Layers sort **before** specificity; unlayered wins; `!important` inverts the order | no |
| MDN custom properties / `@property` | via domain-restricted search | Registered properties change the *failure mode* — fallback is never consulted | no |
| ARIA APG patterns | `github.com/w3c/aria-practices` | Per-widget keyboard and focus contracts; roving tabindex vs `aria-activedescendant` | no |
| WCAG 2.2 normative SC | `github.com/w3c/wcag` | 1.4.3, 1.4.11, 2.4.11, 2.4.13, 2.5.8 thresholds and their exact scope | no |
| axe-core rule catalogue | `github.com/dequelabs/axe-core` | What the standard tooling does and does **not** check | no |

Read-only. Nothing downloaded, cloned, or installed. `w3.org`, `developer.mozilla.org`,
`m3.material.io`, `open-ui.org` and `html.spec.whatwg.org` were egress-blocked; W3C material was
read at the **same organisation's canonical source repositories**, which are the files the
published pages are generated from. **Open UI and Material 3 prose could not be read** — see Risk
review.

## Improvements over the references

- **Enforce the one-way dependency graph as a lint rule, not a convention.** The "danger colour
  drifts" symptom is a component reaching past its semantic layer to a primitive, and that is
  statically detectable: resolve each `var()` chain in the emitted CSS and fail any component-layer
  declaration terminating in a primitive. No source proposes checking this.
- **Contrast-check the token graph, not the rendered page.** Because every background-role token
  ships with its bound foreground, contrast becomes **enumerable over token pairs** — cheap,
  exhaustive across all themes, and it catches drift *before a component exists*. Every source
  assumes contrast testing happens on a rendered page.
- **Publish the third theme.** Every source treats theming as light/dark. High-contrast is not "dark
  with more contrast": it **collapses the surface-elevation stack** (graded surface tokens lose
  meaning when everything must clear a higher ratio) and forces borders onto components that relied
  on fill contrast. Nothing found addresses this. We also name `forced-colors` mode — the fourth
  theme you do not control, where the OS bypasses your token layer entirely.
- **Argue the layer count instead of copying it.** Material shows three layers and no source
  justifies three over two. Its component layer does two different jobs — genuine per-component
  values and pure pass-throughs — and only the first earns its keep. We give the test for when a
  component token is justified.
- **Make token names computable rather than memorable.** Material's semantic layer conflates role,
  prominence and pairing in one flat namespace of 48 strings, with no rule for generating the next
  name — which is precisely what "survives growth" means. We specify orthogonal axes so a name is
  derived. Multi-brand is absent from every source and Sable serves four products.
- **Teach the whole cascade-layer mechanism, including the inversion.** A system inside layers is
  un-fightable by selector escalation but *trivially* overridable by any unlayered rule — a feature
  for four consuming teams, **provided it is a stated contract rather than a surprise**. And
  `!important` inverts the entire ordering. Teaching layers without the inversion teaches half a
  mechanism.
- **State axe's blind spots plainly, because its defaults are misleading here.**
  `color-contrast-enhanced` is **disabled by default**; contrast returns *incomplete* on gradients,
  images and overlapping stacking contexts, so a gate asserting only on `violations` passes them
  silently; and **there is no axe rule for 1.4.11, 2.4.13 or 2.4.11** — precisely the criteria this
  project is built around.
- **Generate keyboard conformance tests from the APG contracts.** The APG specifies each state
  machine precisely enough to be a test oracle, and nobody has written that down as a harness.
- **Bring engineering-skill discipline to design subject matter.** The rigorous patterns — numbered
  phases, annotated load order, validator loops, evals as deliverable — live in `mcp-builder` and
  `skill-creator`, not in the design skills. `frontend-design` gives accessibility a single
  unelaborated clause; `theme-factory` treats a theme as a flat hex list with "ensure proper
  contrast" left unverified.
- **Deliberately left out: chart colour and chart accessibility** — `dataviz` owns that territory
  and duplicating it would make both skills trigger ambiguously. Also left out: aesthetic direction
  and typography voice, which `frontend-design` covers.

## The skill to build

### Frontmatter
- `name:` design-token-systems
- `description:` Builds component libraries on a token architecture that survives growth and
  theming, with keyboard and focus contracts designed in rather than retrofitted. Use when starting
  a design system or component library, adding a themeable component, introducing dark or
  high-contrast mode, refactoring hardcoded values into tokens, or when a semantic colour has
  drifted between components, a modal or popover mishandles focus, or contrast fails in one theme
  but not another.
- `allowed-tools:` Read, Write, Edit, Glob, Grep, Bash

### Body structure
1. **Decide the token architecture before any component exists** — layers, axes, naming
2. **Theming is a function swap** — and the third theme changes the rules
3. **Cascade layers** — override authority, and the two traps
4. **The keyboard contract is a state machine** — ARIA is the reporting layer
5. **Per-widget contracts** — routed to reference files
6. **The visual contract** — where tokens and accessibility actually meet
7. **Validate** — token-graph contrast, `var()` chain lint, generated keyboard tests
8. **Refusals** — what this skill will not build

### The technique it encodes

**Token architecture.** Three namespaces with a **strictly one-way** dependency direction:
primitives (raw values, referenced by nothing in the UI) → semantics (roles) → components. Nothing
skips a level or points sideways. A component token is justified only when it carries a genuine
per-component value that no semantic token expresses — a pass-through to a semantic token is not a
justification, and for a dozen components the pass-through tax can exceed the benefit.

Make names **computed, not remembered**, by keeping the axes orthogonal: role (primary, danger,
success), prominence (base, container, subtle), pairing (the `on-` foreground bound to each
background role), and state (hover, active, disabled). Every background-role token ships with its
bound foreground so "what colour is text here" is a lookup rather than a judgement. For multiple
brands, brand varies the primitive layer only; semantics and components must not know which brand
is active.

Emit each token as a custom property with the resolved value as its fallback, so an unthemed page
still renders. Note the sharp edge: if a property is registered via `@property` with a non-universal
syntax and an initial value, an invalid computed value substitutes **that registered initial and the
fallback is never consulted** — so registration changes your failure mode, not just animatability.

**Theming.** Light, dark and high-contrast are **the same key set produced by different functions**
from the same primitives. The component layer is untouched by theme. High-contrast is not dark with
more contrast: it collapses the graded surface stack, because elevation-by-tint stops being
distinguishable once everything must clear the higher ratio, and it forces explicit borders onto
components that relied on fill contrast alone. Say what happens under `forced-colors`, where the OS
overrides colours entirely and the token layer is bypassed.

**Cascade layers.** Layers are evaluated **before specificity** in the cascade, so a one-class
selector in a higher layer beats a five-class selector in a lower one and specificity only arbitrates
within a layer. Two traps: **unlayered rules sort after all layered rules**, so anything a consuming
team writes outside a layer wins over everything the system ships — state this as a deliberate
contract; and `!important` **inverts the whole ordering**, with earlier layers winning and unlayered
important declarations losing to layered ones. Import with `layer()` so the order is fixed even if a
stylesheet fails to load.

**The keyboard contract.** A composite widget contributes **exactly one stop to the tab sequence**.
Tab moves between components; arrows, Home/End and typeahead move within one. Choose roving tabindex
(DOM focus genuinely moves, so the browser scrolls it into view for free) or `aria-activedescendant`
(focus stays on the container — **you must scroll the active option into view yourself**). Never use
a positive `tabindex`; reorder the DOM instead, since DOM order is also reading order. ARIA
attributes *report* a state machine you have already built — which is exactly why adding them last
produces widgets that read correctly and behave wrongly.

Initial focus is a **decision, not "the first focusable thing"**: land the user before long content
via a `tabindex="-1"` anchor; focus a static element such as the title when focusing a control would
scroll the dialog; and on a destructive confirmation focus the **least destructive** action. On
close, return focus to the invoker unless it no longer exists.

**The visual contract.** This is where tokens and accessibility meet. Text needs 4.5:1 (3:1 at large
sizes). **Non-text contrast needs 3:1 on the visual information identifying a component *and its
states*** — input borders, checkbox ticks, switch tracks, focus rings, icon-only buttons — and values
must not be rounded, so 2.999:1 fails. A focused component must not be **entirely** hidden by sticky
headers, popovers or cookie banners. And focus appearance is measured as a **3:1 ratio between the
same pixels in focused and unfocused states** — a change-of-state ratio, not adjacency, which is a
different test from non-text contrast and can pass one while failing the other. So **the focus ring is
not one token but a relationship between two token values**, and it must hold in every theme
independently. Interactive targets need 24×24 CSS px, or the spacing exception.

**Validation.** Three checks, run as a loop until clean:
1. **`var()` chain lint** — resolve every chain in the emitted CSS; fail any component-layer
   declaration terminating in a primitive.
2. **Token-graph contrast** — enumerate every background/foreground token pair in every theme and
   assert the applicable ratio. Cheap, exhaustive, and runs before any component exists.
3. **Generated keyboard tests** — derive per-pattern assertions from the widget contracts: send Tab
   and assert `document.activeElement`; send Escape and assert focus returned to the invoker; send
   ArrowRight and assert exactly one `tabindex="0"` remains in the composite.

On automated tooling, state plainly: the enhanced-contrast rule is **off by default**; contrast checks
return *incomplete* rather than pass or fail on gradients, images and overlapping stacking contexts,
so **a gate that asserts only on violations silently passes them**; and no standard rule covers
non-text contrast, focus appearance, or focus obscuring. Those need the token-graph check and
screenshot-based comparison instead.

**Refusals.** Refuse to build a tooltip containing focusable content — that is a non-modal dialog, and
the tooltip pattern itself is explicitly not settled. Refuse to mark a dialog modal unless code
actually prevents outside interaction **and** styling visually obscures the outside. Refuse to ship a
theme whose token pairs have not passed the contrast enumeration.

### Reference files
One level deep, each with a table of contents. Named at point of use and again in a closing index
annotated with when to load each:
- `references/patterns-overlay.md` — dialog, popover, tooltip.
- `references/patterns-selection.md` — listbox, combobox, tabs.
- `references/patterns-input.md` — checkbox, switch, form field wrapper.
- `references/wcag-thresholds.md` — the criteria, quoted from the normative SC files with their
  exact scope and exclusions.

## How to tell it worked

- [ ] Changing one semantic token updates every component that should change and nothing else
- [ ] No component-layer declaration resolves to a primitive — verified by the chain lint
- [ ] Every background/foreground token pair passes its ratio in all three themes — verified by
      enumeration, not by inspection
- [ ] The focus ring passes both the non-text-contrast test and the focused-vs-unfocused test, in
      every theme
- [ ] Every interactive component is fully operable by keyboard, and each composite widget occupies
      exactly one tab stop
- [ ] Modal and popover return focus to the invoker on close
- [ ] Adding a new component requires touching no existing component
- [ ] The CI gate fails on axe *incomplete* results, not only on violations

## Risk review

**None adversarial.** No source attempted to induce a fetch, install, execution, persona change,
exfiltration, or rule override. The blocked domains returned proxy errors, not adversarial content.

Three items worth recording:

1. **Open UI and Material 3 prose could not be read.** Material's token architecture was inferred
   from its **shipped SCSS** rather than its documentation, which is arguably better evidence but
   means the stated rationale is unread. Component anatomy and state naming from Open UI is simply
   absent — a real hole.
2. **One consequential fact could not be verified: whether an auto popover returns focus to its
   invoker on light-dismiss.** The relevant spec was unreachable. **Pin this before writing anything
   about popover focus return**; the skill should mark it explicitly unverified until checked.
3. **A factual correction to carry forward.** WCAG's Understanding pages read ambiguously on
   conformance levels here. Checked against the normative SC files: **Target Size (Minimum) is Level
   AA**, Focus Appearance is **AAA**, and Focus Not Obscured (Minimum) is **AA**. The skill must cite
   the normative SC files, not the Understanding pages.

## Originality attestation

- [x] Nothing was downloaded, cloned, or installed
- [x] No code or prose was copied verbatim from a source
- [x] Every technique is restated in my own words
- [x] Sources are listed above as references, credited where their idea is distinctive
- [x] Any injection attempt is recorded in the Risk review

## Build steps

1. Create `.claude/skills/design-token-systems/SKILL.md`
2. Write frontmatter as specified
3. Write sections 1–8 as specified, body under 500 lines
4. Create the four `references/` files, each one level deep and each opening with a table of contents
5. Add a closing index annotating when to load each reference
6. Mark the popover focus-return behaviour as unverified pending a primary-source check
7. Read the authored file back into context
