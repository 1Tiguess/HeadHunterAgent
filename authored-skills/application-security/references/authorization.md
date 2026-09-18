# The authorization ladder, worked

Four rungs, asked in request order. Each prevents a different failure with different code in a
different place. This file works them through on one concrete API and gives the test for each.

## Contents
- [The example API](#the-example-api)
- [Rung 1 — a trusted service layer](#rung-1--a-trusted-service-layer)
- [Rung 2 — per object (BOLA)](#rung-2--per-object-bola)
- [Rung 3 — per field (BOPLA)](#rung-3--per-field-bopla)
- [Rung 4 — the originating subject](#rung-4--the-originating-subject)
- [Alongside: function level (BFLA)](#alongside-function-level-bfla)
- [Why the names matter](#why-the-names-matter)
- [A test suite that actually catches these](#a-test-suite-that-actually-catches-these)

## The example API

An invoicing product. Organisations have members; members have roles; invoices belong to an
organisation and name a customer.

```
GET    /api/invoices/:id
PATCH  /api/invoices/:id
GET    /api/orgs/:orgId/members
POST   /api/orgs/:orgId/members/:userId/role
```

Every failure below is reachable on this API with curl and nothing else.

## Rung 1 — a trusted service layer

**ASVS 8.3.1.** The decision is made server-side, in a layer the client cannot reach around.

```js
// WRONG — the check is in the client
if (user.role === 'admin') {
  showDeleteButton();           // hiding the button is not a control
}
```

The button is a UX affordance. The endpoint behind it is the control. A hidden button is discovered
by reading the bundle; a missing server check is discovered by an attacker.

**Also on this rung:** do not trust a role, org ID, or permission list that arrived in the request
body or a client-set header. Re-derive it from the authenticated session on every request.

**Test:** call every endpoint directly with a valid session for a low-privilege user, ignoring the
UI entirely.

## Rung 2 — per object (BOLA)

**ASVS 8.2.2.** Does this caller own *this specific record*?

```js
// WRONG — authenticated, but not authorized
app.get('/api/invoices/:id', requireAuth, async (req, res) => {
  const invoice = await db.invoices.findById(req.params.id);
  res.json(invoice);                       // any logged-in user reads any invoice
});
```

```js
// RIGHT — ownership is part of the lookup, not a separate check
app.get('/api/invoices/:id', requireAuth, async (req, res) => {
  const invoice = await db.invoices.findOne({
    id:    req.params.id,
    orgId: req.session.orgId,              // scoped at the query
  });
  if (!invoice) return res.sendStatus(404);
  res.json(invoice);
});
```

**Two details that matter more than they look.**

*Scope the query, do not check after the fetch.* A separate `if (invoice.orgId !== session.orgId)`
works until someone adds a code path that forgets it. Making the scope part of every lookup means
the unsafe version does not exist to be forgotten.

*Return 404, not 403.* A 403 confirms the record exists, which is an enumeration oracle. 404 says
nothing.

**Test:** authenticate as user A, request a resource belonging to user B. Do it for **every**
endpoint taking an ID, including nested ones — `/orgs/:orgId/members` is the same bug with an extra
segment.

## Rung 3 — per field (BOPLA)

**ASVS 8.2.3.** Two directions, and most code gets one and misses the other.

### Write side — mass assignment

```js
// WRONG
app.patch('/api/invoices/:id', requireAuth, async (req, res) => {
  await db.invoices.update(scopedQuery(req), req.body);   // every field is writable
});
```

`PATCH {"status": "paid", "amount": 0}` — and the invoice is settled for nothing.

```js
// RIGHT — an allowlist of writable fields, per role
const WRITABLE = {
  member: ['customerName', 'lineItems', 'notes'],
  admin:  ['customerName', 'lineItems', 'notes', 'status'],
};

app.patch('/api/invoices/:id', requireAuth, async (req, res) => {
  const allowed = WRITABLE[req.session.role] ?? [];
  const patch = pick(req.body, allowed);
  if (Object.keys(patch).length !== Object.keys(req.body).length) {
    return res.status(400).json({ error: 'unwritable_field' });   // reject, do not silently drop
  }
  await db.invoices.update(scopedQuery(req), patch);
});
```

**Reject rather than silently dropping.** Silently ignoring a field the caller sent means a
legitimate client's bug looks like success, and an attacker's probe looks identical to normal
traffic.

### Read side — over-fetching

```js
// WRONG — the ORM returns everything the table has
res.json(invoice);          // includes internalMargin, assignedRep, riskScore, auditNotes
```

Serialise through an explicit projection, per role. "The UI does not display it" is not a control —
the response body is the API.

**Test:** send an extra field like `role`, `orgId`, `balance` or `isAdmin` and check whether it
sticks. Fetch a record as a low-privilege user and read the raw JSON for fields they should not see.

## Rung 4 — the originating subject

**ASVS 8.3.3.** When service A calls service B on a user's behalf, the authorization decision must
derive from **the user**, not from A's machine-to-machine token.

```
browser ──(user session)──> billing-api ──(service token)──> invoice-service
                                                                    │
                                    "the caller is billing-api" ────┘   ← WRONG
                                    "the caller is user 4171"  ────┘   ← RIGHT
```

If `invoice-service` authorizes on the service token, then **anything holding a valid service token
can read every user's invoices**, and a single compromised internal service becomes total data
access. This is the most damaging rung and the least tested, because it only appears once there is
more than one service.

Propagate the subject — a token exchange, an assertion, or a signed on-behalf-of claim. Not a
plain `X-User-Id` header, which any internal caller can set.

**Test:** call the internal service directly with a valid service token and a user ID you have no
relationship to.

## Alongside: function level (BFLA)

Not a rung — a parallel axis. Can a non-admin call the admin endpoint directly?

```
POST /api/orgs/42/members/99/role   {"role": "admin"}
```

The UI never shows this to a member. The endpoint does not care what the UI shows.

**Test:** enumerate every route, call each as the lowest-privilege user you have, and record which
ones respond with anything other than a denial. Pay attention to verbs — `GET /users` may be
protected while `DELETE /users/:id` was added later and was not.

## Why the names matter

| Name | Full | Rung | Fix lives in |
|---|---|---|---|
| **BOLA** | Broken Object Level Authorization | 2 | The data access layer — scope the query |
| **BOPLA** | Broken Object Property Level Authorization | 3 | The serialisation and binding layer — allowlist fields |
| **BFLA** | Broken Function Level Authorization | parallel | The routing layer — require a role per route |

**Collapsing these into "check permissions" is exactly how they get missed**, because the three
mitigations are in three different layers and a single "did we check auth?" review question passes
when any one of them is present.

## A test suite that actually catches these

These are cheap to write once and they catch regressions forever.

```
Fixtures: org A with user A1 (member) and A2 (admin); org B with user B1.
          One invoice in each org.

For every endpoint taking an ID:
  1. A1 requests B's invoice                     → expect 404
  2. unauthenticated request                     → expect 401
  3. A1 sends a field only admins may write      → expect 400
  4. A1 fetches A's invoice, assert the response  → exact field set, no extras
  5. A1 calls every admin-only route             → expect 403 or 404
  6. internal service token with B1's ID
     against an A-scoped resource                → expect denial
```

Case 4 is the one people leave out, and it is the only one that catches read-side BOPLA. Assert the
**exact** set of keys in the response — a test that checks for the presence of expected fields will
not notice unexpected ones.
