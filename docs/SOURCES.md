# Sources (appendix)

Every external fact used in the methodology, the input files and the agency comparison, grouped
by the decision it supports. Each input file also carries its source per row, so this list and
the files can be checked against each other. Last updated November 2026.

## A. Rating agency methodologies (COMPARISON.md, METHODOLOGY.md v0.6)

Used for: the structure of a grade, through-the-cycle ratios, the qualitative overlay, the
sovereign constraint, the ability factor for support and the 0.5 support ceiling.

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

## B. Sovereign ratings (`data/sovereign_ratings.csv`)

Fitch long-term foreign-currency issuer default rating, taken as the rating in force at 31
December. Read from the Fitch rating history tables on countryeconomy.com, one page per
country. The site is a secondary source; Fitch's own sovereign rating history is the primary
one and should replace it when available.

| Country | Source |
|---|---|
| Azerbaijan | https://countryeconomy.com/ratings/azerbaijan |
| Belgium | https://countryeconomy.com/ratings/belgium |
| Cyprus | https://countryeconomy.com/ratings/cyprus |
| Denmark | https://countryeconomy.com/ratings/denmark |
| Finland | https://countryeconomy.com/ratings/finland |
| France | https://countryeconomy.com/ratings/france |
| Georgia | https://countryeconomy.com/ratings/georgia |
| Germany | https://countryeconomy.com/ratings/germany |
| Greece | https://countryeconomy.com/ratings/greece |
| Hungary | https://countryeconomy.com/ratings/hungary |
| Ireland | https://countryeconomy.com/ratings/ireland |
| Italy | https://countryeconomy.com/ratings/italy |
| Netherlands | https://countryeconomy.com/ratings/netherlands |
| Poland | https://countryeconomy.com/ratings/poland |
| Spain | https://countryeconomy.com/ratings/spain |
| Türkiye | https://countryeconomy.com/ratings/turkey |
| Ukraine | https://countryeconomy.com/ratings/ukraine |
| United Kingdom | https://countryeconomy.com/ratings/uk |

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

### Verified against a primary or official source (48)

| Bank | Country | Year | Event | Source |
|---|---|---|---|---|
| International Bank of Azerbaijan | Azerbaijan | 2015 | State rescue after manat devaluation | https://www.intellinews.com/london-court-upholds-request-to-protect-azerbaijan-s-iba-against-creditors-123148/ |
| Parabank OJSC | Azerbaijan | 2016 | Licence cancelled by FIMSA (2016 clean-up) | https://www.azernews.az/business/99714.html |
| International Bank of Azerbaijan | Azerbaijan | 2017 | Default on USD 3.3bn foreign debt and restructuring (May 2017) | https://www.intellinews.com/94-of-creditors-of-azerbaijan-s-iba-approve-debt-restructuring-plan-125621/ |
| Amrahbank OJSC | Azerbaijan | 2020 | Licence revoked by Central Bank (28 Apr 2020) | https://www.cbar.az/press-release-2586/azrbaycan-respublikasi-mrkzi-bankinin-mlumati |
| AGBank OJSC | Azerbaijan | 2020 | Licence revoked by Central Bank (12 May 2020) | https://en.trend.az/business/finance/3238073.html |
| Dexia SA | Belgium | 2011 | Second state rescue and orderly resolution plan | Commission Decision 2014/189/EU of 28 Dec 2012 (Dexia orderly resolution; describes Oct-Dec 2011 sale of DBB to Belgium and Dec 2011 state guarantees): https://eur-lex.europa.eu/eli/dec/2012/836/oj |
| Bank of Cyprus Holdings | Cyprus | 2013 | Bail-in of uninsured depositors | Central Bank of Cyprus, Bailing-in of Bank of Cyprus Decree (29 Mar 2013); Bank of Cyprus history page: https://www.bankofcyprus.com/en-gb/group/who-we-are/our-bank/our-history/2010-2020/ |
| Max Bank A/S | Denmark | 2011 | Failed solvency requirement; wound up via Finansiel Stabilitet (Oct 2011) | https://fs.dk/media/1eab2ogc/fs_annual_report_2011_uk.pdf |
| Tønder Bank A/S | Denmark | 2012 | Taken over by Finansiel Stabilitet (Nov 2012) | https://admin.finanstilsynet.dk/Media/638513584887639182/Finanstilsynets_aarsrapport2012.pdf |
| Østjydsk Bank A/S | Denmark | 2018 | Failed solvency requirement; Finansiel Stabilitet involved in transfer | https://finanstilsynet.dk/media/43211/Redegrelse_om_stjydsk_Bank_0820 pdf.pdf |
| Dexia Crédit Local S.A. | France | 2011 | Part of Dexia group rescue | Commission Decision 2014/189/EU of 28 Dec 2012 (Dexia orderly resolution; describes Oct-Dec 2011 sale of DBB to Belgium and Dec 2011 state guarantees): https://eur-lex.europa.eu/eli/dec/2012/836/oj |
| Norddeutsche Landesbank Girozentrale | Germany | 2019 | EUR 3.6bn recapitalisation led by owner states (EC: no state aid) | https://www.nordlb.com/nordlb/press/eu-commission-gives-green-light-to-capital-measures |
| Greensill Bank AG | Germany | 2021 | BaFin moratorium (3 Mar 2021) and insolvency | https://www.bafin.de/ref/19621044 |
| National Bank of Greece S.A. | Greece | 2013 | HFSF recapitalisation | Commission Decision (EU) 2015/1092 (NBG): HFSF Spring 2013 recapitalisation, https://eur-lex.europa.eu/eli/dec/2015/1092/oj/eng |
| Piraeus Financial Holdings S.A. | Greece | 2013 | HFSF recapitalisation | Commission Decision (EU) 2015/455 (Piraeus): HFSF Spring 2013 recapitalisation, https://eur-lex.europa.eu/eli/dec/2015/455/oj/eng |
| Eurobank Ergasias | Greece | 2013 | HFSF recapitalisation | Eurobank announcement 20 Jun 2013 (HFSF acquired 98.56% after recapitalisation): https://www.athexgroup.gr/en/node/736515 ; Commission Decision 2014/885/EU: https://eur-lex.europa.eu/eli/dec/2014/885/oj |
| National Bank of Greece S.A. | Greece | 2015 | Second recapitalisation after 2015 ECB assessment | ECB press release 31 Oct 2015 (capital shortfall): https://www.ecb.europa.eu/press/pr/date/2015/html/pr151031.en.html ; ESM 8 Dec 2015, EUR 2.71bn for NBG recapitalisation: https://www.esm.europa.eu/print/pdf/node/81 |
| Piraeus Financial Holdings S.A. | Greece | 2015 | Second recapitalisation after 2015 ECB assessment | ECB press release 31 Oct 2015 (capital shortfall): https://www.ecb.europa.eu/press/pr/date/2015/html/pr151031.en.html ; Eurostat advice 2016 on 2015 recapitalisations (HFSF EUR 2,720mn in Piraeus): https://ec.europa.eu/eurostat/documents/1015035/7142247/Advice-2016-EL-Statistical-treatment-2015-bank-recapitalisations.pdf/01f5a9df-a8be-4d69-b8bc-621b1acc062e |
| Eurobank Ergasias | Greece | 2015 | Capital shortfall in ECB 2015 assessment, covered by private capital and liability management exercise | ECB press release 31 Oct 2015 (Eurobank shortfall EUR 2,122mn adverse): https://www.ecb.europa.eu/press/pr/date/2015/html/pr151031.en.html ; Eurostat advice 2016 (Eurobank covered needs through private investors only): https://ec.europa.eu/eurostat/documents/1015035/7142247/Advice-2016-EL-Statistical-treatment-2015-bank-recapitalisations.pdf/01f5a9df-a8be-4d69-b8bc-621b1acc062e |
| Allied Irish Banks, p.l.c. | Ireland | 2011 | State recapitalisation after 2011 PCAR | Central Bank of Ireland, Financial Measures Programme report (Mar 2011, PCAR capital requirements for AIB, BOI, EBS, IL&P): https://centralbank.ie/docs/default-source/publications/financial-measures-programme/the-financial-measures-programme-report.pdf ; Dail answer 20 Jul 2011 on State recapitalisation: https://www.oireachtas.ie/en/debates/question/2011-07-20/82/ |
| Permanent TSB plc | Ireland | 2011 | State recapitalisation after 2011 PCAR | Central Bank of Ireland, Financial Measures Programme report (Mar 2011, PCAR capital requirements for AIB, BOI, EBS, IL&P): https://centralbank.ie/docs/default-source/publications/financial-measures-programme/the-financial-measures-programme-report.pdf ; Dail answer 20 Jul 2011 on State recapitalisation: https://www.oireachtas.ie/en/debates/question/2011-07-20/82/ |
| Permanent TSB Group Holdings plc | Ireland | 2011 | State recapitalisation after 2011 PCAR | Central Bank of Ireland, Financial Measures Programme report (Mar 2011, PCAR capital requirements for AIB, BOI, EBS, IL&P): https://centralbank.ie/docs/default-source/publications/financial-measures-programme/the-financial-measures-programme-report.pdf ; Dail answer 20 Jul 2011 on State recapitalisation: https://www.oireachtas.ie/en/debates/question/2011-07-20/82/ |
| Banca Popolare di Spoleto SpA | Italy | 2013 | Extraordinary administration (Feb 2013) | https://en.wikipedia.org/wiki/Banca_Popolare_di_Spoleto |
| Banca Monte dei Paschi di Siena S.p.A. | Italy | 2013 | State aid (Monti bonds) | Commission decision of 27 Nov 2013, SA.36175 (MPS restructuring aid, New Financial Instruments of Feb 2013), cited in: https://ec.europa.eu/competition/state_aid/cases/270037/270037_1951496_149_2.pdf |
| Banca Monte dei Paschi di Siena S.p.A. | Italy | 2017 | Precautionary recapitalisation | European Commission decision of 4 Jul 2017, SA.47677 (precautionary recapitalisation, EUR 5.4bn): https://ec.europa.eu/competition/state_aid/cases/270037/270037_1951496_149_2.pdf ; BMPS press release 5 Jul 2017: https://www.gruppomps.it/en/media-and-news/press-releases/bmps-european-commission-approves-the-2017-2021-restructuring-plan.html |
| Veneto Banca S.p.A. | Italy | 2017 | Compulsory administrative liquidation (25 Jun 2017) | https://www.bancaditalia.it/media/notizia/piano-di-intervento-per-la-soluzione-della-crisi-della-banca-popolare-di-vicenza-e-di-veneto-banca |
| Banca Nuova SpA | Italy | 2017 | Subsidiary of failed Banca Popolare di Vicenza; transferred to Intesa | https://group.intesasanpaolo.com/it/investor-relations/comunicati-stampa-price-sensitive/2017/06/CNT-05-00000004DDFA8 |
| Banca Apulia SpA | Italy | 2017 | Subsidiary of failed Veneto Banca; transferred to Intesa | https://group.intesasanpaolo.com/it/investor-relations/comunicati-stampa-price-sensitive/2017/06/CNT-05-00000004DDFA8 |
| Cassa di Risparmio di Cesena S.p.A. | Italy | 2017 | FITD Voluntary Scheme rescue and sale to Crédit Agricole | https://fitd.it/Content/public/documents/Files/SVI_Relazione_e_Rendiconto_2025.pdf |
| BANCA CARIM - Cassa di Risparmio di Rimini S.p.A. | Italy | 2017 | FITD Voluntary Scheme rescue and sale to Crédit Agricole | https://fitd.it/Content/public/documents/Files/SVI_Relazione_e_Rendiconto_2025.pdf |
| Banca Carige S.p.A. | Italy | 2019 | ECB temporary administration (2 Jan 2019) | https://www.bankingsupervision.europa.eu/press/pr/date/2019/html/ssm.pr190102.en.html |
| SRH N.V. (SNS REAAL) | Netherlands | 2013 | Nationalised by the Dutch State (1 Feb 2013) | https://government.nl/latest/news/2013/02/01/state-of-the-netherlands-nationalises-sns-reaal |
| Idea Bank S.A. | Poland | 2020 | Resolution by BFG (31 Dec 2020) | https://bfg.pl/en/resolution-of-idea-bank-s-a/ |
| Getin Noble Bank S.A. | Poland | 2022 | Resolution by BFG (30 Sep 2022) | https://bfg.pl/en/?p=15344 |
| Caja de Ahorros de Galicia | Spain | 2011 | FROB recapitalisation and control of NCG Banco (Sep 2011) | https://agenceurope.eu/en/bulletin/article/10464/32/state-aid-allows-for-rescue-of-three-spanish-banks |
| Bankia, S.A. | Spain | 2012 | Nationalisation and FROB recapitalisation | Banco de Espana press release 27 Nov 2012 (approval of BFA-Bankia restructuring plan): https://www.bde.es/f/webbde/SSICOM/20121127/presbe2012_52e.pdf ; FROB recapitalisation 26 Dec 2012: https://www.bde.es/f/webbde/GAP/prensa/info_interes/ficheros/frob261212en.pdf |
| Liberbank, S.A. | Spain | 2012 | EC-approved restructuring with ESM/FROB capital (Group 2 bank; 20 Dec 2012) | https://cms.law/en/int/regulatory-news/ec-liberbank-caja3-banco-mare-nostrum-banco-ceiss |
| Banco Grupo Cajatres SA | Spain | 2012 | EC-approved restructuring with ESM/FROB capital (Group 2 bank; 20 Dec 2012) | https://cms.law/en/int/regulatory-news/ec-liberbank-caja3-banco-mare-nostrum-banco-ceiss |
| JSC Brokbusinessbank | Ukraine | 2014 | Declared insolvent by NBU (28 Feb 2014); licence revoked Jun 2014 | https://bank.gov.ua/en/news/all/natsionalniy-bank-priynyav-rishennya-pro-vidklikannya-bankivskoyi-litsenziyi-ta-likvidatsiyu-at-brokbiznesbank |
| PJSC Delta Bank | Ukraine | 2015 | Declared insolvent by NBU (2 Mar 2015) | https://bank.gov.ua/en/news/all/at-delta-bank-vidneseno-do-kategoriyi-neplatospromojnih |
| PJSC Kyivska Rus Bank | Ukraine | 2015 | Declared insolvent by NBU (19 Mar 2015) | https://bank.gov.ua/en/news/all/pat-bank-kiyivska-rus-vidneseno-do-kategoriyi-neplatospromojnih |
| Commercial Bank Financial Initiative PJSC | Ukraine | 2015 | Declared insolvent by NBU (23 Jun 2015) | https://bank.gov.ua/news/all/pat-kb-finansova-initsiativa-vidneseno-do-kategoriyi-neplatospromojnih |
| JSC CB PrivatBank | Ukraine | 2016 | Nationalisation | National Bank of Ukraine, 18 Dec 2016 (Cabinet decision on state participation): https://bank.gov.ua/en/news/all/derjava-uhvalila-rishennya-pro-vhodjennya-do-kapitalu-pat-privatbank |
| Diamantbank PJSC | Ukraine | 2017 | Declared insolvent by NBU (24 Apr 2017) | https://bank.gov.ua/news/all/pat-diamantbank-vidneseno-do-kategoriyi-neplatospromojnih |
| JSC VTB Bank (Ukraine) | Ukraine | 2018 | Declared insolvent by NBU (27 Nov 2018); liquidity crisis after court asset freeze | https://bank.gov.ua/en/news/all/at-vtb-bank-vidneseno-do-kategoriyi-neplatospromojnih |
| MEGABANK JSC | Ukraine | 2022 | Declared insolvent by NBU (Jun 2022); problems predate the war | https://bank.gov.ua/en/news/all/at-megabank-vidneseno-do-kategoriyi-neplatospromojnih |
| Marfin Laiki Bank UK | United Kingdom | 2013 | Parent Laiki resolved; UK branch closed and deposits transferred to Bank of Cyprus UK | Bank of England, 2 Apr 2013: https://www.bankofengland.co.uk/news/2013/april/closure-of-cyprus-popular-bank-public-co-ltd |
| The Co-operative Bank p.l.c. | United Kingdom | 2013 | Capital shortfall and liability management exercise | Bank of England PRA statements 2013 (GBP 1.5bn capital shortfall): https://www.bankofengland.co.uk/news/2013/august/pra-statements-on-bank-capital-and-leverage-ratios-released-in-2013 ; FCA final notice 2015 (LME completed 20 Dec 2013): https://www.fca.org.uk/publication/final-notices/the-co-operative-bank-plc-2015.pdf |

All events in the file are verified against a primary or official source.

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
