# Constraints and indexes

PostgreSQL. Reproductions are runnable.

## Contents
- [The three silent NULL failures](#the-three-silent-null-failures)
- [The fourth: unindexed foreign keys](#the-fourth-unindexed-foreign-keys)
- [ON DELETE as a modelling decision](#on-delete-as-a-modelling-decision)
- [Index design](#index-design)
- [Covering and index-only scans](#covering-and-index-only-scans)
- [Partial indexes](#partial-indexes)
- [Expression indexes](#expression-indexes)
- [Multiple indexes and bitmap scans](#multiple-indexes-and-bitmap-scans)
- [The testing discipline](#the-testing-discipline)

## The three silent NULL failures

These produce wrong data and never raise. That is what makes them worth leading with.

### 1. CHECK is satisfied by null

> A check constraint is satisfied if the check expression evaluates to true **or the null value**.

```sql
CREATE TABLE products (price numeric CHECK (price > 0));
INSERT INTO products VALUES (NULL);   -- succeeds
```

`NULL > 0` is `NULL`, which is not false, so the constraint passes. Every check constraint over a
nullable column has this hole.

```sql
CREATE TABLE products (price numeric NOT NULL CHECK (price > 0));
```

Explicit `NOT NULL` is also **more efficient** than `CHECK (price IS NOT NULL)`, and a column may
have at most one explicit not-null constraint.

### 2. UNIQUE treats two nulls as distinct

> Two null values are not considered equal in this comparison. That means even in the presence of a
> unique constraint it is possible to store duplicate rows that contain a null value.

```sql
CREATE TABLE memberships (tenant_id int, email text, UNIQUE (tenant_id, email));
INSERT INTO memberships VALUES (NULL, 'a@example.com');
INSERT INTO memberships VALUES (NULL, 'a@example.com');   -- both succeed
```

The fix:

```sql
UNIQUE NULLS NOT DISTINCT (tenant_id, email)
```

The documentation warns explicitly that the default *"is implementation-defined according to the SQL
standard, and other implementations have a different behavior"* — so this is a portability trap as
well. **State the NULLS decision on every unique constraint over a nullable column**, even when you
want the default, so the next reader knows it was chosen.

### 3. Foreign keys default to MATCH SIMPLE

> By default, a referencing row need not satisfy the foreign key constraint if any of its
> referencing columns are null.

With a composite foreign key, **one null disables the entire check**:

```sql
-- (org_id, project_id) references projects(org_id, id)
INSERT INTO tasks (org_id, project_id) VALUES (42, NULL);   -- passes, references nothing
```

`MATCH FULL` requires *all* referencing columns to be null for the row to escape, *"ensuring a mix of
null and non-null values is guaranteed to fail"* — which is almost always what was meant.

## The fourth: unindexed foreign keys

A foreign key requires the **referenced** columns to be a primary key or unique, so that side is
indexed. **The referencing side is not indexed automatically.**

> The declaration of a foreign key constraint does not automatically create an index on the
> referencing columns... it is often a good idea to index the referencing columns too.

Every `DELETE` or `UPDATE` of a referenced row must scan the referencing table for matches. On a
large child table with no index, deleting one parent row is a sequential scan — and under
`ON DELETE CASCADE` it is a sequential scan per parent row deleted.

**Rule: every foreign key gets an index on the referencing side, unless you have measured that it
does not need one.**

## ON DELETE as a modelling decision

| Action | Behaviour | Deferrable |
|---|---|---|
| `NO ACTION` (default) | Refuses if references remain | Yes |
| `RESTRICT` | Refuses if references remain | **No** |
| `CASCADE` | Deletes referencing rows too | — |
| `SET NULL` / `SET DEFAULT` | Nulls or defaults the referencing columns | — |

The documentation gives a modelling rule rather than a preference:

> When the referencing table represents something that is a component of what is represented by the
> referenced table and cannot exist independently, then CASCADE could be appropriate. If the two
> tables represent independent objects, then RESTRICT or NO ACTION is more appropriate.

Order lines are components of an order — `CASCADE`. Orders are not components of a customer — `NO
ACTION`, and deleting a customer with orders should fail loudly.

`SET NULL` and `SET DEFAULT` **do not bypass other constraints**: if the new value violates one, the
operation fails. A `SET NULL` onto a `NOT NULL` column is a delete that can never succeed.

## Index design

**The multicolumn ordering rule, exactly:**

> Equality constraints on leading columns, plus any inequality constraints on the first column that
> does not have an equality constraint, will always be used to limit the portion of the index that is
> scanned.

```sql
CREATE INDEX ON t (x, y, z);
SELECT * FROM t WHERE x = 5 AND y >= 42 AND z < 77;
```

The scan runs from the first `x=5, y=42` entry through the last `x=5` entry. **`z` filters the rows
found; it does not narrow the scan.**

Consequences for design:

- **Equality columns first**, in order of selectivity
- **Then one range column.** A second range column contributes nothing to narrowing
- A query that does not constrain the **leading** column generally cannot use the index at all
  (skip scan helps only when the leading column has few distinct values)

**Non-unique indexes with more than three columns rarely improve performance.** *"Start an index with
columns that narrow down the results the most."*

**An unused index is worse than idle.** Indexes *"prevent the creation of heap-only tuples"*, so they
add cost to every update of the table even when no query uses them. *"Indexes that are seldom or
never used in queries should be removed."*

## Covering and index-only scans

Two requirements, and the second is the one people miss:

1. The index type supports it — B-tree always; GiST/SP-GiST conditionally; **GIN cannot**
2. **The visibility map**:

> An index-only scan will be a win only if a significant fraction of the table's heap pages have
> their all-visible map bits set.

The visibility map tracks whether all rows on a heap page are old enough to be universally visible.
A hot table with constant writes has few all-visible pages, so **the index-only scan degrades to a
heap fetch anyway** and you paid the index maintenance for nothing.

**Covering indexes are a static-table optimisation.** On a write-heavy table they usually are not.

```sql
CREATE INDEX tab_x_y ON tab (x) INCLUDE (y);
```

`INCLUDE` columns are payload: outside the search key, outside uniqueness.

> If the heap tuple must be visited anyway, it costs nothing more to get the column's value from
> there.

Which is the same point from the other direction — `INCLUDE` only pays when the heap visit is
avoided.

## Partial indexes

Three cases where they pay:

1. **Excluding common values.** A query searching for a common value will not use the index anyway,
   *"so there is no point in keeping those rows in the index at all."*
2. **Excluding uninteresting rows.** Index only what you query — unbilled orders, active users,
   pending jobs.
3. **Enforcing uniqueness on a subset:**

```sql
-- one active subscription per customer; unlimited cancelled ones
CREATE UNIQUE INDEX ON subscriptions (customer_id) WHERE status = 'active';
```

That third case has no other expression in SQL and is the strongest reason to reach for a partial
index.

**The caveat:** *"do not use many non-overlapping partial indexes as a substitute for table
partitioning"* — the planner must test each one, and the overhead grows with the count. A single
multicolumn index or real partitioning is more efficient.

## Expression indexes

```sql
CREATE INDEX test1_lower_col1_idx ON test1 (lower(col1));
```

> Relatively expensive to maintain, because the derived expression(s) must be computed for each row
> insertion and non-HOT update.

But: *"the index expressions are not recomputed during an indexed search, since they are already
stored in the index."* So they pay when retrieval speed matters more than write cost — a read-heavy
case-insensitive lookup, not a write-heavy one.

## Multiple indexes and bitmap scans

PostgreSQL can combine index scans: scan each index, build an in-memory bitmap of row locations, then
AND or OR the bitmaps.

**The trade:** bitmap scans reorder heap access for efficiency and therefore **lose index ordering**,
so an `ORDER BY` needs an explicit sort afterwards.

For a mixed workload — sometimes `x`, sometimes `y`, sometimes both:

| Choice | Good at | Bad at |
|---|---|---|
| Two single-column indexes | Either column alone; both via bitmap | Slower than a composite for both-column queries |
| One multicolumn `(x, y)` | Both columns; `x` alone | `y` alone |
| Both | Everything | Highest write cost |

There is no universal answer. Measure with your query mix.

## The testing discipline

In this order. Skipping step 1 invalidates everything after it.

**1. Run `ANALYZE` first.**

> In absence of any real statistics, some default values are assumed, which are almost certain to be
> inaccurate.

**2. Use realistic data.** Selecting 1 row of 100 fits on a single page and will never benefit from
an index — the planner is right and your test is wrong. Artificially uniform, sorted, or
low-cardinality test data skews the statistics in ways that do not reproduce.

**3. Force index use to test viability.**

```sql
SET enable_seqscan = off;
EXPLAIN ANALYZE SELECT ...;
```

> If the system still chooses a sequential scan... there is probably a more fundamental reason why
> the index is not being used.

**4. Time both with `EXPLAIN ANALYZE`.** Compare estimated against actual rows. A large divergence
means either bad per-row cost estimates or bad selectivity estimates.

**5. Tune.** Raise the statistics target on the offending column
(`ALTER TABLE ... ALTER COLUMN ... SET STATISTICS`), re-analyze, and re-check. Cost parameters are
the last resort, and they are global.

**Always `SET enable_seqscan = on` afterwards.** It is a session setting, and leaving it off in a
pooled connection affects whoever gets that connection next.
