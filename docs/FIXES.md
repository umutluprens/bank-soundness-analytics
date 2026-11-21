# Fix log: 2023 UCD CAMELS project → camels-score v0.9

Sources reviewed: FDS Final Report (Executive Style), 21 April 2023, with its code appendix, and
the original 2023 data folder (CAMELS_2010–2021.xlsx, Data_Management_2.xlsx, BICRA.xlsx,
merged_data.xlsx, merged_data_with_clusters_and_scores_PCA.xlsx). The GitHub repository itself
was not reachable from this session; the code was rebuilt from the appendix.

## Results on the real 2023 data

Panel rebuilt from the raw Capital IQ files: 7,867 bank-years, 18 countries, 2010–2021,
14 ratios scored. Calibration on 2010–2017; 2018–2021 is out-of-time. Labels are built from
unimputed data and never enter the scorecard.

**Against real distress events** (seed list of 28 failures, resolutions, state aid and
distressed recapitalisations; v0.3 seed list, since replaced by `data/events.csv`; event within 2 years):

| Score | AUC all years | AUC 2018+ |
|---|---|---|
| 2023 score (actual output file) | 0.632 | 0.735 |
| New final grade | **0.916** | **0.869** |
| New standalone grade (no country anchor) | 0.924 | 0.897 |

Event rate by new final grade: 0% in grades 1–6 (one exception in grade 3), 0.6% in grade 8,
2.8% in grade 9, 7.6% in grade 10. The 2023 model gave its second-best score (2) to Bankia,
Bank of Cyprus, Eurobank, Monte dei Paschi (2011–12), NordLB, Co-operative Bank, Liberbank,
Cajatres and Dexia SA in the years before their rescue; the new grades put almost all of them
at 9–10. Clear miss: Greensill Bank (grade 4), whose failure came from fraud and concentration
that balance-sheet ratios do not show.

Caution: only 40 event bank-years (7 after 2017). The list is a seed built from public knowledge
and must be checked against official sources (SRB, ECB, EC state aid register, national
authorities) and extended before any figure is quoted externally.

**Against the forward proxy** (next-year capital < 10.5%, ROAA < -1% or NPL spike):

| Score | AUC all years | AUC 2018+ |
|---|---|---|
| 2023 score | 0.603 | 0.549 |
| New final grade | 0.728 | 0.599 |
| Logit on the same pillar scores (challenger) | | 0.818 |

After 2017 the proxy is almost entirely "loss next year" (132 of 142 cases; no capital breaches),
which the Earnings pillar predicts well (AUC 0.81 alone) but which carries only 15% weight.
It is weak evidence of distress, so the expert weights were not tuned to it.

**Findings about the 2023 data**

- `merged_data.xlsx` is already imputed: 64% of LCR values, 21–27% of asset-quality and
  liquidity values, 16% of total capital values were filled in. It should not be used to calibrate.
- LCR exists in Capital IQ only from 2014–15 (below 40% coverage in every year), so it is
  dropped automatically until better data is available.
- The 2023 score uses 7 levels, with 43% of bank-years in score 2, which limits its ability
  to separate banks.
- The sample contains the Netherlands, not Belarus as the report text says (Belarus is only in
  the BICRA file).
- The NON-OPERATING EXPENSE RATIO ranges from -580,600% to 257,720%, confirming the formula issue (#5).
- Banks that later failed are present in the export (Veneto Banca, Delta Bank, PrivatBank,
  Greensill), so survivorship bias is limited.

**Open methodology issues found in real data**

- Top grades (1–2) include small, very highly capitalised, loss-making niche banks (UK: Melli
  Bank, Al Rayan, Hampshire Trust). Their next-year loss rate (7–10%) is higher than grades 3–5.
  The 2023 report noted the same pattern. Options: cap the credit given for capital above a
  level, and notch down loss-making banks.
- PSI of the composite between 2010–17 and 2018–21 is 0.21 (a material shift: banks improved
  after the crisis). Grades remain comparable because the yardstick is frozen, but the
  calibration window should be reviewed.
- Country anchor: a blend weight of 0 (cap only) gave the best event AUC; the default was cut
  from 35% to 15% pending more events.

## Measured on a synthetic panel (core 2023 ratios), before the real data was available

| Check | 2023 rule | Fixed scorecard |
|---|---|---|
| AUC vs future distress events | 0.721 | 0.727 |
| AUC after adding one ratio (LCR) to the scoring list | **0.518** (random) | stable, ratios are direction-aligned |
| Past scores that change when later years are added | **48.6%** | 0% (frozen calibration) |
| "Validation" AUC of a model re-predicting its own label | 0.990 | not used |

Reading: on clean one-factor synthetic data the 2023 rule ranks banks roughly correctly, but
only because Total Debt / Total Equity carries 38% of the cluster ordering and happens to point
the right way (high = weak). Adding a single "high = good" ratio with a large scale breaks it.
Since the plan is to add more ratios, the old rule could not be extended safely.

## Methodology fixes

| # | Issue in 2023 version | Where | Fix in v0.2 |
|---|---|---|---|
| 1 | Cluster score = plain average of raw ratio values. Mixes directions (high capital good, high Texas ratio bad) and is dominated by large-scale ratios. | App. F.5.3 | Every ratio has a direction in `ratios.py`. Scores use oriented robust z-scores, so positive always means sounder. |
| 2 | Final XGBoost predicts "score ≤ 5", a label built from the same ratios. AUC 0.997 is circular. | §6.6, App. F.5.5 | `validation.py` tests grades against FUTURE outcomes only: external event file (preferred) or a forward proxy (capital < 10.5%, ROAA < -1%, NPL spike). Out-of-time split. |
| 3 | No distress outcome anywhere in the project. | whole | Event-file interface (`ID, YEAR, EVENT`) plus forward proxy. Disappearing banks are not counted as failures (could be mergers). |
| 4 | Sensitivity to market risk pillar is empty. None of the 14 ratios measure it. | §1.2 | Six S ratios added: EVE and NII sensitivity, FX loans share, net open FX position, securities share, unrealised securities losses / CET1. |
| 5 | Management pillar rests on one self-built ratio whose formula subtracts a stock (loan loss reserve) from a flow (operating income). | §2.1.4 | Cost-to-income added as the main efficiency ratio; non-interest income share added; legacy ratio kept for comparability and flagged. |
| 6 | Missing values filled with `nsmallest(5).median()` for every ratio. For "low is good" ratios this filled gaps with the BEST values, rewarding non-reporting banks. It also returned one figure for all countries. | App. B.1.10 | Direction-aware penalty: weak-side quartile of the bank's country-year peers, with year and panel fallbacks. `MISSING_COUNT` and a data-quality flag are kept. |
| 7 | `IterativeImputer` fitted on one column at a time, which reduces to mean imputation. | App. B.1.10 | Removed. |
| 8 | Whole bank-year dropped if total capital ratio > 100. | §2.2.3 | Only the implausible value is removed, using bounds per ratio, then winsorised at 1%/99% per year. |
| 9 | Banks kept with only one ratio reported. | §2.2.2 | Minimum of 5 reported ratios per bank-year. |
| 10 | Report says scores 1 to 10, the model has 7 clusters; text says "sound ≥ 5", code uses `score <= 5`. | §7.1, §7.3, App. F.5.5 | Single 1–10 scale, 1 = soundest, same orientation as BICRA. |
| 11 | Clusters refitted on pooled data, so a grade has no fixed meaning and changes when data is added. | App. F.5 | Medians, scales and grade cut-offs frozen in `calibration.json` at fit time. New years are scored on the same yardstick. |
| 12 | Multicollinearity (Tier 1 vs total capital, ROAA vs ROAE) handled by PCA, which makes the score unexplainable. | §6.5, §7.1 | Correlated ratios share one pillar weight, so they are not double counted and every grade can be traced to ratios. K-Means + PCA kept as a peer-profile tool on oriented data (`profiles.py`). |
| 13 | Operating environment entered as just another feature, so a bank in a weak country could still score top grade. | §7.2 | OE becomes an anchor: blended into the grade and a bank cannot be more than 2 notches better than its country score (4 with parent support). |
| 14 | Small subsidiaries and branches of foreign groups clustered as best banks (noted in §7.2). | §7.2 | `PARENT_SUPPORT` flag: standalone grade and supported grade are reported separately. |
| 15 | Business-model mixing (group vs bank-only accounts, Permanent TSB example). | §7.2 | Not solved in code; documented as a data rule: score bank-level accounts, or flag consolidation level. |

## Supervised-model bugs (kept only as challengers now)

| # | Issue | Where | Fix |
|---|---|---|---|
| 16 | `RISK_12` target derived from total capital ratio while Tier 1, which the report itself calls highly correlated with it (§7.1), is a feature: target leakage. | §6.1 | Not used. Challengers predict future distress. |
| 17 | Logistic ROC computed on the full dataset including training rows. | App. F.1 | Out-of-time test set only. |
| 18 | Decision tree fitted on all data, then "tested" on a random split of the same data, using hard 0/1 predictions for ROC. | App. F.2.3 | Removed. |
| 19 | Grid search picked `max_features=6`, model trained with 7. | App. F.3.2 | Removed. |
| 20 | XGBoost train AUC 1.000 is overfitting, not "exceptional performance". | §6.4 | Challenger is depth-limited and train/test AUC are both reported. |
| 21 | "R-squared" of a logit reported as share of variance explained. | §6.1 | Use McFadden pseudo R² wording if reported. |

## Code hygiene

| # | Issue | Fix |
|---|---|---|
| 22 | NewsAPI key in plain text (App. E.0.1) and a former employer email in the scraping code (App. A.2). | **Rotate the NewsAPI key and remove both from the repo history** (`git filter-repo` or BFG). Use environment variables. |
| 23 | BICRA scraped with paid credentials; Capital IQ data is licensed. | Product code reads any 1–10 country score (`OE_SCORE` or `BICRA`). Raw licensed data should not be committed. |
| 24 | `CAMELS_2013.xlsx` read three times; year dictionaries zipped by insertion order. | Single tidy panel with `YEAR` column; no year-by-year variables. |
| 25 | Trailing space in `LIQUID ASSETS/ TOTAL DEPOSITS & BORROWINGS ` column. | Column names normalised on load. |

## Added in v0.3 (real data)

| # | Change |
|---|---|
| 26 | `capiq.py` rebuilds the panel from the raw yearly exports. Columns are mapped by position because the export headers change by year (`SNL_TOTAL_CAPITAL_RATIO7`, `27377078` for ROAA in 2010). |
| 27 | Cost-to-income, ROAA volatility (3 years) and log total assets added from data already in the folder. |
| 28 | Legacy non-operating expense ratio kept for comparison but no longer scored. |
| 29 | Distress labels built from unimputed data. |
| 30 | Calibration medians and scales taken from reported values only, not from penalty-imputed values. |
| 31 | Country blend weight cut from 35% to 15%; 2-notch cap kept. |

## Added in v0.4

| # | Change |
|---|---|
| 32 | `data/events.csv`: 48 events at 43 banks, 30 verified against official sources (NBU, CBAR, Finanstilsynet, Finansiel Stabilitet, Bank of Italy, FITD, ECB, BaFin, BFG, EC). Replaces the 28-event seed list. |
| 33 | Capital ceiling: a capital ratio adds at most z = +1. Fixes top grades for highly capitalised loss-making niche banks (next-year loss rate in grades 1–2 fell from 8.4% to 4.1%, in line with grades 3–5). |
| 34 | Loss notch: 1 notch down if ROAA < 0, 2 if ROAA < -1%. |
| 35 | METHODOLOGY.md written: scale, pillars, steps, reference bands, overrides, open country score design, validation, data request, governance. |

v0.4 results with the full event file: AUC 0.90 all years and 0.92 after 2017 (2023 score: 0.71 and 0.78).
The v0.3 figures above were measured on the 28-event seed list and are kept for the record.

## Added in v0.5

| # | Change |
|---|---|
| 36 | Continuous `FINAL_SCORE` (1.00–10.00) with `GRADE_LABEL` modifiers (`6+`, `6`, `6-`), so effects below one notch are visible. |
| 37 | Group support (`camels_score/group.py`), support only: subsidiary closes p × the gap to a stronger parent, with support probability p = 0.50 core, 0.35 strategic, 0.15 moderate (maximum 0.5). |
| 38 | Country score is a hard cap for every bank: support cannot lift a bank more than 2 notches above its country score, so a subsidiary in a weak country never reaches its parent's grade. A weaker parent does not pull the subsidiary down (left to analyst override). The old `PARENT_SUPPORT` flag is read as `strategic`. |
| 39 | `data/parents.csv`: 68 foreign-owned subsidiaries found by brand name; 47 with the parent in the panel, 21 needing an external `PARENT_GRADE`. Support levels assumed, marked for review. Indicative rating-to-grade map added. |

Effect: 167 of 498 subsidiary bank-years with a parent score receive support (mean 0.97 notches); 111 change grade, 56 move within the notch. Event AUC unchanged at 0.91 (few events on subsidiaries), so the rule rests on credit judgement, not back-test evidence.

## Added in v0.6 (agency comparison applied)

| # | Change |
|---|---|
| 40 | Through-the-cycle ratios: asset quality and earnings ratios are scored on the weaker of the latest value and the 3-year average (Moody's). Calibration medians use the same basis; outcome labels keep the latest values. `--no-multi-year` switches it off. |
| 41 | Sovereign cap on support: `data/sovereign_ratings.csv` (Fitch long-term FC rating at 31 December, 18 countries, 2010–2021, source per row). Support cannot lift a bank above its sovereign grade. |
| 42 | Ability factor: support probability × 0.75 when the subsidiary has 10–20% of the parent's total assets, × 0.50 above 20% (Fitch relative size). |
| 43 | Parent stress years (`STRESS_FROM` in parents.csv): support withdrawn for VTB and Sberbank subsidiaries from 2014 (EU sanctions), Greek parents' Cypriot subsidiaries from 2013 (HFSF recapitalisation), Banca Apulia and Banca Nuova from 2016 (Atlante). No downward pull, in line with the support-only rule. |
| 44 | `WEAK_PARENT` flag where the parent scores at least one notch weaker; information only. |
| 45 | Qualitative overlay (`camels_score/overlays.py`, `data/overlays.csv`): five factors, total capped at ±2 notches, reason, analyst and decision date required, applied point in time, excluded from the back-test. |
| 46 | `--extra-ratios`: any tidy ID/YEAR file with registry ratio names (CET1, loans/deposits, NSFR ...) is merged and scored once coverage reaches 30%. |
| 47 | The 0.5 support ceiling documented as a deliberate conservative choice. SOURCES.md appendix added (rebuilt by `tools/build_sources.py`). Two Greek events re-checked against Commission decisions (32 verified, 16 to re-check). Parent list 70 subsidiaries (Banca Apulia, Banca Nuova added). 27 tests. |

Effect: event AUC 0.91 overall and 0.92 after 2017 (unchanged); proxy AUC after 2017 0.70 to 0.73; grade vs event-rate rank correlation 0.94 to 0.96; composite PSI 0.21 to 0.15. Grade 10 now holds 10.5% of bank-years (8.4% in v0.5). 159 subsidiary bank-years receive support (167 in v0.5).

## Added in v0.7

| # | Change |
|---|---|
| 48 | Pillar weights changed to C 20%, A 30%, M 5%, E 25%, L 15%, S 5% (decision, Nov 2026). Country cap of 2 notches and loss notch on three-year earnings kept. |
| 49 | Grade descriptors in the S&P style: 1–2 very strong, 3–4 strong, 5–6 adequate, 7–8 moderate, 9 weak, 10 very weak (`GRADE_DESCRIPTOR`). |
| 51 | New-bank scoring: `camels_score/newbank.py`, `score_new_bank.py` with a CSV template, and a browser tool (`tool/`). Calibration now stores the pooled percentiles and weak-side fill values a single bank needs. Same grade as the pipeline for 99.3% of 2,474 full-data bank-years. 31 tests. |
| 50 | Data plan moved to public sources (EBA Transparency Exercise and Pillar 3 Data Hub, National Bank of Ukraine, Banks Association of Türkiye, annual reports), since Capital IQ is no longer available. |

Effect of the new weights: event AUC 0.90 all years (0.91), 0.92 after 2017 (unchanged); proxy AUC after 2017 0.77 (0.73); PSI 0.20 (0.15); grade 10 share 11.1% (10.5%). The gain is on the earnings-driven proxy; event ranking is flat.

## Added in v0.8

| # | Change |
|---|---|
| 52 | The 16 remaining events checked against official sources (European Commission decisions, Central Bank of Ireland, Banco de España, Bank of England, ECB, ESM, Eurostat, National Bank of Ukraine). All 48 events are now verified. Eurobank 2015 reclassified from state aid to distressed recapitalisation (covered privately). Back-test unchanged. |
| 54 | New-bank grader accepts annual-report figures (`--raw`, `templates/raw_items_template.csv`): 18 items per year, ratios calculated with the panel's definitions. Forecast ranges calibrated with conformalised quantile regression (coverage 75% to 79%). |
| 53 | Phase 2, first version: `camels_score/forecast.py` and `run_forecast.py`. Walk-forward forecast of next year's score by three routes (persistence, direct, ratios scored by the frozen scorecard), downgrade classifier, 80% range, slot for macro expectations. 33 tests. |

## Added in v0.9

| # | Change |
|---|---|
| 55 | Open operating-environment score (`camels_score/oe.py`, `--open-oe`) from World Bank WDI, Global Financial Development and Worldwide Governance Indicators. Rank correlation with BICRA 0.81; event AUC 0.90 / 0.93 against 0.90 / 0.92 with BICRA. The pipeline no longer needs a proprietary country score. |
| 56 | `tools/fetch_open_data.py` downloads the World Bank indicators and the IMF WEO October vintages (through DBnomics) into `data/open/`. |
| 57 | Macro expectations tested in the forecast (`--macro`): no improvement (error 0.73 against 0.72 notches), so not used by default. |
| 58 | EBA Transparency Exercise files 2019–2025 (`tr_oth.csv`, metadata) downloaded to `external_data/eba/` for the next step: CET1, leverage, NPE and P&L items for about 120 EU banks. Not yet mapped to the panel. 34 tests. |

## Added in v0.10

| # | Change |
|---|---|
| 59 | EBA banks matched to the panel (`data/eba_bank_map.csv`): 75 of 164, each row checked by hand. Automatic name matching had linked Bank of Ireland to KBC Bank Ireland and UniCredit to a former subsidiary. |
| 60 | `camels_score/eba.py` builds 22 registry ratios from the EBA files for 2018–2024 (`data/eba_ratio_map.csv`). Two reading errors fixed on the way: thousands separators in the 2019 file, and meaningless loan ratios for banks with almost no loans. |
| 61 | EBA against Capital IQ on 233 common bank-years: capital and earnings ratios near identical, asset quality rank correlation 0.84 to 0.91. Grades with EBA ratios: 96% within one notch (98% for 2019–2021). |
| 62 | `--eba-folder` extends the panel to 2022–2024 (161 bank-years, 56 banks). Liquid asset ratio carried from the bank's last report, book value growth neutral, country score and sovereign rating held at 2021. |
| 63 | Forecast: three more test years (error 0.36 notches for the ratio route against 0.54 for persistence) and `outlook_next_year.csv` with the 2025 forecast for 54 banks. Forecast range now always contains the point forecast. 37 tests. |

## Still open

1. EBA follow-up: download the 2015–2018 exercises (item codes differ), add the credit risk file for forborne and non-performing exposures, find a public source for LCR and NSFR (Pillar 3 data hub), and update the country score and sovereign ratings beyond 2021. Only 14 of the 36 registry ratios are scored today.
2. Open country score: put it on a wider country sample so the scale is not relative to 18 countries; add house prices.
3. Decide on the remaining proposals in METHODOLOGY.md section 11 (cap-only country anchor, absolute bands).
4. Confirm ownership and support levels in data/parents.csv and enter PARENT_GRADE for the 22 parents outside the panel (VTB, Sberbank, Raiffeisen, Erste, Deutsche Bank, Citi, Banca Popolare di Vicenza and others). Check the Danske Bank Hamburg branch record (assets 68% of the parent's).
5. Replace the countryeconomy.com sovereign series with Fitch's own history, and add S&P and Moody's from a primary source.
6. Phase 2: improve the downgrade signal with bank-level drivers from the EBA files (ROADMAP.md).
