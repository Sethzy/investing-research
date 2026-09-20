# Accumulating company brief validation

Implemented a single company `brief.md` backed by immutable, content-addressed journal entries. Collection appends coverage and captured evidence; completed review/dossier generation appends updated analysis and artifact inventories. Exact retries are idempotent. Old entries remain byte-identical. Both X and public-web lanes are always represented, including skipped/failed coverage. All captured X matches remain visible with source URL, literal captured text, completeness and short recorded analysis.

MLX backfill includes both stored MLX runs, all their captured X text, source links, reported facts, recommendation, historical model memos and three Excel files. No fresh X searches or primary-source research were performed. Full source reports are linked as retained files, not falsely described as wholly reviewed. The PDF exports the full journal and embeds exact UTF-8 Markdown; unsupported glyphs use explicit Unicode code points.

Validation: 122 tests passed. Focused tests verify literal source fences/markup, missing lanes, pending-to-reviewed history, exact retries, immutable prior entries, artifact revisions, tamper detection, PDF text/links and byte-exact Markdown attachment. Ruff and standalone distribution build passed. All MLX referenced local links resolve in the companion bundle, and every captured X text is present in the brief. PDF page layouts were visually inspected. Research remains illustrative with the existing MLX evidence gaps.

Generated user research stays ignored/private. Public code and workflow documentation contain no session credentials or copied research captures.
