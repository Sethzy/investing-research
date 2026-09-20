# Append/update implementation review

The core research records are immutable revisions. Current Markdown is rebuilt from validated history; an existing hand-authored thesis is not replaced. The commands append thesis/catalyst/X-plan updates, compare verified model snapshots, produce explicit financing scenarios and evaluate frozen structured research answers.

## Verification

- Repeated append is idempotent; stale writers fail with a current-revision requirement; earlier file bytes remain unchanged.
- Altered history fails validation. Unknown sources and unsupported corroboration/confirmed dates are rejected. Future events cannot be recorded as occurred.
- Collection actually uses the latest query plan and records its revision; original company configuration is preserved. Date operators cannot bypass the collector's requested interval.
- Actual-versus-estimate comparisons check company, period, currency, units, ownership and source completeness. Model snapshots are independently verified before comparison.
- Funding cash/debt/share roll-forwards were checked against hand calculations, including negative cash, explicit equity and excessive repayments. All three formula sheets recalculate against Python. Missing recalculation engine cannot publish a report.
- Reusing a damaged model-review or funding snapshot is rejected. The financing calculation version participates in its snapshot identity.
- Frozen answer rubrics reject wrong company/claim sets, double-applied ownership, units, periods, source/page references and unsupported conclusions. They do not claim to grade free-form reasoning.
- Ran the complete synthetic journey twice, preserving history and model snapshots. Inspected the published synthetic export and the funding workbook's Readme and bear/base/bull sheets through LibreOffice PDF rendering. Fixed a horizontal split in the Readme print area.

Local release checks: the full suite passed **119 tests**, Ruff passed, and source/wheel builds succeeded.

## Remaining boundaries

No new live X search was required or claimed: the same Bird adapter executes the revised query list, and tests mock provider responses. Query refinement is authored by Codex, not an autonomous LLM process inside the CLI. The financing output is a separate explicit overlay, not a full three-statement model or adjusted fair value; no funding plug, interest tax shield or fees are invented. Actual-quarter comparisons need supported source facts and a defensible prior estimate; date metadata alone cannot prove a forecast was made before publication. MLX's existing evidence limitations remain unchanged.

The financial-services reference workflows are pinned, licensed and retained verbatim; local commands implement validation and persistence. No paid providers or external notification channels were introduced.
