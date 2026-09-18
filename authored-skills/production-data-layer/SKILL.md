---
name: production-data-layer
description: Designs database schemas, migrations, transactions and background work that survive production rather than only demo scale — constraints that actually hold including the NULL semantics that fail silently, index design that matches how the planner works, the three safe shapes every risky migration reduces to, transaction boundaries that do not span the outside world, connection pooling that does not break session state, and observability with a bounded cardinality budget. Use when designing a schema, writing a migration, adding an index, choosing a transaction boundary, adding a background job or cache, or when a migration locked a table, duplicate rows appeared, a job ran twice, connections ran out, or something is fast locally and slow in production.
allowed-tools: Read, Write, Edit, Glob, Grep, Bash
---

# Production data layer

Backends that work at demo scale and break in production fail in a consistent way: **every one of
these bugs is invisible at 100 rows and unrecoverable at 100 million.** A missing `NOT NULL` does
not throw — it admits a null that a `CHECK` constraint then silently passes. A non-concurrent
`CREATE INDEX` is instant on a test table and a multi-minute write outage on a live one.

**Engine note.** The lock matrix, `NOT VALID`, `CONCURRENTLY` and `NULLS NOT DISTINCT` below are
**PostgreSQL** semantics. MySQL differs materially and is flagged where it appears. Every section
that depends on the engine says which one it means.

## 1. Constraints that actually hold

Start here, because these three fail **silently**. Nothing raises; the data is just wrong.

### CHECK passes on null

> A check constraint is satisfied if the check expression evaluates to true **or the null value**.

If any operand is null, most expressions evaluate to null and **the constraint passes**.

```sql
-- does NOT prevent a null price
price numeric CHECK (price > 0)

-- does
price numeric NOT NULL CHECK (price > 0)
```

Explicit `NOT NULL` is also **more efficient** than `CHECK (col IS NOT NULL)`.

### UNIQUE treats nulls as distinct

> Even in the presence of a unique constraint it is possible to store duplicate rows that contain a
> null value.

```sql
-- (tenant_id, email) with a nullable tenant_id: unlimited duplicates where tenant_id IS NULL
UNIQUE (tenant_id, email)

-- treats nulls as equal
UNIQUE NULLS NOT DISTINCT (tenant_id, email)
```

The default is **implementation-defined in the SQL standard** and differs between engines, so this
is a portability trap as well as a correctness one. **State the decision explicitly** on every
unique constraint over a nullable column.

### Foreign keys default to MATCH SIMPLE

A referencing row escapes the constraint if **any** of its columns is null. With a composite foreign
key, one null disables the whole check. `MATCH FULL` requires *all* of them to be null, so a mix of
null and non-null is guaranteed to fail — which is usually what you meant.

### And the fourth: a foreign key does not index the referencing column

The referenced side is indexed because it must be a primary key or unique. **The referencing side is
not.** Every `DELETE` or `UPDATE` of a referenced row scans for matching rows. Add the index.

### ON DELETE is a modelling decision

> When the referencing table represents something that is a component of what is represented by the
> referenced table and cannot exist independently, then CASCADE could be appropriate. If the two
> tables represent independent objects, then RESTRICT or NO ACTION is more appropriate.

`RESTRICT` additionally forbids deferred checking; `NO ACTION` permits it. Default to `NO ACTION`
and reach for `CASCADE` only for genuine components — order lines, not orders.

## 2. Indexes

**The multicolumn ordering rule**, which decides whether your index is used at all:

> Equality constraints on leading columns, plus any inequality constraints on the first column that
> does not have an equality constraint, will always be used to limit the portion of the index that is
> scanned.

Everything after that point **filters but does not narrow the scan**.

```sql
CREATE INDEX ON t (x, y, z);
SELECT ... WHERE x = 5 AND y >= 42 AND z < 77;
```

The scan runs from the first `x=5, y=42` entry to the last `x=5` entry. `z` is applied afterwards as
a filter. **Lead with equality columns; put the most selective first.**

**Index-only scans need more than the right columns.**

> An index-only scan will be a win only if a significant fraction of the table's heap pages have
> their all-visible map bits set.

So covering indexes pay off on static or slowly-changing tables and quietly do not on hot ones.
`INCLUDE (y)` adds a payload column outside the search key and outside uniqueness — useful precisely
because *"if the heap tuple must be visited anyway, it costs nothing more to get the column's value
from there."*

**Partial indexes** pay off for excluding common values (a query for a common value will not use the
index anyway), excluding rows you never query, and **enforcing uniqueness on a subset**. But: **do
not use many non-overlapping partial indexes as a substitute for partitioning** — the planner must
test each one.

**An unused index is worse than idle.** Indexes *prevent the creation of heap-only tuples*, so they
add write cost even when no query touches them. Remove seldom-used ones.

**Non-unique indexes with more than three columns rarely help.** Lead with the column that narrows
the most.

**Testing discipline**, in order: run `ANALYZE` first — default statistics are *"almost certain to be
inaccurate"*; use realistic data, because selecting 1 of 100 rows fits on one page and will never use
an index; force with `enable_seqscan = off` to test viability, and if the planner still refuses,
there is a more fundamental reason; then time with `EXPLAIN ANALYZE`.

## 3. The three safe shapes

Migration guides list dozens of unsafe operations. **They reduce to three shapes.** Learn the
shapes and the next case is derivable.

### Shape 1 — expand and contract

For: type changes, renaming a column, table or schema, adding an auto-increment column, renaming an
enum value.

```
1. create the new thing
2. write to BOTH                    ← deploy
3. backfill, batched and throttled
4. migrate reads to the new thing   ← deploy
5. stop writing the old thing       ← deploy
6. drop the old thing
```

Six steps and several deploys. **There is no shortcut** — a single `ALTER` that renames a column in
use breaks every running instance of the old code.

### Shape 2 — NOT VALID, then VALIDATE

For: foreign keys, check constraints, **and NOT NULL**.

PostgreSQL states the purpose itself:

> The main purpose of the NOT VALID constraint option is to reduce the impact of adding a constraint
> on concurrent updates. With NOT VALID, the ADD CONSTRAINT command does not scan the table and can
> be committed immediately. After that, a VALIDATE CONSTRAINT command can be issued.

The constraint applies to **new** rows immediately; validation of existing rows runs later under only
`SHARE UPDATE EXCLUSIVE`, which does not block writes.

`NOT NULL` needs the indirect route, because `SET NOT NULL` itself scans:

```sql
ALTER TABLE t ADD CONSTRAINT t_col_nn CHECK (col IS NOT NULL) NOT VALID;
-- deploy
ALTER TABLE t VALIDATE CONSTRAINT t_col_nn;
ALTER TABLE t ALTER COLUMN col SET NOT NULL;   -- now cheap: the check proves it
ALTER TABLE t DROP CONSTRAINT t_col_nn;
```

**No safe form exists** for exclusion constraints — they cannot be marked `NOT VALID`.

### Shape 3 — concurrently, outside a DDL transaction

For: **every** index.

```sql
-- must not run inside a transaction block
CREATE INDEX CONCURRENTLY idx ON t (col);
```

Including the index hiding inside `add_reference`, and the one hiding inside a unique constraint:

```sql
CREATE UNIQUE INDEX CONCURRENTLY idx ON t (col);
ALTER TABLE t ADD CONSTRAINT c UNIQUE USING INDEX idx;
```

## 4. Migrations against live traffic

**Rewrite, scan, or neither** — this decides deployability.

| Operation | Cost |
|---|---|
| Change a column's type | **Full rewrite** (unless binary-coercible via `USING` with no collation change) |
| Add a column with a **volatile** DEFAULT (`gen_random_uuid()`, `clock_timestamp()`) | **Full rewrite** |
| Add a stored generated column, identity column, or constrained domain type | **Full rewrite** |
| Add a CHECK or NOT NULL constraint | **Scan only** |
| Add a column with a **non-volatile** DEFAULT | **Neither** — evaluated once, stored in metadata |

That last row is the one worth internalising: adding a column with a constant default is fast even on
a huge table. Adding one with `gen_random_uuid()` rewrites it. Same statement shape, opposite cost.
The fix is to add the column, then `change_column_default`, then backfill.

**The lock matrix**, which is what actually decides whether a statement is safe:

| Mode | Taken by | Notable conflict |
|---|---|---|
| ACCESS SHARE | SELECT | ACCESS EXCLUSIVE only |
| ROW EXCLUSIVE | INSERT/UPDATE/DELETE | SHARE and above |
| SHARE UPDATE EXCLUSIVE | VACUUM, ANALYZE, **CREATE INDEX CONCURRENTLY**, VALIDATE CONSTRAINT | self, SHARE and above |
| SHARE | **CREATE INDEX** (non-concurrent) | ROW EXCLUSIVE → **blocks writes** |
| SHARE ROW EXCLUSIVE | CREATE TRIGGER, **ADD FOREIGN KEY** | self-exclusive |
| ACCESS EXCLUSIVE | DROP, TRUNCATE, most ALTER TABLE, ADD COLUMN, ALTER TYPE | **everything** |

**`ADD FOREIGN KEY` takes only SHARE ROW EXCLUSIVE** — weaker than most people assume, on both
tables.

**Dropping a column is unsafe for a reason that is not about locks:** the ORM caches the column list,
so running code queries a column that no longer exists. Ignore the column in code, deploy, *then*
drop.

**`json` has no equality operator**, which breaks existing `SELECT DISTINCT`. Use `jsonb`.

**Backfills.** Backfilling in the same transaction as the `ALTER` **holds the lock for the whole
backfill**. Batch (10,000 rows is a reasonable start) and throttle with a short sleep between
batches.

## 5. CONCURRENTLY, and the INVALID index

This is the most likely thing to go wrong in a migration and the least likely to be planned for.

The algorithm: **two table scans across three transactions**, waiting between them for existing
modifying transactions to finish. It *"requires more total work than a standard index build and takes
significantly longer."*

**On failure — deadlock, or a uniqueness violation — the command fails and leaves an INVALID index
behind.** That index:

- is **not used for queries**
- **still carries write overhead on every insert and update**

Detect it with `\d` in psql, where it shows as `INVALID`. Recover by dropping and retrying, or with
`REINDEX INDEX CONCURRENTLY`.

**Plan for it.** A migration that runs `CREATE INDEX CONCURRENTLY` and does not check the result
afterwards can leave a table permanently slower with no error anywhere.

Restrictions: cannot run inside a transaction block; only one concurrent build per table at a time;
**not supported on partitioned tables** — build each partition individually. And for unique indexes,
the constraint is **already enforced against other transactions from the second scan**, so violations
can surface before the index is ready, or even if the build ultimately fails.

## 6. Three sets of timeouts, pointing different ways

| Where | Lock timeout | Statement timeout | Why |
|---|---|---|---|
| **Migration** | 10s | 1 hour | May run long; must never *wait* long |
| **Application** | 10s | 15s | Must never do either |
| **Pooler** | `query_wait_timeout` 120s default | — | Turns pool exhaustion into a visible error instead of a hang |

**The asymmetry is the point.** A migration is allowed to take an hour of work, but if it cannot get
its lock in ten seconds it must give up — otherwise it sits at the head of the lock queue and
**every query behind it blocks**, which is how a "safe" migration takes the site down.

Set the migration timeouts before the first risky migration, not after.

## 7. Transaction boundaries

**Nested blocks are savepoints, not transactions.** An inner block that completes successfully can
still be rolled back by an exception in the outer block. Use a "must be outermost" assertion where
that matters.

**Do not catch exceptions inside an atomic block.** After a database error the transaction is
broken, and any query issued before the rollback raises. Wrap the atomic block in try/except, not the
reverse.

**A rollback does not revert in-memory state.** Model objects keep the values you assigned. Restore
them by hand or re-read.

**Transaction-per-request is a scaling trap.** Frameworks offering it warn that it becomes
inefficient as traffic grows — and middleware and template rendering run *outside* the boundary
anyway, so it does not even give you what it appears to.

### The one that matters most: side effects

**Never do non-database work inside a transaction** — no emails, no HTTP calls, no job enqueues, no
cache writes. The transaction cannot span the database and the outside world.

That leaves exactly two options, and you must pick consciously:

| | How it works | Failure mode |
|---|---|---|
| **After-commit callback** | Fires once the commit succeeds | **Lossy.** A failure in the callback rolls nothing back. The row is committed; the email never sends |
| **Outbox** | Write an outbox row **inside** the same transaction; a separate process delivers it | Not lossy. Costs a table and a worker |

There is no third option. **After-commit callbacks are the lossy one**, and most code reaches for
them without noticing that is the trade being made. For an email confirmation, lossy is usually
fine. For "charge the card and grant access", it is not.

## 8. Concurrent writes

**Optimistic** — a version column in the `UPDATE`'s `WHERE` clause. A mismatch affects zero rows and
raises. **The application must catch it and decide whether to retry**; the framework will not.

Choose optimistic on the **right axis**: it fits *read-often, write-sometimes*, and especially **long
conversations spanning several database transactions** — a user editing a form across minutes. The
argument is conversation *length*, not contention rate.

Useful modes beyond the basic one:

- **force-increment** — bump the version even with no field change. This is the mechanism for "a
  child row changed, so the aggregate root is now stale."
- **versionless / dirty** — put only the changed fields in the `WHERE` clause, which minimises false
  conflicts between non-overlapping edits.

**Pessimistic** — `SELECT ... FOR UPDATE`. Two modifiers worth knowing:

- **`NOWAIT`** — fail immediately if the row is locked
- **`SKIP LOCKED`** — **skip locked rows entirely.** This is the primitive underneath every
  Postgres-backed job queue: each worker claims rows nobody else holds, with no coordination.

**Advisory locks** are the documented escape hatch for coordination that does not fit MVCC:
application-defined meaning, not system-enforced, **faster than a table-based flag and without the
table bloat**, session- or transaction-scoped, visible in `pg_locks`. This is the right answer to
"only one worker should do X" — consistently passed over in favour of a `locked_at` column that
bloats the table and needs its own cleanup.

**Deadlocks:** PostgreSQL detects them and aborts one transaction. *"The best defense against
deadlocks is generally to avoid them by being certain that all applications using a database acquire
locks on multiple objects in a consistent order."* Take the most restrictive lock you will need up
front, and retry on detection — the abort is the engine telling you to.

## 9. Connection pooling

| Mode | Server released | Cost |
|---|---|---|
| **Session** (default) | When the client disconnects | Least efficient, fully compatible |
| **Transaction** | At COMMIT/ROLLBACK | Efficient — **breaks session state** |
| **Statement** | Per query | **Multi-statement transactions disallowed outright** |

**Transaction pooling is the trap.** Clients *"must not use any session-based features, since each
transaction ends up in a different connection and thus gets a different session state."* `SET` and
`RESET` **leak to other clients**. And `server_reset_query` (default `DISCARD ALL`) **is not used in
transaction mode at all** — precisely because you are not supposed to need it.

**What transaction mode breaks.** The upstream docs say these are *"implied incompatible but not
explicitly enumerated"*, which is a real documentation gap. Enumerated:

- **Session-level advisory locks** — a different connection holds them
- **`LISTEN` / `NOTIFY`**
- **`WITH HOLD` cursors**
- **Temporary tables**
- **Session `SET` / `SET LOCAL` outside a transaction**
- **Prepared statements** — need `max_prepared_statements`, which makes the pooler track and rewrite
  them

**Sizing.** `max_client_conn` is global; `default_pool_size` is per user/database pair. File
descriptor ceiling ≈ `max_client_conn + (pool_size × databases × users)`.

**Bulkhead your pools.** One pool per dependency class, so a slow report query cannot consume the
connections serving interactive traffic.

## 10. Background jobs

> **No queue gives you exactly-once delivery. Even completed jobs can re-run if the acknowledgement
> fails.**

Everything else follows from that.

- **Jobs must be idempotent by construction**, not by luck. Derive a stable key per work item and
  check before acting.
- **Pass identifiers, not objects.** *"Don't save state in the queue, save simple identifiers."* The
  object may be stale by the time the job runs, and serialised objects break across deploys.
- Arguments must be JSON-safe: strings, numbers, booleans, null, arrays, maps. No symbols, no
  date/time objects, no language-specific types.
- Keep jobs small. Design for parallelism without resource locking.
- Claim work with **`SELECT ... FOR UPDATE SKIP LOCKED`** if you are building on Postgres.
- Wrap database changes in a transaction, **or** make the job resilient to partial execution.

**Evidence limit, stated plainly.** The sourcing for this section is thinner than the rest of this
skill. **Not covered here because it was not read at the source:** transactional enqueue and the
outbox pattern's operational details, deduplication and uniqueness keys, retry and backoff policy,
dead-letter handling, visibility timeouts and crash recovery. For retries, backoff and dead-lettering
specifically, use the `resilience-patterns` skill, which sourced them properly.

## 11. Caching

The one primary source here carries the sharpest distinction available, and it is the right frame
for cache stampedes:

> **Expiry forces retrievals to block and wait for a new value. Refresh loads asynchronously in the
> background and returns the stale value to concurrent readers.**

And the subtlety: *"a refresh will only be actually initiated when the entry is queried"* — so an
unused key simply expires rather than triggering an expensive recomputation. On failure the old value
is kept and the exception is logged and swallowed, preferring availability over strict consistency.

**Expire-on-write versus refresh-on-write is the decision**, and most stampede problems are really
"we chose expiry where we wanted refresh."

**Evidence limit.** Beyond that contrast, the stampede material available was secondary and is not
reproduced here. The techniques that exist and are worth investigating properly — **single-flight via
a distributed lock, probabilistic early expiration, request coalescing, jittered TTLs, event-driven
invalidation** — are named so you know what to look for, **not described, because they were not read
at the source.** Jittered TTLs specifically are covered from a primary source in
`resilience-patterns`, under desynchronisation.

## 12. Observing it

**Instrument choice is a decision tree, not a preference:**

| Shape | Instrument |
|---|---|
| Monotonically increasing count | **Counter** |
| Can go up or down (queue depth) | **UpDownCounter** |
| Timing, or a distribution you want percentiles from | **Histogram** |
| An absolute reading, non-additive | Asynchronous Gauge |

**Cardinality is a hard budget.** The canonical worked example: **7 attributes × 30 values each ⇒
21,870,000,000 combinations** the SDK might have to remember. High-cardinality attributes — user IDs,
raw URLs, error messages — cause unbounded memory growth. **The default limit is 2,000 unique
attribute combinations per metric stream**; past it, data is dropped or combined.

Never put a user ID, a full URL path with IDs in it, or an exception message in a metric label.
Those belong on spans and logs.

**Alert on symptoms.**

> Alert on symptoms, have good consoles to allow pinpointing causes, and avoid having pages where
> there is nothing to do.

- Page on **latency at one point** in the stack, not at several
- Alert on **user-visible errors**; suppress downstream failures unless they independently need
  intervention
- For batch jobs, page when the job *"has not succeeded recently enough"* to affect users — allow at
  least **two cycles** of buffer (10 hours for a 4-hour job)
- **Metamonitor**: test the alerting pipeline end to end, not component health

## Review checklist

- [ ] Explicit `NOT NULL` rather than relying on a CHECK
- [ ] Unique constraints over nullable columns state a NULLS decision
- [ ] Foreign keys have an index on the referencing column
- [ ] Index column order leads with equality predicates
- [ ] Every index migration is concurrent and outside a DDL transaction
- [ ] Constraints on large tables use NOT VALID then VALIDATE
- [ ] Renames and type changes use expand–contract, not a single ALTER
- [ ] Backfills are batched and throttled, outside the ALTER's transaction
- [ ] Migration and application timeouts are both set, and differ in the right direction
- [ ] No email, HTTP call or enqueue inside a transaction; after-commit vs outbox chosen consciously
- [ ] Background jobs are idempotent and take identifiers
- [ ] Transaction-mode pooling was checked against the incompatibility list
- [ ] No unbounded label values on metrics; alerts are on symptoms

## References

- `references/migrations.md` — the three shapes worked through, the rewrite/scan table, the lock
  matrix, INVALID-index recovery, the three timeout sets
- `references/constraints-and-indexes.md` — the NULL gotchas with reproductions, index design and
  the testing discipline
- `references/concurrency.md` — transaction boundaries, after-commit vs outbox, locking modes,
  advisory locks, SKIP LOCKED, pool modes and the full incompatibility list
- `references/observability.md` — instrument choice, the cardinality budget, a default metric set,
  symptom-based alerting
