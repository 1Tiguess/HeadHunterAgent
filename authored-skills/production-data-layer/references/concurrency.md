# Concurrency: transactions, locking, pooling

## Contents
- [Transaction boundaries](#transaction-boundaries)
- [Side effects: after-commit versus outbox](#side-effects-after-commit-versus-outbox)
- [Optimistic locking](#optimistic-locking)
- [Pessimistic locking](#pessimistic-locking)
- [SKIP LOCKED and the queue pattern](#skip-locked-and-the-queue-pattern)
- [Advisory locks](#advisory-locks)
- [Deadlocks](#deadlocks)
- [Connection pooling](#connection-pooling)
- [What transaction-mode pooling breaks](#what-transaction-mode-pooling-breaks)

## Transaction boundaries

**Nested blocks are savepoints, not transactions.**

> When an inner block completes successfully, its effects can still be rolled back if an exception is
> raised in the outer block at a later point.

This surprises people who wrote the inner block expecting it to be durable on its own. Where a block
genuinely must be outermost, assert it — most frameworks have a "durable" flag that raises if the
block turns out to be nested.

**Do not catch exceptions inside an atomic block.**

> You may hide from the framework the fact that a problem has happened.

After a database error the transaction is **broken**, and any query issued before the rollback
raises a transaction-management error. The correct shape is:

```python
try:
    with atomic():
        do_work()
except IntegrityError:
    handle()          # outside the block — the rollback has already happened
```

Not:

```python
with atomic():
    try:
        do_work()
    except IntegrityError:
        handle()      # the transaction is already broken; this query will raise
```

**A rollback does not revert in-memory state.** Model objects keep whatever you assigned to them
before the failure. Re-read or restore by hand, or you will serialise values that were never
committed.

**Transaction-per-request is a scaling trap.** Frameworks offering it warn that it *"makes it
inefficient when traffic increases"*, and middleware and template rendering execute **outside** the
transaction anyway — so it does not even deliver the guarantee it appears to. Scope transactions to
the unit of work.

**Keep transactions short.** An open transaction holds locks, pins the snapshot, and blocks vacuum
from reclaiming rows. A transaction open for minutes while an HTTP call completes is how a healthy
database runs out of room.

## Side effects: after-commit versus outbox

**Never do non-database work inside a transaction.** No emails, no HTTP calls, no job enqueues, no
cache writes, no file operations.

The transaction cannot span the database and the outside world. That leaves exactly two designs, and
**they are not equivalent**:

### After-commit callback

```python
with atomic():
    order = Order.objects.create(...)
    on_commit(lambda: send_confirmation(order.id))
```

> Your callbacks are executed **after** a successful commit, so a failure in a callback will not
> cause the transaction to roll back.

**This is the lossy option.** The row is committed; if the process dies between commit and callback,
or the callback throws, the side effect never happens and nothing records that it did not. There is
no retry, because there is no record.

Acceptable when losing the side effect is tolerable — a confirmation email, a metric, a cache
warm.

### Outbox

```python
with atomic():
    order = Order.objects.create(...)
    Outbox.objects.create(                 # same transaction, same durability
        topic="order.created",
        payload={"order_id": order.id},
    )
# a separate worker polls Outbox, delivers, marks delivered
```

The outbox row commits atomically with the data. If delivery fails, the row is still there and the
worker retries. Costs a table, a worker, and at-least-once semantics the consumer must tolerate.

**Required when the side effect must not be lost** — granting access after a payment, provisioning
after a signup, notifying another system of record.

**There is no third option.** Code that calls the external system inside the transaction has chosen
a worse version of the lossy one: it holds locks for the duration of a network call, and a commit
failure after a successful external call leaves the two systems permanently disagreeing.

## Optimistic locking

A version column participates in the `UPDATE`'s `WHERE` clause:

```sql
UPDATE documents SET body = $1, version = version + 1
WHERE id = $2 AND version = $3;
-- 0 rows affected means someone else got there first
```

**The application must catch the zero-row result and decide whether to retry.** The framework will
not decide for you, and silently ignoring it is a lost update.

**Choose optimistic on the right axis.** It fits *read-often, write-sometimes*, and especially **long
conversations spanning several database transactions** — a user editing a form over several minutes,
where a pessimistic lock would have to be held across a think-time gap. **The argument is
conversation length, not contention rate.**

Two variants worth knowing:

- **Force-increment** — bump the version even when no field on the row changed. This is the mechanism
  for *"a child row changed, so the aggregate root is now stale"*, which plain versioning cannot
  express.
- **Versionless / dirty checking** — put only the **changed** fields in the `WHERE` clause. This
  *"minimises the risk of a conflict across non-overlapping property changes"*, so two users editing
  different fields of the same row both succeed. It needs dynamic UPDATE generation.

A version or timestamp property **can never be null** on a detached instance — a null version means
"transient", regardless of any other rule.

## Pessimistic locking

```sql
SELECT * FROM accounts WHERE id = $1 FOR UPDATE;            -- waits
SELECT * FROM accounts WHERE id = $1 FOR UPDATE NOWAIT;     -- fails immediately if locked
SELECT * FROM accounts WHERE id = $1 FOR UPDATE SKIP LOCKED; -- skips locked rows
```

- **`FOR UPDATE`** — exclusive; other writers wait
- **`FOR NO KEY UPDATE`** — weaker; permits concurrent foreign-key references
- **`FOR SHARE`** — shared read lock
- **`NOWAIT`** — fail immediately rather than queue. Use when waiting is worse than failing
- **`SKIP LOCKED`** — see below

Set a lock timeout. An unbounded `FOR UPDATE` wait is the same unbounded-quantity bug as a missing
HTTP timeout.

## SKIP LOCKED and the queue pattern

**This is the primitive underneath every Postgres-backed job queue**, and it deserves to be named as
such rather than buried in a lock-mode table.

```sql
WITH claimed AS (
  SELECT id FROM jobs
  WHERE status = 'pending' AND run_at <= now()
  ORDER BY run_at
  FOR UPDATE SKIP LOCKED
  LIMIT 10
)
UPDATE jobs SET status = 'running', started_at = now(), worker = $1
FROM claimed WHERE jobs.id = claimed.id
RETURNING jobs.*;
```

Each worker claims rows nobody else holds, with **no coordination, no leader, and no external
broker**. Workers never block on each other; they simply skip past what is taken.

Pair it with a partial index on the claim predicate:

```sql
CREATE INDEX CONCURRENTLY ON jobs (run_at) WHERE status = 'pending';
```

For very hot queues, order by a randomised or bucketed key so all workers do not contend on the same
head rows.

## Advisory locks

The documented escape hatch for coordination that does not fit MVCC:

> Locks that have application-defined meanings... the system does not enforce their use — it is up to
> the application to use them correctly.

Properties that matter:

- **Faster than a table-based flag, and no table bloat** — this is the direct argument against the
  `locked_at` column everyone writes instead
- **Session-scoped** (held until released or the session ends) or **transaction-scoped** (released at
  transaction end)
- Automatically cleaned up at session end — no stale-lock recovery to write
- Visible in `pg_locks`
- Multiple acquisitions require matching releases

```sql
SELECT pg_try_advisory_xact_lock(hashtext('nightly-rollup'));
-- true: you hold it for this transaction. false: someone else does; do nothing.
```

**This is the right answer to "only one worker should run X".** The common alternative — a `locks`
table with a `locked_at` column — needs its own expiry logic, its own cleanup for crashed holders,
and bloats under churn. Advisory locks need none of that.

**One caveat that matters:** session-level advisory locks are **incompatible with transaction-mode
pooling** — see below. Transaction-scoped advisory locks are fine.

## Deadlocks

PostgreSQL detects them automatically and resolves them by **aborting one of the transactions**,
letting the others proceed.

> The best defense against deadlocks is generally to avoid them by being certain that all
> applications using a database acquire locks on multiple objects in a **consistent order**.

Three rules:

1. **Consistent ordering.** If two code paths lock `accounts` and `ledger`, both must lock them in
   the same order. Sorting IDs before locking a set of rows is the cheap version of this.
2. **Take the most restrictive lock you will need up front**, rather than upgrading a shared lock to
   exclusive mid-transaction — upgrades are a classic deadlock source.
3. **Retry on deadlock.** The abort is the engine's designed signal that a retry should succeed.
   Treating a deadlock error as fatal is the most common mishandling.

## Connection pooling

| Mode | Server released | Notes |
|---|---|---|
| **Session** (default) | When the client disconnects | Safest, least efficient |
| **Transaction** | At COMMIT/ROLLBACK | The common production choice — **breaks session state** |
| **Statement** | After each query | *"Transactions spanning multiple statements are disallowed in this mode"* |

**Sizing.** `max_client_conn` is a global cap on client connections; `default_pool_size` is per
user/database pair. The file-descriptor ceiling is approximately
`max_client_conn + (pool_size × databases × users)`.

**Bulkhead your pools.** Separate pools for interactive traffic, background jobs, and reporting. A
single shared pool means one slow analytical query starves the request path — and for most
applications, **the pool is the thing that actually fails under load**, more often than any
individual dependency.

## What transaction-mode pooling breaks

The upstream documentation is candid that it does not enumerate this:

> Clients must not use any session-based features, since each transaction ends up in a different
> connection and thus gets a different session state.

and notes that features are *"implied incompatible but not explicitly enumerated"*. That gap is worth
closing, so:

| Feature | Why it breaks |
|---|---|
| **Session-level advisory locks** | Acquired on one server connection, released on a different one — or never |
| **`LISTEN` / `NOTIFY`** | The listening connection is handed to another client |
| **`WITH HOLD` cursors** | Outlive their transaction, but the connection does not |
| **Temporary tables** | Created on one connection, invisible from the next |
| **Session `SET` outside a transaction** | **Leaks to other clients** unless reset is forced |
| **Prepared statements** | Need `max_prepared_statements` so the pooler tracks and rewrites them |
| **`SET ROLE` / `SET SESSION AUTHORIZATION`** | Same leak, with a security consequence |
| **Sequence `currval()`** | Session-scoped state |

**The `SET` leak is the dangerous one**, because it is silent and cross-tenant: a client sets
`search_path`, `statement_timeout` or `role`, the connection returns to the pool, and the next client
inherits it. `server_reset_query` (default `DISCARD ALL`) **is not used in transaction mode at all**,
precisely because you are not supposed to need it. `server_reset_query_always` forces it back on, and
exists for *"broken setups that run applications that use session features over a transaction-pooled
pooler"* — which is an accurate description of what you are doing if you need it.

**Use `SET LOCAL` inside an explicit transaction** where you need a per-operation setting. It is
scoped to the transaction and therefore safe under transaction pooling.
