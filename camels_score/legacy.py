"""Faithful reproduction of the 2023 scoring rule (appendix F.5), for side-by-side comparison only."""
import pandas as pd
from sklearn.cluster import KMeans
from sklearn.decomposition import PCA
from sklearn.preprocessing import StandardScaler

LEGACY_X = ["TOTAL CAPITAL RATIO", "TIER1 RATIO", "TEXAS RATIO", "PROBLEM LOANS RATIO",
            "LOAN LOSS RESERVE TO PROBLEM LOANS", "NET INTEREST MARGIN", "ROAA", "ROAE",
            "LIQUID ASSETS/ TOTAL DEPOSITS & BORROWINGS", "TOTAL DEBT/ TOTAL EQUITY",
            "LIQUIDITY COVERAGE RATIO", "BOOKVALUE PER SHARE GROWTH",
            "OPERATING RETURN ON ASSETS", "NON-OPERATING EXPENSE RATIO", "BICRA"]
LEGACY_KEY = ["BICRA", "TOTAL CAPITAL RATIO", "TEXAS RATIO", "PROBLEM LOANS RATIO",
              "LOAN LOSS RESERVE TO PROBLEM LOANS", "NET INTEREST MARGIN", "ROAE",
              "LIQUID ASSETS/ TOTAL DEPOSITS & BORROWINGS", "TOTAL DEBT/ TOTAL EQUITY",
              "BOOKVALUE PER SHARE GROWTH", "OPERATING RETURN ON ASSETS",
              "NON-OPERATING EXPENSE RATIO"]


def legacy_score(df: pd.DataFrame) -> pd.Series:
    X = df[[c for c in LEGACY_X if c in df]].astype(float)
    X = X.fillna(X.median())          # 2023 input was already fully imputed
    Xp = PCA(n_components=0.95).fit_transform(StandardScaler().fit_transform(X))
    lab = KMeans(n_clusters=7, random_state=42, n_init=10).fit(Xp).labels_
    tmp = df.assign(cluster=lab)
    key = [c for c in LEGACY_KEY if c in df]
    perf = tmp[key + ["cluster"]].fillna(tmp[key].median()).groupby("cluster")[key].mean().mean(axis=1)   # raw average, mixed directions
    rank = perf.rank(ascending=True).astype(int)               # lowest average -> score 1
    return tmp["cluster"].map(rank)
