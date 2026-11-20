"""
Score a bank that is not in the panel from up to three years of its ratios.

  python score_new_bank.py --input templates/example_bank.csv --calibration ../results/calibration.json \
      --country-score 4 --sovereign BBB --name "Example Bank"
  # with a parent: --parent-rating A --support strategic --assets-share 0.08
  # analyst overlay (notches, positive = weaker): --overlay 1

Fill templates/new_bank_template.csv: one row per ratio, one column per year, values in %
(debt / equity as a multiple). Leave a cell empty if the figure is not available; it is then
filled with a weak value, as in the panel. ROAA volatility is calculated, not entered.
"""
import argparse
import json

from camels_score.newbank import score_new_bank, read_template


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--input", required=True)
    ap.add_argument("--calibration", required=True, help="calibration.json from run_pipeline.py")
    ap.add_argument("--name", default="New bank")
    ap.add_argument("--country-score", type=float, help="1 (strong) to 10 (weak) operating environment score")
    ap.add_argument("--sovereign", help="sovereign long-term FC rating, e.g. BBB-")
    ap.add_argument("--parent-rating", help="parent issuer rating, e.g. A+")
    ap.add_argument("--parent-score", type=float, help="parent CAMELS score 1-10 (instead of a rating)")
    ap.add_argument("--support", default="none", choices=["core", "strategic", "moderate", "none"])
    ap.add_argument("--assets-share", type=float, help="subsidiary assets / parent assets, e.g. 0.12")
    ap.add_argument("--parent-stress", action="store_true")
    ap.add_argument("--overlay", type=float, default=0.0)
    ap.add_argument("--json", help="also write the full result to this file")
    a = ap.parse_args()

    res = score_new_bank(read_template(a.input), a.calibration, country_score=a.country_score,
                         sovereign_rating=a.sovereign, parent_rating=a.parent_rating,
                         parent_score=a.parent_score, support_level=a.support,
                         assets_share=a.assets_share, parent_stress=a.parent_stress,
                         overlay=a.overlay)
    last = res["latest"]
    print(f"\n{a.name}, {last['year']}: grade {last['label']} ({last['descriptor']}), score {last['final_score']}")
    for s, v in last["steps"]:
        print(f"  {s:<62} {v:5.2f}")
    print("\n  Pillar z-scores: " + ", ".join(f"{p} {z:+.2f}" for p, z in last["pillars"].items()))
    imp = [r for r, x in last["ratios"].items() if x["imputed"]]
    if imp:
        print(f"  Filled with a weak value (not reported): {', '.join(imp)}")
    print(f"  Data quality: {last['data_quality']}  ({last['reported_ratios']} of {len(last['ratios'])} ratios reported)")
    if len(res["bank_years"]) > 1:
        print("\n  By year: " + ", ".join(f"{r['year']} {r['label']}" for r in res["bank_years"]))
    if not last["enough_data"]:
        print("  Warning: fewer than 5 ratios reported. The panel would not grade this bank-year.")
    if a.json:
        with open(a.json, "w") as f:
            json.dump(res, f, indent=2, default=str)


if __name__ == "__main__":
    main()
