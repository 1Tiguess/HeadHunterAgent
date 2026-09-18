# Patterns, in plain code

No framework. Each of these is small enough to read in full and adapt. Python for concreteness; the
shapes are language-independent.

## Contents
- [Token bucket retry budget](#token-bucket-retry-budget)
- [Bounded concurrency](#bounded-concurrency)
- [Circuit breaker with four states](#circuit-breaker-with-four-states)
- [Slow-call detection](#slow-call-detection)
- [Scaled load shedding](#scaled-load-shedding)
- [Checkpointed work](#checkpointed-work)
- [Dead-letter handling](#dead-letter-handling)
- [Deadline propagation](#deadline-propagation)

## Token bucket retry budget

```python
import threading

class RetryBudget:
    """Caps retries as a share of traffic. Shared across all callers of one dependency."""

    def __init__(self, ratio=0.1, capacity=100, min_tokens=10):
        self.ratio = ratio            # retries permitted per first-attempt success
        self.capacity = capacity
        self.min_tokens = min_tokens  # stop retrying below this
        self.tokens = capacity
        self.lock = threading.Lock()

    def record_success(self):
        with self.lock:
            self.tokens = min(self.capacity, self.tokens + self.ratio)

    def try_acquire(self, cost=1.0):
        """cost=2.5 for a timeout-triggered retry: the upstream work is probably still running."""
        with self.lock:
            if self.tokens - cost < self.min_tokens:
                return False
            self.tokens -= cost
            return True
```

Wire it so `record_success` fires on **first-attempt** successes only. Crediting on retried
successes defeats the purpose — a dependency failing half its requests would keep refilling its own
budget.

## Bounded concurrency

The circuit breaker you should reach for first.

```python
import threading

class Bulkhead:
    def __init__(self, limit):
        self.sem = threading.Semaphore(limit)

    def __enter__(self):
        if not self.sem.acquire(blocking=False):   # reject, never queue
            raise Overloaded("concurrency limit reached")
        return self

    def __exit__(self, *exc):
        self.sem.release()
```

**`blocking=False` is the whole design.** Blocking turns a concurrency limit into an unbounded queue
— the exact bug this is meant to prevent. Rejecting immediately pushes backpressure to the caller,
which is the cheapest place to absorb it.

One `Bulkhead` **per dependency**, not one per process. A shared pool means a sick dependency starves
the healthy ones.

## Circuit breaker with four states

```python
import time
import threading
from collections import deque

CLOSED, OPEN, HALF_OPEN, ISOLATED = "closed", "open", "half_open", "isolated"

class CircuitBreaker:
    def __init__(self, threshold=0.5, min_throughput=20, window_s=10,
                 break_s=30, probes=3):
        self.threshold = threshold
        self.min_throughput = min_throughput
        self.window_s = window_s
        self.break_s = break_s
        self.probes = probes
        self.state = CLOSED
        self.calls = deque()          # (timestamp, ok)
        self.opened_at = None
        self.probe_results = []
        self.lock = threading.Lock()

    def isolate(self):
        """Human decision. Deliberately distinct from the breaker's own decision."""
        with self.lock:
            self.state = ISOLATED

    def reset(self):
        with self.lock:
            self.state, self.calls, self.probe_results = CLOSED, deque(), []

    def allows(self):
        with self.lock:
            if self.state == ISOLATED:
                return False
            if self.state == OPEN:
                if time.monotonic() - self.opened_at >= self.break_s:
                    self.state, self.probe_results = HALF_OPEN, []
                    return True
                return False
            return True

    def record(self, ok):
        with self.lock:
            if self.state == ISOLATED:
                return
            if self.state == HALF_OPEN:
                self.probe_results.append(ok)
                if not ok:
                    self.state, self.opened_at = OPEN, time.monotonic()
                elif len(self.probe_results) >= self.probes:
                    self.state, self.calls, self.probe_results = CLOSED, deque(), []
                return

            now = time.monotonic()
            self.calls.append((now, ok))
            while self.calls and now - self.calls[0][0] > self.window_s:
                self.calls.popleft()

            if len(self.calls) < self.min_throughput:    # the gate that matters at low traffic
                return
            failures = sum(1 for _, o in self.calls if not o)
            if failures / len(self.calls) >= self.threshold:
                self.state, self.opened_at = OPEN, now
```

Two details that are easy to drop and expensive to omit:

- **`min_throughput` is checked before the ratio.** Without it, two failures out of two trips the
  breaker on a low-traffic dependency.
- **`ISOLATED` never transitions on its own.** A human opened it; a human closes it. Otherwise you
  cannot tell recovery from intervention.

## Slow-call detection

A failure-rate breaker cannot see this. Count slow successes as failures:

```python
def record_with_latency(breaker, ok, duration_s, slow_threshold_s):
    breaker.record(ok and duration_s < slow_threshold_s)
```

Set `slow_threshold_s` from the baseline, not from the timeout — by the time you hit the timeout the
damage is done. A call at 5x the normal median is a signal even though it succeeded.

## Scaled load shedding

```python
import random

def shed_probability(inflight, scaling_limit, saturation_limit):
    """0.0 below the scaling threshold, 1.0 at saturation, linear between."""
    if inflight <= scaling_limit:
        return 0.0
    if inflight >= saturation_limit:
        return 1.0
    span = saturation_limit - scaling_limit
    return (inflight - scaling_limit) / span
```

Interpolating means the system tightens progressively instead of flipping between fine and
refusing. Binary shedding oscillates: it sheds, load drops, it stops shedding, load returns.

Apply it **by priority class**, so the ranked degradation list is enforced mechanically:

```python
CRITICAL, IMPORTANT, OPTIONAL = 0.0, 0.5, 1.0   # shed multiplier

def should_shed(priority_multiplier, p):
    return random.random() < p * priority_multiplier
```

`CRITICAL` is never shed. That is the "never dropped" row of the plan, expressed in code.

## Checkpointed work

```python
def run_job(job, checkpoint_store, heartbeat):
    cursor = checkpoint_store.load(job.id) or job.start
    for item in job.items_from(cursor):
        key = stable_key(job.id, item)
        if not already_done(key):          # idempotency: check before acting
            process(item)
            mark_done(key)
        cursor = item.position
        heartbeat(job.id, cursor)          # liveness AND checkpoint, one write
```

**The heartbeat carries the checkpoint.** You needed the liveness signal anyway, so resumption costs
one extra field. That converts "restart the six-hour job" into "continue from item 40,000".

The progress-gap timeout watches this heartbeat. It is the **only** timeout that detects a worker
that died mid-job — the job is not queued, not failed, and not finished, so nothing else will notice.

## Dead-letter handling

```python
def handle(msg, max_attempts=5):
    try:
        process(msg)
    except Exception as e:
        if classify(e, msg.operation) != RETRYABLE or msg.attempts + 1 >= max_attempts:
            dead_letter(msg, reason=failure_class(e))   # low-cardinality class, not a message
            return
        requeue(msg, delay=backoff(msg.attempts))
```

Without the dead-letter branch, one poisoned message consumes the retry budget indefinitely and
starves everything behind it.

## Deadline propagation

```python
import time

class Deadline:
    """Absolute, so it survives hops. A duration would silently reset at each boundary."""

    def __init__(self, seconds):
        self.at = time.monotonic() + seconds

    def remaining(self):
        return max(0.0, self.at - time.monotonic())

    def expired(self):
        return self.remaining() <= 0

    def for_attempt(self, per_attempt_cap):
        return min(per_attempt_cap, self.remaining())
```

Pass the `Deadline` down, not a fresh timeout. Each hop gets what is left. Send `remaining()` in a
header so the next service inherits the same absolute bound rather than starting a new clock.
