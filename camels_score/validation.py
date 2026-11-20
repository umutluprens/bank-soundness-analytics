"""
Validation against an OUTCOME, not against the model's own labels.

The 2023 final model trained XGBoost to predict "score <= 5", where the score came from
clusters built on the same ratios. A test AUC of 0.997 only showed that XGBoost can redraw
the cluster boundaries. It said nothing about whether low grades precede distress.

Here the target is a future event:
  * preferred: an external event file (ID, YEAR, EVENT) with failures, resolutions, state aid,
    distressed mergers or multi-notch downgrades;
  * fallback: a forward proxy built from next year's data (capital breach, heavy loss,
    NPL spike). The proxy is weaker evidence and is labelled as such in every output.
Grades at year t are always compared with outcomes in t+1..t+h, never the same year.
"""
import numpy as np
import pandas as pd
from sklearn.metrics import roc_auc_score
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import HistGradientBoostingClassifier


def forward_proxy_label(df, horizon=1, tcr_floor=10.5, roaa_floor=-1.0, npl_jump=1.5,
                        npl_level=10.0):
    """
    DISTRESS_FWD = 1 if, within the next `horizon` years, the bank shows any of:
      - total capital ratio below 10.5% (8% Pillar 1 minimum + 2.5% conservation buffer)
      - ROAA below -1%
      - problem loans ratio above 10% AND at least 1.5x its current level
    Bank-years with no future observation get NaN (unknown, excluded from validation).
    Disappearance from the data is NOT treated as failure: it can be a merger or a data gap.
    """
    df = df.sort_values(["ID", "YEAR"]).copy()
    hits = []
    for k in range(1, horizon + 1):
        g = df.groupby("ID")
        nxt_year = g["YEAR"].shift(-k)
        consecutive = nxt_year == df["YEAR"] + k
        conds = []
        if "TOTAL CAPITAL RATIO" in df:
            conds.append(g["TOTAL CAPITAL RATIO"].shift(-k) < tcr_floor)
        if "ROAA" in df:
            conds.append(g["ROAA"].shift(-k) < roaa_floor)
        if "PROBLEM LOANS RATIO" in df:
            fut = g["PROBLEM LOANS RATIO"].shift(-k)
            conds.append((fut > npl_level) & (fut >= npl_jump * df["PROBLEM LOANS RATIO"]))
        hit = np.logical_or.reduce(conds) if conds else pd.Series(False, index=df.index)
        hits.append(pd.Series(np.where(consecutive, hit.astype(float), np.nan), index=df.index))
    lab = pd.concat(hits, axis=1).max(axis=1, skipna=True)
    df["DISTRESS_FWD"] = lab
    df["LABEL_SOURCE"] = "forward proxy (weak evidence)"
    return df


def event_label(df, events: pd.DataFrame, horizon=2):
    """events: columns ID, YEAR (year of the event). Label = event within (t, t+horizon]."""
    df = df.copy()
    ev = events[["ID", "YEAR"]].rename(columns={"YEAR": "EV_YEAR"})
    m = df[["ID", "YEAR"]].reset_index().merge(ev, on="ID", how="left")
    m["hit"] = (m["EV_YEAR"] > m["YEAR"]) & (m["EV_YEAR"] <= m["YEAR"] + horizon)
    df["DISTRESS_FWD"] = m.groupby("index")["hit"].max().reindex(df.index).astype(float)
    df["LABEL_SOURCE"] = "external events"
    return df


def discrimination(scored, grade_col="FINAL_GRADE", target="DISTRESS_FWD"):
    d = scored.dropna(subset=[target])
    y = d[target].astype(int)
    if y.nunique() < 2:
        return {"n": len(d), "events": int(y.sum()), "auc": np.nan, "gini": np.nan}
    auc = roc_auc_score(y, d[grade_col])          # higher grade = weaker = more distress
    return {"n": len(d), "events": int(y.sum()), "auc": round(auc, 3),
            "gini": round(2 * auc - 1, 3)}


def grade_table(scored, grade_col="FINAL_GRADE", target="DISTRESS_FWD"):
    """Observed distress rate by grade. A sound scale shows rates rising with the grade."""
    d = scored.dropna(subset=[target])
    t = d.groupby(grade_col)[target].agg(bank_years="size", events="sum", rate="mean")
    t["rate"] = (t["rate"] * 100).round(2)
    t["events"] = t["events"].astype(int)
    rho = pd.Series(t.index).corr(t["rate"].reset_index(drop=True), method="spearman")
    t.attrs["spearman_grade_vs_rate"] = round(float(rho), 3) if pd.notna(rho) else np.nan
    return t


def migration_matrix(scored, grade_col="FINAL_GRADE"):
    """Share of banks moving from grade at t to grade at t+1 (rows sum to 100)."""
    d = scored.sort_values(["ID", "YEAR"])[["ID", "YEAR", grade_col]].copy()
    d["NEXT"] = d.groupby("ID")[grade_col].shift(-1)
    d["NEXT_YEAR"] = d.groupby("ID")["YEAR"].shift(-1)
    d = d[d["NEXT_YEAR"] == d["YEAR"] + 1]
    m = pd.crosstab(d[grade_col], d["NEXT"].astype(int), normalize="index") * 100
    return m.round(1)


def psi(expected, actual, bins=10):
    """Population stability index of a score between two samples."""
    cuts = np.unique(np.quantile(expected, np.linspace(0, 1, bins + 1)))
    e = np.histogram(expected, cuts)[0] / len(expected)
    a = np.histogram(np.clip(actual, cuts[0], cuts[-1]), cuts)[0] / len(actual)
    e, a = np.clip(e, 1e-6, None), np.clip(a, 1e-6, None)
    return float(np.sum((a - e) * np.log(a / e)))


def out_of_time_challengers(scored, ratios, split_year, target="DISTRESS_FWD"):
    """
    Train on years <= split_year, test on later years. Compares:
      scorecard  : FINAL_GRADE, no training on the target at all
      logit      : logistic regression on the six pillar z-scores
      gbm        : gradient boosting on raw ratios (XGBoost if installed, else sklearn HGB)
    If the challengers beat the scorecard by a wide margin, revisit weights or ratios.
    """
    d = scored.dropna(subset=[target])
    tr, te = d[d["YEAR"] <= split_year], d[d["YEAR"] > split_year]
    res = {"train_years": f"<= {split_year}", "test_years": f"> {split_year}",
           "test_n": len(te), "test_events": int(te[target].sum())}
    if tr[target].nunique() < 2 or te[target].nunique() < 2:
        res["note"] = "not enough events on one side of the split"
        return res
    res["scorecard_auc"] = round(roc_auc_score(te[target], te["FINAL_GRADE"]), 3)

    pz = [c for c in d.columns if c.startswith("PILLAR_") and c.endswith("_Z")]
    lr = LogisticRegression(max_iter=1000).fit(tr[pz], tr[target])
    res["logit_pillars_auc"] = round(roc_auc_score(te[target], lr.predict_proba(te[pz])[:, 1]), 3)
    res["logit_coefficients"] = dict(zip(pz, np.round(lr.coef_[0], 3)))

    try:
        from xgboost import XGBClassifier
        gbm, name = XGBClassifier(n_estimators=200, max_depth=3, learning_rate=0.05,
                                  subsample=0.8, eval_metric="auc"), "xgboost"
    except ImportError:
        gbm, name = HistGradientBoostingClassifier(max_depth=3, learning_rate=0.05,
                                                   max_iter=200), "sklearn_hgb"
    gbm.fit(tr[ratios], tr[target])
    res[f"gbm_{name}_train_auc"] = round(roc_auc_score(tr[target], gbm.predict_proba(tr[ratios])[:, 1]), 3)
    res[f"gbm_{name}_test_auc"] = round(roc_auc_score(te[target], gbm.predict_proba(te[ratios])[:, 1]), 3)
    return res
