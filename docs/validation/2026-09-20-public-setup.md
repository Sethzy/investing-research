# Public setup release validation

Date: 2026-09-20. Scope: recipient onboarding, installation, X authentication guidance and public-source handoff.

## What changed

- A terminal installer provisions locked Python dependencies and checks Node 22+.
- A resumable `invest setup` interview stores local preferences and supports a strictly validated, noninteractive `--answers` path for a conversational coding agent.
- A bundled setup skill guides identity resolution, first research, optional portfolio setup and host scheduling. These are explicitly separate from saving preferences.
- The README supplies a copyable Git-link installation request. A dedicated authentication guide explains profile selection, OS prompts, expiry, rate limits and browser fallback.
- Public CI installs from the lockfile on macOS and Ubuntu, tests offline behaviour, and runs independent workbook recalculation on Ubuntu with LibreOffice. CI contains no X credentials.

## Checks performed before publication

- **83 tests passed**, including ten onboarding tests. Ruff, shell syntax, relative documentation links and Git whitespace checks passed.
- Clean source-only directory: installer provisioned a fresh Python 3.12 environment; noninteractive setup validated answers, preserved an empty watchlist and completed a live authenticated X search with session-token environment variables removed.
- Fresh installation produced the synthetic mine report, chart and editable workbook; independent LibreOffice recalculation passed.
- Existing workspace `doctor --live-x` also returned `ok`, with three bounded results.
- Distribution build included the onboarding module and vendored Bird licence; no private data directories were present in the wheel.
- Pre-release history was scanned with Gitleaks in redacted mode: no leaks found. Historical filenames were also checked for ignored settings, portfolio, session and generated-research directories. Only source and public documentation are published.

Live authentication used the current operator's own browser session on macOS. A different recipient's account or machine was not available for testing; every installation must perform its own live check. Synthetic model success does not establish a real-company valuation. The first actual scheduled host run remains a separate verification requirement.

## Review and correction

Applied the personal implementation workflow and performed an independent read-only review using the security and code-quality review skills. The referenced `ce-code-review`/`ce-simplify-code` wrappers were unavailable; the actual review and manual simplification pass were used instead.

The reviewer found that resuming setup could reuse an old successful X check after cookies expired. Setup now invalidates historical success, uses the current browser settings, and performs or explicitly defers a fresh check. Regression tests cover expired access, externally changed profiles and declining the recheck. No other actionable finding remained in this review's scope.

## Operational validation

For each recipient, inspect `private/preferences.json` for the current `x_check` timestamp/status and `private/setup-summary.md` for unresolved identities or scheduling. `ready_for_research` means preferences and a current X probe passed; it does not mean an investment dossier or schedule is complete. Failures must remain `x_setup_pending`, explicit failed collection receipts, or pending-review work.

The recipient and their host agent own the first interactive and first scheduled execution checks. Recheck immediately after an auth failure or browser/profile change. If an update breaks collection, retain receipts, stop relying on automatic coverage, and use explicitly labelled browser capture while investigating. Disable the host automation separately when uninstalling the checkout.
