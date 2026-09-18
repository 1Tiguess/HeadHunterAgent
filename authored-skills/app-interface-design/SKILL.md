---
name: app-interface-design
description: >-
  Designs application interfaces — products with many screens, persistent navigation, and dense
  task-oriented views — as opposed to marketing pages. Covers the layout ladder from stack to
  list-detail to split view, navigation architecture and item counts for tab bars sidebars and
  rails, per-screen density, empty and loading and error states as one family, and web app
  surfaces like command palettes, filter rails, bulk-selection bars and inspector panels. Use
  when designing or reviewing a dashboard, admin tool, data table, settings area, list-detail
  view, or any product where a user moves between sections; when a task takes too many screens;
  when navigation differs between areas; or when empty and loading states are missing or look
  unrelated to the loaded view.
allowed-tools: Read, Write, Edit, Glob, Grep, Bash
---

# Application interface design

## 1 — Why this skill exists

The default failure is designing an app as a stack of landing pages: generous whitespace, one
idea per screen, a hero at the top of each view. It photographs well and fails in use. A task
that should take one screen takes six. Navigation changes between sections. Density is uniform
whether the screen is for scanning a thousand rows or committing to one irreversible action.
Empty and loading states are missing, or look like they came from a different product.

Those are not separate faults. They are one: **the page is the unit of design, when the product
is the unit.**

This skill is about application structure. Aesthetic direction, typography and interface copy
belong to `frontend-design`; token architecture and per-widget keyboard contracts belong to
`design-token-systems`; charts belong to `dataviz`. Use those alongside this.

## 2 — The layout ladder

The correction to six-screens-for-one-task is not spacing. It is **how many things can be on
screen at once**. Pick a rung by how many things the user must hold simultaneously:

| Rung | Holds | Use when |
|---|---|---|
| **Stack** | One thing | Narrow surface, or a genuinely linear task |
| **List-detail** | A set and a member | The user picks from a collection and acts on one |
| **Three-column** | A scope, a set, a member | The collection itself needs choosing (a project, a mailbox, a workspace) |
| **Multi-window** | Independent tasks | Two tasks that do not share context and run in parallel |

Extra screen area buys you a **higher rung**, not more padding. Every drill-down level you
remove is a level the user no longer has to hold in their head and navigate back out of.

Split views exist to **avoid modality**. If you find yourself reaching for a modal to show
detail, you probably want the next rung up.

## 3 — Reversibility

**Resizing must never permanently alter the layout.** When space returns, the app returns to its
previous arrangement, opportunistically and without asking.

This converts adaptivity from a breakpoint problem into an invariant, and it is what makes the
ladder coherent: a rung is a *response to available space*, not a state you get stuck in.

Two mechanics follow. Collapse shows **the last column carrying useful information** — a
three-column app becomes a three-level push stack, and rows that were selections become rows
with disclosure chevrons. And the transition **preserves scroll position and selection** in both
directions, because a user who resizes has not changed their mind about where they were.

Columns collapse; they do not reflow. Never show a sidebar and a tab bar in the same view.

## 4 — Navigation by counts and switching frequency

The numbers are real constraints, not preferences:

| Surface | Items | Notes |
|---|---|---|
| Bottom bar / tab bar | **3–5** | Hard ceiling of 5. Labelling flips at 4: all labelled at ≤3, selected-only at ≥4 |
| Collapsed rail | **3–7** | More reachable through submenus when expanded |
| Expanded rail | More | Now the replacement for the navigation drawer |
| Sidebar | Deep | Flattens hierarchy to one tap; morphs to a tab bar at narrow widths |

These form a **width ladder**, where the item ceiling rises as the surface widens. That ladder is
the decision rule — more so than any individual component's guidance.

**Sidebar vs tab bar.** Sidebar when the hierarchy is deep enough that flattening it to one tap
is the point. Tab bar when you want maximum content area and easier adaptation. **When unsure,
start with the tab bar** — sidebars have to morph into tab bars at narrow widths anyway, so
starting there costs you nothing and starting with a sidebar commits you to the harder case.

**Every additional tab is a decision imposed on every user on every visit.** So the question is
never "what could be a tab" but "what deserves one". If a candidate tab is only a grouping of
another tab's content, merge it.

**Tabs are navigation. Never actions.** A primary action belongs inside the screen where it
applies.

Two anti-patterns worth naming. A **"Home" tab that reassembles content from the other tabs**
destroys the user's model of where things live and produces tab-jumping. And **hiding menu items
based on context** destroys spatial memory — dim them instead.

**Sidebar contents depend on navigation type.** For a flat app: primary destinations at the top,
user-generated collections below under collapsible headers. For a hierarchical app: top-level
destinations plus **shortcuts only** — do not try to render the whole hierarchy in the sidebar,
browse it in the content area.

For choosing between a list and a grid: grids are visual but eat vertical space and handle long
text badly; lists are scannable and fit more per screen. For large collections, group by time, by
progress state, or by relationship rather than presenting an undifferentiated list.

## 5 — Two navigation invariants

**The primary navigation surface is persistent and never hidden by navigating.** That is exactly
what lets someone go deep in one section and come back out. An app that hides its tab bar three
levels in has trapped the user in a hierarchy.

**Past two levels you need a trail.** Either a breadcrumb, or a back control carrying the title
of the screen you came from — never a generic label.

State the distinction plainly, because it is the most commonly conflated pair in navigation:

> **Up is one level of hierarchy. Back is one step of history.**

They diverge whenever a user arrives laterally — from a search result, a notification, a deep
link. Up goes to the parent that always existed; Back goes wherever they happened to come from.
A product that implements only one of them will surprise users in exactly those cases.

A breadcrumb is **the trail of parent pages in hierarchical order, not the user's history.** It
belongs in a labelled navigation landmark with the current page marked as current.

Every screen should answer the toolbar's three questions: *where am I* (title), *what can I do
here* (screen-specific actions), *how did I get here* (back). That is a compact test you can run
against any screen in the product.

`references/navigation.md` carries the width ladder, the shell landmark contract, and worked
back-vs-up cases.

## 6 — Density by screen job

> *This section is reasoned from primitives rather than cited. Published sources supply a density
> mechanism with no criteria for using it, and a per-platform posture with no per-screen rule.
> The taxonomy below is the missing middle.*

Classify every screen before setting its spacing. Three jobs:

| Job | The user is | Density | Examples |
|---|---|---|---|
| **Scanning** | Looking for one item among many | **Compact** — maximise items visible | Tables, inboxes, logs, search results |
| **Deciding** | Comparing a few things, or committing | **Comfortable** — give the decision room, separate the primary action | Detail views, confirmations, settings |
| **Monitoring** | Watching for change, often not looking directly | **Legible at distance** — larger type, fewer elements, status encoded redundantly | Dashboards, status boards, wall displays |

**A product with one uniform density has not classified its screens.** Mixing all three inside
one product is correct, not inconsistent — what stays constant is the type scale, the component
anatomy and the spacing *ratios*, not the absolute values.

Two mechanical constraints:

- **Density does not inherit.** A dense container does not densify its children; each component
  is set independently. Treat density as a per-component decision, not a global multiplier.
- **Compaction forfeits the touch-target guarantee.** Below the minimum target size you have
  spent an accessibility budget. That is a legitimate trade on a pointer-driven scanning screen
  and rarely legitimate on a touch surface — but it must be spent deliberately, not by reflex.

Increased density does not have to mean increased complexity. The failure is not "too much on
screen", it is "too much *undifferentiated*" — grouping, alignment and a clear hierarchy let a
dense screen stay readable.

For tables specifically: limit columns so the table never scrolls horizontally, and nominate one
column as the compact representation for when the layout collapses to a single column.

## 7 — The state family

Empty, no-results, error, offline, permission-denied and loading are **one composition with
different fills** — not six ad-hoc screens.

The composition: a label (icon and title), a description, and optional actions. Same slot, same
position, same typographic scale as the loaded view. That sameness is the entire mechanism by
which states read as the same product.

Concretely: no-results echoes the query back. Permission-denied says who can grant access, not
just that access is denied. Offline distinguishes *stale data shown* from *nothing to show*.
Error says what to do next.

**Timing rules**, which prevent the two visible failures:

- **Delay before showing** an indicator — do not paint a spinner for a load that resolves in
  80ms.
- **Minimum visible duration** once shown — do not remove it in the next frame.
- **Indeterminate under five seconds**; above that, show real progress.
- **One indicator type per kind of activity, across the whole app.** If refresh is a circular
  indicator on one screen it must not be a linear one elsewhere.
- For a chain of sequential operations, show **overall** progress, not per-step.

**Skeleton vs spinner** *(reasoned from primitives — no canonical source covers skeletons)*: use
a **skeleton** when you know the shape of what is arriving and it fills a region, because it
reserves layout and prevents shift. Use a **spinner** when the shape is unknown, or the wait
occupies a control rather than a region. Both obey the delay and minimum-duration rules. **A
skeleton that does not match the loaded layout is worse than a spinner** — it promises a shape
and then breaks it.

`references/states.md` has the full state catalogue and worked compositions.

## 8 — Web application surfaces

> *This section is reasoned from primitives rather than cited. Every canonical source in this
> domain is native-shaped; none of them names any of the following.*

- **Command palette** — a flat, searchable index of every action. This is what keeps a deep app
  navigable without deepening the navigation tree, and it is the single highest-leverage surface
  in a dense product.
- **Workspace / org / project switcher** — pinned to a fixed position, because scope is context
  and ambiguous scope is how people act on the wrong data.
- **Filter rail with saved views** — a repeated query becomes a *named destination* rather than
  state the user re-enters. Saved views are navigation, and belong in the navigation surface.
- **Bulk-selection action bar** — appears on selection, replaces nothing permanent, and branches
  its actions three ways: no selection, one item, many items.
- **Inspector panel** — edit the selected item without leaving the list. The list-detail rung
  expressed as a panel rather than a route.
- **Notification centre** — an addressable location, not a transient toast. Anything a user might
  need to find again cannot be only a toast.
- **Multi-level side navigation** — for hierarchies deeper than a sidebar handles. Past two
  levels, pair it with a breadcrumb rather than nesting further.

`references/web-app-surfaces.md` covers each in detail.

## 9 — Coherence across screens

Separate the **content layer** from the **navigation layer**. Navigation sits above content on
its own surface rather than directly on it.

What must stay fixed across every screen and form factor:

- Component anatomy in familiar placements
- The same core interactions
- Spatial groupings that stay grouped as layouts adapt
- Consistent selection and state signalling
- Stable symbol meanings

Group bar items by function and frequency. Do not mix symbols and text within one group. Keep
the primary action visually separate. **Screen-specific actions never migrate into persistent
chrome** — chrome is for what is true everywhere.

Design the anatomy once and let it scale across form factors, treating platform variation as
expression of one framework rather than as a set of exceptions.

## Reference files

| File | Contents | Load when |
|---|---|---|
| `references/navigation.md` | Width ladder, shell landmark contract, worked back-vs-up cases | Choosing or reviewing a navigation surface |
| `references/states.md` | Full state catalogue, compositions, timing, skeleton-vs-spinner | Designing any non-loaded state |
| `references/web-app-surfaces.md` | Command palette, switchers, filter rails, bulk bars, inspectors | Building a web application shell |

## Done means

- A task that took six screens takes one or two, by moving up the ladder rather than adding padding
- Resizing and restoring the window returns the original layout, with scroll and selection intact
- The primary navigation surface is visible on every screen and never hidden by navigating
- No navigation surface exceeds its item ceiling
- Past two levels there is a trail, and Up and Back behave differently on lateral arrival
- Every screen is classified scanning / deciding / monitoring, and density differs accordingly
- Empty, error, offline and loading share one composition with the loaded view
- No indicator appears for a sub-threshold load, and none vanishes inside its minimum duration
