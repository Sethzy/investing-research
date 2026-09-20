# Third-party notices

Original project code is available under the root MIT licence. Dependencies retain their own licences; the root licence does not replace them.

The vendored Bird 0.8.0 subset is copyright Peter Steinberger and distributed under its [retained MIT licence](src/investing_research/vendor/bird-search/LICENSE). It was sourced through the Last30Days distribution. [Provenance and modifications](docs/upstream-bird.md) describe this snapshot's limitations.

Python dependencies are installed from the versions and hashes in [uv.lock](uv.lock). Their distributions contain upstream licence metadata. Optional Docling model weights are separately downloaded and retain their own terms. See [upstream decisions](docs/upstream-decisions.md) for each adopted component and the exact scope of reuse. No Dexter or AI Hedge Fund runtime is redistributed.

Pinned modelling guidance from Anthropic’s `financial-services` repository is redistributed verbatim under Apache-2.0 in [vendor/financial-services](vendor/financial-services/). Its [licence](vendor/financial-services/LICENSE), [SHA-256 provenance](vendor/financial-services/provenance.json) and [adaptation notes](docs/upstream-excel.md) are retained. The workbook generator is local application code; no upstream workbook or financial estimates are claimed.
