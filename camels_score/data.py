"""Loading, cleaning and direction-aware imputation."""
import re
import numpy as np
import pandas as pd

from .ratios import REGISTRY, ID_COLS, OE_COL_CANDIDATES, LEGACY_ONLY


def _norm(col: str) -> str:
    return re.sub(r"\s+", " ", str(col)).strip().upper()


def load(path: str) -> pd.DataFrame:
    """Read xlsx or csv and normalise column names (the 2023 file has trailing spaces)."""
    df = pd.read_excel(path) if str(path).lower().endswith((".xlsx", ".xls")) else pd.read_csv(path)
    return standardise_columns(df)


def standardise_columns(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df.columns = [_norm(c) for c in df.columns]
    # 2023 file: "LIQUID ASSETS/ TOTAL DEPOSITS & BORROWINGS " -> registry name
    return df


def available_ratios(df: pd.DataFrame, min_coverage: float = 0.30) -> list:
    """Ratios present in the data with at least `min_coverage` non-missing values."""
    out = []
    for name in REGISTRY:
        if name in LEGACY_ONLY:
            continue
        if name in df.columns and df[name].notna().mean() >= min_coverage:
            out.append(name)
    return out


def oe_column(df: pd.DataFrame):
    for c in OE_COL_CANDIDATES:
        if c in df.columns:
            return c
    return None


def add_derived(df: pd.DataFrame) -> pd.DataFrame:
    """Ratios that can be built from history already in the panel."""
    df = df.copy()
    if "ROAA" in df.columns and "ID" in df.columns and "ROAA VOLATILITY 3Y" not in df.columns:
        df = df.sort_values(["ID", "YEAR"])
        df["ROAA VOLATILITY 3Y"] = (
            df.groupby("ID")["ROAA"].transform(lambda s: s.rolling(3, min_periods=3).std())
        )
    return df


# Ratios scored on a through-the-cycle basis: the weaker of the latest value and the 3-year
# average, as in Moody's bank scorecard (asset risk and profitability).
THROUGH_CYCLE = ["PROBLEM LOANS RATIO", "TEXAS RATIO", "LOAN LOSS RESERVE TO PROBLEM LOANS",
                 "COST OF RISK", "STAGE 2 LOANS RATIO", "ROAA", "ROAE", "NET INTEREST MARGIN",
                 "OPERATING RETURN ON ASSETS", "COST TO INCOME RATIO", "PRE-PROVISION PROFIT / RWA"]


def through_cycle(df: pd.DataFrame, ratios: list, window: int = 3) -> pd.DataFrame:
    """Replace each THROUGH_CYCLE ratio by the weaker of its latest value and its average over
    the last `window` years (at least 2 reported years; otherwise the latest value)."""
    df = df.sort_values(["ID", "YEAR"]).copy()
    for r in [x for x in THROUGH_CYCLE if x in ratios]:
        avg = df.groupby("ID")[r].transform(lambda s: s.rolling(window, min_periods=2).mean())
        d = REGISTRY[r].direction
        weaker = np.fmin(df[r], avg) if d == +1 else np.fmax(df[r], avg)
        df[r] = weaker.where(df[r].notna())
    return df.sort_index()


def clean(df: pd.DataFrame, ratios: list, winsor=(0.01, 0.99)) -> pd.DataFrame:
    """
    1. 'NM' and other text -> NaN, cast to float.
    2. Values outside the plausible bounds -> NaN (data errors, e.g. capital ratio > 100).
       The 2023 version dropped the whole bank-year; here only the bad value is removed.
    3. Winsorise each ratio within each year so one extreme bank cannot drive the scale.
    """
    df = df.copy()
    for r in ratios:
        s = pd.to_numeric(df[r].replace({"NM": np.nan, "nm": np.nan}), errors="coerce").astype(float)
        lo, hi = REGISTRY[r].bounds
        if lo is not None:
            s = s.where(s >= lo)
        if hi is not None:
            s = s.where(s <= hi)
        df[r] = s
    if winsor and "YEAR" in df.columns:
        lo_q, hi_q = winsor
        for r in ratios:
            g = df.groupby("YEAR")[r]
            df[r] = df[r].clip(g.transform(lambda x: x.quantile(lo_q)),
                               g.transform(lambda x: x.quantile(hi_q)))
    return df


def drop_empty_banks(df: pd.DataFrame, ratios: list, min_ratios: int = 5) -> pd.DataFrame:
    """Drop bank-years with fewer than `min_ratios` reported ratios (2023 version required only one)."""
    return df[df[ratios].notna().sum(axis=1) >= min_ratios].copy()


def impute_penalised(df: pd.DataFrame, ratios: list, penalty_quantile: float = 0.25) -> pd.DataFrame:
    """
    Fill a missing ratio with a deliberately weak value from the bank's own country-year peers.

    The 2023 version used nsmallest(5).median() for every ratio. For ratios where low is GOOD
    (Texas ratio, problem loans, leverage) that filled gaps with the BEST values, rewarding
    banks that did not report. It also returned one figure for all countries.

    Here the fill is the `penalty_quantile` of the country-year distribution on the WEAK side:
      direction +1 -> 25th percentile (low capital, low liquidity)
      direction -1 -> 75th percentile (high NPLs, high Texas ratio)
    Fallback when the country-year has too few peers: same rule on the year, then the panel.
    A MISSING_COUNT column is kept so the grade can be flagged for data quality.
    """
    df = df.copy()
    df["MISSING_COUNT"] = df[ratios].isna().sum(axis=1)
    for r in ratios:
        q = penalty_quantile if REGISTRY[r].direction == +1 else 1 - penalty_quantile
        fill_cy = df.groupby(["COUNTRY", "YEAR"])[r].transform(
            lambda x: x.quantile(q) if x.notna().sum() >= 5 else np.nan)
        fill_y = df.groupby("YEAR")[r].transform(lambda x: x.quantile(q))
        fill_all = df[r].quantile(q)
        df[r] = df[r].fillna(fill_cy).fillna(fill_y).fillna(fill_all)
    return df


def prepare(df: pd.DataFrame, min_coverage: float = 0.30, min_ratios: int = 5,
            return_unimputed: bool = False, multi_year: bool = True, return_reference: bool = False):
    """
    Full preparation. Returns (clean dataframe, list of ratios used) and, if asked, the
    cleaned but UNIMPUTED frame. Distress labels must be built from the unimputed frame,
    otherwise imputed values can create or hide events.
    """
    df = standardise_columns(df)
    df = add_derived(df)
    ratios = available_ratios(df, min_coverage)
    cleaned = clean(df, ratios)                       # raw reported values: used for labels
    scored_basis = through_cycle(cleaned, ratios) if multi_year else cleaned
    kept = drop_empty_banks(scored_basis, ratios, min_ratios)
    imputed = impute_penalised(kept, ratios)
    if return_reference:                              # + unimputed basis for calibration medians
        return imputed, ratios, cleaned, scored_basis
    return (imputed, ratios, cleaned) if return_unimputed else (imputed, ratios)


def merge_extra_ratios(df: pd.DataFrame, path) -> pd.DataFrame:
    """Merge a tidy file of extra ratios (ID, YEAR, then any REGISTRY ratio names such as
    CET1 RATIO, LOANS TO DEPOSITS, NSFR, COST OF RISK) into the panel. Ratios reach the score
    automatically once their coverage passes `min_coverage`; unknown columns are ignored."""
    extra = standardise_columns(load(path))
    known = [c for c in extra.columns if c in REGISTRY]
    unknown = [c for c in extra.columns if c not in REGISTRY and c not in ("ID", "YEAR")]
    if unknown:
        print(f"extra ratios: ignored unknown columns {unknown}")
    base = df.drop(columns=[c for c in known if c in df.columns])
    return base.merge(extra[["ID", "YEAR"] + known], on=["ID", "YEAR"], how="left")
