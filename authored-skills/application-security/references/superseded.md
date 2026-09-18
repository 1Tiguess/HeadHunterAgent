# The eighteen reversals, and why each old rule existed

Knowing *why* a rule existed is what lets you recognise the next one that goes stale. Each entry
below pairs the old advice with the reasoning that produced it, the current position, and the source
that reverses it.

## Contents
- [Passwords](#passwords)
- [Sessions and tokens](#sessions-and-tokens)
- [Browser headers](#browser-headers)
- [CSRF](#csrf)
- [OAuth](#oauth)
- [JWT](#jwt)
- [Injection](#injection)
- [Account recovery](#account-recovery)
- [The pattern underneath](#the-pattern-underneath)

## Passwords

**1. Periodic expiry.** *Why it existed:* if a password leaks and you do not know, rotation bounds
the exposure window. *Why it reversed:* forced rotation produces predictable derivations —
`Summer2024!` becomes `Summer2025!` — so the entropy gain is near zero while the usability cost is
real. NIST §3.1.1.2 now says verifiers **SHALL NOT** require periodic change. The only trigger is
evidence of compromise.

**2. Composition rules.** *Why it existed:* a proxy for entropy, back when the threat model was
brute force against a short password. *Why it reversed:* users satisfy the rule in the most
predictable way available (`Password1!`), so the rule constrains the search space rather than
expanding it. Length and a compromised-password blocklist do the work instead.

**3. Minimum length of 8.** *Why it existed:* it was a reasonable floor against offline cracking with
the hardware of the time. *Why it reversed:* hardware. **NIST now tiers it — 15 characters when the
password is the sole factor, 8 only when combined with MFA** (§3.1.1.2, ASVS 6.2.1). This is the
single change most generated code has not absorbed. Maximum must accept at least 64, all printing
ASCII plus space, plus Unicode (ASVS 6.2.9).

**4. Security questions.** *Why it existed:* a recovery channel that needed no second device. *Why it
reversed:* the answers are public records, social-media content, or guessable from a short list.
NIST §3.1.1.2 prohibits verifiers prompting for them.

**5. SMS as a second factor.** *Why it existed:* everyone has a phone, and SMS needs no app. *Why it
reversed:* SIM swap, SS7 interception, and carrier-support social engineering. Discouraged and
restricted, not banned — it is still better than nothing, and materially worse than everything else.

**12. PBKDF2 at 10,000 iterations.** *Why it existed:* it was a defensible cost in the era it was
published. *Why it reversed:* GPUs. **600,000 with HMAC-SHA256, 220,000 with SHA512.** Orders of
magnitude above the figures still circulating in tutorials.

**18. bcrypt without regard for its 72-byte truncation.** *Why it was missed:* bcrypt silently
ignores bytes past 72, so nothing fails and nobody notices. Long passphrases and pre-hashed inputs
both hit it. The naive fix — hash then bcrypt — reintroduces two problems: raw digest bytes can
contain a null that truncates again, and a plain pre-hash enables password shucking. The corrected
form is `bcrypt(base64(hmac-sha384(password, pepper)), salt, cost)`.

## Sessions and tokens

**15. Tokens in `localStorage`.** *Why it existed:* convenient for SPAs, avoids cookie configuration,
and sidesteps CSRF by removing the ambient credential. *Why it reversed:* any XSS reads it
instantly, and XSS is far more common than CSRF. A `__Host-` prefixed `HttpOnly` cookie is
unreadable by script. The CSRF you reintroduce is a solved problem; the XSS exposure is not.

**16. Binding a session to IP or User-Agent.** *Why it existed:* a stolen cookie used from elsewhere
would not work. *Why it reversed:* NAT, corporate proxies, mobile networks moving between towers,
and privacy features all change the IP mid-session; User-Agent is attacker-controlled anyway. Treat
divergence as a **detection signal** worth logging and possibly re-authenticating on — never as a
control that must hold.

## Browser headers

**6. `X-Frame-Options`.** *Why it existed:* it was the first clickjacking defense browsers shipped.
*Why it reversed:* it is coarse — `ALLOW-FROM` was never widely supported — and CSP
`frame-ancestors` expresses the same intent with a proper source list and consistent support.

**7. CSP host allowlists.** *Why it existed:* enumerate the CDNs you trust and block everything else.
*Why it reversed:* allowlists leak. A single allowlisted host serving a JSONP endpoint, an outdated
Angular, or arbitrary user uploads reopens injection. **Nonce or hash based, with
`strict-dynamic`** so trust propagates to scripts your trusted script loads, rather than to
whatever else lives on an allowlisted domain.

## CSRF

**8. Naive double-submit.** *Why it existed:* it needs no server-side state — put a random value in a
cookie and in the form, compare them. *Why it reversed:* an attacker who can set a cookie on your
domain (a subdomain XSS, a MITM on a sibling host) controls both halves of the comparison. Use a
**signed** double-submit token bound to the session, or a synchronizer token, with `SameSite` as
defense in depth rather than the whole answer.

## OAuth

**9. Implicit and password (ROPC) grants.** *Why they existed:* implicit predated CORS being usable
for token exchange; ROPC was a migration path for first-party apps holding credentials. *Why they
reversed:* implicit puts the token in the URL fragment, where it lands in history, logs and
referrers; ROPC teaches users to type their password into anything asking. **Authorization code with
PKCE** for both cases.

## JWT

**10. Algorithm blocklists.** *Why they existed:* block `none`, permit the rest. *Why it reversed:*
**implementations have compared `alg` case-insensitively, so `"noNE"` passed a blocklist checking for
`"none"`** (RFC 8725 §2.9). §3.1 therefore requires **allowlists** for critical parameters, and
requires libraries to expose a mechanism for restricting the permitted set. The same section carries
the stronger rule: **each key MUST be used with exactly one algorithm, enforced and validated at the
moment the cryptographic operation executes.**

**11. Denylisting a revoked JWT by its hash.** *Why it existed:* the obvious way to revoke a
stateless token. *Why it reversed:* **JWTs are malleable** — particularly with ECDSA signatures, an
attacker can produce a different byte string that verifies against the same key, so the hash
changes and the denylist misses. **Key on `jti` + `iss`.**

## Injection

**13. Escaping as an SQL injection defense.** *Why it existed:* before prepared statements were
universal, escaping was the available tool. *Why it reversed:* escaping is character-set dependent
and context dependent, and one missed path is a full compromise. **Parameterize.** Escaping is not a
weaker version of parameterization; it is a different and less reliable mechanism.

**14. "Sanitize on the way in".** *Why it existed:* it feels like a single chokepoint. *Why it
reversed:* you cannot know at input time which interpreter the value will reach, and the same value
may reach several. Stored data must remain faithful to what the user typed. **Encode on the way out,
per context** — ASVS 1.1.2 makes output encoding the last step before the interpreter. Validation
still happens on input, as defense in depth, never as the control.

## Account recovery

**17. Auto-login after a password reset.** *Why it existed:* it is smoother. *Why it reversed:* it
turns a reset link — which travels through email and may sit in an inbox indefinitely — into a
direct session grant. Reset the password, then make them authenticate with it.

## The pattern underneath

Four forces produced almost every reversal above:

1. **Hardware moved.** Iteration counts and length minimums decay on a schedule.
2. **Human behaviour was measured.** Composition rules and expiry were reasoned about rather than
   observed, and the observation reversed them.
3. **Allowlists beat blocklists, every time.** CSP allowlists is the one exception, and only because
   the "allowlist" there was of *hosts*, which is a proxy for what you actually trust.
4. **Defense in depth got mistaken for the defense.** Validation, escaping and IP binding are all
   useful and none is a control.

When you meet security advice that is not on this list, ask which of the four it is exposed to.
That is how you spot the next one.
