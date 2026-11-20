# camels-score v0.5 compared with S&P, Moody's and Fitch bank methodologies

Purpose: check the scorecard design against the three agencies before fixing the methodology.
Based on the agencies' public criteria summaries, rating reports and rating actions (sources at
the end). Agency criteria change over time; Moody's and Fitch both updated their bank methodologies
in 2025–2026, so details should be re-checked against the full criteria documents before external use.

## 1. Overall structure

| | S&P | Moody's | Fitch | camels-score v0.5 |
|---|---|---|---|---|
| Starting point | Anchor from BICRA economic and industry risk | Macro Profile of the country | Operating environment score | Standalone CAMELS composite |
| Country role | The anchor itself: bank factors notch up or down from it | Weights and adjusts the financial profile; BCA typically not above the sovereign | Strong influence on the Viability Rating; can be capped by the sovereign | 15% blend and a cap of 2 notches above the country score |
| Bank-specific factors | Business position, capital and earnings, risk position, funding and liquidity | Solvency (asset risk, capital, profitability) and liquidity (funding structure, liquid resources), plus qualitative adjustments | Business profile, risk profile, financial profile (asset quality, earnings, capital, funding and liquidity) | Six CAMELS pillars, 14 ratios now |
| Standalone result | SACP | BCA | Viability Rating | STANDALONE_SCORE |
| Support | Group and government support | Affiliate support (Adjusted BCA), government support | Shareholder Support Rating, Government Support Rating | Parent support only |
| Loss severity / resolution | ALAC uplift | Advanced Loss Given Failure | Resolution buffer uplift | Not covered |

**Reading.** The three-layer logic is the same in all four: country, then bank, then
support. The main structural difference is the weight of the country. For S&P the
country is the starting point and every bank is notched from it; for Moody's and Fitch it
shapes and limits the standalone view. In camels-score the country is a light blend plus a cap.
The back-test preferred a light blend, but on only 10 post-2017 events.

## 2. Financial ratios

| Factor | S&P | Moody's core ratio | Fitch core metric | camels-score |
|---|---|---|---|---|
| Asset quality | Risk position (qualitative and quantitative) | Problem loans / gross loans | Impaired (Stage 3) loans / gross loans | Problem loans ratio, Texas ratio, reserve coverage |
| Capital | Risk-adjusted capital (RAC) ratio, S&P's own risk weights | Tangible common equity / RWA (leverage recalibrated 2025) | CET1 ratio | Total capital, Tier 1, debt / equity |
| Earnings | Part of capital and earnings | Net income / tangible assets | Operating profit / RWA | ROAA, ROAE, NIM, BVPS growth, ROAA volatility |
| Funding | Funding assessment | Market funds / tangible banking assets | Loans / customer deposits | Not scored |
| Liquidity | Liquidity assessment | Liquid banking assets / tangible banking assets | Complementary liquidity ratios alongside the funding metric | Liquid assets / deposits and borrowings |
| Through-the-cycle | Forward-looking RAC | Weaker of the 3-year average and the latest value | Four-year averages of core metrics | Single year only |

**Reading.**
- The agencies use one core metric per factor and then adjust it with judgement. camels-score
  averages several correlated ratios per pillar. That is stable, but weaker at isolating the
  one number that matters.
- All three use capital measures closer to loss absorption (RAC, TCE, CET1) than the total
  capital ratio.
- All three smooth over several years. camels-score reacts to a single year, which is one reason
  the loss notch was needed.
- Funding is a full factor at every agency. In camels-score it has no ratio yet.

## 3. Qualitative factors

All three agencies score business model and franchise (S&P business position, Fitch business
profile, Moody's qualitative adjustments for business diversification, opacity and complexity,
corporate behaviour). Risk appetite, concentration, growth and governance are also scored (S&P
risk position, Fitch risk profile). camels-score has no qualitative factor apart from analyst
override. The main known miss of the back-test, Greensill Bank (grade 4 before its 2021
failure), is the kind of case these factors are meant to catch: concentration and opacity
rather than weak ratios.

## 4. Country cap

| | Practice | camels-score |
|---|---|---|
| S&P | Separate criteria section for rating banks above the sovereign | Cap of 2 notches above the BICRA-based country score |
| Moody's | BCA typically not above the sovereign rating; long-term ratings not more than two notches above the sovereign (Italian banks example) | Same shape (2 notches), but anchored to the country score, not the sovereign rating |
| Fitch | Sovereign rating can cap the operating environment score; support-driven ratings of foreign-owned banks constrained by the Country Ceiling (Turkish foreign-owned banks); support for BNL capped at one notch above Italy's sovereign | The cap also binds supported subsidiaries |

**Reading.** The rule that the country is a ceiling, including for supported subsidiaries, is
consistent with Moody's and Fitch practice. The difference is the reference point. The agencies
cap against the sovereign rating or country ceiling (transfer and convertibility risk), while
camels-score caps against a banking-system score (BICRA). The two can differ: a country can have a
weak banking system but a better sovereign rating, or the reverse.

## 5. Parent support

| | S&P | Moody's | Fitch | camels-score v0.5 |
|---|---|---|---|---|
| Classification | Core, highly strategic, strategically important, moderately strategic, nonstrategic. Based on ownership, brand, strategy, track record, integration | Probability of affiliate support (low, moderate, high, very high) | Parent's propensity (role in group, brand, potential for disposal) and ability (relative size, regulation, country risks) | Core, strategic, moderate, none; assumed from brand names |
| Size of uplift | Core (and often highly strategic) subsidiaries rated at or near the group credit profile; lower categories receive fewer notches above their SACP | Examples: 1 notch for moderate or high probability, 2–3 notches for very high; no uplift if the parent's BCA is not higher | Equalised with the parent for very high probability; fewer notches when ability is constrained (for example HVB two notches below UniCredit because of its size) | Support probability × gap, at most 0.5 of the gap |
| Ceiling from parent | Generally not above the group credit profile unless insulated | Usually capped at the parent's level | Capped by the parent's rating and the country ceiling | Never better than the parent, and never above the country cap |
| Weaker parent | Can cap the subsidiary; insulation allows 1 to 3 notches above the group | No uplift; standalone BCA not lowered mechanically | Considered through ability and propensity | No effect (left to override) |
| Parent's ability | Group credit profile | Parent BCA as anchor | Relative size, regulation, country risk explicitly scored | Not considered |

**Reading.**
- **Support as a probability.** This matches Moody's and Fitch, which both state support as a
  likelihood.
- **Maximum of 0.5 of the gap.** This is more conservative than all three. They allow full
  alignment with the parent for core or very-high-probability subsidiaries (S&P core status,
  Fitch equalisation, Moody's very high support). For a counterparty limit tool, conservatism is
  defensible, but grades of well-supported subsidiaries in strong countries will sit below the
  agencies' views.
- **No effect from a weaker parent.** This matches Moody's (no uplift, BCA not reduced) but
  differs from S&P, which can cap a subsidiary at a weaker group's level unless it is insulated.
  The VTB Bank Ukraine and Sberbank cases show the risk; under v0.5 they rely on analyst override.
- **No ability factor.** Fitch explicitly reduces support when the subsidiary is large relative to
  the parent. camels-score ignores relative size.

## 6. What camels-score does that the agencies do not publish

- A fixed, reproducible formula with a frozen calibration and a back-test against 48 distress
  events.
- A continuous score with +/- modifiers, so changes below one notch stay visible.
- Results for banks the agencies do not rate (small regional banks, Ukrainian, Azerbaijani and
  Georgian banks in the panel).

## 7. Recommended changes before fixing the methodology

Ordered by expected benefit relative to effort. All seven were taken up in v0.6; the last column
says how (details in METHODOLOGY.md and FIXES.md items 40–47).

| # | Change | Agency basis | Effort | v0.6 |
|---|---|---|---|---|
| 1 | Use the weaker of the 3-year average and the latest value for asset quality and earnings ratios | Moody's scorecard; Fitch four-year averages | Low, data already in the panel | Done. Proxy AUC 2018+ 0.70 to 0.73, PSI 0.21 to 0.15 |
| 2 | Add a sovereign rating (or country ceiling) input and cap supported ratings against it, alongside the banking-system score | Moody's and Fitch sovereign and country-ceiling constraints | Low, needs a sovereign rating history | Done with Fitch FC year-end ratings, 18 countries, 2010–2021; binds in 15 bank-years |
| 3 | Add an ability factor to support: lower the probability when the subsidiary's assets exceed a set share of the parent's (for example 10%) | Fitch relative size | Low, total assets in the panel | Done: factor 0.75 at 10–20% of parent assets, 0.50 above 20%; 98 bank-years |
| 4 | Add a bounded qualitative overlay (±2 notches) with defined criteria: business model and concentration, governance and transparency, growth | S&P business and risk position; Fitch business and risk profile; Moody's qualitative adjustments | Medium, analyst inputs | Mechanism done (`data/overlays.csv`, ±2, point in time, excluded from back-test); no overlays entered yet |
| 5 | Add one core metric each for funding and for loss-absorbing capital (loans / deposits, CET1 or tangible equity / RWA) | All three | Medium, new data download | Loader done (`--extra-ratios`); waits for the data download |
| 6 | Decide whether a weaker parent should cap a subsidiary, at least as a flag (sanctions, parent failure) | S&P negative group influence | Low | Done within the support-only rule: support withdrawn in parent stress years (sanctions, rescue), `WEAK_PARENT` flag; no downward pull |
| 7 | Keep the 0.5 support ceiling but document it as a deliberate conservative choice against agency practice | Section 5 | None | Documented in METHODOLOGY.md section 8 |

Out of scope by design: government support and loss-given-failure uplifts. Both are about
instrument recovery and bail-in, not about the bank's standalone soundness that a
counterparty limit depends on.

## Sources

S&P Global Ratings, "How We Rate Financial Institutions" (Dec 2024) and Financial Institutions
Rating Methodology (Dec 2021):
https://spglobal.com/ratings/en/research/articles/241213-how-we-rate-financial-institutions-13327814
https://spglobal.com/ratings/en/research/articles/211209-criteria-financial-institutions-general-financial-institutions-rating-methodology-12135180
S&P, "Credit FAQ: A Closer Look At Insulated Entities In Financial Services" (Jul 2023):
https://www.spglobal.com/ratings/en/research/articles/230718-credit-faq-a-closer-look-at-insulated-entities-in-financial-services-12787070
Moody's, Banks methodology and scorecard ratios (credit opinion example):
https://brb.uz/assets/credit_opinion_business_development_bank_06jul2026_pbc_1488515.pdf
Moody's rating actions on Italian banks (sovereign constraint):
https://www.mediobanca.com/static/upload_new/rat/rating_action-moodys-ratings-takes-rating-25nov2025-pr_516174.pdf
Moody's affiliate support examples: https://finance.yahoo.com/news/banco-bilbao-vizcaya-argentaria-paraguay-234508266.html ,
https://www.novobanco.pt/content/dam/novobancopublicsites/docs/pdfs/rating/20230526%20-%20Moodys%20-%20Moody%27s%20takes%20rating%20action%20on%20seven%20Portuguese%20banks.pdf.coredownload.inline.pdf
Fitch rating reports and actions (core metrics, operating environment, support):
https://www.sc.com/en/uploads/sites/66/content/docs/Fitch-Affirms-Standard-Chartered-PLC-at-A-Outlook-Stable-09-Jun-2025.pdf
https://www.globalbank.com.pa/sites/default/files/media/calificaciones_riesgo/fitch-global-bank-octubre-2025-eng.pdf
https://icbc.com.tr/en/images/pdf/Fitch_Press_Release_July_2016.pdf
https://mediobanca.com/static/upload/fit/fitch_press-release_28oct161.pdf
https://hypovereinsbank.de/content/dam/hypovereinsbank/ueber-uns/pdf/investor-relations/Ratings/2024-11-05_Fitch_PR_UniCredit_Bank_GmbH.pdf
https://www.bancaakros.it/media/Banca_Akros_Rating-Report.pdf
