# Diagnosing multiplayer feel

Load when invoked against an existing implementation.

## Contents

- [How to use this](#how-to-use-this)
- [Instrument first](#instrument-first)
- [Symptom entries](#symptom-entries)
- [Reproducing bad networks](#reproducing-bad-networks)

## How to use this

Do not start rewriting. Most of these have a single cause, and the wrong fix for a
netcode symptom usually makes the next one worse — adding interpolation delay to hide a
prediction failure, for instance, trades one complaint for another.

Confirm the cause with an instrument before changing anything.

## Instrument first

Five numbers explain nearly everything. Put them on screen behind a debug flag:

1. **RTT**, current and minimum observed.
2. **Jitter** — standard deviation of inter-arrival time for state packets, over a rolling
   window. This is the number that should drive interpolation delay.
3. **Interpolation delay currently in use**, so you can see it against jitter.
4. **Reconciliation error magnitude** per correction — distance between predicted and
   authoritative position at the reconciled moment.
5. **Buffer depth** — how many state samples are queued ahead of the render point, and how
   often it runs dry.

A buffer that runs dry is extrapolation. Extrapolation is where teleporting comes from.

## Symptom entries

### Remote player teleports or warps on a straight line

Buffer ran dry and the renderer extrapolated past the last known sample, then snapped when
real data arrived. Check instrument 5 against 2: if delay is below jitter, the buffer will
empty regularly.

Fix: raise the interpolation delay, and make it adaptive rather than constant. If it is
already adaptive, check that the estimator is not being dragged down by a few fast samples —
size from a high percentile of jitter, not the mean.

### Remote player rubber-bands

Corrections are being applied to the rendered position. Look for authoritative state being
assigned straight to the transform.

Fix: introduce the visual error offset. Snap the simulation, decay the offset.

### Local input feels heavy, delayed, floaty

The local entity is waiting for confirmation. Look for the local transform being driven by
received state rather than by local simulation.

Fix: predict locally and reconcile. Instrument 4 will tell you whether reconciliation is then
firing constantly, which indicates a deeper mismatch.

### Feels fine alone, bad with two players

Same cause: the local player is being treated as a remote one. Single-player has no network
path so the bug is invisible.

### Agrees at low speed, disagrees in corners or on impact

Quantisation asymmetry, or the two peers stepping at different rates. Check that both ends
quantise identically before values re-enter the simulation, and that `dt` matches.

Stiff systems — slip angles, grip thresholds, anything with a sharp response curve — amplify
differences that a gentler simulation would absorb. A quantisation step that is fine for
rendering may be far too coarse for simulation feedback.

### Occasional large snap after smooth play

Reconciliation is firing without smoothing, or the decay rate is not adaptive so a large
error is being decayed at the gentle rate and then overridden by the next correction.

Fix: adaptive decay — aggressive for large errors, gentle for small.

### Slow desync over a long session

Deterministic lockstep in a browser. There is no fix that preserves the approach; floating
point is not bit-specified across engines and JIT tiers, and divergence compounds.

Move to state synchronisation with per-entity authority.

### Everything degrades together under load

Channel backpressure. Check `bufferedAmount`. A channel that cannot drain queues state which
is delivered later as a burst of stale samples — it looks like packet loss and is not.

Fix: drop rather than queue. State is superseded by the next tick, so sending stale state is
worse than sending nothing. Gate sends on `bufferedAmount` being below threshold.

## Reproducing bad networks

You cannot diagnose any of this on localhost.

- Chrome DevTools network throttling does **not** affect WebRTC data channels. Do not rely
  on it.
- Use an OS-level shaper: `tc netem` on Linux, Network Link Conditioner on macOS.
- Test at least three profiles: 80ms RTT with 2% loss and moderate jitter; a 500ms latency
  spike lasting a couple of seconds; and a brief total outage followed by recovery.
- The spike profile is the one that exposes buffer sizing. The outage profile is the one that
  exposes session lifecycle handling, which most implementations omit entirely.

Record the five instruments across each run rather than judging by eye. "Feels better" is not
a measurement, and the failure modes here are specifically ones that feel fine right up until
they do not.
