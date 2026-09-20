"""Validated boundaries for portable configuration and agent-authored decisions."""

from datetime import date
from typing import Literal
from zoneinfo import ZoneInfo

from pydantic import BaseModel, ConfigDict, Field, field_validator


class Record(BaseModel):
    model_config = ConfigDict(extra="forbid", allow_inf_nan=False)


class Company(Record):
    id: str = Field(pattern=r"^[a-z0-9]+-[a-z0-9.-]+$", max_length=80)
    name: str = Field(min_length=1, max_length=150)
    exchange: str
    ticker: str
    currency: str = Field(pattern=r"^[A-Z]{3}$")
    reporting_currency: str = Field(pattern=r"^[A-Z]{3}$")
    sector: str
    aliases: list[str] = Field(default_factory=list)
    queries: list[str] = Field(default_factory=list, max_length=6)
    sources: list[str] = Field(default_factory=list, max_length=30)
    website: str
    holding: bool = False
    gaps: list[str] = Field(default_factory=list)


class Settings(Record):
    browser: Literal["chrome", "firefox", "brave", "edge"] = "chrome"
    profile: str | None = None
    timezone: str = "UTC"
    result_limit: int = Field(default=50, ge=1, le=100)
    budget_minutes: int = Field(default=30, ge=1, le=120)
    companies: list[Company] = Field(default_factory=list)

    @field_validator("timezone")
    @classmethod
    def valid_zone(cls, value: str) -> str:
        ZoneInfo(value)
        return value

    @field_validator("companies")
    @classmethod
    def distinct_companies(cls, companies: list[Company]) -> list[Company]:
        if len({c.id for c in companies}) != len(companies):
            raise ValueError("Duplicate company ID")
        return companies


class Fact(Record):
    company_id: str
    metric: str = Field(min_length=1)
    value: float
    unit: str
    currency: str | None = None
    period: str
    published_at: date
    source_id: str
    page: str = Field(min_length=1)
    entity: str
    ownership_basis: Literal["whole_operation", "attributable", "consolidated"]
    basis: Literal["reported", "adjusted", "guidance"] = "reported"
    note: str = ""


class BrowserCapture(Record):
    url: str
    title: str
    text: str = Field(min_length=1, max_length=2_000_000)
    completeness: Literal["complete", "partial"] = "partial"
    completeness_reason: str = Field(min_length=1)
    published_at: date | None = None
    capture_method: Literal["authenticated-browser", "public-browser"]


class Decision(Record):
    capture_id: str
    company_id: str
    material: bool
    verification: Literal["unverified", "corroborated", "contradicted", "unresolved", "irrelevant"]
    summary: str = Field(min_length=1)
    thesis_impact: str
    model_impact: str
    follow_up: str
    corroborating_sources: list[str] = Field(default_factory=list)


class Recommendation(Record):
    company_id: str
    action: Literal["buy", "hold", "sell", "insufficient evidence"]
    as_of: date
    horizon: str
    thesis: str
    counterarguments: list[str]
    catalysts: list[str]
    entry_conditions: list[str]
    invalidation_conditions: list[str]
    confidence_rationale: str
    limitations: list[str]
    source_ids: list[str]
    model_path: str | None = None
    price: float | None = Field(default=None, gt=0)
    price_date: date | None = None
