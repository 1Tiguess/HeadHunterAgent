# Navigation architecture

Load when choosing or reviewing a navigation surface.

## Contents

- [The width ladder](#the-width-ladder)
- [Choosing a surface](#choosing-a-surface)
- [Up versus Back, worked](#up-versus-back-worked)
- [Breadcrumbs](#breadcrumbs)
- [The shell landmark contract](#the-shell-landmark-contract)
- [Push versus modal](#push-versus-modal)

## The width ladder

The navigation components form a ladder in which the item ceiling rises as the surface widens.
This is the decision rule; individual component guidance is downstream of it.

| Surface | Items | Behaviour |
|---|---|---|
| Bottom bar | 3–5, hard ceiling 5 | Labelling flips at 4 — all labelled at ≤3, selected-only at ≥4 |
| Collapsed rail | 3–7 | Submenus reach further when expanded |
| Expanded rail | More | Replaces the navigation drawer, which is deprecated |
| Sidebar | Deep hierarchy | Morphs to a tab bar at narrow width; overlays rather than pushes when space is tight |

Drawers, where still used: a **standard** (persistent) drawer permits simultaneous interaction
with content and suits tablet and desktop; a **modal** drawer scrims the content and suits
phones. Prefer the expanded rail.

The ladder is why "start with the tab bar when unsure" is good advice rather than timidity — a
sidebar has to become a tab bar at narrow widths regardless, so the tab bar is the case you
cannot avoid designing.

## Choosing a surface

Three inputs, in order:

1. **Destination count.** Above the ceiling for a surface, you are choosing the next rung up, not
   squeezing.
2. **Switching frequency.** Frequent switching wants persistent, always-visible destinations.
   Rare switching tolerates a surface that is one interaction away.
3. **Hierarchy depth.** A sidebar earns its place when flattening a deep hierarchy to one tap is
   the point. If the hierarchy is shallow, a sidebar is just a wider tab bar that costs content
   area.

Then apply the constraints:

- Never a sidebar and a tab bar in the same view.
- Tabs are navigation, never actions.
- No "Home" tab that reassembles the other tabs' content.
- Dim unavailable items rather than hiding them.

**Sidebar contents by navigation type.** Flat app: primary destinations at the top, user-generated
collections below under collapsible headers. Hierarchical app: top-level destinations plus
*shortcuts only* — the sidebar is not a tree view of the whole product, and trying to make it one
produces a control nobody can scan.

## Up versus Back, worked

The distinction that most products get wrong:

- **Up** — one level of *hierarchy*. Deterministic. Always leads to the parent that exists
  regardless of how the user arrived.
- **Back** — one step of *history*. Non-deterministic. Leads wherever the user came from.

They coincide when the user navigated down through the hierarchy, which is why the bug hides in
development and appears in production. They diverge on **lateral arrival**:

| Arrival | Up goes to | Back goes to |
|---|---|---|
| Drilled down from the list | The list | The list |
| Search result | The item's parent list | Search results |
| Notification or deep link | The item's parent list | Outside the app, or nothing |
| Cross-linked from a sibling item | The parent list | The sibling |

Two rules follow. **A back control must carry the title of the screen it returns to**, not a
generic label — that is what lets the user tell which of the two they are about to get. And when
Up and Back diverge, offer Up: after a deep link, "Back" that exits the app entirely is the worst
available outcome.

## Breadcrumbs

A breadcrumb is **the trail of parent pages in hierarchical order — not the user's history.**
Getting this wrong turns it into a second, worse back button.

Mechanics: it lives in a navigation landmark; that landmark carries a label, because a page will
have more than one; the current page is marked as current. It needs no keyboard interaction of its
own beyond its links being links.

Use one past two levels of hierarchy. Below that it is noise; above that a single back control
cannot express where the user is.

## The shell landmark contract

For an app with persistent chrome, the shell's regions are named once and stay named on every
screen. That constancy is what makes the shell navigable by assistive technology rather than
re-announced as new furniture per screen.

- At most one **banner**, one **main**, one **contentinfo** per page.
- **navigation**, **complementary**, **search**, **form** and **region** may repeat, but each
  repeat needs a unique label.
- **One deliberate exception:** identical controls serving the same purpose in two places — a
  pagination bar above and below a table — should share a label rather than being artificially
  distinguished.
- Landmarks double as skip-link targets.

## Push versus modal

Decide by what the user is doing, not by how much content there is:

- **Push** when traversing levels of one hierarchy, and when people toggle between views
  frequently.
- **Modal** when the task is self-contained and you want to sever the user from the surrounding
  hierarchy on purpose.

A modal that is really a hierarchy level will feel like a trap; a push that is really a bounded
task will leak state back into the hierarchy.

Modal composition: a title; the affirmative action as a verb on the right; cancel on the left;
the affirmative action disabled until requirements are met; and a confirmation prompt if the user
cancels with unsaved input. A bare close control with no cancel/confirm pair is reserved for
content that took no input.

And the reason the tab bar stays visible during a push: the user needs to be able to leave a deep
position in one hierarchy and return to it. Hiding the tab bar to gain vertical space trades a
navigational guarantee for a few pixels.
