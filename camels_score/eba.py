"""EBA EU-wide transparency exercise: read the "other templates" file (tr_oth) and build ratios.

The EBA publishes one csv per exercise. Each row is one bank (LEI), one reference date, one item.
Item codes carry the exercise year in the first two digits (1920142, 2420142, ...); the last five
digits identify the item and are stable across exercises, so the mapping below uses them.

Amounts are in EUR million; ratio items are fractions (0.18 = 18%). Profit and loss items are
cumulative over `n_quarters` of the bank's financial year and are annualised here.

Only December reference dates are used, to line up with the annual panel.

Source: https://www.eba.europa.eu/risk-and-data-analysis/data/data-analytics-tools (open data).
"""
from __future__ import annotations

import glob
import os

import numpy as np
import pandas as pd

# last five digits of the EBA item code -> short name
ITEMS = {
    20101: "own_funds", 20102: "cet1", 20110: "intangibles_deduction", 20133: "tier1",
    20138: "rwa", 20140: "cet1_ratio", 20141: "tier1_ratio", 20142: "total_capital_ratio",
    20903: "leverage_exposure", 20905: "leverage_ratio",
    20301: "interest_income", 20304: "interest_expense", 20309: "net_fees",
    20316: "operating_income", 20317: "admin_expenses", 20318: "depreciation",
    20319: "provisions", 20324: "impairment_financial", 20326: "impairment_amortised_cost",
    20332: "profit_before_tax", 20335: "net_profit",
    21001: "cash", 21002: "trading_assets", 21010: "total_assets",
    21214: "total_liabilities", 21216: "total_equity",
}
FLOW = {"interest_income", "interest_expense", "net_fees", "operating_income", "admin_expenses",
        "depreciation", "provisions", "impairment_financial", "impairment_amortised_cost",
        "profit_before_tax", "net_profit"}
# items broken down by IFRS 9 stage (ASSETS_Stages 1, 2, 3)
STAGED = {21016: "debt_fvoci", 21017: "loans_fvoci", 21018: "debt_ac", 21019: "loans_ac",
          21027: "imp_loans_fvoci", 21029: "imp_loans_ac"}
LIABILITY_BREAKDOWN = 21215          # by Financial_instruments and Exposure (counterparty sector)
CUSTOMER_SECTORS = {102, 202, 301, 401}   # governments, other financials, non-financials, households

# How each product ratio is built from the EBA items. quality: exact / close / proxy.
RATIO_MAP = [
    ("TOTAL CAPITAL RATIO", "exact", "reported ratio, transitional"),
    ("TIER1 RATIO", "exact", "reported ratio, transitional"),
    ("CET1 RATIO", "exact", "reported ratio, transitional"),
    ("LEVERAGE RATIO", "exact", "reported ratio, transitional Tier 1"),
    ("RWA DENSITY", "exact", "total risk exposure amount / total assets"),
    ("PROBLEM LOANS RATIO", "close", "stage 3 loans / gross loans (amortised cost and FVOCI); "
                                     "loans include loans to banks"),
    ("STAGE 2 LOANS RATIO", "exact", "stage 2 loans / gross loans"),
    ("LOAN LOSS RESERVE TO PROBLEM LOANS", "close", "accumulated impairment on loans, all stages / stage 3 loans"),
    ("TEXAS RATIO", "close", "stage 3 loans / (equity - intangibles + accumulated impairment); "
                             "foreclosed assets not included"),
    ("COST OF RISK", "close", "impairment on assets at amortised cost / average gross loans"),
    ("LOAN GROWTH", "exact", "change in gross loans, %"),
    ("ROAA", "exact", "profit for the year / average total assets"),
    ("ROAE", "close", "profit for the year / average total equity (equity from June 2020; "
                      "assets less liabilities for December 2019)"),
    ("NET INTEREST MARGIN", "proxy", "net interest income / average total assets (not earning assets)"),
    ("COST TO INCOME RATIO", "exact", "(administrative expenses + depreciation) / operating income"),
    ("OPERATING RETURN ON ASSETS", "proxy", "total operating income / total assets; the panel uses a wider revenue line"),
    ("NON-INTEREST INCOME SHARE", "exact", "1 - net interest income / operating income"),
    ("PRE-PROVISION PROFIT / RWA", "exact", "(operating income - costs) / RWA"),
    ("TOTAL DEBT/ TOTAL EQUITY", "proxy", "debt securities issued / total equity (multiple); other borrowings not included"),
    ("LOANS / DEPOSITS", "close", "gross loans / customer deposits"),
    ("CUSTOMER DEPOSITS / TOTAL FUNDING", "close", "customer deposits / financial liabilities"),
    ("SECURITIES / TOTAL ASSETS", "close", "debt securities at amortised cost and FVOCI + trading assets / total assets"),
]
NOT_AVAILABLE = ["LIQUIDITY COVERAGE RATIO", "NET STABLE FUNDING RATIO",
                 "LIQUID ASSETS/ TOTAL DEPOSITS & BORROWINGS", "ASSET ENCUMBRANCE RATIO",
                 "FORBORNE LOANS RATIO", "BOOKVALUE PER SHARE GROWTH", "TANGIBLE EQUITY / TANGIBLE ASSETS",
                 "EVE SENSITIVITY / TIER1", "NII SENSITIVITY", "FX LOANS / TOTAL LOANS",
                 "NET OPEN FX POSITION / CAPITAL", "UNREALISED SECURITIES LOSSES / CET1"]


def _read(path: str) -> pd.DataFrame:
    d = pd.read_csv(path, encoding="latin-1", low_memory=False)
    d.columns = [c.strip() for c in d.columns]
    for c in ("ASSETS_FV", "ASSETS_Stages", "Exposure", "Financial_instruments", "n_quarters"):
        if c not in d.columns:
            d[c] = 0
        d[c] = pd.to_numeric(d[c], errors="coerce").fillna(0).astype(int)
    d = d[d["Period"] % 100 == 12].copy()
    d["YEAR"] = d["Period"] // 100
    d["CODE"] = d["Item"] % 100000
    # the 2019 file writes amounts with thousands separators
    d["Amount"] = pd.to_numeric(d["Amount"].astype(str).str.replace(",", "", regex=False), errors="coerce")
    d = d[d["ASSETS_FV"] == 0]                      # drop the fair value level breakdown
    d["FILE"] = os.path.basename(os.path.dirname(path))
    return d[["LEI_Code", "YEAR", "CODE", "ASSETS_Stages", "Exposure", "Financial_instruments",
              "n_quarters", "Amount", "FILE"]]


def load_items(folder: str) -> pd.DataFrame:
    """One row per bank and December year-end, one column per item (EUR million / fractions)."""
    files = sorted(glob.glob(os.path.join(folder, "*", "tr_oth*.csv")))
    if not files:
        raise FileNotFoundError(f"no tr_oth*.csv under {folder}")
    d = pd.concat([_read(f) for f in files], ignore_index=True)
    key = ["LEI_Code", "YEAR"]

    def last(x):          # if a date appears in two exercises keep the later file
        return x.sort_values("FILE").groupby(key + [c for c in x.columns if c == "K"]).tail(1)

    simple = d[d.CODE.isin(ITEMS) & (d.ASSETS_Stages == 0) & (d.Exposure == 0)
               & (d.Financial_instruments == 0)].copy()
    simple["K"] = simple.CODE.map(ITEMS)
    q = simple[simple.K == "net_profit"].set_index(key).n_quarters
    q = q[~q.index.duplicated(keep="last")]
    wide = last(simple).pivot_table(index=key, columns="K", values="Amount", aggfunc="last")

    st = d[d.CODE.isin(STAGED) & d.ASSETS_Stages.isin([1, 2, 3])].copy()
    st["K"] = st.CODE.map(STAGED) + "_s" + st.ASSETS_Stages.astype(str)
    wide = wide.join(last(st).pivot_table(index=key, columns="K", values="Amount", aggfunc="last"))

    li = d[d.CODE == LIABILITY_BREAKDOWN].copy()
    li["K"] = np.select(
        [(li.Financial_instruments == 30) & li.Exposure.isin(CUSTOMER_SECTORS),
         (li.Financial_instruments == 30) & (li.Exposure > 0),
         (li.Financial_instruments == 40) & (li.Exposure == 0),
         (li.Financial_instruments == 0) & (li.Exposure == 0)],
        ["customer_deposits", "bank_deposits", "debt_issued", "financial_liabilities"], default="")
    li = li[li.K != ""]
    li = li[li.FILE == li.groupby(key).FILE.transform("max")]
    wide = wide.join(li.pivot_table(index=key, columns="K", values="Amount", aggfunc="sum", min_count=1))

    wide["n_quarters"] = q.reindex(wide.index)
    return wide.reset_index().rename(columns={"LEI_Code": "LEI"})


def build_ratios(items: pd.DataFrame) -> pd.DataFrame:
    """Product ratios (in percent, same units as the panel) from the item table."""
    x = items.sort_values(["LEI", "YEAR"]).copy()
    g = lambda c: x[c] if c in x.columns else pd.Series(np.nan, index=x.index)
    s = lambda *cols: sum(g(c).fillna(0) for c in cols).where(pd.concat([g(c) for c in cols], axis=1).notna().any(axis=1))

    nq = g("n_quarters").where(g("n_quarters") > 0)
    ann = 4.0 / nq                                  # annualise profit and loss items
    loans = s(*[f"loans_{p}_s{i}" for p in ("ac", "fvoci") for i in (1, 2, 3)])
    stage3 = s("loans_ac_s3", "loans_fvoci_s3")
    stage2 = s("loans_ac_s2", "loans_fvoci_s2")
    # accumulated impairment is reported as a negative number in some exercises
    reserve = s(*[f"imp_loans_{p}_s{i}" for p in ("ac", "fvoci") for i in (1, 2, 3)]).abs()
    securities = s(*[f"debt_{p}_s{i}" for p in ("ac", "fvoci") for i in (1, 2, 3)])
    equity = g("total_equity").fillna(g("total_assets") - g("total_liabilities"))
    tangible = equity - g("intangibles_deduction").abs().fillna(0)

    def avg(v):                                     # average of this and previous year-end
        prev = v.groupby(x["LEI"]).shift(1)
        consecutive = x["YEAR"] - x.groupby("LEI")["YEAR"].shift(1) == 1
        return ((v + prev) / 2).where(consecutive & prev.notna(), v)

    nii = g("interest_income") - g("interest_expense")
    costs = g("admin_expenses") + g("depreciation")
    ppp = (g("operating_income") - costs) * ann
    pos = lambda v: v.where(v > 0)
    # loan ratios are meaningless for banks with almost no loan book (custodians, clearing houses)
    loans = loans.where(loans >= 0.01 * g("total_assets"))
    stage3 = stage3.where(loans.notna())
    stage3_min = stage3.where(stage3 >= 1.0)        # coverage needs a real stock of stage 3 loans

    r = pd.DataFrame({"LEI": x["LEI"], "YEAR": x["YEAR"], "TOTAL ASSETS": g("total_assets")})
    r["TOTAL CAPITAL RATIO"] = 100 * g("total_capital_ratio")
    r["TIER1 RATIO"] = 100 * g("tier1_ratio")
    r["CET1 RATIO"] = 100 * g("cet1_ratio")
    r["LEVERAGE RATIO"] = 100 * g("leverage_ratio")
    r["RWA DENSITY"] = 100 * g("rwa") / pos(g("total_assets"))
    r["PROBLEM LOANS RATIO"] = 100 * stage3 / pos(loans)
    r["STAGE 2 LOANS RATIO"] = 100 * stage2 / pos(loans)
    r["LOAN LOSS RESERVE TO PROBLEM LOANS"] = 100 * reserve / stage3_min
    r["TEXAS RATIO"] = 100 * stage3 / pos(tangible + reserve)
    r["COST OF RISK"] = 100 * g("impairment_amortised_cost") * ann / pos(avg(loans))
    prev_loans = loans.groupby(x["LEI"]).shift(1).where(x["YEAR"] - x.groupby("LEI")["YEAR"].shift(1) == 1)
    r["LOAN GROWTH"] = 100 * (loans / pos(prev_loans) - 1)
    r["ROAA"] = 100 * g("net_profit") * ann / pos(avg(g("total_assets")))
    r["ROAE"] = 100 * g("net_profit") * ann / pos(avg(equity))
    r["NET INTEREST MARGIN"] = 100 * nii * ann / pos(avg(g("total_assets")))
    r["COST TO INCOME RATIO"] = 100 * costs / pos(g("operating_income"))
    r["OPERATING RETURN ON ASSETS"] = 100 * g("operating_income") * ann / pos(g("total_assets"))
    r["NON-INTEREST INCOME SHARE"] = 100 * (1 - nii / pos(g("operating_income")))
    r["PRE-PROVISION PROFIT / RWA"] = 100 * ppp / pos(g("rwa"))
    r["TOTAL DEBT/ TOTAL EQUITY"] = g("debt_issued") / pos(equity)        # multiple, as in the panel
    r["LOANS / DEPOSITS"] = 100 * loans / pos(g("customer_deposits"))
    r["CUSTOMER DEPOSITS / TOTAL FUNDING"] = 100 * g("customer_deposits") / pos(g("financial_liabilities"))
    r["SECURITIES / TOTAL ASSETS"] = 100 * (securities + g("trading_assets").fillna(0)) / pos(g("total_assets"))
    r["LOG TOTAL ASSETS"] = np.log(pos(g("total_assets")))
    return r.replace([np.inf, -np.inf], np.nan)


def load(folder: str, bank_map: str | None = None) -> pd.DataFrame:
    """Ratios per LEI and year; with `bank_map` (data/eba_bank_map.csv) the panel ID is attached."""
    r = build_ratios(load_items(folder))
    if bank_map:
        m = pd.read_csv(bank_map)
        m = m[m["ID"].notna()][["LEI", "ID", "PANEL_NAME", "MATCH"]]
        r = r.merge(m, on="LEI", how="left")
    return r


# ---------------------------------------------------------------- extending the panel
# ECB euro reference rate (USD per EUR) on the last business day of the year. The Capital IQ
# panel holds total assets in USD thousand; EBA reports EUR million.
EURUSD = {2018: 1.1450, 2019: 1.1234, 2020: 1.2271, 2021: 1.1326, 2022: 1.0666, 2023: 1.1050, 2024: 1.0389}

# Scored ratios the EBA files cannot supply, and what the extension does about them.
#   carry   : the bank's own last reported value (liquidity moves slowly; flagged as carried)
#   neutral : the panel median of the calibration years (no information either way)
STRUCTURAL_GAPS = {"LIQUID ASSETS/ TOTAL DEPOSITS & BORROWINGS": "carry",
                   "LIQUIDITY COVERAGE RATIO": "carry",
                   "BOOKVALUE PER SHARE GROWTH": "neutral"}
CARRY_ID_COLS = ["BANK NAME", "TYPE", "COUNTRY", "CCODE", "GEOGRAPHY", "BICRA", "OE_SCORE", "PARENT_SUPPORT"]


def extend_panel(panel: pd.DataFrame, eba_folder: str, bank_map: str, calib_end: int = 2017,
                 include_approximate: bool = False) -> pd.DataFrame:
    """Add EBA bank-years after the last panel year, and EBA-only ratios for the overlap years.

    New rows exist only for banks matched in `bank_map`. Their descriptive columns (name, country,
    type, country score) are copied from the bank's last panel row. Rows carry DATA_SOURCE = "EBA".
    Back-test of this route against Capital IQ on 2018-2021: METHODOLOGY.md section 15.
    """
    p = panel.copy()
    p.columns = [str(c).strip().upper() for c in p.columns]
    p["DATA_SOURCE"] = "PANEL"
    r = load(eba_folder, bank_map)
    r = r[r["ID"].notna()].copy()
    if not include_approximate:
        r = r[r["MATCH"] != "approximate"]
    r["ID"] = r["ID"].astype(p["ID"].dtype)
    r = r.sort_values(["ID", "YEAR", "LEI"]).drop_duplicates(["ID", "YEAR"], keep="last")
    ratio_cols = [c for c, _, _ in RATIO_MAP]
    last_year = int(p["YEAR"].max())

    # 1. overlap years: add ratios the panel does not have (CET1, leverage, stage 2, ...)
    new_cols = [c for c in ratio_cols if c not in p.columns]
    if new_cols:
        p = p.merge(r[["ID", "YEAR"] + new_cols], on=["ID", "YEAR"], how="left")

    # 2. later years: new rows
    ext = r[(r["YEAR"] > last_year) & r["ID"].isin(p["ID"])].copy()
    if ext.empty:
        return p
    last = p.sort_values("YEAR").groupby("ID").tail(1).set_index("ID")
    for c in [c for c in CARRY_ID_COLS if c in p.columns]:
        ext[c] = ext["ID"].map(last[c])
    ext["TOTAL ASSETS"] = ext["TOTAL ASSETS"] * ext["YEAR"].map(EURUSD) * 1000.0
    ext["LOG TOTAL ASSETS"] = np.log(ext["TOTAL ASSETS"].where(ext["TOTAL ASSETS"] > 0))
    carried = []
    for c, how in STRUCTURAL_GAPS.items():
        if c not in p.columns:
            continue
        col = pd.to_numeric(p[c], errors="coerce")
        if how == "carry":
            own = col.groupby(p["ID"]).apply(lambda s: s.dropna().iloc[-1] if s.notna().any() else np.nan)
            ext[c] = ext["ID"].map(own)
            carried.append(c)
        else:
            ext[c] = col[p["YEAR"] <= calib_end].median()
    ext["CARRIED_RATIOS"] = ", ".join(carried)
    ext["DATA_SOURCE"] = "EBA"
    keep = [c for c in ext.columns if c in p.columns or c in ("CARRIED_RATIOS",)]
    return pd.concat([p, ext[keep]], ignore_index=True, sort=False)
