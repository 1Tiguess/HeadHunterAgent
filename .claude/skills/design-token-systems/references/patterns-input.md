# Input patterns: checkbox, switch, form field

Load when building form controls.

## Contents

- [Checkbox](#checkbox)
- [Switch](#switch)
- [Checkbox or switch?](#checkbox-or-switch)
- [The form field wrapper](#the-form-field-wrapper)

## Checkbox

**Keyboard.** Space toggles. **Enter is not part of the contract** — do not add it; in a form
context Enter submits, and intercepting it breaks that.

**State.** `aria-checked` takes `true`, `false`, or **`mixed`**. `mixed` is reserved for a
tri-state parent controlling a group of children where some but not all are checked.

**Grouping.** Related checkboxes go in `role="group"` with `aria-labelledby` pointing at the
visible group label. Without the group, a screen reader user gets a series of unrelated
checkboxes with no sense of what they collectively configure.

A tri-state parent needs its own behaviour defined: clicking it when `mixed` should select
all, not cycle through `mixed` — nobody wants to *set* an indeterminate state.

## Switch

**Keyboard.** Space toggles. Enter may optionally do the same.

**State.** `aria-checked` is **`true` or `false` only — never `mixed`.** That is the semantic
line separating a switch from a checkbox.

If you build it from a native `input[type=checkbox]` styled as a switch, use the HTML `checked`
property, not `aria-checked`.

**Two explicit prohibitions:**

1. **Do not change the label text when the state changes.** A switch labelled "Enable sync"
   that becomes "Disable sync" when on is ambiguous: the label should say what the control
   *governs*, and the state says whether it is on. Changing both means the user cannot tell
   whether the label describes the current state or the action.
2. **`aria-selected` does not apply.** Selection is a different concept.

## Checkbox or switch?

| | Checkbox | Switch |
|---|---|---|
| Meaning | This item is included / this statement is true | This capability is on or off |
| Takes effect | Usually on form submit | **Immediately** |
| Tri-state | Yes (`mixed`) | Never |
| In a group | Common | Rare |

The practical test is **when it takes effect**. A control that applies immediately reads as a
switch; one that stages a value for later submission reads as a checkbox. Getting this
backwards — a switch inside a form with a Save button — makes users wonder whether their
change was already applied.

## The form field wrapper

The component that ties label, control, hint and error into one accessible unit. It is worth
building once and using everywhere, because the wiring is easy to get subtly wrong per-field.

**What it must guarantee:**

- **The label is programmatically associated** with the control — `<label for>` or wrapping.
  A visually adjacent label with no association is invisible to assistive technology.
- **Hint text is referenced by `aria-describedby`**, not merely positioned nearby.
- **Error text is also referenced by `aria-describedby`**, appended to the hint rather than
  replacing it — the user needs both the constraint and what they got wrong.
- **`aria-invalid="true"`** on the control when in error.
- **The error is announced when it appears.** A live region, or moving focus to the field on
  submit failure. An error that is only visible is not an error for a screen reader user who
  has already moved past it.
- **Never convey error state by colour alone.** A red border is not an error message. Include
  text and, typically, an icon.
- **Required fields are marked programmatically** (`required` or `aria-required`), not only
  with a visual asterisk.

**Generate the ids.** The wrapper owns the relationship between control, hint and error, so it
should generate and wire the ids itself. Hand-written ids are where these associations break
as components get copied.

**Grouped controls need a different wrapper.** A radio group or checkbox group needs
`role="group"` or a fieldset with a legend, with the group label associated to the group
rather than to any individual control. A single wrapper trying to serve both cases usually
serves neither; make it two components.

**Contrast note.** The error state's border and icon are non-text content that identifies a
component state, so they need the 3:1 non-text ratio — in every theme. This is a common place
for a design to pass in light mode and fail in dark, because error red is often chosen against
a white background and then reused unchanged.
