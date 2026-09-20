# Excel and Markdown implementation validation

The primary report is readable Markdown with a relative link to a detailed Excel snapshot. Excel edits to mapped inputs are accepted only after all three scenarios and all nine sensitivities recalculate independently and agree with the Python financial checks. Existing model snapshots remain immutable.

## Checks performed

- Edited a synthetic commodity-price assumption; checked the resulting value with a hand calculation and verified the Markdown and dossier links.
- Recalculated bear/base/bull with different forecast horizons, negative EBIT, closure and residual values.
- Confirmed formula/static-cell tampering, invalid shares, invalid selectors, corrupt snapshots and missing reports are rejected.
- Preserved numeric, date and blank quote overrides across repeated source refreshes; recorded concurrent source/user conflicts.
- Confirmed missing LibreOffice cannot publish stale cached values and repeated default model creation preserves existing edits.
- Confirmed working-workbook edits are marked unsynchronized and old snapshot bytes remain intact.
- Reconciled FY2024/FY2025 historical gross profit, net income, assets/liabilities/equity and opening-to-closing cash.
- Generated the public MLX workbook, independently recalculated all scenarios, verified its exported snapshot and visually inspected its rendered sheets and charts.

Local release checks: **102 tests passed**, Ruff passed, wheel/source distribution built, tracked-file secret scan passed, and pinned upstream file hashes matched their provenance manifest.

## Review fixes

The code review identified two concrete workflow defects: text/null overrides could be lost on a later refresh, and reusing a snapshot could bypass verification of damaged or missing files. Both are fixed with regression coverage. Quote and quote date are preserved together. Subsequent source changes are compared with the prior incoming source value to avoid repeated false conflicts.

## Scope limits

The MLX example uses cited public history with explicitly illustrative forecasts. Production is a proxy for payable sales, imputed price is not realized selling price, mine life and closure are assumptions, and the current reference quote is missing. It does not establish an actionable valuation or integrated three-statement forecast. Recalculation was tested with LibreOffice, not interactive Microsoft Excel automation. Public CI has no X credentials; X authentication remains per user.
