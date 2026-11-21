"""
Open operating-environment score (1 = strongest, 10 = weakest) from public data, as a
replacement for a proprietary country score. Input: the tidy World Bank file written by
tools/fetch_open_data.py (COUNTRY, YEAR, NAME, VALUE).

Components and weights (METHODOLOGY.md section 9):
  economic resilience 30%       GDP per capita (PPP, log), growth volatility (5 years), inflation
  credit and asset risk 30%     private credit / GDP against its 5-year average, sector NPL ratio
  funding and profitability 20% sector credit / deposits, sector return on assets
  institutions 20%              rule of law, regulatory quality

Each indicator becomes an oriented robust z-score against the country-years of the calibration
window (frozen), components are averaged, and the weighted composite is mapped to 1-10 through
the calibration window's decile cut-offs: the same construction as the bank scorecard.
The composite is a trailing 3-year average, because a country score should move slowly.
A missing indicator is skipped; a component with no data passes its weight to the others.
"""
import numpy as np
import pandas as pd

COMPONENTS = {
    "ECONOMY": (0.30, {"LOG_GDP_PER_CAPITA": +1, "GROWTH_VOLATILITY_5Y": -1, "INFLATION_ABOVE_2": -1}),
    "CREDIT_RISK": (0.30, {"CREDIT_GAP_5Y": -1, "SECTOR_NPL_RATIO": -1}),
    "FUNDING_PROFIT": (0.20, {"SECTOR_CREDIT_DEPOSITS": -1, "SECTOR_ROA": +1}),
    "INSTITUTIONS": (0.20, {"RULE_OF_LAW": +1, "REGULATORY_QUALITY": +1}),
}


def indicators(wb):
    """Wide country-year table of the indicators the score uses."""
    w = wb.pivot_table(index=["COUNTRY", "YEAR"], columns="NAME", values="VALUE").sort_index()
    g = w.groupby(level="COUNTRY")
    out = pd.DataFrame(index=w.index)
    out["LOG_GDP_PER_CAPITA"] = np.log(w["GDP_PER_CAPITA_PPP"])
    out["GROWTH_VOLATILITY_5Y"] = g["GDP_GROWTH"].transform(lambda s: s.rolling(5, min_periods=4).std())
    out["INFLATION_ABOVE_2"] = (w["INFLATION"] - 2).abs()
    credit = w["PRIVATE_CREDIT_GDP"].fillna(w.get("PRIVATE_CREDIT_GDP_GFDD"))
    out["CREDIT_GAP_5Y"] = credit - credit.groupby(level="COUNTRY").transform(
        lambda s: s.shift(1).rolling(5, min_periods=3).mean())
    out["SECTOR_NPL_RATIO"] = w["SECTOR_NPL_RATIO"].fillna(w.get("SECTOR_NPL_RATIO_GFDD"))
    for c in ("SECTOR_CREDIT_DEPOSITS", "SECTOR_ROA", "RULE_OF_LAW", "REGULATORY_QUALITY"):
        out[c] = w[c]
    return out.reset_index()


class OpenOE:
    def __init__(self, smooth_years=3):
        self.smooth_years = smooth_years      # trailing average: a country score should move slowly

    def fit(self, ind, calib_end=2017, calib_start=2010):
        ref = ind[ind["YEAR"].between(calib_start, calib_end)]
        self.centre, self.scale = {}, {}
        for _, (_, cols) in COMPONENTS.items():
            for c in cols:
                x = ref[c].dropna()
                self.centre[c] = float(x.median())
                mad = float((x - x.median()).abs().median()) * 1.4826
                self.scale[c] = mad if mad > 0 else float(x.std()) or 1.0
        comp = self._smoothed(ind)[ind["YEAR"].between(calib_start, calib_end)]
        self.cuts = np.quantile(comp.dropna(), np.linspace(0, 1, 11)[1:-1]).tolist()
        return self

    def _smoothed(self, ind):
        comp = self._composite(ind)
        d = ind[["COUNTRY", "YEAR"]].assign(C=comp).sort_values(["COUNTRY", "YEAR"])
        sm = d.groupby("COUNTRY")["C"].transform(lambda x: x.rolling(self.smooth_years, min_periods=1).mean())
        return sm.reindex(ind.index)

    def _composite(self, ind):
        parts, weights = [], []
        for name, (w, cols) in COMPONENTS.items():
            z = pd.concat([(d * (ind[c] - self.centre[c]) / self.scale[c]).clip(-3, 3)
                           for c, d in cols.items()], axis=1).mean(axis=1, skipna=True)
            parts.append(z.rename(name)); weights.append(w)
        P = pd.concat(parts, axis=1)
        W = pd.DataFrame({c: w for c, w in zip(P.columns, weights)}, index=P.index).where(P.notna())
        return (P * W).sum(axis=1) / W.sum(axis=1)

    def transform(self, ind):
        out = ind[["COUNTRY", "YEAR"]].copy()
        comp = self._smoothed(ind)
        c = self.cuts
        xs = np.r_[c[0] - (c[1] - c[0]), c, c[-1] + (c[-1] - c[-2])]
        pct = np.interp(comp, xs, np.linspace(0, 1, 11))
        out["OE_COMPOSITE_Z"] = comp.round(3)
        out["OE_SCORE_OPEN"] = np.clip(10.5 - 10 * pct, 1, 10).round(2)
        out["OE_SCORE"] = np.clip(np.round(out["OE_SCORE_OPEN"]), 1, 10).astype(int)
        return out


def build_open_oe(worldbank_csv, calib_end=2017, smooth_years=3):
    ind = indicators(pd.read_csv(worldbank_csv))
    return OpenOE(smooth_years).fit(ind, calib_end).transform(ind), ind
