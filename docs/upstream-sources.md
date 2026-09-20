# Public-source collection and extraction

The source adapter adopts HTTPX for bounded HTTPS downloads, Beautiful Soup for static HTML, pypdf for baseline PDF text extraction, and optional Docling for structured tables and document provenance. These are installed dependencies, not vendored rewrites. Exact installed versions are recorded in the project lockfile. The adapter contains only download policy, capture metadata, discovery, and output wiring.

## Source interfaces

- `fetch_source(url, output_dir, extract=True)` preserves original bytes in a directory keyed by URL and content hash. Changed content gets a new directory; repeated downloads never overwrite the first capture. It returns capture metadata and absolute local paths for the workspace registry to normalize.
- `discover_links(url, limit=30)` identifies public report-index and PDF candidates from one index page. The agent chooses the appropriate date and report and follows further indexes as needed. Discovery is bounded and is not proof of exhaustive coverage.
- `extract_source(path, output_dir, engine="pypdf")` writes page-addressable Markdown and JSON. Physical page numbers start at 1. The `docling` engine instead exports Docling Markdown and structured JSON, retaining page and table provenance; it requires the project's document-extraction extra.

Public downloads accept HTTPS port 443 only, reject credential-bearing URLs and non-public addresses, pin a validated IP for each request, preserve TLS hostname validation, and revalidate every redirect. Environment proxies and `.netrc` are not used. Responses are bounded to 40 MiB and 90 seconds of streamed elapsed time, with separate connect/read timeouts and five redirects. DNS lookup is provided by the operating system and subject to its resolver timeout. URL query parameters may be preserved in metadata: pass public links, never signed/private credential-bearing links.

Capture publication dates are unknown until the agent reads the document; retrieval time is not publication time. Static HTML may omit browser-rendered content. Recognized login/challenge pages are labelled blocked and cannot be complete evidence. PDF original-download completeness and extraction completeness are separate: empty/scanned pages are explicitly partial, damaged or encrypted PDFs retain original bytes and report extraction failure. Baseline layout text does not assert accurate table boundaries. Check important figures against the PDF or use Docling.

PDF extraction runs in an isolated Python child with a sanitized environment (no session tokens, API keys, proxies or Python startup overrides), discarded diagnostics, a 120-second wall-clock limit and process-tree RSS monitoring (1 GiB for pypdf, 6 GiB for Docling). The worker accepts at most 500 physical pages and publishes at most 20 MiB of derived output. POSIX CPU/file-size/core-dump limits supplement portable parent monitoring. Memory is sampled every 50 ms rather than being a hard OS allocation boundary; this is resource containment, not a filesystem/network sandbox. Failed or timed-out workers are terminated and originals remain intact. Temporary results are published only after successful bounded extraction.

Docling runs local inference with remote services disabled; its first invocation may download public model weights. Conversion must complete successfully before its extracted tables are used as evidence. Source text is untrusted data and never executed.

## Verified discovery, 2026-09-20

Live public-HTTPS discovery returned these company-hosted sources:

| Company | Source | Original URL |
|---|---|---|
| Metals X, ASX:MLX | Annual report for 31 December 2025 | [Original PDF](https://www.metalsx.com.au/wp-content/uploads/2026/03/MLX-Annual-Report-31-December-2025.pdf) |
| Metals X, ASX:MLX | Quarterly report for 30 June 2026 | [Original PDF](https://www.metalsx.com.au/wp-content/uploads/2026/07/02_MLX_Quarterly-Report_30-June-2026_Final.pdf) |
| Microsoft, NASDAQ:MSFT | Annual report 2025 | [Original HTML](https://www.microsoft.com/investor/reports/ar25/index.html) |

Discovery indexes: [Metals X annual reports](https://www.metalsx.com.au/asx-announcements-2/), [quarterly reports](https://www.metalsx.com.au/quarterly-reports/), and [Microsoft download center](https://www.microsoft.com/investor/reports/ar25/download-center/). These are example discovery evidence, not hard-coded source locations in the adapter. No financial facts are inferred merely from a link title.

## Upstream documentation and attribution

API usage was checked through Context7 against upstream documentation before implementation:

- [HTTPX quick start](https://www.python-httpx.org/quickstart/): streaming, response status, redirects; BSD-3-Clause.
- [Beautiful Soup documentation](https://www.crummy.com/software/BeautifulSoup/bs4/doc/): parsing, text extraction, links; MIT.
- [pypdf](https://github.com/py-pdf/pypdf): page extraction, layout mode and metadata; BSD-3-Clause.
- [Docling](https://github.com/docling-project/docling): local `DocumentConverter`, disabled remote services, structured export; MIT (individual model artefacts have their own upstream licences).

Tests exercise capture immutability, changed content, unsafe URLs and redirects, pinned addresses, relative link discovery, blocked pages, HTTP failures, oversized responses, damaged PDFs, explicit empty-page provenance, stalled-worker termination, credential environment filtering, oversized output, page limits and successful following-source capture after extraction failure.

### Live download and extraction result

On 2026-09-20 all three original sources above downloaded successfully using the adapter without API keys. The MLX annual report has 79 physical pages: pypdf extracted pages 2–79 and explicitly marked the image-only cover page 1 as missing text, leaving extraction status `partial`. The quarterly report has 10 pages, all with extracted text. Microsoft annual HTML was captured and extracted, subject to the static-HTML limitation above. Captures and generated research remain under ignored `data/`.

Important interpretation checks: MLX's Q2 CY2026 table describes whole-operation figures, with 50% attribution applied only to operating flows. Its quoted tin price is an **imputed LME quarterly average**, not a realized sales price. Sales/marketing costs include royalties and smelter deductions, so adding a second payable deduction would double-count. Group balance-sheet cash and liabilities already reflect consolidation. Source page references are physical PDF pages; annual printed labels run one behind them.

Docling also passed a bounded local conversion smoke on annual report physical page 25 (the consolidated statement of financial position). Conversion returned `SUCCESS`, produced a structured table with physical-page/bounding-box provenance, and retained the `293,606` cash figure in Markdown. The excerpt's page 1 maps to original PDF physical page 25 in an ignored provenance sidecar. Initial public model-weight downloads required no API key. This validates the adapter and table export on one representative page, not the accuracy of every table in the full annual report.

The same one-page Docling smoke was repeated after adding the isolated-worker resource boundary. It again returned `ConversionStatus.SUCCESS` and retained `293,606`; the new security boundary is exercised by the live adapter smoke as well as deterministic failure tests.
