# Resolve uncertainty with conditional analysis

Apply after the readiness review identifies a material unknown. Do not stop at a missing-input list. Re-read the exact revenue, tax, cash-flow, capital, options and subsequent-events notes. Classify each gap as undisclosed, stale, inconsistent or not yet analyzed. Correct earlier omissions explicitly and preserve the previous edition.

## Cash quality

Reconcile reported operating cash to cash before working-capital/provision movements. Strip investment income and identifiable one-offs when investment assets are valued separately. Distinguish accrued income from cash interest. Show the treatment of financing interest, lease additions/principal, corporate costs, taxes and all capital spending. Use disclosed current taxes or an explicit tax approximation, not cash tax timing alone. Do not call two adjusted historical periods a through-cycle forecast. Do not annualize the latest strong half-year without defending volume, price, cost, tax and capital assumptions.

## What must be true?

For finite assets, show cash/life combinations with closure, ownership and discount timing. Solve the recurring operating cash required by the reference price after separately assessing cash, debt and investments. Report a conditional value, not a target. A resource is not a reserve; a historical life estimate must be depleted from its effective date before it supports a forecast. A life stress test is permitted if clearly identified as an assumption.

For omitted developments distinguish:
1. Annual post-tax cash needed for economic break-even at an assumed capital cost.
2. Annual cash needed to explain a stated residual after an independently specified operating case.
3. Funding capacity after corporate reserves, commitments and debt, with explicit ownership and no imaginary financing plug.

Test delay and cost overrun. If the residual is negative, the development economic hurdle remains zero NPV; do not imply the project can destroy unlimited value. Investment haircuts are assumptions, not appraisals. Recheck delistings, corporate actions, FX, offers, tax and liquidity before treating a carrying amount as realizable value. Do not count an investment and its redemption proceeds twice.

## Reusable implementation and worked reference

Use the maintained [valuation questions module](../../../../src/investing_research/valuation_questions.py), [worked inputs](../../../../examples/mlx/editions/2026-09-20-valuation-questions/questions/inputs.json) and [workbook](../../../../examples/mlx/editions/2026-09-20-valuation-questions/questions/questions.xlsx). Run `uv run python -m investing_research.valuation_questions INPUT NEW_DIRECTORY`. The input contract requires two chronological annual periods, one currency with money/shares in millions, explicit driver provenance and limitations. Replace every company-specific value and assumption. The fixed matrix axes are illustrative stress tests; choose relevant axes in a reviewed template extension for a different scale of business.

This is a companion diagnostic, not an accepted operating-model snapshot. Preserve the existing forecast unless new inputs justify changing it. Recalculate in LibreOffice/Excel, compare against `calculate()`, check all formulas and inputs against the template, and visually inspect each sheet. Ship inputs, calculated results and a hashed companion record alongside the reader release. Never pass this file to `excel-sync` as if it were the operating workbook.

In the report explain the new finding, what it changes, what remains uncertain and the next observable test. Keep the executive opinion separate from the calculation. No Buy/Hold/Sell from a stress grid alone. Saved X evidence keeps its actual check dates; a valuation follow-up is not a fresh social sweep.

## Patterns rechecked, 20 September 2026

- [Dexter write-memo](https://github.com/virattt/dexter/blob/main/src/skills/write-memo/SKILL.md), steps 3, 5, 6: coherent driver cases, priced-in expectations, observable falsifiers. These are instructions, not a project calculation engine. Do not import forced probabilities or alter assumptions to meet its asymmetry heuristic.
- [Financial-services task3 valuation](https://github.com/anthropics/financial-services/blob/main/plugins/vertical-plugins/equity-research/skills/initiating-coverage/references/task3-valuation.md): reconcile asset values to equity and cross-check valuation methods. Reuse the pinned, attributed guidance already vendored. Do not import perpetual growth into finite mines.
- [AI Hedge Fund current Buffett signal](https://github.com/virattt/ai-hedge-fund/blob/main/hedge_fund/signals/buffett.py): cash generation, capital allocation and financial strength. The current file is a persona prompt; DeepWiki returned legacy `src/agents/valuation.py` and `charlie_munger.py` paths, so its claim of current reusable owner-earnings code was not accepted. Avoid persona votes and a new runtime.
- FinanceToolkit remains the existing mathematical dependency; no extra provider, orchestrator or API key is needed. Docling and Bird retain extraction/capture roles, not valuation authority.

The conditional equations here are small local business logic, not copied upstream implementation. These patterns improve disciplined analysis; they do not settle undisclosed mine/project economics.
