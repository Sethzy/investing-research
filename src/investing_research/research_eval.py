"""Offline research-answer rubric. Structured evidence checks, not an LLM judge."""

import math
from typing import Literal

from pydantic import Field

from .contracts import Record


class Claim(Record):
    value: float
    unit: str
    period: str
    ownership_basis: str
    source_id: str
    page: str


class ResearchAnswer(Record):
    company_id: str
    claims: dict[str, Claim]
    conclusion: Literal["buy", "hold", "sell", "insufficient evidence"]
    limitations: list[str]
    counterevidence_ids: list[str]


class ResearchCase(Record):
    company_id: str
    question: str
    claims: dict[str, Claim]
    permitted_conclusions: list[str]
    required_limitations: list[str]
    required_counterevidence_ids: list[str]
    tolerance: float = Field(default=1e-8, ge=0, le=0.001)


def evaluate(case_payload, answer_payload):
    case = ResearchCase.model_validate(case_payload)
    answer = ResearchAnswer.model_validate(answer_payload)
    checks = {
        "company_identity": answer.company_id == case.company_id,
        "claim_set": set(answer.claims) == set(case.claims),
        "supported_conclusion": answer.conclusion in case.permitted_conclusions,
        "limitations": set(case.required_limitations).issubset(answer.limitations),
        "counterevidence": set(case.required_counterevidence_ids).issubset(answer.counterevidence_ids),
    }
    for name, expected in case.claims.items():
        actual = answer.claims.get(name)
        checks[name] = (
            actual is not None
            and all(
                getattr(actual, k) == getattr(expected, k)
                for k in ("unit", "period", "ownership_basis", "source_id", "page")
            )
            and math.isclose(actual.value, expected.value, rel_tol=case.tolerance, abs_tol=case.tolerance)
        )
    return {
        "status": "passed" if all(checks.values()) else "failed",
        "score": sum(checks.values()) / len(checks),
        "checks": checks,
        "scope": "Frozen structured-answer rubric only; narrative quality and source interpretation still require human/Codex review.",
    }
