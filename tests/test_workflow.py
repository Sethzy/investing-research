import json
from pathlib import Path

import pytest
from filelock import Timeout
from typer.testing import CliRunner

from investing_research.cli import app
from investing_research.contracts import Company, Decision, Fact, Recommendation, Settings
from investing_research.monitor import collect, review
from investing_research.reports import add_facts, add_recommendation, dossier
from investing_research.workspace import Workspace, read_json, write_json


@pytest.fixture
def ws(tmp_path):
    space = Workspace(tmp_path)
    company = Company(
        id="asx-mlx",
        name="Metals X",
        exchange="ASX",
        ticker="MLX",
        currency="AUD",
        reporting_currency="AUD",
        sector="tin",
        website="https://example.com",
        queries=['"Metals X"'],
        sources=[],
    )
    write_json(space.settings_path, Settings(companies=[company]).model_dump(mode="json"))
    return space


def search_result(text="A relevant report link", capped=False):
    return {
        "status": "ok",
        "coverage": {"capped": capped, "exhaustive": False},
        "posts": [
            {
                "id": "123",
                "url": "https://x.com/a/status/123",
                "text": text,
                "author": "a",
                "published_at": "2026-09-18",
                "completeness": "partial",
            }
        ],
    }


def decisions(run, material=False):
    return [
        Decision(
            **c,
            material=material,
            verification="unverified",
            summary="Research lead",
            thesis_impact="Investigate",
            model_impact="No change",
            follow_up="Read filing",
        )
        for c in run["candidates"]
    ]


def test_collect_review_repeat_and_edit(ws, monkeypatch):
    monkeypatch.setattr("investing_research.x.search", lambda *a, **k: search_result())
    first = collect(ws)
    assert first["status"] == "pending_review"
    assert not list((ws.root / "briefs").glob("*.md"))
    reviewed = review(ws, first["id"], decisions(first, material=True))
    assert reviewed["status"] == "material_changes"
    assert len(list((ws.root / "briefs").glob("*.md"))) == 1
    second = collect(ws)
    assert second["candidates"] == []
    assert second["status"] == "no_change"
    monkeypatch.setattr("investing_research.x.search", lambda *a, **k: search_result("Edited claim"))
    third = collect(ws)
    assert len(third["candidates"]) == 1
    assert len(ws.captures()) == 2


def test_shared_query_is_collected_once_for_multiple_companies(ws, monkeypatch):
    settings = ws.settings()
    second = settings.companies[0].model_copy(update={"id": "asx-other", "name": "Other"})
    settings.companies.append(second)
    write_json(ws.settings_path, settings.model_dump(mode="json"))
    calls = []

    def search(query, **kwargs):
        calls.append(query)
        return search_result()

    monkeypatch.setattr("investing_research.x.search", search)
    run = collect(ws)
    assert len(calls) == 1
    assert {c["company_id"] for c in run["candidates"]} == {"asx-mlx", "asx-other"}


def test_failed_source_does_not_advance_checkpoint(ws, monkeypatch):
    monkeypatch.setattr("investing_research.x.search", lambda *a, **k: search_result())
    collect(ws)
    before = read_json(ws.root / "state/checkpoints.json")
    monkeypatch.setattr(
        "investing_research.x.search", lambda *a, **k: {"status": "error", "error": {"message": "secret"}}
    )
    failed = collect(ws)
    assert failed["status"] == "degraded"
    assert read_json(ws.root / "state/checkpoints.json") == before
    assert "secret" not in json.dumps(failed)
    assert (ws.root / "briefs" / (failed["id"] + ".md")).exists()


def test_capped_results_not_complete(ws, monkeypatch):
    monkeypatch.setattr("investing_research.x.search", lambda *a, **k: search_result(capped=True))
    run = collect(ws)
    assert run["errors"]
    assert not (ws.root / "state/checkpoints.json").exists()
    assert review(ws, run["id"], decisions(run))["status"] == "degraded"


def test_review_requires_all_candidates_and_independent_source(ws, monkeypatch):
    monkeypatch.setattr("investing_research.x.search", lambda *a, **k: search_result())
    run = collect(ws)
    with pytest.raises(ValueError, match="every run candidate"):
        review(ws, run["id"], [])
    rows = decisions(run)
    rows[0].verification = "corroborated"
    rows[0].corroborating_sources = [rows[0].capture_id]
    with pytest.raises(ValueError, match="another captured source"):
        review(ws, run["id"], rows)


def test_lock_and_path_escape(ws):
    with ws.lock():
        with pytest.raises(Timeout):
            with ws.lock():
                pass
    with pytest.raises(ValueError):
        ws.inside("../outside.json")


def test_fact_import_requires_known_complete_primary_source(ws):
    source, _ = ws.capture_record(
        {
            "url": "https://example.com/report.pdf",
            "sha256": "a" * 64,
            "files": [],
            "kind": "pdf",
            "completeness": "complete",
        }
    )
    fact = Fact(
        company_id="asx-mlx",
        metric="cash",
        value=10,
        unit="AUD",
        currency="AUD",
        period="2025",
        published_at="2026-03-01",
        source_id=source["id"],
        page="25",
        entity="group",
        ownership_basis="consolidated",
    )
    first = add_facts(ws, [fact])
    assert add_facts(ws, [fact]) == first
    assert len(list((ws.root / "state/facts").glob("*.json"))) == 1
    path = dossier(ws, "asx-mlx")
    assert "report.pdf" in path.read_text()
    fact.source_id = "missing"
    with pytest.raises(ValueError):
        add_facts(ws, [fact])


def test_cli_portable_init_watchlist_and_missing_portfolio(tmp_path):
    runner = CliRunner()
    root = str(tmp_path / "different user's workspace")
    assert runner.invoke(app, ["--root", root, "init"]).exit_code == 0
    config = Path(__file__).parents[1] / "examples/company-mlx.json"
    assert runner.invoke(app, ["--root", root, "watch-add", str(config)]).exit_code == 0
    result = runner.invoke(app, ["--root", root, "size", "asx-mlx", "0.1"])
    assert result.exit_code == 2
    assert json.loads(result.stdout)["status"] == "blocked"


def test_pending_retries_emit_one_material_brief(ws, monkeypatch):
    monkeypatch.setattr("investing_research.x.search", lambda *a, **k: search_result())
    first, second = collect(ws), collect(ws)
    assert review(ws, first["id"], decisions(first, True))["status"] == "material_changes"
    assert review(ws, second["id"], decisions(second, True))["status"] == "no_change"
    assert len(list((ws.root / "briefs").glob("*.md"))) == 1


def test_incomplete_run_cannot_finalize_no_change(ws):
    run = {
        "id": "interrupted",
        "status": "collecting",
        "finished_at": None,
        "operations": [{"status": "pending"}],
        "candidates": [],
        "errors": [],
    }
    write_json(ws.root / "state/runs/interrupted.json", run)
    with pytest.raises(ValueError, match="incomplete"):
        review(ws, "interrupted", [])
    assert read_json(ws.root / "state/runs/interrupted.json")["status"] == "collecting"


def test_next_collection_recovers_interrupted_receipt(ws, monkeypatch):
    run = {
        "id": "interrupted",
        "started_at": "2026-09-01T00:00:00+00:00",
        "status": "collecting",
        "finished_at": None,
        "operations": [{"status": "pending"}],
        "candidates": [],
        "errors": [],
        "company_ids": ["asx-mlx"],
    }
    write_json(ws.root / "state/runs/interrupted.json", run)
    monkeypatch.setattr("investing_research.x.search", lambda *a, **k: search_result())
    collect(ws)
    old = read_json(ws.root / "state/runs/interrupted.json")
    assert old["status"] == "degraded"
    assert old["operations"][0]["status"] == "interrupted"
    assert old["errors"]


def test_browser_x_import_remains_social(ws, monkeypatch):
    monkeypatch.setattr("investing_research.sources._public_target", lambda u: ("x.com", "1.1.1.1"))
    path = ws.root / "browser.json"
    write_json(
        path,
        {
            "url": "https://x.com/a/status/123",
            "title": "A post",
            "text": "Company cash 10",
            "completeness": "complete",
            "completeness_reason": "Read all post text",
            "capture_method": "authenticated-browser",
        },
    )
    result = CliRunner().invoke(app, ["--root", str(ws.root), "browser-capture", str(path)])
    assert result.exit_code == 0
    assert json.loads(result.stdout)["kind"] == "x"


def test_self_corroboration_with_social_reference_is_rejected(ws, monkeypatch):
    monkeypatch.setattr("investing_research.x.search", lambda *a, **k: search_result())
    run = collect(ws)
    social_id = run["candidates"][0]["capture_id"]
    web, _ = ws.capture_record(
        {
            "url": "https://example.com/report",
            "sha256": "b" * 64,
            "kind": "html",
            "completeness": "complete",
            "files": [],
        }
    )
    run["candidates"] = [{"company_id": "asx-mlx", "capture_id": web["id"]}]
    write_json(ws.root / "state/runs" / f"{run['id']}.json", run)
    row = decisions(run, True)[0]
    row.verification = "corroborated"
    row.corroborating_sources = [web["id"], social_id]
    with pytest.raises(ValueError, match="complete non-social"):
        review(ws, run["id"], [row])


def test_metadata_only_model_cannot_justify_buy(ws):
    source, _ = ws.capture_record(
        {
            "url": "https://example.com/report",
            "sha256": "b" * 64,
            "kind": "html",
            "completeness": "complete",
            "files": [],
        }
    )
    model = ws.root / "companies/asx-mlx/models/invalid/model.json"
    write_json(model, {"company_id": "asx-mlx", "currency": "AUD"})
    value = Recommendation(
        company_id="asx-mlx",
        action="buy",
        as_of="2026-09-20",
        horizon="3 years",
        thesis="Test",
        counterarguments=[],
        catalysts=[],
        entry_conditions=[],
        invalidation_conditions=[],
        confidence_rationale="test",
        limitations=[],
        source_ids=[source["id"]],
        model_path=ws.relative(model),
        price=1,
        price_date="2026-09-18",
    )
    with pytest.raises(ValueError, match="generated model"):
        add_recommendation(ws, value)


def test_actionable_recommendation_currency_must_match_company(ws):
    source, _ = ws.capture_record(
        {
            "url": "https://example.com/report",
            "sha256": "b" * 64,
            "kind": "html",
            "completeness": "complete",
            "files": [],
        }
    )
    model = ws.root / "companies/asx-mlx/models/mismatch/model.json"
    write_json(model, {"company_id": "asx-mlx", "currency": "USD"})
    value = Recommendation(
        company_id="asx-mlx",
        action="buy",
        as_of="2026-09-20",
        horizon="3 years",
        thesis="Test",
        counterarguments=[],
        catalysts=[],
        entry_conditions=[],
        invalidation_conditions=[],
        confidence_rationale="test",
        limitations=[],
        source_ids=[source["id"]],
        model_path=ws.relative(model),
        price=1,
        price_date="2026-09-18",
    )
    with pytest.raises(ValueError, match="trading currency"):
        add_recommendation(ws, value)


def test_revalidate_existing_workbook_after_engine_becomes_available(ws, monkeypatch):
    from investing_research.models import run_model

    monkeypatch.setattr(
        "investing_research.workbook.verify_workbook",
        lambda *args: {"status": "unverified", "reason": "engine absent"},
    )
    source = Path(__file__).parents[1] / "examples/model-mine.json"
    result = run_model(source, ws.root / "companies/demo-mine/models")
    model = Path(result["output_dir"]) / "model.json"
    original = model.read_bytes()
    monkeypatch.setattr("investing_research.workbook.verify_workbook", lambda *args: {"status": "passed"})
    output = CliRunner().invoke(app, ["--root", str(ws.root), "validate-workbook", str(model)])
    assert output.exit_code == 0, output.stdout
    assert json.loads(output.stdout)["status"] == "passed"
    assert model.read_bytes() == original
    assert len(list(model.parent.glob("validation-*.json"))) == 1
