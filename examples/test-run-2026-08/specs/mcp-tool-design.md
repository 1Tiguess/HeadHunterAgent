# Build instructions: mcp-tool-design

**Status:** draft
**Target:** `.claude/skills/mcp-tool-design/SKILL.md` (project)
**Serves:** plan 06 "Relay" — an MCP server fronting several home-lab REST APIs
**Hunt notes:** `.headhunter/hunts/relay-notes.md`

## Capability gap

Claude builds MCP servers by mirroring an underlying REST API one-to-one, producing dozens of
narrow tools with overlapping names and developer-facing descriptions. The model then picks
the wrong tool, retries blindly on errors that do not say what to change, and blows its
context window on a single unbounded response.

## References studied

| Source | URL / path | What it contributes | Tried to instruct? |
|---|---|---|---|
| Anthropic `mcp-builder` skill | `github.com/anthropics/skills` + `/mnt/skills/examples/mcp-builder/` | Coverage-vs-workflow framing; naming; the load-order-annotated reference index; evals as the terminal deliverable | no |
| Claude tool-use docs | `docs.claude.com/…/tool-use/implement-tool-use` | Description is the largest lever; consolidate operations behind an action parameter; return high-signal fields only | no |
| MCP spec — tools | `github.com/modelcontextprotocol/modelcontextprotocol` `…/server/tools.mdx` | **The two-channel error model**: in-tool failures ride the result so the model can see and act on them | no |
| MCP spec — elicitation | `…/client/elicitation.mdx` | Mid-call human input; three response actions; hard ban on soliciting credentials through form mode | no |
| MCP spec — server index | `…/server/index.mdx` | Tools/resources/prompts separate by *who decides* — model, application, user | no |

Read-only. Nothing downloaded, cloned, or installed. `modelcontextprotocol.io` and
`anthropic.com` were egress-blocked; the spec was read at its canonical source repository and
the engineering post could only be reached via search extraction — claims from it are marked
weak-provenance in the notes and are **not load-bearing here**.

## Improvements over the references

- **A decision procedure for tool granularity, which no source supplies.** `mcp-builder`'s
  stated tie-breaker is "when uncertain, prioritise comprehensive API coverage" — that *is* the
  endpoint-mirroring instruction, and it contradicts the docs page's "consolidate related
  operations". We replace the coin-flip with three questions: does the user's request map to
  one call or a fixed sequence; are two endpoints ever chosen between on the same evidence; is
  this endpoint ever a terminal answer or only ever an intermediate lookup. **Lookups that only
  feed other calls are arguments, not tools.**
- **An error taxonomy by retryability.** Sources say "actionable" and illustrate it once. A
  model told only "actionable" will retry the unfixable. We classify every error as *fix your
  arguments* / *retry unchanged after delay* / *stop and tell the user*, and require the error
  text to say which.
- **Scrub secrets on the error path.** Sources cover keys at rest (environment variables) and
  say nothing about egress. Home-lab APIs commonly authenticate by query parameter, so an
  upstream failure echoed with its request URL leaks the credential into the transcript through
  a path "store keys in env vars" does nothing to close. This is the largest gap for this task.
- **A confirmation fallback for when elicitation is unavailable.** Elicitation is a *client*
  capability that may be absent, and destructive annotations are hints a client may ignore. No
  source says what a server does then. We specify a two-step shape: first call returns a
  preview of exactly what would change plus a short-lived token; the mutation executes only
  when that token returns.
- **Cursor semantics for append-only streams.** The offset/cursor/`has_more` envelope assumes a
  stable collection. A live log grows under the reader and is read newest-first, so numeric
  offsets shift between calls. We anchor to a byte position or timestamp and bound by lines,
  not records.
- **Multi-backend guidance.** Every published naming convention assumes one server fronts one
  service. We specify namespacing by task domain rather than backend, and a degraded-mode
  response shape for partial failure.
- **Deliberately left out: transport implementation detail.** `mcp-builder` covers it well and
  its own default (Streamable HTTP) is wrong for a single-user home lab. We state the criteria
  and pick stdio, then stop.
- **Deliberately left out: the Claude-API-only features.** `input_examples`, strict schema
  enforcement and tool search are Claude API features, not MCP protocol features. A caller
  working from the docs page alone would design for a field that does not exist over the wire.
  We name the boundary explicitly.

## The skill to build

### Frontmatter
- `name:` mcp-tool-design
- `description:` Designs the tool surface of an MCP server so a model picks the right tool
  first time — task-shaped tools rather than one per endpoint, descriptions that make selection
  unambiguous, errors that say what to do next, and bounded responses. Use when building or
  reviewing an MCP server, adding tools to one, or when a model is choosing tools badly,
  retrying blindly, or overflowing context on a single response. Covers Python (FastMCP) and
  Node/TypeScript MCP SDK.
- `allowed-tools:` Read, Write, Edit, Glob, Grep, Bash

### Body structure
1. **Decide the surface before writing a tool** — the granularity decision procedure
2. **Name and describe for selection** — mutual exclusivity as the test
3. **Errors are a control surface** — the retryability taxonomy
4. **Bound every response** — token budget, pagination, append-only streams
5. **Writes and secrets** — confirmation fallback, error-path scrubbing
6. **Ship evals** — including the write and refusal paths `mcp-builder` cannot test

### The technique it encodes

**Granularity.** Start from the tasks a user would ask for, not the endpoint list. For each
candidate tool ask: (a) does a typical request map to this single call, or to a fixed sequence
of calls — if a sequence, that sequence is the tool; (b) would two tools ever be chosen between
on the same evidence — if so they are one tool with an action parameter; (c) is this endpoint
ever a terminal answer, or only ever a lookup feeding another call — if only a lookup, it is a
parameter, not a tool. Prefer few task-shaped tools. Where coverage genuinely matters, add an
escape-hatch tool that takes an operation name, not forty tools.

**Descriptions.** The description is the largest single lever. Minimum three or four sentences
covering: what it does; when it should fire *and when it should not*; what each parameter does
to behaviour; and **what the tool does not return**. The test for the whole surface is mutual
exclusivity — read any two descriptions and ask whether a model could confuse them; if yes,
merge or re-scope. Name as `domain_action_resource` in snake_case, namespaced by **task domain,
not backing service**. For the read/write split, the read tool's description must state in
words that it never mutates and name the write tool that does — the split is a naming and
description problem before it is an architecture problem.

**Errors.** Failures inside a working tool ride the *result* with an error flag, never the
transport, because a result reaches the model and a protocol error generally does not. Classify
every error into exactly one of: **fix-arguments** (validation, unknown id, out of range — say
which argument and what a valid one looks like); **retry-after-delay** (upstream timeout, rate
limit, service restarting — give a concrete duration); **stop-and-escalate** (auth failure,
backend down, permission denied — say plainly that retrying will not help). The error text must
name its class. Before any error leaves the server, scrub it: never echo the outbound request
URL, query string, headers, or raw exception text. Whitelist the fields you emit; do not
blacklist the ones you fear.

**Response bounds.** Give every tool a token budget and enforce it server-side. Return
high-signal fields only, with stable semantic identifiers rather than opaque handles. For
collections: honour a `limit` always, default 20–50, never materialise the full set, and return
an envelope with count, `has_more` and the next cursor. For an **append-only stream** such as a
log tail, a numeric offset is wrong — anchor the cursor to a byte position or a timestamp, bound
by lines rather than records, and state explicitly whether the read is a stable snapshot or a
live tail, because those want different cursor semantics. When truncating, say so *in the
response* and name the narrowing parameter that would avoid it.

**Writes.** Annotations are hints a client may ignore, so they are not a confirmation mechanism.
Where the client supports elicitation, use it — but never form mode for credentials, which the
spec forbids outright; those go through URL mode, out of band. Where elicitation is unavailable,
use the two-step: the write tool called without a confirmation token returns a **preview of
exactly what would change** plus a short-lived token; called with a valid unexpired token, it
executes. Compose the human-readable summary into the message string yourself, because
elicitation's flat-primitives-only schema cannot render a complex pending change.

**Multi-backend.** Namespace by task domain. On partial failure return the results you have plus
an explicit per-backend status block naming which are degraded — a model that gets a bare error
cannot tell "everything is down" from "one of three is down". Expose the roster of configured
backends and their reachability as a **resource**, not a tool: it is application-controlled
context the host should supply, not something the model should have to call a tool to learn.

**Evals.** `mcp-builder` mandates all evaluation questions be read-only, which is a sound safety
default and means it cannot test the three things that matter most here. Add write-path evals
that assert on *refusal and confirmation behaviour* rather than on effects: the model attempted a
write and correctly stopped for confirmation; the model was denied and did not retry; the model
received a truncation notice and re-issued with a narrower filter.

### Reference files
- `references/error-taxonomy.md` — the three classes, worked message templates per class, and
  the scrubbing whitelist. Load when writing error paths.
- `references/pagination.md` — stable-collection envelope vs append-only stream cursors. Load
  when a tool returns a collection or a log.

## How to tell it worked

- [ ] No two tool descriptions in the server could be confused for one another
- [ ] Every tool description states what the tool does *not* return
- [ ] Every error message names its retryability class and, for fix-arguments, the offending
      parameter and a valid example
- [ ] No credential, request URL, query string, or raw exception appears in any schema,
      response, or error — verified by grepping a full transcript of an induced failure
- [ ] A log-tail tool returns bounded output with a cursor that stays correct while the log is
      being appended to
- [ ] Every destructive tool refuses to execute without a valid unexpired confirmation token
- [ ] The eval suite includes at least one write-refusal and one truncation-recovery case

## Risk review

**None.** No source attempted to induce a fetch, execution, installation, persona change, or
exfiltration. The MCP spec's prohibition on soliciting credentials through form-mode elicitation
is ordinary specification content addressed to server implementers, recorded here as data.

Environmental, not adversarial: `modelcontextprotocol.io` and `anthropic.com` are egress-blocked
in this environment. The spec was read at its canonical source repository; the engineering post
was reachable only via search extraction and its claims are excluded from the load-bearing
content above.

## Originality attestation

- [x] Nothing was downloaded, cloned, or installed
- [x] No code or prose was copied verbatim from a source
- [x] Every technique is restated in my own words
- [x] Sources are listed above as references, credited where their idea is distinctive
- [x] Any injection attempt is recorded in the Risk review

## Build steps

1. Create `.claude/skills/mcp-tool-design/SKILL.md`
2. Write frontmatter as specified
3. Write sections 1–6 as specified, body under 500 lines
4. Create `references/error-taxonomy.md` and `references/pagination.md`, each opening with a
   table of contents if over 100 lines, each exactly one level deep from SKILL.md
5. Name each reference at its point of use *and* in a closing index annotated with when to load
   it
6. Read the authored file back into context — new skills are not hot-loaded mid-session
