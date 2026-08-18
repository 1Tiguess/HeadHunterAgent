# 05 — Tabkeep

**Chrome extension for saving, restoring and pruning tab sessions.**

## Problem

A researcher habitually has 60+ tabs across five windows. Closing a window loses context
they can't reconstruct. Existing extensions either sync everything to someone's server or
break every time Chrome updates. They want something local, fast, and durable.

## Who it's for

Anyone whose browser is their working memory.

## Scope

- Save the current window, all windows, or a selection as a named session
- Restore a session into a new window, or merge into the current one
- Auto-save a rolling snapshot so a crash loses at most a few minutes
- Search across saved sessions by title and URL
- Prune: find duplicates, tabs unopened in 30 days, and dead links
- Export and import as JSON, entirely local
- Keyboard-first popup, and an options page for retention policy
- Optional sync through the browser's own sync storage, off by default

## Out of scope

Accounts, a hosted backend, cross-browser builds beyond Chromium, tab grouping automation.

## Constraints

Manifest V3. No remote code, which the store forbids outright. Must handle a 500-tab
session without freezing the popup. Local storage only unless the user opts into browser
sync. Must survive the service worker being killed at arbitrary moments.

## Success criteria

- Saving 500 tabs completes without blocking the UI
- A session survives browser restart, extension update, and service-worker termination
- Restore reproduces tab order, pinned state, and window grouping
- No network request leaves the machine with sync disabled — verifiable in DevTools
- Passes Chrome Web Store review without a permissions justification round-trip

## The hard part

Manifest V3's service-worker lifecycle. The worker is killed aggressively and unpredictably,
so anything held in memory is gone; state has to round-trip through storage on every
meaningful transition, and long operations need to be chunked and resumable. On top of that:
`chrome.storage.local` quota behaviour at this data volume, the difference between
`session`/`local`/`sync` areas, which permissions trigger store review friction, and how to
request host permissions optionally rather than up front.

These are precisely the failure modes that are invisible from outside and expensive to
discover by trial and error.

## Predicted verdict

**HUNT.** I cannot currently state the service-worker lifecycle rules, the storage quota
thresholds, or the store's permission-review triggers with the precision needed to build
this right. That is a nameable gap in observable behaviour, which is the test
`SKILL.md:83` sets.

**Verified sources for the hunt:** `developer.chrome.com` (MV3 migration, service worker
lifecycle, storage API, Web Store program policies), `developer.mozilla.org` for the
cross-engine extension baseline.
