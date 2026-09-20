from typer.testing import CliRunner

from investing_research.cli import app
from investing_research.contracts import Company, Settings
from investing_research.workspace import Workspace, read_json, write_json


def answers():
    return (
        "\n".join(
            [
                "codex",
                "AUD",
                "3–5 years",
                "fundamental mining",
                "ASX:MLX",
                "Asia/Singapore",
                "08:00",
                "10",
                "15",
                "chrome",
                "Profile 3",
            ]
        )
        + "\n"
    )


def test_interview_saves_preferences_without_inventing_watchlist(tmp_path):
    result = CliRunner().invoke(app, ["--root", str(tmp_path), "setup", "--skip-x"], input=answers())
    assert result.exit_code == 0, result.output
    preferences = read_json(tmp_path / "private/preferences.json")
    assert preferences["watchlist_requests"] == ["ASX:MLX"]
    assert preferences["max_position_weight"] == 0.1
    assert preferences["minimum_cash_weight"] == 0.15
    assert preferences["setup_status"] == "x_setup_pending"
    assert Workspace(tmp_path).settings().companies == []
    assert not (tmp_path / "private/portfolio.json").exists()


def test_interrupt_resume_preserves_existing_companies(tmp_path):
    ws = Workspace(tmp_path)
    company = Company(
        id="asx-mlx",
        name="Metals X",
        exchange="ASX",
        ticker="MLX",
        currency="AUD",
        reporting_currency="AUD",
        sector="tin",
        website="https://example.com",
    )
    write_json(ws.settings_path, Settings(companies=[company], budget_minutes=42).model_dump(mode="json"))
    runner = CliRunner()
    interrupted = runner.invoke(app, ["--root", str(tmp_path), "setup"], input="claude\nSGD\n")
    assert interrupted.exit_code != 0
    assert read_json(tmp_path / "private/preferences.json")["base_currency"] == "SGD"
    remaining = "\n".join(answers().splitlines()[2:]) + "\n"
    resumed = runner.invoke(app, ["--root", str(tmp_path), "setup", "--skip-x"], input=remaining)
    assert resumed.exit_code == 0, resumed.output
    assert "Portfolio base currency" not in resumed.output
    assert ws.settings().companies == [company]
    assert ws.settings().budget_minutes == 42
    assert read_json(tmp_path / "private/preferences.json")["host"] == "claude"


def test_x_retry_and_no_secret_output(tmp_path, monkeypatch):
    calls = []

    def search(*args, **kwargs):
        calls.append(kwargs)
        if len(calls) == 1:
            raise RuntimeError("auth_token=VERY_SECRET")
        return {"status": "ok", "posts": [{"text": "PRIVATE_POST"}]}

    monkeypatch.setattr("investing_research.x.search", search)
    result = CliRunner().invoke(app, ["--root", str(tmp_path), "setup"], input=answers() + "y\ny\n")
    assert result.exit_code == 0, result.output
    assert len(calls) == 2 and calls[0]["profile"] == "Profile 3"
    contents = (tmp_path / "private/preferences.json").read_text() + result.output
    assert "VERY_SECRET" not in contents and "PRIVATE_POST" not in contents
    assert read_json(tmp_path / "private/preferences.json")["setup_status"] == "ready_for_research"


def test_invalid_values_reprompt_and_optional_limits_unset(tmp_path):
    input_text = "codex\nAUD\nlong\nvalue\n\nBad/Zone\nUTC\n29:00\n\nnan\n\n\nchrome\n\n"
    result = CliRunner().invoke(app, ["--root", str(tmp_path), "setup", "--skip-x"], input=input_text)
    assert result.exit_code == 0, result.output
    prefs = read_json(tmp_path / "private/preferences.json")
    assert prefs["daily_time"] is None
    assert prefs["max_position_weight"] is None
    assert prefs["minimum_cash_weight"] is None
    assert prefs["watchlist_requests"] == []


def test_x_failure_deferred_is_not_success(tmp_path, monkeypatch):
    monkeypatch.setattr(
        "investing_research.x.search",
        lambda *a, **kw: {
            "status": "error",
            "error": {"code": "credentials_unavailable", "message": "secret"},
        },
    )
    result = CliRunner().invoke(app, ["--root", str(tmp_path), "setup"], input=answers() + "y\nn\n")
    assert result.exit_code == 0, result.output
    prefs = read_json(tmp_path / "private/preferences.json")
    assert prefs["setup_status"] == "x_setup_pending"
    assert prefs["x_check"]["error_code"] == "credentials_unavailable"
    assert "secret" not in result.output


def answer_json(tmp_path, **updates):
    payload = dict(
        host="codex",
        base_currency="AUD",
        horizon="long",
        research_style="value",
        watchlist_requests=[],
        timezone="UTC",
        daily_time=None,
        max_position_weight=None,
        minimum_cash_weight=None,
        browser="chrome",
        profile=None,
    )
    payload.update(updates)
    path = tmp_path / "answers.json"
    write_json(path, payload)
    return path


def test_answers_runs_live_without_prompts_and_preserves_companies(tmp_path, monkeypatch):
    ws = Workspace(tmp_path)
    company = Company(
        id="asx-mlx",
        name="Metals X",
        exchange="ASX",
        ticker="MLX",
        currency="AUD",
        reporting_currency="AUD",
        sector="tin",
        website="https://example.com",
    )
    write_json(ws.settings_path, Settings(companies=[company], budget_minutes=42).model_dump(mode="json"))
    calls = []

    def search(*a, **kw):
        calls.append(kw)
        return {"status": "ok"}

    monkeypatch.setattr("investing_research.x.search", search)
    path = answer_json(tmp_path)
    result = CliRunner().invoke(app, ["--root", str(tmp_path), "setup", "--answers", str(path)])
    assert result.exit_code == 0, result.output
    assert len(calls) == 1
    assert ws.settings().companies == [company]
    assert ws.settings().budget_minutes == 42
    prefs = read_json(tmp_path / "private/preferences.json")
    assert prefs["daily_time"] is None and prefs["max_position_weight"] is None
    assert prefs["x_check"]["status"] == "ok"


def test_answers_failure_does_not_loop_or_leak(tmp_path, monkeypatch):
    monkeypatch.setattr(
        "investing_research.x.search",
        lambda *a, **kw: {"status": "error", "error": {"code": "credentials_unavailable"}},
    )
    path = answer_json(tmp_path, profile="", daily_time="")
    result = CliRunner().invoke(app, ["--root", str(tmp_path), "setup", "--answers", str(path)])
    assert result.exit_code == 0, result.output
    assert read_json(tmp_path / "private/preferences.json")["setup_status"] == "x_setup_pending"


def test_invalid_answers_no_writes(tmp_path):
    path = answer_json(tmp_path, password="SECRET")
    result = CliRunner().invoke(app, ["--root", str(tmp_path), "setup", "--answers", str(path)])
    assert result.exit_code != 0
    assert "SECRET" not in result.output
    assert not (tmp_path / "config/local.json").exists()
    payload = read_json(path)
    del payload["password"]
    del payload["host"]
    write_json(path, payload)
    result = CliRunner().invoke(app, ["--root", str(tmp_path), "setup", "--answers", str(path)])
    assert result.exit_code != 0
    assert not (tmp_path / "private/preferences.json").exists()


def test_rerun_rechecks_expired_session_and_external_profile_change(tmp_path, monkeypatch):
    runner = CliRunner()
    monkeypatch.setattr("investing_research.x.search", lambda *a, **kw: {"status": "ok"})
    assert runner.invoke(app, ["--root", str(tmp_path), "setup"], input=answers() + "y\n").exit_code == 0
    ws = Workspace(tmp_path)
    settings = ws.settings()
    settings.profile = "Profile 5"
    write_json(ws.settings_path, settings.model_dump(mode="json"))
    calls = []

    def expired(*a, **kw):
        calls.append(kw)
        return {"status": "error", "error": {"code": "authentication_failed"}}

    monkeypatch.setattr("investing_research.x.search", expired)
    result = runner.invoke(app, ["--root", str(tmp_path), "setup"], input="y\nn\n")
    assert result.exit_code == 0, result.output
    assert len(calls) == 1 and calls[0]["profile"] == "Profile 5"
    prefs = read_json(tmp_path / "private/preferences.json")
    assert prefs["setup_status"] == "x_setup_pending"
    assert prefs["x_check"]["error_code"] == "authentication_failed"
    assert prefs["x_check"]["profile"] == "Profile 5"


def test_declining_recheck_does_not_reuse_previous_success(tmp_path, monkeypatch):
    runner = CliRunner()
    monkeypatch.setattr("investing_research.x.search", lambda *a, **kw: {"status": "ok"})
    assert runner.invoke(app, ["--root", str(tmp_path), "setup"], input=answers() + "y\n").exit_code == 0
    result = runner.invoke(app, ["--root", str(tmp_path), "setup"], input="n\n")
    assert result.exit_code == 0, result.output
    prefs = read_json(tmp_path / "private/preferences.json")
    assert prefs["setup_status"] == "x_setup_pending"
    assert prefs["x_check"]["status"] == "deferred"
