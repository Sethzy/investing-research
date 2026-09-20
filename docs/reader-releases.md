# Matching reader editions

Each edition contains a reader Markdown/PDF, a synchronized `model.xlsx`, `model.json` and `inputs.json`, a `coverage.json` evidence review, and `release.json`. Technical JSON is supporting material; the user reads the story and opens Excel.

`release.json` has `schema_version: 1`, `company_id`, timezone-aware `research_cutoff`, `valuation_class` matching the model purpose, and `files`. The file roles are `report`, `workbook`, `model`, `inputs`, `coverage`; each records a relative `path` and the actual file's `sha256`. Keep the model snapshot files together. Compute hashes after authoring and reviewing the final files, never to conceal an unexplained change. Use the evidence review saved by `coverage-review`; its artifact hashes must include the final reader Markdown and model JSON. Reference both through the review items' `analysis_path` and `model_path`. This binding does not require falsely marking model use complete.

Include the model comparison as a simple Markdown table with rows `| Bear | 0.45 |`, `| Base | 0.79 |`, `| Bull | 1.39 |` (replace example values with accepted results). Label units and whether results are illustrative directly above it. The exporter verifies these values to two decimal places. Other narrative figures still need source review.

Run `uv run python scripts/export-reader-report.py EDITION/review.md --output EDITION/review.pdf`. The exporter requires `release.json` beside the report, or an explicit `--manifest` path. It rejects changed files, mismatched companies, dates, model/workbook inputs, wrong links and scenario values. It accepts incomplete research as an explicitly limited briefing; hashes and declared coverage do not establish truth or a recommendation.

Update the current-edition README only after calculation and visual review. Link older editions; never overwrite them. A re-export preserves the original research dates. For substantive research, update the evidence register only for sources actually checked and preserve failed searches.

## Decision editions

All newly authored investment opinions use an additional `decision` object in the release manifest. It is mandatory for presentation-v4 workbooks. Existing historical editions remain valid. Fields are `opinion` (Buy/Hold/Sell/Not rated), `as_of` (research-cutoff date), `horizon`, `rationale`, `next_checkpoint`, `previous_assessment`, `change_triggers` (nonempty list), and `blocker` (required for Not rated).

The first `##` heading must be `Executive summary and investment opinion`; include `**Opinion: Not rated**` (or the supported rating) and the declared text fields verbatim within that section. This binds the human-readable summary to the review record. Definitive price-based ratings require a model classified as valuation; an illustrative operating sensitivity cannot support one. Classification and consistency alone never establish investment suitability or evidence quality.

The v4 Decision sheet is a diagnostic: price paid versus selected operating model, carrying-value inventory and historical cash yields. Its residual is not a project's valuation, and the historical yields are not normalized forecasts. Follow the skill's asset, cash-flow, funding and contrary-case research checks before reaching an opinion.

## Conditional valuation companion

For quantified questions that do not yet justify changing the accepted operating forecast, use the investing skill's `valuation-questions` reference and maintained module. A reader release may include `valuation_questions` with hashed `inputs`, `results` and `workbook` entries pointing to one directory containing `inputs.json`, `results.json`, `questions.xlsx`. The exporter validates the formula/input template, independently computed outputs, company, currency and date, and permits this explicitly registered workbook link alongside the mandatory operating workbook. It does not promote valuation readiness or alter the rating. The CLI generator independently recalculates with LibreOffice before accepting its output.

Preserve the prior edition and record new discoveries in research history. Verify each companion sheet visually. Direct workbook edits do not synchronize into the operating model; update the companion JSON and generate a new directory. Inputs and calculations are published for inspection, not as undisclosed project estimates.
