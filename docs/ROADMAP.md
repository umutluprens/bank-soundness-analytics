# Roadmap

## Phase 1: soundness scorecard (current, v0.8)

A grade for the latest reported year, built from ratios, the operating environment, group
support and a bounded overlay. See METHODOLOGY.md. Open items are listed at the end of FIXES.md.

## Phase 2: next-year forecast with machine learning

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

1. IMF WEO historical vintages for the 18 countries: done (`data/open/weo_vintages.csv`).
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

### First version (November 2026)

`camels_score/forecast.py`, run with `run_forecast.py`. Bank and country-score information only;
no macro expectations yet. Walk-forward on the 2010–2021 panel: each year from 2014 to 2021 is
forecast from the year before, with models trained only on earlier years (5,235 forecasts).
The score is the own score (country anchor and loss notch, before group support).

| Route | Error in notches (MAE) | Exact grade | Within one notch |
|---|---|---|---|
| Persistence (next year = this year) | 0.77 | 50.5% | 83.2% |
| Direct: gradient boosting on the score change | 0.74 | 52.2% | 84.3% |
| Ratios: gradient boosting on each ratio change, scored by the frozen scorecard | 0.72 | 53.4% | 84.7% |

- The ratio route beats persistence in all eight test years, by 7% on average and most in 2019
  and 2021. It is the route proposed above, and its forecasts can be traced to ratios.
- A first try on the score level, with mean-squared loss, did worse than persistence (MAE 0.80).
  Forecasting the change with a median loss fixed that: the score is persistent and its yearly
  changes are fat-tailed.
- The 10–90% range from the direct route covers 79% of outcomes after conformal calibration
  on the latest training year (75% before). Coverage still varies by year, from 68% (2014) to
  89% (2016, 2019), and the range is wide: about 2.3 notches on average.
- Downgrades are hard to call: the classifier ranks one-notch downgrades with AUC 0.64.
- Events: the forecast score ranks events in the next two years about as well as today's score
  (AUC 0.92–0.93 against 0.92), on 32 event bank-years. The forecast adds little to event
  warning yet.
- The yardstick (medians and cut-offs) is calibrated on 2010–2017, so the 2014–2017 targets are
  measured on a scale that saw those years. The model itself never sees its target year.

### Macro expectations (tested, not adopted)

IMF WEO October vintages for 2010–2021 were added through DBnomics (`data/open/weo_vintages.csv`,
`--macro`): for each country and year t, the growth, inflation and unemployment forecasts for t
and t+1 as published in October of year t. April 2011 stands in for October 2011, which is not
on DBnomics.

| Route | Without macro | With macro |
|---|---|---|
| Ratios, error in notches | 0.72 | 0.73 |
| Direct, error in notches | 0.74 | 0.75 |
| Downgrade classifier AUC | 0.64 | 0.63 |

The forecasts did not improve on bank-level information, including for 2020. With 18 countries
and 12 years the macro variables take few distinct values, and the country score already
carries most of the country signal. The option stays in the code; the default run does not use
it.

### EBA extension (v0.10)

The panel now runs to 2024 for 56 EU banks (METHODOLOGY.md section 15). Three more target years:

| Target years | Forecasts | Persistence | Direct | Ratio route | 80% range coverage |
|---|---|---|---|---|---|
| 2022–2024 | 159 | 0.54 | 0.46 | 0.36 | 80% |

`outlook_next_year.csv` holds the 2025 forecast for the 54 banks with 2024 data.

Next: use the EBA-only drivers (cost of risk, Stage 2 loans, CET1) as forecast features; they
exist from 2018, so the test window for them is short.

### Steps

| Step | Output |
|---|---|
| 1 | Point-in-time feature table: bank-year at t joined with WEO vintage for t+1 |
| 2 | Baselines and walk-forward framework (`camels_score/forecast.py`): done |
| 3 | Ratio forecasts with gradient boosting, scored by the frozen scorecard: done, first version |
| 4 | Downgrade probability and expected grade per bank in the output file |
| 5 | Scenario runs with EBA adverse paths |
| 6 | Validation report and methodology section for phase 2 |
