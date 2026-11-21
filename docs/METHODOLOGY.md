# CAMELS Bank Soundness Scorecard: Methodology

Version 0.9 (November 2026). Author: Umut Yasar.
Status: working methodology, calibrated and back-tested on the 2023 UCD Capital IQ panel.
Not reviewed by a model validation function.

## 1. Purpose and scope

The scorecard gives a 1 to 10 soundness grade for a bank in a given financial year. It is
built for counterparty work in trade finance, FI limit setting and development finance,
where an analyst needs a consistent first view of many banks across different countries.

The grade is a relative soundness measure. It ranks banks by how likely they are to need
rescue or fail within the next two years. It is not a probability of default and not a
substitute for a credit rating. The current calibration covers commercial banks in 18 European
countries from 2010 to 2021.

## 2. Rating scale

| Grade | Descriptor | Distress events within 2 years, 2010–2021 back-test |
|---|---|---|
| 1–2 | Very strong | 0 in 883 bank-years |
| 3–4 | Strong | 0 in 2,198 bank-years |
| 5–6 | Adequate | 5 in 1,758 bank-years (0.3%) |
| 7–8 | Moderate | 7 in 1,691 bank-years (0.4%) |
| 9 | Weak | 6 in 467 bank-years (1.3%) |
| 10 | Very weak | 56 in 870 bank-years (6.4%) |

1 is the soundest grade and 10 the weakest, the same orientation as S&P's BICRA groups. The
descriptors follow S&P's assessment scale (very strong, strong, adequate, moderate, weak, very
weak). Grades 9 and 10 are kept apart because their event rates differ by a factor of five.
The output file carries the descriptor in `GRADE_DESCRIPTOR`. An event is
a failure, resolution, state aid, bail-in, default or distressed recapitalisation (Section 10).

Behind every grade is a continuous score (`FINAL_SCORE`, 1.00 to 10.00). The grade is its
rounding, and the label shows where the score sits inside the notch: `6+` is the better third
of grade 6, `6-` the weaker third. Adjustments of less than one notch, such as moderate parent
support, therefore stay visible even when the integer grade does not move.

## 3. Structure of a grade

A grade is built in six layers.

1. **Standalone profile.** Six CAMELS pillars scored from financial ratios. Asset quality and
   earnings ratios are scored through the cycle (Section 5, step 3).
2. **Operating environment anchor.** A 1 to 10 country score. It is blended into the grade
   and caps how far a bank can sit above its country.
3. **Own adjustments.** A notch-down for loss-making banks.
4. **Group support.** Uplift from a stronger parent as a support probability of at most 0.5,
   reduced for large subsidiaries, withdrawn when the parent is under stress, and never beyond
   the country cap or the sovereign rating (Section 8).
5. **Qualitative overlay.** Up to 2 notches for documented business model, concentration,
   governance or growth concerns (Section 7).
6. **Analyst override** above 2 notches, with a second reviewer (Section 7).

## 4. Pillars, ratios and weights

| Pillar | Weight | Ratios scored now | Ratios to add (Section 12) |
|---|---|---|---|
| C Capital adequacy | 20% | Total capital ratio, Tier 1 ratio, Total debt / equity | CET1, leverage ratio, tangible equity / tangible assets, RWA density |
| A Asset quality | 30% | Problem loans ratio, Texas ratio, Loan loss reserves / problem loans | Cost of risk, Stage 2 share, forborne loans, loan growth |
| M Management and efficiency | 5% | Cost-to-income, Operating return on assets | Non-interest income share |
| E Earnings | 25% | ROAA, ROAE, NIM, Book value per share growth, ROAA volatility (3 years) | Pre-provision profit / RWA |
| L Liquidity and funding | 15% | Liquid assets / deposits and borrowings | LCR (once coverage allows), NSFR, loans / deposits, deposits / funding, encumbrance |
| S Sensitivity to market risk | 5% | None in current data | EVE and NII sensitivity, FX loans share, net open FX position, securities share, unrealised securities losses / CET1 |

If a pillar has no data, its weight is shared out across the other pillars in proportion to their
weights. With the current data the effective weights are C 21%, A 32%, M 5%, E 26% and L 16%.

The weights were changed in v0.7 from C 20%, A 25%, M 10%, E 15%, L 20%, S 10%. The new set
gives more weight to asset quality and earnings, where the agencies' core metrics also sit, and
less to management (one efficiency ratio) and liquidity (one ratio). The effect is reported in
Section 10. The weights were chosen with the back-test results in view, so the 2018–2021 figures
are no longer a clean out-of-time test for them.

Correlated ratios (Tier 1 and total capital, ROAA and ROAE) sit in the same pillar and share
one weight, so they are not double counted. This replaces the PCA step of the 2023 version and
keeps every grade traceable to named ratios.

The 2023 non-operating expense ratio is kept for comparison only. Its formula divides by
operating income minus a loan loss reserve stock, and it ranges from -580,600% to 257,720% in
the data.

## 5. Scoring steps

1. **Clean.** `NM` and text become missing values. A value outside a ratio's plausible range
   (for example a capital ratio above 100%) is removed. Each ratio is then winsorised at the
   1st and 99th percentile within each year.
2. **Minimum data.** A bank-year needs at least 5 reported ratios.
3. **Through the cycle.** For problem loans, Texas ratio, reserve coverage, cost of risk,
   Stage 2 share, ROAA, ROAE, NIM, operating return on assets, cost-to-income and
   pre-provision profit, the value scored is the weaker of the latest year and the average of
   the last 3 years (at least 2 reported years). This follows Moody's bank scorecard. A single
   good year does not lift a bank with a weak record, and a deterioration still counts in
   full. Outcome labels are always built from the latest reported values.
4. **Penalised imputation.** A missing ratio is filled with the weak-side quartile of the
   bank's country-year peers: the 25th percentile where higher is better, the 75th where
   lower is better. Year and panel values are the fallback. A bank-year with more than 40% of
   its ratios missing is flagged as low data quality.
5. **Oriented robust z-score.** For each ratio,
   z = direction × (value − median) / (1.4826 × MAD). Median and MAD (median absolute deviation)
   come from reported values in the calibration window, not from imputed ones, on the basis of
   step 3. z is limited to
   the range −3 to +3, so a positive z always means sounder than the typical bank.
6. **Capital ceiling.** A capital ratio cannot contribute more than z = +1. Very high capital
   in small niche banks was hiding losses in the 2023 version and in the first runs of this one.
7. **Pillar and composite.** A pillar score is the average z of its ratios. The composite is
   the weighted average of the pillar scores.
8. **Standalone score.** The composite is mapped to a continuous 1 to 10 score:
   10.5 − 10 × (share of calibration composites below it), interpolated between the decile
   cut-offs of the calibration window and frozen, so a score means the same in every year.
9. **Operating environment.** Own score = 85% × standalone + 15% × country score, and not more
   than 2 notches better than the country score. This cap applies to every bank, including
   supported subsidiaries.
10. **Loss notch.** One notch worse if ROAA is below 0, two notches if it is below −1%. ROAA
    here is the through-the-cycle value from step 3.
11. **Group support** (Section 8).
12. **Qualitative overlay** (Section 7), then the final grade is the rounded score, with a + or −
    modifier, never beyond 10.

## 6. Reference bands

These bands show what each z-score level means in ratio terms on the 2010–2017 calibration
sample, in percent unless the ratio is a multiple. They help an analyst read a pillar score and
are a starting point for absolute bands in a later version. The scale is symmetric, so for
skewed ratios one side can fall below the natural floor. Those cells show the floor.

| Pillar | Ratio | Better when | Basis | Strong (z = +1) | Typical (median) | Weak (z = -1) | Very weak (z = -2) |
|:--|:--|:--|:--|--:|--:|--:|--:|
| C | Total Capital Ratio | Higher | latest | 21.68 | 16.71 | 11.74 | 6.77 |
| C | Tier1 Ratio | Higher | latest | 19.97 | 14.76 | 9.55 | 4.34 |
| C | Total Debt/ Total Equity | Lower | latest | 0 (floor) | 0.48 | 1.19 | 1.90 |
| A | Problem Loans Ratio | Lower | weaker of latest and 3-year average | 0 (floor) | 6.28 | 13.00 | 19.72 |
| A | Texas Ratio | Lower | weaker of latest and 3-year average | 0 (floor) | 31.91 | 65.01 | 98.11 |
| A | Loan Loss Reserve To Problem Loans | Higher | weaker of latest and 3-year average | 77.93 | 53.13 | 28.33 | 3.53 |
| M | Cost To Income Ratio | Lower | weaker of latest and 3-year average | 50.50 | 67.88 | 85.25 | 102.63 |
| M | Operating Return On Assets | Higher | weaker of latest and 3-year average | 4.86 | 3.09 | 1.32 | -0.45 |
| E | ROAA | Higher | weaker of latest and 3-year average | 0.82 | 0.28 | -0.25 | -0.79 |
| E | ROAE | Higher | weaker of latest and 3-year average | 9.02 | 3.29 | -2.44 | -8.18 |
| E | Net Interest Margin | Higher | weaker of latest and 3-year average | 3.01 | 1.89 | 0.77 | -0.35 |
| E | Bookvalue Per Share Growth | Higher | latest | 10.46 | 2.62 | -5.22 | -13.05 |
| E | ROAA Volatility 3Y | Lower | latest | 0 (floor) | 0.22 | 0.47 | 0.72 |
| L | Liquid Assets/ Total Deposits & Borrowings | Higher | latest | 56.97 | 35.68 | 14.40 | 0 (floor) |

## 7. Qualitative overlay and overrides

All three agencies score factors that ratios miss: S&P's business position and risk position,
Fitch's business profile and risk profile, Moody's qualitative adjustments. The scorecard keeps
this judgement in a separate, bounded and logged layer rather than mixing it into the ratios.

**Overlay.** Recorded in `data/overlays.csv` (`ID, FROM_YEAR, TO_YEAR, FACTOR, NOTCHES, REASON,
ANALYST, DATE`). Positive notches mean weaker. The total per bank-year is capped at ±2 notches.

| Factor | What it covers |
|---|---|
| `business_model` | Franchise, diversification, dependence on one product, client or market |
| `concentration` | Single-name, sector or related-party concentration in assets or funding (the Greensill Bank case) |
| `governance` | Ownership, transparency, audit, regulatory findings, accounting quality |
| `growth` | Loan or balance-sheet growth well above peers, new risky business lines |
| `other` | Any other documented factor, with a second reviewer |

Every overlay needs a reason, an analyst and the date it was decided. An overlay only counts
for a year if it was decided by the end of the following year, when that year's accounts would
have been reviewed. The back-test is run on the score **without** overlays, so judgement made
with hindsight cannot flatter the validation. The file is empty in this version.

**Override.** A move of more than 2 notches, or any move for reasons outside the overlay
factors (a change of ownership not yet in `data/parents.csv`, sanctions affecting liquidity, a
resolution or capital plan already announced, consolidation effects such as the Permanent TSB
case in the 2023 report), needs a second reviewer. Overrides are logged in the same way and
reviewed against outcomes once a year.

## 8. Group support

A bank owned by a foreign group does not stand alone: a stronger parent can be expected to
support it in stress through capital, liquidity or funding. The scorecard treats this support
as a **probability**, and keeps the **country score as a ceiling** that support cannot breach.

### Principles

1. **Support only.** A parent can improve a subsidiary's grade, never worsen it. When the
   parent is itself under stress, support is withdrawn and the subsidiary keeps its own score.
2. **Support is a probability, at most 0.5.** Even full ownership does not make support
   certain, so a subsidiary closes at most half of the gap to its parent. The agencies can
   equalise a core subsidiary with its parent. The 0.5 ceiling is a deliberate, more
   conservative choice for a tool used in counterparty limits, where overstating support is
   the costlier error.
3. **The country score is a cap.** No bank, supported or not, may sit more than 2 notches above
   its country score. A subsidiary in a weak country therefore never reaches the grade of a
   strong parent.
4. **Support cannot lift a bank above its sovereign.** Where a sovereign rating is entered,
   support stops at the sovereign's grade equivalent, in line with Moody's sovereign
   constraint and Fitch's Country Ceiling. Transfer and convertibility risk sits with the
   country, not the parent.
5. **Ability matters as well as willingness.** A large subsidiary is harder for a parent to
   carry. Support probability is cut to 75% of its level when the subsidiary's total assets are
   10–20% of the parent's, and to 50% above 20% (Fitch's relative size factor).

### Inputs

`data/parents.csv`, one row per subsidiary and period: `PARENT_ID` (the parent's ID in the
panel) or `PARENT_GRADE` (an external 1 to 10 equivalent), `SUPPORT_LEVEL`, `FROM_YEAR`,
`TO_YEAR`, and optionally `STRESS_FROM` and `STRESS_REASON` for the first year in which the
parent is under stress. An entered `PARENT_GRADE` takes precedence over the panel score.

`data/sovereign_ratings.csv`: Fitch long-term foreign-currency issuer default rating at 31
December for the 18 countries, 2010–2021, with source and status per row (Appendix: SOURCES.md).
It is converted to a grade with the same map as parent ratings.

| Support level | Typical evidence | Support probability |
|---|---|---|
| Core | Branch, or fully owned with the group brand and strategy | 0.50 |
| Strategic | Majority owned, group brand, part of the long-term strategy | 0.35 |
| Moderate | Minority or non-core stake, could be sold | 0.15 |
| None | Not assessed or no expected support | 0 |

### Rule

With *own* the subsidiary's score after the country anchor and loss notch, *parent* the
parent's own score in the same year (lower is stronger), *p* the support probability and
*cap* = country score − 2:

- p = level probability × ability factor, and 0 in parent stress years
- supported = own − p × (own − parent), only when the parent is stronger
- final = max(supported, cap, sovereign grade), and never worse than own

`SUPPORT_PROB`, `SUPPORT_ABILITY`, `ASSETS_SHARE_OF_PARENT`, `PARENT_STRESS` and `GROUP_ADJ`
record what was used and the effect (negative means support). `WEAK_PARENT` flags a parent that
scores at least one notch weaker than the subsidiary. The flag has no effect on the grade; it
tells the analyst to check whether the parent could become a source of stress. Because the rule works on the continuous score, support of less than one notch
shows as a label change (for example `6` to `6+`) even when the integer grade does not move.

For parents outside the panel, enter `PARENT_GRADE` from the parent's issuer rating using this
indicative map (`group.rating_to_grade`). It is a convenience, not a calibrated equivalence.

| Rating | AAA to AA- | A+, A | A- | BBB+, BBB | BBB- | BB+, BB | BB- | B+, B | B- | CCC+ and below |
|---|---|---|---|---|---|---|---|---|---|---|
| Grade | 1 | 2 | 3 | 4 | 5 | 6 | 7 | 8 | 9 | 10 |

### Current mapping and effect

The mapping has 70 subsidiaries found by brand name (for example Santander Bank Polska, HSBC
Bank A.S., ING Bank Ukraine, Eurobank Cyprus, Piraeus Bank ICB, Akbank AG, Ziraat Bank
International, Banca Apulia). The parent is in the panel for 48 of them. The other 22 (VTB and
Sberbank subsidiaries, Raiffeisen, Erste, Deutsche Bank, Citi, Banca Popolare di Vicenza and
others) need a `PARENT_GRADE`. All support levels are assumed `strategic` (one Danske Bank
branch is `core`) and are marked for review.

Parent stress years entered so far, each with a public source (SOURCES.md):

| Parent | Stress from | Reason |
|---|---|---|
| VTB Bank, Sberbank (5 subsidiaries) | 2014 | EU sectoral sanctions, Council Regulation 833/2014 of 31 July 2014 |
| Greek parents of Cypriot subsidiaries (4) | 2013 | Parents recapitalised by the Hellenic Financial Stability Fund (events file) |
| Veneto Banca, Banca Popolare di Vicenza | 2016 | Capital increases taken up by the Atlante fund in 2016 |

Of 505 subsidiary bank-years with a parent score, 150 receive support, on average 0.88
notches (at most 2.44). The integer grade moves in 93 of them. The ability factor reduces
support in 98 bank-years (for example Santander UK and UniCredit Bank AG, each above 20% of the
parent's assets), the stress rule removes it in 67, and the sovereign grade binds in 12.

| Bank, year | Country score | Sovereign grade | Own score | Parent score | Final | Reading |
|---|---|---|---|---|---|---|
| HSBC Bank A.S., 2015 | 6 | 5 (BBB-) | 8.77 | 2.97 | 6.74 (7+) | 35% of the gap to HSBC closed |
| HSBC Bank A.S., 2019 | 9 | 7 (BB-) | 7.00 | 2.73 | 7.00 (7) | Already at the country cap (9 − 2) |
| OTP Bank (Ukraine), 2015 | 10 | 10 (CCC) | 10.00 | 6.00 | 10.00 (10) | Sovereign in distress, support cannot help (8.60 in v0.5) |
| Standard Chartered Yatirim Bankasi Türk, 2012 | 5 | 5 (BBB-) | 5.99 | 2.06 | 5.00 (5) | Support stops at the sovereign grade |
| Sberbank Magyarország, 2014 | 8 | 6 (BB+) | 10.00 | n/a | 10.00 (10) | Parent under sanctions, no support |
| Akbank AG (Germany), 2019 | 2 | 1 (AAA) | 1.86 | 7.00 | 1.86 (2) | Parent weaker, no effect, `WEAK_PARENT` set |

The event AUC barely moves with group support, because few events fall on subsidiaries in the
current list. The adjustment rests on credit judgement, not on back-test evidence, and should be
reviewed once the 22 missing parent grades are entered. The Danske Bank Hamburg branch shows
total assets of 68% of the parent's, which points to group figures in the branch record; it is
on the review list.

## 9. Operating environment score

The first back-tests used S&P BICRA groups. BICRA is proprietary, so the scorecard now has its
own country score on the same 1 to 10 scale, built from public data (`camels_score/oe.py`,
`--open-oe`). A run on it needs no restricted country input.

| Component | Weight | Indicators | Source |
|---|---|---|---|
| Economic resilience | 30% | GDP per capita (PPP), volatility of growth over 5 years, inflation away from 2% | World Bank WDI |
| Credit and asset risk | 30% | Private credit / GDP against its 5-year average, banking sector NPL ratio | World Bank WDI, Global Financial Development |
| Funding and profitability | 20% | Sector credit / deposits, sector return on assets | Global Financial Development |
| Institutions | 20% | Rule of law, regulatory quality | Worldwide Governance Indicators |

Each indicator is turned into an oriented robust z-score against the country-years of
2010–2017, the components are averaged with these weights, and a trailing 3-year average of the
composite is mapped to 1 to 10 through the 2010–2017 decile cut-offs. This is the same
construction as the bank scorecard. The data are downloaded by `tools/fetch_open_data.py`
and stored in `data/open/`.

Two tests were set before building it, and both are met:

| Test | Result |
|---|---|
| Rank correlation with BICRA above 0.8, 2010–2021 | 0.81 (0.77 without the 3-year average, 0.85 with 5 years) |
| Event ranking not weaker than with BICRA | Event AUC 0.90 all years and 0.93 for 2018–2021, against 0.90 and 0.92 |

Limits. The score is relative to the 18 countries of the panel, not a global scale: the best of
them receive 1, which is more generous than BICRA (Hungary and Spain score 1 in 2019, BICRA 6
and 4). It agrees with BICRA within one notch for 63% of country-years and within two for 87%.
It moves faster than BICRA in recoveries and in 2020. House prices and sector funding from
abroad are not in it yet. The grade figures in Sections 2, 8 and 10 come from the BICRA-based
run; the open-score run is in `results/open_oe/` and differs little.

The anchor weight is a judgement call. In the back-test a weight of 0 (cap only) gave the
best event ranking. With only 10 events after 2017 that is weak evidence, so the weight is
15% for now.

## 10. Validation

### Outcome data

The event file (`data/events.csv`) has 48 events at 43 banks: failures, resolutions, state
aid, bail-ins, a sovereign-linked default and distressed recapitalisations. Each row shows its
type and status. All 48 are verified against official or primary sources: national central
banks, resolution funds, supervisors, the ECB, the ESM, Eurostat and European Commission
decisions (SOURCES.md). The check reclassified one event: Eurobank's 2015 recapitalisation was
covered by private investors and a liability management exercise, so it is a distressed
recapitalisation rather than state aid. It still counts as an event. Four events cannot be
used because the bank has no data before the event year.

A grade at year t is compared with events in years t+1 and t+2. The scorecard never uses the
events. The calibration only uses the ratio distribution up to 2017, so 2018–2021 is an
out-of-time test.

### Results

| Measure | 2023 model | v0.5 | v0.6 | v0.7 (new weights) |
|---|---|---|---|---|
| AUC, events, all years | 0.71 | 0.91 | 0.91 | 0.90 |
| AUC, events, 2018–2021 | 0.78 | 0.92 | 0.92 | 0.92 |
| AUC, next-year loss or capital breach (proxy), all years | 0.60 | 0.77 | 0.77 | 0.79 |
| AUC, proxy, 2018–2021 | 0.55 | 0.70 | 0.73 | 0.77 |
| Rank correlation, grade vs event rate | not monotonic | 0.94 | 0.96 | 0.96 |
| PSI of the composite, 2010–2017 vs 2018–2021 | | 0.21 | 0.15 | 0.20 |
| Share of bank-years in grade 10 | | 8.4% | 10.5% | 11.1% |

Reading of the v0.7 weights: the gain is on the proxy, which after 2017 is almost entirely
"loss next year" and so rewards a higher earnings weight. Event ranking is unchanged after 2017
and slightly lower over all years. The composite also moves more between periods (PSI 0.20),
because earnings changed more than capital after the crisis. Seven event bank-years now sit in
grades 5 to 7: Dexia SA (2010), Tønder Bank (2010–2011), Co-operative Bank (2011),
International Bank of Azerbaijan (2013–2014) and Greensill Bank (2019).

The through-the-cycle rule is the main source of the v0.6 change: run without it
(`--no-multi-year`), the same data give the v0.5 figures (proxy AUC 2018–2021 0.70, rank
correlation 0.93, PSI 0.21). It leaves the event ranking unchanged and makes the score more
stable over time. The cost is a more crowded bottom grade (10.5% of bank-years in grade 10,
from 8.4%), because three-year earnings also feed the loss notch.

Challengers trained on 2010–2017 and tested on 2018–2021 for the proxy label: a logit on the
same pillar scores reached 0.84, gradient boosting on raw ratios 0.90. The gap shows that the
expert weights leave some predictive power unused on the proxy. The proxy, however, is mostly
"loss next year", which earnings persistence explains. Weights should not be tuned to it.

Examples from the back-test: in the years before their rescue, the 2023 model gave its
second-best score (2) to Bankia, Bank of Cyprus, Eurobank, Monte dei Paschi, NordLB,
Co-operative Bank and Liberbank. v0.6 grades all of them 8 to 10, most of them 10. Greensill Bank is
graded 5- for 2019 (7- for 2018) and is the main known miss: its weakness was concentration and
governance, which belongs in the qualitative overlay, not in the ratios.

### Limitations

- Few events, especially after 2017. AUC figures for 2018–2021 rest on 10 event bank-years.
- Population shift: the composite PSI between 2010–2017 and 2018–2021 is 0.20 (0.15 with the
  v0.6 weights), a moderate shift as banks strengthened after the crisis. Grades stay
  comparable because the yardstick is frozen, but the calibration window needs review.
- No sensitivity-to-market-risk ratios yet, and liquidity rests on one ratio.
- Grade 10 holds 11.1% of bank-years, because the loss notch, now on three-year earnings,
  pushes loss-making banks to the bottom of the scale.
- Parent support levels are assumed from brand names and not yet confirmed; 22 parents have no
  grade yet. Sovereign ratings use one agency (Fitch) at year end.
- Consolidation level (group or bank-only accounts) is not controlled.

## 11. Proposed changes for review

These are not yet adopted, because the evidence comes partly from the same data used to
test them.

| Proposal | Effect in back-test | Concern |
|---|---|---|
| Country score as cap only (0% blend) | Better event AUC | Only 10 recent events |
| Absolute bands instead of decile cut-offs | Grades no longer depend on the sample mix | Needs expert agreement per ratio |

Decided in November 2026: the 2-notch country cap and the loss notch on three-year earnings are
kept; the weights in Section 4 were adopted in v0.7.

## 12. Data request

The 2023 export gives 14 usable ratios. The registry (`camels_score/ratios.py`) holds 36.
Capital IQ is no longer available to the author, so the next data come from public sources.
In order of value:

1. **Capital.** CET1 ratio, leverage ratio, tangible common equity / tangible assets, RWA / total assets.
2. **Asset quality.** Loan loss provisions / average loans (cost of risk), Stage 2 loans (from
   2018), forborne loans, gross loan growth.
3. **Liquidity and funding.** Net loans / customer deposits, customer deposits / total funding,
   NSFR, asset encumbrance.
4. **Sensitivity.** FX loans / total loans, net open FX position / capital, securities / total
   assets, unrealised losses on amortised-cost securities, IRRBB EVE and NII sensitivity
   (Pillar 3, from 2018 for most EU banks).
5. **Earnings.** Pre-provision operating profit / RWA, net fee income / operating income.
6. **Ownership.** Ultimate parent, ownership share and parent issuer rating for every bank,
   to replace the name-matched parent mapping.

Any of these can be added without code changes: put them in a tidy file with `ID`, `YEAR` and
the registry ratio names (for example `CET1 RATIO`, `LOANS TO DEPOSITS`, `NSFR`) and pass it with
`--extra-ratios`. A ratio enters the score once it covers at least 30% of bank-years.

**Public sources, bulk files first.**

| Source | Coverage | Gives | Note |
|---|---|---|---|
| EBA EU-wide Transparency Exercise | About 120 large EU and EEA banks, highest level of consolidation, 2015–2025 | CET1, leverage, RWA, NPL and coverage, sovereign exposures, P&L items | Discontinued after the 2025 exercise |
| EBA Pillar 3 Data Hub | EU banks, from 2025–2026 | Pillar 3 templates, including LCR, NSFR and IRRBB | Successor to the Transparency Exercise |
| National Bank of Ukraine supervisory data | Every Ukrainian bank, monthly | Balance sheet and income items by bank | |
| Banks Association of Türkiye statistical reports | Every Turkish bank, annual | Bank-level financial statements and selected ratios | To be checked |
| Bank annual reports and Pillar 3 reports | Any bank | Everything above | Manual; for small banks and the non-EU countries only |

For the large EU banks, which carry most of the distress events, the EBA files replace
downloading reports one by one. Annual reports are needed only for small banks, and a
fill-in template (raw items in, ratios out) would make that a 15-minute task per bank-year.

## 13. Governance

- Recalibrate once a year. Track the PSI of the composite against the calibration window, and
  review the window when it exceeds 0.25.
- Refresh the event file every six months and re-run validation (`run_pipeline.py`).
- Keep every calibration file (`calibration.json`) with its version, so past grades can be
  reproduced.
- S&P Capital IQ exports and S&P BICRA: the figures come from public bank reports, but the exports and BICRA fall under S&P's terms of use. They, and bank-level outputs built from them, stay outside the public repository.
- Every external input file (events, parents, sovereign ratings, overlays) carries a source and
  status per row. The full list of sources is in SOURCES.md.

## 14. Scoring a new bank

A bank that is not in the panel can be graded from up to three years of its own ratios, on the
same frozen yardstick: `score_new_bank.py` on the command line (input: `templates/new_bank_template.csv`)
or the browser tool built by `tool/build_tool.py`. Both run the same steps as the panel: bounds,
winsorising, the through-the-cycle rule, z-scores, pillars, weights, the country anchor and cap,
the loss notch, group support and the overlay.

Two steps need peer banks, which a single bank does not have. They use values stored in
`calibration.json` at calibration time instead:

| Step | Panel | New bank |
|---|---|---|
| Winsorising | 1st and 99th percentile of each year | 1st and 99th percentile of the 2010–2017 calibration window |
| Missing ratio | Weak-side quartile of country-year peers | Weak-side quartile of the calibration window |

The ratios can also be calculated from annual-report figures: `score_new_bank.py --raw` reads
18 balance sheet, income statement and capital items per year
(`templates/raw_items_template.csv`, any currency) and builds the 13 ratios with the
definitions of the panel. ROAA, ROAE and NIM use average balances when the previous year is
given.

ROAA volatility is calculated from three consecutive years of ROAA; with fewer years it is
treated as missing. The country score is entered by the analyst on the 1 to 10 scale (BICRA, if
available, or the analyst's own view of the banking system), and the sovereign and parent
ratings are chosen from the rating scale.

Check against the panel: for the 2,474 bank-years from 2012 with all ratios reported in three
consecutive years, the new-bank route gives the same score as the pipeline in the median case and
the same integer grade in 99.3% of them (99.9% within one notch). The differences come from
winsorising at extreme values. The browser tool and the Python route agree on all 946 bank-years
of a random test set (`tests/test_newbank.py` repeats this check).

## Version log

| Version | Change |
|---|---|
| 2023 | UCD project: K-Means + PCA clusters, 7 scores |
| 0.2 | Direction-aware scorecard, frozen calibration, outcome-based validation |
| 0.3 | Raw Capital IQ loader, cost-to-income, ROAA volatility, unimputed labels and medians, country blend 15% |
| 0.4 | Verified event file (48 events), capital ceiling, loss notch, methodology document |
| 0.5 | Continuous score with +/- modifiers, group support as a probability (max 0.5) under the country cap, parent mapping for 68 subsidiaries |
| 0.6 | Agency comparison applied: through-the-cycle ratios, sovereign cap on support, ability factor, parent stress years, weak-parent flag, bounded qualitative overlay, loader for extra ratios, sources appendix |
| 0.7 | Pillar weights C 20%, A 30%, M 5%, E 25%, L 15%, S 5%; S&P-style grade descriptors; new-bank scoring (command line and browser tool) |
| 0.8 | All 48 events verified against official sources; phase 2 forecast, first version (ROADMAP.md) |
| 0.9 | Open operating-environment score from World Bank data; new-bank grading from annual-report figures; macro expectations tested in the forecast |
