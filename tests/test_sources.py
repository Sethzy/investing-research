import json
from pathlib import Path

import httpx
import pytest
from pypdf import PdfWriter
from investing_research import sources


def test_immutable_capture_versions_and_retry(tmp_path, monkeypatch):
    contents = [b'<html><title>Report</title><body>' + b'Annual result ' * 20 + b'</body></html>']
    monkeypatch.setattr(sources, '_download', lambda url: (contents[0], 'text/html', url))
    first = sources.fetch_source('https://example.org/report', tmp_path)
    original = Path(first['files']['original']).read_bytes()
    again = sources.fetch_source('https://example.org/report', tmp_path)
    assert again['id'] == first['id']
    contents[0] += b'New revision'
    updated = sources.fetch_source('https://example.org/report', tmp_path)
    assert updated['id'] != first['id']
    assert Path(first['files']['original']).read_bytes() == original


@pytest.mark.parametrize('url', ['http://example.org', 'file:///etc/passwd', 'https://u:p@example.org', 'https://example.org:8080'])
def test_unsafe_schemes_and_credentials(url):
    with pytest.raises(sources.SourceError):
        sources._public_target(url)


def test_private_resolution_blocked(monkeypatch):
    monkeypatch.setattr(sources.socket, 'getaddrinfo', lambda *a, **k: [(2, 1, 6, '', ('127.0.0.1', 443))])
    with pytest.raises(sources.SourceError):
        sources._public_target('https://localhost')


def test_pins_checked_address(monkeypatch):
    monkeypatch.setattr(sources.socket, 'getaddrinfo', lambda *a, **k: [(2, 1, 6, '', ('8.8.8.8', 443))])
    assert sources._public_target('https://example.org/a?q=b#page') == ('example.org', 'https://8.8.8.8/a?q=b')


def test_report_discovery_relative_links(tmp_path, monkeypatch):
    monkeypatch.setattr(sources, '_download', lambda url: (b'<html><a href="../2025.pdf">Annual report</a><a href="../2025.pdf">Again</a><a href="javascript:alert(1)">Report</a><a href="/contact">Contact</a></html>', 'text/html', url))
    results = sources.discover_links('https://example.org/investor/reports/')
    assert [r['url'] for r in results] == ['https://example.org/investor/2025.pdf']


def test_blocked_html_is_not_complete(tmp_path, monkeypatch):
    monkeypatch.setattr(sources, '_download', lambda url: (b'<html><title>Just a moment</title>Verify you are human</html>', 'text/html', url))
    assert sources.fetch_source('https://example.org/report', tmp_path)['completeness'] == 'blocked'
    with pytest.raises(sources.SourceError):
        sources.discover_links('https://example.org/report')


def test_page_provenance_and_empty_page(tmp_path):
    writer = PdfWriter()
    writer.add_blank_page(width=100, height=100)
    writer.add_blank_page(width=100, height=100)
    pdf = tmp_path / 'fixture.pdf'
    writer.write(pdf)
    result = sources.extract_source(pdf, tmp_path / 'extracted')
    assert result['status'] == 'partial'
    assert [p['page'] for p in result['pages']] == [1, 2]
    assert '## Page 2' in Path(result['files']['markdown']).read_text()
    assert len(json.loads(Path(result['files']['pages']).read_text())) == 2


def test_bad_pdf_retains_bytes_and_labels_failure(tmp_path, monkeypatch):
    monkeypatch.setattr(sources, '_download', lambda url: (b'%PDF-invalid', 'application/pdf', url))
    result = sources.fetch_source('https://example.org/report.pdf', tmp_path)
    assert result['extraction']['status'] == 'failed'
    assert Path(result['files']['original']).read_bytes() == b'%PDF-invalid'


def test_unsafe_redirect_is_not_followed(monkeypatch):
    real_client = httpx.Client
    calls = []
    def handle(request):
        calls.append(request)
        return httpx.Response(302, headers={'location': 'https://127.0.0.1/private'})
    monkeypatch.setattr(sources.httpx, 'Client', lambda **kw: real_client(transport=httpx.MockTransport(handle), **kw))
    monkeypatch.setattr(sources.socket, 'getaddrinfo', lambda host, *a, **k: [(2, 1, 6, '', ('127.0.0.1' if host == '127.0.0.1' else '8.8.8.8', 443))])
    with pytest.raises(sources.SourceError):
        sources._download('https://example.org/report')
    assert len(calls) == 1


def test_http_failure_and_size_limit(monkeypatch):
    real_client = httpx.Client
    monkeypatch.setattr(sources, '_public_target', lambda url: ('example.org', url))
    monkeypatch.setattr(sources.httpx, 'Client', lambda **kw: real_client(transport=httpx.MockTransport(lambda r: httpx.Response(503)), **kw))
    with pytest.raises(sources.SourceError, match='HTTPStatusError'):
        sources._download('https://example.org/report')
    monkeypatch.setattr(sources.httpx, 'Client', lambda **kw: real_client(transport=httpx.MockTransport(lambda r: httpx.Response(200, headers={'content-length': str(sources.MAX_BYTES + 1)})), **kw))
    with pytest.raises(sources.SourceError, match='size limit'):
        sources._download('https://example.org/report')


def test_extraction_timeout_retains_original_and_next_source_succeeds(tmp_path, monkeypatch):
    import subprocess
    import sys
    import time
    real_popen = subprocess.Popen
    children = []
    def stalled(command, **kwargs):
        assert 'X_AUTH_TOKEN' not in kwargs['env']
        assert 'SECRET_KEY' not in kwargs['env']
        child = real_popen([sys.executable, '-I', '-c', 'import time; time.sleep(30)'], **kwargs)
        children.append(child)
        return child
    monkeypatch.setenv('X_AUTH_TOKEN', 'do-not-inherit')
    monkeypatch.setenv('SECRET_KEY', 'do-not-inherit')
    monkeypatch.setattr(sources.subprocess, 'Popen', stalled)
    monkeypatch.setattr(sources, 'EXTRACT_SECONDS', 0.1)
    monkeypatch.setattr(sources, '_download', lambda url: (b'%PDF-test', 'application/pdf', url))
    started = time.monotonic()
    result = sources.fetch_source('https://example.org/stalled.pdf', tmp_path)
    assert time.monotonic() - started < 5
    assert result['extraction']['status'] == 'failed'
    assert 'time limit' in result['extraction']['error']
    assert Path(result['files']['original']).read_bytes() == b'%PDF-test'
    assert children[0].poll() is not None
    monkeypatch.setattr(sources, '_download', lambda url: (b'<html><title>Report</title>' + b'Annual results ' * 30 + b'</html>', 'text/html', url))
    followup = sources.fetch_source('https://example.org/next', tmp_path)
    assert followup['extraction']['status'] == 'complete'


def test_extraction_output_limit_publishes_no_derived_files(tmp_path, monkeypatch):
    writer = PdfWriter()
    writer.add_blank_page(width=100, height=100)
    pdf = tmp_path / 'source.pdf'
    writer.write(pdf)
    monkeypatch.setattr(sources, 'MAX_EXTRACT_BYTES', 1)
    with pytest.raises(sources.SourceError, match='output limit'):
        sources.extract_source(pdf, tmp_path / 'output')
    assert not list((tmp_path / 'output').rglob('*.md'))
    assert pdf.exists()


def test_pdf_page_limit_is_rejected_in_worker(tmp_path):
    writer = PdfWriter()
    for _ in range(sources.MAX_PAGES + 1):
        writer.add_blank_page(width=10, height=10)
    pdf = tmp_path / 'many.pdf'
    writer.write(pdf)
    with pytest.raises(sources.SourceError, match='page limit'):
        sources.extract_source(pdf, tmp_path / 'output')
