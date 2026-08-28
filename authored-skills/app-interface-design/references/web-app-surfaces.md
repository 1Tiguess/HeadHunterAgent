# Web application surfaces

Load when building a web application shell.

*Reasoned from primitives. Every canonical source in this domain — Apple, Google, W3C — is
native-shaped and names none of these surfaces. Treat this file as considered design reasoning
rather than as citation.*

## Contents

- [Command palette](#command-palette)
- [Scope switcher](#scope-switcher)
- [Filter rail and saved views](#filter-rail-and-saved-views)
- [Bulk-selection action bar](#bulk-selection-action-bar)
- [Inspector panel](#inspector-panel)
- [Notification centre](#notification-centre)
- [Multi-level side navigation](#multi-level-side-navigation)

## Command palette

A flat, searchable index of every action and destination, opened by keyboard from anywhere.

**Why it earns its place:** it is the pressure valve on navigation depth. Without it, every
capability must be reachable by clicking, so the navigation tree grows until it is unnavigable.
With it, the tree carries only what people *browse*, and everything else is *searched*. This is
the single highest-leverage surface in a dense product.

Design constraints:

- **Actions and destinations in one index.** Splitting them makes the user decide which they want
  before typing, which is the decision the palette exists to remove.
- **Show the keyboard shortcut next to any action that has one.** The palette is how people learn
  shortcuts; it is a teaching surface as much as a control.
- **Rank by recency and frequency**, not alphabetically. The right answer is usually something
  they did yesterday.
- **Scope-aware.** Actions that apply to the current selection or project should rank above
  global ones, and actions that cannot apply should not appear at all.
- It supplements navigation; it never replaces it. A product reachable *only* by palette is
  undiscoverable.

## Scope switcher

Workspace, organisation, project, environment — whatever bounds the data on screen.

**Pin it to a fixed position, usually the top of the navigation surface, and never move it.**
Scope is context, and ambiguous scope is how people act on the wrong data. The cost of a
mis-scoped destructive action is unbounded, which justifies giving this surface permanent
real estate.

- The **current scope is always visible**, not only on hover or on opening the switcher.
- Switching scope should preserve the user's location where an equivalent exists — the same view
  in the new project, not the new project's home.
- Where scopes have meaningfully different risk (production versus staging), **encode the
  difference visually** in persistent chrome, not just in the switcher's label.

## Filter rail and saved views

**The key idea: a repeated query is a destination, not state.** Once a user has entered the same
filter combination three times, it should have a name and live in the navigation surface.

- Filters are visible and individually removable, not buried behind a modal. A user must be able
  to see why a list is short.
- **A filtered empty list is a no-results state, not an empty state** — it must echo the active
  filters and offer to clear them.
- Saved views belong in the **navigation** surface, because that is what they now are.
- Filter state belongs in the URL. A view a user cannot link to is a view they cannot share, and
  sharing a filtered list is the most common collaborative act in an admin tool.

## Bulk-selection action bar

Appears on selection, disappears when selection clears, and **replaces nothing permanent** —
overlay or insert it, never swap out the existing toolbar, because the user needs both.

Branch the available actions three ways: **no selection**, **one item**, **many items**. They are
genuinely different action sets, and offering a single-item action greyed out across a
multi-selection teaches nothing.

- Always show the **count** of what is selected. "Delete" and "Delete 847 items" are different
  decisions.
- Provide **select-all-matching-filter** distinctly from **select-all-loaded**. In a paginated or
  virtualised list these differ by orders of magnitude, and conflating them is a data-loss bug
  wearing a UI costume.
- Destructive bulk actions confirm with the count restated.

## Inspector panel

Editing the selected item beside the list rather than navigating to it — the list-detail rung
expressed as a panel rather than a route.

- **Selection drives it.** Changing the list selection updates the inspector; the inspector never
  has its own independent selection.
- **Edits save explicitly or autosave visibly.** An inspector that silently discards edits on
  selection change is the classic bug here — either commit on change with a visible indicator, or
  block the selection change and prompt.
- Collapsible, with the collapsed state remembered — but per the reversibility rule, collapsing
  under narrow width must revert when width returns.
- For a multi-selection, show what is *common* and what *differs*, and allow editing the common
  fields. Blanking the inspector on multi-select wastes the surface.

## Notification centre

**An addressable location, not a transient toast.**

The rule: **anything a user might need to find again cannot exist only as a toast.** Toasts are
for confirmation of an action the user just took and already knows about. Everything else — a
background job finishing, another user's change, a failure that occurred while they were
elsewhere — needs a place it persists.

- Unread state that survives reload.
- Grouped by source or type once there are more than a handful.
- Each entry links to the thing it is about. A notification you cannot act on from is a log line.
- Never let a toast be the only representation of a failure. The user was probably looking
  somewhere else.

## Multi-level side navigation

For hierarchies deeper than a sidebar's flat list handles.

- **Two levels is the practical limit for nesting.** Past that, pair a two-level sidebar with a
  breadcrumb in the content area rather than nesting a third time — a three-level tree in a
  sidebar is a control nobody can scan.
- **Expansion state persists** across navigation and reload. Re-collapsing the tree on every
  navigation destroys the user's place.
- The **current location is marked at every level** that contains it, not only on the leaf, so the
  user can see where they are in the hierarchy without expanding anything.
- Sections the user cannot access are dimmed, not hidden — hiding destroys spatial memory and
  makes two users' descriptions of the product disagree.
