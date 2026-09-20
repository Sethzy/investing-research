# Synthetic append/update example

All numbers and company hypotheses in this folder are synthetic. No live X call or MLX investment conclusion is represented.

- [Living thesis and catalyst history](research.md): original expectation remains alongside the revised one; both estimated event dates remain in the record.
- [Model change report](update/report.md): compares [baseline](baseline/report.md) and [revised](revised/report.md) snapshots.
- [Funding and dilution report](funding/report.md): links the native formula workbook.

The public export retains the demonstration receipts; their workspace-relative paths describe the original synthetic workspace. Use the report links here to navigate this export. Model `output_dir` fields were made repository-relative for portability. Run `uv run python scripts/demo-research-updates.py` to recreate the operational workspace under ignored private data; rerun it to exercise exact-retry idempotency.

Visual audit: the funding workbook was recalculated in LibreOffice and compared with Python. Its Readme and three scenario sheets were rendered and inspected. Interest is on opening debt; financing is at year end; no interest tax shield or automatic funding plug is assumed. This is not a fully integrated three-statement forecast.
