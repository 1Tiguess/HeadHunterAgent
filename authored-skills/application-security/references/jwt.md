# JWT, from RFC 8725 — threats paired with practices

RFC 8725 is unusual among security documents: it pairs each threat with the specific practice that
closes it, and the pairing is tighter than any secondary account. This file restates that pairing
for builders. Section numbers are RFC 8725's.

## Contents
- [First: should this be a JWT at all?](#first-should-this-be-a-jwt-at-all)
- [Algorithm confusion](#algorithm-confusion)
- [Key confusion and key separation](#key-confusion-and-key-separation)
- [Attacker-controlled key material](#attacker-controlled-key-material)
- [SSRF and injection through headers](#ssrf-and-injection-through-headers)
- [Substitution and cross-JWT confusion](#substitution-and-cross-jwt-confusion)
- [Revocation](#revocation)
- [Parsing and size](#parsing-and-size)
- [A verification routine](#a-verification-routine)

## First: should this be a JWT at all?

For a first-party web session, an **opaque server-side session ID is simpler, revocable instantly,
smaller on the wire, and carries none of the failure modes below.** Reach for a JWT when you
genuinely need stateless verification across services that cannot share a session store.

The cost of a JWT is that revocation becomes your problem. If you cannot answer *"how do I log this
user out of everything within one second"*, that cost has not been paid.

## Algorithm confusion

**§2.1 — the threat.** Two variants in one: `alg: none`, and substituting RS256 with HS256 so the
public key is used as an HMAC secret. Both let an attacker mint tokens.

**§3.2 — the practice.** Require current algorithms. Libraries **MUST NOT** generate `none` unless
explicitly asked.

**§2.9 — the variant that defeats the obvious fix, and the reason this section exists.**
Implementations have treated `alg` **case-insensitively**, so `"noNE"` slipped past a blocklist
checking for `"none"`.

**§3.1 — therefore: allowlists, not blocklists**, for critical parameters. And libraries must expose
a mechanism letting the developer restrict the permitted set.

```js
// WRONG
if (header.alg === 'none') reject();

// RIGHT
const PERMITTED = new Set(['ES256']);
if (!PERMITTED.has(header.alg)) reject();
```

## Key confusion and key separation

**§3.1 carries the rule that closes this at the root:**

> Each key **MUST** be used with exactly one algorithm, and this **MUST** be enforced and validated
> at the moment the cryptographic operation executes.

Stronger and more implementable than "don't confuse HMAC and RSA", because it does not depend on
your recognising that a confusion is happening. Bind the algorithm to the key at the key store, and
the substitution attack has nowhere to land.

**§3.6:** a human-memorizable password **MUST NOT** be used directly as an HMAC key. MAC secrets
need **≥ 160 bits** of entropy, should match the algorithm's output size, and must not be reused
across issuer/audience pairs.

**§3.4:** every cryptographic operation in the token must validate, or the whole token is rejected.
Libraries must let the recipient distinguish an unsecured JWT from a JWS, a JWE, and a nested token.

## Attacker-controlled key material

Four header parameters can carry or point at a verification key:

| Header | Carries |
|---|---|
| `jwk` | An embedded public key |
| `jku` | A URL to a key set |
| `x5u` | A URL to an X.509 certificate |
| `x5c` | An embedded certificate chain |

**Never take a verification key from the token** unless it chains to a **pre-established trust
anchor**. Taking `jwk` at face value means the attacker signs with their own key and you verify
against it — the signature is valid and means nothing.

Validate `kid` before using it in a lookup.

## SSRF and injection through headers

**§2.8 → §3.9.** `kid`, `jku` and `x5u` are attacker-controlled strings that reach a **database
lookup** or an **HTTP fetch**. Therefore:

- sanitize against SQL and LDAP injection — **MUST**
- match against a location allowlist — **SHOULD**
- **check any resolved hostname so the request is not made to loopback or local addresses** — MUST

That last one is **SSRF through a JWT header**, and it is the failure mode least likely to be
anticipated, because nothing about "verify this token" suggests your server is about to make an
outbound request to a URL the attacker chose.

## Substitution and cross-JWT confusion

**§2.6 → §3.7, §3.8.** The application **MUST** validate that the keys used belong to the `iss`.
The token **MUST** carry `aud`, and the relying party **MUST** reject when `aud` is absent or does
not include it.

Without `aud` validation, a token minted for service X is accepted by service Y — same issuer, same
key, wrong audience.

**§2.7 → §3.11, §3.12.** Explicit typing via the `typ` header with a registered media type
(`application/example+jwt` → `typ: example+jwt`) — **SHOULD**. And when one issuer mints more than
one kind of JWT, the validation rules **MUST be mutually exclusive**, so a token of the wrong kind is
**rejected** rather than merely unrecognised.

That distinction matters: "I do not know what this is, so I will ignore the fields I do not
recognise" accepts an access token where a refresh token was expected.

## Revocation

**The rule that is genuinely non-obvious:** keying a denylist on the raw JWT, or on a hash of it, is
**unsafe**, because **JWTs are malleable**. Particularly with ECDSA signatures, an attacker can
produce a different byte string that still verifies against the same key. The hash changes; the
denylist misses; the token still works.

**Key the denylist on `jti` + `iss`.**

The alternatives RFC 8725 points at:

- **Token Status Lists** — a compact revocation structure the verifier fetches
- **Short expiry plus sender-constraining** — DPoP or TLS binding, so a stolen token is not usable by
  the thief and the window is small enough that revocation matters less

Short expiry alone is not revocation. It is a bound on how long revocation takes, which is a
different property, and it is only acceptable if you have decided the bound is tolerable.

## Parsing and size

**§2.11 → §3.14.** Confirm the token is a legal compact serialization **while parsing** — only
base64url characters and periods. A mismatch between the format used for verification and the format
used for claim extraction allows a forged payload: one parser sees one thing, the other sees
another.

**§3.15.** Cap JWE decompressed size. Deployed libraries use a few hundred KB — 250 KB is a cited
figure. Without a cap, a small token expands into a memory exhaustion.

**§3.13.** Reject `p2c` values above roughly twice the recommended figure (600,000 for
HMAC-SHA-256). An unbounded iteration count is a CPU exhaustion the attacker chooses.

**§3.5.** **SHOULD NOT** compress before encrypting — ciphertext length leaks plaintext information.

## A verification routine

In order. Each step can reject; none is optional.

```
1.  Parse as compact serialization. Reject anything not base64url-and-periods.       §3.14
2.  Read the header. Do NOT trust it yet.
3.  alg is in your allowlist, exact match.                                            §3.1
4.  Resolve the key by kid — sanitized, allowlisted, never fetched from a URL in
    the token unless it chains to a pre-established anchor.                           §3.9
5.  The key is bound to exactly this algorithm. Enforce at this point.                §3.1
6.  Verify the signature. Every cryptographic operation must validate.                §3.4
7.  typ matches the kind of token this endpoint accepts — mutually exclusive
    from your other token kinds.                                                      §3.11-12
8.  iss is one you trust, and the key belongs to that iss.                            §3.7
9.  aud is present and includes you. Reject if absent.                                §3.8
10. exp / nbf within tolerance. Small leeway for clock skew, not minutes.
11. jti + iss is not on the denylist.
12. Only now read the claims.
```

**Step 12 is the discipline.** Reading a claim before step 11 completes is how a rejected token
still influences behaviour — logging the subject, looking up the user, warming a cache. Do nothing
with the payload until verification has fully passed.
