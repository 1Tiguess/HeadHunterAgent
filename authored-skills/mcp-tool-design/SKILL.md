---
name: mcp-tool-design
description: >-
  Designs the tool surface of an MCP server so a model picks the right tool first time —
  task-shaped tools rather than one per endpoint, descriptions that make selection
  unambiguous, errors that say what to do next, and bounded responses. Use when building
  or reviewing an MCP server, adding tools to an existing one, fronting a REST API with
  MCP, or when a model is choosing tools badly, retrying blindly on errors, or overflowing
  its context on a single response. Covers Python (FastMCP) and Node/TypeScript MCP SDK.
allowed-tools: Read, Write, Edit, Glob, Grep, Bash
---

# MCP tool design

A server is not a good server because it exposes everything. It is a good server because a
model reading only the tool list picks correctly, recovers from failure without guessing,
and never gets a response it cannot afford.

The default failure is mechanical: someone maps forty REST endpoints to forty tools, writes
each description from the endpoint's docstring, and ships. The model then picks between
`get_status` and `fetch_state` on a coin flip, retries a permission error forever, and
spends its whole context on one log tail.

## 1 — Decide the surface before writing a tool

Start from tasks a user would ask for, not from the endpoint list. For each candidate,
answer three questions in order:

1. **Does a typical request map to this one call, or to a fixed sequence of calls?**
   If a sequence, *the sequence is the tool*. Three endpoints a caller always invokes
   together are one tool, not three.
2. **Would two candidates ever be chosen between on the same evidence?**
   If yes they are one tool with an `action` parameter. Two tools a model cannot
   distinguish are worse than one tool with a mode.
3. **Is this endpoint ever a terminal answer, or only ever a lookup feeding another call?**
   A lookup that only ever supplies an argument is **a parameter, not a tool**. Resolve it
   server-side.

Prefer few task-shaped tools. Where broad coverage genuinely matters, add one escape-hatch
tool taking an operation name — not forty tools.

> Some published guidance says to favour comprehensive API coverage when uncertain. That
> advice produces the endpoint-mirrored surface described above. Prefer the three questions;
> they resolve the same uncertainty without defaulting to breadth.

## 2 — Name and describe for selection

The description is the largest single lever on whether the model picks correctly. Write at
least three or four sentences covering:

- what the tool does
- when it should fire **and when it should not**
- what each parameter does to the behaviour
- **what the tool does not return**

That last clause is the one everyone omits and the one that prevents a model calling a tool
hoping for data it was never going to get.

Name as `domain_action_resource` in snake_case, namespaced **by task domain, not by backing
service**. A user asking "is anything broken?" does not know which of your three backends
answers that.

**The test for the whole surface is mutual exclusivity.** Read any two descriptions
side by side and ask whether a model could confuse them. If yes, merge them or re-scope
them. Apply this every time you add a tool, because ambiguity is created pairwise.

For a read/write split, the separation is a *naming and description* problem before it is
an architecture problem. A read tool's description must say in words that it never mutates,
and name the write tool that does.

Use enums for closed value sets, with a description on each property. Return stable
semantic identifiers — slugs, UUIDs — never opaque internal handles.

**Portability note.** Some tool-definition features are Claude API features, not MCP
protocol features — `input_examples`, strict schema enforcement, deferred tool loading and
tool search among them. An MCP server cannot emit them over the wire. Where you need to
convey a format-sensitive input, put the example in the description prose or the schema
field description instead.

## 3 — Errors are a control surface, not a report

Failures inside a working tool ride the **result** with an error flag, never the transport.
The reason is practical: a result reaches the model, a protocol-level error generally does
not. An error the model cannot see is an error it cannot recover from.

Every error belongs to exactly one class, and the message must say which:

| Class | Means | Message must give |
|---|---|---|
| **fix-arguments** | The request was wrong | Which parameter, and what a valid value looks like |
| **retry-after-delay** | Transient; the same call will work later | A concrete duration |
| **stop-and-escalate** | Retrying will not help | Plainly that this needs a human |

A model told only "be actionable" will retry the unfixable one forever. Naming the class is
what prevents that.

Load `references/error-taxonomy.md` when writing error paths — it carries message templates
per class and the scrubbing rules below.

**Scrub before anything leaves the server.** Never echo the outbound request URL, its query
string, request headers, or raw exception text. Home-lab and internal APIs commonly
authenticate by query parameter, so an upstream failure echoed verbatim leaks the credential
into the model's transcript — a path that storing keys in environment variables does nothing
to close. **Whitelist the fields you emit; never blacklist the ones you fear.**

## 4 — Bound every response

Give each tool a token budget and enforce it server-side. Return high-signal fields only.

For collections: always honour `limit`, default to 20–50, never materialise the full result
set, and return an envelope carrying count, `has_more`, and the next cursor.

For an **append-only stream** — a log tail, an event feed — a numeric offset is wrong. The
collection grows under the reader, so offsets shift between calls. Anchor the cursor to a
byte position or a timestamp, bound by lines rather than records, and state explicitly
whether the read is a stable snapshot or a live tail. Those want different cursor semantics
and should not be the same call with different behaviour.

When you truncate, **say so in the response** and name the parameter that would narrow it.
A truncation notice that does not suggest the next action just wastes the tokens it saved.

Load `references/pagination.md` when a tool returns a collection or a log.

## 5 — Writes and secrets

Behavioural annotations such as read-only or destructive are **hints a client may ignore**.
They are metadata, not a confirmation mechanism, and a server that needs a write genuinely
confirmed cannot delegate it to them.

Where the client supports elicitation, use it — but **never form-mode elicitation for
credentials**. Passwords, API keys, tokens and payment details must go out of band. This is
a hard prohibition in the protocol, not a preference.

Where elicitation is unavailable, use the two-step:

1. The write tool called **without** a confirmation token returns a *preview of exactly what
   would change*, plus a short-lived token.
2. Called **with** a valid unexpired token, it executes.

Compose the human-readable summary into the message yourself. Elicitation's schema is
restricted to flat primitives and cannot faithfully render a complex pending change.

## 6 — Multi-backend servers

Namespace by task domain, not by backend. On partial failure return the results you *do*
have plus an explicit per-backend status block. A model that receives a bare error cannot
distinguish "everything is down" from "one of three is down", and will report the wrong
thing to the user.

Expose the roster of configured backends and their reachability as a **resource**, not a
tool. The split is about who decides: tools are model-controlled, resources are
application-controlled context the host supplies, prompts are user-controlled. Which
backends exist is context, not a decision the model should have to spend a call on.

## 7 — Transport

For a single-user local server, prefer **stdio**: no Origin validation, no loopback binding,
no DNS-rebinding defence, no token story. One caveat that bites hard — a stdio server must
**never log to stdout**, because that channel *is* the protocol.

Choose Streamable HTTP when you genuinely need remote or multi-client access, and accept the
security work that comes with it. Published guidance often names HTTP as the default stack;
for a local single-user deployment that contradicts its own criteria table.

## 8 — Ship evaluations

The server is not done when it runs. It is done when it has tests that would catch a
regression in tool *selection*.

Read-only evaluation questions are the safe default and cannot test the three things that
matter most here. Add write-path evals that assert on **refusal and confirmation behaviour**
rather than on effects:

- the model attempted a write and correctly stopped for confirmation
- the model was denied and did not retry
- the model received a truncation notice and re-issued with a narrower filter

## Reference files

Load each at the point named, not up front.

| File | Contents | Load when |
|---|---|---|
| `references/error-taxonomy.md` | The three classes, message templates per class, the scrubbing whitelist | Writing any error path |
| `references/pagination.md` | Stable-collection envelope vs append-only stream cursors | A tool returns a collection or a log |

## Done means

- No two tool descriptions could be confused for one another
- Every description states what the tool does *not* return
- Every error names its class, and fix-arguments errors name the parameter and a valid example
- No credential, request URL, query string or raw exception appears in any schema, response
  or error — check by grepping a transcript of an induced failure
- A log-tail tool stays correct while the log is being appended to
- Every destructive tool refuses to execute without a valid unexpired confirmation token
- The eval suite includes a write-refusal case and a truncation-recovery case
