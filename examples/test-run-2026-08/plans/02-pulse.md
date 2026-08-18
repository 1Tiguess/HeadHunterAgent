# 02 — Pulse

**Real-time operations dashboard for a small fleet of services.**

## Problem

An engineer running six or seven services has metrics in three places and no single view.
When something degrades they find out from a user. They want one screen that makes the
current state obvious at a glance and the recent past legible on a second look.

## Who it's for

The on-call engineer, glancing at a wall display or a second monitor, mostly not looking
directly at it.

## Scope

- Live tiles: request rate, error rate, p50/p95/p99 latency, saturation, per service
- Time-series panel with a shared, brushable time range across all charts
- Eight chart forms in play: line, stacked area, bar, grouped bar, heatmap (hour × day),
  histogram (latency buckets), sparkline (in tiles), and a status matrix
- Threshold and anomaly annotation drawn on the series, not just coloured text
- Drill-down: click a spike, get the request sample behind it
- Light and dark, both first-class — a wall display in a bright room and a laptop at night
- Auto-refresh with a visible staleness indicator when the feed drops

## Out of scope

Alerting and paging, log aggregation, tracing UI, user management, long-term storage.
This reads an existing metrics endpoint.

## Constraints

Data arrives as JSON over SSE. Up to 40 series live at once. Must stay responsive at 5s
refresh with 24h of history in the browser. Colour must survive projection and the common
forms of colour blindness.

## Success criteria

- Every chart uses the same categorical palette, and a given service is the same colour everywhere
- Axis labels survive a 320px viewport without overlapping
- Nothing is encoded by colour alone
- The dashboard is readable at three metres on a wall display
- A dropped feed is visually unmistakable within one refresh interval

## The hard part

Chart design, and it is real craft. The naive version picks a colour per chart, uses a
rainbow ramp, double-encodes nothing, and produces eight charts that look like eight
different products. Consistent chart grammar, an accessible categorical palette that holds
in both themes, and knowing which form fits which question — that is exactly the expertise
that separates a good dashboard from a bad one.

## Predicted verdict

**Phase 2 clear — Tier 0 hit.** The `dataviz` skill covers precisely this: a form
heuristic, a colour formula with a runnable validator, mark specs, interaction rules, and a
validated palette in `references/palette.md`. `web-artifacts-builder` covers the
multi-component front end and `artifact-design` the layout pass. `SKILL.md:74` is explicit
— if an existing skill covers the work, say which one and stop. Hunting here would be
inventing a worse `dataviz`.
