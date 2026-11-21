"""
Score a bank that is not in the panel, from up to three years of its own ratios.

The new bank is measured on the frozen v0.7 yardstick (calibration.json): the same medians,
scales, weights, decile cut-offs, country cap, loss notch and group support rule as the panel.
Two steps that need peers are replaced by values stored at calibration time:

  winsorising   panel: 1st/99th percentile of each year      new bank: of the calibration window
  missing ratio panel: weak-side quartile of country-year peers   new bank: of the calibration window

so a new bank with full data gets the same grade it would get inside the panel, and a new bank
with gaps is penalised in the same direction.

The same logic runs in the browser tool (tool/camels_tool.js). tests/test_newbank.py checks that
the two agree with each other and with the pipeline.
"""
import json
import math
import numpy as np
import pandas as pd

from .ratios import REGISTRY, GRADE_DESCRIPTOR
from .data import THROUGH_CYCLE
from .group import SUPPORT_PROB, MAX_SUPPORT_PROB, COUNTRY_GAP, ABILITY_STEPS, RATING_TO_GRADE

# What to take from an annual report for each scored ratio (all in % unless a multiple)
DEFINITIONS = {
    "TOTAL CAPITAL RATIO": "Total regulatory capital / risk-weighted assets",
    "TIER1 RATIO": "Tier 1 capital / risk-weighted assets",
    "TOTAL DEBT/ TOTAL EQUITY": "Total debt (borrowings, debt securities, subordinated debt) / total equity, multiple",
    "PROBLEM LOANS RATIO": "Problem (non-performing, Stage 3) loans / gross customer loans",
    "TEXAS RATIO": "Problem loans / (tangible equity + loan loss reserves)",
    "LOAN LOSS RESERVE TO PROBLEM LOANS": "Loan loss reserves / problem loans (NPL coverage)",
    "COST TO INCOME RATIO": "Operating expenses / total operating income",
    "OPERATING RETURN ON ASSETS": "Total operating income (before expenses and provisions) / total assets",
    "ROAA": "Net income / average total assets",
    "ROAE": "Net income / average total equity",
    "NET INTEREST MARGIN": "Net interest income / average interest-earning assets",
    "BOOKVALUE PER SHARE GROWTH": "Change in book value per share on the previous year",
    "ROAA VOLATILITY 3Y": "Calculated from three years of ROAA (standard deviation); not entered",
    "LIQUID ASSETS/ TOTAL DEPOSITS & BORROWINGS": "Cash, interbank and liquid securities / (deposits + borrowings)",
}
DERIVED = {"ROAA VOLATILITY 3Y"}


def add_new_bank_params(scorer, cleaned_ref, basis_ref):
    """Store what a single bank needs in place of its peers: pooled 1st/99th percentiles
    (winsorising) and the weak-side quartile (missing ratios) of the calibration window."""
    p = {}
    for r in scorer.params_["ratios"]:
        x = cleaned_ref[r].astype(float).dropna()
        b = basis_ref[r].astype(float).dropna()
        d = REGISTRY[r].direction
        p[r] = {"p01": float(x.quantile(0.01)), "p99": float(x.quantile(0.99)),
                "weak_fill": float(b.quantile(0.25 if d == 1 else 0.75)),
                "direction": d, "pillar": REGISTRY[r].pillar,
                "bounds": list(REGISTRY[r].bounds), "through_cycle": r in THROUGH_CYCLE,
                "definition": DEFINITIONS.get(r, REGISTRY[r].note)}
    scorer.params_["new_bank"] = p
    return scorer


def _round_half_even(x):
    return float(np.round(x))          # same rounding as pandas .round()


def _label(score):
    g = int(min(max(_round_half_even(score), 1), 10))
    frac = score - g
    return f"{g}{'+' if frac <= -1/6 else '-' if frac >= 1/6 else ''}", g


def score_new_bank(years, calib, country_score=None, sovereign_rating=None, parent_rating=None,
                   parent_score=None, support_level="none", assets_share=None,
                   parent_stress=False, overlay=0.0):
    """
    years : dict {year: {ratio name: value}}, up to three years (more are allowed; the last three
            count for the through-the-cycle rule). Values in %, as in the panel.
    calib : dict from calibration.json (or its path).
    Returns a dict with one result per year (latest last) and a step-by-step breakdown.
    """
    if isinstance(calib, str):
        with open(calib) as f:
            calib = json.load(f)
    P, cfg = calib["params"], calib["config"]
    nb = P["new_bank"]
    ratios = P["ratios"]
    yrs = sorted(int(y) for y in years)

    # 1. clean: bounds, then winsorise at the calibration window's 1st/99th percentile
    raw = {}
    for y in yrs:
        row = {}
        for r in ratios:
            v = years[y].get(r) if y in years else years[str(y)].get(r)
            v = None if v in ("", "NM", None) else float(v)
            if v is not None and (math.isnan(v)):
                v = None
            if v is not None:
                lo, hi = nb[r]["bounds"]
                if (lo is not None and v < lo) or (hi is not None and v > hi):
                    v = None
            row[r] = v
        raw[y] = row
    # derived: ROAA volatility from three consecutive years of raw ROAA (sample std)
    for i, y in enumerate(yrs):
        last3 = [raw[yy]["ROAA"] for yy in yrs[max(0, i - 2): i + 1]]
        if "ROAA VOLATILITY 3Y" in ratios:
            ok = len(last3) == 3 and all(v is not None for v in last3) and yrs[i] - yrs[max(0, i - 2)] == 2
            raw[y]["ROAA VOLATILITY 3Y"] = float(np.std(last3, ddof=1)) if ok else None
    clean = {y: {r: (None if v is None else min(max(v, nb[r]["p01"]), nb[r]["p99"]))
                 for r, v in raw[y].items()} for y in yrs}

    results = []
    for i, y in enumerate(yrs):
        steps, used, imputed = [], {}, []
        for r in ratios:
            v = clean[y][r]
            if nb[r]["through_cycle"] and v is not None:
                window = [clean[yy][r] for yy in yrs if y - 2 <= yy <= y and clean[yy][r] is not None]
                if len(window) >= 2:
                    avg = sum(window) / len(window)
                    v = min(v, avg) if nb[r]["direction"] == 1 else max(v, avg)
            if v is None:
                v = nb[r]["weak_fill"]
                imputed.append(r)
            used[r] = v
        reported = len(ratios) - len(imputed)

        # 2. oriented z, pillars, composite
        z = {}
        for r in ratios:
            d = nb[r]["direction"]
            zz = d * (used[r] - P["centre"][r]) / P["scale"][r]
            if nb[r]["pillar"] == "C" and P.get("capital_z_cap") is not None:
                zz = min(zz, P["capital_z_cap"])
            z[r] = max(-3.0, min(3.0, zz))
        pillars = {}
        for r in ratios:
            pillars.setdefault(nb[r]["pillar"], []).append(z[r])
        pillars = {p: sum(v) / len(v) for p, v in pillars.items()}
        w = {p: P["weights"].get(p, 0) for p in pillars}
        tw = sum(w.values())
        comp = sum(pillars[p] * w[p] / tw for p in pillars)

        cuts = P["composite_cuts"]
        qs = np.linspace(0, 1, cfg["n_grades"] + 1)[1:-1]
        lo = cuts[0] - (cuts[1] - cuts[0]); hi = cuts[-1] + (cuts[-1] - cuts[-2])
        pct = float(np.interp(comp, np.r_[lo, cuts, hi], np.r_[0.0, qs, 1.0]))
        standalone = min(max(10.5 - 10 * pct, 1), 10)
        steps.append(("Standalone (ratios only)", standalone))

        # 3. country anchor and cap
        score = standalone
        if country_score is not None:
            oe = min(max(float(country_score), 1), 10)
            blended = cfg["oe_weight"] * oe + (1 - cfg["oe_weight"]) * standalone
            floor = max(oe - cfg["max_uplift"], 1)
            score = max(blended, floor)
            steps.append((f"Country score {oe:g}: 15% blend, at most {cfg['max_uplift']} notches above", score))
        # 4. loss notch on through-the-cycle ROAA
        notch = 0
        if cfg.get("loss_notch"):
            notch = 2 if used["ROAA"] < -1 else 1 if used["ROAA"] < 0 else 0
            score += notch
            if notch:
                steps.append((f"Loss notch (+{notch})", score))
        own = min(max(score, 1), 10)

        # 5. group support
        parent = None
        if parent_rating:
            parent = RATING_TO_GRADE.get(parent_rating)
        elif parent_score is not None:
            parent = float(parent_score)
        sov = RATING_TO_GRADE.get(sovereign_rating) if sovereign_rating else None
        final = own
        p_used = 0.0
        if parent is not None and support_level != "none":
            p = min(SUPPORT_PROB.get(support_level, 0.0), MAX_SUPPORT_PROB)
            ability = 1.0
            if assets_share is not None:
                for limit, factor in ABILITY_STEPS:
                    if assets_share > limit:
                        ability = factor
                        break
            p = 0.0 if parent_stress else p * ability
            gap = max(own - parent, 0.0)
            supported = own - p * gap
            if country_score is not None:
                supported = max(supported, max(min(max(float(country_score), 1), 10) - COUNTRY_GAP, 1))
            if sov is not None:
                supported = max(supported, sov)
            final = min(max(min(supported, own), 1), 10)
            p_used = p if gap > 0 else 0.0
            steps.append((f"Group support (probability {p_used:.2f})", final))
        # 6. overlay
        if overlay:
            final = min(max(final + max(min(float(overlay), 2), -2), 1), 10)
            steps.append((f"Analyst overlay ({overlay:+g})", final))

        label, grade = _label(final)
        results.append({
            "year": y, "final_score": round(final, 2), "grade": grade, "label": label,
            "descriptor": GRADE_DESCRIPTOR[grade], "standalone_score": round(standalone, 2),
            "own_score": round(own, 2), "loss_notch": notch, "support_prob": round(p_used, 3),
            "composite_z": round(comp, 3),
            "pillars": {p: round(v, 3) for p, v in pillars.items()},
            "ratios": {r: {"entered": raw[y][r], "used": round(used[r], 4), "z": round(z[r], 3),
                           "imputed": r in imputed} for r in ratios},
            "reported_ratios": reported,
            "data_quality": "LOW" if len(imputed) / len(ratios) > 0.4 else "OK",
            "enough_data": reported >= 5,
            "steps": [(s, round(v, 2)) for s, v in steps],
        })
    return {"bank_years": results, "latest": results[-1]}


def read_template(path):
    """CSV with a RATIO column and one column per year (definitions column optional)."""
    t = pd.read_csv(path)
    year_cols = [c for c in t.columns if str(c).strip().isdigit()]
    t["RATIO"] = t["RATIO"].str.strip().str.upper()
    return {int(y): {r: t.loc[i, y] for i, r in t["RATIO"].items()
                     if pd.notna(t.loc[i, y])} for y in year_cols}


# ---- from annual-report figures to ratios --------------------------------------------------
# Items to take from the balance sheet, income statement and Pillar 3 / capital note.
# Any currency and unit, as long as all items of a bank use the same one.
RAW_ITEMS = {
    "TOTAL REGULATORY CAPITAL": "Own funds (Tier 1 + Tier 2), capital adequacy note",
    "TIER 1 CAPITAL": "Tier 1 capital, capital adequacy note",
    "RISK-WEIGHTED ASSETS": "Total risk-weighted assets (risk exposure amount)",
    "TOTAL ASSETS": "Balance sheet total",
    "TOTAL EQUITY": "Total equity including minority interests",
    "INTANGIBLE ASSETS": "Goodwill and other intangibles (0 if none)",
    "TOTAL DEBT": "Borrowings from banks, debt securities issued and subordinated debt (not customer deposits)",
    "GROSS LOANS": "Gross loans to customers, before loss allowances",
    "PROBLEM LOANS": "Non-performing / Stage 3 / impaired loans, gross",
    "LOAN LOSS RESERVES": "Loss allowances on customer loans (stock, balance sheet)",
    "TOTAL OPERATING INCOME": "Net interest income + net fees + trading and other income, before expenses and provisions",
    "OPERATING EXPENSES": "Staff, administrative and depreciation expenses, without loan loss provisions",
    "NET INTEREST INCOME": "Interest income minus interest expense",
    "NET INCOME": "Profit for the year after tax",
    "INTEREST-EARNING ASSETS": "Loans, interbank placements and debt securities (total assets if not available)",
    "LIQUID ASSETS": "Cash, central bank balances, interbank placements and liquid securities",
    "CUSTOMER DEPOSITS": "Deposits from customers",
    "SHARES OUTSTANDING": "Number of shares at year end (optional; equity growth is used if empty)",
}


def ratios_from_raw(raw_years):
    """raw_years: {year: {item: value}}. Returns ({year: {ratio: value}}, notes).

    Averages (ROAA, ROAE, NIM) use the previous year's balance when that year is given, and the
    year-end balance otherwise. A year given only to supply opening balances (no income
    statement) is not scored."""
    yrs = sorted(int(y) for y in raw_years)
    g = lambda y, k: (lambda v: None if v is None or (isinstance(v, float) and math.isnan(v)) else float(v))(
        raw_years.get(y, raw_years.get(str(y), {})).get(k))
    div = lambda a, b, m=100.0: None if a is None or b is None or b == 0 else a / b * m
    out, notes = {}, []
    for y in yrs:
        if g(y, "NET INCOME") is None and g(y, "TOTAL OPERATING INCOME") is None:
            notes.append(f"{y}: no income statement, used for opening balances only")
            continue
        prev = y - 1 if (y - 1) in yrs else None
        avg = lambda k: (None if g(y, k) is None else
                         (g(y, k) + g(prev, k)) / 2 if prev and g(prev, k) is not None else g(y, k))
        if prev is None:
            notes.append(f"{y}: ROAA, ROAE and NIM on year-end balances (no {y - 1} figures)")
        eq, intan = g(y, "TOTAL EQUITY"), g(y, "INTANGIBLE ASSETS") or 0.0
        npl, llr = g(y, "PROBLEM LOANS"), g(y, "LOAN LOSS RESERVES")
        dep, debt = g(y, "CUSTOMER DEPOSITS"), g(y, "TOTAL DEBT")
        iea = "INTEREST-EARNING ASSETS" if g(y, "INTEREST-EARNING ASSETS") is not None else "TOTAL ASSETS"
        oi = g(y, "TOTAL OPERATING INCOME")
        bv = lambda yy: (None if yy is None or g(yy, "TOTAL EQUITY") is None else
                         g(yy, "TOTAL EQUITY") / g(yy, "SHARES OUTSTANDING")
                         if g(yy, "SHARES OUTSTANDING") else g(yy, "TOTAL EQUITY"))
        r = {
            "TOTAL CAPITAL RATIO": div(g(y, "TOTAL REGULATORY CAPITAL"), g(y, "RISK-WEIGHTED ASSETS")),
            "TIER1 RATIO": div(g(y, "TIER 1 CAPITAL"), g(y, "RISK-WEIGHTED ASSETS")),
            "TOTAL DEBT/ TOTAL EQUITY": div(debt, eq, 1.0),
            "PROBLEM LOANS RATIO": div(npl, g(y, "GROSS LOANS")),
            "TEXAS RATIO": div(npl, None if eq is None or llr is None else eq - intan + llr),
            "LOAN LOSS RESERVE TO PROBLEM LOANS": div(llr, npl),
            "COST TO INCOME RATIO": div(g(y, "OPERATING EXPENSES"), oi if oi and oi > 0 else None),
            "OPERATING RETURN ON ASSETS": div(oi, g(y, "TOTAL ASSETS")),
            "ROAA": div(g(y, "NET INCOME"), avg("TOTAL ASSETS")),
            "ROAE": div(g(y, "NET INCOME"), avg("TOTAL EQUITY")),
            "NET INTEREST MARGIN": div(g(y, "NET INTEREST INCOME"), avg(iea)),
            "BOOKVALUE PER SHARE GROWTH": (None if bv(y) is None or bv(prev) in (None, 0)
                                           else (bv(y) / bv(prev) - 1) * 100),
            "LIQUID ASSETS/ TOTAL DEPOSITS & BORROWINGS": div(
                g(y, "LIQUID ASSETS"), None if dep is None else dep + (debt or 0.0)),
        }
        out[y] = {k: v for k, v in r.items() if v is not None}
    return out, notes


def read_raw_template(path):
    """CSV with an ITEM column and one column per year."""
    t = pd.read_csv(path)
    year_cols = [c for c in t.columns if str(c).strip().isdigit()]
    t["ITEM"] = t["ITEM"].str.strip().str.upper()
    return {int(y): {r: float(t.loc[i, y]) for i, r in t["ITEM"].items() if pd.notna(t.loc[i, y])}
            for y in year_cols}
