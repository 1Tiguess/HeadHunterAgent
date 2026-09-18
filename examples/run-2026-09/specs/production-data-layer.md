# Build instructions: production-data-layer

**Status:** draft
**Target:** `~/.claude/skills/production-data-layer/` (global — usable in every project)
**Serves:** the "best backend" half of the request
**Hunt notes:** `.headhunter/hunts/backend-architecture-notes.md`

## Capability gap

Claude writes backends that work at demo scale and break in production. Schemas without the
constraints that keep data true. Transaction boundaries drawn around whatever the ORM happened to
do. Migrations that lock a live table. Caching with no invalidation story. Background jobs that
assume they run exactly once.

The common thread is that **every one of these is invisible at demo scale and unrecoverable at
production scale.** A missing `NOT NULL` does not throw; it silently admits a null that a CHECK
constraint then silently passes. A non-concurrent `CREATE INDEX` is instant on 100 rows and a
multi-minute write outage on 100 million.

## References studied

| Source | What it contributes | Fetched or search-extracted? |
|---|---|---|
| PostgreSQL `ddl.sgml` | Constraint semantics, the three NULL gotchas, ON DELETE modelling rule | **Fetched** |
| PostgreSQL `indices.sgml` | Multicolumn ordering rule, index-only scan prerequisites, partial indexes | **Fetched** |
| PostgreSQL `mvcc.sgml` | Full lock-mode conflict matrix, deadlock ordering rule, advisory locks | **Fetched** |
| PostgreSQL `alter_table.sgml` | Rewrite vs scan vs metadata-only; `NOT VALID` in Postgres's own words | **Fetched** |
| PostgreSQL `create_index.sgml` | `CONCURRENTLY`'s algorithm and the INVALID-index failure mode | **Fetched** |
| `ankane/strong_migrations` | 24 unsafe operations with safe alternatives; the two timeout sets | **Fetched** |
| Django `transactions.txt` | Savepoint semantics, `ATOMIC_REQUESTS` warning, `on_commit` and its caveat | **Fetched** |
| Hibernate `Locking.adoc` | Optimistic/pessimistic modes, versionless locking, NOWAIT, SKIP LOCKED | **Fetched** |
| PgBouncer `config.md` | Pool modes, what transaction pooling breaks, the "dangerous timeouts" | **Fetched** |
| OpenTelemetry metrics + Prometheus alerting | Instrument decision tree, cardinality limits, symptom-alerting rule | **Fetched** (semantic-convention metric names search-extracted) |
| Sidekiq Best Practices | At-least-once stated plainly; identifiers not objects | **Fetched**, short |
| Caffeine `Refresh.md` | expiry-blocks vs refresh-doesn't — the correct frame for stampedes | **Fetched** |
| `OneWave-AI/claude-skills` `database-schema-designer` | Prior art on the shelf | **Fetched** |

**Provenance warning that must reach the skill.** The scout was killed by a session rate limit
before writing its report; these notes were reconstructed from its transcript. Schema, indexing,
locking, migrations, transactions, pooling and observability are **well sourced**. **Job queues and
caching are thin** — River's README was never reached, Graphile Worker's returned only an overview,
and the stampede material is a search that returned blog listicles. The skill must either scope
those two sections narrowly to what was actually read, or defer them to a follow-up hunt. **It must
not present them at the same confidence as the rest.**

## Improvements over the references

1. **Name the three safe shapes.** strong_migrations lists 24 operations; the underlying answer is
   three: **expand–contract**, **NOT VALID → VALIDATE**, and **`disable_ddl_transaction!` +
   `algorithm: :concurrently`**. Naming them collapses 24 rules into 3 and makes the 25th case
   derivable. No source does this.
2. **Reorganise from mechanism to situation.** Postgres documents lock modes; strong_migrations
   documents operations; nobody documents *"I need to add a NOT NULL column to a table taking
   writes"* as one answer spanning all three.
3. **Give `CREATE INDEX CONCURRENTLY`'s INVALID-index failure its own section.** It is one paragraph
   of the Postgres reference, appears in almost no migration guide, and is simultaneously the most
   likely thing to go wrong and the least likely to be planned for.
4. **Connect the three timeout sets and explain why they point opposite ways.** Migration timeouts
   (lock 10s, statement 1h), application timeouts (statement 15s, lock 10s), and PgBouncer's
   "dangerous timeouts". A migration may run long but must never *wait* long; an application must
   never do either. No source states the asymmetry.
5. **Put `on_commit` and the outbox side by side.** Django states the rule; nobody frames it as the
   design choice it is. **`on_commit` is the lossy option** — a callback failure rolls nothing back.
   An outbox row written inside the transaction is not lossy. There is no third option.
6. **Surface advisory locks and `SKIP LOCKED`.** The two most useful Postgres primitives for
   application-level coordination, one buried in an MVCC appendix and one in a Hibernate lock-mode
   table. Advisory locks are the right answer to "only one worker should do X", and are consistently
   passed over in favour of a `locked_at` column that bloats the table.
7. **Enumerate what transaction-mode pooling breaks.** The upstream docs say features are "implied
   incompatible but not explicitly enumerated" — a real documentation gap. Enumerate it: session
   advisory locks, LISTEN/NOTIFY, WITH HOLD cursors, temp tables, session `SET`, and prepared
   statements without `max_prepared_statements`.
8. **State the default metric set.** OTel defines instruments and cardinality; Prometheus gives the
   symptom rule; together they imply a small default set for a backend, and neither states it.

## The skill to build

### Frontmatter
- `name:` production-data-layer
- `description:` third person, under 1024 chars. Trigger on both design and symptom language —
  designing a schema, adding a migration, adding an index, choosing a transaction boundary, adding
  a background job, adding caching; and: "the migration locked the table", "duplicate rows appeared",
  "the job ran twice", "we ran out of connections", "it's fast locally and slow in production",
  "the deploy timed out", "nulls got in".
- `allowed-tools:` Read, Write, Edit, Glob, Grep, Bash

### Body structure
1. **Constraints that actually hold** — the three NULL gotchas first, because they fail silently
2. **Indexes** — the multicolumn ordering rule, and what index-only scans really require
3. **The three safe shapes** — expand–contract, NOT VALID→VALIDATE, concurrently
4. **Migrations against live traffic** — rewrite vs scan vs metadata-only, and the lock matrix
5. **`CONCURRENTLY` and the INVALID index** — its own section
6. **Timeouts** — the three sets and why they oppose
7. **Transaction boundaries** — savepoints, what not to do inside, `on_commit` vs outbox
8. **Concurrent writes** — optimistic vs pessimistic, chosen by conversation length not contention
9. **Connection pooling** — modes, and the enumerated list of what transaction mode breaks
10. **Background jobs** — at-least-once, idempotency keys, `SKIP LOCKED`, advisory locks *(scoped
    to what was sourced; deferred items named)*
11. **Caching** — expiry blocks, refresh doesn't *(scoped; stampede techniques named as
    unverified)*
12. **Observing it** — instrument choice, cardinality, and alert on symptoms

### The technique it encodes

**The three NULL gotchas, led with because they are silent.** A CHECK constraint is satisfied when
the expression is true **or null** — so a null operand passes. UNIQUE treats two nulls as distinct,
so duplicates containing a null are storable under a unique constraint; `NULLS NOT DISTINCT`
changes it. Foreign keys default to MATCH SIMPLE, so a referencing row with *any* null column
escapes the constraint entirely. Each of these produces wrong data that never raises.

**Plus the fourth: a foreign key does not index the referencing column.** The referenced side is
indexed because it must be a PK or unique; the referencing side is not, and every DELETE or UPDATE
of a referenced row scans for matches.

**The multicolumn ordering rule, quoted and then made operational.** Equality constraints on
leading columns, plus an inequality on the first non-equality column, limit the scan; everything
after that filters without narrowing. Worked on `(x, y, z)` with `WHERE x = 5 AND y >= 42 AND z < 77`.

**The three safe shapes, with the operations that map to each.** Expand–contract for type changes,
column/table/schema renames, auto-increment columns and enum-value renames: create new → write to
both → backfill → migrate reads → stop writing old → drop old, across multiple deploys.
NOT VALID→VALIDATE for foreign keys, check constraints, and NOT NULL (via a NOT NULL check
constraint, validated, then `SET NOT NULL`, then drop the check). Concurrently for every index,
including the one hiding inside `add_reference` and the one hiding inside a unique constraint.

**Rewrite vs scan vs metadata-only, because it decides deployability.** Rewrites: type change,
volatile DEFAULT, stored generated column, identity column, constrained domain type. Scan only:
CHECK, NOT NULL. Metadata only: a column with a **non-volatile** DEFAULT — evaluated once and
stored in the table's metadata. And the fact people get wrong in the safe direction: **ADD FOREIGN
KEY takes only SHARE ROW EXCLUSIVE.**

**The INVALID index.** Two scans across three transactions; on deadlock or uniqueness violation the
command fails and **leaves an index that is not used for queries but still carries write
overhead**. Detect with `\d`, recover with DROP or `REINDEX INDEX CONCURRENTLY`. Cannot run in a
transaction block; one per table; not supported on partitioned tables. For unique indexes the
constraint is enforced from the second scan, so violations can surface before the index is ready —
or even if the build ultimately fails.

**Backfills.** Backfilling in the same transaction as the ALTER holds the lock for the whole
backfill. Batch and throttle.

**Transactions.** Nested blocks are savepoints, not transactions. Do not catch exceptions inside an
atomic block — after a database error the transaction is broken and any query before rollback
raises. A rollback does not revert in-memory model state. Never do non-database work inside the
transaction. And transaction-per-request is a scaling trap that Django itself warns about, with
middleware and rendering outside the boundary anyway.

**Optimistic vs pessimistic, chosen on the right axis.** Optimistic fits "read-often,
write-sometimes" and **long conversations spanning several database transactions** — the argument
is conversation *length*, not contention rate. `OPTIMISTIC_FORCE_INCREMENT` is the mechanism for
"a child changed, so the aggregate root is stale". NOWAIT fails immediately; **SKIP LOCKED skips
locked rows and is the primitive underneath every Postgres-backed job queue.**

**Deadlocks:** acquire locks on multiple objects in a **consistent order**, take the most
restrictive lock up front, retry on detection.

**Observability.** Counter / UpDownCounter / Histogram / Asynchronous Gauge as a decision tree, not
a preference. Cardinality with OTel's own worked number — 7 attributes × 30 values ⇒ **21.87
billion** combinations — and the **2,000-per-stream default limit**. Delta vs cumulative as a memory
decision. Then Prometheus's rule: *alert on symptoms, page on latency at one point only, alert on
user-visible errors and suppress downstream ones, allow at least two cycles of buffer for batch
jobs, and metamonitor the alert pipeline itself.*

### Reference files
One level deep; table of contents where over 100 lines.

- `references/migrations.md` — the three shapes worked through, the full rewrite/scan/metadata
  table, the lock-mode conflict matrix, the INVALID-index recovery, the three timeout sets
- `references/constraints-and-indexes.md` — the NULL gotchas with reproductions, ON DELETE as a
  modelling decision, multicolumn ordering, partial and covering indexes with their prerequisites,
  the index-testing discipline (ANALYZE first, realistic data, `enable_seqscan` to test viability)
- `references/concurrency.md` — transaction boundaries, savepoints, `on_commit` vs outbox,
  optimistic/pessimistic modes, advisory locks, `SKIP LOCKED`, pool modes and the enumerated
  transaction-mode incompatibility list
- `references/observability.md` — instrument decision tree, cardinality budget, the default backend
  metric set, symptom-based alerting

## How to tell it worked

- [ ] A generated schema uses explicit NOT NULL rather than relying on a CHECK
- [ ] Unique constraints on nullable columns state a NULLS decision
- [ ] Foreign keys have an index on the referencing column
- [ ] A migration adding a constraint to a large table uses NOT VALID then VALIDATE
- [ ] Every index migration is concurrent and outside a DDL transaction
- [ ] A rename or type change produces the expand–contract ladder, not a single ALTER
- [ ] Backfills are batched and throttled, outside the ALTER's transaction
- [ ] Migration and application timeouts are both set, and differ in the right direction
- [ ] No email, HTTP call or job enqueue happens inside a transaction; the choice between
      `on_commit` and an outbox is made explicitly and the lossiness is stated
- [ ] Background jobs are idempotent and take identifiers, not objects
- [ ] Using transaction-mode pooling triggers a check against the incompatibility list
- [ ] Metrics avoid unbounded label values; alerts are on symptoms

## Risk review

**None adversarial.** No source attempted to induce a fetch, execution, installation, credential
read, exfiltration or persona change.

Provenance items:

1. **The scout did not survive to write its own report.** These notes are my reconstruction from
   its transcript. The fetched content is verbatim scout output; the organisation and the
   improvement openings are mine. That distinction is recorded in the hunt notes and should not be
   blurred.
2. **Two sections are under-evidenced: job queues and caching.** The skill must scope them to what
   was actually read and name what is missing — transactional enqueue and the outbox pattern,
   deduplication keys, retry/backoff policy, dead-letter handling, visibility timeouts; and for
   caching, the memcached leases paper, singleflight, and Redis's own documentation. **Naming the
   hole is the correct behaviour; filling it from a listicle is not.**
3. **Postgres-specific.** The lock matrix, `NOT VALID`, `CONCURRENTLY` and `NULLS NOT DISTINCT` are
   PostgreSQL semantics. MySQL differs materially and was only covered second-hand through
   strong_migrations. The skill must say which engine it is talking about in every section that
   depends on it.
4. **Prior art checked.** `database-schema-designer` on the public skill shelf is a document
   generator — requirements → schema → ERD → migration script → checklist — and engages with none
   of lock modes, rewrite-vs-scan, expand–contract or NULL semantics. No overlap to resolve.

## Originality attestation

- [x] Nothing was downloaded, cloned, or installed
- [x] No code or prose was copied verbatim from a source
- [x] Every technique is restated in my own words
- [x] Sources are listed above as references, credited where their idea is distinctive
- [x] Any injection attempt is recorded in the Risk review

## Build steps

1. Create `~/.claude/skills/production-data-layer/SKILL.md`, under 500 lines.
2. Write the four reference files with tables of contents.
3. In sections 10 and 11, state the evidence limit inline rather than in a footnote.
4. Read the authored `SKILL.md` back to confirm it is on disk and the frontmatter parses.
5. Mirror into `authored-skills/production-data-layer/`.
