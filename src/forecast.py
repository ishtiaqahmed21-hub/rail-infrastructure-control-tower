"""Transparent rate-extrapolation scenarios; no causal recovery claims."""

import numpy as np
import pandas as pd


def forecast_packages(ledger, week, multiplier=1.25):
    """Use last four intervals of progress, cap quantities, refuse zero-rate finish."""
    if week <= 0 or multiplier <= 0:
        raise ValueError("Week and recovery multiplier must be positive")
    if week not in ledger.week.values or max(0, week - 4) not in ledger.week.values:
        raise ValueError("Required reporting snapshot missing")
    current = ledger[ledger.week == week].set_index("wbs")
    previous = ledger[ledger.week == max(0, week - 4)].set_index("wbs")
    out = current[
        [
            "section",
            "discipline",
            "baseline_finish",
            "scope_quantity",
            "actual_quantity",
        ]
    ].copy()
    out["weekly_rate"] = (current.actual_quantity - previous.actual_quantity) / (
        week - max(0, week - 4)
    )
    remaining = (out.scope_quantity - out.actual_quantity).clip(lower=0)
    duration = np.where(
        remaining <= 0,
        0,
        np.where(out.weekly_rate > 0, remaining / out.weekly_rate, np.nan),
    )
    status = pd.to_datetime(current.date)
    out["current_finish"] = status + pd.to_timedelta(duration * 7, unit="D")
    out["recovery_finish"] = status + pd.to_timedelta(
        duration * 7 / multiplier, unit="D"
    )
    for wbs in out.index[remaining <= 0]:
        completed = ledger[
            (ledger.wbs == wbs) & (ledger.actual_quantity >= ledger.scope_quantity)
        ]
        actual_finish = pd.to_datetime(completed.date).min()
        out.loc[wbs, "current_finish"] = actual_finish
        out.loc[wbs, "recovery_finish"] = actual_finish
    out["current_delay_days"] = (
        out.current_finish - pd.to_datetime(out.baseline_finish)
    ).dt.total_seconds() / 86400
    return out.reset_index()


def progress_scenarios(ledger, week, multiplier=1.25, horizon=52):
    """Project future physical quantities under baseline/current/recovery assumptions.

    Zero recent rate is a flat scenario, not evidence of eventual completion.
    Budget-weighted projections retain native units at WBS grain.
    """
    forecasts = forecast_packages(ledger, week, multiplier).set_index("wbs")
    current = ledger[ledger.week == week].set_index("wbs")
    rows = []
    for wbs, row in current.iterrows():
        rate = forecasts.loc[wbs, "weekly_rate"]
        for offset in range(horizon + 1):
            future_week = week + offset
            planned = row.scope_quantity * np.clip(
                (future_week - row.start_week) / (row.finish_week - row.start_week),
                0,
                1,
            )
            for scenario, quantity in [
                ("BASELINE", planned),
                (
                    "CURRENT",
                    min(row.scope_quantity, row.actual_quantity + rate * offset),
                ),
                (
                    "RECOVERY",
                    min(
                        row.scope_quantity,
                        row.actual_quantity + rate * offset * multiplier,
                    ),
                ),
            ]:
                if (
                    row.discipline in ("Stations", "Signaling")
                    and scenario != "BASELINE"
                ):
                    quantity = np.floor(quantity)
                rows.append(
                    {
                        "wbs": wbs,
                        "section": row.section,
                        "discipline": row.discipline,
                        "week": future_week,
                        "date": (pd.Timestamp(row.date) + pd.Timedelta(weeks=offset))
                        .date()
                        .isoformat(),
                        "scenario": scenario,
                        "quantity": quantity,
                        "scope_quantity": row.scope_quantity,
                        "budget": row.budget,
                        "projected_ev": row.budget * quantity / row.scope_quantity,
                        "evidence_type": "DERIVED",
                        "origin": "SIMULATED",
                    }
                )
    return pd.DataFrame(rows)
