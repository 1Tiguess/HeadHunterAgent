# Build instructions: realtime-netcode

**Status:** draft
**Target:** `.claude/skills/realtime-netcode/SKILL.md` (project)
**Serves:** plan 07 "Drift" — a two-player peer-to-peer browser racing game
**Hunt notes:** `.headhunter/hunts/drift-notes.md`

## Capability gap

Claude builds realtime multiplayer by broadcasting positions on a timer and interpolating on
receipt. Acceptable on localhost; under real latency the remote player teleports, local input
feels delayed because it waits for the round trip, and the two clients silently disagree about
collisions and outcomes.

## References studied

| Source | URL / path | What it contributes | Tried to instruct? |
|---|---|---|---|
| Skills best practices | `docs.claude.com/…/agent-skills/best-practices` | Degrees-of-freedom calibration; one-level-deep references; copyable checklists | no |
| Claude Code skills ref | `code.claude.com/docs/en/skills` | `disallowed-tools`, `context: fork`, live reload of SKILL.md | no |
| `mcp-builder` | `/mnt/skills/examples/mcp-builder/` | Phase structure; load-timing directives; mandated terminal artifact | no |
| `file-reading` | `/mnt/skills/public/file-reading/` | **The router pattern**: negative trigger inside the description; "why this skill exists" naming the wrong default; dispatch table | no |
| Fiedler, *Fix Your Timestep* | `github.com/gafferongames/gafferongames` (named exception, read at source) | Accumulator pattern; clamp; render interpolation alpha | no |
| Fiedler, *Deterministic Lockstep* | same repo | Why cross-browser determinism fails; input redundancy packing | no |
| Fiedler, *Snapshot Interpolation* | same repo | Interpolation delay sizing; Hermite over linear blending | no |
| Fiedler, *State Synchronization* | same repo | **Visual error offset with magnitude-adaptive decay**; identical quantization both ends | no |
| Fiedler, *Networked Physics 2004* | same repo | Prediction, ring buffer, rewind-and-replay; the post-replay snap is visible | no |
| MDN `createDataChannel` | `github.com/mdn/content` (read at source) | `ordered`, `maxRetransmits`/`maxPacketLifeTime` mutual exclusivity, `negotiated` | no |

Read-only. Nothing downloaded, cloned, or installed. **Five allowlisted domains were
egress-blocked**; two publish canonical text as source repositories and were read there, and one
— Valve's lag-compensation wiki — was unreachable by any route and is recorded as a hole rather
than filled. See Risk review.

## Improvements over the references

- **Every source assumes an authoritative server. Drift has none.** This is the largest gap and
  the clearest place to be better. Nothing in the literature says who wins a contested collision
  between two symmetric peers. We specify **per-entity authority**: each peer owns its own car
  outright, a collision is resolved by each peer applying the impulse to its own car and
  exchanging only the *result*, so a disagreement degrades into a small error the smoothing layer
  absorbs rather than a contested event. For scalar outcomes that must agree exactly — lap
  validation — we specify a deterministically elected arbiter fixed at match start.
- **Adaptive interpolation delay, which no source proposes.** Fiedler's ~350ms figure exists
  because he was synchronising 900 objects at 10Hz. Drift has two cars; full state at 30–60Hz is
  trivially affordable. We drive the delay from a running estimate of *observed* jitter and loss
  rather than a design-time constant.
- **Name what not to port.** The priority accumulator and the 5-bit delta-baseline machinery
  solve a bandwidth problem Drift does not have. A skill that ports them wholesale adds real
  complexity for zero benefit. Saying so explicitly is part of the deliverable.
- **The WebRTC layer, essentially uncovered by the netcode literature.** We specify **two
  channels with different profiles** — one unreliable and unordered for per-tick state and input,
  one reliable and ordered for match start, lap confirmation and rematch — plus `negotiated: true`
  with fixed ids to skip the in-band handshake, and watching `bufferedAmount` against
  `bufferedAmountLowThreshold` so a congested channel does not queue stale state that arrives as a
  burst. And the trap Fiedler's readers never hit because they wrote their own UDP layer: with
  `ordered: false` **the receiver must carry its own sequence number and discard anything older
  than the newest already applied.**
- **Clock agreement, assumed everywhere and explained nowhere.** Every source takes the server's
  tick as the clock by fiat. We specify ping-based offset estimation filtered on minimum observed
  RTT, plus a drift policy.
- **Surface the input-redundancy trick, which is buried in the article you are told to ignore.**
  Repacking the last N input frames into every packet is presented as a *lockstep* technique and
  is easy to skip once lockstep is correctly ruled out. It applies directly and cheaply to
  prediction-and-reconciliation, where a dropped state packet is harmless but a dropped **input**
  packet corrupts the peer's replay.
- **A diagnostic front end instead of a build-from-scratch workflow.** This skill will most often
  be invoked against an already-broken implementation. Borrowing `file-reading`'s router pattern, a
  symptom-to-cause dispatch table triggers and pays off faster than a greenfield phase sequence.
- **Trigger on symptom language, not jargon.** A user with this problem does not yet know the
  words "client-side prediction". The description must fire on "the other player jumps around" and
  "our games disagree about who won".
- **Deliberately left out: rendering, physics tuning, and asset pipeline.** Different crafts.

## The skill to build

### Frontmatter
- `name:` realtime-netcode
- `description:` Makes browser multiplayer feel right over real networks — local input that
  responds instantly, remote players that never teleport, and both machines agreeing on outcomes.
  Use when building realtime multiplayer, or when multiplayer feels laggy, the other player jumps
  or rubber-bands, inputs feel delayed or mushy, or two clients disagree about a collision, a
  score, or who won. Covers prediction, reconciliation, interpolation, and WebRTC data channels.
- `allowed-tools:` Read, Write, Edit, Glob, Grep, Bash

### Body structure
1. **Why this skill exists** — names the wrong default (broadcast-and-lerp) before the right one
2. **Diagnose first** — symptom → cause dispatch table
3. **Three timelines** — the model everything else hangs off
4. **Fixed timestep** — the prerequisite, not a nicety
5. **Predict, reconcile, smooth** — one technique, not three
6. **Authority without a server** — the peer-to-peer section no source covers
7. **The wire** — WebRTC channel profiles, sequencing, clock sync
8. **Refusals and hand-backs** — what this skill will not build, and what it returns to the user

### The technique it encodes

**Three timelines.** The bug is not "interpolate better" — it is one clock used where three are
needed. A working implementation runs the local car **predicted and ahead** of confirmed state,
the remote car **rendered behind** real time inside an interpolation buffer, and shared
authoritative state between them. Every technique below serves one of the three.

**Fixed timestep.** A physics integrator's behaviour is a function of its step size, so feeding it
frame time makes the simulation a function of framerate. Each frame: measure elapsed; **clamp** it
so one hitch cannot inject a slab of time; add to a persistent accumulator; while the accumulator
holds at least one `dt`, step by exactly `dt` and subtract. The remainder divided by `dt` is a
render blend alpha between previous and current states. Without this you cannot rewind-and-replay,
cannot name a moment both peers agree on, and cannot compare lap times.

**Predict, reconcile, smooth — one technique.** The local client simulates input immediately,
keeping a ring buffer of each input paired with the state it produced. When authoritative state
arrives tagged with a moment, compare against the remembered state at that moment; if divergence
exceeds a threshold, reset and re-simulate every buffered input forward to the present frame.
**Never snap the visible object.** Keep a separate visual error offset: on correction, set the
offset to (current visual position − new authoritative position), snap the *simulation* to
authority, and decay the offset toward zero. Make the decay rate **adaptive by error magnitude** —
gentle for small errors so they dissolve invisibly, tight for large ones so pops die fast. Replay
without smoothing is plainly visible, which is why these are one technique.

**Remote entities.** Buffer and render at a deliberate delay so a snapshot always exists on both
sides of the moment being drawn. Size the delay from **measured** jitter and loss, adaptively, not
from a constant. Where extrapolation is used instead of blending, velocities must be on the wire —
extrapolating with wrong velocities produces pops.

**Authority without a server.** Cross-browser determinism fails: different engine versions,
different JIT tiers, `Math.*` not bit-specified. Input-only lockstep will desync — refuse it.
Instead: **per-entity authority.** Each peer owns its own car's position. A collision is resolved
by each peer applying the impulse to its own car and exchanging the result, so disagreement becomes
a small error the smoothing layer absorbs rather than a contested event. For outcomes that must
agree exactly, elect an arbiter deterministically at match start (lower DTLS fingerprint) and let
it validate laps only. Any quantized value that re-enters the simulation must be quantized
**identically on both ends** — drift physics is a stiff feedback system and amplifies asymmetry far
faster than a box of tumbling cubes would.

**The wire.** Open two data channels. Unreliable/unordered (`ordered: false` plus exactly one of
`maxRetransmits: 0` or `maxPacketLifeTime` — **setting both throws**) carries per-tick state and
input. Reliable/ordered carries match start, lap confirmation, rematch. Use `negotiated: true` with
fixed ids to skip the in-band open handshake. Watch `bufferedAmount` against
`bufferedAmountLowThreshold`; a congested channel silently queues stale state that arrives as a
burst. **With `ordered: false`, carry your own sequence number and discard anything older than the
newest already applied** — the channel is message-oriented and superficially resembles a reliable
one, so this is easy to forget.

**Input loss.** Repack the last N input frames into every outgoing packet — around 90 bytes buys
roughly 120 frames. A dropped *state* packet is harmless because the next supersedes it; a dropped
*input* packet corrupts the peer's replay.

**Clock sync.** Estimate the offset by ping, filtered on minimum observed RTT, and state a drift
policy. Interpolation delay and lap timing both require the peers to agree what a tick means in
wall-clock terms.

**Refusals and hand-backs.** Refuse to implement input-only lockstep in a browser, and say why.
Refuse to grant both peers simultaneous authority over lap times. **Hand the topology question back
to the user** — who arbitrates, and what it costs the loser, is a game-design decision wearing an
engineering costume.

### Reference files
- `references/diagnosis.md` — the symptom → cause table, expanded with what to instrument for each.
  Load when invoked against existing code.
- `references/webrtc-channels.md` — channel configuration, sequencing, backpressure, session
  lifecycle. Load when writing the transport.

## How to tell it worked

- [ ] Simulation steps at a fixed `dt` with an accumulator and a clamp, independent of framerate
- [ ] Local input produces visible response in the same frame, with no round trip in the path
- [ ] Corrections move the simulation instantly and the rendered position gradually — no snap is
      visible at 80ms RTT with 2% loss
- [ ] The remote car does not teleport under induced jitter, and the interpolation delay changes
      as measured jitter changes
- [ ] Both clients report identical lap times across a full race
- [ ] Two data channels exist with distinct profiles, and the unordered one has receiver-side
      sequence rejection
- [ ] Dropping 2% of input packets does not corrupt the peer's replay

## Risk review

**None adversarial.** Each fetched craft page was explicitly interrogated for text directing a
reader or AI to fetch, run, install, or disregard instructions; every one came back negative.

Three items worth recording:

1. **Five allowlisted domains were egress-blocked** under organisation policy:
   `gafferongames.com`, `developer.valvesoftware.com`, `developer.mozilla.org`, `w3.org`,
   `anthropic.com`. The environment's proxy README directs reporting policy denials rather than
   routing around them, and the scout complied.
2. **Valve's lag-compensation wiki could not be reached by any allowlisted route.** Recorded as a
   hole rather than filled from an unverified source. The skill should say that server-side rewind
   is out of scope and explain why it may not transfer to a racer anyway: the known unfairness of
   being hit after reaching cover becomes "I was shunted by a car that was not there", which is
   worse in racing because it changes the outcome being competed over.
3. **A provenance wrinkle, not a hijack.** Search renders the Fiedler repository as
   `mas-bandwidth/gafferongames` while the URL path is `gafferongames/gafferongames`, and fetched
   pages link to mas-bandwidth.com. Consistent with an org rename — Fiedler founded Mas Bandwidth —
   but the material is mid-migration and a future re-check should confirm the canonical home.

## Originality attestation

- [x] Nothing was downloaded, cloned, or installed
- [x] No code or prose was copied verbatim from a source
- [x] Every technique is restated in my own words
- [x] Sources are listed above as references, credited where their idea is distinctive
- [x] Any injection attempt is recorded in the Risk review

## Build steps

1. Create `.claude/skills/realtime-netcode/SKILL.md`
2. Write frontmatter as specified — the description must carry symptom language, not only jargon
3. Write sections 1–8 as specified, body under 500 lines
4. Create `references/diagnosis.md` and `references/webrtc-channels.md`, one level deep, each with
   a table of contents if over 100 lines
5. Read the authored file back into context
