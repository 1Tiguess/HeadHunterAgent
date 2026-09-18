# Selection patterns: listbox, combobox, tabs

Load when building a widget where the user picks from a set.

## Contents

- [Tabs](#tabs)
- [Listbox](#listbox)
- [Combobox](#combobox)

All three are composite widgets: **one tab stop, arrows move within.** See the keyboard
contract section of SKILL.md for roving tabindex versus `aria-activedescendant`.

## Tabs

**Keyboard.** Tab enters the tablist at the **active** tab — not the first — and exits to the
panel or the next element. Left/Right cycle with wrap (Up/Down when vertical). Home/End to
first/last are optional but expected past a few tabs. Delete may remove a tab, moving focus to
an adjacent one.

**The decision the pattern forces: automatic or manual activation.**

| | Automatic | Manual |
|---|---|---|
| Behaviour | Selection follows focus — arrowing selects | Arrow moves focus; Space/Enter activates |
| Use when | Panels are preloaded and switch with no perceptible latency | **Activation costs a fetch or heavy render** |

This is not a style preference. With automatic activation and a fetch per panel, arrowing
through five tabs fires five loads — and the user only wanted the fifth. Choose manual
whenever activation is expensive.

**Roles.** `role="tablist"` with `aria-label` or `aria-labelledby`, and `aria-orientation` if
vertical. Each `role="tab"` carries `aria-selected` and `aria-controls`. Each
`role="tabpanel"` carries `aria-labelledby` pointing back at its tab.

**Give the panel `tabindex="0"` only if it contains no focusable content.** If it does, the
panel stop is redundant and adds a tab press between the tab and the thing the user wants.

## Listbox

**Focus technique.** Either roving tabindex or `aria-activedescendant` is permitted. If you
choose the latter, remember you must scroll the active option into view yourself.

**Initial focus differs by selection mode:**

- **Single-select** — focus the selected option, or the first option if none is selected. It
  may auto-select that first option.
- **Multi-select** — focus the first *selected* option, or the first option **without
  selecting it**. Auto-selecting in a multi-select changes the user's data.

**Keyboard.** Arrows move. Home/End are strongly recommended past about five options.
Typeahead matches a single character; rapid successive characters match as a string.

**Multi-select has two selection models, and the recommended one needs no modifier keys:**

| Key | Action |
|---|---|
| Space | Toggle the focused option |
| Shift+Arrow | Extend selection |
| Shift+Space | Select contiguously from the last selected |
| Ctrl+A | Select all |

Modifier-only models (Ctrl+click to toggle) are discoverable by mouse users and invisible to
keyboard users.

**Use `aria-selected` or `aria-checked`, never both.** Pick one for the whole listbox and be
consistent. Mixing them within a widget produces contradictory announcements.

## Combobox

**The pattern most implementations get backwards.**

For a listbox, grid or tree popup, **DOM focus stays on the input for the entire
interaction.** Navigation is expressed purely through `aria-activedescendant`. Moving DOM
focus into the popup breaks typing, which is the whole point of a combobox.

The one exception is a **dialog** popup, where focus does move in.

**Keyboard.**

| Key | Action |
|---|---|
| Down Arrow | Open the popup **and** move into it |
| Alt+Down | Open the popup **without** moving into it |
| Alt+Up | Return to the input and close |
| Escape | Dismiss the popup; optionally clear the input if already closed |
| Enter | Accept the active option and close |
| Left/Right | On an editable combobox, return to the input and move the caret |

The Down / Alt+Down distinction is the one usually missed, and it matters: a user who wants to
*see* the options without committing to navigating them has no other way to ask.

**Roles.** `role="combobox"` on the input, carrying `aria-expanded`, `aria-controls`,
`aria-haspopup` (`listbox` by default, or `grid`/`tree`/`dialog`), and `aria-autocomplete`
(`none`, `list`, or `both`).

**Filtering.** If the popup filters as the user types, the active descendant must be
re-established after each filter — a stale `aria-activedescendant` pointing at a removed
option leaves assistive technology describing something that is no longer there. Either reset
to the first match or clear it explicitly.
