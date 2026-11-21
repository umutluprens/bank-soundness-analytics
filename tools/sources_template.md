# Sources (appendix)

Every external fact used in the methodology, the input files and the agency comparison, grouped
by the decision it supports. Each input file also carries its source per row, so this list and
the files can be checked against each other. Last updated November 2026.

## A. Rating agency methodologies (COMPARISON.md, METHODOLOGY.md v0.6)

Used for: the structure of a grade, through-the-cycle ratios, the qualitative overlay, the
sovereign constraint, the ability factor for support and the 0.5 support ceiling.

{comp}

## B. Sovereign ratings (`data/sovereign_ratings.csv`)

Fitch long-term foreign-currency issuer default rating, taken as the rating in force at 31
December. Read from the Fitch rating history tables on countryeconomy.com, one page per
country. The site is a secondary source; Fitch's own sovereign rating history is the primary
one and should replace it when available.

| Country | Source |
|---|---|
{sv}

Checks and corrections:

- **Türkiye 2012.** countryeconomy.com shows the upgrade to BBB- only from 26 February 2013.
  Fitch upgraded Türkiye to BBB- on 5 November 2012 (Bloomberg, 5 Nov 2012,
  https://www.bloomberg.com/news/articles/2012-11-05/turkey-raised-to-investment-grade-first-time-since-1994-by-fitch ;
  Daily Sabah, https://www.dailysabah.com/business/2012/11/05/fitch-upgrades-turkeys-rating-to-investment-grade ;
  Oxford Business Group, https://oxfordbusinessgroup.com/news/turkey-upgrade-set-boost-investment-prospects ).
  The 2012 row uses BBB- and is marked `corrected`.
- **S&P not used.** The S&P foreign-currency series for Türkiye on the same site appeared to mix
  in local-currency ratings (it showed investment grade in 2011–2015, when S&P rated Türkiye
  below investment grade). S&P and Moody's series were therefore left out until a primary
  source is available.

## C. Parent stress years (`data/parents.csv`, `STRESS_FROM`)

| Parent | From | Source |
|---|---|---|
| VTB Bank, Sberbank | 2014 | Council Regulation (EU) No 833/2014 of 31 July 2014, Annex III lists Sberbank, VTB Bank, Gazprombank, VEB and Rosselkhozbank: https://eur-lex.europa.eu/eli/reg/2014/833/oj ; summaries: https://www.pinsentmasons.com/out-law/guides/sanctions-against-russia-and-ukraine-from-31-july-2014 , https://natlawreview.com/article/european-union-issues-new-sectoral-sanctions-against-russia |
| Banca Popolare di Vicenza | 2016 | Atlante fund subscribed the May 2016 capital increase and held 99.7%: ECB failing-or-likely-to-fail assessment, https://www.bankingsupervision.europa.eu/ecb/pub/pdf/ssm.2017_FOLTF_ITPVI.en.pdf ; ANSA, https://www.ansa.it/english/news/business/2016/04/26/ecb-boi-ok-quaestio-50-stake-2_feb687ae-c83d-498b-ad18-a4bae89dde7d.html |
| Veneto Banca | 2016 | Atlante fund sub-underwrote the June 2016 capital increase and took control: ECB failing-or-likely-to-fail assessment, https://www.bankingsupervision.europa.eu/ecb/pub/pdf/ssm.2017_FOLTF_ITVEN.en.pdf |
| National Bank of Greece, Alpha Bank, Eurobank, Piraeus | 2013 | Spring 2013 recapitalisation by the Hellenic Financial Stability Fund (HFSF converted its 2012 bridge capital into equity in June 2013). Commission Decisions (EU) 2015/1092 (NBG), https://eur-lex.europa.eu/eli/dec/2015/1092/oj/eng ; 2015/455 (Piraeus), https://eur-lex.europa.eu/eli/dec/2015/455/oj/eng ; 2015/454 (Alpha Bank), https://www.legislation.gov.uk/eudn/2015/454/data.htm . Eurobank: also recapitalised by the HFSF in 2013 (events file, not yet re-checked) |

## D. Distress events (`data/events.csv`)

### Verified against a primary or official source ({nv})

| Bank | Country | Year | Event | Source |
|---|---|---|---|---|
{ev}

### Well-documented crisis events, not yet re-checked line by line ({nu})

| Bank | Country | Year | Event |
|---|---|---|---|
{un}

## E. Public data in use and downloaded

- World Bank API (`data/open/worldbank_indicators.csv`, licence CC BY 4.0): World Development
  Indicators, Global Financial Development (source 32) and Worldwide Governance Indicators
  (source 3), for example https://api.worldbank.org/v2/country/TUR/indicator/FB.AST.NPER.ZS?format=json .
  Used for the open operating-environment score.
- IMF World Economic Outlook, October vintages 2010–2021 (April 2011 for 2011), through DBnomics
  (`data/open/weo_vintages.csv`): https://db.nomics.world/IMF , series such as
  https://api.db.nomics.world/v22/series/IMF/WEO:2015-10/TUR.NGDP_RPCH.pcent_change . Used for the
  macro expectations test in phase 2.

Further sources for bank-level data:

- EBA EU-wide Transparency Exercise, bank-by-bank data for about 120 EU and EEA banks; discontinued
  after the 2025 exercise: https://www.eba.europa.eu/risk-and-data-analysis/risk-analysis/eu-wide-transparency-exercise ,
  https://www.eba.europa.eu/eu-wide-transparency-exercise-0
- EBA Pillar 3 Data Hub and the EBA data portal (successor source): https://www.eba.europa.eu/node/19124
- EBA 2025 EU-wide stress test, bank-level CSV files and data guide (scenario inputs for phase 2):
  https://www.eba.europa.eu/assets/st25/full_database/763451/CSV_guide.pdf
- National Bank of Ukraine supervisory data, breakdown by bank: https://bank.gov.ua/en/statistic/supervision-statist ;
  open data API: https://bank.gov.ua/open-data/api-dev
- Banks Association of Türkiye (TBB) statistical reports, bank-level financial statements: to be
  checked before use.

## F. Data not in the repository (S&P terms of use)

- S&P Capital IQ Pro exports used for the 2023 UCD project (figures from public bank reports; the exports fall under S&P's terms of use): yearly CAMELS ratio files 2010–2021,
  management items (Data_Management_2.xlsx) and bank list.
- S&P BICRA groups by country and year (BICRA.xlsx), used as the operating environment score in
  the back-test.

## G. The 2023 project

Yasar, U. (2023). "CAMELS Modelling: Understanding Soundness of Bank", MSc Financial Data
Science, University College Dublin. Code: https://github.com/umutluprens/camels-bank-soundness
