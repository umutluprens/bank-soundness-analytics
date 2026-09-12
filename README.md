# European Bank Soundness Analytics

An end-to-end financial data science project for profiling the soundness of European banks using CAMELS-style indicators, operating-environment measures, and explainable machine learning.

This repository is an individual portfolio adaptation of a Financial Data Science project completed at University College Dublin. The original study covered 8,033 bank-year observations across 18 European countries from 2010 to 2021.

## Business question

Which financial indicators provide the clearest early warning that a bank may have a weak capital position, and how can banks with similar risk profiles be grouped for monitoring?

The analysis combines two complementary views:

1. **Supervised risk screening** - classify bank-years whose total capital ratio is below a configurable threshold.
2. **Unsupervised segmentation** - use PCA and K-means to identify groups of banks with similar financial profiles.

## Portfolio highlights

- Financial-ratio cleaning and validation
- Leakage-aware target construction
- Time-based holdout evaluation
- Logistic-regression and random-forest benchmarks
- ROC-AUC and average-precision reporting
- PCA-based bank segmentation
- Reproducible command-line pipeline
- A synthetic demo mode that runs without licensed data

## Why the model excludes total capital ratio

The risk label is constructed from the total capital ratio. Using that same ratio as an input would leak the answer into the model. The modelling pipeline therefore excludes it from the predictor set and evaluates whether the remaining CAMELS indicators contain useful risk information.

## Repository structure

```text
.
├── data/README.md
├── notebooks/original_coursework_sanitised.ipynb
├── src/bank_soundness/
│   ├── __init__.py
│   └── pipeline.py
├── tests/test_pipeline.py
├── run_analysis.py
└── requirements.txt
```

## Quick start

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python run_analysis.py --demo --output results
```

To analyse an authorised dataset:

```bash
python run_analysis.py --input data/raw/bank_ratios.csv --output results
```

The pipeline writes model metrics, feature importance, cluster assignments, and an ROC chart to the selected output directory.

The `notebooks/` folder also contains the original end-to-end coursework notebook. Saved outputs and credentials were removed before publication; the notebook otherwise preserves the project's collection, database, visualisation, textual-analysis, and modelling code for reference.

## Expected data

Column names are normalised automatically. The minimum expected fields are:

- `bank_name`, `year`, and `country`
- `total_capital_ratio` for constructing the risk label
- CAMELS-style measures including Tier 1 ratio, Texas ratio, problem-loans ratio, net interest margin, profitability, liquidity, leverage, BICRA, and bank type

See [data/README.md](data/README.md) for the complete schema.

## Data availability

The original analysis used licensed financial data and information collected from annual reports. Those source files are deliberately not published here. The repository provides a synthetic demo so the analytical workflow can be reviewed and executed without redistributing restricted data.

## Interpretation and limitations

- This is a bank-soundness screening exercise, not a prediction of actual bank failure.
- A regulatory-ratio threshold is a proxy outcome and should not be treated as a default event.
- Bank-year observations from the same institution are related; production validation should use grouped and out-of-time testing.
- Results depend on data quality, reporting standards, and the representativeness of the selected countries.
- Model scores support analyst review; they do not replace supervisory or credit judgement.

## Skills demonstrated

Python, pandas, scikit-learn, financial-ratio analysis, CAMELS, data quality controls, model validation, explainability, PCA, K-means, and business communication.
