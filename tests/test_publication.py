import json
import shutil
from pathlib import Path

import pytest

from investing_research.publication import sha256, validate_decision, validate_release
from datetime import datetime
from test_coverage import request

ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture
def edition(tmp_path):
    for name in ("model.xlsx", "model.json", "inputs.json"):
        shutil.copy2(ROOT / "examples/mlx" / name, tmp_path / name)
    model = json.loads((tmp_path / "model.json").read_text())
    coverage = request()
    coverage["company_id"] = model["company_id"]
    (tmp_path / "coverage.json").write_text(json.dumps(coverage))
    headings = ["What changed", "Historical cash generation", "Valuation", "Projects and funding",
                "Industry and opposing case", "Investor discussion", "What remains unresolved"]
    text = "\n".join("## " + h for h in headings) + "\n[Excel](model.xlsx)\n"
    text += "\n".join(f'| {c.title()} | {model["scenarios"][c]["per_share"]:.2f} |' for c in ("bear", "base", "bull"))
    (tmp_path / "review.md").write_text(text)
    coverage["artifact_sha256"] = {"review.md": sha256(tmp_path / "review.md"),
                                  "model.json": sha256(tmp_path / "model.json")}
    (tmp_path / "coverage.json").write_text(json.dumps(coverage))
    value = dict(schema_version=1, company_id=model["company_id"],
                 research_cutoff=coverage["researched_at"], valuation_class=model["purpose"],
                 files={role: {"path": name, "sha256": sha256(tmp_path / name)} for role, name in
                        [("report", "review.md"), ("workbook", "model.xlsx"), ("model", "model.json"),
                         ("inputs", "inputs.json"), ("coverage", "coverage.json")]})
    (tmp_path / "release.json").write_text(json.dumps(value))
    return tmp_path, value


def test_partial_briefing_can_publish(edition):
    root, _ = edition
    assert validate_release(root / "review.md", root / "release.json")["status"] == "passed"


@pytest.mark.parametrize('change', ['none', 'rating', 'hidden', 'late', 'blocker', 'date', 'trigger'])
def test_decision_opinion_contract(change):
    decision = dict(opinion='Not rated', as_of='2026-09-20', horizon='24 months',
                    rationale='Project economics could reverse the assessment.',
                    next_checkpoint='Next reserve update', previous_assessment='Previously unpriced',
                    blocker='Funding unknown', change_triggers=['Publish capital schedule'])
    text = '# Company\n## Executive summary and investment opinion\n**Opinion: Not rated**\n'
    text += '\n'.join([decision[k] for k in ['horizon', 'rationale', 'next_checkpoint', 'previous_assessment', 'blocker']])
    text += '\nPublish capital schedule\n## Business\n'
    if change == 'rating':
        decision['opinion'] = 'Hold'
        text = text.replace('Not rated', 'Hold')
    elif change == 'hidden':
        text = text.replace('**Opinion: Not rated**', '')
    elif change == 'late':
        text = '## Background\n' + text
    elif change == 'blocker':
        decision.pop('blocker')
    elif change == 'date':
        decision['as_of'] = '2026-09-19'
    elif change == 'trigger':
        text = text.replace('Publish capital schedule', '')
    if change == 'none':
        validate_decision(text, decision, {'purpose': 'illustrative_sensitivity'}, datetime.fromisoformat('2026-09-20T08:00:00Z'))
    else:
        with pytest.raises(ValueError):
            validate_decision(text, decision, {'purpose': 'illustrative_sensitivity'}, datetime.fromisoformat('2026-09-20T08:00:00Z'))


@pytest.mark.parametrize("mutation", ["edited", "headline", "link", "company", "cutoff", "promotion", "escape"])
def test_release_mismatch_rejected(edition, mutation):
    root, value = edition
    report = root / "review.md"
    if mutation in {"edited", "headline", "link"}:
        text = report.read_text()
        text = text + "\nChanged" if mutation == "edited" else text.replace("| Base |", "| Wrong |") if mutation == "headline" else text.replace("model.xlsx)", "other.xlsx)")
        report.write_text(text)
        if mutation != "edited":
            value["files"]["report"]["sha256"] = sha256(report)
            coverage_path = root / "coverage.json"
            coverage = json.loads(coverage_path.read_text())
            coverage["artifact_sha256"]["review.md"] = sha256(report)
            coverage_path.write_text(json.dumps(coverage))
            value["files"]["coverage"]["sha256"] = sha256(coverage_path)
    elif mutation == "company":
        value["company_id"] = "wrong-company"
    elif mutation == "cutoff":
        value["research_cutoff"] = "2026-09-21T05:00:00Z"
    elif mutation == "promotion":
        value["valuation_class"] = "valuation"
    else:
        value["files"]["report"]["path"] = "../outside.md"
    (root / "release.json").write_text(json.dumps(value))
    with pytest.raises(ValueError):
        validate_release(report, root / "release.json")
