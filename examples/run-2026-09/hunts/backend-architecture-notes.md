# Hunt notes — backend architecture

**Gap.** Claude writes backends that work at demo scale and break in production:
schemas without the constraints that keep data true, transaction boundaries drawn
around whatever the ORM happened to do, migrations that lock a live table,
caching with no invalidation story, and background jobs that assume they run
exactly once.

## Provenance — read this first

**This scout was killed by the session rate limit before it wrote its report.**
These notes are reconstructed by me from the 29 tool results still present in its
transcript, which I read directly from disk. Twenty-two fetches succeeded; six
404'd on branch or path changes (`indexes.sgml` → `indices.sgml`, River's README
on `main` not `master`, three OTel semantic-convention paths, one Prometheus
path); two were `WebSearch`.

**What this means for coverage.** Schema constraints, indexing, locking,
migrations, transactions, connection pooling and observability are **well
sourced from primary text**. **Job queues and caching are thin** — Graphile
Worker's README returned only a project overview, River's README was never
reached, Sidekiq's Best Practices wiki is short, and the caching material is
largely a `WebSearch` that returned listicles. The scout's last recorded words
were *"The caching search returned listicles — I'll go to primary craft sources
instead"*, and it died before doing so.

**Treat job queues and caching below as incomplete.** They are enough to state
the shape of the problem, not enough to be the authoritative section of a skill.

---

## 1. Schema constraints — PostgreSQL `ddl.sgml`, fetched

**The NULL gotchas are the whole section**, and they are exactly the class of
bug that survives to production because it never throws.

- **A CHECK constraint is satisfied if the expression evaluates to true *or
  null*.** If any operand is null, most expressions evaluate to null and the
  constraint **passes silently**. To prevent nulls you must add NOT NULL
  explicitly — the check will not do it for you.
- **UNIQUE treats two nulls as distinct by default.** "Even in the presence of a
  unique constraint it is possible to store duplicate rows that contain a null
  value." `UNIQUE NULLS NOT DISTINCT` changes this. The docs warn the default is
  implementation-defined in the SQL standard and differs between engines — so
  this is also a portability trap.
- **Foreign keys use MATCH SIMPLE by default**: a referencing row escapes the
  constraint if **any** of its columns is null. `MATCH FULL` requires *all* of
  them to be null, so a mix of null and non-null is guaranteed to fail.
- **A foreign key does not index the referencing column.** The referenced side
  must already be a PK or unique, so it is indexed; the referencing side is not,
  and DELETE/UPDATE of a referenced row scans for matching rows. "It is often a
  good idea to index the referencing columns too."
- Explicit `NOT NULL` is **more efficient** than the equivalent
  `CHECK (col IS NOT NULL)`.
- ON DELETE guidance, stated as a modelling rule rather than a preference: **when
  the referencing table represents a component that cannot exist independently,
  CASCADE may be right; when the two tables represent independent objects,
  RESTRICT or NO ACTION is more appropriate.** RESTRICT additionally forbids
  deferred checking; NO ACTION permits it.

## 2. Indexing — `indices.sgml`, fetched

**The multicolumn ordering rule, stated exactly:** "equality constraints on
leading columns, plus any inequality constraints on the first column that does
not have an equality constraint, will always be used to limit the portion of the
index that is scanned." Everything after that point **filters but does not
narrow the scan**. For `(x, y, z)` and `WHERE x = 5 AND y >= 42 AND z < 77`, the
scan runs from the first `x=5, y=42` entry through the last `x=5` entry; `z` is
applied afterwards.

- **Index-only scans need the visibility map**, not just the right columns: "an
  index-only scan will be a win only if a significant fraction of the table's
  heap pages have their all-visible map bits set." So covering indexes pay off on
  static or slowly-changing tables and quietly do not on hot ones.
- `INCLUDE (y)` adds a non-key payload column — outside the search key and
  outside uniqueness. "If the heap tuple must be visited anyway, it costs nothing
  more to get the column's value from there", which is why INCLUDE is a
  static-table optimisation.
- **Partial indexes** pay off for excluding common values (a query for a common
  value won't use the index anyway), excluding uninteresting rows, and
  **enforcing uniqueness on a subset**. Caveat: **do not use many non-overlapping
  partial indexes as a substitute for partitioning** — the planner must test each
  one.
- Expression indexes recompute per insert and non-HOT update, but **not** during
  search.
- Indexes "prevent the creation of heap-only tuples", so an unused index is
  actively counterproductive, not merely idle. Seldom-used indexes should be
  removed.
- Testing discipline: **run ANALYZE first** (default statistics are "almost
  certain to be inaccurate"); use realistic data (selecting 1 of 100 rows fits on
  one page and will never use an index); force with `enable_seqscan` to test
  viability — if it still won't, there is a more fundamental reason; time with
  EXPLAIN ANALYZE.

## 3. Locking — `mvcc.sgml` and `alter_table.sgml`, fetched

The table-lock conflict matrix, which is what actually decides whether a
migration is safe:

| Mode | Taken by | Notable conflict |
|---|---|---|
| ACCESS SHARE | SELECT | ACCESS EXCLUSIVE only |
| ROW SHARE | SELECT FOR UPDATE/SHARE | EXCLUSIVE, ACCESS EXCLUSIVE |
| ROW EXCLUSIVE | INSERT/UPDATE/DELETE/MERGE | SHARE and above |
| SHARE UPDATE EXCLUSIVE | VACUUM, ANALYZE, **CREATE INDEX CONCURRENTLY**, VALIDATE CONSTRAINT | self, SHARE and above |
| SHARE | **CREATE INDEX** (non-concurrent) | ROW EXCLUSIVE → **blocks writes** |
| SHARE ROW EXCLUSIVE | CREATE TRIGGER, **ADD FOREIGN KEY** | self-exclusive |
| EXCLUSIVE | REFRESH MATVIEW CONCURRENTLY | everything but ACCESS SHARE |
| ACCESS EXCLUSIVE | DROP, TRUNCATE, most ALTER TABLE, ADD COLUMN, ALTER TYPE | **everything** |

Deadlocks: detected automatically, resolved by aborting one transaction. **"The
best defense against deadlocks is generally to avoid them by being certain that
all applications using a database acquire locks on multiple objects in a
consistent order."** Take the most restrictive lock you'll need up front; retry
on deadlock.

**Advisory locks** are the documented escape hatch for locking strategies that
don't fit MVCC — application-defined meaning, not system-enforced, **faster than
a table-based flag and without the table bloat**, session-scoped or
transaction-scoped, visible in `pg_locks`. This is the right primitive for
"only one worker should do X", and it is consistently overlooked in favour of a
`locked_at` column.

**ALTER TABLE, rewrites vs scans — the distinction that decides deployability:**

- **Rewrites the whole table:** changing a column's type (normally); adding a
  column with a **volatile** DEFAULT, a stored generated column, an identity
  column, or a constrained domain type.
- **Scans only:** adding a CHECK or NOT NULL constraint.
- **Neither:** adding a column with a **non-volatile** DEFAULT — "the default
  value is evaluated at the time of the statement and the result stored in the
  table's metadata", making it fast even on large tables.
- **ADD FOREIGN KEY takes only SHARE ROW EXCLUSIVE**, on both tables — weaker
  than most people assume.

**`NOT VALID` is the documented mechanism, in Postgres's own words:** "The main
purpose of the NOT VALID constraint option is to reduce the impact of adding a
constraint on concurrent updates. With NOT VALID, the ADD CONSTRAINT command does
not scan the table and can be committed immediately. After that, a VALIDATE
CONSTRAINT command can be issued." The constraint applies to new rows
immediately; validation of existing rows runs later under only SHARE UPDATE
EXCLUSIVE.

## 4. `CREATE INDEX CONCURRENTLY` — the failure mode nobody plans for

Fetched from `create_index.sgml`. Normal CREATE INDEX "locks out writes (but not
reads)". CONCURRENTLY allows normal operation, at a cost:

- **Two table scans across three transactions**, waiting between them for
  existing modifying transactions to finish. "Requires more total work… and takes
  significantly longer."
- **On failure it leaves an INVALID index behind** — deadlock or uniqueness
  violation both do this. The invalid index **is not used for queries but still
  carries update overhead**. Visible as INVALID in `psql \d`. Recovery is DROP
  and retry, or `REINDEX INDEX CONCURRENTLY`. **This is the single most
  under-anticipated production failure in the whole migration story.**
- Cannot run inside a transaction block. Only one concurrent build per table.
  Not supported on partitioned tables — build each partition individually.
- Unique indexes: the constraint is **already enforced against other transactions
  when the second scan begins**, so violations can surface before the index is
  ready, or even if the build ultimately fails.

## 5. Migrations — `ankane/strong_migrations`, fetched

An enumerated catalogue of 24 unsafe operations with a safe alternative for each.
Its real contribution is that **the unsafe operations share three recurring safe
shapes**, and naming those shapes is worth more than memorising 24 entries:

1. **The expand–contract ladder** (type change, rename column, rename table,
   rename schema, add auto-increment, rename enum value): create new → **write to
   both** → backfill → migrate reads → stop writing old → drop old. Six steps,
   multiple deploys, and it is the *only* safe answer for that entire family.
2. **NOT VALID then VALIDATE** (foreign keys, check constraints, **and NOT NULL**
   — via `add_check_constraint … validate: false` → deploy → validate → set
   `NOT NULL` → drop the check).
3. **`disable_ddl_transaction!` + `algorithm: :concurrently`** for every index,
   including the one hiding inside `add_reference` and the one hiding inside a
   unique constraint (index concurrently, *then* `add_unique_constraint … using_index:`).

Other load-bearing items:

- **Removing a column is unsafe** because the ORM caches the column list: ignore
  the column in code → deploy → then drop.
- **Volatile defaults** (`gen_random_uuid()`) force a rewrite; add the column,
  then `change_column_default`, then backfill.
- **`json` has no equality operator**, which breaks existing `SELECT DISTINCT`.
  Use `jsonb`.
- **Backfilling in the same transaction as the ALTER keeps the table locked for
  the whole backfill.** Batch (10,000) and **throttle** (`sleep 0.01`).
- **Timeouts are the safety net, and there are two different sets.** Migration:
  `lock_timeout = 10.seconds`, `statement_timeout = 1.hour` — "if a migration
  can't acquire a lock in a timely manner, other statements won't be stuck behind
  it." Application: `statement_timeout: 15s`, `lock_timeout: 10s`. The asymmetry
  is the point: a migration may run long but must never *wait* long; an
  application must never do either.
- Exclusion constraints have **no safe method** (cannot be NOT VALID).
  MySQL/MariaDB check constraints likewise.
- A non-unique index with more than three columns rarely helps; **lead with the
  column that narrows the most.**

## 6. Transactions — Django `transactions.txt`, fetched

Chosen as a source because Django states the ORM-boundary rules more explicitly
than most, and they generalise.

- Autocommit by default; nested `atomic()` blocks create **savepoints, not
  transactions** — "when an inner block completes successfully, its effects can
  still be rolled back if an exception is raised in the outer block."
  `durable=True` asserts outermost.
- **`ATOMIC_REQUESTS` (transaction-per-request) is named as inefficient as
  traffic increases**, and middleware and template rendering run *outside* it
  anyway. A transaction-per-request default is a scaling trap.
- **Do not catch exceptions inside an atomic block.** Catching hides the failure
  from the ORM; after a database error "the transaction is broken" and any query
  before rollback raises `TransactionManagementError`. Wrap the atomic block in
  try/except, not the reverse. **Model field values are not reverted by a
  rollback** — in-memory state must be restored by hand.
- **Never do non-database work inside a transaction** — emails, cache writes,
  enqueueing jobs. Use `on_commit()`. And the caveat that matters: **callbacks
  run *after* commit, so a failure in a callback does not roll anything back.**
  They are conditional on success but are not part of the transaction.
- "Keep your transactions as short as possible", especially outside the
  request/response cycle.

**This is the single cleanest statement of the dual-write problem in the hunt:**
the transaction cannot span the database and the outside world, so either the
side effect is enqueued transactionally (an outbox row written in the same
transaction) or it is fired after commit and may be lost. There is no third
option, and `on_commit` is the *lossy* one.

## 7. Optimistic vs pessimistic locking — Hibernate `Locking.adoc`, fetched

- `@Version` participates in the UPDATE's WHERE clause; a version mismatch
  affects zero rows and raises `StaleStateException` /
  `OptimisticEntityLockException`. **The application must catch and decide
  whether to retry** — the framework will not.
- Modes: OPTIMISTIC · OPTIMISTIC_FORCE_INCREMENT (bumps the version even with no
  entity change — the mechanism for "a child changed, so the aggregate root is
  now stale") · PESSIMISTIC_READ · PESSIMISTIC_WRITE (`SELECT … FOR UPDATE`) ·
  PESSIMISTIC_FORCE_INCREMENT.
- **Versionless optimistic locking**: `OptimisticLockType.ALL` puts every field
  in the WHERE clause; `DIRTY` puts only the changed fields, "minimizing the risk
  of OptimisticEntityLockException across non-overlapping entity property
  changes". Both need `@DynamicUpdate`.
- **When each fits:** optimistic "works particularly well in read-often-
  write-sometimes situations" and in **long conversations spanning several
  database transactions** — which is the real argument, and it is about
  *conversation length*, not contention rate.
- **NOWAIT (timeout 0) fails immediately if the row is locked; SKIP LOCKED
  (timeout −2) skips locked rows** via `SELECT … FOR UPDATE SKIP LOCKED`.
  SKIP LOCKED is the primitive underneath every Postgres-backed job queue, and it
  is worth naming as such.

## 8. Connection pooling — PgBouncer `config.md`, fetched

- **Session mode** (default): server released when the client disconnects.
  **Transaction mode**: released at COMMIT/ROLLBACK. **Statement mode**: released
  per query, and **multi-statement transactions are disallowed outright**.
- **Transaction pooling breaks session state, and this is the trap.** "Clients
  must not use any session-based features, since each transaction ends up in a
  different connection and thus gets a different session state." `SET`/`RESET`
  **leak to other clients** unless `server_reset_query_always` is on — and
  `server_reset_query` (default `DISCARD ALL`) **is not used in transaction mode
  at all**, precisely because you are not supposed to need it.
- **Prepared statements** need `max_prepared_statements`, which makes PgBouncer
  track and rewrite them. LISTEN/NOTIFY, WITH HOLD cursors, **session-level
  advisory locks** and temporary tables are implied incompatible but **not
  explicitly enumerated in the docs** — a genuine documentation gap worth
  recording.
- `max_client_conn` (global) and `default_pool_size` (per user/database pair) are
  different scopes. FD ceiling ≈ `max_client_conn + (pool_size × databases ×
  users)`.
- Three timeouts the docs themselves file under **"Dangerous timeouts"**:
  `idle_transaction_timeout` (disabled by default), `query_wait_timeout`
  (**120s default** — disconnects a client that never gets a server, which is
  what turns pool exhaustion into a visible error instead of a hang), and
  `transaction_timeout` (disabled by default).

## 9. Observability — OpenTelemetry + Prometheus, fetched

- **Instrument selection is a decision tree, not a style choice.** Monotonic
  count → Counter. Can go down → UpDownCounter. Timing or a distribution you want
  statistics over → **Histogram**. Absolute non-additive reading → Asynchronous
  Gauge. Additive monotonic → Asynchronous Counter. Additive non-monotonic →
  Asynchronous UpDownCounter.
- **Cardinality, with OTel's own worked example:** 7 attributes × 30 values each
  ⇒ **21,870,000,000 combinations** the SDK might have to remember. High-
  cardinality attributes (user IDs, raw URLs) cause unbounded memory growth.
  **OTel enforces a default cardinality limit of 2,000 unique attribute
  combinations per metric stream.**
- **Delta vs cumulative temporality is a memory decision.** Delta tracks only
  since the last export; cumulative must remember everything since process start,
  which is what makes cardinality explode.
- **`db.client.operation.duration` is a required metric**, and "when reported
  alongside a database operation span, the metric value SHOULD be the same as the
  span duration", with explicit bucket boundaries
  `[0.001, 0.005, 0.01, 0.05, 0.1, 0.5, 1, 5, 10]`. `db.client.connection.count`
  and `db.client.connection.max` exist but are **not yet stable**.
  *(Search-extracted — the three semantic-convention paths 404'd.)*
- **Prometheus alerting philosophy, quoted:** "Alert on symptoms, have good
  consoles to allow pinpointing causes, and avoid having pages where there is
  nothing to do." Page on latency at **one** point in the stack, not several.
  **Alert only on user-visible errors**; suppress downstream failures unless they
  independently need intervention. For batch jobs, page when the job "has not
  succeeded recently enough" to affect users, allowing **at least two cycles** of
  buffer (10 hours for a 4-hour job). Allow slack for small blips. Implement
  **metamonitoring** — test the alerting pipeline end to end, not component
  health. "Irrelevant alerts breed fatigue and erode trust."

## 10. Background jobs — **thin, see provenance**

From Sidekiq's Best Practices wiki (fetched, short):

- **Pass identifiers, not objects** — "don't save state to Sidekiq, save simple
  identifiers." JSON-safe argument types only; no symbols, Date, Time or keyword
  arguments.
- **At-least-once, stated plainly: "Sidekiq provides no exactly-once delivery.
  Even completed jobs can re-run if acknowledgment fails."** Therefore jobs must
  be idempotent by construction.
- Wrap database changes in transactions or make the job resilient to partial
  execution. Keep jobs small. Design for parallelism without resource locking.

From Hibernate (above): **`SELECT … FOR UPDATE SKIP LOCKED`** is the claim
primitive.

**Not reached:** transactional enqueue / the outbox pattern, deduplication and
uniqueness keys, retry and backoff policy, dead-letter handling, crash recovery
and visibility timeouts. River's README was never fetched; Graphile Worker's
returned only an overview. **This section needs a follow-up hunt before it can
anchor a skill.**

## 11. Caching — **thin, and the one section with no primary source**

The only fetched primary source is **Caffeine's Refresh wiki**, and it happens to
carry the sharpest distinction available:

**`expireAfterWrite` forces retrievals to block and wait for a new value.
`refreshAfterWrite` loads asynchronously in the background and returns the stale
value to concurrent readers.** "The old value (if any) is still returned while
the key is being refreshed, in contrast to eviction, which forces retrievals to
wait." And the subtlety: **"a refresh will only be actually initiated when the
entry is queried"** — so an unused key simply expires rather than triggering an
expensive recomputation. On failure the old value is kept and the exception is
logged and swallowed, preferring availability over strict consistency.

**That single contrast — expiry blocks, refresh doesn't — is the correct frame
for cache stampedes**, and it generalises well beyond Caffeine.

The remaining stampede material is a `WebSearch` that returned blog listicles and
is **not usable as evidence**. It names the right techniques — single-flight via
a distributed lock, probabilistic early expiration, request coalescing, jittered
TTLs, event-driven invalidation — and attributes a leases result to a 2013 USENIX
Facebook paper, but none of that was read at the source. **A follow-up hunt
should go to the memcached leases paper, Groupcache/singleflight, and Redis's own
documentation directly.**

## 12. Prior art on the skill shelf

`OneWave-AI/claude-skills` `database-schema-designer` was fetched. Structure:
249-character description, ~400–450 word body, four H2 sections (intro, contents,
seven-step workflow, example triggers), three references
(`schema-templates.md`, `output-format.md`, `best-practices.md`).

**It is a document generator, not an engineering skill.** The workflow runs
requirements → schema → statements → ERD → migration script → formatting →
checklist. **Nothing in it engages with lock modes, rewrite-vs-scan,
expand–contract, or NULL semantics** — the things that decide whether a schema
change can actually be deployed. It also never refuses or defers a decision.
That is the space an authored skill occupies.

---

## Improvement openings

1. **Everything here is organised by *mechanism*; developers arrive by
   *situation*.** Postgres documents lock modes; strong_migrations documents
   operations; nobody documents "I need to add a NOT NULL column to a table
   taking writes" as a single answer that spans all three.
2. **The three safe shapes are never named as shapes.** strong_migrations lists
   24 operations; the underlying answer is expand–contract, NOT VALID→VALIDATE,
   and concurrently+disable_ddl_transaction. Naming them collapses 24 rules into
   3 and makes the 25th case derivable.
3. **`CREATE INDEX CONCURRENTLY`'s INVALID-index failure mode is documented in
   one paragraph of the Postgres reference and appears in almost no migration
   guide.** It is the most likely thing to go wrong and the least likely to be
   planned for.
4. **Nobody connects the two timeout sets.** strong_migrations gives migration
   timeouts and app timeouts on the same page without saying *why* they are
   opposite, and PgBouncer's "dangerous timeouts" are a third set that interacts
   with both.
5. **The transaction/side-effect boundary is stated by Django as a rule and
   nowhere as a design.** `on_commit` is lossy; an outbox is not; no source puts
   them side by side and says which to choose when.
6. **Advisory locks and SKIP LOCKED are the two most useful Postgres primitives
   for application-level coordination, and both are buried** — one in an MVCC
   appendix, one in a Hibernate lock-mode table.
7. **Transaction-mode pooling's incompatibility list is genuinely incomplete in
   the upstream docs** ("implied incompatible but not explicitly enumerated").
   Enumerating it — advisory locks, LISTEN/NOTIFY, WITH HOLD cursors, temp
   tables, session `SET` — is a real contribution.
8. **Observability sources define instruments and cardinality but never say what
   a backend should actually emit.** The OTel database conventions plus the
   Prometheus symptom rule together imply a small default set; neither states it.

## Injection attempts

None observed in the recovered transcript. The one source-quality note: the cache
stampede search returned commercial blog content, which the scout itself flagged
and declined to rely on before it was terminated.
