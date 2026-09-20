# Excel detail, Markdown research

The user reads Markdown dossiers and follows their Excel links for detailed analysis. Editable workbook assumptions drive native formulas. Explicit synchronization recalculates, independently checks and publishes an immutable workbook/results/Markdown version; user edits never silently leave a report current.

Implementation units:

1. Professional workbook layout: separated source history, assumptions, active operating schedule, equity bridge, sensitivity formulas and checks. Preserve finite-life/ownership conventions and missing-data labels.
2. Workbook workflow: create, synchronize, status and three-way source refresh. Accept edits to mapped inputs; reject changed model formulas pending code/model review. Preserve immutable versions and user overrides.
3. Markdown integration: clearly link detail workbook and snapshot, display reconciliation/coverage limits and detect changed working workbook.
4. Public MLX worked example: source-linked historical statements and operating facts with clearly identified forecast assumptions. Do not imply a completed reserve-backed valuation or full integrated three-statement forecast.
5. Adopt pinned upstream modelling/audit references with licences, update user guidance, review and publish.

Verification: edit commodity price and select each scenario, independently recalculate Excel and compare all operating/valuation/sensitivity results; confirm Markdown uses the synchronized values. Test refresh preservation/conflicts, missing recalc engine, invalid inputs, stale caches, changed formulas, unsafe workbook structures, interrupted publication, history reconciliation and clean standalone installation. Visually inspect workbook output and charts. Retain existing regression suite and public CI.
