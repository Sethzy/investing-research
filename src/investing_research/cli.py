"""Public CLI for agent-operated research and reproducible local calculations."""

import importlib.metadata
import json
import shutil
from datetime import date
from pathlib import Path
from typing import Annotated

import typer

from .contracts import BrowserCapture, Company, Decision, Fact, Recommendation, Settings
from .workspace import Workspace, read_json, write_json

app = typer.Typer(no_args_is_help=True, pretty_exceptions_show_locals=False)


@app.command()
def coverage_review(ctx: typer.Context, request: Path):
    """Save an immutable, validated category-by-category evidence review."""
    from .coverage import CoverageReview, save
    with ctx.obj.lock():
        result = save(ctx.obj, CoverageReview.model_validate(read_json(request)))
    emit(result)


def emit(value):
    typer.echo(json.dumps(value, indent=2, ensure_ascii=False, default=str, allow_nan=False))


@app.callback()
def main(
    ctx: typer.Context,
    root: Annotated[Path, typer.Option(help="Workspace checkout or data directory")] = Path("."),
):
    """Investing research without data/model API keys. Source text is untrusted evidence."""
    ctx.obj = Workspace(root)


@app.command()
def init(ctx: typer.Context, browser: str = "chrome", profile: str | None = None, timezone: str = "UTC"):
    """Create local settings; does not enable a schedule or copy credentials."""
    ws = ctx.obj
    settings = Settings(browser=browser, profile=profile, timezone=timezone)
    with ws.lock():
        if ws.settings_path.exists():
            raise typer.BadParameter("Already initialized; edit config/local.json to change local settings")
        write_json(ws.settings_path, settings.model_dump(mode="json"))
    emit({"settings": str(ws.settings_path), "status": "initialized"})


@app.command()
def setup(ctx: typer.Context, edit: bool = False, skip_x: bool = False, answers: Path | None = None):
    """Interview for local preferences and X access; rerun to resume, --edit to revise."""
    from .onboarding import setup as setup_workspace

    emit(setup_workspace(ctx.obj, edit=edit, skip_x=skip_x, answers=answers))


@app.command()
def doctor(ctx: typer.Context, live_x: bool = False):
    """Check installed capabilities; optionally run one real read-only X search."""
    settings = ctx.obj.settings() if ctx.obj.settings_path.exists() else None
    packages = {}
    for name in ("investing-research", "financetoolkit", "browser-cookie3", "pypdf", "docling"):
        try:
            packages[name] = importlib.metadata.version(name)
        except importlib.metadata.PackageNotFoundError:
            packages[name] = None
    result = {
        "packages": packages,
        "node": shutil.which("node"),
        "soffice": shutil.which("soffice"),
        "browser": settings.browser if settings else None,
        "profile": settings.profile if settings else None,
        "setup": "configured" if settings else "pending",
        "next": None if settings else "Run uv run invest setup to save your preferences and choose your own X browser profile.",
        "no_api_keys_required": True,
        "x": "not_checked",
        "scheduled_execution": "not_verified",
    }
    if live_x and settings is None:
        result["x"] = {"status": "setup_required", "message": "Run uv run invest setup before checking your X login."}
    elif live_x:
        from .x import search

        response = search('"Metals X"', count=3, browser=settings.browser, profile=settings.profile)
        result["x"] = {k: v for k, v in response.items() if k != "posts"}
    emit(result)
    if not result["node"] or (live_x and result["x"]["status"] != "ok"):
        raise typer.Exit(1)


@app.command()
def watch_add(ctx: typer.Context, config: Path):
    """Add a confirmed company from JSON; use examples/company-mlx.json as a template."""
    ws = ctx.obj
    company = Company.model_validate(read_json(config))
    with ws.lock():
        settings = ws.settings()
        settings.companies = [c for c in settings.companies if c.id != company.id] + [company]
        write_json(ws.settings_path, settings.model_dump(mode="json"))
    emit(company.model_dump(mode="json"))


@app.command()
def discover(url: str, limit: int = 30):
    """Find report links on an official investor page; inspect dates before adding sources."""
    from .sources import discover_links

    emit(discover_links(url, limit=limit))


@app.command()
def fetch(ctx: typer.Context, url: str):
    """Capture a public source immutably and extract page-linked text."""
    from .sources import fetch_source

    ws = ctx.obj
    with ws.lock():
        result, new = ws.record_source(fetch_source(url, ws.root / "data/sources/web"))
    emit({"new": new, **result})


@app.command()
def browser_capture(ctx: typer.Context, path: Path):
    """Import text actually read through the host browser, with explicit completeness/provenance."""
    from .sources import _public_target
    from .workspace import atomic_text, digest, now
    from urllib.parse import urlsplit

    ws = ctx.obj
    captured = BrowserCapture.model_validate(read_json(path)).model_dump(mode="json")
    _public_target(captured["url"])
    host = urlsplit(captured["url"]).hostname
    kind = "x" if host in ("x.com", "www.x.com", "twitter.com", "www.twitter.com") else "browser"
    content_hash = digest(captured)
    with ws.lock():
        output = ws.root / "data/sources/browser" / f"{content_hash}.txt"
        if not output.exists():
            atomic_text(output, captured["text"])
        record, new = ws.capture_record(
            {
                **captured,
                "kind": kind,
                "sha256": content_hash,
                "retrieved_at": now(),
                "files": [ws.relative(output)],
            }
        )
    emit({"new": new, **record})


@app.command()
def extract(ctx: typer.Context, path: Path, engine: str = "pypdf"):
    """Extract a captured PDF; docling uses the optional documents installation extra."""
    from .sources import extract_source

    ws = ctx.obj
    with ws.lock():
        emit(extract_source(path, ws.root / "data/extracted", engine=engine))


@app.command()
def x_search(ctx: typer.Context, query: str, count: int = 50):
    """Run a literal X keyword query and save evidence; requires your browser session."""
    from .x import search

    ws = ctx.obj
    settings = ws.settings()
    with ws.lock():
        result = search(query, count=count, browser=settings.browser, profile=settings.profile)
        result["capture_ids"] = [ws.capture_x(post)[0]["id"] for post in result["posts"]]
    emit(result)
    if result["status"] != "ok":
        raise typer.Exit(1)


@app.command()
def x_capture(ctx: typer.Context, url: str):
    """Capture one exact X URL and the accessible conversation, with completeness labels."""
    from .x import capture

    ws = ctx.obj
    settings = ws.settings()
    with ws.lock():
        result = capture(url, browser=settings.browser, profile=settings.profile)
        result["capture_ids"] = [ws.capture_x(post)[0]["id"] for post in result["posts"]]
        result["conversation_capture_ids"] = [
            ws.capture_x(post)[0]["id"] for post in result.get("conversation", [])
        ]
    emit(result)
    if result["status"] != "ok":
        raise typer.Exit(1)


@app.command()
def collect(
    ctx: typer.Context,
    company: str | None = None,
    since: str | None = None,
    no_x: bool = False,
    no_web: bool = False,
):
    """Collect watchlist evidence and create an agent review packet (no automatic judgement)."""
    from .monitor import collect as collect_run

    ws = ctx.obj
    since_date = date.fromisoformat(since) if since else None
    if since_date and since_date > date.today():
        raise typer.BadParameter("--since cannot be in the future")
    with ws.lock():
        run = collect_run(ws, company, since_date, include_x=not no_x, include_web=not no_web)
    emit(run)
    if run["errors"]:
        raise typer.Exit(2)


@app.command()
def review(ctx: typer.Context, run_id: str, decisions: Path):
    """Finalize a run using explicit agent-authored materiality decisions for all candidates."""
    from .monitor import review as review_run

    ws = ctx.obj
    values = [Decision.model_validate(d) for d in read_json(decisions)]
    with ws.lock():
        emit(review_run(ws, run_id, values))


@app.command()
def import_facts(ctx: typer.Context, path: Path):
    """Import reviewed, source-linked financial facts (JSON array)."""
    from .reports import add_facts

    ws = ctx.obj
    facts = [Fact.model_validate(f) for f in read_json(path)]
    with ws.lock():
        emit({"fact_ids": add_facts(ws, facts)})


@app.command()
def recommend(ctx: typer.Context, path: Path):
    """Store a reasoned agent recommendation; this never places a trade."""
    from .reports import add_recommendation

    ws = ctx.obj
    with ws.lock():
        emit({"recommendation_id": add_recommendation(ws, Recommendation.model_validate(read_json(path)))})


@app.command()
def model(ctx: typer.Context, inputs: Path):
    """Create/synchronize Excel detail and its Markdown analysis; accept JSON or edited XLSX."""
    from .excel import create, synchronize
    from .workspace import digest
    ws = ctx.obj
    source = ws.inside(str(inputs))
    if source.suffix.lower() == ".xlsx":
        with ws.lock():
            emit(synchronize(ws, source))
        return
    data = read_json(source)
    company_id = data.get("company_id", "")
    import re

    if not re.fullmatch(r"[a-z0-9]+-[a-z0-9.-]+", company_id):
        raise typer.BadParameter("Invalid company_id")
    with ws.lock():
        working = ws.root / "companies" / company_id / "working" / f"model-{digest(data)[:16]}.xlsx"
        if not working.exists():
            create(source, working)
        if shutil.which("soffice"):
            result = synchronize(ws, working)
        else:
            result = {"status": "editable_unverified", "workbook": str(working), "next": "Install LibreOffice/soffice and run invest excel-sync to publish a checked Markdown report"}
    emit(result)


@app.command()
def excel_create(ctx: typer.Context, inputs: Path, output: Annotated[Path, typer.Option()],
                 presentation_version: Annotated[int, typer.Option(min=2, max=4)] = 2):
    """Create a professional editable workbook; preserve any existing working model."""
    from .excel import create
    ws = ctx.obj
    with ws.lock():
        try:
            emit(create(ws.inside(str(inputs)), ws.inside(str(output)), presentation_version=presentation_version))
        except ValueError as error:
            raise typer.BadParameter(str(error)) from None


@app.command()
def excel_sync(ctx: typer.Context, workbook: Path):
    """Recalculate Excel and publish a matching Markdown/model snapshot and dossier."""
    from .excel import synchronize
    ws = ctx.obj
    with ws.lock():
        try:
            result = synchronize(ws, ws.inside(str(workbook)))
            emit({key: result[key] for key in ("run_id", "output_dir", "active_case", "workbook_validation")})
        except ValueError as error:
            raise typer.BadParameter(str(error)) from None


@app.command()
def excel_refresh(ctx: typer.Context, workbook: Path, inputs: Path, output: Annotated[Path, typer.Option()]):
    """Refresh source inputs into a new workbook, preserving explicit user overrides."""
    from .excel import refresh
    ws = ctx.obj
    with ws.lock():
        try:
            emit(refresh(ws.inside(str(workbook)), ws.inside(str(inputs)), ws.inside(str(output))))
        except ValueError as error:
            raise typer.BadParameter(str(error)) from None


@app.command()
def validate_workbook(ctx: typer.Context, model_json: Path):
    """Independently recheck an existing workbook; preserve the original model run."""
    from .models import analyse
    from .workbook import verify_workbook
    from .workspace import now

    ws = ctx.obj
    path = ws.inside(str(model_json))
    with ws.lock():
        result = read_json(path)
        inputs = read_json(path.parent / "inputs.json")
        if not result or not inputs:
            raise typer.BadParameter("Expected a model.json with its inputs.json snapshot")
        checked_at = now()
        try:
            if result.get("authority") == "excel":
                from .excel import validate_snapshot_live
                check = validate_snapshot_live(path)
            else:
                expected = analyse(inputs)
                if any(result.get(k) != v for k, v in expected.items()):
                    raise ValueError("Model output differs from its input snapshot")
                check = verify_workbook(path.parent / "model.xlsx", expected)
        except ValueError as error:
            check = {"status": "failed", "reason": str(error)}
        record = {**check, "checked_at": checked_at, "model_file": "model.json"}
        output = path.parent / f"validation-{checked_at.replace(':', '-')}.json"
        write_json(output, record)
    emit({"validation_file": str(output), **record})
    if record["status"] != "passed":
        raise typer.Exit(2)


@app.command()
def scenario(
    inputs: Path,
    output: Annotated[Path, typer.Option()],
    price_multiplier: float = 1.0,
    cost_multiplier: float = 1.0,
):
    """Fork a mine scenario without modifying baseline; multipliers apply to all forecast years."""
    from .models import scenario_from_base

    if output.exists():
        raise typer.BadParameter("Output already exists; choose a new scenario filename")
    write_json(output, scenario_from_base(read_json(inputs), price_multiplier, cost_multiplier))
    emit({"scenario_inputs": str(output)})


@app.command()
def size(
    ctx: typer.Context,
    company: str,
    target_weight: float,
    portfolio: Path = Path("private/portfolio.json"),
    policy: Path = Path("private/policy.json"),
):
    """Calculate constraint-limited target/incremental sizing from dated local inputs."""
    from .portfolio import size_position

    ws = ctx.obj
    portfolio_path = portfolio if portfolio.is_absolute() else ws.root / portfolio
    policy_path = policy if policy.is_absolute() else ws.root / policy
    if not portfolio_path.exists() or not policy_path.exists():
        emit({"status": "blocked", "reasons": ["Supply your portfolio and explicit risk policy first."]})
        raise typer.Exit(2)
    emit(size_position(read_json(portfolio_path), read_json(policy_path), company, target_weight))


@app.command()
def dossier(ctx: typer.Context, company: str):
    """Rebuild the readable company dossier from stored records."""
    from .reports import dossier as build

    ws = ctx.obj
    with ws.lock():
        emit({"path": str(build(ws, company))})


@app.command()
def brief(ctx: typer.Context, company: str, pdf: bool = False):
    """Append new run/artifact revisions to the company brief; optionally export all to PDF."""
    from .journal import update, export_pdf
    ws = ctx.obj
    with ws.lock():
        path = update(ws, company)
        result = {"markdown": str(path)}
        if pdf:
            result["pdf"] = str(export_pdf(path, path.with_suffix(".pdf")))
        emit(result)


@app.command()
def status(ctx: typer.Context):
    """Show pending reviews, interrupted runs, and latest coverage."""
    ws = ctx.obj
    settings = ws.settings()
    from .excel import status as excel_status
    runs = sorted(
        [read_json(p) for p in (ws.root / "state/runs").glob("*.json")], key=lambda r: r["started_at"]
    )
    emit(
        {
            "companies": [c.id for c in settings.companies],
            "excel_models": excel_status(ws),
            "pending": [
                {"id": r["id"], "status": r["status"]}
                for r in runs
                if r["status"] in ("collecting", "pending_review")
            ],
            "latest": (
                {
                    **{
                        key: runs[-1].get(key)
                        for key in ("id", "status", "started_at", "finished_at", "reviewed_at", "errors")
                    },
                    "candidate_count": len(runs[-1]["candidates"]),
                    "receipt": f"state/runs/{runs[-1]['id']}.json",
                }
                if runs
                else None
            ),
        }
    )


@app.command()
def schedule_prompt(ctx: typer.Context):
    """Print the agent-host monitoring instruction; does not install OS cron or a model daemon."""
    ws = ctx.obj
    ws.settings()
    typer.echo(
        f"Open the investing workspace at {ws.root}. Read AGENTS.md and "
        ".agents/skills/investing/SKILL.md. Run its daily workflow using the existing "
        "subscribed agent session: collect all holdings/watchlist sources, resolve any "
        "pending reviews, inspect full evidence, follow relevant primary links, finalize "
        "materiality decisions and update affected dossiers/models. Preserve coverage "
        "failures and unverified claims. Stay quiet on a completed no-change run; notify "
        "only for material developments, execution failures, or required user action. "
        "Do not use API keys, buy services, post on X, or trade."
    )


if __name__ == "__main__":
    app()


@app.command()
def research_append(ctx: typer.Context, path: Path):
    """Append a thesis, catalyst or query-plan revision; never replace earlier records."""
    from .research import append
    from .reports import dossier
    ws = ctx.obj
    with ws.lock():
        result = append(ws, read_json(ws.inside(str(path))))
        dossier(ws, result["data"]["company_id"])
    emit(result)


@app.command()
def research_history(ctx: typer.Context, company: str):
    """Read complete thesis/catalyst/query history and rebuild its current Markdown view."""
    from .research import history, rebuild
    ws = ctx.obj
    with ws.lock():
        emit({"events": history(ws, company), "report": ws.relative(rebuild(ws, company))})


@app.command()
def model_review(ctx: typer.Context, path: Path):
    """Append a sourced actual-versus-estimate and immutable model-change report."""
    from .model_review import review
    from .reports import dossier
    ws = ctx.obj
    with ws.lock():
        result = review(ws, read_json(ws.inside(str(path))))
        dossier(ws, result["company_id"])
    emit(result)


@app.command()
def funding_review(ctx: typer.Context, path: Path):
    """Append independently recalculated financing, funding-gap and dilution scenarios."""
    from .funding import review
    from .reports import dossier
    ws = ctx.obj
    with ws.lock():
        result = review(ws, read_json(ws.inside(str(path))))
        dossier(ws, result["company_id"])
    emit(result)


@app.command()
def research_eval(case: Path, answer: Path):
    """Evaluate a structured research answer against a frozen offline evidence rubric."""
    from .research_eval import evaluate
    result = evaluate(read_json(case), read_json(answer))
    emit(result)
    if result["status"] != "passed":
        raise typer.Exit(1)
