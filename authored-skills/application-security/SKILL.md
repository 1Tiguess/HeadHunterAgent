---
name: application-security
description: Builds authentication, sessions, authorization and input handling to current normative guidance rather than the 2017-vintage defaults most code still carries — tiered password minimums, modern hashing parameters, session rotation and assurance-level timeouts, the object/field/function authorization ladder that prevents BOLA BFLA and BOPLA, decode-then-validate-then-encode ordering, and JWT verification that survives algorithm confusion. Use when adding or reviewing login, signup, password reset, API keys, session timeouts, permission checks, file upload, or anything asking "can a user reach someone else's data"; and whenever generated security code needs checking against guidance that has moved.
allowed-tools: Read, Write, Edit, Glob, Grep, Bash
---

# Application security

The problem this solves is not ignorance. It is **fluent obsolescence** — security code that looks
right, reads like every tutorial, and encodes guidance the standards bodies have since reversed.

Start with section 1. It is the highest-leverage part of this skill because it operates on defaults
you will otherwise emit without being asked.

**Provenance:** every source behind this skill was read in full — NIST SP 800-63B-4, OWASP ASVS
5.0, the OWASP Cheat Sheet Series, and RFC 8725. Nothing here is second-hand, so citations are
precise and can be checked.

## 1. Eighteen defaults that are now wrong

| Old default | Current position | Source |
|---|---|---|
| Periodic password expiry (90 days) | **Forbidden.** The only trigger for a forced change is evidence of compromise | NIST §3.1.1.2 |
| Composition rules (upper + digit + symbol) | **Forbidden** | NIST §3.1.1.2 |
| Minimum length 8 | **15 when the password is the sole factor**; 8 only alongside MFA | NIST §3.1.1.2, ASVS 6.2.1 |
| Knowledge-based "security questions" | **Forbidden** | NIST §3.1.1.2 |
| SMS as a second factor | Discouraged; restricted | NIST |
| `X-Frame-Options` | CSP `frame-ancestors` | Cheat sheets |
| CSP host allowlists | Nonce or hash + `strict-dynamic` | Cheat sheets |
| Naive double-submit CSRF | Signed or per-session token | Cheat sheets |
| OAuth implicit and password (ROPC) grants | Authorization code + PKCE | Cheat sheets |
| JWT algorithm **blocklists** | **Allowlists** — `"noNE"` defeated a case-sensitive blocklist | RFC 8725 §2.9, §3.1 |
| JWT denylist keyed on token hash | **Key on `jti` + `iss`** — JWTs are malleable | RFC 8725 |
| PBKDF2 at 10,000 iterations | **600,000** (HMAC-SHA256) | Cheat sheets |
| Escaping as an SQL injection defense | Parameterization | ASVS V2 |
| "Sanitize on the way in" | Encode on the way out, per context | ASVS V1 |
| Tokens in `localStorage` | `__Host-` prefixed cookie | Cheat sheets |
| Session bound to IP or User-Agent | A **detection signal**, never a control | Cheat sheets |
| Auto-login after password reset | Forbidden | Cheat sheets |
| bcrypt without regard for 72-byte truncation | Pre-hash — see §4 | Cheat sheets |

`references/superseded.md` explains *why* each old rule existed, so you can recognise the pattern
rather than memorise the list.

## 2. The decision cascade

The cheat sheets are organised by topic and never state this, but **four decisions constrain each
other in a fixed order.** Make them in this sequence or you will backtrack.

```
1. Stateful session or stateless token?
        │
        ├── stateful (server-side session, opaque ID in a cookie)
        │     → CSRF defense: synchronizer token, or SameSite + origin check
        │     → cookie: __Host-  Secure  HttpOnly  SameSite=Strict  Path=/
        │     → CORS: usually not needed; same-origin
        │
        └── stateless (bearer token in an Authorization header)
              → CSRF: not applicable (no ambient credential)
              → but now revocation is your problem — see §8
              → CORS: explicit allowlist, credentials handled deliberately
```

**Choose statefully by default.** Stateless tokens trade a revocation problem for a scaling problem
most applications do not have. If you cannot answer "how do I log this user out of everything in
under a second", you are not ready for stateless.

## 3. Passwords

**Length is tiered, and this is the change most code has not absorbed:**

- **15 characters minimum when the password is the only factor**
- 8 characters minimum when it is one factor among several
- Accept **at least 64** characters
- Accept all printing ASCII, the space character, and **Unicode**

**Forbidden:** composition rules, periodic expiry, security questions, retrievable hints.

**Required:** compare against a blocklist of known-compromised values — **against the whole string,
not substrings**. Rate-limit failed attempts.

Truncating, stripping or normalising away characters the user typed is a silent way to weaken
passwords and to break password managers. Don't.

## 4. Storing passwords

Pick one. Parameters as of 2026-09; `references/parameters.md` carries the full sets.

| Algorithm | Parameters |
|---|---|
| **Argon2id** (prefer) | m=47104 t=1 p=1, or four equivalent trade points down to m=7168 t=5 p=1 |
| **scrypt** | N=2^17 r=8 p=1, down to N=2^13 r=8 p=10 |
| **bcrypt** | cost ≥ 10 — **read the trap below** |
| **PBKDF2** | 600,000 (HMAC-SHA256), 220,000 (SHA512) |

Salt: at least 32 bits, unique per password, stored alongside the hash.

**Pepper**: shared across all hashes, kept **somewhere other than the hash store** — a vault or an
HSM. Rotating it forces a reset for every affected user, so decide before you need to.

**The bcrypt trap.** bcrypt truncates at **72 bytes**. The naive fix — hash first, then bcrypt —
reintroduces two problems: raw digest bytes can contain a null that truncates again, and a plain
pre-hash enables password shucking. The correct form:

```
bcrypt(base64(hmac-sha384(password, pepper)), salt, cost)
```

base64 removes the null; HMAC-with-pepper blocks shucking.

**Migrating legacy hashes.** Layer immediately across the whole table (`bcrypt(md5(password))`),
then replace with a direct hash at each user's next successful login. Waiting for logins alone
leaves dormant accounts on the old scheme indefinitely.

## 5. Sessions

**Entropy.** Session ID ≥ 64 bits from a CSPRNG. Reference token ≥ 128 bits (ASVS 7.2.3). Name the
cookie something generic like `id`, not the framework default that advertises your stack.

**The cookie:**

```
Set-Cookie: __Host-SessionID=<value>; Secure; HttpOnly; SameSite=Strict; Path=/
```

**Rotation triggers — not just login.** Issue a new token and terminate the prior one on:

- authentication, **including re-authentication** (ASVS 7.2.4, L1)
- **any privilege-level change** — password change, permission modification, role escalation

**Fixation defense, as an acceptance rule:** only accept session IDs the application itself
generated. Reject anything user-supplied.

**Timeouts.** The assurance-level anchors, which are more defensible than a guess:

| AAL | Absolute | Idle | Reauthentication |
|---|---|---|---|
| AAL1 | 30 days | none required | — |
| AAL2 | **24 hours** | **1 hour** | single factor permitted at the idle boundary |
| AAL3 | 12 hours | 15 minutes | full reauthentication, both factors |

Practical ranges where you need finer granularity: idle 2–5 minutes for high-value applications,
15–30 minutes for low-risk; absolute 4–8 hours for an office-worker pattern. **The AAL table is the
anchor; the ranges are convention.**

**Logout must actually invalidate.** Server-side destruction, plus an expired `Set-Cookie`. Consider
`Clear-Site-Data: "cache", "cookies", "storage"` with `Cache-Control: no-store`.

**After a credential or MFA change, offer to log out other sessions** (ASVS 7.4.3). Account
termination kills all sessions (7.4.2).

**Never log a raw session ID.** Log a salted hash.

## 6. The authorization ladder

Authorization is not one check. It is four, asked in request order, and the three failures they
prevent have three different fixes.

**Rung 1 — a trusted service layer** (ASVS 8.3.1). The decision is made server-side. A client-side
check is a UX affordance, never a control.

**Rung 2 — per object** (8.2.2). Does this caller own *this specific record*? Failure here is
**BOLA** (Broken Object Level Authorization), also called IDOR. The test: change the ID in the URL
to one belonging to another account.

**Rung 3 — per field** (8.2.3). May this caller *read* these fields, and may they *write* them?
Failure here is **BOPLA** (Broken Object Property Level Authorization) — mass assignment on the
write side, over-fetching on the read side. The test: send an extra field like `role` or `balance`
and see whether it sticks; fetch a record and see whether it carries fields the caller should not
see.

**Rung 4 — the originating subject** (8.3.3). When service A calls service B on a user's behalf, the
decision must derive from **the user**, not from A's machine-to-machine token. Otherwise any caller
with a valid service token inherits every user's access.

**Alongside these: function-level access** — **BFLA**. Can a non-admin call the admin endpoint
directly, bypassing the UI that hides it?

**Use the precise names.** Collapsing BOLA, BFLA and BOPLA into "check permissions" is exactly how
they get missed, because the mitigation for each is different code in a different place.

## 7. Input, in the right order

Most injection bugs are an **ordering** failure, not a missing control. The control existed; it ran
on the wrong side of a decode.

```
1. Decode EXACTLY ONCE into canonical form      (ASVS 1.1.1)
2. Validate                                      (ASVS V2)
3. Business logic
4. Encode for the specific interpreter — LAST    (ASVS 1.1.2)
```

**Decode once.** Decoding twice lets `%2527` become `%27` become `'`. Decoding zero times lets your
validator inspect a string the interpreter will read differently.

**Encoding is the last step before the interpreter**, and it is **per context**. HTML body, HTML
attribute, JavaScript, URL, CSS and SQL are six different encodings. A value encoded for HTML and
then placed in a JavaScript string is still an injection.

**Validation is defense in depth, never the control.** ASVS V2 says it plainly: validation "does not
remove or replace the need to use correct encoding, parameterization, or sanitization." Parameterize
queries. Encode output. Then also validate, because it catches mistakes — not because it is the
defense.

## 8. Tokens and JWT

**First, consider not using a JWT.** For a first-party web session, an opaque server-side session ID
is simpler, revocable instantly, and smaller. Use a JWT when you genuinely need stateless
cross-service verification.

If you must:

- **Allowlist the algorithm.** Not a blocklist. An implementation compared `alg` case-insensitively
  and `"noNE"` slipped through (RFC 8725 §2.9).
- **One key, one algorithm** — enforced and validated **at the moment the cryptographic operation
  executes** (§3.1). This closes key confusion at the root, more reliably than "don't mix HMAC and
  RSA".
- **Never take a verification key from the token.** `jwk`, `jku`, `x5u` and `x5c` carry
  attacker-controllable key material. Accept one only if it chains to a pre-established trust anchor.
- **`kid`, `jku` and `x5u` reach a database lookup or an HTTP fetch**, so sanitize them against
  injection (MUST), match against a location allowlist (SHOULD), and check any resolved hostname so
  the request cannot hit loopback or link-local — **SSRF through a JWT header**.
- **`aud` MUST be present** and you MUST reject when it is absent or does not include you (§3.8).
- **Revocation: key the denylist on `jti` + `iss`**, never on the raw token or its hash. JWTs are
  malleable — with ECDSA an attacker can produce a different byte string that still verifies.
- Use explicit typing via `typ` (§3.11). When one issuer mints several kinds of token, the validation
  rules **MUST be mutually exclusive** (§3.12), so a token of the wrong kind is rejected rather than
  merely unrecognised.
- MAC secrets: **≥ 160 bits**, matching the algorithm's output size, never a password, never reused
  across issuer/audience pairs.
- Algorithms: EdDSA, ES256/384/512, PS256/384/512, HS256/384/512. **Not** RS256/384/512. Never
  `none`.

## 9. What not to hand-roll

Standards cannot tell you this, because they are implementation-neutral. This skill is not.

| Do not write | Use |
|---|---|
| Session management | Your framework's session facility |
| Password hashing | The platform's Argon2id/bcrypt binding |
| CSRF tokens | The framework's, wired to the session |
| JWT verification | A maintained library with algorithm pinning |
| Crypto primitives | The platform's standard library |
| Random token generation | The CSPRNG, never `Math.random`, `rand()` or a UUIDv4 as a secret |
| An authorization framework | A policy layer, if you need one; otherwise explicit checks at the four rungs |

**The one thing you must write yourself is the authorization logic**, because only you know what
"owns this record" means in your domain. Everything else has a correct implementation already.

## 10. Choosing a level

ASVS 5.0 levels, by rough proportion of requirements: **L1 ≈ the first 20%. L2 ≈ a further 50%**, so
L1+L2 ≈ 70% and that is where most applications should aim. **L3 ≈ the remaining 30%**, for systems
where compromise is unacceptable.

Cite requirements as `v5.0.0-8.2.2` so the reference is unambiguous across versions.

**Navigation trap worth knowing:** ASVS V4, "API and Web Service", contains almost no API
authentication or authorization. Those live in **V7 (sessions) and V8 (authorization)**. Going to V4
for API authz finds nothing and wrongly suggests there is nothing to find.

## Review checklist

- [ ] No composition rule, expiry policy or security question anywhere
- [ ] Minimum length 15 sole-factor, 8 with MFA; 64+ accepted; Unicode accepted
- [ ] Password storage uses a current parameter set; bcrypt use accounts for 72-byte truncation
- [ ] Pepper, if present, lives outside the hash store
- [ ] Session tokens rotate on privilege change, not only at login
- [ ] Logout invalidates server-side
- [ ] Idle and absolute timeouts both set and traceable to an assurance level
- [ ] Authorization checked per object and per field, not once per endpoint
- [ ] Decisions crossing a service boundary derive from the originating subject
- [ ] Decode once, before validation; encode last, per context
- [ ] Queries parameterized, not escaped
- [ ] JWT uses an algorithm allowlist, validates `aud`, revokes on `jti`+`iss`
- [ ] No token in `localStorage`
- [ ] Nothing in the "do not hand-roll" table was hand-rolled

## References

- `references/superseded.md` — the eighteen, with why each old rule existed
- `references/parameters.md` — every concrete number, attributed, dated **2026-09**
- `references/authorization.md` — the ladder worked through on a real API, with the tests
- `references/jwt.md` — RFC 8725's threats and practices, restated for builders
