# Bird keyword-search smoke test

Date: 2026-09-20

## Result

**PASS for interactive authenticated keyword search in the existing development environment.** Both requests completed successfully and returned five posts. This is not a standalone-install, exact-post completeness, pagination, or scheduled-execution pass.

| Query | Requested | Returned | Outcome |
|---|---:|---:|---|
| `"Metals X"` | 5 | 5 | Success |
| `"Metals X" since:2026-09-01` | 5 | 5 | Success; returned timestamps were within the requested lower date bound |

The two queries returned the same five post IDs. Results included relevant investing discussion and irrelevant matches. Transport success does not establish relevance, factual accuracy, or exhaustive coverage. No investment claims from these posts were verified in this test.

## Tested component and method

- Vendored `bird-search` package version `0.8.0`, based on `@steipete/bird`, MIT; package declares Node.js >=22.
- Existing personal-skills checkout revision: `743c43ef4c1165e57e575e8976a7177551332dfa`. This records the development fixture, not a dependency for the new project.
- Vendored component tree SHA-256: `0ee4ab0800156839b346c52421d73c99720544310e753fc7f9bf167dd36bc857` (sorted relative filenames plus NUL, contents plus NUL).
- Used Last30Days' existing cookie extraction for the local authenticated Chrome profile, scoped to X cookies only.
- Passed session values in process environment to the read-only Bird search subprocess; no developer API key used. No session values were printed or saved in this repository.
- Requested JSON results with a five-result limit. The inspected search implementation uses the `Latest` product.
- No second-brain ingestion, wiki writes, or portfolio operations performed.

The existing installed code was tested directly. It has not yet been packaged into this repository. A receiving user's machine must use its own browser/profile/session and documented project dependencies, without referring to this developer's checkout.

## Remaining acceptance gates

1. Reproduce keyword search from a fresh standalone installation with documented dependency pins.
2. Verify exact-post/thread/article capture and completeness classification.
3. Verify pagination, result caps, date-window overlap, deduplication, and failure handling.
4. Run through the supported scheduled agent host to verify unattended session access.
5. Test on another user's supported machine with no second-brain/personal-skills installation.

## Reference

[Bird documentation](https://github.com/steipete/bird): cookie-authenticated access uses undocumented X endpoints, so endpoint changes can break access. Context7 documentation was consulted alongside the installed source; the live results above are the evidence for this smoke-test outcome.
