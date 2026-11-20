# Roadmap

## Phase 1: soundness scorecard (current, v0.6)

A grade for the latest reported year, built from ratios, the operating environment, group
support and a bounded overlay. See METHODOLOGY.md. Open items are listed at the end of FIXES.md.

## Phase 2: next-year forecast with machine learning (proposal)

**Question.** Given a bank's position at the end of year t and the expectations for year t+1
that were known at that time, what grade is the bank likely to have at t+1, and how likely is
it to move down?

The scorecard says where a bank stands. Phase 2 adds where it is heading. For limit setting this
matters most for banks near a threshold, where next year's direction decides the action.

### Design choice: forecast the ratios, keep the scorecard

The proposed approach forecasts the drivers and scores them with the frozen scorecard, rather
than training a model to predict the grade directly.

1. Forecast the main ratios for t+1: problem loans, reserve coverage, ROAA, NIM, cost-to-income,
   capital and liquidity ratios.
2. Score the forecast ratios with the v0.6 calibration to get an expected grade for t+1.
3. Produce a range (10th to 90th percentile) and the probability of a downgrade of one notch or
   more.

This keeps the forecast explainable: a forecast downgrade can be traced to the ratios expected
to weaken, and the grade means the same as in phase 1. A direct grade or event classifier is
kept as a challenger.

### Features (all as known at the end of year t)

| Group | Examples |
|---|---|
| Bank level, year t | All scored ratios, pillar z-scores, final score, data quality flag |
| Bank trend | 1-year and 3-year changes, ROAA volatility, loan growth |
| Group and country | Operating environment score, sovereign grade, parent score, support level |
| Expectations for t+1 | IMF World Economic Outlook forecasts for GDP growth, inflation and unemployment from the October vintage of year t; policy rate expectations where available |
| Scenario inputs | EBA stress test baseline and adverse paths (2014, 2016, 2018, 2021 exercises) for "what if" runs |

Point in time is the main rule: only the forecast vintage published by the end of year t may be
used, never the realised macro outcome. Using realised GDP would show forecast skill the model
could not have had.

### Models

| Model | Role |
|---|---|
| Persistence (t+1 = t) and bank-level AR(1) | Baselines every model must beat |
| Panel regression with country-year macro terms | Transparent benchmark |
| Gradient boosting (LightGBM or XGBoost), quantile loss | Main candidate for ratio forecasts and ranges |
| Gradient boosting classifier for downgrade and event within 2 years | Challenger |

Ranges are checked with conformal prediction, so a stated 80% interval covers about 80% of
outcomes out of sample.

### Validation

- Walk-forward by year: train on years up to t, forecast t+1, move one year on (first test year
  2014, using 2010–2013 for training).
- Ratio forecasts: error against persistence for each ratio.
- Grade forecasts: share of exact and within-one-notch hits, downgrade AUC, comparison with the
  grade migration matrix of phase 1.
- Events: does the forecast grade rank the next two years' events better than today's grade?
- Stress years reported separately (2011–2012 euro crisis, 2014–2015 Russia and Ukraine, 2020
  COVID), because a model that only works in calm years is of little use.

### Data needed

1. IMF WEO historical vintages (public, October of each year 2009–2021) for the 18 countries.
2. EBA stress test scenario files (public).
3. The extended ratio download already listed in METHODOLOGY.md section 12. Cost of risk, CET1
   and loans/deposits are the most useful forecast targets after problem loans and ROAA.
4. 2022–2025 data from the public sources in METHODOLOGY.md section 12 (EBA files for large EU
   banks), to extend the test period beyond 2021. Capital IQ is no longer available.

### Risks

- Small sample: about 7,900 bank-years over 12 years and few events. Strong regularisation,
  simple models first, and no feature selection on the test years.
- Regime change: 2020 support measures broke the usual link between GDP and loan losses.
- Survivorship: banks that failed leave the panel, so the forecast must be tested on the event
  file, not only on surviving banks.

### Steps

| Step | Output |
|---|---|
| 1 | Point-in-time feature table: bank-year at t joined with WEO vintage for t+1 |
| 2 | Baselines and walk-forward framework (`camels_score/forecast.py`) |
| 3 | Ratio forecasts with quantile gradient boosting, scored by the frozen scorecard |
| 4 | Downgrade probability and expected grade per bank in the output file |
| 5 | Scenario runs with EBA adverse paths |
| 6 | Validation report and methodology section for phase 2 |
