"""Cost reporting avoids double-counting outstanding commitments."""

from .kpi_engine import earned_value


def cost_summary(frame):
    """EAC is cost-efficiency estimate; floor covers legally committed unpaid work."""
    out = earned_value(frame)
    out["outstanding_commitments"] = float(frame.outstanding_commitments.sum())
    out["committed_floor"] = out["AC"] + out["outstanding_commitments"]
    out["management_EAC"] = max(out["EAC"], out["committed_floor"])
    out["VAC"] = out["BAC"] - out["management_EAC"]
    out["EAC_remaining_at_budget"] = out["AC"] + out["BAC"] - out["EV"]
    return out
