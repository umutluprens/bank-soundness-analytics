"""Leakage-aware bank soundness modelling and segmentation pipeline."""

from __future__ import annotations

import json
import re
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from sklearn.cluster import KMeans
from sklearn.compose import ColumnTransformer
from sklearn.decomposition import PCA
from sklearn.ensemble import RandomForestClassifier
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (
    RocCurveDisplay,
    average_precision_score,
    classification_report,
    roc_auc_score,
)
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler


FEATURE_COLUMNS = [
    "tier1_ratio",
    "texas_ratio",
    "problem_loans_ratio",
    "loan_loss_reserve_to_problem_loans",
    "net_interest_margin",
    "roaa",
    "roae",
    "liquid_assets_total_deposits_borrowings",
    "total_debt_total_equity",
    "liquidity_coverage_ratio",
    "book_value_per_share_growth",
    "operating_return_on_assets",
    "non_operating_expense_ratio",
    "bicra",
    "bank_type",
]

NUMERIC_FEATURES = [column for column in FEATURE_COLUMNS if column != "bank_type"]
REQUIRED_COLUMNS = {"bank_name", "year", "country", "total_capital_ratio", *FEATURE_COLUMNS}


def _snake_case(value: str) -> str:
    value = re.sub(r"[^a-zA-Z0-9]+", "_", str(value).strip().lower())
    aliases = {
        "liquid_assets_total_deposits_borrowings_": "liquid_assets_total_deposits_borrowings",
        "bookvalue_per_share_growth": "book_value_per_share_growth",
        "type": "bank_type",
        "bank_name_": "bank_name",
    }
    return aliases.get(value, value.strip("_"))


def load_bank_data(path: str | Path) -> pd.DataFrame:
    frame = pd.read_csv(path)
    frame.columns = [_snake_case(column) for column in frame.columns]
    missing = sorted(REQUIRED_COLUMNS - set(frame.columns))
    if missing:
        raise ValueError(f"Missing required columns: {', '.join(missing)}")
    frame["year"] = pd.to_numeric(frame["year"], errors="coerce")
    for column in ["total_capital_ratio", *NUMERIC_FEATURES]:
        frame[column] = pd.to_numeric(frame[column], errors="coerce")
    return frame.dropna(subset=["bank_name", "year", "total_capital_ratio"]).copy()


def generate_demo_data(rows: int = 1_200, seed: int = 42) -> pd.DataFrame:
    """Create realistic-looking synthetic bank-year records for a runnable demo."""
    rng = np.random.default_rng(seed)
    years = rng.integers(2010, 2022, rows)
    countries = rng.choice(["Ireland", "Germany", "France", "Spain", "Italy", "Poland"], rows)
    bank_types = rng.choice(
        ["Diversified Commercial Bank", "Savings Bank", "Investment Bank"],
        rows,
        p=[0.65, 0.25, 0.10],
    )
    stress = rng.normal(0, 1, rows) + np.where(years <= 2012, 0.5, 0)
    tier1 = np.clip(15 - 1.8 * stress + rng.normal(0, 1.7, rows), 4, 30)
    total_capital = np.clip(tier1 + rng.normal(2.3, 1.1, rows), 5, 35)
    return pd.DataFrame(
        {
            "bank_name": [f"Synthetic Bank {i % 160:03d}" for i in range(rows)],
            "year": years,
            "country": countries,
            "total_capital_ratio": total_capital,
            "tier1_ratio": tier1,
            "texas_ratio": np.clip(28 + 16 * stress + rng.normal(0, 10, rows), 0, 160),
            "problem_loans_ratio": np.clip(4 + 2.5 * stress + rng.normal(0, 2, rows), 0, 35),
            "loan_loss_reserve_to_problem_loans": np.clip(70 - 10 * stress + rng.normal(0, 12, rows), 5, 160),
            "net_interest_margin": np.clip(2.4 - 0.15 * stress + rng.normal(0, 0.5, rows), -1, 7),
            "roaa": rng.normal(0.8 - 0.35 * stress, 0.6, rows),
            "roae": rng.normal(8 - 2.2 * stress, 4, rows),
            "liquid_assets_total_deposits_borrowings": np.clip(rng.normal(26 - stress, 7, rows), 3, 70),
            "total_debt_total_equity": np.clip(rng.normal(8 + stress, 2.5, rows), 0.5, 25),
            "liquidity_coverage_ratio": np.clip(rng.normal(145 - 8 * stress, 28, rows), 45, 300),
            "book_value_per_share_growth": rng.normal(4 - 1.2 * stress, 7, rows),
            "operating_return_on_assets": rng.normal(1.0 - 0.3 * stress, 0.7, rows),
            "non_operating_expense_ratio": np.clip(rng.normal(2.2 + 0.2 * stress, 0.7, rows), 0, 8),
            "bicra": np.clip(np.rint(rng.normal(4.5 + 0.7 * stress, 1.5, rows)), 1, 10),
            "bank_type": bank_types,
        }
    )


def _preprocessor(scale: bool) -> ColumnTransformer:
    numeric_steps = [("impute", SimpleImputer(strategy="median"))]
    if scale:
        numeric_steps.append(("scale", StandardScaler()))
    return ColumnTransformer(
        [
            ("numeric", Pipeline(numeric_steps), NUMERIC_FEATURES),
            (
                "category",
                Pipeline(
                    [
                        ("impute", SimpleImputer(strategy="most_frequent")),
                        ("one_hot", OneHotEncoder(handle_unknown="ignore")),
                    ]
                ),
                ["bank_type"],
            ),
        ]
    )


def _time_split(frame: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    years = sorted(frame["year"].dropna().unique())
    if len(years) < 2:
        raise ValueError("At least two reporting years are required for out-of-time evaluation.")
    cutoff = years[max(1, int(len(years) * 0.7)) - 1]
    train = frame[frame["year"] <= cutoff].copy()
    test = frame[frame["year"] > cutoff].copy()
    if train.empty or test.empty:
        raise ValueError("Unable to create a non-empty time-based holdout.")
    return train, test


def _evaluate(name: str, model: Pipeline, train: pd.DataFrame, test: pd.DataFrame) -> tuple[dict, np.ndarray]:
    x_train, x_test = train[FEATURE_COLUMNS], test[FEATURE_COLUMNS]
    y_train, y_test = train["high_risk"], test["high_risk"]
    model.fit(x_train, y_train)
    probabilities = model.predict_proba(x_test)[:, 1]
    predictions = (probabilities >= 0.5).astype(int)
    report = classification_report(y_test, predictions, output_dict=True, zero_division=0)
    metrics = {
        "model": name,
        "roc_auc": roc_auc_score(y_test, probabilities),
        "average_precision": average_precision_score(y_test, probabilities),
        "precision_high_risk": report["1"]["precision"],
        "recall_high_risk": report["1"]["recall"],
        "test_observations": len(test),
    }
    return metrics, probabilities


def _cluster(frame: pd.DataFrame, clusters: int = 5) -> pd.DataFrame:
    imputed = SimpleImputer(strategy="median").fit_transform(frame[NUMERIC_FEATURES])
    scaled = StandardScaler().fit_transform(imputed)
    components = PCA(n_components=0.90, random_state=42).fit_transform(scaled)
    labels = KMeans(n_clusters=clusters, random_state=42, n_init=20).fit_predict(components)
    result = frame[["bank_name", "year", "country"]].copy()
    result["cluster"] = labels
    return result


def run_analysis(frame: pd.DataFrame, output_dir: str | Path, threshold: float = 12.0) -> pd.DataFrame:
    """Run the supervised benchmark and unsupervised segmentation workflow."""
    output = Path(output_dir)
    output.mkdir(parents=True, exist_ok=True)
    data = frame.copy()
    missing = sorted(REQUIRED_COLUMNS - set(data.columns))
    if missing:
        raise ValueError(f"Missing required columns: {', '.join(missing)}")
    data["high_risk"] = (data["total_capital_ratio"] < threshold).astype(int)
    train, test = _time_split(data)

    models = {
        "logistic_regression": Pipeline(
            [("prepare", _preprocessor(scale=True)), ("model", LogisticRegression(max_iter=2_000, class_weight="balanced"))]
        ),
        "random_forest": Pipeline(
            [
                ("prepare", _preprocessor(scale=False)),
                (
                    "model",
                    RandomForestClassifier(
                        n_estimators=400,
                        min_samples_leaf=8,
                        class_weight="balanced_subsample",
                        random_state=42,
                        n_jobs=-1,
                    ),
                ),
            ]
        ),
    }

    rows: list[dict] = []
    fig, ax = plt.subplots(figsize=(7, 5))
    for name, model in models.items():
        metrics, probabilities = _evaluate(name, model, train, test)
        rows.append(metrics)
        RocCurveDisplay.from_predictions(
            test["high_risk"], probabilities, name=name.replace("_", " "), ax=ax
        )
    ax.plot([0, 1], [0, 1], linestyle="--", color="grey", linewidth=1)
    ax.set_title("Out-of-time bank risk screening")
    fig.tight_layout()
    fig.savefig(output / "roc_curve.png", dpi=180)
    plt.close(fig)

    forest = models["random_forest"]
    feature_names = forest.named_steps["prepare"].get_feature_names_out()
    feature_importance = pd.DataFrame(
        {
            "feature": feature_names,
            "importance": forest.named_steps["model"].feature_importances_,
        }
    ).sort_values("importance", ascending=False)
    feature_importance.to_csv(output / "feature_importance.csv", index=False)

    metrics_frame = pd.DataFrame(rows).sort_values("roc_auc", ascending=False)
    metrics_frame.to_csv(output / "model_metrics.csv", index=False)
    _cluster(data).to_csv(output / "bank_clusters.csv", index=False)
    metadata = {
        "risk_threshold": threshold,
        "training_years": [int(train["year"].min()), int(train["year"].max())],
        "test_years": [int(test["year"].min()), int(test["year"].max())],
        "predictors_exclude_target_constructor": True,
    }
    (output / "run_metadata.json").write_text(json.dumps(metadata, indent=2), encoding="utf-8")
    return metrics_frame
