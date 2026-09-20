import copy
import json
from datetime import date
from pathlib import Path
from investing_research.portfolio import size_position

ROOT = Path(__file__).resolve().parents[1]
TODAY = date(2026, 9, 20)


def inputs():
    return tuple(
        json.loads((ROOT / "examples" / name).read_text()) for name in ["portfolio.json", "policy.json"]
    )


def test_cash_position_target_increment_separate():
    portfolio, policy = inputs()
    result = size_position(portfolio, policy, "demo-mine", 0.5, TODAY)
    assert result["status"] == "ready"
    assert result["portfolio_value"] == 1200
    assert result["target_shares"] == 150
    assert result["incremental_shares"] == 50
    assert result["post_trade_cash"] == 900
    assert result["constrained_target_weight"] == 0.25


def test_stale_other_holding_blocks_all_shares():
    portfolio, policy = inputs()
    other = copy.deepcopy(portfolio["positions"][0])
    other.update(company_id="demo-other", quote_date="2026-09-17")
    portfolio["positions"].append(other)
    result = size_position(portfolio, policy, "demo-mine", 0.2, TODAY)
    assert result["status"] == "blocked"
    assert "incremental_shares" not in result
    assert any("demo-other" in reason for reason in result["reasons"])


def test_foreign_fx_and_missing_policy():
    portfolio, policy = inputs()
    portfolio["positions"][0].update(
        currency="USD", fx_to_base=1.5, fx_date="2026-09-17", last_completed_fx_session="2026-09-18"
    )
    assert size_position(portfolio, policy, "demo-mine", 0.2, TODAY)["status"] == "blocked"
    assert size_position(portfolio, {}, "demo-mine", 0.2, TODAY)["status"] == "blocked"


def test_snapshot_stale_and_exclusion():
    portfolio, policy = inputs()
    portfolio["as_of"] = "2026-09-01"
    assert size_position(portfolio, policy, "demo-mine", 0.2, TODAY)["status"] == "blocked"
    portfolio["as_of"] = "2026-09-20"
    policy["excluded_instruments"] = ["demo-mine"]
    result = size_position(portfolio, policy, "demo-mine", 0.2, TODAY)
    assert result["target_shares"] == 0
    assert result["incremental_shares"] == -100


def test_sector_and_reserve_constraints():
    portfolio, policy = inputs()
    policy["max_sector_weights"]["mining"] = 0.18
    assert size_position(portfolio, policy, "demo-mine", 0.25, TODAY)["target_shares"] == 108
    policy["max_sector_weights"]["mining"] = 0.4
    policy["minimum_cash_weight"] = 0.9
    result = size_position(portfolio, policy, "demo-mine", 0.25, TODAY)
    assert result["target_shares"] == 60
    assert result["post_trade_cash"] == 1080


def test_malformed_policy_fields_and_non_target_limits_block():
    portfolio, policy = inputs()
    policy["max_commodity_weight"] = 0.05
    assert size_position(portfolio, policy, "demo-mine", 0.2, TODAY)["status"] == "blocked"
    policy.pop("max_commodity_weight")
    policy["max_sector_weights"]["unused"] = float("nan")
    assert size_position(portfolio, policy, "demo-mine", 0.2, TODAY)["status"] == "blocked"
    policy["max_sector_weights"].pop("unused")
    policy["excluded_instruments"] = [42]
    assert size_position(portfolio, policy, "demo-mine", 0.2, TODAY)["status"] == "blocked"


def test_empty_currency_and_malformed_json_objects_block():
    portfolio, policy = inputs()
    portfolio["positions"][0].update(
        currency="", fx_date="2026-09-18", last_completed_fx_session="2026-09-18"
    )
    assert size_position(portfolio, policy, "demo-mine", 0.2, TODAY)["status"] == "blocked"
    assert size_position([], policy, "demo-mine", 0.2, TODAY)["status"] == "blocked"


def test_converted_price_underflow_blocks_quantities():
    portfolio, policy = inputs()
    portfolio["positions"][0].update(
        price=5e-324,
        fx_to_base=5e-324,
        currency="USD",
        fx_date="2026-09-18",
        last_completed_fx_session="2026-09-18",
    )
    result = size_position(portfolio, policy, "demo-mine", 0.2, TODAY)
    assert result["status"] == "blocked"
    assert "target_shares" not in result
