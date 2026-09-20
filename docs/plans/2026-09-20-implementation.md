# Standalone implementation plan

Approved scope: [specification](../superpowers/specs/2026-09-20-investing-research-design.md).

## Units and verification

1. Package and contracts: Python CLI, validated local JSON, atomic versioned storage, locks, portable configuration. Verify fresh installation and input rejection.
2. X adapter: retain coherent vendored Bird code/licence, authenticate with the user's browser, search and exact-post capture. Verify live MLX searches, date windows, sanitized failures, and standalone package resources.
3. Public evidence: bounded HTTPS downloads, report-link discovery, immutable snapshots, PDF page text, optional Docling. Verify live annual/operating reports and deterministic local fixtures.
4. Financial models: offline FinanceToolkit primitives, finite-life and explicit-FCF scenarios, sensitivity/reverse valuation, editable formula workbooks, chart/report outputs. Independently check numerical fixtures and LibreOffice parity.
5. Workflow/state: per-source checkpoints, deduplication, collection receipts, agent review packets, material event decisions, standalone dossiers. Verify repeated runs, source failures, interruption recovery, source-to-fact traceability.
6. Portfolio/recommendations: dated manual holdings, explicit risk policy and freshness gates, target/incremental distinction. Verify cash/sector/position limits and stale data rejection.
7. Agent integration and handoff: repository instructions, reusable local workflow skill, runnable README, host scheduling prompt, synthetic demo, clean-clone test. No key-backed service, wiki, dashboard, or trading execution.
8. Quality gate: personal-skills code-quality, overengineering, and security review, fixes, regression tests, repeat focused review, validation record, final commit.

Workers own disjoint adapter/model files; the coordinator owns contracts, workflow, CLI, packaging, integration, documentation, and commits. Third-party source stays separate with provenance and licences. No external posting or messaging.
