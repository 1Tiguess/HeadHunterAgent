# 01 — Beacon

**One-page launch site for a side project.**

## Problem

A solo developer finishes a small paid tool and has nowhere to send people. They need one
page that explains what it is, shows it working, and takes money or an email address.
Today that page either doesn't exist or is a template with the placeholder copy still in it.

## Who it's for

The developer shipping the tool, and the stranger who clicked a link from a forum post and
will decide in about eight seconds whether to keep reading.

## Scope

- Single page, no router
- Hero: one-sentence value claim, one screenshot or short loop, one primary action
- Three-to-five capability blocks, each a concrete outcome rather than a feature name
- Pricing: at most three tiers, with the recommended one visually settled rather than shouted
- FAQ addressing the four objections that actually block purchase
- Footer: contact, terms, privacy
- Email capture that posts somewhere real
- Responsive from 320px, light and dark, prefers-reduced-motion honoured
- Open Graph and Twitter card metadata so shared links render

## Out of scope

Blog, docs, auth, dashboard, CMS, i18n, A/B testing infrastructure.

## Constraints

Static host. No build step heavier than a bundler. Lighthouse performance ≥ 95 on mobile.
Total page weight under 500KB including the hero image. No cookie banner, because no
cookies.

## Success criteria

- Loads and is readable with JavaScript disabled
- Every interactive element reachable and operable by keyboard
- Contrast passes WCAG AA against both themes
- The value claim is legible without scrolling on a 360×640 viewport
- Email capture round-trips to a real inbox and fails visibly when it can't

## The hard part

Honestly: not very. Landing pages are the most-trodden ground in web development, the
constraints are well understood, and the failure modes (vague copy, hero carousel, four
competing calls to action) are ones I can already name without research.

## Predicted verdict

**Phase 1 clear.** `triage-rubric.md:53` calls this out directly: landing pages usually
clear, and hunt only if the user signals a high bar — brand-critical work, a conversion
target, an unusual aesthetic. None of those is present. Clearing this is the gate working,
not the gate failing.
