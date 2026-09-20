# MLX template reference audit

20 September 2026. Presentation version 2. Workbook SHA-256: `094641e69087c127b01b8936fbc77aec8a52a7863158a6b26f4a4ae97f41f60c`.

This public worked example retains its original illustrative inputs. It is a formatting reference, not the latest private MLX research or a recommendation. The previous workbook hash was `ab74c5afd84ccee0ff9ee1ea797447f2cc415728f13b4b8edd7a45b158d8ce23`; Git retains that edition.

| Sheet | Verification | Result |
|---|---|---|
| Summary | Headline results, wrapped notes, both charts and printable bounds | Passed |
| Assumptions | Case selector, complete case blocks, input comments and page breaks | Passed |
| Historical | 73 source-linked rows, original URLs/page fragments, repeated print headings | Passed |
| Operating | All forecast columns and calculated cash flows, totals and closing note | Passed |
| Valuation | Enterprise/equity bridge, per-share result, units and unavailable quote | Passed |
| Sensitivities | Nine cells per case recalculate; central value ties; grid and helpers readable | Passed |
| Checks | All six checks pass; no cached Excel error cells | Passed |
| Readme | Instructions and all limitations readable; paragraphs preserved at page breaks | Passed |

Methods: artifact-tool worksheet renders and inspection of all 17 LibreOffice PDF pages. The 254 formula expressions and public example assumptions are unchanged. All three scenarios and sensitivities passed independent Python comparison after LibreOffice recalculation. All 73 saved hyperlinks and 178 source comments match their recorded provenance. The hidden model manifest remains intact.

Native Microsoft Excel UI was not directly tested. Source links were compared with recorded URLs, not refetched; this audit does not establish current source accessibility or close financial research gaps. Some financial schedules require horizontal scrolling at normal zoom.

The [skill template reference](../../.agents/skills/investing/references/excel-template.md) links this [workbook](model.xlsx), [summary preview](template-summary.png) and the maintained generator. Complete its per-sheet checks for every new export. Read the [matching Markdown report](report.md) for this example's assumptions.
