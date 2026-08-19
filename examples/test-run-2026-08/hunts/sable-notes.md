# Hunt notes — 10 Sable (design system: tokens + accessibility)

Scout report, reported speech. Read-only. Nothing downloaded, cloned, or installed.

## Access note

The egress proxy blocked `w3.org`, `developer.mozilla.org`, `m3.material.io`, `open-ui.org`
and `html.spec.whatwg.org` directly. For W3C material the scout substituted the **same
organisations' canonical source repositories** — `w3c/aria-practices`, `w3c/wcag`,
`w3c/csswg-drafts` — the files the published pages are generated from, so provenance is
identical. MDN came via domain-restricted search returning MDN's own text.

**Open UI and Material 3 prose could not be read substantively.** Treat their absence as a
real hole, not a summary.

## Tier 1 — skill construction

**`docs.claude.com/…/agent-skills/best-practices`.** `name` ≤ 64 chars, lowercase/digits/
hyphens, may not contain "anthropic" or "claude". `description` ≤ 1024 chars and is the
**only** thing resident before the skill fires, so it carries the entire triggering burden.
Three rules make it fire reliably: third person (first/second person causes discovery
problems because the text is injected into a system prompt); **what it does and when to use
it as separate clauses**; and seeded with the literal vocabulary a user would type, because
selection happens against 100+ competing descriptions.

Body under 500 lines. **Reference depth is a hard constraint, not a style preference** —
exactly one level deep, because when Claude follows a reference from *within* another
referenced file it previews with `head -100`, so information at the bottom of a second-hop
file silently never arrives. Any reference over 100 lines opens with a table of contents for
the same reason.

**Degrees of freedom:** calibrate specificity to fragility — a narrow bridge with cliffs
(exact commands, no variation) versus an open field (direction only).

**Two structural devices worth stealing.** Complex workflows given as a checklist the model
is told to **copy into its own response** and tick off — the checklist becomes visible
working state rather than remembered intent. And the feedback loop: run validator → read
error → fix → re-run, with an explicit "only proceed when validation passes" gate. The page
shows this working both with a script validator *and* with a document validator (a style
guide the model checks against by reading).

**Eval-first ordering:** build three evaluations before writing documentation, and measure a
baseline without the skill, so you stop documenting imagined problems.

**`/mnt/skills/public/frontend-design/SKILL.md`** — 55 lines, zero bundled files. Structure:
persona framing → ground it in the subject → design principles → an explicitly **two-pass
process** (brainstorm a compact token plan, then *critique that plan against the brief before
writing any code*) → restraint/self-critique → writing.

Most transferable move: **it names its own failure mode concretely** — it calls out three
specific looks that AI design converges on, including a literal hex value it says is a tell,
and instructs that where the brief leaves an axis free, don't spend that freedom on a
default. A negative constraint stated precisely enough to be checkable, far more useful than
"be original". Deference rule: "the brief's own words always win", including when the brief
asks for one of the clichés.

**Directly relevant to this gap:** accessibility appears as a **single unelaborated clause** —
a "quality floor" mentioning visible keyboard focus and reduced motion. That is the whole
treatment. It is exactly the "ARIA at the end" posture the capability gap describes,
occurring in Anthropic's own published design skill.

**`/mnt/skills/examples/theme-factory/SKILL.md`** — 59 lines + `themes/*.md` (one file per
theme) + a showcase asset. SKILL.md contains **no token values at all** — it is navigation
plus procedure, and each theme's palette lives in its own leaf file read only when chosen.
The domain-partitioned reference pattern applied to design data. **It refuses to proceed
without a human:** display showcase → ask which theme → *wait for explicit confirmation* →
only then apply. A named blocking step, not a suggestion. Escape hatch routes back through
the same gate.

*Weakness worth noting:* a theme here is a flat list of hexes and font names. No
primitive/semantic distinction, no state variants, and "ensure proper contrast and
readability" left as an unverified instruction. **The closest published analogue to Sable,
and it stops well short.**

**`mcp-builder`** — the closing **"Documentation Library"** listing every reference annotated
with *when* to load it ("Load First", "Load During Phase 1/2", "Load During Phase 4").
Loading order treated as part of the instruction set rather than left to inference. Phase 4
makes an evaluation suite part of the deliverable.

**`skill-creator`** — codifies the directory contract: `scripts/` for deterministic
executable work, `references/` for docs pulled in on demand, `assets/` for files that end up
in the output. Raises the table-of-contents threshold to >300 lines. Carries a **"Principle
of Lack of Surprise"** — a skill's contents must not surprise a user who has read its
description.

## Tier 2 — the craft

### Token layering — Material Web's shipped `_md-sys-color.scss` / `_md-comp-filled-button.scss`

The concrete artifact behind the unreachable m3.material.io prose. Three namespaces, with the
dependency direction **strictly one-way**:

- `md.ref.palette.*` — primitives. Raw generated tones. Nothing in the UI references these
  directly.
- `md.sys.color.*` — semantics. 48 names: `primary`, `on-primary`, `primary-container`,
  `on-primary-container`, `error`, `on-error`, `surface` plus a graded stack (`surface-dim`,
  `surface-bright`, `surface-container-lowest` → `-low` → `-container` → `-high` →
  `-highest`), `outline`, `outline-variant`, `inverse-surface`, `scrim`, `shadow`, and a
  `-fixed` family that deliberately does *not* flip between themes.
- `md.comp.<component>.*` — component tokens named `element.state.property`:
  `container-color`, `hover-container-elevation`, `disabled-label-text-color`,
  `pressed-state-layer-opacity`.

Two structural facts matter more than the names. **Theming is a function swap, not a file
rewrite:** light and dark are two functions (`values-light()` / `values-dark()`) producing the
*same 48 keys* from the same reference palette — the component layer is untouched by theme.
And **every component token is emitted as `var(--md-comp-…, <resolved-system-value>)`** — the
custom property is the override seam, the resolved value the baked fallback, so an unthemed
page still renders.

The **`on-X` pairing convention** generalises hardest: every background-role token ships with
its foreground partner, so "text on this surface" is a lookup rather than a judgement call,
and contrast can be asserted pairwise.

Observed: the component layer leaks — some spacing tokens in the button file are hardcoded
pixel literals rather than references to a system spacing scale.

### Cascade layers — `w3c/csswg-drafts` css-cascade-5

Layers sort by **first declaration**, nested layers grouped inside their parent. The rule
people get wrong: **unlayered rules sort *after* all layered rules**, so for normal
declarations unlayered styles beat everything in a layer regardless of specificity.
`!important` **inverts the whole ordering** — important declarations in *earlier* layers win
over later ones, and unlayered important declarations *lose* to important declarations in any
explicit layer.

The critical fact: in the cascade sort order, layers are evaluated **before specificity**
(Origin/Importance → Context → Element-attached → **Layers** → Specificity → Order). A
one-class selector in a higher layer defeats a five-class selector in a lower one; specificity
only arbitrates *within* a layer. That is what makes specificity wars structurally impossible
rather than merely discouraged.

Also load-bearing: `@import url() layer(name)` adds the layer to the order **even if the
stylesheet fails to load**, so layer order is stable regardless of network outcome. Anonymous
layers get a unique identity per occurrence and cannot be referenced from outside — a library
can hide internal layering while exposing named layers for consumers to slot around.

### Custom properties and `@property` (MDN)

Custom properties inherit and resolve at computed-value time, which is why a theme can be
swapped by redeclaring a handful of names on an ancestor and having every descendant
recompute — no selector rewriting.

The sharp edge: when a custom property's value is **invalid at computed-value time** and the
property is unregistered or registered with universal `*` syntax, the `var()` **fallback** is
used. But if registered via `@property` with a *non-universal* syntax and an `initial-value`,
**that registered initial value is substituted and the fallback is never consulted**. So
`@property` changes the failure mode of your token layer, not just its animatability — a
typo'd theme value degrades to the registered initial rather than to your inline fallback.

### Keyboard and focus contracts — `w3c/aria-practices`

**Keyboard interface practice.** The governing rule: **a composite widget contributes exactly
one stop to the tab sequence.** Tab moves *between* components; arrows, Home/End and typeahead
move *within* one. Two implementations:
- **Roving tabindex** — one descendant carries `tabindex="0"`, siblings `-1`; on arrow you
  flip and call `.focus()`. DOM focus genuinely moves, so the UA scrolls into view for free.
- **`aria-activedescendant`** — the container holds `tabindex="0"`, DOM focus never leaves it,
  and `aria-activedescendant` points at the active child's id. **You must scroll it into view
  yourself.**

Never use `tabindex` greater than 0 — reorder the DOM instead, since DOM order is also
screen-reader reading order. Focus and selection must be visually distinguishable from each
other *(the fetched text was garbled at this exact sentence — concept is standard, wording is
low-confidence)*.

**Modal dialog.** Tab and Shift+Tab cycle within and **wrap** — that wrap is the trap, and it
is author-implemented. Escape closes. Initial focus is a **decision**, not "the first
focusable thing", with four cases: list/table/prose content → `tabindex="-1"` on a static
element at the start so the user lands before the content; if focusing the first control would
scroll the dialog → focus a static element such as the title; **destructive confirmations →
focus the least destructive action**; otherwise the most-used control. On close, focus returns
to the invoking element unless it no longer exists or workflow dictates otherwise.
`role="dialog"` + `aria-modal="true"` + `aria-labelledby`. `aria-describedby` advised against
for complex semantic content because it flattens into one announcement. `aria-modal`
supersedes `aria-hidden`-ing the rest of the page. You may only mark it modal if **both**
hold: code actually prevents outside interaction, **and** styling visually obscures the
outside.

**Tabs.** Tab enters the tablist at the *active* tab. Left/Right cycle with wrap.
**Automatic vs manual activation is the decision the pattern forces:** automatic (selection
follows focus) is *recommended* when panels are preloaded and switch without perceptible
latency; manual (arrow moves focus, Space/Enter activates) is **required** when activation
costs a fetch, because otherwise arrowing through five tabs fires five loads. Panel gets
`tabindex="0"` **only if it contains no focusable content** — otherwise you create a redundant
stop.

**Listbox.** Either focus technique permitted. Single-select focuses the selected option, or
the first if none. Multi-select focuses the first *selected* option, or the first option
**without selecting it**. Home/End "strongly recommended" past five options. Multi-select has
two selection models and the pattern **recommends the one needing no modifier keys**. Options
carry `aria-selected` **or** `aria-checked` — pick one, use it consistently, never both.

**Combobox** — the pattern most implementations get backwards. For listbox/grid/tree popups,
**DOM focus stays on the input for the entire interaction** and navigation is expressed purely
through `aria-activedescendant`. The one exception is a dialog popup. Down Arrow opens and
moves into the popup; **Alt+Down opens *without* moving into it**; Alt+Up returns and closes;
Escape dismisses, and optionally clears the input if already closed.

**Switch.** Space toggles; Enter optionally. `aria-checked` true/false — **binary only, no
`mixed`**, which is the semantic line against checkbox. Two explicit prohibitions: do not
change the label text when state changes, and `aria-selected` does not apply.

**Checkbox.** Space toggles; **Enter is not part of the contract.** `aria-checked` takes
`true`/`false`/`mixed`, `mixed` reserved for a tri-state parent.

**Tooltip.** The header states this pattern **is work in progress and does not have task force
consensus** — the one APG pattern not to treat as settled. Escape dismisses; focus stays on
the trigger; a hover-triggered tooltip persists while the pointer is over the trigger *or the
tooltip itself*. Hard constraint: **a tooltip can never receive focus and must never contain
focusable content** — if you need interactive content it is a non-modal dialog.

**Popover.** No APG pattern exists. The platform primitive is the `popover` attribute with
three states: `auto` (light-dismissible, one at a time), `manual` (no light dismiss, multiple
coexist), `hint`. All render in the top layer and are **non-modal by design** — no focus trap,
no inertness. **MDN's text did not cover focus-return-on-hide, so that behaviour is
unverified.**

### WCAG thresholds — `w3c/wcag`

**1.4.3 Contrast (Minimum), AA** — 4.5:1 normal text, 3:1 large (18pt, or 14pt bold ≈ 24px /
18.66px). Exempt: incidental/decorative text, logotypes, and UI components **not available for
interaction**. **1.4.6 Enhanced, AAA** raises to 7:1.

**1.4.11 Non-text Contrast, AA** — 3:1 for the visual information needed to identify a
component **and its states**, and for graphical objects needed to understand content. This is
the one that catches design systems: input borders, checkbox ticks, switch thumbs and tracks,
focus indicators, icon-only buttons. **Values must not be rounded — 2.999:1 fails.** Disabled
components exempt.

**2.4.11 Focus Not Obscured (Minimum), AA — new in 2.2.** A focused component must not be
*entirely* hidden by author content. Named failure modes: sticky headers/footers, non-modal
overlays and popovers, cookie banners. **2.4.12 Enhanced, AAA** requires no part obscured.

**2.4.13 Focus Appearance, AAA — new in 2.2.** The indicator must have an area at least equal
to a **2 CSS px thick perimeter of the unfocused component**, and a **3:1 contrast ratio
between the same pixels in the focused and unfocused states**. Note carefully — this is a
**change-of-state ratio measured on identical pixels, not adjacency**, which distinguishes it
from 1.4.11. Both can apply at once and an indicator can pass one while failing the other.

**2.5.8 Target Size (Minimum), AA — new in 2.2.** 24×24 CSS px, five exceptions. The spacing
test is precise: draw a 24px-diameter circle centred on each undersized target's bounding box;
it passes if that circle intersects neither another target nor another undersized target's
circle.

### Automated checking — axe-core rule catalogue

Outside the stated allowlist; included because it is the canonical primary reference for the
rule set that `@axe-core/playwright`, jest-axe, Lighthouse and Pa11y all execute — there is no
more upstream source for "test contrast automatically".

`color-contrast` (1.4.3, serious, **issue types: failure *and* needs-review**);
`color-contrast-enhanced` (AAA, **disabled by default**); `aria-required-attr`,
`aria-required-children`, `aria-required-parent` (critical); `aria-hidden-focus` (catches the
classic bug of an `aria-hidden` wrapper still containing tabbable children);
`scrollable-region-focusable`; `tabindex` (flags any positive tabindex); `aria-dialog-name`
(**best practice, not a WCAG mapping**).

**The "needs review" classification is the important structural fact:** axe cannot resolve
contrast when the background is an image, a gradient, or a stacking-context overlap, so it
returns *incomplete* rather than pass or fail. **A CI gate that only fails on `violations`
will silently green-light every incomplete.**

## Synthesis

**1. The one-way dependency graph is the whole trick, and its enforcement is a lint rule, not
a convention.** Primitives referenced only by semantics, semantics only by components, nothing
skipping a level or pointing sideways. The "danger colour drifts" symptom is what happens when
a component reaches past its semantic layer to a primitive — and that is **statically
detectable**: parse the emitted CSS, resolve each `var()` chain, fail any component-layer
declaration whose chain terminates in a primitive. The corollary is the `on-X` pairing
convention: shipping every background-role token with its bound foreground makes "what colour
is text here" a lookup, which is simultaneously what makes automated contrast checking
**enumerable over token pairs** rather than requiring a rendered page.

**2. Cascade layers relocate override authority from specificity to a declared ordering, and
the two traps are unlayered styles and `!important`.** A system that puts everything it ships
inside layers becomes structurally un-fightable by selector escalation — but also *trivially*
overridable by any unlayered rule a consumer writes. For four products sharing one system that
is a feature, **provided it is a stated contract rather than a surprise**. A skill that teaches
layers without teaching the `!important` inversion has taught half a mechanism.

**3. Accessibility here is two separable contracts, and only one is about ARIA at all.** The
*keyboard* contract is a state machine: which key moves focus where, one tab stop or many,
whether selection follows focus, where focus goes on open and returns on close. The APG
specifies this per pattern, and `aria-*` attributes are the **reporting** layer describing a
state machine you have already built — which is precisely why bolting them on last produces
widgets that read correctly and behave wrongly. The *visual* contract is where tokens and
accessibility meet: 1.4.11's 3:1 on component and state indicators, and 2.4.13's 3:1 between
focused and unfocused states of the same pixels, mean **the focus ring is not one token but a
relationship between two token values** — and it must hold in all three themes independently.

## Improvement openings

1. **Nobody publishes the third theme.** Every source treats theming as light/dark. Material
   ships two functions and stops. High-contrast has genuinely different constraints — it is not
   "dark with more contrast", it typically **collapses the surface-elevation stack** (the graded
   `surface-container-*` tokens lose meaning when everything must clear 7:1) and forces borders
   onto components that relied on fill contrast alone. Nothing found addresses what happens to a
   graded surface scale under high contrast. Also unaddressed anywhere: **`forced-colors` mode**,
   where the OS overrides your colours entirely and your token layer is bypassed — a system
   claiming three themes should say what happens in the fourth one it does not control.
2. **"How many token layers" is answered by example, never by argument.** Material shows three;
   no source justifies three over two or says when a component layer earns its keep. Reading the
   Material files directly, the component layer is doing two different jobs — genuine
   per-component values (`with-leading-icon-trailing-space`) and pure pass-throughs — and only
   the first justifies the layer. For twelve components the pass-through tax may exceed the
   benefit. A live design question the literature will not settle.
3. **Token naming guidance is thin where it matters most.** Material's names are enumerated but
   not *derived* — no stated rule for generating the next name as the system grows, which is
   exactly what "survives growth" means. Its semantic layer conflates role (`primary`, `error`)
   with prominence (`-container`, `-fixed`, `-dim`) with pairing (`on-`) in one flat namespace of
   48 strings, and pixel literals leak into the component layer. A better scheme makes the axes
   explicit and orthogonal so a name is **computed rather than remembered**. Multi-brand is
   entirely absent — Material assumes one identity, and Sable serves four products.
4. **Popover is genuinely underspecified and the brief names it.** APG has no pattern; the HTML
   primitive is non-modal by design, so the gap between "auto popover" and "the popover in your
   design system that contains a menu" is unbridged by any spec. **Whether focus returns to the
   invoker on light-dismiss could not be verified** — the single most consequential unverified
   fact in this report, and it must be pinned before writing anything about popover focus return.
5. **The tooltip pattern is explicitly not consensus** — APG says so in its own header. Mark
   anything built on it provisional. The real guidance is the negative one: a tooltip that needs
   to contain a link is a non-modal dialog and the skill must refuse to build it as a tooltip.
   Note also the collision with 2.4.11: **a focus-triggered tooltip positioned over the *next*
   focusable element is a new AA failure introduced by an accessibility feature.**
6. **Automated testing is the weakest-covered requirement by a wide margin, and axe's defaults
   are actively misleading here.** Three traps: `color-contrast-enhanced` is disabled by default,
   so a "passing" run has not checked AAA at all; contrast checks return `incomplete` on
   gradients, images and overlapping stacking contexts, and a gate asserting only on `violations`
   passes them silently; and **there is no axe rule for 1.4.11, 2.4.13, or 2.4.11** — precisely
   the criteria this project is built around. Focus appearance requires comparing rendered pixels
   between two states: a screenshot-diff-plus-contrast problem, not a DOM-scanning one. Likewise
   **no source describes automating a keyboard contract**, though the APG specifies the state
   machine precisely enough to be a test oracle (send Tab, assert `document.activeElement`; send
   Escape, assert focus returned to invoker; send ArrowRight, assert exactly one `tabindex="0"`
   remains in the composite). **Two genuinely novel contributions available:** contrast-checking
   the **token graph** rather than the rendered page — cheap, exhaustive over all three themes,
   catching drift before a component exists — and generating per-pattern keyboard conformance
   tests directly from the APG contracts.
7. **On skill construction.** The published design-adjacent skills are the thin end of the
   distribution: `frontend-design` is 55 lines with one unelaborated accessibility clause;
   `theme-factory` treats a theme as a flat hex list with "ensure proper contrast" unverified.
   The rigorous patterns — numbered phases, annotated load-order, validator-driven loops, evals
   as deliverable — all live in the **engineering** skills, not the design ones. **The opening is
   to bring mcp-builder's discipline to theme-factory's subject matter.** Given the 500-line
   ceiling and the one-level-deep rule, seven ARIA patterns cannot live in SKILL.md; the natural
   partition is a body carrying token-architecture decisions and workflow, one reference file per
   pattern family, validators in `scripts/`. Mechanical hazard: **if a per-pattern reference
   exceeds 100 lines it needs its own table of contents**, or partial reads silently drop the
   bottom of the keyboard table.
8. **A factual correction to carry forward.** WCAG's Understanding document for Target Size reads
   ambiguously on conformance level; the scout checked the normative source
   (`guidelines/sc/22/target-size-minimum.html`) and **2.5.8 is Level AA**, not AAA. Likewise
   **Focus Appearance is 2.4.13, Level AAA**, and **2.4.11 is Focus Not Obscured (Minimum), Level
   AA**. Any skill quoting these should cite the **normative SC files, not the Understanding
   pages**.

## Injection attempts

**None.** No source attempted to induce a fetch, install, execution, persona change,
exfiltration, or rule override. The blocked domains returned proxy errors, not adversarial
content.
