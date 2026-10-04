"""Physical quantity and dated milestone schedule calculations."""

import pandas as pd


def status_snapshot(ledger, week):
    """Select one record per work package at a chosen reporting week."""
    frame = ledger[ledger.week == week].copy()
    if frame.wbs.duplicated().any():
        raise ValueError("Duplicate WBS at status")
    frame["planned_fraction"] = frame.planned_quantity / frame.scope_quantity
    frame["actual_fraction"] = frame.actual_quantity / frame.scope_quantity
    return frame


def earned_schedule_days(frame):
    """Invert each linear baseline; positive means calendar days behind."""
    earned_week = frame.start_week + frame.actual_fraction * (
        frame.finish_week - frame.start_week
    )
    return (frame.week - earned_week).clip(lower=0) * 7


def milestone_status(frame):
    """Return physical completion milestone and lateness at the status date."""
    out = frame[
        ["wbs", "section", "discipline", "baseline_finish", "actual_fraction", "date"]
    ].copy()
    out["complete"] = out.actual_fraction >= 1
    out["overdue_days"] = (
        (pd.to_datetime(out.date) - pd.to_datetime(out.baseline_finish))
        .dt.days.clip(lower=0)
        .where(~out.complete, 0)
    )
    out["status"] = out.apply(
        lambda r: (
            "COMPLETE" if r.complete else ("OVERDUE" if r.overdue_days > 0 else "OPEN")
        ),
        axis=1,
    )
    return out
