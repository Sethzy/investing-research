"""Append-only research revisions; current Markdown is a rebuildable projection."""

from __future__ import annotations

from datetime import date
from pathlib import Path
from typing import Annotated, Literal

from pydantic import Field, TypeAdapter, model_validator

from .contracts import Record
from .workspace import Workspace, atomic_text, digest, now, read_json, write_json


class Revision(Record):
    company_id: str
    key: str = Field(pattern=r"^[a-z0-9][a-z0-9-]{0,79}$")
    previous: str | None = None
    as_of: date
    rationale: str = Field(min_length=1)
    source_ids: list[str] = Field(default_factory=list)


class Pillar(Revision):
    kind: Literal["pillar"]
    claim: str = Field(min_length=1)
    expectation: str = Field(min_length=1)
    invalidation: str = Field(min_length=1)
    status: Literal["unresolved", "strengthening", "weakening", "invalidated"]
    evidence_status: Literal["unverified", "corroborated", "contradicted", "unresolved"]


class Catalyst(Revision):
    kind: Literal["catalyst"]
    title: str = Field(min_length=1)
    event_date: date | None = None
    date_basis: Literal["unknown", "estimated", "confirmed"]
    status: Literal["upcoming", "occurred", "cancelled"]
    expectation: str = Field(min_length=1)
    outcome: str | None = None

    @model_validator(mode="after")
    def consistent(self):
        if (self.event_date is None) != (self.date_basis == "unknown"):
            raise ValueError("Unknown date must be blank; estimated/confirmed dates require a date")
        if self.status == "occurred" and self.event_date and self.event_date > self.as_of:
            raise ValueError("Occurred catalyst date cannot follow its as-of date")
        if self.status == "occurred" and not self.outcome:
            raise ValueError("Occurred catalysts require an outcome")
        return self


class Query(Record):
    query: str = Field(min_length=1, max_length=500)
    intent: Literal["identity", "contrary", "specialist", "event", "industry"]
    reason: str = Field(min_length=1)


class QueryPlan(Revision):
    kind: Literal["queries"]
    key: Literal["x-plan"] = "x-plan"
    queries: list[Query] = Field(min_length=1, max_length=6)

    @model_validator(mode="after")
    def distinct(self):
        if len({q.query for q in self.queries}) != len(self.queries):
            raise ValueError("Duplicate query")
        if not any(q.intent == "contrary" for q in self.queries):
            raise ValueError("Include a search for disconfirming evidence")
        if any(
            any(t in q.query.lower() for t in ("since:", "until:")) or "\n" in q.query for q in self.queries
        ):
            raise ValueError("Collection owns query dates; omit since/until operators and newlines")
        return self


Event = Annotated[Pillar | Catalyst | QueryPlan, Field(discriminator="kind")]
ADAPTER = TypeAdapter(Event)


def history(ws: Workspace, company_id: str) -> list[dict]:
    ws.company(company_id)
    events = sorted(
        (read_json(p) for p in (ws.root / "state/research" / company_id).glob("*.json")),
        key=lambda e: e["sequence"],
    )
    heads = {}
    for sequence, event in enumerate(events, 1):
        data = ADAPTER.validate_python(event["data"]).model_dump(mode="json")
        key = (data["kind"], data["key"])
        if (
            event["id"] != digest(data)
            or event["sequence"] != sequence
            or data["company_id"] != company_id
            or data["previous"] != heads.get(key)
        ):
            raise ValueError("Research history integrity check failed")
        heads[key] = event["id"]
    return events


def latest(ws: Workspace, company_id: str) -> dict:
    return {(e["data"]["kind"], e["data"]["key"]): e for e in history(ws, company_id)}


def append(ws: Workspace, payload: dict) -> dict:
    """Caller holds workspace lock. An exact retry is idempotent; stale updates fail."""
    data = ADAPTER.validate_python(payload).model_dump(mode="json")
    events = history(ws, data["company_id"])
    identity = digest(data)
    existing = next((e for e in events if e["id"] == identity), None)
    if existing:
        rebuild(ws, data["company_id"])
        return existing
    key = data["kind"], data["key"]
    previous = next((e for e in reversed(events) if (e["data"]["kind"], e["data"]["key"]) == key), None)
    if data["previous"] != (previous["id"] if previous else None):
        raise ValueError(
            "Stale research revision: supply the current previous ID; history is never overwritten"
        )
    captures = ws.captures()
    if set(data["source_ids"]) - captures.keys():
        raise ValueError("Unknown research source")
    needs_primary = data.get("evidence_status") == "corroborated" or data.get("date_basis") == "confirmed"
    if needs_primary and not any(
        captures[s].get("kind") != "x" and captures[s].get("completeness") == "complete"
        for s in data["source_ids"]
    ):
        raise ValueError("Corroborated claims/confirmed dates require complete non-social evidence")
    if data["as_of"] > date.today().isoformat():
        raise ValueError("Research as-of date cannot be in the future")
    event = {"id": identity, "sequence": len(events) + 1, "recorded_at": now(), "data": data}
    path = ws.root / "state/research" / data["company_id"] / f"{event['sequence']:08d}-{identity}.json"
    if path.exists():
        raise ValueError("Research record already exists")
    write_json(path, event)
    rebuild(ws, data["company_id"])
    return event


def rebuild(ws: Workspace, company_id: str) -> Path:
    from .reports import cell, link

    events = history(ws, company_id)
    heads = latest(ws, company_id)
    folder = ws.root / "companies" / company_id
    lines = [
        f"# {company_id} — living research",
        "",
        "Current view rebuilt from immutable revisions. Original claims, forecasts and outcomes remain in the history below.",
        "",
        "## Thesis scorecard",
        "",
        "| Pillar | Original expectation | Current expectation | Status / evidence | Invalidation |",
        "|---|---|---|---|---|",
    ]
    for (kind, key), event in heads.items():
        d = event["data"]
        if kind == "pillar":
            original = next(
                e["data"] for e in events if e["data"]["kind"] == kind and e["data"]["key"] == key
            )
            lines.append(
                "| "
                + " | ".join(
                    cell(v)
                    for v in (
                        d["claim"],
                        original["expectation"],
                        d["expectation"],
                        d["status"] + " / " + d["evidence_status"],
                        d["invalidation"],
                    )
                )
                + " |"
            )
    lines += [
        "",
        "## Catalyst calendar",
        "",
        "| Date / basis | Event | Status | Prior expectation | Outcome |",
        "|---|---|---|---|---|",
    ]
    catalysts = sorted(
        (e for (kind, _), e in heads.items() if kind == "catalyst"),
        key=lambda e: e["data"].get("event_date") or "9999",
    )
    for e in catalysts:
        d = e["data"]
        original = next(
            v["data"] for v in events if v["data"]["kind"] == "catalyst" and v["data"]["key"] == d["key"]
        )
        status = d["status"]
        if d["event_date"] and d["event_date"] < date.today().isoformat() and status == "upcoming":
            status = "overdue — verify outcome/date"
        lines.append(
            "| "
            + " | ".join(
                cell(v)
                for v in (
                    f"{d['event_date'] or 'Unknown'} / {d['date_basis']}",
                    d["title"],
                    status,
                    original["expectation"],
                    d["outcome"] or "Not recorded",
                )
            )
            + " |"
        )
    plan = heads.get(("queries", "x-plan"))
    if plan:
        lines += [
            "",
            "## Current X research plan",
            "",
            f"Revision `{plan['id']}`; collection remains bounded and requires your own login.",
            "",
        ]
        lines += [f"- **{q['intent']}**: `{q['query']}` — {q['reason']}" for q in plan["data"]["queries"]]
    lines += ["", "## Append-only history", ""]
    captures = ws.captures()
    for e in reversed(events):
        d = e["data"]
        path = ws.root / "state/research" / company_id / f"{e['sequence']:08d}-{e['id']}.json"
        citations = " ".join(f"[Source]({captures[s]['url']})" for s in d["source_ids"])
        lines += [
            f"- {d['as_of']} · {d['kind']}/{d['key']} · [revision {e['sequence']}]({link(path, folder)}): {d['rationale']} {citations}"
        ]
    target = folder / "research.md"
    atomic_text(target, "\n".join(line.rstrip() for line in lines).rstrip() + "\n")
    return target
