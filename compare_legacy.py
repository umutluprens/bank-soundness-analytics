"""
Compare the 2023 scores with the fixed scorecard.

  python compare_legacy.py --capiq-folder "<...>/Final Report/Data" --events data/events.csv
  python compare_legacy.py                                   # synthetic panel

With --capiq-folder the ACTUAL 2023 output (merged_data_with_clusters_and_scores_PCA.xlsx in the
same folder) is used. Otherwise the 2023 rule is re-run with camels_score.legacy.
"""
import argparse
import warnings
from pathlib import Path

import pandas as pd
from sklearn.metrics import roc_auc_score

from camels_score import legacy, validation as v
from camels_score.data import prepare
from camels_score.scoring import CamelsScorer

warnings.filterwarnings("ignore")


def _auc(y, s, mask):
    m = mask & y.notna() & s.notna()
    return round(roc_auc_score(y[m], s[m]), 3) if y[m].nunique() > 1 else None


def run(raw, events, old_scores=None, calib_end=2017):
    df, ratios, un = prepare(raw, return_unimputed=True)
    sc = (CamelsScorer().fit(df[df.YEAR <= calib_end], ratios, reference=un[un.YEAR <= calib_end])
          .transform(df).reset_index(drop=True))
    if old_scores is None:
        sc["OLD"] = legacy.legacy_score(sc)
    else:
        sc = sc.merge(old_scores, on=["ID", "YEAR"], how="left")
    px = v.forward_proxy_label(un)[["ID", "YEAR", "DISTRESS_FWD"]].rename(columns={"DISTRESS_FWD": "PX"})
    d = sc.merge(px, on=["ID", "YEAR"], how="left")
    if events is not None:
        d = v.event_label(d, events, 2).rename(columns={"DISTRESS_FWD": "EV"})
    base = d["OLD"].notna()
    oot = base & (d.YEAR > calib_end)
    scores = {"2023 score": d["OLD"], "new final grade": d["FINAL_GRADE"],
              "new standalone grade": d["STANDALONE_GRADE"]}
    rows = []
    for k, s in scores.items():
        r = {"score": k}
        if "EV" in d:
            r["events_all"], r[f"events_{calib_end + 1}+"] = _auc(d.EV, s, base), _auc(d.EV, s, oot)
        r["proxy_all"], r[f"proxy_{calib_end + 1}+"] = _auc(d.PX, s, base), _auc(d.PX, s, oot)
        rows.append(r)
    print(f"{base.sum():,} bank-years with a 2023 score; {len(ratios)} ratios in the new scorecard")
    if "EV" in d:
        print(f"event rows: {int(d.loc[base, 'EV'].sum())} (after {calib_end}: {int(d.loc[oot, 'EV'].sum())})")
    print("\nAUC (0.5 = random; higher = better ranking of future distress)")
    print(pd.DataFrame(rows).to_string(index=False))
    print("\nScore distribution, 2023:", d["OLD"].value_counts().sort_index().astype(int).to_dict())
    print("Grade distribution, new:", d["FINAL_GRADE"].value_counts().sort_index().to_dict())
    if "EV" in d:
        hit = d[d.EV == 1].sort_values(["BANK NAME", "YEAR"])
        print("\nGrades in the year(s) before each event:")
        print(hit[["BANK NAME", "COUNTRY", "YEAR", "OLD", "STANDALONE_GRADE", "FINAL_GRADE"]]
              .rename(columns={"OLD": "2023 score"}).to_string(index=False))
    return d


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--capiq-folder")
    ap.add_argument("--events")
    a = ap.parse_args()
    ev = pd.read_csv(a.events) if a.events else None
    if a.capiq_folder:
        from camels_score.capiq import build_panel
        raw = build_panel(a.capiq_folder)
        old = pd.read_excel(Path(a.capiq_folder) / "merged_data_with_clusters_and_scores_PCA.xlsx")
        old = old[["ID", "YEAR", "score"]].rename(columns={"score": "OLD"})
        run(raw, ev, old)
    else:
        from camels_score.synthetic import make_panel
        raw, ev_syn = make_panel(extended=False)
        run(raw, ev if ev is not None else ev_syn)
