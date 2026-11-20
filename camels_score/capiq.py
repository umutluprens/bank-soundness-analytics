"""
Loader for the 2023 S&P Capital IQ exports (CAMELS_20XX.xlsx + Data_Management_2.xlsx + BICRA.xlsx).

Builds the bank-year panel from the RAW files so that genuine gaps stay missing.
merged_data.xlsx from 2023 is already imputed (e.g. every Azerbaijani bank in 2010 shows the
same NIM and LCR), so it should not be used as input for a new calibration.

Management items (Data_Management_2.xlsx, Sheet1, one block of 12 years per item):
  273925  Operating income (total operating revenue before expenses)
  279005  Operating expense
  278992  Interest expense
  278788  Loan loss reserve (stock)
  SP_TOTAL_ASSETS
"""
from pathlib import Path
import numpy as np
import pandas as pd

RAW_MAP = {
    "SP_ENTITY_NAME": "BANK NAME", "SP_ENTITY_ID": "ID", "MI_INDUSTRY_CLASSIFICATION": "TYPE",
    "SP_COUNTRY_NAME": "COUNTRY", "SP_COUNTRY_CODE": "CCODE", "SP_GEOGRAPHY": "GEOGRAPHY",
    "SNL_TOTAL_CAPITAL_RATIO": "TOTAL CAPITAL RATIO",
    "SNL_TIER_1_RATIO": "TIER1 RATIO",
    "SNL_PROBLEM_LOANS_TO_TANG_EQUITY_RESERVES": "TEXAS RATIO",
    "SNL_PROBLEM_LOANS_TO_CUSTOMER_LOANS": "PROBLEM LOANS RATIO",
    "SP_LLR_PROBLEM_LOANS": "LOAN LOSS RESERVE TO PROBLEM LOANS",
    "SNL_NIM": "NET INTEREST MARGIN",
    "ROAA": "ROAA", "ROAE": "ROAE",
    "SNL_LIQUID_ASSETS_TO_TOTAL_DEP_BORROW": "LIQUID ASSETS/ TOTAL DEPOSITS & BORROWINGS",
    "SNL_DEBT_TO_EQUITY": "TOTAL DEBT/ TOTAL EQUITY",
    "SNL_LIQUIDITY_COV_RATIO": "LIQUIDITY COVERAGE RATIO",
    "SNL_BASIC_BV_PER_SHARE_GROWTH": "BOOKVALUE PER SHARE GROWTH",
}
MGMT_MAP = {"273925": "OPERATING INCOME", "279005": "OPERATING EXPENSE",
            "278992": "INTEREST EXPENSE", "278788": "LOAN LOSS RESERVE",
            "SP_TOTAL_ASSETS": "TOTAL ASSETS"}


def _num(s):
    return pd.to_numeric(s.replace({"NM": np.nan, "NA": np.nan}), errors="coerce")


def load_camels_years(folder, years=range(2010, 2022)):
    # Column headers carry export suffixes that change by year (SNL_TOTAL_CAPITAL_RATIO7,
    # 27377078 for ROAA in 2010, ...). The column ORDER is the same in every file, so map by position.
    names = list(RAW_MAP.values())
    order = names[:6] + names[6:]
    frames = []
    for y in years:
        d = pd.read_excel(Path(folder) / f"CAMELS_{y}.xlsx")
        if d.shape[1] != 19:
            raise ValueError(f"CAMELS_{y}.xlsx: expected 19 columns, found {d.shape[1]}")
        d.columns = [order[0], "YEAR"] + order[1:]
        d["YEAR"] = y
        frames.append(d)
    df = pd.concat(frames, ignore_index=True)
    for c in RAW_MAP.values():
        if c not in ("BANK NAME", "ID", "TYPE", "COUNTRY", "CCODE", "GEOGRAPHY"):
            df[c] = _num(df[c])
    return df


def load_management(path):
    raw = pd.read_excel(path, sheet_name="Sheet1", header=None)
    items = raw.iloc[2].astype(str).str.replace(r"\.0$", "", regex=True)
    fys = raw.iloc[3]
    body = raw.iloc[4:].reset_index(drop=True)
    out = body.iloc[:, [2]].copy()
    out.columns = ["ID"]
    long = []
    for j in range(3, raw.shape[1]):
        item, fy = items[j], fys[j]
        if item not in MGMT_MAP or not isinstance(fy, str):
            continue
        long.append(pd.DataFrame({"ID": body.iloc[:, 2], "YEAR": int(fy.replace("FY", "")),
                                  "ITEM": MGMT_MAP[item], "VALUE": _num(body.iloc[:, j])}))
    m = pd.concat(long).pivot_table(index=["ID", "YEAR"], columns="ITEM", values="VALUE",
                                    aggfunc="first").reset_index()
    m["ID"] = pd.to_numeric(m["ID"], errors="coerce")
    return m


def add_management_ratios(df):
    """Management and size ratios, built so that every input is a flow over a flow or a flow over a stock."""
    df = df.copy()
    ta = df["TOTAL ASSETS"].where(df["TOTAL ASSETS"] > 0)
    oi = df["OPERATING INCOME"]
    df["OPERATING RETURN ON ASSETS"] = oi / ta * 100
    df["COST TO INCOME RATIO"] = (df["OPERATING EXPENSE"] / oi.where(oi > 0)) * 100
    # Legacy 2023 formula, reproduced for comparison only (mixes a stock and a flow)
    den = (oi - df["LOAN LOSS RESERVE"])
    df["NON-OPERATING EXPENSE RATIO"] = ((df["OPERATING EXPENSE"] - df["INTEREST EXPENSE"])
                                         / den.where(den != 0)) * 100
    df["LOG TOTAL ASSETS"] = np.log(ta)
    return df


def load_bicra(path):
    b = pd.read_excel(path)
    return b[["COUNTRY", "YEAR", "BICRA"]]


def build_panel(data_folder):
    """Raw panel: one row per bank-year, ratios unimputed, BICRA attached."""
    f = Path(data_folder)
    df = load_camels_years(f)
    df = df.merge(load_management(f / "Data_Management_2.xlsx"), on=["ID", "YEAR"], how="left")
    df = add_management_ratios(df)
    df = df.merge(load_bicra(f / "BICRA.xlsx"), on=["COUNTRY", "YEAR"], how="left")
    return df
