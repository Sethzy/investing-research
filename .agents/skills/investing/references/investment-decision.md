# From research to an investment opinion

Use for company initiations, substantive updates and a request for Buy/Hold/Sell. Put the executive summary immediately after company, ticker and as-of date, before background or research history. Aim for one readable page; follow it with the supporting analysis.

## Executive summary

State in this order:

- **Opinion:** Buy, Hold or Sell, with a one-sentence investment rationale. If material unresolved evidence could reverse the conclusion, state **Not rated — wait for evidence**, explain the specific blocker and give a next decision checkpoint. Do not use Hold to conceal insufficient research or failed tools.
- **Price and horizon:** dated reference quote, currency, rating horizon and separate valuation date. Distinguish an analyst-selected horizon from the user's preferences.
- **Valuation and return:** supported value range, central value if justified, and prospective return over the stated horizon. Label present fair value separately from a future price target. Include dividends only when supportable; do not count retained cash twice. If valuation is unavailable, say so rather than turning a partial operating sensitivity into a target.
- **Why this opinion:** the two or three findings that determine the decision, with nearby citations. Explain what appears priced in and what evidence supports a different outcome; never invent consensus.
- **Principal downside and uncertainty:** the most important way the thesis fails, including financing/dilution where material. Confidence is an explained judgment, not an LLM-generated probability.
- **What changes the rating:** observable evidence or price conditions, next dated catalyst/checkpoint, and previous rating/date with the reason for any change. Separate new-investor consideration from personalized sizing, which requires portfolio context.

Buy means supported prospective reward is attractive relative to risk and the stated hurdle. Hold is a supported neutral/retention assessment at the current price. Sell means the evidence supports an unattractive reward/risk balance or a broken investment thesis. Define the horizon and decision rationale; do not apply arbitrary universal percentage cutoffs. A Sell research opinion does not authorize shorting or any order.

## What makes a decision defensible

Complete the material enterprise-to-equity bridge, not every imaginable data field. For a finite mine, cover attributable payable sales, selling terms, operating costs, staged capital, remaining life, closure, tax, working capital, corporate cash/costs, investments and current diluted shares. Keep optional development assets separate. Unsupported exclusions are not zero economic value.

Bound material unknowns and test whether reasonable alternatives change the decision. If the conclusion is robust even under a defensible adverse bound, perfect information is unnecessary. If an unresolved project's value or funding could flip the rating, prioritize that investigation and withhold a definitive price-based rating meanwhile. State when missing inputs are not disclosed versus simply not researched.

Use one primary sector-appropriate valuation and one genuinely different cross-check. For MLX: finite-life asset NAV plus a small, normalized cash-flow/multiple comparison. Align periods, FX, ownership and minority interests. Explain disagreement between methods; do not average incompatible results to manufacture a target. No generic perpetuity for an exhausting mine.

Test priced-in expectations using the existing model's reverse calculation only when its scope supports the inference. A one-variable solution holds all other assumptions fixed; it is not a unique reconstruction of investors' beliefs. With major assets omitted, show an unexplained valuation residual and its possible sources instead. Do not call the entire residual Rentails value.

Use coherent downside cases: lower realized tin prices, realistic selling costs, disruption and capital timing, funding and dilution. Avoid changing every input independently into mutually inconsistent worlds. Explain return sources (cash generation, distributions, growth, valuation multiple) and the time needed to realize them. Risk discounts must not count the same downside repeatedly without justification.

Preserve each dated rating, expectation and outcome through existing research revisions. An operational milestone is not automatically a share-price catalyst; explain the information or cash-flow change and what may already be anticipated. Link important X claims to the exact assumption being tested; repeated posts never increase evidence weight by themselves.

## Exact upstream patterns rechecked on 20 September 2026

- [Dexter: write-memo, steps 3, 5 and 6](https://github.com/virattt/dexter/blob/main/src/skills/write-memo/SKILL.md): driver-consistent cases, priced-in expectations, opposing thesis and observable failure tests. Adapt the method; do not require invented probabilities or alter a case to achieve a preferred asymmetry ratio.
- [Financial Services: initiating-coverage / task3-valuation](https://github.com/anthropics/financial-services/blob/main/plugins/vertical-plugins/equity-research/skills/initiating-coverage/references/task3-valuation.md), steps 2D, 3, 5, 6 and sanity checks: equity bridge, comparables, reconciled methods and recommendation/horizon consistency. Keep two or three useful peers and finite mine lives, rather than copying its generic perpetuity or peer-count requirements. [Earnings analysis](https://github.com/anthropics/financial-services/blob/main/plugins/vertical-plugins/equity-research/skills/earnings-analysis/SKILL.md): actual evidence → revised assumptions → thesis/rating impact.
- [AI Hedge Fund: hedge_fund/signals/llm_agent.py](https://github.com/virattt/ai-hedge-fund/blob/main/hedge_fund/signals/llm_agent.py), `predict`, `_to_signal`, `_abstain`: retain as-of evidence and decision provenance; keep abstention separate from a valid neutral signal. The old `src/agents` paths did not resolve; the current tree was checked directly. Do not adopt persona voting or interpret confidence scores as calibrated probabilities.
- [AI Hedge Fund: hedge_fund/risk/limits.py](https://github.com/virattt/ai-hedge-fund/blob/main/hedge_fund/risk/limits.py), `apply_limits`: separate an investment opinion from deterministic portfolio limits. Existing local sizing already serves this purpose; no second allocator needed.
- [FinanceToolkit: models/intrinsic_model.py](https://github.com/JerBouma/FinanceToolkit/blob/main/financetoolkit/models/intrinsic_model.py): visible cash-flow-to-equity arithmetic and explicit assumptions. Its generic terminal-growth formula is not a substitute for a supported finite-life mine model.
- [Docling](https://github.com/docling-project/docling), [Last30Days](https://github.com/mvanhorn/last30days-skill), [Bird](https://github.com/steipete/bird): retain extraction/discovery/capture roles; no new rating engine. Bird's upstream page was unavailable in this check. Discovery coverage does not establish decision readiness.

These instructions specify analyst behavior; they do not claim that code automatically evaluates economic completeness or generates a reliable rating.

## Executable decision edition

Optional workbook presentation v4 adds a Decision worksheet using the existing inputs and model outputs. It requires the latest unambiguous consolidated investment-inventory period with `financial_assets_fvtpl` and `investment_in_associates`, plus two comparable FY periods of operating cash flow, equipment and mine-development payments. Keep original source dates/pages and currency. Use v2/v3 when the company's reporting does not support this exhibit; never insert zeros to unlock it.

Compare selected model equity with quote times the declared share denominator. Identify stale or proxy shares prominently. Show financial investments and associates at their disclosed carrying amounts, separately from any fair-value assessment. The residual after these carrying amounts is available only if model `other_assets` is zero; otherwise reconcile overlaps manually in the report. Do not add book equity, deferred-tax assets, plant book values or rehabilitation provisions mechanically to an operating DCF. Closure belongs once in the appropriate schedule; a discounted accounting provision is not an undiscounted closure cheque.

Historical operating cash less equipment and mine-development spending remains a diagnostic. It includes interest and tax timing and precedes other investing/financing. Compare it with market equity, not enterprise value, and do not label its reciprocal a normalized or prospective valuation multiple. A genuine normalized cross-check still needs adjustments, not a renamed historical ratio.

For the opposing case, describe the linked mechanism: weaker selling prices can reduce price-linked charges but leave fixed mine costs; disruption can reduce receipts while committed capital continues; delay shifts project benefits beyond the holding horizon; funding can introduce debt or dilution. Quantify supported links and explicitly identify unmodelled ones. Do not fabricate a capital envelope, share issue or project NPV to fill a table.

Store the dated opinion in the reader release's `decision` record and the existing recommendation/research history. The exporter checks consistency for v4 editions, including a visible blocker for Not rated; this is a publication check, not a proof of analytical correctness. Recheck original disclosures when a peer's guidance becomes final results, and explain substantive changes in tax, minority interests and actual shareholder distributions.
