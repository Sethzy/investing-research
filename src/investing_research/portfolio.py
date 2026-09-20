"""Constraint-first whole-portfolio sizing. No execution or implicit risk profile."""

from __future__ import annotations
from datetime import date
import math
import re
from .models import number


def size_position(
    portfolio: dict, policy: dict, company_id: str, target_weight: float, as_of: date | None = None
) -> dict:
    today = as_of or date.today()
    reasons = []
    result = {"status": "blocked", "company_id": company_id, "reasons": reasons, "as_of": today.isoformat()}
    try:
        if not isinstance(portfolio, dict) or not isinstance(policy, dict):
            raise ValueError("Portfolio and policy must be JSON objects")
        allowed_policy = {
            "max_position_weight",
            "minimum_cash_weight",
            "max_sector_weights",
            "excluded_instruments",
            "notes",
            "synthetic",
        }
        if set(policy) - allowed_policy:
            raise ValueError(f"Unsupported policy fields: {sorted(set(policy) - allowed_policy)}")
        if not isinstance(portfolio.get("base_currency"), str) or not re.fullmatch(
            r"[A-Z]{3}", portfolio["base_currency"]
        ):
            raise ValueError("Supply a three-letter uppercase portfolio base_currency")
        snapshot = date.fromisoformat(portfolio["as_of"])
        if snapshot > today or (today - snapshot).days > 7:
            reasons.append("Portfolio snapshot is future dated or older than seven days; reconfirm holdings")
        cash = number(portfolio["cash"], "cash", 0)
        target = number(target_weight, "target_weight", 0, 1)
        maximum = number(policy["max_position_weight"], "max_position_weight", 0, 1)
        reserve = number(policy["minimum_cash_weight"], "minimum_cash_weight", 0, 1)
        sector_limits = policy["max_sector_weights"]
        if not isinstance(sector_limits, dict):
            raise ValueError("Supply explicit max_sector_weights")
        excluded = policy["excluded_instruments"]
        if not isinstance(excluded, list) or not all(isinstance(item, str) and item for item in excluded):
            raise ValueError("excluded_instruments must be a list of company IDs")
        for sector_name, limit in sector_limits.items():
            if not isinstance(sector_name, str) or not sector_name:
                raise ValueError("Sector limit names must be nonempty strings")
            number(limit, f"{sector_name} limit", 0, 1)
        positions = portfolio["positions"]
        if not isinstance(positions, list) or not positions:
            raise ValueError("Supply positions (include a zero-share target with its quote)")
        seen = set()
        values = {}
        sectors = {}
        instruments = {}
        for holding in positions:
            if not isinstance(holding, dict):
                raise ValueError("Each position must be an object")
            ident = holding["company_id"]
            if not isinstance(ident, str) or not ident:
                raise ValueError("Each position needs a company ID")
            if ident in seen:
                raise ValueError(f"Duplicate holding {ident}")
            seen.add(ident)
            instruments[ident] = holding
            shares = number(holding["shares"], f"{ident} shares", 0)
            price = number(holding["price"], f"{ident} price", 0)
            fx = number(holding["fx_to_base"], f"{ident} FX", 0)
            if price <= 0 or fx <= 0:
                raise ValueError(f"{ident} price and FX must be positive")
            currency = holding["currency"]
            if not isinstance(currency, str) or not re.fullmatch(r"[A-Z]{3}", currency):
                raise ValueError(f"{ident} requires a three-letter uppercase currency")
            if currency == portfolio["base_currency"] and fx != 1:
                raise ValueError(f"{ident} same-currency FX must equal 1")
            session = date.fromisoformat(holding["last_completed_session"])
            quote = date.fromisoformat(holding["quote_date"])
            if session > today or quote > today or quote < session:
                reasons.append(f"{ident}: stale/future quote or trading-session date")
            if currency != portfolio["base_currency"]:
                fx_session = date.fromisoformat(holding["last_completed_fx_session"])
                fx_date = date.fromisoformat(holding["fx_date"])
                if fx_session > today or fx_date > today or fx_date < fx_session:
                    reasons.append(f"{ident}: stale/future FX observation")
            sector = holding["sector"]
            if not isinstance(sector, str) or not sector:
                raise ValueError(f"{ident} missing sector")
            if sector not in sector_limits:
                reasons.append(f"No explicit sector limit for {sector}")
            values[ident] = number(shares * price * fx, f"{ident} market value", 0)
            sectors[sector] = sectors.get(sector, 0) + values[ident]
        if company_id not in instruments:
            raise ValueError(
                "Add target as a zero-share position with current quote, FX, sector and session dates"
            )
        total = number(cash + math.fsum(values.values()), "portfolio value", 0)
        if total <= 0:
            raise ValueError("Portfolio total must be positive")
        if reasons:
            return result
        holding = instruments[company_id]
        current = values[company_id]
        desired = target * total
        sector = holding["sector"]
        sector_other = sectors[sector] - current
        max_value = min(
            maximum * total, sector_limits[sector] * total - sector_other, current + cash - reserve * total
        )
        if company_id in excluded:
            max_value = 0
        constrained = max(0, min(desired, max_value))
        share_value = number(holding["price"] * holding["fx_to_base"], "base-currency price", 0)
        if share_value == 0:
            raise ValueError("Converted share price underflows to zero")
        # Whole-share target floors, ensuring buying never exceeds any cap.
        proposed_shares = math.floor(constrained / share_value)
        delta_shares = proposed_shares - holding["shares"]
        actual_value = proposed_shares * share_value
        post_cash = cash - (actual_value - current)
        post_values = dict(values, **{company_id: actual_value})
        post_sectors = dict(sectors)
        post_sectors[sector] += actual_value - current
        # A target trade cannot silently approve pre-existing violations elsewhere.
        for ident, value in post_values.items():
            if value > maximum * total + 1e-8:
                reasons.append(f"Post-trade {ident} exceeds maximum position weight")
            if ident in excluded and value > 0:
                reasons.append(f"Post-trade portfolio still holds excluded instrument {ident}")
        for name, value in post_sectors.items():
            if value > sector_limits[name] * total + 1e-8:
                reasons.append(f"Post-trade {name} exceeds sector limit")
        if post_cash < reserve * total - 1e-8:
            reasons.append("Trade cannot restore required cash reserve")
        if reasons:
            return result
        result.update(
            status="ready",
            portfolio_value=total,
            base_currency=portfolio["base_currency"],
            requested_target_weight=target,
            constrained_target_weight=actual_value / total,
            current_weight=current / total,
            target_shares=proposed_shares,
            incremental_shares=delta_shares,
            incremental_value=actual_value - current,
            post_trade_cash=post_cash,
            constraints_applied=target > actual_value / total + 1e-12,
            limitations=[
                "Whole shares, no fees/taxes/slippage; reconfirm costs before acting.",
                "Trading-calendar dates supplied explicitly; accuracy depends on the supplied last completed sessions.",
            ],
        )
    except (KeyError, TypeError, ValueError, OverflowError) as error:
        reasons.append(f"Invalid or missing input: {error}")
    return result
