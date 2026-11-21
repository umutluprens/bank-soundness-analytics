"""
Phase 2: next-year forecast of the soundness score (first version).

Question: given everything known about a bank at the end of year t, what will its score be at
t+1, and how likely is a downgrade?

Three routes are compared, all walk-forward by year (train on pairs whose target year is at most
T, forecast T+1 from T, then move one year on), so no forecast uses information from its own
target year:

  persistence  score(t+1) = score(t). The baseline every model must beat.
  direct       gradient boosting predicts the change in score from t to t+1 from features at t
               (median, with 10% and 90% quantiles for a range)
  ratios       gradient boosting predicts the change in each scored ratio; the forecast ratios are then
               graded with the frozen scorecard. Slower, but a forecast downgrade can be traced
               to the ratios expected to weaken (the route proposed in ROADMAP.md).

A downgrade classifier (score(t+1) at least one notch weaker) is fitted alongside.

Macro expectations: pass `macro`, a table with COUNTRY, YEAR and forecast columns, where YEAR is
the year the forecast was published (for example the IMF WEO October vintage of year t for
year t+1). It is joined on the bank's country and year t, so only forecasts available at t are
used. Without it the models use bank and country-score information only.
"""
import numpy as np
import pandas as pd
from sklearn.ensemble import HistGradientBoostingRegressor, HistGradientBoostingClassifier
from sklearn.metrics import roc_auc_score

SCORE = "OWN_SCORE"           # score after the country anchor and loss notch, before group support


def _grade(s):
    return np.clip(np.round(np.asarray(s, dtype=float)), 1, 10)


def build_pairs(scored, ratios, macro=None):
    """One row per bank and year t with features at t and outcomes at t+1."""
    d = scored.sort_values(["ID", "YEAR"]).copy()
    pz = [c for c in d.columns if c.startswith("PILLAR_") and c.endswith("_Z")]
    base = ratios + pz + ["COMPOSITE_Z", SCORE, "OE_SCORE_USED", "MISSING_COUNT"]
    base = [c for c in dict.fromkeys(base) if c in d.columns]
    g = d.groupby("ID")
    feat = d[["ID", "YEAR", "COUNTRY"] + base].copy()
    for c in [SCORE, "COMPOSITE_Z"] + [r for r in ratios if r in d.columns]:
        feat[f"D1_{c}"] = d[c] - g[c].shift(1)          # change on the previous year
    if "LOG TOTAL ASSETS" in d.columns:
        feat["LOG TOTAL ASSETS"] = d["LOG TOTAL ASSETS"]
    nxt = d[["ID", "YEAR", SCORE] + [r for r in ratios if r in d.columns]].copy()
    nxt["YEAR"] = nxt["YEAR"] - 1
    nxt = nxt.rename(columns={c: f"NEXT_{c}" for c in nxt.columns if c not in ("ID", "YEAR")})
    pairs = feat.merge(nxt, on=["ID", "YEAR"], how="inner")
    if macro is not None:
        pairs = pairs.merge(macro, on=["COUNTRY", "YEAR"], how="left")
    pairs["DOWNGRADE"] = (_grade(pairs[f"NEXT_{SCORE}"]) - _grade(pairs[SCORE]) >= 1).astype(int)
    return pairs


def _features(pairs):
    skip = {"ID", "YEAR", "COUNTRY", "DOWNGRADE"}
    return [c for c in pairs.columns if c not in skip and not c.startswith("NEXT_")]


def _hgb(loss="absolute_error", q=None):
    # Median (absolute-error) loss on the CHANGE from year t: the score is persistent and its
    # yearly changes are fat-tailed, so a mean-loss model on the level did worse than persistence.
    kw = dict(max_iter=200, learning_rate=0.05, max_depth=3, min_samples_leaf=80, random_state=0)
    if q is not None:
        return HistGradientBoostingRegressor(loss="quantile", quantile=q, **kw)
    return HistGradientBoostingRegressor(loss=loss, **kw)


def walk_forward(scored, ratios, scorer, first_target=2014, last_target=None, macro=None,
                 ratio_route=True):
    """Forecast each target year from the year before, training only on earlier pairs."""
    pairs = build_pairs(scored, ratios, macro)
    X = _features(pairs)
    last_target = last_target or int(pairs["YEAR"].max()) + 1
    out = []
    for target in range(first_target, last_target + 1):
        tr = pairs[pairs["YEAR"] + 1 < target]
        te = pairs[pairs["YEAR"] + 1 == target].copy()
        if len(tr) < 200 or te.empty:
            continue
        y = tr[f"NEXT_{SCORE}"] - tr[SCORE]               # forecast the change, add it back
        now = te[SCORE].to_numpy()
        te["F_PERSIST"] = now
        te["F_DIRECT"] = np.clip(now + _hgb().fit(tr[X], y).predict(te[X]), 1, 10)
        widen = _conformal_margin(tr, X, target)
        te["RANGE_MARGIN"] = widen
        te["F_DIRECT_P10"] = np.clip(now + _hgb(q=0.1).fit(tr[X], y).predict(te[X]) - widen, 1, 10)
        te["F_DIRECT_P90"] = np.clip(now + _hgb(q=0.9).fit(tr[X], y).predict(te[X]) + widen, 1, 10)
        clf = HistGradientBoostingClassifier(max_iter=200, learning_rate=0.05, max_depth=3,
                                             min_samples_leaf=40, random_state=0)
        te["P_DOWNGRADE"] = clf.fit(tr[X], tr["DOWNGRADE"]).predict_proba(te[X])[:, 1] \
            if tr["DOWNGRADE"].nunique() > 1 else np.nan
        if ratio_route:
            te["F_RATIOS"] = _ratio_route(tr, te, X, ratios, scored, scorer)
        out.append(te)
    return pd.concat(out, ignore_index=True)


def _conformal_margin(tr, X, target, coverage=0.8):
    """Conformalised quantile regression: fit the 10% and 90% models without the latest training
    year, measure on that year how far outcomes fall outside the range, and widen (or narrow) the
    range by the margin that would have given the stated coverage there."""
    cal = tr[tr["YEAR"] + 1 == target - 1]
    fit = tr[tr["YEAR"] + 1 < target - 1]
    if len(fit) < 200 or len(cal) < 50:
        return 0.0
    y = fit[f"NEXT_{SCORE}"] - fit[SCORE]
    lo = cal[SCORE] + _hgb(q=0.1).fit(fit[X], y).predict(cal[X])
    hi = cal[SCORE] + _hgb(q=0.9).fit(fit[X], y).predict(cal[X])
    act = cal[f"NEXT_{SCORE}"]
    miss = np.maximum(lo - act, act - hi)
    return float(np.quantile(miss, min(1.0, coverage * (1 + 1 / len(cal)))))


def _ratio_route(tr, te, X, ratios, scored, scorer):
    """Forecast every ratio, then grade the forecast ratios with the frozen scorecard."""
    rows = scored.set_index(["ID", "YEAR"]).loc[list(zip(te["ID"], te["YEAR"]))].reset_index()
    for r in [r for r in ratios if f"NEXT_{r}" in te.columns]:
        m = tr[f"NEXT_{r}"].notna() & tr[r].notna()
        chg = _hgb().fit(tr.loc[m, X], tr.loc[m, f"NEXT_{r}"] - tr.loc[m, r]).predict(te[X])
        rows[r] = rows[r].to_numpy() + chg
    rows["YEAR"] = rows["YEAR"] + 1                 # country score stays at its year-t value
    keep = [c for c in rows.columns if not c.startswith(("PILLAR_", "OWN_", "FINAL_", "STANDALONE"))]
    return scorer.transform(rows[keep])[SCORE].to_numpy()


def evaluate(fc, events=None, horizon=2):
    """Accuracy against the realised score, downgrade ranking, and event ranking."""
    act = fc[f"NEXT_{SCORE}"].to_numpy()
    res = {"bank_years": int(len(fc)), "target_years": sorted(int(y) + 1 for y in fc["YEAR"].unique())}
    routes = [c for c in ("F_PERSIST", "F_DIRECT", "F_RATIOS") if c in fc]
    for c in routes:
        f = fc[c].to_numpy()
        res[c] = {"mae_score": round(float(np.mean(np.abs(f - act))), 3),
                  "exact_grade": round(float(np.mean(_grade(f) == _grade(act))), 3),
                  "within_one_notch": round(float(np.mean(np.abs(_grade(f) - _grade(act)) <= 1)), 3)}
        if c != "F_PERSIST" and fc["DOWNGRADE"].nunique() > 1:
            res[c]["downgrade_auc"] = round(float(roc_auc_score(fc["DOWNGRADE"], f - fc[SCORE])), 3)
    if "P_DOWNGRADE" in fc and fc["DOWNGRADE"].nunique() > 1:
        res["downgrade_classifier_auc"] = round(float(roc_auc_score(fc["DOWNGRADE"], fc["P_DOWNGRADE"])), 3)
    if "F_DIRECT_P10" in fc:
        inside = (act >= fc["F_DIRECT_P10"]) & (act <= fc["F_DIRECT_P90"])
        res["direct_80pct_interval_coverage"] = round(float(inside.mean()), 3)
    res["downgrade_rate"] = round(float(fc["DOWNGRADE"].mean()), 3)
    if events is not None:
        ev = events[["ID", "YEAR"]].drop_duplicates()
        hit = []
        for _, r in fc[["ID", "YEAR"]].iterrows():
            yrs = ev.loc[ev["ID"] == r["ID"], "YEAR"]
            hit.append(int(((yrs > r["YEAR"]) & (yrs <= r["YEAR"] + horizon)).any()))
        fc = fc.assign(EVENT_NEXT=hit)
        if fc["EVENT_NEXT"].nunique() > 1:
            res["event_auc"] = {c: round(float(roc_auc_score(fc["EVENT_NEXT"], fc[c])), 3) for c in routes}
            res["event_bank_years"] = int(fc["EVENT_NEXT"].sum())
    return res, fc


def load_macro(path):
    """Tidy WEO vintage file (tools/fetch_open_data.py) -> one row per COUNTRY and YEAR = vintage
    year, with the forecast for the current and the next year as known in October of that year."""
    w = pd.read_csv(path)
    w["H"] = np.where(w["TARGET_YEAR"] == w["VINTAGE_YEAR"], "NOW", "NEXT")
    t = w.pivot_table(index=["COUNTRY", "VINTAGE_YEAR"], columns=["NAME", "H"], values="VALUE")
    t.columns = [f"{n.replace('_FORECAST', '')}_{h}" for n, h in t.columns]
    for n in ("GDP_GROWTH", "INFLATION", "UNEMPLOYMENT"):
        if f"{n}_NEXT" in t and f"{n}_NOW" in t:
            t[f"{n}_CHANGE"] = t[f"{n}_NEXT"] - t[f"{n}_NOW"]
    return t.reset_index().rename(columns={"VINTAGE_YEAR": "YEAR"})
