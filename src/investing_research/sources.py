"""Bounded public downloads and immutable, page-addressable source captures.

Fetched text is evidence, never instructions. No cookies or API credentials are used.
"""
from __future__ import annotations

import hashlib
import ipaddress
import json
import re
import socket
import os
import subprocess
import sys
import tempfile
import time
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urljoin, urlsplit, urlunsplit

import httpx
from bs4 import BeautifulSoup
from pypdf import PdfReader

MAX_BYTES = 40 * 1024 * 1024
MAX_SECONDS = 90
MAX_REDIRECTS = 5
EXTRACT_SECONDS = 120
MAX_PAGES = 500
MAX_EXTRACT_BYTES = 20 * 1024 * 1024
USER_AGENT = "InvestingResearch/0.1 (public financial research; no authentication)"


class SourceError(ValueError):
    """A source could not safely be fetched or interpreted."""


def _public_target(url: str) -> tuple[str, str]:
    parsed = urlsplit(url)
    if (parsed.scheme != "https" or not parsed.hostname or parsed.username
            or parsed.password or parsed.port not in (None, 443)):
        raise SourceError("Only public HTTPS URLs on port 443 without credentials are supported")
    hostname = parsed.hostname
    try:
        addresses = list(dict.fromkeys(info[4][0] for info in socket.getaddrinfo(
            hostname, 443, type=socket.SOCK_STREAM)))
    except OSError as exc:
        raise SourceError("Source hostname cannot be resolved") from exc
    if not addresses or any(not ipaddress.ip_address(ip).is_global for ip in addresses):
        raise SourceError("Private, loopback, link-local and reserved network addresses are prohibited")
    address = addresses[0]
    address = f"[{address}]" if ":" in address else address
    pinned = urlunsplit(("https", address, parsed.path or "/", parsed.query, ""))
    return hostname, pinned


def _download(url: str) -> tuple[bytes, str, str]:
    deadline = time.monotonic() + MAX_SECONDS
    current = url
    # trust_env=False prevents inherited authenticated proxies or .netrc credentials.
    with httpx.Client(timeout=httpx.Timeout(25, connect=10), follow_redirects=False,
                      trust_env=False) as client:
        for _ in range(MAX_REDIRECTS + 1):
            if time.monotonic() > deadline:
                raise SourceError("Source exceeded elapsed-time limit")
            hostname, pinned = _public_target(current)
            # Pin the checked IP while retaining the original TLS hostname and HTTP host.
            try:
                with client.stream("GET", pinned,
                    headers={"Host": hostname, "User-Agent": USER_AGENT},
                    extensions={"sni_hostname": hostname}) as response:
                    if response.status_code in (301, 302, 303, 307, 308):
                        location = response.headers.get("location")
                        if not location:
                            raise SourceError("Redirect has no location")
                        current = urljoin(current, location)
                        continue
                    response.raise_for_status()
                    size = response.headers.get("content-length", "")
                    if size.isdigit() and int(size) > MAX_BYTES:
                        raise SourceError("Source exceeds the download size limit")
                    chunks, total = [], 0
                    for chunk in response.iter_bytes(chunk_size=65536):
                        total += len(chunk)
                        if total > MAX_BYTES or time.monotonic() > deadline:
                            raise SourceError("Source exceeded download size or elapsed-time limit")
                        chunks.append(chunk)
                    return b"".join(chunks), response.headers.get("content-type", ""), current
            except httpx.HTTPError as exc:
                # Do not include headers or response bodies in errors.
                raise SourceError(f"Public download failed: {type(exc).__name__}") from exc
    raise SourceError("Source exceeded redirect limit")


def _write_once(path: Path, content: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    try:
        with path.open("xb") as output:
            output.write(content)
    except FileExistsError:
        if path.read_bytes() != content:
            raise SourceError(f"Refusing to overwrite immutable source file: {path.name}")


def _json_once(path: Path, value: dict | list) -> None:
    _write_once(path, (json.dumps(value, indent=2, ensure_ascii=False) + "\n").encode())


def _html_text(body: bytes) -> tuple[str, str, str]:
    soup = BeautifulSoup(body, "html.parser")
    title = soup.title.get_text(" ", strip=True) if soup.title else "Untitled web source"
    for tag in soup(["script", "style", "noscript", "template"]):
        tag.decompose()
    text = soup.get_text("\n", strip=True)
    block_patterns = ("just a moment", "verify you are human", "access denied", "checking your browser",
                      "enable javascript and cookies", "sign in to continue", "log in to continue")
    blocked = any(term in title.lower() for term in block_patterns) or (
        len(text) < 2000 and any(term in text.lower() for term in block_patterns))
    completeness = "blocked" if blocked else "partial" if len(text) < 100 else "complete"
    return title, text, completeness


def _extract_local(path: Path, output_dir: Path, *, engine: str = "pypdf") -> dict:
    """Extract a local PDF; every page gets its physical one-based page reference.

    Docling is optional and runs locally. Model weights may download on first use.
    Its structured JSON retains table cells and provenance bounding boxes.
    """
    path, output_dir = Path(path), Path(output_dir)
    digest = hashlib.sha256(path.read_bytes()).hexdigest()
    directory = output_dir / digest / engine
    reader = PdfReader(path)
    if reader.is_encrypted:
        raise SourceError("Encrypted PDFs require an accessible public version")
    if len(reader.pages) > MAX_PAGES:
        raise SourceError("PDF exceeds extraction page limit")
    if engine == "docling":
        try:
            from docling.datamodel.base_models import InputFormat
            from docling.datamodel.pipeline_options import PdfPipelineOptions
            from docling.document_converter import DocumentConverter, PdfFormatOption
        except ImportError as exc:
            raise SourceError("Docling is not installed; install the project's documents extra") from exc
        converter = DocumentConverter(format_options={InputFormat.PDF: PdfFormatOption(
            pipeline_options=PdfPipelineOptions(enable_remote_services=False))})
        result = converter.convert(path)
        document = result.document
        markdown_bytes = document.export_to_markdown().encode()
        structured = (json.dumps(document.export_to_dict(), indent=2, ensure_ascii=False) + "\n").encode()
        if len(markdown_bytes) + len(structured) > MAX_EXTRACT_BYTES:
            raise SourceError("PDF exceeds extraction output limit")
        _write_once(directory / "document.md", markdown_bytes)
        _write_once(directory / "document.json", structured)
        return {"status": str(result.status), "engine": engine,
                "files": {"markdown": str((directory / "document.md").resolve()),
                          "structured": str((directory / "document.json").resolve())},
                "provenance": "Document JSON prov entries retain page_no and bounding boxes"}
    if engine != "pypdf":
        raise SourceError("Extraction engine must be pypdf or docling")
    pages, markdown = [], []
    text_bytes = 0
    for index, page in enumerate(reader.pages, 1):
        text = (page.extract_text(extraction_mode="layout") or "") if "/Contents" in page else ""
        text_bytes += len(text.encode())
        if text_bytes > MAX_EXTRACT_BYTES // 3:
            raise SourceError("PDF exceeds extraction output limit")
        pages.append({"page": index, "text": text, "status": "extracted" if text.strip() else "no_text"})
        markdown.append(f"## Page {index}\n\n{text}")
    _json_once(directory / "pages.json", pages)
    _write_once(directory / "document.md", "\n\n".join(markdown).encode())
    return {"engine": engine, "status": "complete" if pages and all(p["text"].strip() for p in pages) else "partial",
            "page_count": len(pages), "pages": [{"page": p["page"], "status": p["status"]} for p in pages],
            "files": {"markdown": str((directory / "document.md").resolve()),
                      "pages": str((directory / "pages.json").resolve())},
            "warnings": ["Layout text is not a verified table extraction; check figures against the original PDF."]}


def extract_source(path: Path, output_dir: Path, *, engine: str = "pypdf") -> dict:
    """Run untrusted PDF parsing in a bounded, credential-free child process."""
    import psutil

    path = Path(path).resolve()
    if engine not in ("pypdf", "docling"):
        raise SourceError("Extraction engine must be pypdf or docling")
    if path.stat().st_size > MAX_BYTES:
        raise SourceError("PDF exceeds extraction input limit")
    output_dir = Path(output_dir).resolve()
    output_dir.mkdir(parents=True, exist_ok=True)
    # HOME allows existing public model-weight caches; no tokens, proxy settings,
    # Python startup overrides, cookies or other inherited credentials are passed.
    env = {key: os.environ[key] for key in ("HOME", "USERPROFILE", "SYSTEMROOT", "TMPDIR")
           if key in os.environ}
    env["HF_HUB_DISABLE_IMPLICIT_TOKEN"] = "1"
    worker = Path(__file__).with_name("extract_worker.py")
    memory_limit = (6 if engine == "docling" else 1) * 1024**3
    with tempfile.TemporaryDirectory(prefix="investing-extract-") as tmp:
        staging = Path(tmp).resolve()
        receipt = staging / "receipt.json"
        command = [sys.executable, "-I", str(worker), str(path), str(staging / "output"),
                   engine, str(receipt)]
        process = subprocess.Popen(command, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                                   env=env, cwd=tmp)
        deadline = time.monotonic() + EXTRACT_SECONDS
        try:
            while process.poll() is None:
                if time.monotonic() >= deadline:
                    raise SourceError("PDF extraction exceeded time limit")
                try:
                    parent = psutil.Process(process.pid)
                    rss = sum(p.memory_info().rss for p in [parent] + parent.children(recursive=True)
                              if p.is_running())
                    if rss > memory_limit:
                        raise SourceError("PDF extraction exceeded memory limit")
                except psutil.NoSuchProcess:
                    pass
                time.sleep(0.05)
            if process.returncode or not receipt.exists():
                raise SourceError("PDF extraction worker failed or exceeded resource limit")
            if receipt.stat().st_size > MAX_EXTRACT_BYTES:
                raise SourceError("PDF extraction exceeded output limit")
            payload = json.loads(receipt.read_text())
            if not payload.get("ok"):
                raise SourceError(payload.get("error", "PDF extraction failed"))
            result = payload["result"]
            files = {}
            staged_files = list((staging / "output").rglob("*"))
            if sum(p.stat().st_size for p in staged_files if p.is_file()) > MAX_EXTRACT_BYTES:
                raise SourceError("PDF extraction exceeded output limit")
            for key, value in result["files"].items():
                source = Path(value).resolve()
                if not source.is_relative_to(staging / "output") or not source.is_file():
                    raise SourceError("Invalid extraction worker output")
                target = output_dir / source.relative_to(staging / "output")
                _write_once(target, source.read_bytes())
                files[key] = str(target.resolve())
            return {**result, "files": files}
        finally:
            if process.poll() is None:
                try:
                    children = psutil.Process(process.pid).children(recursive=True)
                except psutil.NoSuchProcess:
                    children = []
                for child in children:
                    try:
                        child.kill()
                    except psutil.NoSuchProcess:
                        pass
                process.kill()
            process.wait()


def fetch_source(url: str, output_dir: Path, *, extract: bool = True) -> dict:
    """Fetch evidence; immutable URL+content identity survives changed source URLs.

    Download failures raise SourceError. Extraction failures retain original bytes
    and return an explicit failed extraction, never manufactured text or facts.
    """
    body, content_type, final_url = _download(url)
    if not body:
        raise SourceError("Source returned an empty body")
    digest = hashlib.sha256(body).hexdigest()
    source_id = hashlib.sha256((url + "\0" + digest).encode()).hexdigest()
    directory = Path(output_dir) / source_id
    kind = "pdf" if body.startswith(b"%PDF-") else "html" if (
        "html" in content_type or body.lstrip().lower().startswith((b"<!doctype html", b"<html"))) else "unsupported"
    original = directory / ("original.pdf" if kind == "pdf" else "original.html" if kind == "html" else "original.bin")
    _write_once(original, body)
    record = {"id": source_id, "url": url, "final_url": final_url,
              "retrieved_at": datetime.now(timezone.utc).isoformat(), "published_at": None,
              "sha256": digest, "kind": kind, "title": urlsplit(final_url).path.rsplit("/", 1)[-1],
              "completeness": "complete" if kind == "pdf" else "unsupported",
              "capture_method": "public-https", "files": {"original": str(original.resolve())},
              "extraction": {"status": "not_requested"}}
    if kind == "html":
        record["title"], text, record["completeness"] = _html_text(body)
        if extract:
            _write_once(directory / "document.md", text.encode())
            record["files"]["markdown"] = str((directory / "document.md").resolve())
            record["extraction"] = {"engine": "beautifulsoup4", "status": record["completeness"],
                                    "warnings": ["Static HTML only; browser-rendered content may be missing."]}
    elif kind == "pdf" and extract:
        try:
            record["extraction"] = extract_source(original, directory / "extracted")
            record["files"].update(record["extraction"]["files"])
        except Exception as exc:
            record["extraction"] = {"engine": "pypdf", "status": "failed", "error": str(exc) if isinstance(exc, SourceError) else type(exc).__name__}
    manifest = directory / "capture.json"
    # First retrieval metadata is immutable. A later extraction request may add derived files.
    if not manifest.exists():
        _json_once(manifest, record)
    record["files"]["manifest"] = str(manifest.resolve())
    return record


def discover_links(url: str, *, limit: int = 30) -> list[dict]:
    """Find report candidates from a public index; no claim that discovery is exhaustive."""
    if not 1 <= limit <= 200:
        raise SourceError("Discovery limit must be between 1 and 200")
    body, content_type, final_url = _download(url)
    if body.startswith(b"%PDF-"):
        return [{"url": final_url, "title": urlsplit(final_url).path.rsplit("/", 1)[-1], "kind": "pdf"}]
    _, _, completeness = _html_text(body)
    if completeness == "blocked":
        raise SourceError("Report discovery is blocked by a login or access challenge")
    soup = BeautifulSoup(body, "html.parser")
    found, seen = [], set()
    for link in soup.find_all("a", href=True):
        href = urljoin(final_url, str(link["href"]))
        parsed = urlsplit(href)
        if parsed.scheme != "https" or not parsed.hostname or parsed.username or parsed.password:
            continue
        title = link.get_text(" ", strip=True) or link.get("title", "")
        context = f"{title} {href}"
        if not re.search(r"\.pdf(?:[?#]|$)|annual|quarter|interim|report|10-k|10-q", context, re.I):
            continue
        href = urlunsplit(parsed._replace(fragment=""))
        if href == final_url or href in seen:
            continue
        seen.add(href)
        found.append({"url": href, "title": title or parsed.path.rsplit("/", 1)[-1],
                      "kind": "pdf" if re.search(r"\.pdf(?:[?#]|$)", href, re.I) else "report_index",
                      "discovered_from": final_url})
    # Report PDFs outrank navigation links so small limits remain useful.
    found.sort(key=lambda item: item["kind"] != "pdf")
    return found[:limit]
