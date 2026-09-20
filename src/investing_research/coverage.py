"""Evidence progress is explicit; document collection never implies analysis."""

from datetime import datetime
import hashlib
import re
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

from .workspace import Workspace, atomic_text, digest, now, write_json

CATEGORIES = {"filings", "management", "industry", "peers", "counterevidence", "x", "regulatory"}
STAGES = ("captured", "read", "extracted", "reconciled", "analyzed", "model_used")


def reader_gaps(text: str) -> list[str]:
    required = {
        "changes": r"what changed", "history": r"historical|cash generation",
        "valuation": r"valuation", "development and funding": r"projects? and funding|rentails.*funding",
        "industry and contrary case": r"industry.*opposing|tin market",
        "social research": r"discussing on x|investor discussion", "coverage": r"what remains unresolved",
    }
    headings = "\n".join(line.lower() for line in text.splitlines() if line.startswith("#"))
    missing = [name for name, pattern in required.items() if not re.search(pattern, headings)]
    if not re.search(r"\[[^]]+\]\([^)]*\.xlsx\)", text):
        missing.append("detailed Excel link")
    return missing


class CoverageItem(BaseModel):
    model_config = ConfigDict(extra="forbid")
    category: Literal["filings", "management", "industry", "peers", "counterevidence", "x", "regulatory"]
    question: str = Field(min_length=1)
    period: str = Field(min_length=1)
    source_ids: list[str] = []
    stages: dict[str, Literal["done", "partial", "pending", "not_applicable"]]
    conclusion: str = Field(min_length=1)
    model_implication: str = Field(min_length=1)
    gap: str = ""
    next_step: str = ""
    analysis_path: str | None = None
    model_path: str | None = None
    fact_ids: list[str] = []
    reconciliation: str = ""

    @model_validator(mode="after")
    def check_progress(self):
        if set(self.stages) != set(STAGES):
            raise ValueError("Record every evidence stage explicitly")
        for stage in STAGES[1:]:
            if self.stages[stage] == "done" and self.stages["captured"] != "done":
                raise ValueError("Completed work requires captured evidence")
            if stage != "read" and self.stages[stage] == "done" and self.stages["read"] != "done":
                raise ValueError("Completed work requires reading the evidence")
        if self.stages["model_used"] == "done" and any(
            self.stages[s] != "done" for s in ("extracted", "reconciled", "analyzed")
        ):
            raise ValueError("Model use requires extraction, reconciliation and analysis")
        if self.stages["captured"] == "done" and not self.source_ids:
            raise ValueError("Captured evidence requires source IDs")
        if self.stages["analyzed"] == "done" and not self.analysis_path:
            raise ValueError("Analysis requires its saved path")
        if self.stages["reconciled"] == "done" and not self.reconciliation:
            raise ValueError("Reconciliation requires an explanation")
        if self.stages["model_used"] == "done" and (not self.model_path or not self.fact_ids):
            raise ValueError("Model use requires a model and fact IDs")
        if any(v in {"partial", "pending"} for v in self.stages.values()) and not (self.gap and self.next_step):
            raise ValueError("Incomplete work requires a gap and next step")
        return self


class CoverageReview(BaseModel):
    model_config = ConfigDict(extra="forbid")
    company_id: str
    researched_at: datetime
    mode: Literal["research_update", "re_export"]
    web_checked_at: datetime | None = None
    x_checked_at: datetime | None = None
    x_status: Literal["searched", "failed", "not_run"]
    x_scope: str = Field(min_length=1)
    items: list[CoverageItem]

    @model_validator(mode="after")
    def check_scope(self):
        if {i.category for i in self.items} != CATEGORIES:
            raise ValueError("All seven coverage categories must be recorded, including gaps")
        if self.x_status != "not_run" and self.x_checked_at is None:
            raise ValueError("X attempt requires its actual check time")
        for value in (self.researched_at, self.web_checked_at, self.x_checked_at):
            if value and value.utcoffset() is None:
                raise ValueError("Research timestamps require a timezone")
        if any(t and t > self.researched_at for t in (self.web_checked_at, self.x_checked_at)):
            raise ValueError("Checks cannot follow the research cutoff")
        return self


def save(workspace: Workspace, review: CoverageReview) -> dict:
    workspace.company(review.company_id)
    captures = workspace.captures()
    from .workspace import read_json
    for item in review.items:
        if set(item.source_ids) - captures.keys():
            raise ValueError("Unknown coverage source")
        for path in (item.analysis_path, item.model_path):
            if path and not workspace.inside(path).is_file():
                raise ValueError("Coverage references a missing artifact")
        for fact_id in item.fact_ids:
            fact = read_json(workspace.inside(f"state/facts/{fact_id}.json"))
            if not fact or fact["company_id"] != review.company_id or fact["source_id"] not in item.source_ids:
                raise ValueError("Coverage fact must belong to this company and its cited sources")
        if item.category == "x" and item.stages["model_used"] == "done":
            raise ValueError("Social evidence cannot establish model facts")
    data = review.model_dump(mode="json")
    data["artifact_sha256"] = {
        path: hashlib.sha256(workspace.inside(path).read_bytes()).hexdigest()
        for item in review.items for path in (item.analysis_path, item.model_path) if path
    }
    identity = digest(data)
    folder = workspace.root / "companies" / review.company_id / "coverage" / identity[:16]
    if not (folder / "review.json").exists():
        write_json(folder / "review.json", {**data, "id": identity, "recorded_at": now()})
    lines = ["# Research coverage", "", f"Research cutoff: {review.researched_at.isoformat()}", "",
             f"X: {review.x_status}. {review.x_scope}", "",
             "Capture, reading, extraction, reconciliation, analysis and model use are distinct.", ""]
    for item in review.items:
        lines += [f"## {item.category.title()}: {item.question}", "", f"Period: {item.period}", "",
                  "; ".join(f"{k}: {v}" for k, v in item.stages.items()), "",
                  item.conclusion, "", f"Model implication: {item.model_implication}", "",
                  f"Unresolved: {item.gap or 'None recorded'}", f"Next: {item.next_step or 'Routine monitoring'}", ""]
        lines += [f"- [{captures[s]['title']}]({captures[s]['url']})" for s in item.source_ids]
        lines += [""]
    atomic_text(folder / "report.md", "\n".join(lines))
    return {"id": identity, "report": workspace.relative(folder / "report.md"),
            "complete": review.x_status == "searched" and review.web_checked_at is not None
            and all(i.stages["analyzed"] == "done"
                    and all(v in {"done", "not_applicable"} for v in i.stages.values()) and not i.gap
                    for i in review.items),
            "note": "Declared evidence progress; semantic source review remains required."}
