"""Small portable release boundary; semantic research review remains the author's job."""

import hashlib
import json
import re
from datetime import datetime
from pathlib import Path

from .coverage import CoverageReview, reader_gaps
from .excel import verify_snapshot


def sha256(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def local_file(root, name):
    path = (root / name).resolve()
    if not path.is_relative_to(root.resolve()) or not path.is_file():
        raise ValueError("Release file missing or outside edition")
    return path


def validate_release(report: Path, manifest_path: Path):
    record = json.loads(manifest_path.read_text())
    if record.get("schema_version") != 1:
        raise ValueError("Unsupported release schema")
    root = manifest_path.parent
    files = {}
    for role in ("report", "workbook", "model", "inputs", "coverage"):
        entry = record["files"][role]
        path = local_file(root, entry["path"])
        if sha256(path) != entry["sha256"]:
            raise ValueError(f"Release {role} changed after review")
        files[role] = path
    if report.resolve() != files["report"]:
        raise ValueError("Release belongs to a different reader report")
    if files["workbook"] != files["model"].parent / "model.xlsx" or files["inputs"] != files["model"].parent / "inputs.json":
        raise ValueError("Use one complete synchronized model snapshot")
    text = report.read_text()
    if reader_gaps(text):
        raise ValueError("Reader sections are incomplete")
    links = re.findall(r"\[[^]]+\]\(([^)]*\.xlsx)\)", text)
    if not links or any(local_file(report.parent, link) != files["workbook"] for link in links):
        raise ValueError("Reader Excel link does not match the reviewed workbook")
    model = verify_snapshot(files["model"])
    raw_review = json.loads(files["coverage"].read_text())
    reviewed_hashes = set(raw_review.get("artifact_sha256", {}).values())
    if not {sha256(files["report"]), sha256(files["model"])} <= reviewed_hashes:
        raise ValueError("Evidence review is not bound to this report and model")
    review = CoverageReview.model_validate({k: v for k, v in raw_review.items() if k in CoverageReview.model_fields})
    if model["company_id"] != record["company_id"] or review.company_id != record["company_id"]:
        raise ValueError("Company mismatch in release")
    cutoff = datetime.fromisoformat(record["research_cutoff"])
    if cutoff.utcoffset() is None or cutoff != review.researched_at:
        raise ValueError("Research cutoff differs from evidence review")
    if model["valuation_date"] > cutoff.date().isoformat():
        raise ValueError("Model date follows research cutoff")
    if record["valuation_class"] != model["purpose"]:
        raise ValueError("Release cannot promote model valuation class")
    if model["purpose"] == "valuation":
        material = [i for i in review.items if i.category in {"filings", "management", "regulatory"}]
        if any(i.gap or i.stages["analyzed"] != "done" for i in material):
            raise ValueError("Supported valuation has unresolved material evidence")
    # Use one small explicit table, rather than attempting to parse arbitrary prose.
    matches = re.findall(r"^\| (Bear|Base|Bull) \| (-?[0-9]+\.[0-9]{2}) \|$", text, re.M)
    if len(matches) != 3:
        raise ValueError("Reader needs exactly one scenario table")
    rows = dict(matches)
    for case in ("bear", "base", "bull"):
        expected = f'{model["scenarios"][case]["per_share"]:.2f}'
        if rows.get(case.title()) != expected:
            raise ValueError(f"Reader {case} value differs from the accepted model")
    return {"status": "passed", "company_id": review.company_id,
            "valuation_class": record["valuation_class"], "research_cutoff": record["research_cutoff"],
            "note": "Artifact consistency checked; source interpretation and economic assumptions require review."}
