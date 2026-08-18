# 04 — Atlas

**Versioned internal documentation site with real search.**

## Problem

An infrastructure team's knowledge lives in three Notion pages, a wiki nobody updates, and
six README files. New engineers ask the same eight questions in Slack every month. The team
wants docs in the repo, versioned with the thing they describe, and searchable well enough
that people actually find answers instead of asking.

## Who it's for

The engineer three weeks into the job looking for how deploys work, and the engineer who
wrote it two years ago and has forgotten.

## Scope

- Markdown/MDX sources living in the repo, reviewed through pull requests
- Version switcher: docs for v2 and v3 served side by side, with a banner on stale versions
- Client-side search with useful relevance — title and heading matches beating body matches,
  prefix matching, and results that show enough context to choose between them
- Navigation generated from the file tree, with explicit ordering when needed
- Code blocks with syntax highlighting, copy button, and tabbed variants per language
- "Last reviewed" date per page, with a build warning past a staleness threshold
- Broken internal link detection at build time
- Dark mode, deep links to headings, and a keyboard-accessible search dialog

## Out of scope

Authoring UI, comments, per-user personalisation, translation, analytics beyond page views.

## Constraints

Static output, deployable to any object store behind a CDN. Search index must stay under
about 2MB so it can ship to the client. Build must run in CI in under two minutes.

## Success criteria

- Searching a term that appears only in a heading ranks that page first
- Every internal link resolves at build time, or the build fails
- Switching version keeps the reader on the equivalent page where one exists
- A page untouched for a year is visibly flagged as such
- Search dialog is fully operable by keyboard, including result navigation

## The hard part

Information architecture and search relevance. The naive version dumps every page into a
flat sidebar and ships a substring matcher, and people go back to asking in Slack.

## Predicted verdict

**Phase 3 clear.** This is `triage-rubric.md:46`'s third case — an expert would do it
noticeably better, *and I can already say what they know*: index headings separately and
weight them above body text, keep the index small by storing positions rather than context
strings, make versioning a URL-prefix concern decided before the first file exists, treat
"last reviewed" as build-enforced rather than advisory, and derive navigation from
frontmatter ordering with the file tree as fallback. Writing that down is the whole value;
the hunt would just be ceremony. Name it, record it, build.
