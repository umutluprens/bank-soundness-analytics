# European Bank Soundness Analytics

A transparent CAMELS scorecard that grades the soundness of European banks on a 1 to 10 scale,
and a tool that grades a bank outside the sample from three years of its own ratios.

The project started as a Financial Data Science MSc project at University College Dublin (2023)
on 8,033 bank-years across 18 European countries, 2010–2021. This repository rebuilds it as a
rating method: fixed weights and a frozen calibration, a country anchor and cap, group support,
and validation against real distress events rather than against the model's own labels.

## What it does

- **Grade.** 1 (soundest) to 10, with a continuous score and a `+` / `-` modifier, and S&P-style
  descriptors: 1–2 very strong, 3–4 strong, 5–6 adequate, 7–8 moderate, 9 weak, 10 very weak.
- **Six CAMELS pillars** from 14 ratios (36 in the registry, used once data is supplied), oriented
  robust z-scores, asset quality and earnings scored through the cycle.
- **Country anchor.** A 1–10 operating environment score is blended in and caps how far a bank can
  sit above its country.
- **Group support.** A stronger parent closes part of the gap as a support probability of at most
  0.5, reduced for large subsidiaries, withdrawn when the parent is under stress, and never above
  the country cap or the sovereign rating.
- **Bounded analyst overlay** of up to ±2 notches, with reason and date, excluded from the back-test.
- **New bank grader.** Command line or browser tool, same yardstick as the panel.

## Results on the 2010–2021 panel

Against 48 distress events (failures, resolutions, state aid, bail-ins; 32 verified against
official sources, `data/events.csv`), events within two years of the grade:

| Measure | 2023 project | This scorecard |
|---|---|---|
| AUC, all years | 0.71 | 0.90 |
| AUC, 2018–2021 (out of time) | 0.78 | 0.92 |
| Event rate, grades 1–4 | | 0 in 3,081 bank-years |
| Event rate, grade 10 | | 6.4% |

The 2023 model gave its second-best score to Bankia, Bank of Cyprus, Monte dei Paschi, NordLB and
Co-operative Bank in the years before their rescue; the scorecard grades them 8 to 10. The main
known miss is Greensill Bank, whose weakness was concentration and governance rather than ratios.
Details, limits and the comparison with S&P, Moody's and Fitch are in the documents below.

## Documents

| | |
|---|---|
| [docs/METHODOLOGY.md](docs/METHODOLOGY.md) | Rating scale, pillars, scoring steps, group support, validation, governance |
| [docs/COMPARISON.md](docs/COMPARISON.md) | Design compared with S&P, Moody's and Fitch bank methodologies |
| [docs/FIXES.md](docs/FIXES.md) | What changed from the 2023 project and why |
| [docs/SOURCES.md](docs/SOURCES.md) | Every external source behind the method and the input files |
| [docs/ROADMAP.md](docs/ROADMAP.md) | Phase 2: next-year forecast with machine learning |

## Quick start

```bash
pip install -r requirements.txt
python run_pipeline.py --synthetic --out results_synthetic/   # runs without any data
python -m pytest -q tests
```

With a bank-year panel (one row per bank and year, ratio names as in `camels_score/ratios.py`):

```bash
python run_pipeline.py --input panel.csv --events data/events.csv --parents data/parents.csv \
    --sovereign data/sovereign_ratings.csv --overlays data/overlays.csv --out results/
```

Outputs: `camels_scores.xlsx` (grades, pillars, support, events by bank-year; grade tables;
migration; peer profiles), `validation_report.json` and `calibration.json` (the frozen yardstick).

## Grade a new bank

```bash
# one row per ratio, one column per year (up to three); see templates/new_bank_template.csv
python score_new_bank.py --input templates/example_bank.csv --calibration results/calibration.json \
    --country-score 4 --sovereign BBB --name "Example Bank"
# a parent: --parent-rating A --support strategic --assets-share 0.08     overlay: --overlay 1

# browser version with the calibration embedded
python tool/build_tool.py --calibration results/calibration.json --out results/camels_new_bank_tool.html
```

For bank-years with full data the new-bank route gives the same grade as the pipeline in 99.3%
of cases; the browser tool and the Python route give identical results (`tests/test_newbank.py`).

## Repository structure

```text
camels_score/        scorecard package: ratios, data preparation, scoring, group support,
                     overlays, validation, peer profiles, new-bank scoring
run_pipeline.py      calibrate, grade and validate a panel
score_new_bank.py    grade one bank from a template
compare_legacy.py    2023 score against the new grade
data/                events, parent mapping, sovereign ratings, overlays (each row with its source)
templates/           new-bank template and a fictitious example
tool/                browser tool (template, scoring engine, build script)
tools/               rebuilds docs/SOURCES.md from the input files
docs/                methodology and supporting documents
src/bank_soundness/  earlier portfolio pipeline (capital-ratio screening, PCA and K-means)
notebooks/           original 2023 coursework notebook, outputs and credentials removed
tests/
```

## Data availability

The 2010–2021 panel was exported from S&P Capital IQ, and the country scores are S&P BICRA
groups. The figures come from public bank reports, but the exports and BICRA fall under S&P's
terms of use, so neither they nor bank-level results built from them are published here. The
files in `data/` were compiled for this project from public sources, which are listed row by row.
The synthetic panel lets the whole workflow run without restricted data. A rebuild of the panel
from public sources (EBA transparency data, national supervisors, annual reports) is planned.

## Earlier pipeline

`run_analysis.py` and `src/bank_soundness/` hold the first portfolio adaptation of the coursework:
a classifier for bank-years with a total capital ratio below a threshold (with the ratio itself
excluded from the inputs to avoid leakage) and PCA plus K-means segmentation.

```bash
python run_analysis.py --demo --output results
```

## Limitations

- Few distress events, especially after 2017 (10 event bank-years in 2018–2021).
- Parent support levels are assumed from brand names and await confirmation.
- No market-risk sensitivity ratios yet; liquidity rests on one ratio.
- The grade ranks relative soundness. It is not a probability of default or a credit rating, and
  it supports analyst judgement rather than replacing it.

Author: Umut Yasar. MSc Financial Data Science, University College Dublin.
