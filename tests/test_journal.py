import pytest

from investing_research.contracts import Company, Settings
from investing_research.journal import update, export_pdf
from investing_research.workspace import Workspace, read_json, write_json


@pytest.fixture
def workspace(tmp_path):
    ws = Workspace(tmp_path)
    company = Company(id="asx-mlx", name="Metals X", exchange="ASX", ticker="MLX",
                      currency="AUD", reporting_currency="AUD", sector="mining",
                      website="https://example.com", queries=["MLX"])
    write_json(ws.settings_path, Settings(companies=[company]).model_dump(mode="json"))
    return ws


def seed(ws):
    text = "First line\n\n```\n# untrusted heading <b>literal</b> 🐦\nLast line"
    capture, _ = ws.capture_x({"id": "123", "url": "https://x.com/test/status/123",
                              "text": text, "completeness": "partial", "author": "test"})
    run = {"id": "run1", "started_at": "2026-09-20T01:00:00Z", "status": "pending_review",
           "company_ids": ["asx-mlx"], "errors": [], "operations": [
               {"company_id": "asx-mlx", "kind": "x", "query": "MLX", "status": "ok",
                "capture_ids": [capture["id"]]}]}
    write_json(ws.root / "state/runs/run1.json", run)
    return run, capture, text


def test_history_verbatim_retry_review_and_missing_lane(workspace):
    run, source, text = seed(workspace)
    path = update(workspace, "asx-mlx")
    assert text in path.read_text()
    assert "Public web and reports: not attempted" in path.read_text()
    assert "Completeness: partial" in path.read_text()
    ledger = workspace.root / "state/journal/asx-mlx"
    before = {p.name: p.read_bytes() for p in ledger.glob("*.json")}
    assert len(before) == 1
    update(workspace, "asx-mlx")
    assert before == {p.name: p.read_bytes() for p in ledger.glob("*.json")}
    run.update(status="no_change", reviewed_at="2026-09-20T02:00:00Z", decisions=[
        {"company_id": "asx-mlx", "capture_id": source["id"], "material": False,
         "verification": "irrelevant", "summary": "Software acronym, not company.",
         "model_impact": "None."}])
    write_json(workspace.root / "state/runs/run1.json", run)
    update(workspace, "asx-mlx")
    assert len(list(ledger.glob("*.json"))) == 2
    assert all((ledger / n).read_bytes() == b for n, b in before.items())
    assert "Software acronym" in path.read_text()
    assert path.read_text().count(text) == 2


def test_artifacts_and_tampering(workspace):
    seed(workspace)
    report = workspace.root / "companies/asx-mlx/models/test/report.md"
    report.parent.mkdir(parents=True)
    report.write_text("Original model memo")
    update(workspace, "asx-mlx")
    report.write_text("Corrected memo")
    path = update(workspace, "asx-mlx")
    assert "Original model memo" in path.read_text() and "Corrected memo" in path.read_text()
    entry = next((workspace.root / "state/journal/asx-mlx").glob("*.json"))
    value = read_json(entry)
    value["payload"]["body"] = "tampered"
    write_json(entry, value)
    with pytest.raises(ValueError, match="integrity"):
        update(workspace, "asx-mlx")


def test_reader_editions_preserve_prior_story(workspace):
    seed(workspace)
    report = workspace.root / "companies/asx-mlx/investment-review.md"
    report.parent.mkdir(parents=True, exist_ok=True)
    report.write_text("# Metals X\nFirst reader assessment.")
    update(workspace, "asx-mlx")
    report.write_text("# Metals X\nRevised reader assessment.")
    path = update(workspace, "asx-mlx")
    assert "First reader assessment." in path.read_text()
    assert "Revised reader assessment." in path.read_text()


def test_pdf_preserves_exact_attachment(workspace):
    from pypdf import PdfReader
    seed(workspace)
    path = update(workspace, "asx-mlx")
    target = export_pdf(path, path.with_suffix('.pdf'))
    reader = PdfReader(target)
    assert reader.attachments['brief.md'][0] == path.read_bytes()
    text = '\n'.join(p.extract_text() for p in reader.pages)
    assert 'Last line' in text and 'review pending' in text
    assert any(p.get('/Annots') for p in reader.pages)


def test_repeated_capture_carries_prior_review_not_unrelated_posts(workspace):
    run, source, _ = seed(workspace)
    run.update(status='no_change', decisions=[
        {'company_id': 'asx-mlx', 'capture_id': source['id'], 'material': False,
         'verification': 'irrelevant', 'summary': 'Prior review.', 'model_impact': 'None.'}])
    write_json(workspace.root / 'state/runs/run1.json', run)
    second = {**run, 'id': 'run2', 'started_at': '2026-09-20T03:00:00Z', 'decisions': []}
    write_json(workspace.root / 'state/runs/run2.json', second)
    path = update(workspace, 'asx-mlx')
    assert 'carried forward' in path.read_text()
    assert 'review pending' not in path.read_text()
