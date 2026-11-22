"""
End-to-end run.

  python run_pipeline.py --capiq-folder "<...>/Final Report/Data" --events data/events.csv \
                         --parents data/parents.csv --out results/
  python run_pipeline.py --input panel.xlsx --out results/          # any tidy bank-year file
  python run_pipeline.py --synthetic --out results_synthetic/

Two outcome labels are evaluated whenever possible:
  events : external distress events (ID, YEAR, EVENT) within the next 2 years   -> main evidence
  proxy  : next-year capital < 10.5%, ROAA < -1% or NPL spike, from UNIMPUTED data -> weak evidence
"""
import argparse
import json
from pathlib import Path

import pandas as pd

from camels_score.data import load, prepare, merge_extra_ratios
from camels_score.scoring import CamelsScorer
from camels_score import validation as v
from camels_score.profiles import peer_profiles
from camels_score.group import (load_parents, attach_support_level, apply_group_support,
                                load_sovereign)
from camels_score.overlays import load_overlays, apply_overlays


def evaluate(scored, ratios, calib_end, label_name):
    gt = v.grade_table(scored)
    return gt, {
        "label": label_name,
        "all_years": v.discrimination(scored),
        "out_of_time": v.discrimination(scored[scored["YEAR"] > calib_end]),
        "standalone_grade_all_years": v.discrimination(scored, "STANDALONE_GRADE"),
        "spearman_grade_vs_rate": gt.attrs["spearman_grade_vs_rate"],
        "challengers": v.out_of_time_challengers(scored, ratios, calib_end),
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--input")
    ap.add_argument("--capiq-folder")
    ap.add_argument("--events")
    ap.add_argument("--parents", help="parent mapping (data/parents.csv) for group support")
    ap.add_argument("--sovereign", help="sovereign FC ratings (data/sovereign_ratings.csv)")
    ap.add_argument("--overlays", help="analyst overlays (data/overlays.csv)")
    ap.add_argument("--extra-ratios", help="tidy ID/YEAR file with extra ratios, e.g. CET1")
    ap.add_argument("--no-multi-year", action="store_true",
                    help="score latest values only (no 3-year weaker-of rule)")
    ap.add_argument("--open-oe", help="World Bank indicator file (tools/fetch_open_data.py): use the open "
                                      "operating-environment score in place of BICRA / OE_SCORE")
    ap.add_argument("--eba-folder", help="folder with EBA transparency files (<exercise>/tr_oth*.csv): "
                                         "adds matched banks for the years after the panel ends")
    ap.add_argument("--eba-map", default="data/eba_bank_map.csv", help="LEI to panel ID table")
    ap.add_argument("--synthetic", action="store_true")
    ap.add_argument("--calib-end", type=int, default=2017,
                    help="last year of the calibration sample; later years are out-of-time")
    ap.add_argument("--out", default="results")
    a = ap.parse_args()
    out = Path(a.out)
    out.mkdir(parents=True, exist_ok=True)

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

    if a.extra_ratios:
        raw = merge_extra_ratios(raw, a.extra_ratios)
    if a.eba_folder:
        from camels_score.eba import extend_panel
        n0 = len(raw)
        raw = extend_panel(raw, a.eba_folder, a.eba_map, a.calib_end)
        added = raw[raw["DATA_SOURCE"] == "EBA"]
        print(f"EBA extension: {len(raw) - n0} bank-years added "
              f"({added['ID'].nunique()} banks, {int(added['YEAR'].min())}-{int(added['YEAR'].max())})")
    oe_table = None
    if a.open_oe:
        from camels_score.oe import build_open_oe
        oe_table, _ = build_open_oe(a.open_oe, a.calib_end)
        raw.columns = [str(c).strip().upper() for c in raw.columns]
        raw = raw.drop(columns=[c for c in ("OE_SCORE",) if c in raw.columns]).merge(
            oe_table[["COUNTRY", "YEAR", "OE_SCORE"]], on=["COUNTRY", "YEAR"], how="left")
        # years after the last country score keep the last one
        raw["OE_SCORE"] = raw.sort_values("YEAR").groupby("COUNTRY")["OE_SCORE"].ffill().reindex(raw.index)
        print(f"open operating-environment score attached for {raw['OE_SCORE'].notna().mean():.0%} of bank-years")
    df, ratios, unimputed, basis = prepare(raw, multi_year=not a.no_multi_year,
                                           return_reference=True)
    print(f"{len(df):,} bank-years, {df['ID'].nunique():,} banks, {len(ratios)} ratios scored")

    if a.parents:
        df = attach_support_level(df, load_parents(a.parents))
    if a.sovereign:
        sov = load_sovereign(a.sovereign)
        df = df.merge(sov, on=["COUNTRY", "YEAR"], how="left").set_axis(df.index)
        # years after the last rating in the file keep the last one
        df["SOVEREIGN_GRADE"] = df.sort_values("YEAR").groupby("COUNTRY")["SOVEREIGN_GRADE"].ffill().reindex(df.index)
        print(f"sovereign grade available for {df['SOVEREIGN_GRADE'].notna().mean():.0%} of bank-years")
    scorer = CamelsScorer().fit(df[df["YEAR"] <= a.calib_end], ratios,
                                 reference=basis[basis["YEAR"] <= a.calib_end])
    from camels_score.newbank import add_new_bank_params
    add_new_bank_params(scorer, unimputed[unimputed["YEAR"] <= a.calib_end],
                        basis[basis["YEAR"] <= a.calib_end])
    scorer.save(out / "calibration.json")
    scored = scorer.transform(df)
    if a.parents:
        scored = apply_group_support(scored)
    # Validation runs on the score WITHOUT overlays (an analyst overlay decided with hindsight
    # would flatter the back-test). Overlays are applied to the published score below.
    scored, profile_summary = peer_profiles(scored)

    report = {"ratios_scored": ratios, "calibration_years": f"<= {a.calib_end}",
              "psi_composite_calib_vs_later": round(v.psi(
                  scored.loc[scored["YEAR"] <= a.calib_end, "COMPOSITE_Z"],
                  scored.loc[scored["YEAR"] > a.calib_end, "COMPOSITE_Z"]), 3)}
    tables = {}

    proxy = v.forward_proxy_label(unimputed)[["ID", "YEAR", "DISTRESS_FWD"]]
    s_proxy = scored.merge(proxy, on=["ID", "YEAR"], how="left")
    tables["grade_vs_proxy"], report["proxy"] = evaluate(
        s_proxy, ratios, a.calib_end, "forward proxy from unimputed data (weak evidence)")

    if events is not None:
        s_ev = v.event_label(scored, events, horizon=2)
        tables["grade_vs_events"], report["events"] = evaluate(
            s_ev, ratios, a.calib_end, "external events within 2 years")
        scored = s_ev.rename(columns={"DISTRESS_FWD": "EVENT_NEXT_2Y"}).drop(columns="LABEL_SOURCE")
    scored = scored.merge(proxy.rename(columns={"DISTRESS_FWD": "PROXY_NEXT_1Y"}),
                          on=["ID", "YEAR"], how="left")
    if a.overlays:
        ov = load_overlays(a.overlays)
        scored["SCORE_BEFORE_OVERLAY"] = scored["FINAL_SCORE"]
        scored = apply_overlays(scored, ov)
        report["overlays_applied"] = int((scored["OVERLAY_NOTCHES"] != 0).sum())

    from camels_score.ratios import GRADE_DESCRIPTOR
    scored["GRADE_DESCRIPTOR"] = scored["FINAL_GRADE"].map(GRADE_DESCRIPTOR)
    if oe_table is not None:
        oe_table.to_csv(out / "open_oe_scores.csv", index=False)
        report["operating_environment"] = "open score (World Bank data)"
    with pd.ExcelWriter(out / "camels_scores.xlsx") as xw:
        keep = [c for c in ["BANK NAME", "ID", "COUNTRY", "YEAR", "TYPE"] if c in scored]
        grade_cols = [c for c in scored.columns if c.startswith("PILLAR_") or c in
                      ("COMPOSITE_Z", "STANDALONE_SCORE", "STANDALONE_GRADE", "OE_SCORE_USED",
                       "LOSS_NOTCH", "OWN_SCORE", "SUPPORT_LEVEL", "PARENT_NAME", "PARENT_SCORE",
                       "ASSETS_SHARE_OF_PARENT", "SUPPORT_ABILITY", "PARENT_STRESS", "WEAK_PARENT",
                       "SOVEREIGN_GRADE", "SUPPORT_PROB", "GROUP_ADJ", "SCORE_BEFORE_OVERLAY",
                       "OVERLAY_NOTCHES", "FINAL_SCORE", "FINAL_GRADE", "GRADE_LABEL", "GRADE_DESCRIPTOR",
                       "DATA_QUALITY_FLAG", "MISSING_COUNT", "DATA_SOURCE", "CARRIED_RATIOS",
                       "PROFILE", "EVENT_NEXT_2Y",
                       "PROXY_NEXT_1Y")]
        scored[keep + grade_cols].to_excel(xw, sheet_name="scores", index=False)
        for name, t in tables.items():
            t.to_excel(xw, sheet_name=name)
        v.migration_matrix(scored).to_excel(xw, sheet_name="migration")
        profile_summary.to_excel(xw, sheet_name="peer_profiles")
        scorer.ratio_table().to_excel(xw, sheet_name="calibration", index=False)
    with open(out / "validation_report.json", "w") as f:
        json.dump(report, f, indent=2, default=str)

    print(json.dumps(report, indent=2, default=str))
    for name, t in tables.items():
        print(f"\n{name} (rate in %):\n{t}")
    return scored


if __name__ == "__main__":
    main()
