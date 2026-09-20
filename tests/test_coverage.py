import copy

import pytest

from investing_research.coverage import CATEGORIES, STAGES, CoverageReview, reader_gaps, save
from investing_research.contracts import Company, Settings
from investing_research.workspace import Workspace, write_json


def request():
    return dict(company_id="demo-mine", researched_at="2026-09-20T05:00:00Z", mode="research_update",
                web_checked_at=None, x_checked_at=None, x_status="not_run", x_scope="Not searched",
                items=[dict(category=c, question="What is supported?", period="Not established",
                            source_ids=[], stages={s: "pending" for s in STAGES}, conclusion="Unresolved",
                            model_implication="No change", gap="Evidence missing", next_step="Read primary source")
                       for c in sorted(CATEGORIES)])


def test_gaps_are_valid_but_not_complete(tmp_path):
    ws = Workspace(tmp_path)
    company = Company(id="demo-mine", name="Demo", exchange="DEMO", ticker="D", currency="AUD",
                      reporting_currency="AUD", sector="mining", website="https://example.com", queries=["demo-mine"])
    write_json(ws.settings_path, Settings(companies=[company]).model_dump(mode="json"))
    review = CoverageReview.model_validate(request())
    result = save(ws, review)
    assert not result["complete"]
    assert save(ws, review)["id"] == result["id"]
    assert len(list((tmp_path / "companies/demo-mine/coverage").glob("*/review.json"))) == 1


@pytest.mark.parametrize("change", ["category", "gap", "analysis", "model", "time", "read"])
def test_false_completion_rejected(change):
    value = copy.deepcopy(request())
    item = value["items"][0]
    if change == "category":
        value["items"].pop()
    elif change == "gap":
        item["gap"] = ""
    elif change == "analysis":
        item["stages"]["analyzed"] = "done"
    elif change == "model":
        item["stages"]["model_used"] = "done"
    elif change == "time":
        value["x_status"] = "searched"
    elif change == "read":
        item["source_ids"] = ["source"]
        item["stages"]["captured"] = "done"
        item["stages"]["analyzed"] = "done"
        item["analysis_path"] = "report.md"
    with pytest.raises(ValueError):
        CoverageReview.model_validate(value)


def test_reader_prose_does_not_substitute_for_sections():
    assert "valuation" in reader_gaps("We mention valuation but supply no analysis. [Excel](model.xlsx)")
    headings = "\n".join("## " + title for title in ["What changed", "Historical cash generation", "Valuation",
        "Projects and funding", "Industry and opposing case", "Investor discussion", "What remains unresolved"])
    assert reader_gaps(headings) == ["detailed Excel link"]
    assert not reader_gaps(headings + "\n[Detailed model](model.xlsx)")
