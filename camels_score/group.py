"""
Group support: uplift for a subsidiary of a stronger parent bank. Support only, no contagion.

A subsidiary of a stronger foreign group can expect support in stress. The support is treated
as a probability, at most 0.5, applied to the gap between the subsidiary's own score and its
parent's score. The country score stays a hard ceiling: support can never lift a bank above
the country cap that applies to every bank in that country. A subsidiary in a weak country
therefore never reaches its parent's grade, however strong the parent.

Inputs, one row per subsidiary (data/parents.csv):
  ID, PARENT_ID (bank ID in the panel) or PARENT_GRADE (external 1-10 equivalent),
  SUPPORT_LEVEL, FROM_YEAR, TO_YEAR

Rule, with own = the subsidiary's score after country anchor and loss notch, parent = the
parent's own score in the same year (lower is stronger) and cap = country score - 2:

  supported = own - p x (own - parent)        only when parent < own
  final     = max(supported, cap)             support cannot breach the country cap

  p (support probability) = 0.50 core, 0.35 strategic, 0.15 moderate, 0 none

Further limits (v0.6):
  ability    p is cut to 75% when the subsidiary's total assets are 10-20% of the parent's,
             and to 50% above 20% (a large subsidiary strains the parent's capacity; Fitch)
  sovereign  support cannot lift a bank above its sovereign rating equivalent (SOVEREIGN_GRADE),
             where one is entered (Moody's and Fitch sovereign / country-ceiling constraints)
  stress     in years an analyst marks the parent as stressed (sanctions, rescue, failure:
             STRESS_FROM in parents.csv) support is withdrawn; the subsidiary keeps its own score
             (support-only rule: a weak parent never pulls the subsidiary down)
  flag       WEAK_PARENT marks subsidiaries whose parent scores at least one notch weaker

The rule works on the continuous score, so support of less than one notch still shows in
FINAL_SCORE and in the + / - modifier of GRADE_LABEL.
"""
import numpy as np
import pandas as pd

SUPPORT_PROB = {"core": 0.50, "strategic": 0.35, "moderate": 0.15, "none": 0.0}
MAX_SUPPORT_PROB = 0.50
COUNTRY_GAP = 2            # no bank may sit more than this many notches above its country score
ABILITY_STEPS = [(0.20, 0.50), (0.10, 0.75)]   # (assets share above which, probability factor)


# Indicative mapping from a long-term issuer rating (S&P / Fitch scale) to the 1-10 grade.
# Not a calibrated equivalence: use it to enter PARENT_GRADE for parents outside the panel.
RATING_TO_GRADE = {
    "AAA": 1, "AA+": 1, "AA": 1, "AA-": 1, "A+": 2, "A": 2, "A-": 3,
    "BBB+": 4, "BBB": 4, "BBB-": 5, "BB+": 6, "BB": 6, "BB-": 7,
    "B+": 8, "B": 8, "B-": 9, "CCC+": 10, "CCC": 10, "CCC-": 10, "CC": 10, "C": 10, "D": 10,
}


def rating_to_grade(rating: str):
    return RATING_TO_GRADE.get(str(rating).strip().upper())


def load_parents(path):
    p = pd.read_csv(path)
    p["SUPPORT_LEVEL"] = p["SUPPORT_LEVEL"].str.lower().fillna("none")
    return p


def attach_support_level(df, parents):
    """Add SUPPORT_LEVEL, PARENT_ID, PARENT_GRADE to bank-years covered by parents.csv."""
    for c in ("STRESS_FROM", "STRESS_REASON"):
        if c not in parents.columns:
            parents = parents.assign(**{c: np.nan})
    cols = ["ID", "PARENT_ID", "PARENT_NAME", "PARENT_GRADE", "SUPPORT_LEVEL", "FROM_YEAR", "TO_YEAR",
            "STRESS_FROM", "STRESS_REASON"]
    m = df.drop(columns=[c for c in cols[1:] if c in df.columns]).merge(
        parents[cols], on="ID", how="left")
    inside = (m["YEAR"] >= m["FROM_YEAR"].fillna(0)) & (m["YEAR"] <= m["TO_YEAR"].fillna(9999))
    for c in ("PARENT_ID", "PARENT_NAME", "PARENT_GRADE", "STRESS_FROM", "STRESS_REASON"):
        m[c] = m[c].where(inside)
    m["SUPPORT_LEVEL"] = m["SUPPORT_LEVEL"].where(inside, "none").fillna("none")
    m.index = df.index
    return m.drop(columns=["FROM_YEAR", "TO_YEAR"])


def apply_group_support(scored):
    """Adjust FINAL_SCORE / FINAL_GRADE / GRADE_LABEL of subsidiaries. Needs OWN_SCORE,
    SUPPORT_LEVEL and PARENT_ID or PARENT_GRADE columns."""
    from .scoring import grade_label
    out = scored.copy()
    own_by = out.set_index(["ID", "YEAR"])["OWN_SCORE"]
    key = list(zip(out["PARENT_ID"].fillna(-1).astype(int), out["YEAR"]))
    parent_in_panel = pd.Series([own_by.get(k, np.nan) for k in key], index=out.index)
    # An analyst-entered PARENT_GRADE (e.g. from rating_to_grade) takes precedence over the
    # panel score: for global groups the consolidated CAMELS score can differ from the view
    # of the group's own supervisors and rating agencies.
    parent = out["PARENT_GRADE"].astype(float).fillna(parent_in_panel)
    out["PARENT_SCORE"] = parent.round(2)

    own = out["OWN_SCORE"].astype(float)
    lvl = out["SUPPORT_LEVEL"].fillna("none")
    p = lvl.map(SUPPORT_PROB).fillna(0.0).clip(upper=MAX_SUPPORT_PROB)

    # Ability: relative size of the subsidiary against the parent (same year)
    ability = pd.Series(1.0, index=out.index)
    if "TOTAL ASSETS" in out.columns:
        ta_by = out.set_index(["ID", "YEAR"])["TOTAL ASSETS"]
        parent_ta = pd.Series([ta_by.get(kk, np.nan) for kk in key], index=out.index)
        share = out["TOTAL ASSETS"].astype(float) / parent_ta
        for limit, factor in ABILITY_STEPS:
            ability = ability.where(~((share > limit) & (ability == 1.0)), factor)
        out["ASSETS_SHARE_OF_PARENT"] = share.round(3)
    p = p * ability

    # Parent stress (analyst-entered): no support in those years
    stress = out["YEAR"] >= out["STRESS_FROM"].fillna(9999) if "STRESS_FROM" in out else \
        pd.Series(False, index=out.index)
    p = p.where(~stress, 0.0)

    gap = (own - parent).clip(lower=0).fillna(0.0)       # only a stronger parent helps
    supported = own - p * gap
    if "OE_SCORE_USED" in out.columns:
        cap = (out["OE_SCORE_USED"].astype(float) - COUNTRY_GAP).clip(lower=1)
        supported = np.maximum(supported, cap.fillna(1))
    if "SOVEREIGN_GRADE" in out.columns:
        sov = out["SOVEREIGN_GRADE"].astype(float)
        supported = np.where(sov.notna(), np.maximum(supported, sov), supported)
    score = pd.Series(np.minimum(supported, own), index=out.index)   # support never worsens

    score = score.clip(1, 10)

    out["SUPPORT_ABILITY"] = ability
    out["SUPPORT_PROB"] = p.where(gap > 0, 0.0).round(3)
    out["PARENT_STRESS"] = stress
    out["WEAK_PARENT"] = (parent - own) >= 1

    out["GROUP_ADJ"] = (score - own).round(2)          # negative = support, 0 = no effect
    out["FINAL_SCORE"] = score.round(2)
    out["FINAL_GRADE"] = score.round().clip(1, 10).astype(int)
    out["GRADE_LABEL"] = grade_label(score)
    return out


def load_sovereign(path):
    """COUNTRY, YEAR, RATING (long-term foreign-currency, year-end) -> SOVEREIGN_GRADE."""
    s = pd.read_csv(path)
    s = s.dropna(subset=["RATING"])
    s["SOVEREIGN_GRADE"] = s["RATING"].map(rating_to_grade)
    return s[["COUNTRY", "YEAR", "SOVEREIGN_GRADE"]]
