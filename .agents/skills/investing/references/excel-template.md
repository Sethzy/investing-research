# Excel template and release standard

Read this reference before creating, refreshing or delivering an investing workbook. It applies to the repo's finite-mine and cash-flow models. The visual standard is reusable; another company's economics may require a reviewed model extension.

## Canonical reference

- [Worked workbook](../../../../examples/mlx/model.xlsx): open this to inspect the actual formatting, editable cells, charts and sheet order. This is an illustrative MLX example, **not a blank template or a current recommendation**. Its financial inputs are deliberately separate from later private research editions.
- [Summary preview](../../../../examples/mlx/template-summary.png): quick visual reference; inspect the other sheets in the workbook too.
- [Reference audit](../../../../examples/mlx/presentation-audit.md): checked edition, hash, methods and limitations.
- [Maintained generator](../../../../src/investing_research/excel_layout.py): authoritative reusable layout, default presentation version 2, with optional version 3 for comparable historical analysis and version 4 for the decision diagnostic. Generate with `excel-create` using the subject company's reviewed inputs. Do not copy MLX numbers, sources or assumptions into another company.
- [Calculation workflow](../../../../docs/excel-models.md) and [delivery checklist](../../../../docs/workbook-quality.md).

The generator and versioned calculation contract own the file structure. Apply layout fixes there, then regenerate and synchronize a new snapshot. Do not hand-format just the delivered file and leave future exports broken. Preserve old snapshots and compatibility when changing labels or formulas. A new company, longer text or more forecast years still needs its own visual review.

## Appearance to preserve

Use Arial, navy title bars, restrained teal section headings, white backgrounds and muted explanatory notes. Keep gridlines hidden. Blue identifies editable assumptions; green identifies cross-sheet links; black identifies local calculations. Give totals a subtle fill and top border. Retain explicit currency/unit labels, parentheses for negative numbers and consistent decimal precision. Display rates as percentages. Preserve the existing contract's ISO date text inputs.

Keep the Summary to a compact reading width (approximately 900 pixels at 100% zoom). Long tables may scroll horizontally, with frozen identifiers and periods. Wrap narrative text within bounded cells and allocate enough height; do not depend on text overflowing into empty cells. Use readable type rather than shrinking everything to fit. Charts must remain within the sheet's print area and outside populated cells. Preserve underlying values when shortening a displayed amount to millions.

## Verify every sheet, one by one

| Sheet | Required inspection |
|---|---|
| Summary | Correct company and selected case; headline values tie to Valuation; currency visible; notes wrap; both charts and their axes fit; shorter-case padding is explained in Readme. |
| Decision (optional v4) | Dated quote/share proxy; market-to-model bridge; separately sourced investment carrying amounts; residual never called project value; no double subtraction of other assets; matched annual cash periods and guarded yields/multiples; both printed pages readable. |
| Assumptions | One functioning case selector; all three complete case blocks; editable cells and provenance comments retained; periods chronological; percentages and dates readable; no scenario split across printed pages. |
| Historical | Every input fact retained with period, value, units, ownership basis, date, source URL and page; links match the recorded sources; filter and frozen identifiers work; printed headers repeat. |
| Analysis (optional v3) | Comparable periods and reporting basis; source-linked history; profit and cash bridges reconcile; both charts and print pages readable; ratios do not imply normalized earnings. |
| Operating | Selected drivers feed the formulas; all forecast periods, ownership, tax, closure and cash-flow rows inspected; totals readable; no clipped values or notes. |
| Valuation | Enterprise-to-equity bridge, cash, debt, shares and per-share result tie; missing reference quote remains unavailable; units and limitations visible. |
| Sensitivities | Every grid cell recalculates; central cell ties to the active valuation; row/column drivers understood; heatmap readable; calculation helpers retained and legible. |
| Checks | Every applicable check passes after fresh recalculation; scan the entire workbook for error cells. PASS covers calculation checks, not the quality or completeness of research. |
| Readme | Concise instructions, input legend and all model limitations readable; no truncated paragraphs or broken page boundaries; no developer logs or setup code in the reader-facing sheets. |

Check the hidden model manifest as well: formula/input maps match the trusted generator and it remains hidden. Check hyperlinks and comments against the input provenance. A matching URL proves the link was preserved; it does not prove that the website is currently accessible or its claim correct.

## Repeatable structural check

From the checkout root, run the bundled [audit helper](../scripts/audit_workbook.py) on the synchronized snapshot:

```sh
uv run python .agents/skills/investing/scripts/audit_workbook.py companies/<id>/models/<run>/model.json --recalculate
```

It validates the snapshot, formula contract, source hyperlinks (including PDF page fragments), original provenance comments, cached errors and workbook checks. `--recalculate` freshly evaluates all three scenarios. It intentionally leaves visual review pending and does not refetch source websites. Save the JSON in an ignored audit folder and complete the visual checks separately.

## Delivery gate and audit record

1. Validate the immutable snapshot and freshly recalculate bear/base/bull, operating outputs and every sensitivity against the independent engine. Check formula errors and preservation of supported inputs, source comments and links.
2. Render/open every visible sheet at ordinary viewing size. For long sheets, inspect all sections, including the final rows. Inspect every PDF page if a workbook PDF is delivered, including footers. Correct issues and repeat the affected checks.
3. Record workbook SHA-256, presentation version, date, methods, each sheet's result, links/comments checked, formula count, scenario results and limitations in a companion audit. Distinguish **passed**, **failed**, and **not checked**. Never fill a visual PASS from a numerical test.
4. Deliver the matching readable report and Excel snapshot, keeping older editions. Do not declare formatting guaranteed across applications: name the render/recalculation methods and say if native Microsoft Excel was not opened.

No delivery approval solely because the generator ran, tests passed, a preview looked good, or the reference workbook previously passed. The actual new file is the release candidate.

Presentation v3 adds the optional historical Analysis sheet. Use `write_excel_model(inputs, path, presentation_version=3)` when two complete comparable periods are available, then the ordinary `excel-sync` contract. Otherwise retain v2 and explain the missing comparison. This changes presentation and historical exhibits, not forecast assumptions.

Presentation v4 retains Analysis and adds the Decision sheet using `write_excel_model(inputs, path, presentation_version=4)`. Read [investment-decision.md](investment-decision.md) for required historical metrics and exclusions. The [decision edition](../../../../examples/mlx/editions/2026-09-20-decision/model.xlsx) is the worked reference for this optional exhibit. The original layout versions stay reproducible; refresh preserves the selected version.
