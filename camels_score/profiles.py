"""
Corrected version of the 2023 K-Means + PCA step, kept as a PEER-PROFILE tool, not as the grade.

What changed
  * Clustering runs on the direction-oriented z-scores, so "high" means sound for every ratio.
  * Clusters are ordered by their mean composite z-score (direction-aware), not by the plain
    average of raw ratio values, which was dominated by large-scale ratios and mixed good and
    bad directions.
  * Cluster labels are descriptive ("profile 1 = strongest") and sit next to the grade.
"""
import pandas as pd
from sklearn.cluster import KMeans
from sklearn.decomposition import PCA


def peer_profiles(scored: pd.DataFrame, n_clusters: int = 7, var_kept: float = 0.95, seed: int = 42):
    pz = [c for c in scored.columns if c.startswith("PILLAR_") and c.endswith("_Z")]
    X = scored[pz].values
    Xp = PCA(n_components=var_kept, random_state=seed).fit_transform(X) if len(pz) > 2 else X
    km = KMeans(n_clusters=n_clusters, n_init=10, random_state=seed).fit(Xp)
    out = scored.copy()
    out["CLUSTER"] = km.labels_
    order = out.groupby("CLUSTER")["COMPOSITE_Z"].mean().rank(ascending=False).astype(int)
    out["PROFILE"] = out["CLUSTER"].map(order)
    summary = out.groupby("PROFILE")[pz + ["COMPOSITE_Z"]].mean().round(2)
    summary["bank_years"] = out.groupby("PROFILE").size()
    return out.drop(columns="CLUSTER"), summary
