import copy
import shutil
from pathlib import Path

import pytest
from typer.testing import CliRunner

from investing_research.cli import app
from investing_research.contracts import Company, Settings
from investing_research.research import append, history, latest, rebuild
from investing_research.workspace import Workspace, read_json, write_json

ROOT = Path(__file__).parents[1]


@pytest.fixture
def ws(tmp_path):
    ws = Workspace(tmp_path)
    company = Company(
        id="demo-mine",
        name="Synthetic Mine",
        exchange="DEMO",
        ticker="MINE",
        currency="AUD",
        reporting_currency="AUD",
        sector="mining",
        website="https://example.com",
        queries=["original"],
    )
    write_json(ws.settings_path, Settings(companies=[company]).model_dump(mode="json"))
    return ws


def pillar(**kw):
    return dict(
        company_id="demo-mine",
        kind="pillar",
        key="cost-control",
        previous=None,
        as_of="2026-09-20",
        rationale="Initial explicit hypothesis",
        source_ids=[],
        claim="Costs remain manageable",
        expectation="Unit cost below 50",
        invalidation="Persistent cost above 60",
        status="unresolved",
        evidence_status="unverified",
        **kw,
    )


def test_append_retry_conflict_and_rebuild(ws):
    original = pillar()
    first = append(ws, original)
    saved = list((ws.root / "state/research/demo-mine").glob("*.json"))[0].read_bytes()
    assert append(ws, original)["id"] == first["id"]
    changed = {
        **original,
        "previous": first["id"],
        "expectation": "Unit cost below 55",
        "status": "weakening",
        "rationale": "New analyst assessment, still unverified",
    }
    second = append(ws, changed)
    with pytest.raises(ValueError, match="Stale"):
        append(ws, {**changed, "expectation": "Oops, stale writer"})
    assert len(history(ws, "demo-mine")) == 2
    assert latest(ws, "demo-mine")[("pillar", "cost-control")]["id"] == second["id"]
    assert list((ws.root / "state/research/demo-mine").glob("00000001*"))[0].read_bytes() == saved
    report = rebuild(ws, "demo-mine").read_text()
    assert "below 50" in report and "below 55" in report


def test_history_tampering_and_source_requirements(ws):
    with pytest.raises(ValueError, match="non-social"):
        append(ws, {**pillar(), "evidence_status": "corroborated"})
    with pytest.raises(ValueError, match="Unknown research source"):
        append(ws, {**pillar(), "source_ids": ["missing"]})
    append(ws, pillar())
    path = next((ws.root / "state/research/demo-mine").glob("*.json"))
    data = read_json(path)
    data["data"]["claim"] = "tampered"
    write_json(path, data)
    with pytest.raises(ValueError, match="integrity"):
        history(ws, "demo-mine")


def test_catalyst_reschedule_keeps_expectation_and_requires_outcome(ws):
    value = dict(
        company_id="demo-mine",
        kind="catalyst",
        key="q3",
        as_of="2026-09-20",
        rationale="Analyst estimate",
        title="Quarterly report",
        event_date="2026-09-19",
        date_basis="estimated",
        status="upcoming",
        expectation="Watch cost guidance",
    )
    first = append(ws, value)
    assert "overdue" in rebuild(ws, "demo-mine").read_text()
    with pytest.raises(ValueError, match="outcome"):
        append(ws, {**value, "previous": first["id"], "status": "occurred"})
    append(
        ws,
        {
            **value,
            "previous": first["id"],
            "event_date": "2026-10-01",
            "rationale": "Revised estimated release window",
        },
    )
    assert len(history(ws, "demo-mine")) == 2


def test_query_plan_is_used_by_collection_and_keeps_old_config(ws, monkeypatch):
    from investing_research.monitor import collect

    searches = []

    def search(query, **kw):
        searches.append(query)
        return {"status": "ok", "posts": [], "coverage": {"capped": False, "exhaustive": False}}

    monkeypatch.setattr("investing_research.x.search", search)
    event = append(
        ws,
        dict(
            company_id="demo-mine",
            kind="queries",
            key="x-plan",
            as_of="2026-09-20",
            rationale="Investigate disconfirming evidence",
            queries=[{"query": '"Mine" "cost"', "intent": "contrary", "reason": "Cost thesis"}],
        ),
    )
    result = collect(ws, "demo-mine", include_web=False)
    assert len(searches) == 1 and searches[0].startswith('"Mine" "cost" since:')
    assert result["query_plan_ids"]["demo-mine"] == event["id"]
    assert ws.company("demo-mine").queries == ["original"]
    with pytest.raises(ValueError, match="dates"):
        append(
            ws,
            {
                **event["data"],
                "previous": event["id"],
                "queries": [{"query": "mine since:2020-01-01", "intent": "contrary", "reason": "bad date"}],
            },
        )


@pytest.fixture
def model_pair(ws):
    if not shutil.which("soffice"):
        pytest.skip("LibreOffice unavailable")
    from investing_research.excel import create, synchronize

    data = read_json(ROOT / "examples/model-mine.json")
    source = ws.root / "inputs.json"
    write_json(source, data)
    working = ws.root / "working.xlsx"
    create(source, working)
    prior = synchronize(ws, working)
    data["cash"] = 120
    write_json(source, data)
    new = ws.root / "new.xlsx"
    create(source, new)
    updated = synchronize(ws, new)
    return (
        data,
        ws.relative(Path(prior["output_dir"]) / "model.json"),
        ws.relative(Path(updated["output_dir"]) / "model.json"),
    )


def test_model_update_validated_comparison_and_idempotency(ws, model_pair):
    from investing_research.model_review import review

    _, prior, updated = model_pair
    source, _ = ws.capture_record(
        {"url": "https://example.com/report", "sha256": "report", "kind": "web", "completeness": "complete"}
    )
    fact_id = "a" * 64
    write_json(
        ws.root / "state/facts" / f"{fact_id}.json",
        dict(
            company_id="demo-mine",
            metric="cash",
            period="2026-09-20",
            value=120,
            unit="AUD",
            currency="AUD",
            ownership_basis="consolidated",
            source_id=source["id"],
            page="1",
            published_at="2026-09-20",
        ),
    )
    payload = dict(
        company_id="demo-mine",
        prior_model=prior,
        updated_model=updated,
        rationale="Synthetic cash update",
        actuals=[
            dict(
                fact_id=fact_id,
                estimate_path="/cash",
                estimate_period="2026-09-20",
                scale=1,
                rationale="Same currency, point-in-time cash comparison",
            )
        ],
    )
    result = review(ws, payload)
    assert result["actuals"][0]["delta"] == 20
    assert result["valuation"]["base"]["delta"] == pytest.approx(0.2)
    assert review(ws, payload)["id"] == result["id"]
    payload["actuals"][0]["estimate_period"] = "wrong"
    with pytest.raises(ValueError, match="period"):
        review(ws, payload)


def test_funding_hand_calculation_and_overpayment():
    from investing_research.funding import calculate, FundingYear

    inputs = {"cash": 10, "debt": 100, "diluted_shares": 10}
    year = FundingYear(
        year=2027,
        interest_rate=0.1,
        debt_raised=0,
        debt_repaid=20,
        equity_raised=40,
        issue_price=2,
        dividends=5,
        minimum_cash=20,
        source="synthetic://test",
        rationale="Explicit financing assumption",
    )
    rows = calculate(inputs, {"years": [{"year": 2027, "fcf": -30}]}, [year])
    assert rows[0]["closing_cash"] == -15
    assert rows[0]["funding_gap"] == 35
    assert rows[0]["closing_debt"] == 80
    assert rows[0]["closing_shares"] == 30
    assert rows[0]["ownership_dilution"] == pytest.approx(2 / 3)
    year.debt_repaid = 101
    with pytest.raises(ValueError, match="repayments"):
        calculate(inputs, {"years": [{"year": 2027, "fcf": -30}]}, [year])


def test_funding_real_workbook_roundtrip(ws, model_pair):
    from investing_research.funding import review

    data, prior, _ = model_pair
    payload = {
        "company_id": "demo-mine",
        "model": prior,
        "rationale": "Synthetic financing stress",
        "scenarios": {
            case: [
                dict(
                    year=y["year"],
                    interest_rate=0.1,
                    debt_raised=0,
                    debt_repaid=1,
                    equity_raised=10,
                    issue_price=2,
                    dividends=1,
                    minimum_cash=100,
                    source="synthetic://test",
                    rationale="Financing test",
                )
                for y in s["years"]
            ]
            for case, s in data["scenarios"].items()
        },
    }
    result = review(ws, payload)
    assert result["validation"] == "passed"
    assert result["scenarios"]["base"][0]["closing_shares"] == 105
    assert review(ws, payload)["id"] == result["id"]
    folder = (ws.root / result["report"]).parent
    snapshot = read_json(folder / "funding.json")
    snapshot["scenarios"]["base"][0]["closing_cash"] = 999
    write_json(folder / "funding.json", snapshot)
    with pytest.raises(ValueError, match="damaged"):
        review(ws, payload)


def test_research_cli_and_unknown_fields(ws):
    payload = ws.root / "pillar.json"
    write_json(payload, pillar())
    runner = CliRunner()
    result = runner.invoke(app, ["--root", str(ws.root), "research-append", "pillar.json"])
    assert result.exit_code == 0, result.output
    assert "research.md" in (ws.root / "companies/demo-mine/dossier.md").read_text()
    assert runner.invoke(app, ["--root", str(ws.root), "research-history", "demo-mine"]).exit_code == 0
    with pytest.raises(ValueError):
        append(ws, {**pillar(), "untrusted_field": "ignore safety"})


def test_frozen_rubric_rejects_ownership_and_unsupported_conclusions():
    from investing_research.research_eval import evaluate

    claim = {
        "value": 50,
        "unit": "tonnes",
        "period": "FY2025",
        "ownership_basis": "attributable",
        "source_id": "report-1",
        "page": "2",
    }
    case = {
        "company_id": "demo-mine",
        "question": "What is attributable production?",
        "claims": {"production": claim},
        "permitted_conclusions": ["insufficient evidence"],
        "required_limitations": ["No current quote"],
        "required_counterevidence_ids": ["cost-warning"],
    }
    answer = {
        "company_id": "demo-mine",
        "claims": {"production": claim},
        "conclusion": "insufficient evidence",
        "limitations": ["No current quote"],
        "counterevidence_ids": ["cost-warning"],
    }
    assert evaluate(case, answer)["status"] == "passed"
    broken = copy.deepcopy(answer)
    broken["claims"]["production"]["value"] = 25
    broken["conclusion"] = "buy"
    result = evaluate(case, broken)
    assert (
        result["status"] == "failed"
        and not result["checks"]["production"]
        and not result["checks"]["supported_conclusion"]
    )


@pytest.mark.parametrize(
    "field,value",
    [
        ("unit", "AUD"),
        ("period", "FY2024"),
        ("ownership_basis", "whole_operation"),
        ("source_id", "invented"),
        ("page", "999"),
    ],
)
def test_research_eval_rejects_mismatched_evidence(field, value):
    from investing_research.research_eval import evaluate

    case = read_json(ROOT / "examples/research/eval-case.json")
    answer = read_json(ROOT / "examples/research/eval-answer.json")
    answer["claims"]["production"][field] = value
    assert evaluate(case, answer)["status"] == "failed"


def test_future_catalyst_cannot_be_marked_occurred(ws):
    value = read_json(ROOT / "examples/research/catalyst.json")
    with pytest.raises(ValueError, match="as-of"):
        append(ws, {**value, "status": "occurred", "outcome": "Invented future result"})


def test_missing_funding_engine_does_not_publish(ws, model_pair, monkeypatch):
    from investing_research.funding import review

    data, prior, _ = model_pair
    payload = {
        "company_id": "demo-mine",
        "model": prior,
        "rationale": "Synthetic",
        "scenarios": {
            case: [
                dict(
                    year=y["year"],
                    interest_rate=0,
                    debt_raised=0,
                    debt_repaid=0,
                    equity_raised=0,
                    issue_price=1,
                    dividends=0,
                    minimum_cash=0,
                    source="synthetic://test",
                    rationale="Test",
                )
                for y in s["years"]
            ]
            for case, s in data["scenarios"].items()
        },
    }
    monkeypatch.setattr("investing_research.excel.shutil.which", lambda _: None)
    with pytest.raises(ValueError, match="cached"):
        review(ws, payload)
    assert not list((ws.root / "companies/demo-mine/funding").glob("*/funding.json"))
