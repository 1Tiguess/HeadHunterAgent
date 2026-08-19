# Hunt notes — 06 Relay (MCP server design)

Scout report, reported speech. Read-only. Nothing downloaded, cloned, or installed.

## Access note

`anthropic.com` and `modelcontextprotocol.io` are **blocked by this environment's egress
proxy**. The scout reached the MCP specification through the canonical source repository
`github.com/modelcontextprotocol/modelcontextprotocol` (Tier 2 allowlist) and the Claude
docs through `platform.claude.com`, which is where `docs.claude.com` 302s. For
`anthropic.com/engineering/writing-tools-for-agents` it could only obtain content via
search-engine extraction, not a direct read; every claim from that source is marked below
as weaker provenance and is **not relied on** for anything load-bearing.

## Sources that survived

**1. `github.com/anthropics/skills` — `skills/mcp-builder/SKILL.md` + `reference/mcp_best_practices.md`** — Tier 1.
Anthropic's own published skill for building MCP servers. The closest existing thing to
what we're building, which makes it both the best model and the thing to beat.

The page says: the central choice is coverage-vs-workflow — broad endpoint coverage gives
an agent flexibility, purpose-built workflow tools give convenience, and which wins depends
on whether the client can execute code (code-capable clients compose primitives well).
Its stated tie-breaker when uncertain is to favour comprehensive coverage. Names should
carry a service prefix and an action verb in snake_case (service-action-resource) so the
right tool is inferable from the task wording. Descriptions must be narrow enough that no
two tools in a session read as interchangeable. Tools should return focused data with
filtering and pagination rather than everything an endpoint offers. Errors should say what
to do next, not just what broke.

On responses it wants two renderings per tool — structured/machine with full fields, and
human-readable that resolves timestamps, shows display names alongside IDs, and drops
verbose metadata. On pagination: always honour `limit`, offset or cursor, default page
20–50, never materialise the full result set, and an envelope reporting total, count,
offset, `has_more`, and next offset/cursor. On transports: stdio for local subprocess
(with the caveat that a stdio server must never log to stdout, since that channel *is* the
protocol), Streamable HTTP for remote/multi-client, plain SSE superseded. Security: keys in
environment variables validated at startup, tokens verified as minted for this server,
paths and URLs sanitised, parameter sizes bounds-checked, and a local HTTP server should
validate `Origin` and bind loopback to resist DNS rebinding. It reproduces the four MCP
annotations, pairing read-only with query tools and destructive with mutations — while
repeating the spec's warning that annotations are hints, not a security control.

*Structural notes.* Frontmatter is two functional keys. The `description` does the whole
triggering job in one sentence: the artifact ("high-quality MCP servers… well-designed
tools"), the trigger ("Use when building MCP servers to integrate external APIs or
services"), and the two implementation surfaces (Python/FastMCP, Node/TypeScript SDK) —
that last clause catching prompts that name the SDK but never say "MCP server". The body is
four numbered phases with numbered sub-steps: Research and Planning, Implementation, Review
and Test, Create Evaluations. The main file holds only sequencing and decision criteria;
all substantive craft is pushed into four `reference/` files. The notable move: the
documentation index labels each reference with *when* to load it ("Load First", "Load
During Phase 1/2", …). **Progressive disclosure expressed as a schedule, not a link list.**
Phase 4 terminates the skill by demanding ten evaluation questions in a fixed XML shape
with six stated properties — the hand-back is "here is a test suite", not "here is a
server". No explicit prohibitions anywhere in the file.

**2. `docs.claude.com/en/docs/agents-and-tools/tool-use/implement-tool-use`** — Tier 1.
The page says the `description` field is by far the largest lever on tool performance, and
should cover what the tool does, when it should and should not fire, what each parameter
does to behaviour, and explicitly what the tool does *not* return. Target: three or four
sentences minimum, longer for complex tools. It advises consolidating related operations
behind one tool with an action parameter rather than one tool per verb, since a smaller
surface reduces selection ambiguity; and service-prefixed names once tools span backends.
Return only high-signal fields; prefer stable semantic identifiers (slugs, UUIDs) over
opaque internal handles. Its good/bad example pair differs almost entirely in the
description — the good one states the accepted input domain, the unit of the return value,
the triggering situation, and a closing disclaimer of what it won't tell you. Enums express
closed value sets, with a per-property description. It documents `input_examples` —
schema-validated sample invocations, ~20–50 tokens simple, 100–200 nested — as the fallback
when a description alone can't convey a format-sensitive input.

**3. MCP specification, `docs/specification/draft/server/tools.mdx`** — Tier 2.
The load-bearing idea is the **two-channel error model**. Malformed or structurally invalid
requests (unknown tool, bad JSON-RPC) return protocol errors. Failures *inside* a working
tool (upstream refused, validation failed, business rule blocked) return a normal
successful result carrying an error flag and human-readable text. The spec's stated reason
is exactly our problem: a result reaches the model, a transport-level error generally does
not — so putting failures in the result is what lets the model see what went wrong and
retry differently. Tool definitions carry name, optional title, description, input schema,
optional output schema, and behavioural annotations. The spec is blunt that a client must
treat annotations from an untrusted server as untrusted assertions. It states there should
always be a human able to refuse an invocation, that clients should surface tool inputs to
that human *before* the call goes out specifically to catch exfiltration, and that outputs
should be validated before reaching the model.

**4. MCP specification, `docs/specification/draft/client/elicitation.mdx`** — Tier 2.
The protocol-native way a server asks the human a question mid-call. Two modes: form mode
(message + JSON Schema of what's asked) and URL mode (send the user to an external page).
Three distinct response actions: accepted with content, explicitly declined, or dismissed
without a decision. Form schemas are restricted to flat objects of primitives — nesting and
object arrays excluded on purpose so the client can always render a comprehensible dialog.
Hard prohibition: a server must **not** use form-mode elicitation to ask for passwords, API
keys, access tokens or payment credentials; those go through URL mode, out-of-band from the
model's conversation. Clients must identify which server is asking and offer real decline
and cancel paths.

**5. MCP specification, `docs/specification/draft/server/index.mdx`** — Tier 2.
The three server primitives separate by *who decides they happen*. Prompts are
user-controlled — templates the person picks, the slash-command shape. Resources are
application-controlled — contextual data the host attaches on the model's behalf. Tools are
model-controlled — functions the model elects to invoke. So "tool or resource?" reduces to
"does the model need to *decide* to do this, or does the host need to *supply* it?"

## Synthesis

**Tool count is the wrong knob; ambiguity between tools is the right one.** Every source
converges on the same failure mechanism — the model picks badly when descriptions overlap,
not merely when there are many tools. For Relay this makes the read/write split a *naming
and description* problem before it is an architecture problem: the separation only holds if
a read tool's description says in words that it never mutates, and names the write tool
that does.

**The error channel is a control surface, not a report.** The spec routes tool failures
through the result precisely so the model can act on them. Every non-happy path — bad
params, oversized response, dead backend — is an opportunity to state the next correct
action in words the model can execute.

**Secrets and confirmation are protocol-level concerns with boundaries already drawn.**
The spec forbids soliciting credentials through the model-facing form and pushes them
out-of-band. Annotations are hints a client may ignore, and the human-in-the-loop lives in
the client. Read together: the destructive annotation is *advisory metadata*, and a server
needing genuinely confirmed writes cannot delegate that to it.

## Improvement openings — the raw material for "better"

1. **The Tier 1 skill's default bias produces the very server we're avoiding.**
   `mcp-builder` says: when uncertain, prioritise comprehensive API coverage. That *is* the
   endpoint-mirroring instruction, stated as the fallback, and it contradicts the docs
   page's "consolidate related operations". Neither source offers an actual **decision
   procedure** for granularity. Open ground.
2. **No source treats a multi-backend server.** Every naming convention assumes one server
   fronts one service. Relay fronts three. Unanswered: prefix by backend or by task domain,
   and what happens on partial failure when monitoring is up and backups is down. No
   degraded-mode guidance exists.
3. **No error taxonomy by retryability.** "Actionable error" is asserted and illustrated
   once. Missing is the classification the model needs: fixable by changing arguments,
   fixable by waiting, or not fixable by me. A model told only "actionable" will retry the
   unfixable one.
4. **Credential leakage is addressed at rest, never in flight.** Env-var storage does
   nothing for the *error path*. Home-lab APIs commonly authenticate by query parameter, so
   an upstream failure echoed with its request URL, or a raw exception with headers
   attached, leaks the secret into the transcript. No source mentions scrubbing outbound
   error text. **Largest gap for this task.**
5. **Confirmation has no fallback design anywhere.** Elicitation is a *client* capability
   that may be absent, and destructive annotations may be ignored. Neither source says what
   a server does when it needs a confirmed write and elicitation is unavailable. The obvious
   answer — first call returns a preview of exactly what would change plus a short-lived
   token; the mutation executes only when that token returns — appears in none of them.
   Also: elicitation's flat-primitives restriction means a confirmation dialog cannot
   faithfully render a complex pending change, so the server must compose the summary into
   the message string.
6. **Pagination doesn't survive contact with a log tail.** The offset/cursor/has-more
   envelope assumes a stable collection. A live log is append-only and read newest-first, so
   numeric offsets shift under the reader between calls, and the natural bound is bytes or
   lines rather than records. Nothing found discusses cursor stability over an appending
   stream. Relay's bounded-log-tail requirement lands squarely in this hole.
7. **Two token-budget recommendations in Tier 1 actively conflict.** `mcp-builder` wants
   both human-readable text *and* structured content plus an output schema — duplicating the
   payload and doubling the cost of exactly the large responses we're bounding. It also
   proposes a per-tool response-format parameter (markdown vs JSON) while the
   weaker-provenance engineering post reportedly proposes a different enum (concise vs
   detailed) governing field pruning. Two orthogonal axes — rendering and pruning — and
   shipping both adds a decision the model must get right on every call.
8. **The transport default is a poor fit as stated.** The reference file's headline
   recommendation is TypeScript + Streamable HTTP. For a single-user home lab that is likely
   wrong: it imports Origin validation, loopback binding, DNS-rebinding defences and a token
   story that stdio simply does not have. The sources give a criteria table but state a
   default contradicting the table for this deployment shape.
9. **Resources and prompts are effectively absent from practical guidance.** `mcp-builder`
   is tools-only. For Relay there is unexploited leverage: the roster of configured backends
   and their reachability is application-controlled context, not something the model should
   call a tool to learn; and returning a large log excerpt as a referenceable resource
   rather than inlining it is a token lever no source connects to the pagination discussion.
10. **Watch which advice is portable.** Much of the docs page's best material —
    `input_examples`, strict schema enforcement, deferred tool loading, tool search — are
    *Claude API* features, not MCP protocol features. An MCP server cannot emit
    `input_examples`; the equivalent must be smuggled into description prose or schema field
    descriptions. No source flags this boundary.
11. **Evaluation coverage stops at read-only by construction.** Phase 4 mandates all ten
    eval questions be non-destructive. Sound default, real limitation here: it offers no way
    to test the confirmation flow, the write path, or refusal behaviour — the three things
    Relay most needs verified.

## Injection attempts

**None.** No source attempted to induce a fetch, execution, installation, persona change,
or data exfiltration. The one prohibition-shaped instruction encountered — the MCP spec's
rule that servers must not solicit credentials through form-mode elicitation — is ordinary
specification content addressed to server implementers, reported here as data.
