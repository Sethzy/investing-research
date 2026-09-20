# Decision edition verification

The [MLX decision edition](../../examples/mlx/editions/2026-09-20-decision/README.md) begins with a dated executive opinion and adds a market-to-model bridge, investment carrying inventory, historical cash-flow cross-check, linked adverse cases and later Alphamin primary disclosure. The operating forecast inputs and all three per-share results remain unchanged. Current opinion: **Not rated**, with specific decision blockers and revision conditions.

## Verification performed

- 162 tests passed. New cases cover real LibreOffice formula evaluation, missing quotes, double-count protection, comparable reporting basis, appended inventory selection, incomplete latest data, refresh preservation, formula tampering and executive-opinion consistency. Ruff and skill validation passed.
- All three operating cases and every sensitivity were freshly recalculated against the independent Python engine. The final workbook has 335 protected formula cells, 160 historical source links and 180 provenance comments; no cached formula errors or structural issues were found.
- The Decision equity bridge ties to Valuation. The reference equity calculation is A$1,905.744m; disclosed financial assets and associates total A$92.281m. The residual after the central operating illustration and that carrying inventory is A$1,135.595m, explicitly not Rentails value or a price target.
- All ten visible worksheets were inspected through LibreOffice print rendering. Decision was also rendered at ordinary size with ArtifactTool. Print scaling and page breaks were corrected in the maintained generator, then the delivered recalculated workbook was rechecked. Updated Readme limitations were inspected. Native Microsoft Excel was not opened.
- All 25 reader PDF pages were rendered and inspected. Sparse citation-only pages and a split peer paragraph were corrected; first-page opinion and source links remain visible. The report, workbook, inputs, model and coverage hashes match the release record. The detailed machine-readable result is [verification.json](../../examples/mlx/editions/2026-09-20-decision/verification.json).

## Evidence and limitations

The announcement index, June resource disclosure and later Alphamin Q2 management discussion were checked in this update. MLX investment tables were visually checked against the original half-year PDF. Three fresh X searches retained a capped noisy query plus narrower company and contrary-supply results; source access does not imply complete threads or exhaustive coverage. The reader states actual search dates and retains selected attributed excerpts.

This upgrade does not complete a supported asset NAV, normalized peer valuation or Rentails funding model. Carrying values are not current liquidation values, June issued shares remain a dilution proxy, and historical cash ratios are not normalized forward yields. The original operating illustrations stay labelled as such. Earlier published editions and local dated research revisions remain intact.
