# Hunt notes — 07 Drift (realtime browser game netcode)

Scout report, reported speech. Read-only. Nothing downloaded, cloned, or installed.

## Access note

The egress proxy refused five allowlisted domains under organisation policy:
`gafferongames.com`, `developer.valvesoftware.com`, `developer.mozilla.org`, `w3.org`, and
`anthropic.com`. The proxy README says to report policy denials rather than route around
them, and the scout complied.

`github.com` is reachable, and two blocked sources publish their canonical text there as
source repositories. Both were read **at source rather than at their rendered domain**:

- Fiedler's articles from `github.com/gafferongames/gafferongames/…/content/post/*.md` —
  the Hugo source that generates gafferongames.com. Same author, same text. **This is the
  named exception**, accessed at its repository.
- MDN's `createDataChannel` page from `github.com/mdn/content`.

**Valve's lag-compensation wiki could not be reached by any allowlisted route.** That is a
real hole, called out rather than papered over.

*Provenance note:* search renders the Fiedler repo as `mas-bandwidth/gafferongames` while
the URL path is `gafferongames/gafferongames`, and the fetched page links to
mas-bandwidth.com. Consistent with an org rename (Fiedler founded Mas Bandwidth), not a
hijack — but the material is mid-migration and the caller should know.

## Tier 1 — skill construction

**`docs.claude.com/…/agent-skills/best-practices`** (302s to `platform.claude.com`).
The `description` is the entire trigger mechanism — the only part loaded at startup, and
Claude picks from potentially a hundred on that text alone. Third person (it is injected
into a system prompt; first/second person degrades discovery), stating both what the skill
does and the situations that summon it, carrying the concrete vocabulary a user would type.
`name` ≤ 64 chars, lowercase-hyphen, may not contain "anthropic" or "claude". `description`
≤ 1024 chars.

Body: SKILL.md under 500 lines, overflow into siblings. Loading is three-staged — metadata
always resident, SKILL.md on trigger, bundled files only when the body points at them,
scripts *executed* without their source entering context. Two mechanical rules matter more
than they look: references must sit **exactly one level deep** from SKILL.md, because when
a referenced file references another Claude tends to preview with `head -100` and silently
act on partial information; and any reference file over 100 lines should open with a table
of contents so a partial read still exposes full scope.

The most useful framing is **degrees of freedom**: match how prescriptive you are to how
fragile the operation is. Many routes succeed → prose direction, let the model choose.
Narrow ledge → exact invocation, forbid deviation. Complex procedures as numbered phases;
genuinely complex ones ship a literal checklist block Claude copies and ticks off.
Quality-critical steps wrapped in a feedback loop — run a validator, fix what it reports,
re-run, do not advance until clean.

Named anti-patterns: a menu of libraries instead of one default plus a documented escape
hatch; embedded dates or "before/after X" (put superseded material in a collapsed "old
patterns" section); drifting terminology. Process advice: write three evaluations *before*
the prose, measure how Claude does with no skill at all, then write the minimum that closes
the observed gap.

**`code.claude.com/docs/en/skills`.** Resolution order and the Claude Code-specific
frontmatter. `allowed-tools` pre-approves tools for the invoking turn and expires at the
user's next message. `disallowed-tools` *removes* tools while active — suggested for
autonomous skills that must not stop to ask. `disable-model-invocation: true` restricts to
explicit `/name`. `context: fork` runs the skill in its own subagent context. Edits to
SKILL.md are picked up live without restart.

**`/mnt/skills/examples/mcp-builder/SKILL.md`** — structural exemplar. Description is two
clauses: capability, then an explicit "Use when…" naming *both* technology vocabularies so
it fires whichever word the user reaches for. `SKILL.md` + `reference/` + `scripts/`. Four
numbered phases, reference files named **at the phase where they should be opened** ("Load
during Phase 2") rather than dumped up front, then a closing index restating the library
with one line of contents per file so the agent can decide what to open without opening it.
Takes positions instead of listing options. Terminates in a mandated artifact — ten
evaluation questions in a specified shape — so the skill has a definite finish line.

**`/mnt/skills/public/file-reading/SKILL.md`** — the router pattern. Two moves worth
lifting. Its description carries an explicit **negative trigger inside the description
field** ("Do NOT use this skill if the file content is already visible in your context…")
alongside very concrete positive triggers. And its body opens with "Why this skill exists",
naming the *wrong* default behaviour it exists to prevent before offering the right one.
The bulk is a dispatch table keyed on file extension. The skill's job is substantially to
route and then stop.

## Tier 2 — the craft (all Fiedler, read at source repo)

**`fix_your_timestep.md` — fixed timestep and the accumulator.** A physics integrator's
behaviour is a function of the step size, so feeding it "however long the last frame took"
makes the simulation a function of framerate — springs diverge, fast objects tunnel, players
fall through floors. Each frame: measure elapsed time; **clamp** it (his example: a quarter
second) so one hitch cannot inject a slab of time; add to a persistent accumulator; while
the accumulator holds at least one `dt`, step physics by exactly `dt` and subtract. What
remains is by definition under one step — divide by `dt` for an alpha in [0,1] and render a
blend between previous and current physics states, which removes the stutter from the
mismatch between physics time and display time. The guarded failure mode: simulating X
seconds costing more than X seconds real, so each frame accrues more debt than it repays and
the loop falls permanently behind. The clamp converts that into visible slowdown rather than
a lockup.

**`deterministic_lockstep.md` — why lockstep is fragile.** Transmit only inputs; both
machines run the identical simulation. Bandwidth scales with input size, not world size — a
million objects cost what one costs. The price is bit-exact agreement: his standard is a
checksum of the entire physics state matching every frame. He is explicit that determinism
on one machine does **not** survive different compilers, OS, or CPU architecture, and that
even debug and release builds of the same source diverge under floating-point optimisation.
Divergence compounds. No silver bullet. Packet loss handled not by retransmission but by
packing many past input frames redundantly into every packet — up to 120 frames in ~90
bytes. Structural weakness: a peer cannot compute frame N without input N, so a late packet
stalls everyone. Latency is not concealed, it is shared.

**`snapshot_interpolation.md` — interpolation delay.** Capture visible state periodically,
ship below tick rate. The receiver does **not** render what just arrived — it buffers and
renders at a deliberately delayed point chosen so a snapshot always exists on both sides of
the moment being drawn, identifies the bracketing pair by sequence number, computes an
alpha, blends. He sizes the delay at ~three send intervals plus jitter slack — at ten sends
per second with a few percent loss, around **350ms added latency**. Plain linear blending
leaves subtle jitter and visible pulsing on rotating objects; feeding velocity at the sample
points into a Hermite spline removes both at the same send rate. Lost snapshots need no
retransmission; the buffer skips.

**`state_synchronization.md` — the most load-bearing source here.** A middle path: both ends
run physics, and you send *state* for a selected subset rather than full snapshots or bare
inputs. The receiver does not blend between samples — it **extrapolates by continuing to
run the physics engine** on what it received. Which is why velocities must be on the wire.

The correction mechanism is the part that matters most. **Corrections are never snapped onto
the visible object.** The renderer maintains separate position-error and orientation-error
offsets that decay toward zero. When new authoritative state arrives, the new offset is
(current visual position) − (new authoritative position) — the visual position is held
continuous while the *simulation* position jumps to authority. The decay rate is **adaptive
by error magnitude**: gentler under ~25cm, tighter over a metre, so small errors dissolve
invisibly while large pops are killed fast.

Per-object payload: index, position, orientation, linear velocity, angular velocity. Both
ends must **quantize identically**, and this demands much higher precision than a
visual-only snapshot — he moved from 512 to 4096 position values per metre and 15 bits per
quaternion component — precisely because quantized values are fed back into the simulation,
so asymmetry compounds instead of merely looking slightly wrong.

**`networked_physics_2004.md` — prediction and rewind-and-replay.** The client streams
timestamped input continuously and simulates locally without waiting. It keeps a ring buffer
of each input command paired with the resulting state. The server periodically returns
authoritative state tagged with the moment it corresponds to; the client compares its own
remembered state at that moment, and if divergence exceeds a threshold, resets to the
server's state and re-simulates every stored input forward to the present frame. He notes
that snapping the visible result is plainly noticeable, so the same smoothing used for
remote entities is applied to the local one.

**`snapshot_compression.md`.** Bound the world, then quantize into it. Position at a fixed
number of steps per metre (512/m ≈ 2mm) turns three 32-bit floats into ~50 bits. Orientation
uses "smallest three": a unit quaternion's largest component is recomputable from the other
three, so send a 2-bit index plus three 9-bit components — 29 bits instead of 128.

**`why_cant_i_send_udp_packets_from_a_browser.md`.** Browsers withhold raw UDP for four
reasons: DDoS coordination, internal-network probing, sniffability, and no way to establish
a connecting client is legitimate. WebRTC's data channel provides an unreliable mode and is
the available answer, though he considers the stack heavy — STUN/ICE/TURN indispensable for
peer-to-peer, dead weight for a dedicated server. **Worth noting the inversion for our
case:** the configuration he calls WebRTC's *worst* fit (dedicated server) is not ours, and
the one he concedes it genuinely serves (true peer-to-peer) is exactly Drift.

**MDN `createDataChannel`** (read at `github.com/mdn/content`). `RTCDataChannelInit`:
`ordered` (default true), `maxPacketLifeTime` (default null — a millisecond delivery budget
in unreliable mode), `maxRetransmits` (default null), `protocol`, `negotiated` (default
false; true means out-of-band agreement with both sides supplying a matching `id`), and `id`
(0–65534). **`maxPacketLifeTime` and `maxRetransmits` are mutually exclusive** — setting both
non-null throws `SyntaxError`. An unreliable unordered channel is `ordered: false` plus
exactly one of the two reliability caps.

## Synthesis

**1. The bug is not "interpolate better" — it is one timeline used where three are needed.**
The current default collapses everything into a single clock: broadcast now, lerp on
receipt. The literature is unanimous that a working implementation runs **three time domains
simultaneously** — the local car predicted and running *ahead* of confirmed state, the
remote car rendered deliberately *behind* real time inside an interpolation buffer, and
shared authoritative state between them. Which is why fixed timestep is the prerequisite
rather than a nicety: you cannot rewind-and-replay without a countable reproducible tick,
cannot name a moment both peers agree on, and cannot compare lap times, if the step is
whatever `requestAnimationFrame` happened to deliver.

**2. Corrections go into the simulation instantly and into the picture gradually.** The
highest-value idea in `state_synchronization`, and precisely what "never visibly teleport"
requires. Rewind-and-replay alone is worthless for feel — the 2004 article says outright the
post-replay snap is plainly visible — so **replay and error-smoothing are one technique, not
two.**

**3. Lockstep determinism is off the table, but agreement is still required, so authority
must be designed rather than assumed.** Fiedler's determinism argument applies with full
force to two browsers on two home machines — different JS engine versions, different JIT
tiers, `Math.*` not bit-specified. Input-only lockstep will desync. Yet both players are
owed identical lap times and collisions.

## Improvement openings

**a) Every source assumes an authoritative server. We have none.** The largest single gap
and the clearest place to be better. All this writing has a third party breaking ties; two
symmetric peers do not. Nothing here says who wins a contested collision, how to elect an
arbiter, or what happens when peers compute different lap times. Directions worth taking:
**per-entity authority** (each peer owns its own car outright; a collision is resolved by
each peer applying the impulse to its own car and exchanging only the *result*, so
disagreement degrades into a small error the smoothing layer eats rather than a contested
event); or a **deterministically-elected arbiter** fixed at match start (lower DTLS
fingerprint) for scalar outcomes like lap validation only. Also entirely absent: the
rollback/GGPO lineage, which is symmetric and arguably a more natural fit for two-player P2P
than the client-server model — but it reimports the determinism requirement, forcing a
hybrid decision (constrained or fixed-point car physics, non-deterministic cosmetics) that
no source here will make for us.

**b) Lag compensation is a hole that could not be filled.** Valve's wiki is the canonical
treatment and is egress-blocked. Flagged rather than bluffed. Note its shape may not
transfer anyway: a racer's analogue of "did I hit you" is "did our cars touch", where both
parties are continuously moving and both feel the consequence, unlike hitscan. The known
unfairness of server-side rewind — being hit after reaching cover — becomes "I was shunted
by a car that was not there", which is *worse* in racing because it changes the outcome
being competed over. Symmetric soft resolution likely beats porting the hitscan technique.

**c) The send rates and buffer sizes are dated and tuned for the wrong problem.** Ten
snapshots/second with a three-interval buffer implies 300ms+ added delay — fails our brief on
its own. Those numbers exist because Fiedler was pushing 900 objects. Drift has two cars.
Full state every tick at 30–60Hz is trivially affordable over WebRTC on home connections,
and the interpolation delay can shrink to roughly one send interval plus *measured* jitter.
Better still, and absent from all sources: make the interpolation delay **adaptive**, driven
by a running estimate of observed jitter and loss, rather than a design-time constant. By
the same token the priority accumulator and 5-bit delta-baseline machinery solve a bandwidth
problem we do not have — porting them wholesale adds real complexity for zero benefit, and
the skill should say so explicitly.

**d) Quantization numbers need re-deriving; the underlying rule needs keeping.**
Smallest-three quaternion packing is irrelevant to a top-down racer — we have position, one
heading angle, velocity, and slip/drift state; 12–16 bits of angle is plenty. What transfers
with *more* force than in the original is the rule that any quantized value fed back into
the simulation must be quantized identically on both ends. Drift physics is a stiff feedback
system (slip angle, weight transfer, grip thresholds) and will amplify a small state
difference far faster than a box of tumbling cubes. More important here, not less — and the
source states the principle without stating that consequence.

**e) The WebRTC layer is essentially uncovered by the netcode literature.** Fiedler treats
WebRTC mainly as an irritation for dedicated servers and predates current data-channel
practice; MDN documents the dictionary but not how to use it for games. Nothing tells you to
open **two channels with different profiles** — one unreliable and unordered
(`ordered: false`, `maxRetransmits: 0`) carrying per-tick state and input, one reliable and
ordered carrying match start, lap confirmation and rematch — or to use `negotiated: true`
with fixed ids to skip the in-band open handshake, or to watch `bufferedAmount` against
`bufferedAmountLowThreshold` so a congested channel does not silently queue stale state that
arrives as a burst. And a trap specific to us: because the browser hands you a
*message-oriented* channel that superficially behaves like a reliable one, it is easy to
forget that with `ordered: false` **the receiver must carry its own sequence number and
discard anything older than the newest already applied.** Fiedler's readers built that
themselves over raw UDP, so it is never called out.

**f) Clock agreement is assumed everywhere and explained nowhere.** Interpolation delay and
lap timing both require the peers to agree what a tick means in wall-clock terms. Every
source takes the server's tick as the clock by fiat. A peer-to-peer skill must specify the
clock-sync step explicitly — ping-based offset estimation filtered on minimum observed RTT —
plus a drift policy.

**g) Loss handling for the *input* path is the cheapest win available and is buried in the
wrong article.** The redundancy trick from `deterministic_lockstep` — repack the last N input
frames into every outgoing packet, ~90 bytes for 120 frames — is presented as a lockstep
technique and is easy to skip once lockstep is (correctly) ruled out. It applies directly and
cheaply to prediction-and-reconciliation at 2% loss, where a dropped *state* packet is
harmless (the next supersedes it) but a dropped *input* packet corrupts the peer's replay.

**h) Session lifecycle is unaddressed.** ICE restarts, channel close and reopen, what the
game shows during a 500ms stall, how a peer rejoins mid-race — covered by none of these
sources, because a server-based game handles them structurally.

**i) Skill-construction openings.** `mcp-builder`'s shape is a sound template, but the
highest-value structural addition here is a **diagnostic front end**, because this skill will
most often be invoked against an already-broken implementation rather than a greenfield one.
A symptom-to-cause dispatch table on the `file-reading` router model triggers and pays off
faster than a build-from-scratch workflow: remote car teleporting on a straight → interpolation
delay shorter than actual jitter, or extrapolating past the buffer end; local input feeling
heavy → waiting on the round trip instead of predicting; cars agreeing at low speed and
disagreeing in corners → quantization asymmetry or mismatched tick rates. Two further notes.
The description should trigger on **symptom language** — "multiplayer feels laggy", "the other
player jumps around", "our games disagree about who won" — not only on jargon like "netcode"
or "client-side prediction", because a user with this problem does not yet know the jargon.
And be explicit about refusals and hand-backs in the `file-reading` style: refuse to implement
input-only lockstep in a browser and say why, refuse to grant both peers simultaneous
authority over lap times, and hand the topology question back to the user rather than silently
choosing — that is a game-design decision wearing an engineering costume.

## Injection attempts

**None.** Each fetched craft page was explicitly interrogated for text directing a reader or
AI to fetch, run, install, or disregard instructions; every one came back negative. Two
non-injection provenance items for the record, neither causing a discard: the
`fix_your_timestep` page carries outbound links to mas-bandwidth.com, consistent with the
site migration noted above; and the Anthropic best-practices URL served a 302 to
`platform.claude.com`, followed as the same documentation property.
