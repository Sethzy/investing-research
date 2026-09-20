"""Resumable local onboarding. Preferences are not a portfolio or an enabled schedule."""

from __future__ import annotations

import re
from pathlib import Path
from typing import Literal
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

import typer
from pydantic import BaseModel, ConfigDict, Field, ValidationError, field_validator, model_validator

from .contracts import Settings
from .workspace import Workspace, now, read_json, write_json


def _answer(label, default, validate):
    while True:
        value = typer.prompt(label, default=default or "", show_default=bool(default)).strip()
        if value == "-":
            value = ""
        try:
            return validate(value)
        except (ValueError, ZoneInfoNotFoundError):
            typer.echo("Please enter a valid value for this question.")


def _choice(options):
    def check(value):
        if value.lower() not in options:
            raise ValueError("choice")
        return value.lower()

    return check


def _nonempty(value):
    if not value:
        raise ValueError("required")
    return value


def _currency(value):
    if not re.fullmatch(r"[A-Za-z]{3}", value):
        raise ValueError("currency")
    return value.upper()


def _time(value):
    if value and not re.fullmatch(r"(?:[01][0-9]|2[0-3]):[0-5][0-9]", value):
        raise ValueError("time")
    return value or None


def _percentage(value):
    if not value:
        return None
    number = float(value)
    if not 0 <= number <= 100:
        raise ValueError("percentage")
    return number / 100


def _timezone(value):
    ZoneInfo(value)
    return value


class SetupAnswers(BaseModel):
    """Agent-authored interview answers. All keys explicit, optional answers nullable."""

    model_config = ConfigDict(extra="forbid", allow_inf_nan=False, strict=True)
    host: Literal["codex", "claude"]
    base_currency: str = Field(pattern=r"^[A-Z]{3}$")
    horizon: str = Field(min_length=1)
    research_style: str = Field(min_length=1)
    watchlist_requests: list[str]
    timezone: str
    daily_time: str | None
    max_position_weight: float | None = Field(ge=0, le=1)
    minimum_cash_weight: float | None = Field(ge=0, le=1)
    browser: Literal["chrome", "firefox", "brave", "edge"]
    profile: str | None

    @field_validator("timezone")
    @classmethod
    def zone(cls, value):
        try:
            return _timezone(value)
        except (ValueError, ZoneInfoNotFoundError) as exc:
            raise ValueError("Invalid IANA timezone") from exc

    @field_validator("horizon", "research_style")
    @classmethod
    def text(cls, value):
        return _nonempty(value.strip())

    @field_validator("daily_time")
    @classmethod
    def time(cls, value):
        return _time(value) if value is not None else None

    @field_validator("profile")
    @classmethod
    def profile_text(cls, value):
        return value.strip() or None if value is not None else None

    @field_validator("watchlist_requests")
    @classmethod
    def watchlist(cls, value):
        return [_nonempty(item.strip()) for item in value]

    @model_validator(mode="after")
    def browser_profile(self):
        if self.browser == "firefox" and self.profile and not Path(self.profile).expanduser().is_absolute():
            raise ValueError("Firefox profile requires an absolute path")
        return self


def setup(ws: Workspace, *, edit: bool = False, skip_x: bool = False, answers: Path | None = None):
    """Interview without collecting secrets; save each answer so interruption is resumable."""
    supplied = None
    if answers is not None:
        try:
            supplied = SetupAnswers.model_validate(read_json(answers)).model_dump()
        except (OSError, ValueError, ValidationError):
            raise typer.BadParameter(
                "Invalid setup answers. Supply every documented field with the correct type; unknown fields are rejected. See docs/setup.md."
            ) from None
    path = ws.root / "private/preferences.json"
    # Hold the workspace lock throughout the interview so another setup cannot lose answers.
    with ws.lock():
        preferences = read_json(path, {})
        if not isinstance(preferences, dict):
            raise typer.BadParameter("private/preferences.json must be a JSON object")
        settings = ws.settings() if ws.settings_path.exists() else Settings()
        completed = set(preferences.get("completed_questions", []))
        if not ws.settings_path.exists():
            completed.difference_update({"browser", "profile", "timezone"})
        # An old successful probe is not evidence that this session still works.
        # Read current Settings above, including any external profile edits.
        preferences["x_check"] = {"status": "not_checked"}

        def save():
            preferences["schema_version"] = 1
            preferences["completed_questions"] = sorted(completed)
            preferences["updated_at"] = now()
            write_json(path, preferences)

        def ask(key, label, default, validate, *, setting=False):
            if supplied is None and key in completed and not edit:
                return getattr(settings, key) if setting else preferences.get(key)
            value = supplied[key] if supplied is not None else _answer(label, default, validate)
            if setting:
                if key in ("browser", "profile") and getattr(settings, key) != value:
                    preferences["x_check"] = {"status": "not_checked"}
                setattr(settings, key, value)
                # Round-trip all settings; preserve companies and monitoring budgets.
                checked = Settings.model_validate(settings.model_dump())
                write_json(ws.settings_path, checked.model_dump(mode="json"))
            else:
                preferences[key] = value
            completed.add(key)
            save()
            return value

        typer.echo("Investing Research setup — answers stay in this local workspace.")
        typer.echo("Press Ctrl-C to pause; run invest setup again to resume. Use --edit to revise answers.")
        typer.echo("Never paste X cookies, passwords or tokens into this interview or agent chat.")
        typer.echo("Enter keeps a displayed default; type - to clear an optional answer.")
        preferences["setup_status"] = "interview_in_progress"
        save()
        ask(
            "host",
            "Subscribed agent host (codex/claude)",
            preferences.get("host"),
            _choice(("codex", "claude")),
        )
        ask(
            "base_currency",
            "Portfolio base currency, three letters (for example AUD)",
            preferences.get("base_currency"),
            _currency,
        )
        ask("horizon", "Investment horizon (for example 3–5 years)", preferences.get("horizon"), _nonempty)
        ask(
            "research_style",
            "Research style and priorities (for example fundamental value, mining)",
            preferences.get("research_style"),
            _nonempty,
        )
        ask(
            "watchlist_requests",
            "Companies to research, with exchange if known (comma separated; blank to defer)",
            ", ".join(preferences.get("watchlist_requests", [])),
            lambda value: [item.strip() for item in value.split(",") if item.strip()],
        )
        typer.echo(
            "Company requests require identity confirmation by your agent before watch-add. Existing confirmed companies are retained."
        )
        ask(
            "timezone",
            "IANA timezone (for example Asia/Singapore)",
            settings.timezone,
            _timezone,
            setting=True,
        )
        ask(
            "daily_time",
            "Preferred daily research time, HH:MM (blank for on-demand only)",
            preferences.get("daily_time"),
            _time,
        )
        typer.echo("This records a preference; your agent must separately configure and verify scheduling.")
        typer.echo("Optional risk preferences: blank leaves a limit unspecified. These do not enable sizing.")
        for key, label in (
            ("max_position_weight", "Maximum position weight, percent"),
            ("minimum_cash_weight", "Minimum cash reserve, percent"),
        ):
            existing = preferences.get(key)
            ask(key, label, str(existing * 100) if existing is not None else "", _percentage)
        typer.echo(
            "Sizing still requires actual holdings, current quotes/FX, and a complete explicit sector/exclusion policy."
        )
        ask(
            "browser",
            "Browser signed in to X (chrome/firefox/brave/edge)",
            settings.browser,
            _choice(("chrome", "firefox", "brave", "edge")),
            setting=True,
        )
        typer.echo(
            "Use your own browser profile. Chrome/Brave/Edge: Default or Profile N; Firefox: absolute profile directory."
        )

        def profile(value):
            if settings.browser == "firefox" and value and not Path(value).expanduser().is_absolute():
                raise ValueError("Firefox profile requires an absolute path")
            return value or None

        ask(
            "profile",
            "X browser profile (blank for browser default)",
            settings.profile,
            profile,
            setting=True,
        )
        preferences["setup_status"] = "preferences_saved"
        save()
        if skip_x:
            preferences["x_check"] = {"status": "deferred", "checked_at": now()}
        else:
            typer.echo(
                "Sign into https://x.com in that browser first. OS cookie-access prompts may require your approval."
            )
            while supplied is not None or typer.confirm(
                "Run a read-only X connection test now?", default=True
            ):
                from .x import search

                try:
                    response = search(
                        '"Metals X"', count=1, browser=settings.browser, profile=settings.profile
                    )
                except Exception:
                    # Third-party exceptions can include cookies: never display or persist them.
                    response = {"status": "error", "error": {"code": "upstream_failed"}}
                code = response.get("error", {}).get("code", "upstream_failed")
                allowed = {
                    "authentication_failed",
                    "credentials_unavailable",
                    "dependency_missing",
                    "rate_limited",
                    "upstream_failed",
                    "invalid_request",
                }
                code = code if code in allowed else "upstream_failed"
                ok = response.get("status") == "ok"
                preferences["x_check"] = {
                    "status": "ok" if ok else "error",
                    "checked_at": now(),
                    "browser": settings.browser,
                    "profile": settings.profile,
                    **({} if ok else {"error_code": code}),
                }
                save()
                if ok:
                    typer.echo(
                        "X connection works. Results remain bounded; this is not proof of complete monitoring coverage."
                    )
                    break
                typer.echo(
                    f"X connection unavailable ({code}). Check your login, profile and OS cookie access. See docs/setup.md."
                )
                typer.echo(
                    "You can retry after fixing login access, or defer and rerun invest setup --edit to change the profile."
                )
                if supplied is not None:
                    break
            else:
                if preferences.get("x_check", {}).get("status") != "error":
                    preferences["x_check"] = {"status": "deferred", "checked_at": now()}
        preferences["setup_status"] = (
            "ready_for_research"
            if preferences.get("x_check", {}).get("status") == "ok"
            else "x_setup_pending"
        )
        save()
        typer.echo(f"Saved {path}. No schedule or trades have been enabled.")
        typer.echo(
            "Next: ask your agent to confirm company identities, add the watchlist, and run your first research review."
        )
        return {
            "status": preferences["setup_status"],
            "preferences": str(path),
            "settings": str(ws.settings_path),
        }
