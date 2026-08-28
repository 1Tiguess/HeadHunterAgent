---
name: realtime-netcode
description: >-
  Makes browser multiplayer feel right over real networks — local input that responds
  instantly, remote players that never teleport, and both machines agreeing on outcomes.
  Use when building realtime multiplayer, or when multiplayer feels laggy, the other player
  jumps or rubber-bands or warps, inputs feel delayed or mushy or floaty, players pass
  through each other, or two clients disagree about a collision, a score, a lap time or who
  won. Covers client-side prediction, server reconciliation, entity interpolation, fixed
  timestep simulation, and WebRTC data channel configuration.
allowed-tools: Read, Write, Edit, Glob, Grep, Bash
---

# Realtime netcode

## Why this skill exists

The default implementation is: send your position on a timer, and when a position arrives
for the other player, lerp toward it. This works perfectly on localhost and falls apart the
moment latency varies. It produces exactly three symptoms — the remote player teleports,
your own input feels heavy, and the two machines quietly disagree about what happened.

Those are not three bugs. They are one design error: **using a single timeline where three
are required.**

## 1 — Diagnose before you build

You are most often called against code that already exists. Start here.

| Symptom | Almost always |
|---|---|
| Remote player teleports or warps on a straight line | Interpolation delay shorter than actual jitter, or extrapolating past the end of the buffer |
| Remote player rubber-bands back and forth | Correcting the *rendered* position directly instead of a decaying error offset |
| Local input feels heavy, delayed, floaty | Waiting for the round trip instead of predicting locally |
| Feels fine alone, bad with two players | No prediction; the local player is being treated like a remote one |
| Agrees at low speed, disagrees in corners or on impact | Quantisation asymmetry, or mismatched tick rates between peers |
| Occasional large snap after a period of smoothness | Reconciliation without error smoothing |
| Desyncs slowly over a long session | Attempting deterministic lockstep in a browser (see §4) |
| Everything degrades together under load | Channel backpressure — stale state queued and delivered as a burst |

`references/diagnosis.md` expands each row with what to instrument.

## 2 — Three timelines

Hold this model; everything below serves it.

- **The local player runs ahead.** Input is simulated immediately, before any confirmation.
- **The remote player runs behind.** Rendered at a deliberate delay, inside a buffer, so
  there is always data on both sides of the moment being drawn.
- **Shared authoritative state sits between them**, and both ends reconcile toward it.

Collapsing these into one clock is the original error.

## 3 — Fixed timestep is the prerequisite

A physics integrator's behaviour is a function of the step size you hand it. Feed it "however
long the last frame took" and the simulation becomes a function of the machine's framerate:
springs diverge, fast objects tunnel through walls, handling changes with the monitor.

Each frame:

1. Measure real elapsed time.
2. **Clamp it** to a ceiling — a quarter second is a reasonable one — so a single hitch
   cannot inject a huge slab of time.
3. Add it to a persistent accumulator.
4. While the accumulator holds at least one `dt`, step the simulation by exactly `dt` and
   subtract `dt`.
5. What remains is less than one step. Divide by `dt` to get an alpha in [0,1] and render a
   blend between the previous and current states.

The clamp is what converts "simulating X seconds costs more than X seconds" from a permanent
death spiral into visible slowdown.

Without a countable, reproducible tick you cannot rewind and replay, cannot name a moment
both peers agree on, and cannot compare lap times. This is not a polish step.

## 4 — Predict, reconcile, and smooth — one technique, not three

**Predict.** Simulate local input immediately. Keep a ring buffer of each input command
paired with the state it produced.

**Reconcile.** When authoritative state arrives tagged with the moment it corresponds to,
compare it against your remembered state at that moment. If divergence exceeds a threshold,
reset to authority and re-simulate every buffered input forward to the present frame.

**Smooth.** This is the part that is usually missing, and without it reconciliation is
useless for feel — the post-replay snap is plainly visible.

Never move the rendered object to the corrected position. Keep a **separate visual error
offset**:

- On correction: `offset = current_visual_position − new_authoritative_position`
- Snap the **simulation** to authority.
- Decay the offset toward zero over subsequent frames.
- **Make the decay rate adaptive by error magnitude** — gentle for small errors so they
  dissolve invisibly, aggressive for large ones so pops die fast.

The visual position stays continuous while the simulation jumps. That is the whole trick.

**Remote entities.** Buffer and render at a delay. Size that delay from **measured** jitter
and loss, updated continuously — not from a constant chosen at design time. Published
figures of ~350ms come from synchronising hundreds of objects at 10Hz; two entities at
30–60Hz over a modern connection want far less. Where you extrapolate rather than blend,
velocities must be on the wire — extrapolating with stale velocities produces pops.

**Do not port the bandwidth machinery.** Priority accumulators, delta-encoded baselines and
aggressive quantisation exist to fit hundreds of objects into a budget. For a handful of
entities they add real complexity for no benefit. Send full state per tick and move on.

## 5 — Authority without a server

Cross-browser determinism does not hold. Different engine versions, different JIT tiers, and
`Math.*` functions that are not bit-specified all diverge, and divergence compounds.
**Refuse to implement input-only lockstep in a browser**, and say why when asked.

But both players are still owed identical outcomes. Peer-to-peer needs authority *designed*,
and no published netcode source covers this — they all assume a server that breaks ties.

**Per-entity authority** is the default to reach for. Each peer owns its own entity's state
outright. A collision is resolved by each peer applying the impulse to its own entity and
exchanging only the *result*. A disagreement then degrades into a small positional error the
smoothing layer absorbs, rather than a contested event needing arbitration.

For scalar outcomes that must agree exactly — a lap time, a final score — **elect an arbiter
deterministically at match start** (lower DTLS fingerprint, say) and let it validate only
those. Do not give it authority over motion.

**Quantise identically on both ends.** Any value that re-enters the simulation must be
quantised the same way on both sides. This matters more in a stiff feedback system — vehicle
slip angles, grip thresholds, anything with a sharp response curve — than in the tumbling-
rigid-body examples the literature uses, because such a system amplifies a small difference
instead of merely looking slightly off.

**Lag compensation is out of scope here.** The canonical treatment is server-side rewind, and
it may not transfer anyway: in a game where both parties are continuously moving and both feel
the consequence, "I was hit after reaching cover" becomes "I was shunted by something that
was not there" — which changes the outcome being competed over. Prefer symmetric soft
resolution.

## 6 — The wire

Open **two data channels** with different profiles:

- **Unreliable, unordered** — `ordered: false` plus exactly one of `maxRetransmits: 0` or
  `maxPacketLifeTime`. **Setting both throws.** Carries per-tick state and input.
- **Reliable, ordered** — match start, lap confirmation, rematch, chat.

Use `negotiated: true` with fixed ids on both sides to skip the in-band open handshake.

**With `ordered: false`, carry your own sequence number and discard anything older than the
newest already applied.** The browser hands you a message-oriented channel that superficially
behaves like a reliable one, so this is easy to forget — and readers of classic netcode
material never hit it because they wrote their own UDP layer where it was obvious.

Watch `bufferedAmount` against `bufferedAmountLowThreshold`. A congested channel silently
queues state that arrives later as a burst of stale data, which looks like a network problem
and is not.

**Input loss.** Repack the last N input frames into every outgoing packet — around 90 bytes
buys roughly 120 frames. A dropped *state* packet is harmless because the next supersedes it;
a dropped *input* packet corrupts the peer's replay. This is the cheapest reliability win
available and it is usually filed under lockstep material that peer-to-peer projects skip.

**Clock agreement.** Every source assumes the server's tick is the clock. Peers must
establish one: estimate the offset by ping, filter on **minimum observed RTT** (the least
delayed sample is the least polluted), and state a drift policy. Interpolation delay and any
shared timing both depend on it.

`references/webrtc-channels.md` covers configuration, sequencing, backpressure and session
lifecycle.

## 7 — Refusals and hand-backs

- **Refuse** input-only deterministic lockstep in a browser. Explain the determinism problem.
- **Refuse** to grant both peers simultaneous authority over the same scalar outcome.
- **Hand back** the topology question. Who arbitrates, and what a disagreement costs the
  loser, is a game-design decision wearing an engineering costume. Present the options and
  their felt consequences; let the user choose.

## Reference files

| File | Contents | Load when |
|---|---|---|
| `references/diagnosis.md` | Symptom table expanded, with what to instrument for each | Invoked against existing code |
| `references/webrtc-channels.md` | Channel config, sequencing, backpressure, session lifecycle | Writing the transport |

## Done means

- The simulation steps at a fixed `dt` with an accumulator and a clamp, independent of framerate
- Local input produces visible response in the same frame, with no round trip in the path
- Corrections move the simulation instantly and the rendered position gradually — no visible
  snap under induced latency and loss
- The remote entity does not teleport under induced jitter, and the interpolation delay
  changes as measured jitter changes
- Both clients report identical values for every outcome that is competed over
- Two channels exist with distinct profiles, and the unordered one rejects stale sequences
- Dropping a few percent of input packets does not corrupt the peer's replay
