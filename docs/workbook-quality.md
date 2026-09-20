# Workbook presentation and financial audit

This is a required step in the bundled investing workflow whenever a workbook is created or materially changed. The project uses its portable workbook generator; recipients do not need a personal skills checkout.

## Before delivery

1. Recalculate all scenarios and sensitivities with `excel-sync`. Confirm financial parity, units, ownership, quote dates and evidence limitations. Never use visual polish to imply uncertain assumptions are verified.
2. Render or open every visible sheet. Review Summary, Assumptions, Historical, Operating, Valuation, Sensitivities, Checks and Readme. Inspect both the normal sheet view and print/export layout when sharing a PDF. Review at normal zoom: fitting a wide sheet onto a printed page does not establish on-screen readability. Keep the summary compact and break printed pages between complete scenario tables and narrative paragraphs.
3. Check unclipped labels, figures and source notes; consistent number precision; readable percentages and dates; sufficient column widths; and sensible row heights. Keep input cells blue, cross-sheet links green and calculations black. Use subtle fills and top borders for totals, rather than borders around every cell.
4. Check charts render, titles and axes name the units, and forecast periods are explained. Shorter scenarios have zero-padded periods; flat cash after the selected horizon is not an additional forecast. Ensure chart placement does not cover cells or extend beyond print areas.
5. Ensure long tables retain header rows when printed, sources remain clickable and comments retain provenance. Keep the formula/input contract intact. Formatting changes must not convert units, hardcode outputs or alter financial formulas.
6. Record the workbook hash, rendering method, sheets reviewed, finance-check result and unresolved presentation limitations in the research memo or companion audit note. Do not mark visual review passed if only numerical tests ran. If rendering is unavailable, state that visual review is pending.
7. After a repair, regenerate/synchronize and inspect the affected sheets again. Deliver the Markdown report and matching Excel snapshot together.

The CLI validates the calculation contract; it does not itself certify visual quality. Codex performs and records this presentation review. Use `status` to distinguish later working-copy edits from the published snapshot.

## Local PDF preview

For a previously synchronized, trusted workbook, create a preview in an ignored folder:

```sh
mkdir -p private/workbook-preview
soffice --headless --convert-to pdf --outdir private/workbook-preview examples/mlx/model.xlsx
```

Inspect the PDF or rendered page images with Codex's available file tools. Close an existing LibreOffice session if conversion does not run. The PDF is a visual preview; Excel remains the editable detailed artifact. Do not use PDF export as a substitute for `excel-sync` financial verification.
