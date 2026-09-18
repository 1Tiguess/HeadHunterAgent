# Web Store permissions and review

Load when preparing a Chrome Web Store submission.

## Contents

- [The governing rule](#the-governing-rule)
- [Permission notes](#permission-notes)
- [The all_urls suppression trap](#the-all_urls-suppression-trap)
- [Justification template](#justification-template)
- [Remote code](#remote-code)
- [Data disclosure](#data-disclosure)
- [Pre-submission checklist](#pre-submission-checklist)

## The governing rule

Request the narrowest permissions that implement the features you have actually shipped.
Where two permissions could accomplish the same thing, **the one with less access is
mandatory, not preferred** — this is stated as a requirement, not a recommendation.

Requesting a permission for a feature you have not built is named explicitly as prohibited
"future proofing". Ship the feature first.

The dashboard's privacy section enumerates every permission in your manifest and requires a
written justification for each. Broader-than-necessary requests are a stated rejection cause,
and the justification text is where reviews actually stall.

## Permission notes

| Permission | Warning shown | Notes |
|---|---|---|
| `activeTab` | **None** | Temporary access to the current tab, scoped to user invocation, revoked on navigation away or tab close. Always prefer this where it suffices. |
| `tabs` | "Read your browsing activity" | Required to read `url`, `title` or `favIconUrl` on tab objects. Unavoidable for a tab manager. |
| `storage` | None | Uncontroversial. |
| `unlimitedStorage` | Varies | Whether this draws extra scrutiny is unconfirmed. Avoid unless the ~10 MB `local` budget is genuinely insufficient. |
| `<all_urls>` | Broad host warning | Rarely justifiable. See below. |
| `optional_permissions` | Shown at request time | Preferred wherever functionality allows — gives users informed control at the moment it matters. |

The reason `tabs` carries a browsing-activity warning is worth understanding rather than
memorising: a tab's URL, title and favicon are treated as sensitive, and access to them
across all tabs, accumulated over time, is equivalent to browsing history. The warning is
accurate. Argue with it in your justification, not in your manifest.

## The `all_urls` suppression trap

Requesting `<all_urls>` **suppresses** the `tabs` warning, because the broader host
permission already surfaces a more comprehensive one.

This means an extension optimising for "fewest visible warnings" is led toward requesting
*more* access. It is a trap, not a technique. Reviewers see the manifest, not the warning
count, and a broad host permission without a matching feature is the clearest rejection
trigger there is.

If you find yourself reaching for `<all_urls>` to quiet a warning, stop.

## Justification template

One per permission, in the dashboard. Keep each to a few sentences and make the mapping to a
shipped feature explicit and checkable.

    Permission: tabs

    What the extension does with it: reads the URL, title and favicon of open
    tabs so the user can save a named session and restore it later. These three
    fields are stored locally and are the entire content of a saved session.

    Why a narrower permission does not suffice: activeTab grants access only to
    the tab the user is currently on at the moment of invocation. Saving a
    session requires reading every tab in a window at once, which activeTab
    cannot express.

    What happens to the data: it is written to chrome.storage.local on the
    user's machine. Nothing is transmitted. Browser sync is off by default and
    is opt-in; when enabled, a reduced projection is written to
    chrome.storage.sync and synced by the browser under the user's own account.

The three moves that make these pass: name the exact API surface used, state plainly why the
narrower option cannot do the job, and say where the data goes and where it does not.

## Remote code

MV3 removes the ability to execute remotely hosted code. Only JavaScript inside the reviewed
package may run.

Named violation patterns:

- a `<script>` tag pointing outside the package
- `eval()` or equivalents over a string fetched from a remote source
- **building an interpreter that executes complex commands fetched from a remote source, even
  when those commands arrive shaped as data**

That last one catches designs that feel safe. If a remote payload can change *what the
extension does* rather than *which of its built-in behaviours it selects*, it is remote code.

Still permitted: remote config for feature flags or A/B tests where all the logic already
ships in the package, fetching non-logic resources, and doing work server-side.

## Data disclosure

Under the Limited Use rules in force since 1 August 2026:

- Collected user data must be **strictly necessary** to the disclosed single purpose.
  Collection for any other purpose is prohibited.
- **All** data collection must be prominently disclosed to the user, regardless of how
  closely it relates to that single purpose.

The second point is the raised bar and the one most likely to be missed by anyone working
from older knowledge. It means an opt-in sync feature still needs disclosure even though it
is obviously within the extension's purpose.

Keeping everything local by default is therefore not only a privacy stance — it is what
keeps the disclosure surface small enough to state simply.

## Pre-submission checklist

- [ ] Every entry in `permissions`, `optional_permissions`, `host_permissions` and
      `optional_host_permissions` maps to a shipped feature
- [ ] Anything that could be optional is optional
- [ ] `activeTab` used wherever it suffices
- [ ] No `<all_urls>` unless a shipped feature genuinely needs every origin
- [ ] A justification drafted per permission, naming the API surface and why narrower fails
- [ ] No remote code path, including data-shaped command interpreters
- [ ] Every form of data collection disclosed, including opt-in sync
- [ ] Privacy practices section completed in the dashboard
