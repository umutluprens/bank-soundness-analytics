"""
Download the public data behind the open operating-environment score and the macro expectations.
Standard library only.   python tools/fetch_open_data.py --out ../external_data

  worldbank_indicators.csv   World Bank API: WDI, Global Financial Development, Worldwide Governance Indicators
  weo_vintages.csv           IMF World Economic Outlook, October vintage of each year, through DBnomics
                             (the forecast made in year t for year t+1: point-in-time expectations)
"""
import argparse, csv, json, time, urllib.request, urllib.parse
from pathlib import Path

COUNTRIES = {"AZE": "Azerbaijan", "BEL": "Belgium", "CYP": "Cyprus", "DNK": "Denmark", "FIN": "Finland",
             "FRA": "France", "GEO": "Georgia", "DEU": "Germany", "GRC": "Greece", "HUN": "Hungary",
             "IRL": "Ireland", "ITA": "Italy", "NLD": "Netherlands", "POL": "Poland", "ESP": "Spain",
             "TUR": "Türkiye", "UKR": "Ukraine", "GBR": "United Kingdom"}
WB = {  # indicator: (source id or None, short name)
    "NY.GDP.PCAP.PP.KD": (None, "GDP_PER_CAPITA_PPP"), "NY.GDP.MKTP.KD.ZG": (None, "GDP_GROWTH"),
    "FP.CPI.TOTL.ZG": (None, "INFLATION"), "FS.AST.PRVT.GD.ZS": (None, "PRIVATE_CREDIT_GDP"),
    "FB.AST.NPER.ZS": (None, "SECTOR_NPL_RATIO"), "FB.BNK.CAPA.ZS": (None, "SECTOR_CAPITAL_ASSETS"),
    "GFDD.EI.05": (32, "SECTOR_ROA"), "GFDD.SI.04": (32, "SECTOR_CREDIT_DEPOSITS"),
    "GFDD.DI.01": (32, "PRIVATE_CREDIT_GDP_GFDD"), "GFDD.SI.02": (32, "SECTOR_NPL_RATIO_GFDD"),
    "GOV_WGI_RL.EST": (3, "RULE_OF_LAW"), "GOV_WGI_RQ.EST": (3, "REGULATORY_QUALITY"),
}
VINTAGE = {2011: "2011-04"}   # October 2011 is not on DBnomics; the April 2011 vintage is used (earlier, so still point in time)
WEO = {"NGDP_RPCH": "GDP_GROWTH_FORECAST", "PCPIPCH": "INFLATION_FORECAST", "LUR": "UNEMPLOYMENT_FORECAST"}


def get(url, tries=3):
    for i in range(tries):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "camels-score/0.8"})
            with urllib.request.urlopen(req, timeout=25) as r:
                return json.loads(r.read().decode("utf-8"))
        except Exception as e:
            err = e
            time.sleep(2 * (i + 1))
    print("FAILED", url[:120], err)
    return None


def worldbank(out, first=2000, last=2021):
    rows = []
    for ind, (src, name) in WB.items():
        url = (f"https://api.worldbank.org/v2/country/{';'.join(COUNTRIES)}/indicator/{ind}"
               f"?format=json&date={first}:{last}&per_page=2000" + (f"&source={src}" if src else ""))
        d = get(url)
        n = 0
        if d and len(d) > 1 and d[1]:
            for o in d[1]:
                if o["value"] is not None and o["countryiso3code"] in COUNTRIES:
                    rows.append([COUNTRIES[o["countryiso3code"]], o["countryiso3code"], int(o["date"]), name, ind, o["value"]])
                    n += 1
        print(f"{ind:<22} {name:<26} {n} values")
    with open(out / "worldbank_indicators.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f); w.writerow(["COUNTRY", "ISO3", "YEAR", "NAME", "INDICATOR", "VALUE"]); w.writerows(rows)


def weo(out, first=2010, last=2021):
    rows = []
    for v in range(first, last + 1):
        code = VINTAGE.get(v, f"{v}-10")
        ids = [f"IMF/WEO:{code}/{c}.{s}.pcent_change" if s != "LUR" else f"IMF/WEO:{code}/{c}.{s}.pcent_total_labor_force"
               for c in COUNTRIES for s in WEO]
        n = 0
        for k in range(0, len(ids), 9):
            url = "https://api.db.nomics.world/v22/series?observations=1&limit=100&series_ids=" + urllib.parse.quote(",".join(ids[k:k + 9]))
            d = get(url)
            for s in (d or {}).get("series", {}).get("docs", []):
                c, subj = s["series_code"].split(".")[:2]
                obs = dict(zip(s["period"], s["value"]))
                for target in (str(v), str(v + 1)):
                    val = obs.get(target)
                    if val not in (None, "NA"):
                        rows.append([COUNTRIES[c], c, v, int(target), WEO[subj], val, code]); n += 1
        print(f"WEO {code}: {n} values")
    with open(out / "weo_vintages.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f); w.writerow(["COUNTRY", "ISO3", "VINTAGE_YEAR", "TARGET_YEAR", "NAME", "VALUE", "WEO_VINTAGE"]); w.writerows(rows)


if __name__ == "__main__":
    ap = argparse.ArgumentParser(); ap.add_argument("--out", default="external_data"); a = ap.parse_args()
    o = Path(a.out); o.mkdir(parents=True, exist_ok=True)
    worldbank(o); weo(o)
