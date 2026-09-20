# Institutional equity analysis standard

This is the project's original research standard, informed by the linked methodologies and examples. It is not a claim of bank affiliation, guaranteed returns or access to proprietary consensus. Apply it with public web evidence, the user's X session and Codex. No new data subscriptions or API keys are required.

## Choose the right analytical task

An initiation explains the business and develops a complete investment case. An earnings update explains the new results relative to a dated prior expectation and changes the forecast where justified. A flash note addresses one material event. An uneventful monitoring run can stay short. Do not impose a page or chart quota; answer the decision-relevant questions with enough evidence and reasoning to withstand challenge.

The recommendation record is an executive summary. The substantive memo belongs in `companies/<id>/thesis.md`, with its as-of date, source cutoff, research horizon and matching model snapshot. Save it through the existing dossier/journal workflow before subsequent revisions so earlier analysis remains in the immutable journal. Preserve the full dated evidence appendix requested by the user. Its size is not evidence of analytical depth.

## Reader-facing delivery

The recipient is nontechnical. Deliver the actual investment story as the default Markdown and PDF: the current view, how the business earns money, what changed, the supporting and opposing cases, financial implications, and what to watch next. Use connected prose and selective readable exhibits. Explain unavoidable financial terms on first use. Keep material uncertainties and assumptions visible in plain language; presentation polish does not establish research completeness.

Do not expose code blocks, commands, JSON, file paths, hashes, run IDs, schemas, model-version identifiers, validation logs, software architecture, installation instructions or internal research checklists in the main report. Do not discuss report production as investment analysis. Use descriptive links such as “Detailed financial model” and “Company half-year report”; never make the reader navigate an internal folder tree. Technical support files do not belong in the default reader download.

Include a selective “What investors are discussing on X” section when useful posts were actually captured. Show a short exact quotation within applicable quotation limits, the poster's handle, post date, original link and a concise explanation of why the claim matters and what is verified. Label excerpts and incomplete discussions honestly. Never silently paraphrase inside quotation marks, reconstruct missing text or equate an interesting post with a reliable claim. Keep this readable section in the report; a list of links alone does not meet the user's preference for seeing useful original wording.

Publish a clean companion at `companies/<id>/investment-review.md`. Preserve the technical journal separately; do not concatenate it onto the default PDF. New reader updates should have a date and explain what changed in the investment view. Retain earlier reader editions and original expectations. The complete evidence history remains available separately when requested. Relevant X discussion should include the post link, a permitted attributed excerpt and a short investment interpretation; retain existing full captured text in the evidence archive without placing machine metadata in the reading flow.

Prepare a dated edition with its matching report, synchronized Excel/model/inputs, saved evidence review and `release.json`, following [reader publication checks](../../../../docs/reader-releases.md). Run `uv run python scripts/export-reader-report.py <edition>/investment-review.md --output <edition>/Investment-review.pdf`. Relative Excel links must resolve to that edition's reviewed workbook. Inspect every PDF page before delivery. The story must stand on its own; Excel supplies optional detail.

## Framework selection

| Framework | Use it to answer | Required analytical output |
|---|---|---|
| Expectations and variant perception | What must happen for this investment to outperform what the price already anticipates? | Separate sourced consensus, market-implied assumptions and our own hypothesis. Identify the disagreement and its consequences. |
| Business economics and competitive advantage | Why does this business earn its returns, and how durable are they? | Decompose unit economics, competitive position and reinvestment needs; compare with an appropriate peer or industry baseline. |
| Earnings quality and cash conversion | Do reported earnings produce cash available to owners? | Reconcile profit to operating cash flow and free cash flow, explaining working capital, one-offs, capex and financing. |
| Scenario valuation and downside survival | Which assumptions dominate value, and can the business fund the bad case? | Driver-based scenarios, an equity bridge, sensitivity analysis and a funding assessment. |
| Capital allocation | Will management's use of cash create per-share value? | Evaluate reinvestment, acquisitions, debt, distributions and dilution using documented decisions. |
| Falsifiable thesis and catalysts | What evidence would change our view, and when could it arrive? | Testable pillars, dated events, opposing evidence, thresholds and subsequent outcomes. |

Methodological basis: [Morgan Stanley Counterpoint Global](https://www.morganstanley.com/im/publication/insights/articles/article_roicandtheinvestmentprocess.pdf) connects ROIC, cash-flow drivers and expectations. [Morningstar's methodology overview](https://www.morningstar.com/stocks/morningstars-guide-investing-stocks) connects competitive advantage, intrinsic value and uncertainty. [Damodaran's commodity framework](https://pages.stern.nyu.edu/adamodar/New_Home_Page/littlebook/commodityvaluedrivers.htm) motivates cycle normalization rather than mechanically extrapolating recent profits. The concrete deliverables below are this project's implementation choices.

## Develop an argument, not a topic list

Use this chain for each material pillar:

**Claim -> mechanism -> evidence -> alternative explanation -> forecast consequence -> valuation consequence -> falsification test.**

Explain the mechanism in connected prose. Cite the evidence at the relevant claim. Then show the calculation or reference the exact workbook sheet/range supporting the financial consequence. Include both supporting and adverse evidence. Usually a few well-developed pillars are more useful than many disconnected bullets.

Never write “the market is missing X” without a basis for what is priced in. If accessible consensus is unavailable, state that explicitly. A reverse valuation can reveal conditional price-implied assumptions, but does not establish what every investor believes. Hold other drivers fixed transparently; several combinations of price, cost, growth and discount rate may explain the same share price.

Do not turn a missing market quote into an excuse to avoid business analysis. Explain supported operating conclusions, scenario dependence and evidence quality, while withholding price-based upside or an actionable recommendation when prerequisites are absent.

## Required content for an initiation

1. **Investment judgment.** State what is attractive, unattractive or unresolved, why it matters, the relevant horizon and which findings could change the decision. Distinguish a supported research conclusion from a trade recommendation.
2. **Business and asset economics.** Explain how money moves from customer demand to revenue, operating profit, reinvestment and distributable cash. Identify ownership, segmentation, concentration and the constraints on growth.
3. **Industry and competition.** Explain supply/demand, substitution, bargaining power, barriers and cycle position only where they affect the forecast. Use evidence to assess cost or quality advantages; do not assign a moat because management calls an asset exceptional.
4. **Historical financial diagnosis.** Show comparable periods, identify structural versus cyclical changes, reconcile cash conversion and test one-offs. Keep reported, normalized and forecast figures distinguishable. Explain changing definitions, consolidations and reporting bases.
5. **Thesis and opposing case.** Develop the material pillars using the chain above. Present the strongest credible alternative explanation, not a token generic risk paragraph.
6. **Forecast and valuation.** Explain driver assumptions, valuation method selection and cross-checks. Show bear/base/bull equity values, timing and funding assumptions. Include a verified dated price before calculating market upside. Do not average incompatible valuation methods merely to create a target. Use probabilities only when their rationale is explicit.
7. **Management and capital allocation.** Compare previous commitments with outcomes and examine incentives, dilution and returns on major investments. Distinguish accessible documented history from unverified impressions.
8. **Catalysts and invalidation.** Link each event to the expectation it will test and the possible valuation effect. “Read the report” is a research task, not a catalyst. “Verify shares” is a prerequisite, not an investment entry condition.
9. **Decision-critical gaps.** Rank unresolved inputs by their potential to change the conclusion. State what was attempted, what remains unknown and what new evidence would resolve it. Keep this distinct from the actual analysis.

Useful exhibits include an asset/ownership diagram, a production-to-cash bridge, a comparable-period operating table, a valuation sensitivity and a catalyst calendar. Every exhibit needs a takeaway, period, units and sources. Use diagrams to explain relationships and charts to expose trends; do not add decorative figures to meet a quota.

## Mining and commodity companies: required adaptations

For MLX and other finite-life producers, use asset-level economics and a sum-of-parts or finite-life NAV when supportable. Evaluate cycle-normalized commodity assumptions alongside spot-price stress scenarios. The [historical GMP MLX report, especially physical page 4](https://www.metalsx.com.au/wp-content/uploads/2019/09/20160421_GMP_Securities_Report.pdf#page=4) is a structural example of ownership-adjusted asset valuation and a share-count bridge; its 2016 asset portfolio, estimates and conclusions are not current MLX evidence.

Resolve the following rather than hiding them in a broad risk disclaimer:

- Tonnes mined/processed, grade, recovery, produced metal, payable sales, inventory and realized price. Identify which quantities are observed versus inferred; do not label produced tonnes as payable sales.
- Whole-operation versus attributable economics, joint-venture cash distributions and corporate-level costs. Apply ownership exactly once.
- Unit-cost definitions, royalties and treatment/payability deductions. Reconcile C1, AISC and total capex without subtracting the same cost twice.
- Reserve-supported mine life, resource conversion assumptions, sustaining versus growth capex, closure and rehabilitation timing. Do not add a perpetual terminal value to an exhaustible asset without a separate supported business case.
- Project milestones and funding requirements. Separate existing operations from unapproved development options. Show execution, delay, cost-overrun and dilution consequences.
- Cash quality and availability, current debt, commitments, taxes and a verified diluted share denominator. Cash is not automatically distributable or a hard floor under the share price.
- Commodity supply evidence: distinguish ore from contained metal and refined supply, inventories from flows, and a temporary disruption from a structural deficit. Test opposing supply responses.
- Peer comparisons that adjust for jurisdiction, ownership, mine life, stage, cost definition and commodity exposure. A low multiple alone does not establish mispricing.

## Earnings and dated updates

Lead with a concise judgment, then provide **prior expectation / actual / difference / explanation / new expectation / model effect / thesis effect**. Label whether the comparator is our previous estimate, company guidance or dated accessible consensus. A missing prior estimate cannot be retrospectively invented. Financial comparisons must share periods, units and ownership bases.

For each material change explain whether it changes near-term timing, sustained earnings power, risk or the valuation method. If the model is unchanged, explain why: immaterial magnitude, already assumed, uncorroborated or offsetting changes. Preserve original expectations and append the revised view. Reuse the bundled earnings-analysis and thesis-tracker concepts without importing their paid-data assumptions or fixed report-length rules.

## X evidence: short analysis with investment content

Preserve URL, timestamp, author and verbatim captured text in the dated appendix, with completeness labels. Add a short analysis answering: **what is claimed; why it could matter to a specific driver or pillar; what independent evidence supports or challenges it; what changes now.** Uncorroborated claims may justify investigation, not silently change baseline facts.

A post about a tin shortage should trigger investigation of the original series, units and dates, plus offsetting supply evidence. It should not become “bullish for MLX” merely because it has engagement. Deduplicate narratives analytically while retaining every requested capture in the appendix. For irrelevant posts, one precise sentence is enough.

## Research review before delivery

Review as a skeptical investment committee member. Record pass / partial / fail with evidence in the memo; there is no numerical quality score or word-count shortcut.

| Review question | Failure requiring revision or an explicit incomplete status |
|---|---|
| Can the reader explain how the business makes cash? | Only a business description and a commodity theme. |
| Are the thesis pillars causal and testable? | Attractive adjectives, no mechanism or falsification. |
| Is the alternative case credible? | Generic risks without opposing evidence or impact. |
| Do numbers reconcile to sources and model? | Mixed periods/ownership, missing denominators or unsupported precision. |
| Does valuation follow from the argument? | Assumptions listed without rationale, no sensitivity or funding treatment. |
| Is the alleged market disagreement established? | Invented consensus or an unsourced claim of mispricing. |
| Are catalysts genuine events and expectations preserved? | A research to-do list labelled as catalysts or entry conditions. |
| Does the narrative add judgment beyond the archive? | Repetition of captured text, sparse placeholders or a long disclaimer. |

An incomplete report can still contain strong supported analysis. Say precisely which conclusions are supported and which remain blocked. Do not fill gaps with invented research, interviews, access, probabilities or numbers.

## Worked example and further depth

The original sparse MLX summary is retained as history. Use the [dated research index](../../../../examples/mlx/README.md) for the latest reader edition; its illustrative valuation and disclosed gaps remain substantive limits. Apply [earnings quality and capital allocation](analytical-depth.md) for results-driven updates. Historical scenario numbers must not become universal examples of current value.
