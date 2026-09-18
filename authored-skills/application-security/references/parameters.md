# Security parameters

**As of 2026-09.** Every number here decays. Iteration counts rise with hardware; algorithm postures
shift as attacks mature. Re-check against the current source before quoting any of it in a design
document.

## Contents
- [Password hashing](#password-hashing)
- [Salt and pepper](#salt-and-pepper)
- [Entropy minimums](#entropy-minimums)
- [Password policy](#password-policy)
- [Session lifetimes](#session-lifetimes)
- [Cookies](#cookies)
- [JWT algorithms](#jwt-algorithms)
- [Sources](#sources)

## Password hashing

**Argon2id — preferred.** Five parameter sets presented as equivalent-strength trade points, which is
more useful than a single recommendation because it lets you trade memory against time against your
actual hardware:

| m (KiB) | t | p |
|---|---|---|
| 47104 (46 MiB) | 1 | 1 |
| 19456 (19 MiB) | 2 | 1 |
| 12288 (12 MiB) | 3 | 1 |
| 9216 (9 MiB) | 4 | 1 |
| 7168 (7 MiB) | 5 | 1 |

Higher memory is generally the better trade, because memory is what makes GPU and ASIC attacks
expensive. Drop down the table only when a memory ceiling forces it.

**scrypt.** N=2^17, r=8, p=1 — down through N=2^13, r=8, p=10.

**bcrypt.** Work factor **≥ 10**. And the trap: bcrypt **truncates input at 72 bytes**, silently.
The correct pre-hash, if you need one:

```
bcrypt(base64(hmac-sha384(password, pepper)), salt, cost)
```

- `base64` — because raw digest bytes can contain a null byte, which truncates again
- `hmac-...(password, pepper)` rather than a plain hash — a plain pre-hash enables **password
  shucking**, where an attacker who already has a leaked fast hash of the same password can strip the
  bcrypt layer

**PBKDF2.** 600,000 iterations with HMAC-SHA256. 220,000 with SHA512. 1,300,000+ with SHA1 (legacy
only — do not choose SHA1 for new work).

## Salt and pepper

**Salt.** At least **32 bits**, unique per password, generated from a CSPRNG, stored alongside the
hash. Not secret.

**Pepper.** Shared across all stored hashes, and it must live **somewhere other than the hash
store** — a secrets vault or an HSM. The entire value of a pepper is that a database dump does not
include it.

**Decide the rotation story before you deploy one.** Rotating a pepper invalidates every hash it
protected, which means a password reset for every affected user. If you cannot accept that, either
version your peppers (store which pepper version each hash used) or do not use one.

## Entropy minimums

| Thing | Minimum | Source |
|---|---|---|
| Session ID | **64 bits** (16 hex characters) | OWASP |
| Reference token | **128 bits** | ASVS 7.2.3 |
| JWT MAC secret | **160 bits**, matching the algorithm's output size | RFC 8725 |
| Password salt | 32 bits | NIST |

All from a **CSPRNG**. Never `Math.random()`, never a language `rand()`, and never a UUIDv4 used as
a secret — v4 is random but is not specified as cryptographically secure in every implementation,
and it advertises its own structure.

## Password policy

| Rule | Value |
|---|---|
| Minimum, sole factor | **15 characters** |
| Minimum, with MFA | 8 characters |
| Maximum accepted | at least 64 |
| Character set | all printing ASCII, space, **Unicode** |
| Composition rules | **forbidden** |
| Periodic expiry | **forbidden** |
| Security questions | **forbidden** |
| Retrievable hints | forbidden |
| Compromised-password blocklist | required, compared against the **whole string** |
| Failed-attempt rate limiting | required |

## Session lifetimes

**The assurance-level anchors** (NIST §2.1.3 / §2.2.3 / §2.3.3):

| AAL | Absolute maximum | Inactivity timeout | Reauthentication |
|---|---|---|---|
| AAL1 | 30 days | none required | — |
| AAL2 | 24 hours | 1 hour | single factor permitted at the boundary |
| AAL3 | 12 hours | 15 minutes | full reauthentication, both factors |

**Practical ranges** (OWASP, convention rather than normative):

| Risk | Idle | Absolute |
|---|---|---|
| High-value (banking, admin) | 2–5 minutes | — |
| Low-risk | 15–30 minutes | — |
| Office-worker pattern | — | 4–8 hours |

There is also an optional **renewal** timeout: transparently regenerate the session ID mid-session,
capping the useful life of a stolen one without logging anyone out.

## Cookies

```
Set-Cookie: __Host-SessionID=<value>; Secure; HttpOnly; SameSite=Strict; Path=/
```

`__Host-` is the strongest prefix: it requires `Secure`, requires `Path=/`, and **forbids a `Domain`
attribute**, which is what stops a subdomain from setting it. Use it unless you genuinely need the
cookie shared across subdomains, in which case `__Secure-` is the fallback and you accept the
subdomain risk consciously.

`SameSite=Strict` breaks inbound links from other sites landing on an authenticated page. Where that
matters, `Lax` is the compromise — not `None`.

On logout, send an expired `Set-Cookie` **and** destroy the session server-side. Consider
`Clear-Site-Data: "cache", "cookies", "storage"` with `Cache-Control: no-store`.

## JWT algorithms

**Recommended:** EdDSA · ES256, ES384, ES512 · PS256, PS384, PS512 · HS256, HS384, HS512 (MAC only).

**Not recommended:** RS256, RS384, RS512 (RSASSA-PKCS1-v1_5).

**Rejected:** `none`, in any casing. Enforce with an **allowlist**, because a blocklist checking for
`"none"` has been defeated by `"noNE"`.

**One key, one algorithm** — enforced and validated at the point the cryptographic operation
executes, not at configuration time.

Human-memorizable passwords **MUST NOT** be used directly as an HMAC key (RFC 8725 §3.6).

Cap JWE decompressed size — deployed libraries use a few hundred KB, e.g. 250 KB (§3.15). Reject
`p2c` values above roughly twice the recommended figure (§3.13). **Do not compress before
encrypting** (§3.5) — ciphertext length leaks plaintext information.

## Sources

All four read in full, not search-extracted:

- **NIST SP 800-63B-4** — password policy, AAL session and reauthentication anchors, salt minimum
- **OWASP ASVS 5.0** — entropy minimums, level structure, the V1/V2/V7/V8 requirements cited
  throughout this skill
- **OWASP Cheat Sheet Series** — hashing parameters, cookie form, practical timeout ranges, JWT
  posture
- **RFC 8725 (JWT Best Current Practices)** — algorithm handling, key separation, revocation,
  header-driven SSRF, size caps
