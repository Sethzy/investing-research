# What Investing Research does

A standalone Codex workspace for company research, public-source monitoring and inspectable financial modelling. Open the repo in Codex and ask for a company investigation or update. Codex reasons about evidence; local tools capture sources, track review work, calculate scenarios and publish Markdown linked to Excel. A clone alone does not run unattended research.

![Research workflow](assets/research-flow.svg)

Export the diagram: [SVG](assets/research-flow.svg) · [PNG](assets/research-flow.png) · [PDF](assets/research-flow.pdf). SVG stays sharp when resized; PNG is convenient for slides; PDF is ready to share or print.

## Common journeys

| Ask Codex | What happens | What you receive |
|---|---|---|
| Install and set me up | Codex interviews you about preferences, installs dependencies and checks your own X login | Local configuration and an honest readiness summary |
| Research ASX:MLX | Resolve identity, gather disclosures and web/X evidence, verify facts and identify gaps | Cited company dossier and a model when evidence permits |
| Update since Friday | Collect the interval, deduplicate and assess changes | Material-change brief or an explicit coverage failure |
| Stress tin down 20%, costs up 10% | Fork a defined base-case scenario without overwriting the baseline | Comparison in Markdown, linked detailed Excel |
| Use my edited Excel assumptions | Recalculate all cases, verify parity, preserve an immutable snapshot | Updated model report and matching workbook |
| Should I add to this holding? | Review thesis, counterevidence, dated valuation and supplied portfolio limits | Supported view and constrained sizing, or insufficient evidence |

## How X fits

Bird uses your own signed-in browser session to search X web endpoints. No X developer key is required. ASX:MLX has six configured queries: company name, cashtag, exchange/ticker, Renison, Bluestone Mines Tasmania and the tin market. Public report/news research runs alongside these searches.

The first collection starts with a 30-day lookback. Later runs start at the source's last successful checkpoint with a 48-hour overlap, deduplicating captured posts. An explicit since-date overrides that start. The default request is up to 50 results per query; pagination/provider caps, expiry and failures can reduce actual coverage. This is periodic, bounded search, not a complete firehose or guaranteed historical archive.

Codex reads candidates, separates unrelated posts, follows accessible threads and primary links, and records relevance, verification and thesis/model implications. `collect` by itself leaves a review packet. Only completed review can produce an honest no-change result. Social claims remain leads unless supported by appropriate primary evidence.

## Four different time horizons

| Horizon | Current contract |
|---|---|
| Your investment horizon | Asked during setup; no universal horizon is silently assigned. 3–5 years is an example answer |
| Historical research | Attempt three completed annual periods and eight quarterly periods where published; document missing periods |
| X collection | Initial 30 days; subsequent checkpoint plus 48-hour overlap; explicit dates supported |
| Forecast model | Explicit scenario-specific annual periods. The MLX example uses illustrative 3/5/7-year cases, not verified mine lives |

A monitoring run has a default 30-minute soft collection budget. That is a work budget, not an investment horizon or a guarantee that a complete company investigation takes 30 minutes. Deep first-company research can span multiple sessions. Thesis duration and nearer-term catalysts must be separately dated in the dossier.

## Are all relevant sources covered?

No exhaustive-coverage claim is justified. The collector checks configured URLs and queries. Codex must also search the public web, open linked filings, and investigate industry context and counterevidence. A report-index download does not mean its reports have been read. Paywalls, inaccessible pages, search ranking and unavailable history remain limitations.

The core workflow requires a source coverage table with category, requested/available periods, original URL, publication date, capture completeness, review status and remaining action. Required categories are company/exchange disclosures, management commentary, industry/commodity context, competitors, independent news/counterevidence and X. Add regulators and geographic or operational risks where material. Mark unavailable or not-applicable sources with a reason. A checked category still does not prove all sources within it were found.

## Spec alignment and remaining gaps

Standalone setup, no data API keys, X collection, evidence records, Markdown-linked Excel and portfolio constraints align with the agreed product. Codex is now the sole setup host; users are never asked to choose another agent.

Reuse is component-based: vendored Bird, maintained extraction/spreadsheet libraries and a FinanceToolkit calculation primitive. Dexter and AI Hedge Fund informed the workflow; their complete runtimes were not integrated. The model and integration code contain more custom implementation than the original wholesale-reuse preference.

Supported Excel assumption edits synchronize; arbitrary formula/structure changes require a reviewed model revision. The public MLX example is an illustrative finite-mine sensitivity with historical financial observations, not a completed actionable valuation or integrated three-statement forecast. Source gaps and no verified current reference quote prevent claiming a decision-ready MLX price target. Independent recalculation checks arithmetic, not assumptions.

Scheduled operation must be demonstrated in the actual Codex host. Interactive X success and CI do not prove unattended authentication or another person's environment. The last recorded operational validation still had the first scheduled execution pending.

See [setup](setup.md), [Excel workflow](excel-models.md), [MLX report](../examples/mlx/report.md), [upstream reuse](upstream-decisions.md) and [the specification](superpowers/specs/2026-09-20-investing-research-design.md).
