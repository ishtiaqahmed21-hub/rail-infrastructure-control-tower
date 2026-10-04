"""Distinct financial exposure and ordinal heatmap scores."""

import numpy as np


def assess_risks(frame):
    """Compute expected monetary exposure; scores are not currency."""
    out = frame.copy()
    if not out.probability.between(0, 1).all():
        raise ValueError("Probability outside [0,1]")
    if (out.impact_gbp < 0).any():
        raise ValueError("Negative monetary impact")
    out["exposure_gbp"] = out.probability * out.impact_gbp
    out["probability_band"] = np.ceil(out.probability * 5).clip(1, 5).astype(int)
    out["score"] = out.probability_band * out.impact_band
    out["RAG"] = out.score.map(
        lambda s: "RED" if s >= 15 else ("AMBER" if s >= 8 else "GREEN")
    )
    return out
