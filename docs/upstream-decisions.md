# Upstream reuse decisions

This project reuses working components and keeps a small amount of integration code for company identity, provenance, review receipts and model/portfolio rules. It does not fork a full API-dependent investing agent runtime.

| Upstream | Adopted capability | Boundary |
|---|---|---|
| [Bird](https://github.com/steipete/bird), via [Last30Days](https://github.com/mvanhorn/last30days-skill) | Vendored search client and TweetDetail primitives, retaining source layout and MIT licence | Read-only authenticated web requests; no posting or API-key onboarding |
| [FinanceToolkit](https://github.com/JerBouma/FinanceToolkit) | Offline free-cash-flow-to-firm calculation primitive | Provider downloads and key-requiring Toolkit data flows are not used |
| [Docling](https://github.com/docling-project/docling) | Optional local structured document conversion | Installed documents extra; remote inference disabled; public weights may download |
| [pypdf](https://github.com/py-pdf/pypdf) | Baseline page-addressable PDF extraction | Partial/scanned text is labelled; table accuracy requires review |
| [HTTPX](https://www.python-httpx.org/) and [Beautiful Soup](https://www.crummy.com/software/BeautifulSoup/) | Public document download and HTML parsing | Thin bounded-source policy and evidence metadata are project-specific |
| [XlsxWriter](https://xlsxwriter.readthedocs.io/) and [openpyxl](https://openpyxl.readthedocs.io/) | Editable workbooks and recalculated-value inspection | LibreOffice performs independent formula recalculation when installed |
| [Dexter](https://github.com/virattt/dexter) | Research-workflow reference | No Dexter runtime or token-based X tool adopted |
| [AI Hedge Fund](https://github.com/virattt/ai-hedge-fund) | Analyst/valuation-workflow reference | No analyst modules or complete runtime represented as integrated |

The existing subscribed Codex session provides orchestration, reasoning and semantic source review. There is no model daemon or custom dashboard. FinanceToolkit supplies an offline primitive; the explicit mine/FCF assumptions and portfolio policy logic are purpose-built project code, not a claim that a complete upstream valuation engine was adopted wholesale.

## Pins and licences

[uv.lock](../uv.lock) records exact Python versions and hashes; install with `uv sync --locked`. Package metadata retains upstream attribution. The vendored Bird subset is version-labelled 0.8.0, with MIT licence and upstream package metadata at `src/investing_research/vendor/bird-search/`. It is not claimed to be a pristine verified Git commit. See [Bird provenance and local modifications](upstream-bird.md) and [source/extraction provenance](upstream-sources.md).

Keep upstream licence files with redistributed source. Dependency and public model-weight licences may differ; retain their notices when packaging them. Existing developer installations served as source references only and are not runtime dependencies.

## Upgrade procedure

1. Inspect the relevant upstream change and licence before updating a package lock or vendored snapshot.
2. Record its precise installed version or source revision and local modifications. Preserve upstream layout and licences rather than copying untraceable fragments.
3. Run deterministic tests for collection receipts, authentication error sanitization, completeness, financial known values, ownership/currency checks and portfolio limits.
4. Run a small live keyword search and exact-post check with the operator's own session, plus a public-report capture. Confirm capped, missing and failed results remain visible.
5. Recalculate a model workbook and check parity. Optional Docling changes require an extraction smoke test before claiming conversion support.
6. Recheck the actual scheduled host environment; interactive browser success does not establish unattended availability.

Do not replace a broken no-key component with a paid/key-requiring service silently. Report the blocked capability and use existing browser tools with explicit coverage limitations where available.

## Excel detail and Markdown reports

The current model workflow uses editable Excel assumptions, independent recalculation and immutable Markdown/workbook snapshots. See [the executable workflow](excel-models.md) and [pinned upstream references](upstream-excel.md). Earlier Python-generated snapshots remain readable, but new `model` runs use this workflow.

Append/update workflows retain the pinned financial-services thesis-tracker, model-update, catalyst-calendar and earnings-analysis references. Runtime validation, immutable revisions and funding overlay are local code. Dexter inspired query refinement and structured answer rubrics; its key-dependent runtime and evaluation service are not adopted. See [research updates](research-updates.md).

The evidence-completion upgrade applies those existing model-update/earnings methods through separate captured, read, extracted, reconciled, analyzed and model-used stages. The investing skill bundles source, normalization, valuation-readiness, X-evidence and reader-report references. Category validation and reader export checks are local integration code, not upstream financial-analysis engines. Exact-post text completeness is retained separately from thread and media completeness. See [the completion contract](evidence-completion.md).

The [analytical-depth reference](../.agents/skills/investing/references/analytical-depth.md) records the 20 September recheck of all seven reference repos, adopted earnings/cash/capital-allocation patterns, and explicit exclusions. The optional Analysis worksheet is a small extension of the maintained generator, not a second financial engine. Workbook refresh preserves it.
