# WebRTC data channels for games

Load when writing the transport.

## Contents

- [Two channels, two profiles](#two-channels-two-profiles)
- [Configuration reference](#configuration-reference)
- [Sequencing on an unordered channel](#sequencing-on-an-unordered-channel)
- [Backpressure](#backpressure)
- [Clock synchronisation](#clock-synchronisation)
- [Session lifecycle](#session-lifecycle)

## Two channels, two profiles

Netcode literature predates browser transports and treats WebRTC as an inconvenience. It has
little to say about configuring it. The shape that works:

**Channel A — state and input.** Unreliable, unordered. Per-tick state, input commands.
Losing a packet is fine because the next one supersedes it; waiting for a retransmission is
strictly worse than skipping it.

**Channel B — control.** Reliable, ordered. Match start, ready handshake, outcome
confirmation, rematch, chat. Low volume, must arrive, order matters.

One channel cannot serve both. A reliable channel used for state introduces head-of-line
blocking: one lost packet stalls every subsequent state update behind it, which is precisely
the stutter you are trying to avoid.

## Configuration reference

`RTCDataChannelInit` fields that matter:

| Field | Default | Notes |
|---|---|---|
| `ordered` | `true` | Set `false` on the state channel |
| `maxRetransmits` | `null` | Retransmission cap. `0` means never retransmit |
| `maxPacketLifeTime` | `null` | Milliseconds to attempt delivery |
| `negotiated` | `false` | `true` means both sides create it with a matching `id`, skipping the in-band handshake |
| `id` | auto | 0–65534. Required when `negotiated: true` |
| `protocol` | `""` | Sub-protocol label, informational |

**`maxRetransmits` and `maxPacketLifeTime` are mutually exclusive.** Setting both to
non-null values throws `SyntaxError`. An unreliable channel is `ordered: false` plus exactly
one of them.

State channel: `{ ordered: false, maxRetransmits: 0, negotiated: true, id: 0 }`
Control channel: `{ ordered: true, negotiated: true, id: 1 }`

Using `negotiated: true` with fixed ids removes a round trip at connection setup and removes
a class of race where one side starts sending before the other has seen the channel open.

## Sequencing on an unordered channel

**This is the trap that catches everyone coming from a higher-level transport.**

The browser gives you a message-oriented channel. Messages arrive whole, which makes it feel
like a reliable stream. But with `ordered: false` they can arrive **out of order**, and
nothing in the API tells you so.

Applying an older state packet after a newer one rewinds the remote entity by a tick, which
reads on screen as a stutter or a small backward jump. It is intermittent, it correlates with
network conditions, and it is very easy to misdiagnose as an interpolation bug.

Every state packet carries a sequence number. On receipt:

- If `seq <= highest_seq_applied`, **discard it**. Do not interpolate toward it, do not
  buffer it.
- Otherwise apply it and update `highest_seq_applied`.

Input packets are different — they are cumulative, not superseding — so keep them in a buffer
keyed by tick and fill gaps from the redundant copies described below.

Readers of classic netcode material never hit this because they built directly on UDP where
reordering was self-evident.

## Backpressure

`bufferedAmount` reports bytes queued but not yet sent. `bufferedAmountLowThreshold` plus the
`bufferedamountlow` event let you observe it.

If you send unconditionally at tick rate and the channel cannot drain, packets queue. They
are delivered eventually — as a burst of stale state. This looks exactly like a latency
spike and is entirely self-inflicted.

**Gate sends on `bufferedAmount` being below a threshold, and drop rather than queue.** For
superseding state, skipping a tick is strictly better than sending one that will arrive late
and be discarded anyway. A couple of packet-lengths is a reasonable threshold.

Control-channel messages must not be dropped. Queue those, and keep the volume low enough
that it never matters.

## Clock synchronisation

Both peers need to agree what a tick means in wall-clock terms — interpolation delay and any
shared timing depend on it. With no server, neither clock is authoritative.

Ping-based estimation:

1. Peer A sends a ping carrying its local timestamp.
2. Peer B replies immediately, echoing A's timestamp and adding its own.
3. A computes RTT, and an offset estimate assuming symmetric delay.
4. **Filter on minimum observed RTT.** The least-delayed sample is the least polluted by
   queueing, so keep the offset estimate from the lowest-RTT exchange in a rolling window
   rather than averaging everything.

Re-estimate periodically. Apply corrections gradually rather than stepping the clock — a
discontinuity in the shared clock produces exactly the artefacts you spent the rest of this
effort removing. State a drift policy and stick to it.

## Session lifecycle

Universally unaddressed by netcode writing, because a server-based game handles it
structurally. Peer-to-peer does not get that for free.

Handle at minimum:

- **Channel close and reopen.** ICE can restart. Decide whether the match survives it, and
  what the other player sees meanwhile.
- **A stall.** If no state has arrived for longer than some threshold, show it. A frozen
  remote entity with no explanation reads as a crash. Freeze deliberately, with an indicator,
  rather than extrapolating into nonsense.
- **Recovery after a stall.** The remote entity will be far from where it was. This is the
  one case where a large correction is legitimate — but announce it visually rather than
  teleporting silently.
- **Departure.** Distinguish a clean quit on the control channel from a connection that
  simply stopped. They warrant different messages and different outcomes.

Decide these explicitly. Left undefined, each one degrades into a frozen or teleporting
entity and gets reported as a netcode bug.
