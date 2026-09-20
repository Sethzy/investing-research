# Implementation review and live verification

Date: 2026-09-20. Scope: standalone application, vendored X adapter, public-source collection, local financial models, portfolio checks, host-agent workflows and handoff documentation.

## Review method

Applied the personal-skills `ce-work` execution workflow, `thermo-nuclear-code-quality-review`, `overengineering-review`, and `security-review`. Independent reviewers inspected workflow and security boundaries; a separate finance pass checked model/workbook/portfolio behavior. Review findings were reproduced, fixed and regression-tested. The referenced `ce-code-review` wrapper was not present in the personal-skills or installed skill directories; the available personal review skills supplied the actual review instead.

## Findings and fixes

| Finding | Resolution and evidence |
|---|---|
| Metadata-only JSON could qualify as an investment model | Recommendations now require the input snapshot, validate it, recompute outputs, reject synthetic/illustrative models, and match the quoted price/date |
| Incomplete collection could finalize as no change | Pending operations and missing collection completion prevent finalization; subsequent collection explicitly marks interrupted receipts and retries coverage |
| A source could corroborate itself | The candidate is removed from corroborating references; complete non-social evidence is required |
| Two pending runs could announce the same event twice | Finalization deduplicates against canonical committed reviews, preserves receipts, and rejects conflicting decisions |
| Browser-imported X could bypass social-source restrictions | X/Twitter URL imports retain social classification regardless of capture method |
| PDF parsing had no execution/resource boundary | Isolated parser process, timeout, memory monitoring, page/output limits and temporary staging; original source preserved on failure |
| Trading/model currencies could disagree | Actionable recommendations require model currency to match the company's trading currency |
| Installing LibreOffice could not upgrade an old unverified run | Explicit `validate-workbook` command writes a dated validation record while retaining the original model snapshot |
| Workbook checks depended on JSON scenario order | Verification now matches Summary scenario labels and rejects duplicate, missing or unknown labels; canonical-input reload and real MLX workbooks pass |
| Unknown risk-policy fields could silently omit a limit | Invalid policies, currencies, sectors and malformed holding values are rejected |
| A shared query's checkpoint changed midway through one run | Collection uses a start-of-run checkpoint snapshot, so shared queries are fetched once and associated with each relevant company |
| A failed model build could permanently block the same inputs | Models build in an unpublished staging directory and publish atomically; failed and legacy incomplete artifacts are retained without preventing a retry |

No unresolved substantive finding remained in the independent workflow/finance/security review scopes after focused verification. This is evidence of the checks performed, not a guarantee against all defects or upstream changes.

## Live evidence

- Final local suite: **73 tests passed**; Ruff and Git whitespace checks passed. Tests cover numerical fixtures, workbook edits/recalculation, source/authentication failures, parser limits, interruption recovery, event deduplication, currency/provenance gates and portfolio constraints.
- Standalone Bird keyword, date-filtered and exact-post capture passed using the user's own Chrome session. Exact post text and whole-thread completeness are distinguished.
- MLX: captured three annual reports and eight quarterly reports, imported 23 source-linked facts, reviewed collected X/report candidates, produced a dossier and baseline/downside sensitivity workbooks.
- Microsoft: exercised the same collection/review/fact/dossier path, including the dated official earnings release and 19 source-linked facts. No claim of a completed Microsoft valuation.
- Docling: converted one financial-statement page into a 39-row by 4-column table with page/bounding-box provenance. The test also passed inside the isolated extraction worker.
- Both MLX workbooks independently recalculated successfully in LibreOffice, including revalidation after serialized input reload.
- Fresh checkout: locked dependency install, fresh local configuration, live Bird doctor, synthetic mine model, scenario fork/model, explicit-FCF model, workbook revalidation and test suite passed with API/session-key environment variables removed. Browser authentication still used the current user's own session; a different person's machine was not available for testing.
- Installed wheel: imported from `site-packages` outside the source checkout, contained vendored Bird/licence files and completed a live X search.
- Dependency audit reported no known vulnerabilities in the installed environment at the time of the check. Provider availability remains separate from dependency scanning.

## Operational boundaries

The code is an agent-operated workspace. The subscribed host performs research judgement and follows the bundled skill; the CLI alone collects evidence and leaves it pending review. No model API daemon or trading execution exists.

Daily monitoring was configured through the supported Codex host for 08:00 Asia/Singapore. **The first scheduled host execution is pending**, so the scheduled path must not yet be called verified. That first run is instructed to record its outcome. Interactive and fresh-install browser access passed; sleep, usage limits and browser-session changes can still affect future runs.

MLX outputs are explicitly **illustrative sensitivity analysis**: imputed price/production proxies, assumed finite horizons and closure costs, stale balance-sheet inputs and no verified current quote. They cannot justify an actionable recommendation. Real portfolio sizing remains blocked until the user supplies their own holdings, quotes, session dates and risk limits.

## Post-deployment monitoring and recovery

- Owner: the workspace user and the scheduled host-agent workflow.
- On the first scheduled run, and after browser/dependency updates, run `doctor --live-x`, inspect `status`, and resolve pending review packets.
- Healthy: completed source operations, explicit bounded coverage, reviewed receipts, no duplicated alerts, and successful workbook parity when models change.
- Failures: `collecting` receipts left by interruption, `degraded` coverage, authentication failure, parser timeout or failed workbook validation. Preserve these records, retry/re-authenticate or use an explicitly labelled browser capture; do not advance failed-source checkpoints or substitute invented financial facts.
- Pause host scheduling if repeated failures prevent useful research. Pin/restore the previously working dependency version and rerun the acceptance checks before resuming. Keep credentials and user data out of tracked source and handoff archives.
