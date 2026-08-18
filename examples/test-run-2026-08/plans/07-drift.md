# 07 — Drift

**Two-player realtime browser game: top-down racing with drift physics.**

## Problem

A game that is fun to play for ninety seconds against a friend over the internet, in a
browser, with no install and no account. Most hobby attempts feel broken online — the other
car teleports, your own inputs feel mushy, and collisions disagree between the two screens.

## Who it's for

Two people on a link, on ordinary home connections, one of them possibly on wifi in another
country.

## Scope

- Canvas or WebGL rendering, 60fps target
- Vehicle physics with grip, weight transfer and drift that rewards skill
- Three tracks with collision geometry and lap timing
- Two-player online over WebRTC data channels or WebSockets, with a relay fallback
- Authoritative simulation with client-side prediction and reconciliation
- Lag compensation for collisions between cars
- Join by link, no account
- Graceful degradation: visible connection quality, sane behaviour on disconnect

## Out of scope

More than two players, matchmaking, persistence, leaderboards, mobile touch controls,
audio beyond basic engine and collision sounds.

## Constraints

Playable at 80ms RTT and 2% packet loss. Deterministic simulation so both peers agree.
Bandwidth under 30KB/s per player. No server-side game logic beyond relay if avoidable.

## Success criteria

- The remote car never visibly teleports under normal jitter
- Local input feels immediate — no perceptible delay between key and response
- Both clients agree on lap times and collision outcomes
- A 200ms latency spike degrades smoothly instead of desyncing
- The simulation produces identical results from identical inputs

## The hard part

Netcode, and it is notoriously unforgiving. The naive version sends positions at 20Hz and
interpolates, which feels terrible the moment latency varies. Doing it properly means a
fixed-timestep simulation decoupled from rendering, input prediction on the local client,
server reconciliation that rewinds and replays without visible correction, entity
interpolation for the remote car, and lag compensation for collisions. Each of these has a
known correct shape and a dozen plausible wrong ones, and the wrong ones only reveal
themselves under real network conditions.

Floating-point determinism across browsers is a further trap that ruins lockstep approaches.

## Predicted verdict

**HUNT.** The single hardest item in this set. I can name the techniques but not their
implementation details, ordering constraints, or failure modes with enough precision to get
them right first time — which is exactly `triage-rubric.md:43`'s "yes, but I cannot say
what they know".

**Verified sources for the hunt:** `developer.mozilla.org` (WebRTC data channels,
requestAnimationFrame timing, Canvas/WebGL performance), `w3.org` for the WebRTC spec.
Netcode technique has no standards body; the canonical primary references in this field are
the Gaffer On Games articles on fixed timestep, snapshot interpolation and state
synchronisation, and Valve's published lag-compensation writeup. Both are original primary
sources by the practitioners who established the techniques, not aggregators — they are
admissible under the allowlist's named-exception rule and must be justified as such in the
spec.
