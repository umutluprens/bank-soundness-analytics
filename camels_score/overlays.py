"""
Bounded qualitative overlay (v0.6).

The agencies all score factors that balance-sheet ratios miss: business model and franchise,
concentration, governance and transparency, growth and risk appetite (S&P business position and
risk position, Fitch business profile and risk profile, Moody's qualitative adjustments). This
module lets an analyst record such judgements in data/overlays.csv. They are applied after group
support, in notches on the continuous score (positive = weaker), and the total per bank-year is
capped at +/- 2 notches.

data/overlays.csv columns:
  ID, FROM_YEAR, TO_YEAR, FACTOR, NOTCHES, REASON, ANALYST, DATE

FACTOR must be one of FACTORS. NOTCHES must be between -2 and +2. Every row needs a REASON and
an ANALYST. Overlays are recorded with the date they were decided, so a back-test can exclude any
overlay decided after the year it is applied to (no hindsight).
"""
import numpy as np
import pandas as pd

FACTORS = {
    "business_model": "Franchise, diversification, dependence on one product, client or market",
    "concentration": "Single-name, sector or related-party concentration in assets or funding",
    "governance": "Ownership, transparency, audit, regulatory findings, accounting quality",
    "growth": "Loan or balance-sheet growth well above peers, new risky business lines",
    "other": "Any other documented factor (requires second reviewer)",
}
MAX_TOTAL = 2.0


def load_overlays(path):
    o = pd.read_csv(path)
    if o.empty:
        return o
    bad = ~o["FACTOR"].isin(FACTORS)
    if bad.any():
        raise ValueError(f"unknown FACTOR values: {sorted(o.loc[bad, 'FACTOR'].unique())}")
    if (o["NOTCHES"].abs() > MAX_TOTAL).any():
        raise ValueError("NOTCHES must be between -2 and +2")
    if o[["REASON", "ANALYST"]].isna().any().any():
        raise ValueError("every overlay needs a REASON and an ANALYST")
    return o


def apply_overlays(scored, overlays, point_in_time=True):
    """Add OVERLAY_NOTCHES to FINAL_SCORE. With point_in_time, an overlay counts for a year only
    if its DATE is not later than the end of the following year (when that year's accounts
    would have been reviewed)."""
    from .scoring import grade_label
    out = scored.copy()
    out["OVERLAY_NOTCHES"] = 0.0
    if overlays is None or overlays.empty:
        return out
    for _, r in overlays.iterrows():
        m = (out["ID"] == r["ID"]) & out["YEAR"].between(r["FROM_YEAR"], r["TO_YEAR"])
        if point_in_time and pd.notna(r.get("DATE")):
            decided = pd.to_datetime(r["DATE"]).year
            m &= out["YEAR"] + 1 >= decided
        out.loc[m, "OVERLAY_NOTCHES"] += float(r["NOTCHES"])
    out["OVERLAY_NOTCHES"] = out["OVERLAY_NOTCHES"].clip(-MAX_TOTAL, MAX_TOTAL)
    score = (out["FINAL_SCORE"].astype(float) + out["OVERLAY_NOTCHES"]).clip(1, 10)
    out["FINAL_SCORE"] = score.round(2)
    out["FINAL_GRADE"] = score.round().clip(1, 10).astype(int)
    out["GRADE_LABEL"] = grade_label(score)
    return out
