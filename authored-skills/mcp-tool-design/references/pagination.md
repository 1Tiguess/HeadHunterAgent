# Pagination and response bounds

Load when an MCP tool returns a collection or a log.

## Contents

- [Two different problems](#two-different-problems)
- [Stable collections](#stable-collections)
- [Append-only streams](#append-only-streams)
- [Token budgets](#token-budgets)
- [Truncation notices](#truncation-notices)

## Two different problems

Published pagination guidance assumes a **stable collection** — a list that is not changing
while you walk it. Applying it to an append-only stream produces subtly wrong results, and
the difference is not cosmetic.

| | Stable collection | Append-only stream |
|---|---|---|
| Example | Configured services, saved jobs | Log tail, event feed, alert history |
| Grows while read? | No | Yes, at the head |
| Natural read order | Ascending, stable | Newest first |
| Cursor anchors to | Record index or id | Byte position or timestamp |
| Bounded by | Record count | Lines or bytes |
| Offsets valid? | Yes | **No** — they shift under the reader |

Decide which you have before writing the tool. A tool that serves both needs two modes, and
the mode must be an explicit parameter — never the same call quietly behaving differently.

## Stable collections

Always accept `limit`. Default 20–50. Cap it — a caller passing `limit: 100000` should get
the cap, not the whole set, and should be told the cap applied.

Never materialise the full result set to slice it. Push the limit into the backend query.

Return an envelope:

    {
      "items": [...],
      "count": 20,
      "has_more": true,
      "next_cursor": "..."
    }

`has_more` is a boolean the model can branch on without arithmetic. Include a total only if
it is cheap to compute; an expensive count to satisfy a field nobody reads is wasted work.

Prefer an opaque cursor over a numeric offset even here. It lets you change the underlying
ordering later without breaking callers mid-walk.

## Append-only streams

The log tail is the case that breaks naive pagination, and it is the common case for an
infrastructure server.

**Anchor the cursor to a position, not a count.** A byte offset into the file, or a
timestamp plus a tiebreaker. If you return "records 40–60" and twenty lines are appended
between calls, the next page overlaps or skips depending on read direction, and nothing in
the response reveals that it happened.

**Bound by lines or bytes, not records.** A single stack trace can be four hundred lines.
A limit expressed in records gives no bound on response size at all, which defeats the
purpose.

**Make direction explicit.** Reading a log almost always means newest-first, which is the
opposite of collection order. Say so in the description, and say what the cursor means in
that direction.

**Distinguish snapshot from tail.** A stable snapshot pins a ceiling at first request, so
the page set does not grow underneath the reader — right for "show me what happened during
the incident". A live tail advances into newly appended data — right for "is it still
failing?". These want different cursor semantics and should be separate tools, or one tool
with a required mode parameter.

## Token budgets

Give every tool a budget and enforce it server-side. The model cannot know in advance that
a call will return four megabytes, and by the time it finds out the context is already spent.

Practical shape:

- Set a character or token ceiling per response.
- Truncate at a record boundary, never mid-object — a half-emitted JSON object costs tokens
  and conveys nothing.
- Prefer dropping *fields* before dropping *records* when the caller is scanning; prefer
  dropping records when the caller is reading detail. If both matter, that is two tools.

Resist shipping both a full structured rendering and a human-readable rendering of the same
payload in one response. It duplicates the content and doubles the cost of exactly the large
responses you are trying to bound. Pick sensible defaults per tool and expose at most one
override — two orthogonal formatting knobs is a decision the model must get right on every
single call, and it will not.

## Truncation notices

A truncated response must say three things:

1. That truncation happened.
2. How much was withheld, in units the caller can act on.
3. **The specific parameter that would narrow the query.**

    Returned the 200 most recent lines (of ~14,000 matching). Narrow with
    `since` or `level` to see more of the relevant range, or page with
    `cursor` to continue from here.

The third item is the one that matters. A notice that says only "output truncated" spends
tokens telling the model it has a problem without telling it the solution — and the model
will usually re-issue the identical call.
