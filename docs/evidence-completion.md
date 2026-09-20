# Evidence completion contract

The investing skill requires a question-level coverage register alongside every substantive report. Save it with `uv run invest coverage-review private/coverage-review.json`. This validates references and progress dependencies and saves an immutable, content-addressed review under the company. Dossier links retain every review. It does not certify that an analyst's interpretation is correct.

The request has `company_id`, timezone-aware `researched_at`, `mode` (`research_update` or `re_export`), actual `web_checked_at`, actual `x_checked_at`, `x_status` (`searched`, `failed`, `not_run`), `x_scope`, and `items`. Re-export retains actual research times rather than substituting export time.

Saved reviews include SHA-256 hashes of the referenced analysis/model files. A changed current-view file produces a distinct review rather than silently making the previous declaration refer to a new document. Completeness requires an analyzed entry for every category, completed applicable stages, no open gaps and actual web/X checks; it remains a structural declaration rather than independent certification.

Each item has `category`, `question`, `period`, `source_ids`, `stages`, `conclusion`, `model_implication`, `gap`, `next_step`, optional `analysis_path`, optional `model_path`, `fact_ids`, and `reconciliation`. Categories are `filings`, `management`, `industry`, `peers`, `counterevidence`, `x`, `regulatory`; record each, including unavailable or immaterial categories with an explanation. Multiple items per category support period-by-period or question-by-question detail.

Stages must explicitly contain `captured`, `read`, `extracted`, `reconciled`, `analyzed`, `model_used`, each set to `done`, `partial`, `pending`, or `not_applicable`. A captured document does not automatically advance another stage. Reading is a prerequisite for completed analysis; model use also requires reconciled facts and a model path. Incomplete stages require a gap and next action. Use not_applicable for genuine nonnumeric questions, not missing financial work. Explain applicability in the conclusion.

Source IDs and artifact paths must exist. Fact IDs must belong to this company and cited sources. Social evidence cannot establish model facts. All reviewed sources still need semantic inspection and the Excel template's numerical/visual checks. A register is an analyst declaration with structural validation, not an automatic research-quality score.

Before changing the current reader report, preserve its previous edition. Use the seven reader sections in the skill. Run `uv run python scripts/check-reader-report.py companies/<id>/investment-review.md` before PDF export. This checks structure and the Excel link, not financial correctness. Add the coverage review to the dossier and accumulating brief; deliver the short readable report by default.
