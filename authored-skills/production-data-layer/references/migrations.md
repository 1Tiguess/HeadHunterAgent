# Migrations against live traffic

PostgreSQL unless stated. MySQL notes are marked and are second-hand.

## Contents
- [The three shapes](#the-three-shapes)
- [Rewrite, scan, or neither](#rewrite-scan-or-neither)
- [The lock conflict matrix](#the-lock-conflict-matrix)
- [CONCURRENTLY and the INVALID index](#concurrently-and-the-invalid-index)
- [Backfills](#backfills)
- [The three timeout sets](#the-three-timeout-sets)
- [Operation to shape, as a lookup](#operation-to-shape-as-a-lookup)
- [A pre-flight checklist](#a-pre-flight-checklist)

## The three shapes

Every risky migration reduces to one of these. Learn the shapes and the case not listed below is
derivable.

### Shape 1 — expand and contract

```
1. create the new thing                      (migration)
2. write to BOTH old and new                 (deploy)
3. backfill, batched and throttled           (migration)
4. read from the new thing                   (deploy)
5. stop writing the old thing                (deploy)
6. drop the old thing                        (migration)
```

**Three deploys minimum**, because at every moment both the old and new code must work against the
current schema. That constraint is what forces the shape: during a rolling deploy, instances running
both versions hit the same database.

Worth stating because it is the most common objection: **there is no shortcut.** A single `ALTER
TABLE ... RENAME COLUMN` on a column in use breaks every instance still running the old code, for as
long as the rollout takes.

### Shape 2 — NOT VALID, then VALIDATE

```sql
ALTER TABLE orders
  ADD CONSTRAINT orders_customer_fk
  FOREIGN KEY (customer_id) REFERENCES customers(id)
  NOT VALID;                               -- immediate, no scan

-- deploy, let it soak

ALTER TABLE orders VALIDATE CONSTRAINT orders_customer_fk;
                                           -- SHARE UPDATE EXCLUSIVE, does not block writes
```

PostgreSQL's own statement of purpose:

> The main purpose of the NOT VALID constraint option is to reduce the impact of adding a constraint
> on concurrent updates. With NOT VALID, the ADD CONSTRAINT command does not scan the table and can
> be committed immediately.

The constraint is enforced against **new** rows from the moment it is added. Validation only checks
the rows that were already there.

**`NOT NULL` via the indirect route**, because `SET NOT NULL` scans:

```sql
ALTER TABLE t ADD CONSTRAINT t_col_nn CHECK (col IS NOT NULL) NOT VALID;
-- deploy
ALTER TABLE t VALIDATE CONSTRAINT t_col_nn;
ALTER TABLE t ALTER COLUMN t.col SET NOT NULL;  -- cheap: the validated check proves it
ALTER TABLE t DROP CONSTRAINT t_col_nn;
```

Before validating, you must make the data true — backfill the nulls, and make sure application code
has stopped writing them. `VALIDATE` on data that violates the constraint fails, and you are back
where you started.

**No safe form exists** for exclusion constraints; they cannot be marked `NOT VALID`.

*MySQL/MariaDB: adding a check constraint has no documented safe method. (Second-hand.)*

### Shape 3 — concurrently, outside a DDL transaction

```sql
-- NOT inside a transaction block
CREATE INDEX CONCURRENTLY idx_orders_customer ON orders (customer_id);
```

In a migration framework this needs whatever disables the wrapping transaction —
`disable_ddl_transaction!` or equivalent. Without it the migration errors out, which is at least a
loud failure.

The two hidden cases:

```sql
-- a "reference" or "belongs_to" helper usually creates a NON-concurrent index. Force it.

-- a unique CONSTRAINT creates a blocking unique INDEX. Split it:
CREATE UNIQUE INDEX CONCURRENTLY idx_users_email ON users (email);
ALTER TABLE users ADD CONSTRAINT users_email_key UNIQUE USING INDEX idx_users_email;
```

## Rewrite, scan, or neither

This is what decides whether a statement is deployable.

| Operation | Cost | Note |
|---|---|---|
| `ALTER COLUMN ... TYPE` | **Full rewrite** | Exception: binary-coercible via `USING` with no collation change |
| Add column, **volatile** DEFAULT | **Full rewrite** | `gen_random_uuid()`, `clock_timestamp()`, `now()` in some forms |
| Add stored generated column | **Full rewrite** | |
| Add identity column | **Full rewrite** | |
| Add column of a constrained domain type | **Full rewrite** | |
| Add CHECK constraint | **Scan** | Avoid with `NOT VALID` |
| Add NOT NULL | **Scan** | Avoid with the check-constraint route |
| Add column, **non-volatile** DEFAULT | **Neither** | *"the default value is evaluated at the time of the statement and the result stored in the table's metadata"* |
| `ADD FOREIGN KEY` | Scan both tables | Avoid with `NOT VALID`. Takes only SHARE ROW EXCLUSIVE |
| `DROP COLUMN` | Metadata only | But see the ORM hazard below |

**The volatile/non-volatile split is the one to internalise.** `ADD COLUMN status text DEFAULT
'pending'` is instant on a billion rows. `ADD COLUMN id uuid DEFAULT gen_random_uuid()` rewrites the
whole table. Same statement shape, opposite cost.

The fix for the volatile case:

```sql
ALTER TABLE t ADD COLUMN external_id uuid;                          -- instant
ALTER TABLE t ALTER COLUMN external_id SET DEFAULT gen_random_uuid(); -- instant, applies to new rows
-- then backfill existing rows in batches
```

**The ORM hazard on DROP COLUMN.** The column list is cached at process start, so running code
selects a column that no longer exists and raises until restart. Ignore the column in application
code, deploy, *then* drop it.

**`json` versus `jsonb`.** `json` has no equality operator, which breaks any existing `SELECT
DISTINCT` over the table. Use `jsonb`.

## The lock conflict matrix

| Mode | Acquired by | Conflicts with |
|---|---|---|
| ACCESS SHARE | `SELECT`, any read | ACCESS EXCLUSIVE only |
| ROW SHARE | `SELECT ... FOR UPDATE/SHARE` | EXCLUSIVE, ACCESS EXCLUSIVE |
| ROW EXCLUSIVE | `INSERT`, `UPDATE`, `DELETE`, `MERGE` | SHARE and above |
| SHARE UPDATE EXCLUSIVE | `VACUUM` (no FULL), `ANALYZE`, **`CREATE INDEX CONCURRENTLY`**, `REINDEX CONCURRENTLY`, `VALIDATE CONSTRAINT`, `ATTACH PARTITION`, `SET STATISTICS` | self, SHARE and above |
| SHARE | **`CREATE INDEX`** (non-concurrent) | ROW EXCLUSIVE → **blocks all writes** |
| SHARE ROW EXCLUSIVE | `CREATE TRIGGER`, **`ADD FOREIGN KEY`** | self-exclusive, ROW EXCLUSIVE and above |
| EXCLUSIVE | `REFRESH MATERIALIZED VIEW CONCURRENTLY` | everything except ACCESS SHARE |
| ACCESS EXCLUSIVE | `DROP`, `TRUNCATE`, `REINDEX`, `CLUSTER`, `VACUUM FULL`, most `ALTER TABLE` | **everything** |

**Read this as: what will my statement block?** `CREATE INDEX` without `CONCURRENTLY` takes SHARE,
which conflicts with ROW EXCLUSIVE — so it blocks every insert, update and delete for the duration.
Reads continue, which is why it looks fine in a staging environment with no writes.

**The lock queue is the thing that surprises people.** A statement waiting for ACCESS EXCLUSIVE sits
at the head of the queue, and **everything arriving after it also waits** — including plain
`SELECT`s that would not have conflicted with the running transaction. One long-running query plus
one `ALTER TABLE` equals a full outage on that table. This is the entire reason for a short
`lock_timeout`.

## CONCURRENTLY and the INVALID index

**The algorithm.** Two table scans across three transactions:

1. Mark the index "invalid" in the catalogs — transaction 1
2. First scan — transaction 2
3. Second scan — transaction 3
4. Mark valid

Between scans it **waits for existing transactions that have modified the table to terminate**.
After the second scan it waits for transactions predating that scan. So **a single long-running
transaction anywhere can stall the build indefinitely** — check `pg_stat_activity` before starting.

It *"requires more total work than a standard index build and takes significantly longer."*

**The failure mode.** On a deadlock or a uniqueness violation, the command fails and **leaves an
invalid index behind**:

- not used for queries
- **still carries update overhead on every write**

So the table is now permanently slower, with no error visible anywhere except in the migration log
that already scrolled past.

**Detect:**

```sql
SELECT c.relname, i.indisvalid
FROM pg_class c JOIN pg_index i ON i.indexrelid = c.oid
WHERE NOT i.indisvalid;
```

Or `\d tablename` in psql, where it prints `INVALID`.

**Recover:** `DROP INDEX CONCURRENTLY <name>` and retry, or `REINDEX INDEX CONCURRENTLY <name>`.

**Always check after a concurrent build.** A migration that fires and forgets is how the invalid
index survives.

**Restrictions:**

- Cannot run inside a transaction block
- **One concurrent build per table at a time** (multiple *regular* builds can run simultaneously)
- Schema modifications prohibited during the build
- **Not supported on partitioned tables** — build each partition individually
- For unique indexes: the constraint is **enforced against other transactions from the second scan**,
  so violations can surface before the index is ready, **or even if the build ultimately fails**

## Backfills

**Never backfill in the same transaction as the ALTER.** It *"keeps the table locked for the duration
of the backfill"* — so a five-minute backfill is a five-minute write outage, regardless of how cheap
the ALTER was.

```python
# batched and throttled, outside the DDL transaction
BATCH = 10_000
while True:
    n = execute("""
        UPDATE t SET col = 'value'
        WHERE id IN (SELECT id FROM t WHERE col IS NULL LIMIT %s)
    """, BATCH)
    if n == 0:
        break
    sleep(0.01)          # throttle: let replication and vacuum keep up
```

The sleep matters more than the batch size. Without it, a tight loop of 10,000-row updates generates
WAL faster than replicas can apply it, and replica lag becomes the outage instead.

Batch by **primary key range** rather than `LIMIT` on a filtered scan where the table is large — the
filtered scan gets slower each iteration as the matching rows thin out.

## The three timeout sets

| Context | `lock_timeout` | `statement_timeout` | Rationale |
|---|---|---|---|
| **Migration** | 10s | 1 hour | May legitimately run long; **must never wait long**, because waiting blocks the queue behind it |
| **Application** | 10s | 15s | Must never do either |
| **Pooler** | — | `query_wait_timeout` 120s | Disconnects a client that never gets a server — turns pool exhaustion into a visible error instead of a hang |

The upstream guidance for the migration pair:

> If a migration can't acquire a lock in a timely manner, other statements won't be stuck behind it.

Pooler timeouts are filed by their own documentation under **"Dangerous timeouts"**, with warnings
about unexpected errors from aggressive enforcement: `idle_transaction_timeout` (disabled by
default), `query_wait_timeout` (120s default), `transaction_timeout` (disabled by default).

*MySQL equivalents (second-hand): `max_execution_time` in ms, `lock_wait_timeout` in seconds;
MariaDB uses `max_statement_time` in seconds.*

## Operation to shape, as a lookup

| I want to... | Shape |
|---|---|
| Add an index | 3 |
| Add a unique constraint | 3, then `ADD CONSTRAINT ... USING INDEX` |
| Add a foreign key | 2 |
| Add a check constraint | 2 |
| Make a column NOT NULL | 2, via a check constraint |
| Change a column's type | 1 |
| Rename a column, table or schema | 1 |
| Add an auto-increment column | 1 |
| Rename an enum value | 1 (add the new value, dual-write, backfill; the old value cannot be removed) |
| Add a column with a constant default | None — it is already safe |
| Add a column with a volatile default | Add the column, then set the default, then backfill |
| Drop a column | Ignore in code → deploy → drop |
| Add an exclusion constraint | **No safe shape.** Needs a maintenance window |

## A pre-flight checklist

- [ ] Which shape is this?
- [ ] Rewrite, scan, or neither?
- [ ] What lock does it take, and what does that block?
- [ ] Are `lock_timeout` and `statement_timeout` set for migrations?
- [ ] Any long-running transactions open right now? (`pg_stat_activity`)
- [ ] If it builds an index concurrently — is there a check for an invalid index afterwards?
- [ ] If it backfills — batched, throttled, and outside the ALTER's transaction?
- [ ] If it is expand–contract — are all the deploys planned, in order?
- [ ] Is it reversible, and has the reverse been thought through at production size?
