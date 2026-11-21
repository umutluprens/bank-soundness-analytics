"""
Phase 2, first version: walk-forward forecast of next year's score.

  python run_forecast.py --capiq-folder "<...>/Final Report/Data" --events data/events.csv --out results/forecast
  python run_forecast.py --synthetic --out results_synthetic/forecast
  # with macro expectations (IMF WEO October vintages, tools/fetch_open_data.py):
  python run_forecast.py ... --macro data/open/weo_vintages.csv

Writes forecast_by_bank_year.csv (every forecast with its realised outcome) and forecast_report.json.
"""
import argparse
import json
from pathlib import Path

import pandas as pd

from camels_score.data import load, prepare
from camels_score.scoring import CamelsScorer
from camels_score.forecast import walk_forward, evaluate


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--input"); ap.add_argument("--capiq-folder"); ap.add_argument("--synthetic", action="store_true")
    ap.add_argument("--events"); ap.add_argument("--macro", help="WEO vintage file from tools/fetch_open_data.py")
    ap.add_argument("--open-oe", help="World Bank indicator file: use the open country score")
    ap.add_argument("--calib-end", type=int, default=2017)
    ap.add_argument("--first-target", type=int, default=2014)
    ap.add_argument("--no-ratio-route", action="store_true")
    ap.add_argument("--out", default="results/forecast")
    a = ap.parse_args()
    out = Path(a.out); out.mkdir(parents=True, exist_ok=True)

    events = None
    if a.synthetic:
        from camels_score.synthetic import make_panel
        raw, events = make_panel()
    elif a.capiq_folder:
        from camels_score.capiq import build_panel
        raw = build_panel(a.capiq_folder)
    else:
        raw = load(a.input)
    if a.events:
        events = pd.read_csv(a.events)
    from camels_score.forecast import load_macro
    macro = load_macro(a.macro) if a.macro else None

    if a.open_oe:
        from camels_score.oe import build_open_oe
        oe, _ = build_open_oe(a.open_oe, a.calib_end)
        raw.columns = [str(c).strip().upper() for c in raw.columns]
        raw = raw.drop(columns=[c for c in ("OE_SCORE",) if c in raw.columns]).merge(
            oe[["COUNTRY", "YEAR", "OE_SCORE"]], on=["COUNTRY", "YEAR"], how="left")
    df, ratios, unimputed, basis = prepare(raw, return_reference=True)
    scorer = CamelsScorer().fit(df[df["YEAR"] <= a.calib_end], ratios,
                                 reference=basis[basis["YEAR"] <= a.calib_end])
    scored = scorer.transform(df)
    fc = walk_forward(scored, ratios, scorer, first_target=a.first_target, macro=macro,
                      ratio_route=not a.no_ratio_route)
    rep, fc = evaluate(fc, events)
    rep["note"] = ("Score = OWN_SCORE (country anchor and loss notch, no group support). "
                   "Walk-forward: each target year forecast from the year before, trained on earlier pairs only. "
                   "Macro expectations: " + ("included" if macro is not None else "not included"))
    by_year = []
    for t, g in fc.groupby(fc["YEAR"] + 1):
        r, _ = evaluate(g.drop(columns=[c for c in ("EVENT_NEXT",) if c in g]))
        by_year.append({"target_year": int(t), "n": r["bank_years"],
                        **{k: r[k]["mae_score"] for k in ("F_PERSIST", "F_DIRECT", "F_RATIOS") if k in r}})
    rep["mae_by_target_year"] = by_year
    cols = ["ID", "YEAR", "COUNTRY", "OWN_SCORE", "NEXT_OWN_SCORE", "F_PERSIST", "F_DIRECT", "F_DIRECT_P10",
            "F_DIRECT_P90", "F_RATIOS", "P_DOWNGRADE", "DOWNGRADE", "EVENT_NEXT"]
    fc[[c for c in cols if c in fc]].round(3).to_csv(out / "forecast_by_bank_year.csv", index=False)
    (out / "forecast_report.json").write_text(json.dumps(rep, indent=2))
    print(json.dumps(rep, indent=2))


if __name__ == "__main__":
    main()
