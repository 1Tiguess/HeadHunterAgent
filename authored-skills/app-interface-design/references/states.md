# Non-loaded states

Load when designing any state other than "content is here".

Interface *copy* for these states belongs to `frontend-design`. This file covers structure,
composition and timing.

## Contents

- [One composition, many fills](#one-composition-many-fills)
- [The catalogue](#the-catalogue)
- [Timing rules](#timing-rules)
- [Skeleton versus spinner](#skeleton-versus-spinner)
- [Offline, stale and partial](#offline-stale-and-partial)

## One composition, many fills

Empty, no-results, error, offline, permission-denied and loading are **one component with
different content** — not six screens invented separately.

The composition:

```
  [ icon ]
  Title
  Description
  [ optional primary action ]  [ optional secondary ]
```

Rendered in the **same slot, same position, same typographic scale** as the loaded view. That
sameness is the whole mechanism by which states read as the same product. The moment a state
gets its own layout, its own type scale, or its own vertical position, it reads as a different
screen — and that is the failure this addresses.

The strongest evidence for this being right: the platform components that ship for this purpose
specify *one* view for network failure, empty collection **and** no search results, with loading
as a further configuration of the same object.

## The catalogue

| State | Condition | Must convey |
|---|---|---|
| **Empty** | Collection genuinely has nothing | That this is normal, and the action that creates the first item |
| **No results** | Query matched nothing | **Echo the query**, and offer to clear or broaden it |
| **Error** | Operation failed | What failed, and the next action — not an error code alone |
| **Offline** | No connectivity | Whether anything is shown from cache, and what is unavailable |
| **Stale** | Cached data, refresh failed | **That the data is old, and how old** — while still showing it |
| **Partial** | Some sources failed | What is present, what is missing, and that the rest is missing rather than empty |
| **Permission denied** | Authenticated, not authorised | **Who can grant access** — not merely that access is denied |
| **Loading** | In flight | Progress if known, activity if not; see timing below |

Two failures worth calling out because they are near-universal:

- **Empty and no-results collapsed into one.** "Nothing here" for a filtered list is wrong and
  actively confusing — the user's filter is the cause, and clearing it is the remedy.
- **Permission-denied treated as an error.** It is not a failure; it is a state with a known
  resolution path that involves another person. Say who.

## Timing rules

These prevent the two visible failures — flicker on fast loads, and a stall that looks like a
crash.

| Rule | Value | Why |
|---|---|---|
| Delay before showing | ~100–200ms | A load that resolves in 80ms should never paint an indicator |
| Minimum visible duration | ~300–500ms | Once painted, do not remove it in the next frame |
| Indeterminate ceiling | **5 seconds** | Above this, show real progress — an indeterminate spinner past 5s reads as hung |
| Indicator type per activity | One, app-wide | If refresh is circular on one screen it must not be linear on another |
| Sequential chains | **Overall** progress | Not per-step, which restarts and reads as no progress |

If a process can transition from unknown duration to known, use a progress indicator from the
start rather than swapping representations mid-wait.

Determinate versus indeterminate is a question of *knowledge*, not duration. Linear versus
circular is a question of *space*: linear when the process owns screen width, circular when it
sits on a control or a card.

## Skeleton versus spinner

*Reasoned from primitives. No canonical source addresses skeletons at all, so this is derived
from the timing rules above and the one-composition principle rather than cited.*

**Use a skeleton when** you know the shape of what is arriving and it fills a region. The
skeleton reserves layout, so nothing shifts when content lands. Lists, tables, cards, detail
panes.

**Use a spinner when** the shape is unknown, or the wait occupies a control rather than a region
— a button submitting, a row expanding, a filter applying to a view already on screen.

Both obey the delay and minimum-duration rules. Neither is exempt.

**The rule that matters most:** a skeleton that does not match the loaded layout is *worse* than
a spinner. It promises a shape and then breaks it, producing exactly the layout shift it was
supposed to prevent, plus a moment of false recognition. If your skeleton is three grey bars
standing in for a structure you have not built yet, use a spinner until you have.

Do not animate a skeleton aggressively. A slow shimmer reads as loading; a fast one reads as an
error state.

## Offline, stale and partial

The three states no published source covers, and the three that most products conflate into
"error".

**Offline** is a property of the connection, not the data. The question it must answer is: *is
anything usable still on screen?* An offline banner over a fully populated cached view is
informational. An offline state that blanks the content the user was reading is destructive.

**Stale** is the most under-served. Data is present and known to be old — the refresh failed, or
the device has been asleep. Show the data, mark it stale, and **say how old it is**. "Updated 4
minutes ago" is actionable; a spinner over unchanged content is not, and silently showing old
data as though it were current is the worst of the three.

**Partial** is where one source of several failed. The design requirement is to distinguish
*missing* from *empty*, because they license opposite conclusions: an empty region says "there is
nothing", a missing region says "we could not tell". Mark the failed region in place, keep the
rest live, and offer a retry scoped to what failed rather than to the whole view.

A product that renders all three as a generic error screen has thrown away the information the
user needed to decide what to do.
