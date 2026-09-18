# Overlay patterns: dialog, popover, tooltip

Load when building anything that renders over other content.

## Contents

- [Modal dialog](#modal-dialog)
- [Popover](#popover)
- [Tooltip](#tooltip)
- [Choosing between them](#choosing-between-them)

## Modal dialog

**Keyboard.** Tab and Shift+Tab cycle within the dialog and **wrap** at the ends. That wrap is
the focus trap, and it is **author-implemented** — nothing gives it to you. Escape closes.

**Roles.** `role="dialog"` plus `aria-modal="true"` plus `aria-labelledby` (or `aria-label`).
`aria-modal` supersedes the older practice of applying `aria-hidden` to the rest of the page.

`aria-describedby` is optional and is **advised against for complex semantic content**,
because it flattens the referenced content into a single announcement. Prose is fine; a form
or a table is not.

**Initial focus is a decision.** Four cases:

| Content | Focus |
|---|---|
| A list, table, or block of prose | A static element at the start with `tabindex="-1"`, so the user lands *before* the content |
| Focusing the first control would scroll the dialog | A static element at the top, such as the title |
| **A destructive confirmation** | **The least destructive action** |
| Anything else | The most-used control (OK, Continue) |

**On close, return focus to the invoking element** — unless it no longer exists, or workflow
dictates otherwise (focusing a newly created row, say).

**You may only call it modal if both conditions hold:** code actually prevents interaction
outside it, *and* styling visually obscures the outside. A visually-dimmed dialog that leaves
the page tabbable is not modal, and labelling it so misleads assistive technology.

## Popover

**There is no settled authoring pattern for popovers.** The platform primitive is the
`popover` attribute, with three states:

| State | Light dismiss | Multiple open |
|---|---|---|
| `auto` | Yes — outside click and Escape | No; opening one closes another |
| `manual` | No | Yes |
| `hint` | Yes | Does not close `auto` popovers; does close non-ancestor hints |

All render in the top layer.

**Popovers are non-modal by design.** No focus trap, no inertness of the rest of the page.
This is the gap that matters: "an auto popover" and "the popover in your design system
containing a menu" are not the same object, and no specification bridges them. If yours
contains a composite widget, you are responsible for its keyboard contract, and you should
consider whether it is really a non-modal dialog.

**Unverified, and worth checking before you rely on it:** whether an `auto` popover returns
focus to its invoker on light-dismiss. This could not be confirmed at a primary source during
authoring. Test it in your target browsers and implement return-focus explicitly rather than
assuming the platform provides it.

## Tooltip

**The authoring pattern for tooltips is explicitly work-in-progress and lacks consensus.**
Treat anything built on it as provisional and expect it to change.

What is settled:

- Escape dismisses it.
- **Focus stays on the trigger throughout.** The tooltip never receives focus.
- A focus-triggered tooltip hides when focus leaves the trigger.
- A hover-triggered tooltip persists while the pointer is over **either the trigger or the
  tooltip itself** — otherwise it is unreachable for anyone who wants to read a long one.
- `role="tooltip"` on the bubble, `aria-describedby` on the trigger.

**The hard constraint: a tooltip must never contain focusable content.** It cannot receive
focus, so anything focusable inside it is unreachable by keyboard. If you need a link or a
button in there, it is a **non-modal dialog**, not a tooltip. Build it as one.

**A collision worth knowing about:** a focus-triggered tooltip positioned over the *next*
focusable element creates a focus-obscured failure — an accessibility feature introducing an
accessibility failure. Check tooltip placement against what receives focus after the trigger.

## Choosing between them

```
Does it need to contain focusable content?
├─ No  → Is it purely descriptive text for the trigger?
│        ├─ Yes → tooltip
│        └─ No  → popover (auto)
└─ Yes → Must the user deal with it before continuing?
         ├─ Yes → modal dialog (focus trap, aria-modal, return focus)
         └─ No  → non-modal dialog (no trap, but manage focus and return it)
```

The commonest mistake is building a non-modal dialog and calling it a tooltip, because it
looks like one. The test is focusable content, not appearance.
