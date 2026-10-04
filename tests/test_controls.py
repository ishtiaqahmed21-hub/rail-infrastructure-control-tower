import math
import pandas as pd
import pytest
from src.kpi_engine import earned_value, ratio, rag
from src.cost import cost_summary
from src.risk import assess_risks
from src.forecast import forecast_packages


def fixture_frame():
    return pd.DataFrame(
        {
            "budget": [100.0, 200.0],
            "planned_fraction": [0.5, 0.5],
            "actual_fraction": [0.4, 0.6],
            "actual_cost": [50.0, 150.0],
            "outstanding_commitments": [20.0, 30.0],
        }
    )


def test_weighted_evm_and_no_double_count():
    m = cost_summary(fixture_frame())
    assert m["PV"] == 150 and m["EV"] == 160 and m["AC"] == 200
    assert m["CPI"] == 0.8 and m["EAC"] == 375
    assert m["committed_floor"] == 250 and m["management_EAC"] == 375


def test_zero_and_threshold_boundaries():
    assert math.isnan(ratio(1, 0))
    assert rag(float("nan")) == "UNKNOWN"
    assert rag(0.95) == "GREEN" and rag(0.85) == "AMBER" and rag(0.849) == "RED"


def test_risk_invalid_and_expected_value():
    r = pd.DataFrame({"probability": [0.4], "impact_gbp": [1000.0], "impact_band": [3]})
    assert assess_risks(r).exposure_gbp.iloc[0] == 400
    r["probability"] = 1.1
    with pytest.raises(ValueError):
        assess_risks(r)


def test_zero_productivity_no_finite_finish():
    d = pd.DataFrame(
        {
            "wbs": ["A", "A"],
            "week": [0, 4],
            "date": ["2026-01-01", "2026-01-29"],
            "section": ["S", "S"],
            "discipline": ["Track", "Track"],
            "baseline_finish": ["2026-12-31"] * 2,
            "scope_quantity": [100, 100],
            "actual_quantity": [0, 0],
        }
    )
    assert pd.isna(forecast_packages(d, 4).current_finish.iloc[0])


def test_saved_ledger_reconciles():
    from pathlib import Path

    p = Path(__file__).resolve().parents[1] / "data/processed/ledger.csv"
    d = pd.read_csv(p)
    assert not d.duplicated(["wbs", "week"]).any()
    assert (d.actual_quantity <= d.scope_quantity + 1e-8).all()
    assert (d.groupby("wbs").actual_quantity.diff().dropna() >= 0).all()
    assert (d.outstanding_commitments >= 0).all()
    latest = d[d.week == d.week.max()]
    assert latest[latest.discipline == "Track"].scope_quantity.sum() == 68


def test_forecast_invalid_period_and_multiplier():
    d = pd.DataFrame({"week": [0, 4]})
    with pytest.raises(ValueError):
        forecast_packages(d, 0)
    with pytest.raises(ValueError):
        forecast_packages(d, 4, 0)
    with pytest.raises(ValueError):
        forecast_packages(d, 5)


def test_completed_package_preserves_actual_finish():
    d = pd.DataFrame(
        {
            "wbs": ["A"] * 3,
            "week": [0, 2, 4],
            "date": ["2026-01-01", "2026-01-15", "2026-01-29"],
            "section": ["S"] * 3,
            "discipline": ["Track"] * 3,
            "baseline_finish": ["2026-12-31"] * 3,
            "scope_quantity": [100] * 3,
            "actual_quantity": [0, 100, 100],
        }
    )
    f = forecast_packages(d, 4)
    assert f.current_finish.iloc[0] == pd.Timestamp("2026-01-15")
    assert f.recovery_finish.iloc[0] == pd.Timestamp("2026-01-15")


def test_progress_scenarios_bounded_and_monotonic():
    from pathlib import Path
    from src.forecast import progress_scenarios

    d = pd.read_csv(Path(__file__).resolve().parents[1] / "data/processed/ledger.csv")
    f = progress_scenarios(d, 30, horizon=8)
    assert f.quantity.between(0, f.scope_quantity).all()
    assert (f.groupby(["wbs", "scenario"]).quantity.diff().dropna() >= 0).all()
    assert set(f.scenario) == {"BASELINE", "CURRENT", "RECOVERY"}
