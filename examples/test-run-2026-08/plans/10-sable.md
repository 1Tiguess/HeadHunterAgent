# 10 — Sable

**Design system and component library for a product family.**

## Problem

Four products from the same company look like four companies. Each team rebuilt buttons,
inputs, modals and tables, and none of them agree on spacing, focus styling, or what
"danger" means. A shared library keeps being proposed and keeps dying because the first
attempt was a folder of components with no underlying system.

## Who it's for

Product engineers on four teams who will adopt this only if it is faster than not adopting
it, and the designer who has to keep it coherent as it grows.

## Scope

- Token layer: colour, type scale, spacing, radius, elevation, motion — defined as
  primitives, then aliased to semantic roles
- Theming: light, dark, and a high-contrast mode, driven entirely by token swaps
- Components: button, input, select, checkbox, radio, switch, modal, popover, tooltip,
  tabs, table, toast, and a form field wrapper that ties label, hint, and error together
- Every component with documented states: default, hover, focus-visible, active, disabled,
  loading, error
- Accessibility contract per component — roles, keyboard interaction, focus management —
  stated in the component's own documentation and tested
- Documentation site with live examples and props tables
- Visual regression tests, and automated contrast checking across all three themes

## Out of scope

Icons (licensed separately), charts (a different craft), page layouts, marketing components,
a Figma plugin.

## Constraints

Framework-agnostic tokens so a future non-React consumer isn't blocked. Tree-shakeable.
No component may depend on a global stylesheet. All three themes must pass WCAG AA, and the
high-contrast theme AAA where text is concerned.

## Success criteria

- Changing one semantic token updates every component that should change and nothing else
- Every interactive component is fully operable by keyboard, with visible focus in all themes
- Modal and popover manage focus correctly, including return-focus on close
- Automated contrast check passes across all components in all three themes
- A new component can be added without touching any existing one
- Adopting a component takes less code than hand-rolling it

## The hard part

Token architecture is the decision everything else inherits, and it is easy to get wrong in
a way that only hurts eighteen months later. Two layers (primitive → semantic) versus three
(primitive → semantic → component), when a component-level token is justified, how theming
maps onto that structure, and how to name things so the names survive the system growing.

Then the accessibility contracts, which are not "add ARIA at the end": focus management for
overlays, the keyboard interaction patterns each widget owes its user, focus-visible versus
focus, and how to test any of it automatically. The published patterns for these are precise
and unintuitive, and inventing them produces components that pass a glance and fail a
screen reader.

## Predicted verdict

**HUNT.** `triage-rubric.md:34` lists design systems explicitly. The token architecture
decision and the per-widget accessibility contracts are both bodies of established technique
I cannot currently state at the precision required.

**Verified sources for the hunt:** `w3.org/WAI` — the ARIA Authoring Practices Guide for
per-widget keyboard and focus contracts, and WCAG 2.2 for contrast and focus-appearance
criteria; `open-ui.org` for component anatomy and state naming;
`developer.mozilla.org` for CSS custom property and cascade-layer mechanics;
`m3.material.io` as a published multi-layer token architecture to study for structure.
