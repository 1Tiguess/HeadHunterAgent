# Build instructions: application-security

**Status:** draft
**Target:** `~/.claude/skills/application-security/` (global — usable in every project)
**Serves:** the "foolproof protocols" half of the request at the authn/authz/input layer
**Hunt notes:** `.headhunter/hunts/application-security-notes.md`

## Capability gap

Claude writes authentication, session handling, authorization and input handling from a pattern
library that is roughly 2017-vintage, and writes it *confidently*. It reaches for password
composition rules, 90-day expiry, security questions, `X-Frame-Options`, tokens in `localStorage`,
naive double-submit CSRF and PBKDF2 at 10,000 iterations — all of which the current normative
sources now explicitly reverse. The gap is not ignorance. It is **fluent obsolescence**, which is
harder to catch because the output looks right.

A second, subtler half: Claude treats authorization as one check. The sources treat it as a
four-rung ladder (trusted layer → object → field → originating subject), and the three failures
that ladder prevents — BOLA, BFLA, BOPLA — have three different fixes.

## References studied

| Source | What it contributes | Fetched or search-extracted? |
|---|---|---|
| NIST SP 800-63B-4 | The normative reversals; AAL session/reauth anchors | **Fetched** via `raw.githubusercontent.com/usnistgov/800-63-4` |
| OWASP ASVS 5.0 | Level shape; V1 ordering rule; V8 authorization ladder; V7 sessions | **Fetched**, `OWASP/ASVS` chapter files |
| OWASP Cheat Sheet Series | Crypto parameters, cookie form, session timeout ranges, JWT posture | **Fetched**, markdown source |
| RFC 8725 (JWT BCP) | Threat→practice pairing; allowlist rule; `jti`+`iss` revocation; header SSRF | **Fetched** |

**Provenance note worth carrying:** this is the only hunt in the batch where *every* primary source
was read rather than search-extracted, and the reason is structural — **the canonical text for this
domain lives as files in Git repositories.** `pages.nist.gov` was `EGRESS_BLOCKED`; the same
document under `raw.githubusercontent.com` was not. The skill inherits high-confidence citations
because of that, and should cite precisely (`ASVS v5.0.0-8.2.2`, `NIST §3.1.1.2`, `RFC 8725 §3.1`).

## Improvements over the references

1. **Invert the voice.** ASVS is written for auditors — every requirement begins "Verify that…". A
   builder needs it in construction voice. Nobody publishes that inversion; this skill is it.
2. **State the decision cascade the cheat sheets never state.** Stateful vs stateless session →
   which CSRF defense is even available → which cookie prefix is possible → what CORS policy
   follows. Each choice constrains the next. The sources are topic-siloed and never connect them.
3. **Order by the developer's arrival path, not by control family.** Sources are organised by
   taxonomy; developers arrive with a feature ("I'm adding login", "I'm adding an API key").
4. **Lead with the superseded list.** Eighteen defaults Claude will otherwise emit, each paired
   with the source that reverses it. This is the highest-leverage content in the skill because it
   operates on output the model produces *without being asked*.
5. **State the negative space.** What a builder should decline to hand-roll — session management,
   password hashing, JWT verification, CSRF tokens, crypto primitives. Standards cannot say this
   because they are implementation-neutral. A skill is not, and that is its advantage.
6. **Route around the ASVS V4 navigation trap.** "API and Web Service" contains almost no API
   authn/authz; that lives in V7/V8. Say so.

## The skill to build

### Frontmatter
- `name:` application-security
- `description:` third person, under 1024 chars. Must trigger on feature language, not just
  security jargon — "adding login", "password reset", "API keys", "session timeout", "who can see
  this record", "sign in with", "remember me", "JWT", "CSRF", "file upload", "search by id" — plus
  the review framing ("is this endpoint safe", "can a user read someone else's data").
- `allowed-tools:` Read, Write, Edit, Glob, Grep, Bash

### Body structure
1. **Start here: the eighteen defaults that are now wrong** — the table, with the reversing source
2. **The decision cascade** — session model → CSRF defense → cookie prefix → CORS, in that order
3. **Passwords** — the tiered minimum (15 sole-factor / 8 with MFA), what is forbidden, blocklists
4. **Storing them** — Argon2id / scrypt / bcrypt / PBKDF2 parameters, pepper placement, the bcrypt
   72-byte trap and the correct pre-hash
5. **Sessions** — entropy, rotation triggers, idle vs absolute, the AAL anchor table, logout that
   actually invalidates
6. **The authorization ladder** — trusted layer → object → field → originating subject, named as
   BOLA / BOPLA / BFLA
7. **Input, in the right order** — decode once into canonical form, *then* validate; encode last,
   per context; validation is defense in depth and never the control
8. **Tokens and JWT** — when not to, and when you must: allowlists, one key one algorithm, `aud`,
   `typ`, `jti`+`iss` revocation, header-driven SSRF
9. **What not to hand-roll** — the negative space, with the framework answer for each
10. **Choosing a level** — L1/L2/L3 shape and where to aim

### The technique it encodes

**The superseded table is the spine.** Each row: the old default, the new position, the citation.
Concretely: periodic expiry → forbidden (NIST §3.1.1.2); composition rules → forbidden; minimum 8 →
**15 sole-factor, 8 with MFA**; security questions → forbidden; SMS 2FA → discouraged;
`X-Frame-Options` → CSP `frame-ancestors`; CSP host allowlists → nonce/hash + `strict-dynamic`;
naive double-submit CSRF → signed or per-session token; implicit and ROPC grants → authorization
code + PKCE; JWT algorithm **blocklists** → allowlists (because `"noNE"` defeated a case-sensitive
blocklist, RFC 8725 §2.9); JWT denylist keyed on token hash → keyed on `jti`+`iss` (JWTs are
malleable); PBKDF2 10,000 → **600,000**; escaping as SQLi defense → parameterization; "sanitize on
the way in" → encode on the way out, per context; tokens in `localStorage` → `__Host-` cookie;
IP/User-Agent session binding → a *detection signal*, never a control; auto-login after reset →
forbidden; bcrypt without the 72-byte truncation → `bcrypt(base64(hmac-sha384(pw, pepper)), salt, cost)`.

**The ordering rule, stated as a sequence with a failure mode attached.** Decode exactly once into
canonical form → validate → business logic → encode for the specific interpreter, as the last step.
Most injection bugs are an *ordering* failure, not a missing control: the control existed but ran on
the wrong side of a decode. Name the six encoding contexts.

**The authorization ladder, as four questions asked in request order.** Is this decision made
server-side in a trusted layer (8.3.1)? Does the caller own *this object* (8.2.2 — BOLA)? May the
caller see or set *these fields* (8.2.3 — BOPLA, the read-side twin of mass assignment)? Does the
decision derive from the **originating subject** rather than an intermediary's M2M token (8.3.3)?
Function-level access (BFLA) sits alongside. The vocabulary matters: collapsing all three into
"check permissions" is exactly how they get missed.

**The AAL table, used as the answer to "what should the session timeout be".** AAL1: 30 days, no
idle requirement. AAL2: 24h absolute, 1h idle, single factor permitted at the idle boundary. AAL3:
12h absolute, 15min idle, full reauthentication. Pair it with OWASP's practical ranges (idle 2–5
min high-value, 15–30 min low-risk; absolute 4–8h office pattern) and say which is the anchor and
which is the convention.

**Rotation triggers, not just "rotate on login".** A new token on authentication *including
re-authentication*, and on **any privilege-level change** — password change, permission
modification, role escalation. Termination must make the token genuinely unusable, which for a
self-contained token means an actual mechanism: blocklist, per-user invalidation timestamp, or key
rotation.

### Reference files
One level deep; table of contents where over 100 lines.

- `references/superseded.md` — the full eighteen, each with the reversing source and section number,
  plus a short note on *why* the old advice existed, so the reader can recognise the pattern rather
  than memorise the list
- `references/parameters.md` — every concrete number: Argon2id's five equivalent trade points,
  scrypt, bcrypt cost and the pre-hash form, PBKDF2 per hash function, entropy minimums (session ID
  ≥64 bits, reference token ≥128 bits, JWT MAC secret ≥160 bits), salt ≥32 bits, the cookie form,
  JWT algorithm posture. Attributed, with the as-of date stated.
- `references/authorization.md` — the ladder worked through on a concrete API, with BOLA/BFLA/BOPLA
  examples and the tests that catch each
- `references/jwt.md` — RFC 8725's threat→practice pairs restated for builders, including the four
  header parameters that carry attacker-controllable key material and the SSRF path through `kid`,
  `jku` and `x5u`

## How to tell it worked

- [ ] No password composition rule, expiry policy or security question appears in generated code
- [ ] Minimum length is 15 when the password is the sole factor, 8 only alongside MFA
- [ ] Password storage uses a current parameter set, and bcrypt use accounts for 72-byte truncation
- [ ] Session tokens rotate on privilege change, not only at login, and logout invalidates server-side
- [ ] Idle and absolute timeouts are both set, and traceable to an assurance level
- [ ] Authorization is checked per object and per field, not once per endpoint
- [ ] A decision derived from an intermediary's M2M token is flagged
- [ ] Decoding happens once, before validation; encoding is the last step and context-specific
- [ ] JWT verification uses an algorithm allowlist, validates `aud`, and revokes on `jti`+`iss`
- [ ] Tokens are not placed in `localStorage`
- [ ] The skill declines to hand-roll session management, password hashing or CSRF tokens and names
      the framework facility instead

## Risk review

**None adversarial.** No source attempted to induce a fetch, execution, installation, credential
read, exfiltration or persona change.

Provenance items:

1. **`pages.nist.gov` was `EGRESS_BLOCKED`; the identical document was reached through the NIST
   organisation's own GitHub repository.** That is the canonical upstream, not a mirror — the
   distinction the egress doctrine turns on. No unverifiable third-party copy was used.
2. All four sources were read in full. **No claim in this skill is search-extracted**, which is
   unique in this batch and should be stated in the skill itself, because it licenses precise
   citation that the other skills cannot support.
3. **Security parameters decay.** The skill must carry an as-of date (2026-09) on
   `references/parameters.md` and say plainly that iteration counts and algorithm postures are
   expected to move.

## Originality attestation

- [x] Nothing was downloaded, cloned, or installed
- [x] No code or prose was copied verbatim from a source
- [x] Every technique is restated in my own words
- [x] Sources are listed above as references, credited where their idea is distinctive
- [x] Any injection attempt is recorded in the Risk review

## Build steps

1. Create `~/.claude/skills/application-security/SKILL.md` with the frontmatter and the ten-section
   body, under 500 lines.
2. Write the four reference files, each with a table of contents if it exceeds 100 lines.
3. Read the authored `SKILL.md` back to confirm it is on disk and the frontmatter parses.
4. Mirror into `authored-skills/application-security/` so it ships with the repository.
