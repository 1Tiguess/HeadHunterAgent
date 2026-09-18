# Hunt notes — application security

**Gap.** Claude writes authentication, session handling and authorization from a
pattern library that is roughly 2017-vintage. It reaches for composition rules,
90-day expiry, security questions, `X-Frame-Options`, `localStorage` tokens and
naive double-submit CSRF — all of which the current normative sources now
*reverse*. The gap is not "does not know security"; it is "knows the superseded
version confidently."

**Source reach: excellent.** This is the only hunt in the batch where every
primary source was actually fetched rather than search-extracted. The reason is
structural and worth recording: **the canonical text for this domain lives as
files in Git repositories**, so the GitHub-first route reached it intact where
the rendered sites were blocked.

| Wanted | Blocked | Reached instead |
|---|---|---|
| `pages.nist.gov/800-63-4/sp800-63b.html` | `EGRESS_BLOCKED` | `raw.githubusercontent.com/usnistgov/800-63-4/nist-pages/sp800-63b.html` |
| `cheatsheetseries.owasp.org` | rendered site | `OWASP/CheatSheetSeries` markdown |
| ASVS rendered | — | `OWASP/ASVS` v5.0.0 chapter files |
| RFC 8725 (JWT BCP) | — | fetched |

---

## 1. NIST SP 800-63B-4 — the reversals that are normative, not advisory

Passwords ("memorized secrets", §3.1.1.2):

- Verifiers **SHALL NOT** impose composition rules. No mandated uppercase,
  digit or symbol.
- Verifiers **SHALL NOT** require periodic change. The only trigger for a
  forced change is evidence of compromise.
- **Minimum length is tiered: 15 characters when the password is the sole
  factor, 8 only when it is one factor of several.** The jump from the
  long-standing 8 to 15 is the single change most models have not absorbed.
- Must accept at least 64 characters, all printing ASCII plus space, plus
  Unicode.
- Compare prospective passwords against a blocklist of compromised values —
  **against the whole string, not substrings**.
- A password hint retrievable by an unauthenticated party is prohibited.
- Verifiers **SHALL NOT** prompt for knowledge-based "security questions."
- Salts at least 32 bits. Failed-attempt rate limiting required.

Session and reauthentication anchors (§2.1.3 / §2.2.3 / §2.3.3) — the part
almost nobody quotes correctly:

| AAL | Max session | Inactivity timeout | Reauth |
|---|---|---|---|
| AAL1 | 30 days | none required | — |
| AAL2 | 24 hours | 1 hour | single factor permitted at the inactivity boundary |
| AAL3 | 12 hours | 15 minutes | full reauthentication, both factors |

These are the real anchors behind "idle vs absolute timeout" and are a far
better basis for a design decision than the usual hand-wave.

## 2. ASVS 5.0 — levels, and the one ordering rule that matters

Level shape: **L1 ≈ the first 20% of requirements, L2 ≈ a further 50%** (so
L1+L2 ≈ 70%, which is where most applications should aim), **L3 ≈ the remaining
30%**. Cite requirements as `v5.0.0-8.2.2`.

**V1 ordering rule (the highest-value single item in the hunt).** 1.1.1: decode
input *exactly once* into its canonical form **before** validation. 1.1.2:
output encoding is the **last** step before the interpreter. Six distinct
encoding contexts are named. Most injection bugs are an ordering failure, not a
missing-control failure — the control was present but ran on the wrong side of
a decode.

**V2.** Input validation "does not remove or replace the need to use correct
encoding, parameterization, or sanitization." Validation is defense in depth,
**never the control**.

**V8 — the authorization ladder**, in the order a request traverses it:

1. `8.3.1` decisions made at a **trusted service layer**, never client-side
2. `8.2.2` **per object** — this is IDOR / BOLA
3. `8.2.3` **per field** — this is BOPLA, mass assignment's read-side twin
4. `8.3.3` the decision derives from the **originating subject**, not from an
   intermediary service's machine-to-machine token

**BOLA / BFLA / BOPLA** is the precise vocabulary. Object-level, function-level
and object-property-level authorization are three different failures with three
different fixes, and collapsing them into "check permissions" is exactly how
they get missed.

**V7 sessions.** Reference tokens ≥128 bits from a CSPRNG (7.2.3). New token on
authentication *including re-authentication*, prior token terminated (7.2.4,
L1). After termination the token must be genuinely unusable — for self-contained
tokens that means a real mechanism: blocklist, per-user invalidation timestamp,
or key rotation (7.4.1, L1). Account termination kills all sessions (7.4.2).
After a credential or MFA change, offer to log out other sessions (7.4.3, L2).

## 3. Crypto parameters, current

- **Argon2id** — five equivalent-strength trade points, which is more useful
  than a single number: m=47104/t=1/p=1, m=19456/t=2/p=1, m=12288/t=3/p=1,
  m=9216/t=4/p=1, m=7168/t=5/p=1.
- **scrypt** — N=2^17/r=8/p=1 down through N=2^13/r=8/p=10.
- **bcrypt** — cost ≥10, and the detail that bites: **bcrypt truncates at 72
  bytes.** The correct pre-hash is
  `bcrypt(base64(hmac-sha384(password, pepper)), salt, cost)` — base64 because
  raw digest bytes can contain a null that truncates again, and HMAC-with-pepper
  rather than plain hashing to block password shucking.
- **PBKDF2** — 600,000 iterations (HMAC-SHA256), 220,000 (SHA512), 1,300,000+
  (SHA1, legacy only).
- Session ID ≥64 bits entropy (OWASP), reference token ≥128 bits (ASVS 7.2.3),
  JWT MAC secret ≥160 bits.
- Cookie form: `Set-Cookie: __Host-SessionID=<v>; Secure; HttpOnly; SameSite=Strict; Path=/`
- Pepper is shared across all hashes, lives in a vault or HSM **not** beside the
  hash store, and rotating it forces a reset for every affected user.

## 4. RFC 8725 — JWT, where the threat and the practice are paired

Tighter than any secondary account of it:

- §2.9 → §3.1: implementations have compared `alg` **case-insensitively**, so
  `"noNE"` slipped past a denylist. Therefore **allowlists for critical
  parameters, never blocklists**, and the library must expose a way to restrict
  the permitted set.
- §3.1 also: **each key MUST be used with exactly one algorithm, enforced and
  validated at the moment the cryptographic operation executes.** A stronger and
  more implementable rule than "don't confuse HMAC and RSA."
- Revocation: keying a denylist on the raw JWT or a hash of it is **unsafe**,
  because JWTs are malleable — with ECDSA in particular an attacker can produce
  a different byte string that still verifies. **Key on `jti` + `iss`.**
- `jwk`, `jku`, `x5u`, `x5c` carry attacker-controllable key material. Never
  take a verification key from the token unless it chains to a pre-established
  trust anchor. `kid`, `jku`, `x5u` reach a DB lookup or an HTTP fetch, so they
  must be sanitized against injection (MUST), matched against a location
  allowlist (SHOULD), and resolved hostnames checked so the request cannot hit
  loopback or link-local — **SSRF via a JWT header**.
- §3.8 `aud` MUST be present and the relying party MUST reject when it is absent
  or does not include it. §3.11 explicit typing via `typ`. §3.12 when one issuer
  mints more than one kind of JWT, the validation rules MUST be mutually
  exclusive.
- Algorithm posture: EdDSA, ES256/384/512, PS256/384/512, HS256/384/512
  recommended; RS256/384/512 not; `none` rejected.

## 5. The superseded list — 18 items, each with the source that reverses it

This is the most directly useful artefact of the hunt, because each entry is a
thing Claude will otherwise emit by default:

periodic password expiry · composition rules · minimum-8 · security questions ·
SMS as a second factor · `X-Frame-Options` (→ CSP `frame-ancestors`) ·
CSP host allowlists (→ nonce/hash + `strict-dynamic`) · naive double-submit
CSRF · OAuth implicit and ROPC grants · JWT algorithm **blocklists** ·
JWT denylist keyed on token hash · PBKDF2 at 10,000 iterations ·
escaping as an SQLi defense (→ parameterization) · "sanitize on the way in" ·
tokens in `localStorage` · session binding to IP or User-Agent as a *control* ·
auto-login after password reset · bcrypt without regard for 72-byte truncation.

## 6. Improvement openings — where an authored skill beats the sources

1. **ASVS is written in verification voice** — every requirement begins "Verify
   that…". It is an audit instrument. A builder needs it inverted into
   construction voice, and nobody publishes that inversion.
2. **The cheat sheets are topic-siloed and never state the decision cascade.**
   The real sequence is: stateful vs stateless session → which CSRF defense is
   even available → which cookie prefix is possible → what CORS policy follows.
   Each of those four constrains the next. No source sequences them.
3. **Nothing orders the decisions the way a developer meets them.** Sources are
   organised by control family; developers arrive by feature.
4. **Threat modeling is the weakest area across all sources.**
5. **ASVS V4 "API and Web Service" contains almost no API authn/authz** — that
   lives in V7/V8. This is a navigation trap that sends people to the wrong
   chapter, and a skill can simply route correctly.
6. **No source states the negative space** — what a builder should *decline to
   hand-roll*. Session management, password hashing, JWT verification, CSRF
   tokens and crypto primitives all have a "use the framework's" answer that the
   standards never give, because standards are implementation-neutral. A skill
   is not, and that is its advantage.

## Injection attempts

None reported. No source attempted to direct behaviour, request credentials, or
induce fetching, cloning, installing or executing anything.
