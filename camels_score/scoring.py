"""
Direction-aware CAMELS scorecard with frozen calibration.

Grade scale: 1 = soundest, 10 = weakest (same orientation as BICRA).

How a grade is built
  1. Each ratio -> oriented robust z-score against a FROZEN calibration sample:
         z = direction * (x - median) / (1.4826 * MAD), clipped to [-3, 3]
     so a positive z always means "sounder than the typical bank", whatever the ratio.
  2. Pillar score = average z of the ratios in that pillar. Correlated ratios (Tier 1 and
     total capital, ROAA and ROAE) share one pillar weight, so they are not double counted.
     This replaces the PCA step that was used in 2023 to handle multicollinearity.
  3. Composite = weighted average of pillar scores (weights in ratios.PILLAR_WEIGHTS,
     renormalised if a pillar has no data).
  4. Standalone grade 1-10 from fixed composite cut-offs set on the calibration sample.
  5. Operating environment anchor: final grade blends the standalone grade with the country
     score and cannot be more than `max_uplift` notches better than the country score
     (more uplift allowed when PARENT_SUPPORT = 1).

Because the medians, MADs and cut-offs are frozen at fit time, a bank scored on 2024 data is
measured against the same yardstick as 2010-2021. In 2023 the K-Means clusters were refitted
on the pooled data, so grades had no fixed meaning outside that run.
"""
import json
import numpy as np
import pandas as pd

from .ratios import REGISTRY, PILLARS, PILLAR_WEIGHTS, PARENT_SUPPORT_COL
from .data import oe_column

ONE_SIDED_RISK = {"LOAN GROWTH"}   # only above-median values are penalised

# How many notches above its country score a bank may sit. The country score is a ceiling for
# every bank, supported or not: group support (group.py) cannot breach it.
COUNTRY_UPLIFT = {"core": 2, "strategic": 2, "moderate": 2, "none": 2}


def support_level(df):
    """SUPPORT_LEVEL column (core / strategic / moderate / none). The older PARENT_SUPPORT = 1
    flag is read as 'strategic'."""
    if "SUPPORT_LEVEL" in df.columns:
        return df["SUPPORT_LEVEL"].fillna("none").str.lower()
    if PARENT_SUPPORT_COL in df.columns:
        return pd.Series(np.where(df[PARENT_SUPPORT_COL].fillna(0).astype(int) == 1,
                                  "strategic", "none"), index=df.index)
    return pd.Series("none", index=df.index)


def grade_label(score):
    """Grade with a modifier for the position inside the notch: '6+' is the better third of
    grade 6, '6-' the weaker third."""
    g = score.round().clip(1, 10).astype(int)
    frac = score - g
    mod = np.where(frac <= -1 / 6, "+", np.where(frac >= 1 / 6, "-", ""))
    return g.astype(str) + mod
Z_CLIP = 3.0


class CamelsScorer:
    def __init__(self, weights=None, oe_weight=0.15, max_uplift=2, max_uplift_supported=4,
                 n_grades=10, capital_z_cap=1.0, loss_notch=True):
        """
        capital_z_cap : ceiling on the positive z of each capital ratio (e.g. 1.0). Capital far
                        above the norm stops adding credit, so it cannot hide losses.
        loss_notch    : worsen the final grade by 1 notch if ROAA < 0 and by 2 if ROAA < -1%.
        """
        self.capital_z_cap = capital_z_cap
        self.loss_notch = loss_notch
        self.weights = dict(weights or PILLAR_WEIGHTS)
        self.oe_weight = oe_weight
        self.max_uplift = max_uplift
        self.max_uplift_supported = max_uplift_supported
        self.n_grades = n_grades
        self.params_ = None

    # ------------------------------------------------------------------ fit
    def fit(self, df: pd.DataFrame, ratios: list, reference: pd.DataFrame = None):
        """
        df        : imputed calibration sample (used for the grade cut-offs)
        reference : same sample BEFORE imputation (used for medians and scales). Penalty
                    imputation fills gaps with weak values on purpose; letting those fills set
                    the yardstick would shift every median toward the weak side.
        """
        ref = df if reference is None else reference
        centre, scale = {}, {}
        for r in ratios:
            x = ref[r].astype(float).dropna()
            med = float(x.median())
            mad = float((x - med).abs().median()) * 1.4826
            if not np.isfinite(mad) or mad == 0:
                mad = float(x.std()) or 1.0
            centre[r], scale[r] = med, mad
        self.params_ = {"ratios": list(ratios), "centre": centre, "scale": scale,
                        "weights": self.weights, "capital_z_cap": self.capital_z_cap,
                        "loss_notch": self.loss_notch}
        z = self._oriented_z(df)
        pillars = self._pillars(z)
        comp = self._composite(pillars)
        qs = np.linspace(0, 1, self.n_grades + 1)[1:-1]
        self.params_["composite_cuts"] = [float(v) for v in comp.quantile(qs)]
        self.params_["pillar_cuts"] = {p: [float(v) for v in pillars[p].quantile(qs)]
                                       for p in pillars.columns}
        return self

    # ------------------------------------------------------------ transform
    def transform(self, df: pd.DataFrame) -> pd.DataFrame:
        if self.params_ is None:
            raise RuntimeError("Call fit() first or load() saved parameters.")
        out = df.copy()
        z = self._oriented_z(df)
        pillars = self._pillars(z)
        comp = self._composite(pillars)

        for p in pillars.columns:
            out[f"PILLAR_{p}_Z"] = pillars[p].round(3)
            out[f"PILLAR_{p}_GRADE"] = self._to_grade(pillars[p], self.params_["pillar_cuts"][p])
        out["COMPOSITE_Z"] = comp.round(3)
        # Continuous grade score (1.0 soundest ... 10.0 weakest). Integer grades are its rounding,
        # so a difference of less than one notch stays visible.
        own = self._to_score(comp)
        out["STANDALONE_SCORE"] = own.round(2)
        out["STANDALONE_GRADE"] = own.round().clip(1, self.n_grades).astype(int)

        level = support_level(df)
        oe = oe_column(df)
        score = own.copy()
        if oe is not None and df[oe].notna().any():
            oe_score = df[oe].astype(float).clip(1, 10)
            blended = self.oe_weight * oe_score + (1 - self.oe_weight) * own
            uplift = level.map(COUNTRY_UPLIFT).fillna(self.max_uplift)
            uplift = np.maximum(uplift, self.max_uplift)
            floor = (oe_score - uplift).clip(lower=1)
            score = pd.Series(np.where(oe_score.isna(), own, np.maximum(blended, floor)), index=df.index)
            out["OE_SCORE_USED"] = oe_score

        if self.params_.get("loss_notch") and "ROAA" in df.columns:
            roaa = df["ROAA"].astype(float)
            notch = np.where(roaa < -1, 2, np.where(roaa < 0, 1, 0))
            out["LOSS_NOTCH"] = notch
            score = score + notch

        score = score.clip(1, self.n_grades)
        out["OWN_SCORE"] = score.round(2)          # before group support
        out["FINAL_SCORE"] = score.round(2)        # group.apply_group_support() may change this
        out["FINAL_GRADE"] = score.round().clip(1, self.n_grades).astype(int)
        out["GRADE_LABEL"] = grade_label(score)

        if "MISSING_COUNT" in df.columns:
            share = df["MISSING_COUNT"] / len(self.params_["ratios"])
            out["DATA_QUALITY_FLAG"] = np.where(share > 0.4, "LOW", "OK")
        return out

    def fit_transform(self, df, ratios):
        return self.fit(df, ratios).transform(df)

    # --------------------------------------------------------------- helpers
    def _oriented_z(self, df):
        z = {}
        for r in self.params_["ratios"]:
            if r not in df.columns:
                continue
            d = REGISTRY[r].direction
            v = d * (df[r].astype(float) - self.params_["centre"][r]) / self.params_["scale"][r]
            if r in ONE_SIDED_RISK:
                v = v.clip(upper=0)
            cap = self.params_.get("capital_z_cap")
            if cap is not None and REGISTRY[r].pillar == "C":
                v = v.clip(upper=cap)
            z[r] = v.clip(-Z_CLIP, Z_CLIP)
        return pd.DataFrame(z, index=df.index)

    def _pillars(self, z):
        cols = {}
        for p in PILLARS:
            members = [r for r in z.columns if REGISTRY[r].pillar == p]
            if members:
                cols[p] = z[members].mean(axis=1)
        return pd.DataFrame(cols, index=z.index)

    def _composite(self, pillars):
        w = pd.Series({p: self.params_["weights"].get(p, 0) for p in pillars.columns})
        w = w / w.sum()
        return pillars.mul(w, axis=1).sum(axis=1)

    def _to_score(self, comp):
        """Continuous 1-10 score from the composite: 10.5 - 10 x (share of calibration
        composites below it), interpolated between the frozen decile cut-offs."""
        cuts = np.asarray(self.params_["composite_cuts"])
        qs = np.linspace(0, 1, self.n_grades + 1)[1:-1]
        lo = cuts[0] - (cuts[1] - cuts[0]); hi = cuts[-1] + (cuts[-1] - cuts[-2])
        pct = np.interp(comp.values, np.r_[lo, cuts, hi], np.r_[0.0, qs, 1.0])
        return pd.Series(np.clip(10.5 - 10 * pct, 1, self.n_grades), index=comp.index)

    def _to_grade(self, s, cuts):
        # number of cut-offs the score beats; beating all -> grade 1
        beaten = np.searchsorted(np.asarray(cuts), s.values, side="right")
        return pd.Series(self.n_grades - beaten, index=s.index).astype(int)

    # ------------------------------------------------------------ persistence
    def save(self, path):
        cfg = {"oe_weight": self.oe_weight, "max_uplift": self.max_uplift,
               "max_uplift_supported": self.max_uplift_supported, "n_grades": self.n_grades,
               "capital_z_cap": self.capital_z_cap, "loss_notch": self.loss_notch}
        with open(path, "w") as f:
            json.dump({"config": cfg, "params": self.params_}, f, indent=2)

    @classmethod
    def load(cls, path):
        with open(path) as f:
            blob = json.load(f)
        obj = cls(weights=blob["params"]["weights"], **blob["config"])
        obj.params_ = blob["params"]
        return obj

    def ratio_table(self) -> pd.DataFrame:
        """Calibration summary: what 'typical' looks like for each ratio."""
        rows = []
        for r in self.params_["ratios"]:
            rr = REGISTRY[r]
            rows.append({"ratio": r, "pillar": rr.pillar, "direction": rr.direction,
                         "median": round(self.params_["centre"][r], 3),
                         "robust_scale": round(self.params_["scale"][r], 3),
                         "core_2023": rr.core})
        return pd.DataFrame(rows)
