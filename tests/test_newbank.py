import json
import shutil
import subprocess
from pathlib import Path

import numpy as np
import pytest

from camels_score.data import prepare
from camels_score.scoring import CamelsScorer
from camels_score.synthetic import make_panel
from camels_score.newbank import add_new_bank_params, score_new_bank

ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture(scope="module")
def setup(tmp_path_factory):
    raw, _ = make_panel(n_banks=200, missing=0.0)
    df, ratios, cleaned, basis = prepare(raw, return_reference=True)
    sc = CamelsScorer().fit(df, ratios, reference=basis)
    add_new_bank_params(sc, cleaned, basis)
    path = tmp_path_factory.mktemp("c") / "calibration.json"
    sc.save(path)
    return json.load(open(path)), sc, df, cleaned


def _years(cleaned, bank, year, ratios):
    h = cleaned[(cleaned.ID == bank) & cleaned.YEAR.between(year - 2, year)].sort_values("YEAR")
    return {int(r.YEAR): {k: r[k] for k in ratios if k != "ROAA VOLATILITY 3Y"} for _, r in h.iterrows()}


def test_matches_pipeline_for_full_data_banks(setup):
    calib, sc, df, cleaned = setup
    ratios = calib["params"]["ratios"]
    out = sc.transform(df)
    checked = 0
    diffs = []
    for (bank, year), row in out.groupby(["ID", "YEAR"]):
        yrs = _years(cleaned, bank, year, ratios)
        if len(yrs) < 3 or any(v is None or np.isnan(v) for y in yrs.values() for v in y.values()):
            continue
        res = score_new_bank(yrs, calib, country_score=row["OE_SCORE_USED"].iloc[0]
                             if "OE_SCORE_USED" in row else None)["latest"]
        diffs.append(abs(res["own_score"] - row["OWN_SCORE"].iloc[0]))
        checked += 1
        if checked >= 40:
            break
    assert checked > 10
    # winsorising differs (pooled vs per year), so a few bank-years may move; most must match
    assert np.median(diffs) < 0.05 and np.mean(np.array(diffs) < 0.5) > 0.9


def test_missing_ratio_is_filled_on_the_weak_side(setup):
    calib = setup[0]
    full = {2025: {r: calib["params"]["centre"][r] for r in calib["params"]["ratios"]}}
    gap = {2025: {**full[2025], "TOTAL CAPITAL RATIO": None}}
    a = score_new_bank(full, calib)["latest"]["final_score"]
    b = score_new_bank(gap, calib)["latest"]["final_score"]
    assert b >= a


def test_country_cap_and_overlay(setup):
    calib = setup[0]
    yrs = {2025: {r: calib["params"]["centre"][r] for r in calib["params"]["ratios"]}}
    capped = score_new_bank(yrs, calib, country_score=10)["latest"]["final_score"]
    assert capped >= 8
    over = score_new_bank(yrs, calib, country_score=10, overlay=5)["latest"]["final_score"]
    assert over <= 10 and over >= capped


@pytest.mark.skipif(shutil.which("node") is None, reason="node not installed")
def test_browser_tool_gives_the_same_result(setup, tmp_path):
    calib = setup[0]
    rng = np.random.default_rng(0)
    nb = calib["params"]["new_bank"]
    cases = []
    for _ in range(50):
        yrs = {y: {r: (None if rng.random() < 0.1 else float(rng.uniform(nb[r]["p01"], nb[r]["p99"])))
                   for r in calib["params"]["ratios"] if r != "ROAA VOLATILITY 3Y"} for y in (2023, 2024, 2025)}
        cases.append((yrs, int(rng.integers(1, 11))))
    py = [score_new_bank(y, calib, country_score=c, sovereign_rating="BBB", parent_rating="A",
                         support_level="strategic", assets_share=0.12)["latest"] for y, c in cases]
    f = tmp_path / "in.json"
    json.dump({"calib": calib, "cases": [{"years": {str(k): v for k, v in y.items()}, "c": c} for y, c in cases]},
              open(f, "w"))
    js = ("const T=require(%r);const d=require(%r);console.log(JSON.stringify(d.cases.map(x=>"
          "T.score(x.years,d.calib,{countryScore:x.c,sovereignRating:'BBB',parentRating:'A',"
          "supportLevel:'strategic',assetsShare:0.12}).latest.final_score)))"
          % (str(ROOT / "tool/camels_tool.js"), str(f)))
    got = json.loads(subprocess.run(["node", "-e", js], capture_output=True, text=True, check=True).stdout)
    assert all(abs(p["final_score"] - round(g, 2)) < 0.011 for p, g in zip(py, got))
