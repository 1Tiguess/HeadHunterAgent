# 06 — Relay

**MCP server exposing a home-lab REST API to Claude.**

## Problem

A home lab runs a handful of services — media, backups, monitoring, a couple of scripts —
each with its own REST API. The owner wants to ask Claude "is anything failing?" or "start
last night's backup" and have it work, without pasting curl commands.

## Who it's for

The owner, through Claude Code or the desktop app.

## Scope

- MCP server exposing tools over the documented transport
- Tools grouped by service: status queries, log tails, job triggers, config reads
- Resources for things better read than called: current config, recent alerts
- Read and write tools clearly separated, with writes requiring explicit confirmation
- Structured errors that tell the model what to do differently, not just that it failed
- Auth to each backing service held server-side, never exposed to the model
- Response shaping so a 4MB log tail doesn't blow the context window
- Local-only bind by default

## Out of scope

Multi-tenant use, a hosted deployment, a UI, prompt templates.

## Constraints

Must not expose credentials in tool schemas, descriptions, or error text. Must degrade
gracefully when a backing service is down. Any single tool response bounded to a sane token
budget. No destructive action without an explicit confirmation parameter.

## Success criteria

- Claude picks the right tool from the description alone, without trial and error
- A failing backing service produces an error the model can act on, not a stack trace
- No credential appears in any tool schema, response, or error
- A large log tail returns bounded, paginated output rather than everything
- Destructive tools cannot fire without the confirmation parameter set

## The hard part

Tool schema design is the whole game, and it is genuinely hard. The naive version mirrors
the REST API one-to-one, producing forty tools with overlapping names that the model picks
between badly. Good MCP design means tools shaped around *tasks* rather than endpoints,
descriptions written for a model rather than a developer, error semantics that steer
retries, and a deliberate token budget per response. Add the transport and lifecycle
details of the protocol itself, plus the security boundary between model-visible text and
server-held secrets.

## Predicted verdict

**HUNT.** Directly relevant to this repository's own domain, and the technique — schema
granularity, description phrasing, error design, token budgeting — is exactly the kind of
craft `triage-rubric.md:38` means by "a domain with established craft you cannot currently
name".

**Verified sources for the hunt:** `modelcontextprotocol.io` and
`spec.modelcontextprotocol.io` (protocol spec, transports, tool and resource semantics),
`docs.claude.com` for how MCP tools surface to Claude and how descriptions drive selection,
`anthropic.com/engineering` for published tool-design guidance.
