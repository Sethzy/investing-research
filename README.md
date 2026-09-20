# Investing Research

A standalone investing research workspace operated through your existing Codex/Claude subscription, using public web sources, company reports, authenticated X search, and local financial calculations. No financial-data, model, search-provider, or X developer API keys are required by the design.

**Status: specification stage.** This checkout contains documentation, not a runnable investing application. Bird keyword search has passed a live test in the existing development environment; its standalone packaging and unattended monitoring are not yet validated. See the [test record](docs/validation/2026-09-20-bird-search-smoke.md).

Read the [implementation specification](docs/superpowers/specs/2026-09-20-investing-research-design.md) for the agreed scope, user journeys, upstream reuse decisions, financial modelling requirements, architecture diagrams, and acceptance checks.

## What it will do

- Research a company from public reports, news, and X posts.
- Monitor saved keyword searches for holdings, watchlists, assets, and industry drivers.
- Build source-linked financial models, scenarios, sensitivities, and editable Excel workbooks.
- Produce readable Markdown dossiers, diagrams, and material-change briefs.
- Suggest investment views and portfolio-aware sizing using your manually supplied holdings and limits.

The first acceptance company is Metals X (ASX:MLX). Investment decisions remain with you; this project does not execute trades.

## Standalone by design

You will not need Seth Second Brain, a wiki, QMD, personal-skills, or another user's repository. Adopted upstream components will be installed as pinned dependencies or included with attribution and licence notices. Their existing filesystem conventions should be preserved where practical.

Moving or cloning this repo must not require editing developer-specific absolute paths. Use repository-relative links and configurable local storage. Each user supplies their own agent subscription, browser session, watchlist, timezone, and portfolio settings.

## Requirements and onboarding

Initial platform target: macOS. Other platforms are unverified. The tested Bird subset declares Node.js 22 or newer; final dependency versions and installation commands will be pinned during implementation. Local numerical and document-processing dependencies must be installed by the project's documented setup process.

The implemented setup must walk a new user through:

1. Installing the declared dependencies from a fresh checkout.
2. Opening the workspace in a supported subscribed agent host.
3. Signing in to X in their own browser and selecting the correct profile locally.
4. Running a read-only keyword-search smoke test and checking sample results.
5. Adding a company and producing its first dossier and model.
6. Optionally supplying portfolio/risk settings and enabling a daily schedule in their own timezone.

**There are no project install/run commands yet.** These steps are release requirements, not instructions claiming today's checkout is runnable. Before handoff, this README must contain tested commands, expected outputs, supported runtime versions, and recovery steps for each operation above.

## X search and authentication

Reuse the [Bird](https://github.com/steipete/bird) search component bundled with [Last30Days](https://github.com/mvanhorn/last30days-skill), plus exact-post capture and browser fallback where needed. Store company, asset, and related-topic searches; collect recent results; deduplicate; read relevant sources; and flag material changes.

No X developer API key is needed, but X search requires your authenticated session. Do not copy session cookies between users or put them in Git, logs, or shared configuration. Authentication access may require a local browser or operating-system prompt.

Bird uses X's undocumented web endpoints, which can change. A successful search today does not guarantee future availability, completeness, or unattended access. Failed authentication/search must appear as a coverage failure, never as “nothing changed.” No paid API fallback is introduced automatically.

## Sharing and private files

Share the tracked source and documentation, preferably via a clean clone. Do not send a zip of your entire working directory: ignored local data may still be present in it. Portfolio files, session material, generated research, reports, and operational state are private by default; sample fixtures must be synthetic or explicitly public.

## Documentation

- [Implementation specification](docs/superpowers/specs/2026-09-20-investing-research-design.md)
- [Bird live-search validation](docs/validation/2026-09-20-bird-search-smoke.md)

Before release, document upstream version pins, licences, upgrade checks, and exact troubleshooting commands alongside the implementation. No second-brain filing or wiki maintenance is part of this project.
