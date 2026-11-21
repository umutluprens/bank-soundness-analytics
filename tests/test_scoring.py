import numpy as np
import pandas as pd
import pytest

from camels_score.data import prepare, impute_penalised
from camels_score.scoring import CamelsScorer
from camels_score.synthetic import make_panel
from camels_score import validation as v
from camels_score.ratios import REGISTRY, PILLAR_WEIGHTS


@pytest.fixture(scope="module")
def panel():
    raw, events = make_panel(n_banks=250, seed=3)
    df, ratios = prepare(raw)
    return df, ratios, events


def test_weights_sum_to_one():
    assert abs(sum(PILLAR_WEIGHTS.values()) - 1) < 1e-9


def test_every_pillar_has_ratios():
    pillars = {r.pillar for r in REGISTRY.values()}
    assert pillars == set("CAMELS")


def test_trailing_space_column_is_recognised(panel):
    _, ratios, _ = panel
    assert "LIQUID ASSETS/ TOTAL DEPOSITS & BORROWINGS" in ratios


def test_nm_and_out_of_bounds_removed(panel):
    df, _, _ = panel
    assert df["TOTAL CAPITAL RATIO"].dtype.kind == "f"
    assert df["TOTAL CAPITAL RATIO"].between(0, 100).all()


def test_no_missing_after_imputation(panel):
    df, ratios, _ = panel
    assert df[ratios].notna().all().all()


def test_penalty_is_on_the_weak_side():
    # Texas ratio: higher = weaker, so a missing value must be filled ABOVE the median
    d = pd.DataFrame({"COUNTRY": ["X"] * 11, "YEAR": [2020] * 11,
                      "TEXAS RATIO": [10, 20, 30, 40, 50, 60, 70, 80, 90, 100, np.nan],
                      "TOTAL CAPITAL RATIO": [10, 11, 12, 13, 14, 15, 16, 17, 18, 19, np.nan]})
    out = impute_penalised(d, ["TEXAS RATIO", "TOTAL CAPITAL RATIO"])
    assert out.loc[10, "TEXAS RATIO"] > 55
    assert out.loc[10, "TOTAL CAPITAL RATIO"] < 14.5


def test_direction_better_bank_gets_better_grade(panel):
    df, ratios, _ = panel
    s = CamelsScorer().fit(df, ratios)
    a = df.iloc[[0]].copy()
    b = a.copy()
    b["TOTAL CAPITAL RATIO"] += 8          # more capital
    b["TEXAS RATIO"] -= 20                 # lower Texas ratio
    b["PROBLEM LOANS RATIO"] = max(0.0, float(a["PROBLEM LOANS RATIO"].iloc[0]) - 3)
    ga, gb = s.transform(a)["COMPOSITE_Z"].iloc[0], s.transform(b)["COMPOSITE_Z"].iloc[0]
    assert gb > ga


def test_grades_in_range_and_frozen(panel, tmp_path):
    df, ratios, _ = panel
    s = CamelsScorer().fit(df[df.YEAR <= 2016], ratios)
    out = s.transform(df)
    assert out["FINAL_GRADE"].between(1, 10).all()
    p = tmp_path / "cal.json"
    s.save(p)
    out2 = CamelsScorer.load(p).transform(df)
    assert (out["FINAL_GRADE"] == out2["FINAL_GRADE"]).all()


def test_oe_cap(panel):
    df, ratios, _ = panel
    out = CamelsScorer(max_uplift=2).fit_transform(df, ratios)
    unsupported = out["PARENT_SUPPORT"] == 0
    assert (out.loc[unsupported, "FINAL_GRADE"]
            >= out.loc[unsupported, "BICRA"] - 2).all()


def test_label_is_forward_looking(panel):
    df, ratios, _ = panel
    lab = v.forward_proxy_label(df)
    last_year = lab.groupby("ID")["YEAR"].transform("max") == lab["YEAR"]
    assert lab.loc[last_year, "DISTRESS_FWD"].isna().all()


def test_grade_rank_orders_distress(panel):
    df, ratios, events = panel
    out = CamelsScorer().fit_transform(df, ratios)
    out = v.event_label(out, events)
    assert v.discrimination(out)["auc"] > 0.65


# ---------------------------------------------------------------- group support
from camels_score.group import apply_group_support, rating_to_grade
from camels_score.scoring import grade_label


def _two_banks(own_sub, own_parent, level, oe_sub=3.0, oe_parent=3.0):
    return pd.DataFrame({
        "ID": [1, 2], "YEAR": [2020, 2020], "OWN_SCORE": [own_sub, own_parent],
        "OE_SCORE_USED": [oe_sub, oe_parent], "SUPPORT_LEVEL": [level, "none"],
        "PARENT_ID": [2, np.nan], "PARENT_GRADE": [np.nan, np.nan]})


def test_support_closes_probability_share_of_gap():
    out = apply_group_support(_two_banks(8.0, 4.0, "strategic", oe_sub=3))
    assert out.loc[0, "FINAL_SCORE"] == 6.6                # 8 - 0.35 x 4
    out = apply_group_support(_two_banks(8.0, 4.0, "core", oe_sub=3))
    assert out.loc[0, "FINAL_SCORE"] == 6.0                # 8 - 0.50 x 4


def test_support_probability_never_above_half():
    out = apply_group_support(_two_banks(10.0, 1.0, "core", oe_sub=1))
    assert out.loc[0, "FINAL_SCORE"] == 5.5                # at most half the gap


def test_country_cap_cannot_be_breached_by_support():
    # weak country (score 8 -> cap 6): parent at 2 cannot pull the subsidiary below 6
    out = apply_group_support(_two_banks(8.0, 2.0, "core", oe_sub=8))
    assert out.loc[0, "FINAL_SCORE"] == 6.0
    assert out.loc[0, "FINAL_SCORE"] > 2.0                  # never as good as the parent


def test_weaker_parent_does_not_pull_down():
    out = apply_group_support(_two_banks(2.0, 8.0, "strategic"))
    assert out.loc[0, "GROUP_ADJ"] == 0


def test_no_support_level_means_no_change():
    out = apply_group_support(_two_banks(8.0, 2.0, "none"))
    assert out.loc[0, "GROUP_ADJ"] == 0


def test_sub_notch_effect_is_visible_in_label():
    out = apply_group_support(_two_banks(6.0, 5.0, "strategic"))   # 6.0 -> 5.65
    assert out.loc[0, "FINAL_GRADE"] == 6 and out.loc[0, "GRADE_LABEL"] == "6+"


def test_external_parent_grade_overrides_panel():
    d = _two_banks(8.0, 4.0, "strategic", oe_sub=3)
    d.loc[0, "PARENT_GRADE"] = rating_to_grade("A")     # 2
    out = apply_group_support(d)
    assert out.loc[0, "FINAL_SCORE"] == 5.9                # 8 - 0.35 x 6


# ---- v0.6 ---------------------------------------------------------------------------------
from camels_score.data import through_cycle, merge_extra_ratios
from camels_score.overlays import apply_overlays


def test_through_cycle_takes_weaker_of_latest_and_average():
    d = pd.DataFrame({"ID": [1, 1, 1], "YEAR": [2018, 2019, 2020],
                      "PROBLEM LOANS RATIO": [9.0, 6.0, 3.0],     # lower is better
                      "ROAA": [-1.0, 0.5, 1.5]})                   # higher is better
    out = through_cycle(d, ["PROBLEM LOANS RATIO", "ROAA"])
    assert out.loc[2, "PROBLEM LOANS RATIO"] == 6.0     # avg 6 is worse than latest 3
    assert out.loc[2, "ROAA"] == pytest.approx(1 / 3)  # avg 0.33 is worse than latest 1.5
    assert out.loc[0, "PROBLEM LOANS RATIO"] == 9.0     # one year only: latest value


def test_through_cycle_keeps_a_deterioration():
    d = pd.DataFrame({"ID": [1, 1], "YEAR": [2019, 2020], "PROBLEM LOANS RATIO": [3.0, 9.0]})
    assert through_cycle(d, ["PROBLEM LOANS RATIO"]).loc[1, "PROBLEM LOANS RATIO"] == 9.0


def test_large_subsidiary_gets_less_support():
    d = _two_banks(8.0, 4.0, "core", oe_sub=3)
    d["TOTAL ASSETS"] = [30.0, 100.0]                    # 30% of the parent -> factor 0.5
    out = apply_group_support(d)
    assert out.loc[0, "SUPPORT_PROB"] == 0.25 and out.loc[0, "FINAL_SCORE"] == 7.0


def test_parent_stress_removes_support_without_penalty():
    d = _two_banks(8.0, 4.0, "core", oe_sub=3)
    d["STRESS_FROM"] = [2014, np.nan]
    out = apply_group_support(d)
    assert out.loc[0, "GROUP_ADJ"] == 0 and bool(out.loc[0, "PARENT_STRESS"])


def test_sovereign_caps_support():
    d = _two_banks(8.0, 2.0, "core", oe_sub=1)           # support alone would give 5.0
    d["SOVEREIGN_GRADE"] = [6.0, np.nan]
    assert apply_group_support(d).loc[0, "FINAL_SCORE"] == 6.0


def test_weak_parent_flag():
    out = apply_group_support(_two_banks(4.0, 6.0, "strategic"))
    assert bool(out.loc[0, "WEAK_PARENT"])


def _scored_one():
    return pd.DataFrame({"ID": [1, 1], "YEAR": [2015, 2016], "FINAL_SCORE": [5.0, 9.5]})


def test_overlay_total_capped_at_two_notches():
    ov = pd.DataFrame({"ID": [1, 1], "FROM_YEAR": [2015, 2015], "TO_YEAR": [2016, 2016],
                       "FACTOR": ["governance", "growth"], "NOTCHES": [2, 1],
                       "REASON": ["x", "y"], "ANALYST": ["a", "a"], "DATE": [None, None]})
    out = apply_overlays(_scored_one(), ov)
    assert out.loc[0, "FINAL_SCORE"] == 7.0 and out.loc[1, "FINAL_SCORE"] == 10.0


def test_overlay_is_point_in_time():
    ov = pd.DataFrame({"ID": [1], "FROM_YEAR": [2015], "TO_YEAR": [2016], "FACTOR": ["governance"],
                       "NOTCHES": [1], "REASON": ["x"], "ANALYST": ["a"], "DATE": ["2017-03-01"]})
    out = apply_overlays(_scored_one(), ov)
    assert out.loc[0, "OVERLAY_NOTCHES"] == 0          # decided in 2017: not known for 2015
    assert out.loc[1, "OVERLAY_NOTCHES"] == 1          # known when 2016 accounts reviewed


def test_extra_ratios_are_merged(tmp_path):
    base = pd.DataFrame({"ID": [1], "YEAR": [2020], "ROAA": [1.0]})
    f = tmp_path / "x.csv"
    pd.DataFrame({"ID": [1], "YEAR": [2020], "CET1 RATIO": [14.0], "FOO": [1]}).to_csv(f, index=False)
    out = merge_extra_ratios(base, f)
    assert out.loc[0, "CET1 RATIO"] == 14.0 and "FOO" not in out


def test_forecast_pairs_and_walk_forward_use_only_earlier_years():
    from camels_score.synthetic import make_panel
    from camels_score.data import prepare
    from camels_score.scoring import CamelsScorer
    from camels_score.forecast import build_pairs, walk_forward, evaluate
    raw, _ = make_panel(n_banks=60)
    df, ratios = prepare(raw)
    sc = CamelsScorer().fit(df, ratios)
    s = sc.transform(df)
    p = build_pairs(s, ratios)
    row = p.iloc[0]
    nxt = s[(s.ID == row.ID) & (s.YEAR == row.YEAR + 1)]["OWN_SCORE"].iloc[0]
    assert abs(row["NEXT_OWN_SCORE"] - nxt) < 1e-9
    fc = walk_forward(s, ratios, sc, first_target=2016, last_target=2017, ratio_route=False)
    assert set(fc["YEAR"] + 1) == {2016, 2017}
    rep, _ = evaluate(fc)
    assert rep["F_DIRECT"]["mae_score"] > 0
