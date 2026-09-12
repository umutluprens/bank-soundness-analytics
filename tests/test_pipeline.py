from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parents[1] / "src"))

from bank_soundness.pipeline import FEATURE_COLUMNS, generate_demo_data, run_analysis


def test_demo_schema_and_outputs(tmp_path):
    frame = generate_demo_data(rows=300, seed=7)
    assert set(FEATURE_COLUMNS).issubset(frame.columns)
    assert "high_risk" not in frame.columns
    metrics = run_analysis(frame, tmp_path)
    assert set(metrics["model"]) == {"logistic_regression", "random_forest"}
    assert metrics["roc_auc"].between(0, 1).all()
    assert (tmp_path / "model_metrics.csv").exists()
    assert (tmp_path / "bank_clusters.csv").exists()
    assert (tmp_path / "feature_importance.csv").exists()
    assert (tmp_path / "roc_curve.png").exists()
