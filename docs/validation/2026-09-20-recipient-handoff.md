# Recipient handoff validation

A fresh public clone was installed in a temporary directory on macOS. No existing preferences, company state, portfolio or browser profile was copied into it.

- Locked dependency installation and CLI help passed.
- Git, uv, Node, Python 3.12 and a LibreOffice engine were already available on the host. This verifies a fresh project installation, not automated provisioning of a blank computer.
- The synthetic finite-mine example produced a report and workbook. LibreOffice independently recalculated operating, valuation and sensitivity outputs for all three cases; validation passed.
- Fresh-clone `doctor` initially failed because preferences did not exist. Fixed to return installed capabilities with `setup: pending` and instructions to run setup. Offline diagnostics do not create settings.
- A premature `doctor --live-x` now returns `setup_required` without reading a browser. This deliberate nonzero result is covered by regression tests.
- 17 onboarding tests passed, including the two new first-run checks. Ruff, setup-skill validation and local documentation link checks passed.
- The README now leads with the latest investor PDF and both accurately described workbooks. Reading the pack requires no research installation. The investor guide requests independent feedback on cash quality, assumptions, missing evidence and the investment decision.
- The install prompt includes preferred X handles, the recipient's own login and the separate LibreOffice prerequisite. Setup preserves pending authentication and scheduling status.

Not verified for a different recipient: their OS installation, browser-cookie access, live X response or scheduled execution. These remain interactive onboarding checks. The public artifacts remain the unchanged, audited 20 September valuation-questions edition; this handoff update does not refresh financial research or X captures.
