# Financial modelling references and attribution

The workbook design adapts public modelling guidance from [Anthropic financial-services](https://github.com/anthropics/financial-services). We retain the relevant original reference files verbatim so a new user can inspect their provenance without installing a personal skills repository or a financial-data integration.

## Pinned source

- Repository: `anthropics/financial-services`.
- Commit: [`fca3cc8e6c5692ba576b46d7c4783b8443c2a223`](https://github.com/anthropics/financial-services/commit/fca3cc8e6c5692ba576b46d7c4783b8443c2a223), committed 2026-09-18.
- Pin verified against both the GitHub commit API and recursive tree API on 2026-09-20.
- Licence: Apache-2.0; the original [LICENSE](../vendor/financial-services/LICENSE) accompanies the files.
- File URLs and SHA-256 checksums: [provenance.json](../vendor/financial-services/provenance.json).

| Verbatim reference | Principles adapted here |
|---|---|
| [DCF model](../vendor/financial-services/plugins/vertical-plugins/financial-analysis/skills/dcf-model/SKILL.md) | Formula-driven projections, separate assumptions, source comments, scenario analysis, fully calculated sensitivity grids and an executive summary. |
| [Three-statement formulas](../vendor/financial-services/plugins/vertical-plugins/financial-analysis/skills/3-statement-model/references/formulas.md) | Statement relationships and reconciliation logic where the evidence supports them. |
| [Formatting](../vendor/financial-services/plugins/vertical-plugins/financial-analysis/skills/3-statement-model/references/formatting.md) | Visible input/formula distinction, units, readable negative values, totals and checks. |
| [Spreadsheet audit](../vendor/financial-services/plugins/vertical-plugins/financial-analysis/skills/audit-xls/SKILL.md) | Detect overwritten formulas, broken references, inconsistent logic and failed financial reconciliations. |

These files are **reference material**, not automatically invoked agent instructions. The bundled investing workflow remains the entry point. References to other skills, integrations, tools or approval checkpoints in the retained upstream text do not install those dependencies or change this project's authorized workflow. No upstream workbook engine or completed MLX valuation is claimed: the repository's workbook and synchronization code implement the adapted conventions.

## Deliberate adaptations

1. **Markdown is the reading surface; Excel is the detailed model.** Research conclusions, evidence gaps and validation status are readable without opening Excel. The Markdown model report links to the precise workbook snapshot supporting its numbers.
2. **Editable workbook assumptions are canonical after creation.** JSON is a source/import format and a snapshot of accepted assumptions. A refresh compares prior source inputs, the edited workbook and new source inputs, retaining user overrides and recording conflicts.
3. **Formula edits require review.** Synchronization accepts supported assumption edits. It rejects unsupported formula or structural changes rather than silently overwriting them or endorsing a customized model it cannot independently validate.
4. **MLX uses finite-life cash flows.** Generic perpetual-growth terminal-value guidance is inappropriate for an unsupported mine-life forecast. Assumed life and closure costs are labelled; ownership is applied once. No reserve-backed valuation is implied by the illustrative example.
5. **Historical statements are not an integrated forecast.** The MLX example supplies sourced comparative financial history and reconciliation checks. It does not fabricate forecast balance sheets, debt schedules or cash-flow statements to make the workbook look complete.
6. **No data API keys.** Historical facts come from public issuer disclosures, with dates, units and provenance. Missing quote, diluted-share or operating evidence remains a visible limitation.
7. **Independent calculation checks.** Supported workbook scenarios are recalculated with LibreOffice and compared with the Python implementation before a synchronized snapshot is treated as verified. Formula parity does not validate the economic assumptions or certify investment value.

For the user workflow, see [Excel and Markdown models](excel-models.md). For the evidence and limitations of the worked company example, see [MLX model notes](../examples/MLX-MODEL-NOTES.md).
