"""EBA transparency loader: item mapping, ratio arithmetic and panel extension."""
import numpy as np
import pandas as pd

from camels_score import eba


def _write(folder, exercise, rows, comma=False):
    d = pd.DataFrame(rows, columns=["LEI_Code", "Period", "Item", "ASSETS_FV", "ASSETS_Stages",
                                    "Exposure", "Financial_instruments", "Amount", "n_quarters"])
    d["Label"] = "x"
    if comma:
        d["Amount"] = d["Amount"].map(lambda v: f"{v:,.4f}")
    (folder / exercise).mkdir(parents=True, exist_ok=True)
    d.to_csv(folder / exercise / "tr_oth.csv", index=False, encoding="latin-1")


def _bank(lei, period, prefix, scale=1.0, nq=4):
    p = prefix * 100000
    r = lambda code, amt, st=0, ex=0, fi=0, fv=0: [lei, period, p + code, fv, st, ex, fi, amt, nq]
    return [
        r(20142, 0.18), r(20141, 0.16), r(20140, 0.15), r(20905, 0.06), r(20138, 400 * scale),
        r(20301, 30.0), r(20304, 10.0), r(20316, 40.0), r(20317, 18.0), r(20318, 2.0),
        r(20326, 3.0), r(20335, 10.0 * nq / 4), r(21010, 1000 * scale), r(21216, 80.0), r(20110, -5.0),
        r(21002, 50.0), r(21002, 999.0, fv=1),                       # fair value level row must be ignored
        r(21019, 560.0, st=1), r(21019, 30.0, st=2), r(21019, 10.0, st=3),
        r(21029, -1.0, st=1), r(21029, -2.0, st=2), r(21029, -4.0, st=3),
        r(21018, 100.0, st=1),
        r(21215, 300.0, ex=401, fi=30), r(21215, 200.0, ex=301, fi=30), r(21215, 90.0, ex=201, fi=30),
        r(21215, 120.0, fi=40), r(21215, 900.0),
    ]


def test_ratios_from_items(tmp_path):
    _write(tmp_path, "2023", _bank("L" * 20, 202212, 23) + _bank("L" * 20, 202206, 23))
    _write(tmp_path, "2024", _bank("L" * 20, 202312, 24, scale=1.1))
    r = eba.build_ratios(eba.load_items(str(tmp_path))).set_index("YEAR")
    assert list(r.index) == [2022, 2023]                              # June dates dropped
    a = r.loc[2022]
    assert a["TOTAL CAPITAL RATIO"] == 18.0 and a["LEVERAGE RATIO"] == 6.0
    assert np.isclose(a["PROBLEM LOANS RATIO"], 100 * 10 / 600)
    assert np.isclose(a["STAGE 2 LOANS RATIO"], 5.0)
    assert np.isclose(a["LOAN LOSS RESERVE TO PROBLEM LOANS"], 70.0)
    assert np.isclose(a["TEXAS RATIO"], 100 * 10 / (80 - 5 + 7))
    assert np.isclose(a["COST TO INCOME RATIO"], 50.0)
    assert np.isclose(a["ROAA"], 1.0)                                 # first year: year-end assets
    assert np.isclose(a["LOANS / DEPOSITS"], 120.0)
    assert np.isclose(a["TOTAL DEBT/ TOTAL EQUITY"], 1.5)
    assert np.isclose(a["SECURITIES / TOTAL ASSETS"], 15.0)
    assert np.isclose(r.loc[2023, "ROAA"], 100 * 10 / 1050)           # average of two year-ends
    assert np.isclose(r.loc[2023, "LOAN GROWTH"], 0.0)


def test_thousands_separator_and_annualising(tmp_path):
    _write(tmp_path, "2019", _bank("M" * 20, 201812, 19, scale=5.0, nq=2), comma=True)
    r = eba.build_ratios(eba.load_items(str(tmp_path))).iloc[0]
    assert np.isclose(r["TOTAL ASSETS"], 5000.0)
    assert np.isclose(r["ROAA"], 100 * 5 * 2 / 5000)                  # half-year profit doubled


def test_extend_panel(tmp_path):
    lei = "N" * 20
    _write(tmp_path, "2022", _bank(lei, 202112, 22))
    _write(tmp_path, "2023", _bank(lei, 202212, 23))
    m = tmp_path / "map.csv"
    pd.DataFrame([{"LEI": lei, "ID": 7, "PANEL_NAME": "Bank Seven", "MATCH": "name"}]).to_csv(m, index=False)
    liq = "LIQUID ASSETS/ TOTAL DEPOSITS & BORROWINGS"
    panel = pd.DataFrame({"ID": [7, 7, 8], "YEAR": [2020, 2021, 2021], "BANK NAME": ["Bank Seven"] * 2 + ["Other"],
                          "COUNTRY": ["Spain"] * 3, "BICRA": [4, 4, 4], "ROAA": [0.5, 0.6, 0.2],
                          "TOTAL CAPITAL RATIO": [15.0, 16.0, 14.0], liq: [22.0, 25.0, 30.0],
                          "BOOKVALUE PER SHARE GROWTH": [3.0, 5.0, 1.0], "TOTAL ASSETS": [1e6, 1e6, 1e6]})
    out = eba.extend_panel(panel, str(tmp_path), str(m), calib_end=2021)
    new = out[out["DATA_SOURCE"] == "EBA"]
    assert list(new["YEAR"]) == [2022] and list(new["ID"]) == [7]     # only years after the panel
    row = new.iloc[0]
    assert row["BANK NAME"] == "Bank Seven" and row["BICRA"] == 4
    assert row[liq] == 25.0 and liq in row["CARRIED_RATIOS"]          # own last value
    assert row["BOOKVALUE PER SHARE GROWTH"] == 3.0                   # panel median
    assert np.isclose(row["TOTAL ASSETS"], 1000 * eba.EURUSD[2022] * 1000)
    old = out[(out["ID"] == 7) & (out["YEAR"] == 2021)].iloc[0]
    assert old["TOTAL CAPITAL RATIO"] == 16.0 and old["CET1 RATIO"] == 15.0   # panel kept, new ratio added
