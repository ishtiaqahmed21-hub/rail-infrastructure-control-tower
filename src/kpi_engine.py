"""Earned value arithmetic with explicit undefined denominators."""

import numpy as np


def ratio(numerator: float, denominator: float) -> float:
    """Return undefined for a nonpositive denominator."""
    return float(numerator / denominator) if denominator > 0 else float("nan")


def earned_value(frame):
    """Aggregate WBS budgets and earned physical fractions at one status date."""
    bac = frame.budget.sum()
    pv = (frame.budget * frame.planned_fraction).sum()
    ev = (frame.budget * frame.actual_fraction).sum()
    ac = frame.actual_cost.sum()
    cpi, spi = ratio(ev, ac), ratio(ev, pv)
    return {
        "BAC": float(bac),
        "PV": float(pv),
        "EV": float(ev),
        "AC": float(ac),
        "CPI": cpi,
        "SPI": spi,
        "CV": float(ev - ac),
        "SV": float(ev - pv),
        "EAC": float(ac + (bac - ev) / cpi) if cpi > 0 else float("nan"),
    }


def rag(value: float, green=0.95, amber=0.85) -> str:
    """Example management thresholds are assumptions, not industry standards."""
    if not np.isfinite(value):
        return "UNKNOWN"
    return "GREEN" if value >= green else "AMBER" if value >= amber else "RED"
