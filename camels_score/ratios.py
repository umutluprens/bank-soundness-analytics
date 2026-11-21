"""Ratio registry: one place that says what each ratio measures and which way is good.

direction = +1  higher is sounder (e.g. capital ratio)
direction = -1  higher is weaker  (e.g. Texas ratio)

core = True     ratio was in the 2023 UCD dataset (column names match merged_data.xlsx)
core = False    added ratio; used automatically when the column is present with enough coverage

bounds          plausible range in percent (or multiple); values outside are treated as data errors
                and clipped before scoring. Within bounds, values are winsorised per year.
"""
from dataclasses import dataclass
from typing import Optional, Tuple


@dataclass(frozen=True)
class Ratio:
    name: str
    pillar: str            # C, A, M, E, L, S
    direction: int         # +1 or -1
    core: bool
    bounds: Tuple[Optional[float], Optional[float]] = (None, None)
    note: str = ""


PILLARS = {
    "C": "Capital adequacy",
    "A": "Asset quality",
    "M": "Management and efficiency",
    "E": "Earnings",
    "L": "Liquidity and funding",
    "S": "Sensitivity to market risk",
}

# Default expert weights (sum to 1). Asset quality and capital carry the most weight,
# in line with the 2023 finding that asset quality, capital and earnings drive soundness.
# v0.6 weights (adopted Nov 2026; v0.5 used C .20, A .25, M .10, E .15, L .20, S .10)
PILLAR_WEIGHTS = {"C": 0.20, "A": 0.30, "M": 0.05, "E": 0.25, "L": 0.15, "S": 0.05}

# Grade descriptors in the style of S&P's assessment scale
GRADE_DESCRIPTOR = {1: "Very strong", 2: "Very strong", 3: "Strong", 4: "Strong",
                    5: "Adequate", 6: "Adequate", 7: "Moderate", 8: "Moderate",
                    9: "Weak", 10: "Very weak"}

RATIOS = [
    # ---------------- Capital adequacy ----------------
    Ratio("TOTAL CAPITAL RATIO", "C", +1, True, (0, 100)),
    Ratio("TIER1 RATIO", "C", +1, True, (0, 100),
          "Highly correlated with total capital; pillar averaging stops it being double counted"),
    Ratio("CET1 RATIO", "C", +1, False, (0, 100)),
    Ratio("LEVERAGE RATIO", "C", +1, False, (0, 50), "Tier 1 / leverage exposure (Basel III)"),
    Ratio("TANGIBLE EQUITY / TANGIBLE ASSETS", "C", +1, False, (-20, 60)),
    Ratio("TOTAL DEBT/ TOTAL EQUITY", "C", -1, True, (0, 5000), "Balance sheet leverage multiple"),
    Ratio("RWA DENSITY", "C", -1, False, (0, 150),
          "RWA / total assets. Mild signal only; low density can also reflect model optimism"),

    # ---------------- Asset quality ----------------
    Ratio("PROBLEM LOANS RATIO", "A", -1, True, (0, 100)),
    Ratio("TEXAS RATIO", "A", -1, True, (0, 1000)),
    Ratio("LOAN LOSS RESERVE TO PROBLEM LOANS", "A", +1, True, (0, 1000), "NPL coverage"),
    Ratio("COST OF RISK", "A", -1, False, (-5, 30), "Loan loss provisions / average loans"),
    Ratio("STAGE 2 LOANS RATIO", "A", -1, False, (0, 100), "IFRS 9, available from 2018"),
    Ratio("FORBORNE LOANS RATIO", "A", -1, False, (0, 100)),
    Ratio("LOAN GROWTH", "A", -1, False, (-60, 200),
          "Fast credit growth is a classic early warning sign; scored as risk above peer median"),

    # ---------------- Management and efficiency ----------------
    Ratio("COST TO INCOME RATIO", "M", -1, False, (0, 300),
          "Replaces NON-OPERATING EXPENSE RATIO as the main efficiency measure"),
    Ratio("NON-OPERATING EXPENSE RATIO", "M", -1, True, (-500, 500),
          "Legacy ratio. Formula mixes a flow with a stock (loan loss reserve); kept for comparability"),
    Ratio("OPERATING RETURN ON ASSETS", "M", +1, True, (-30, 30)),
    Ratio("NON-INTEREST INCOME SHARE", "M", +1, False, (-50, 150),
          "Fee and other income / operating income; revenue diversification"),

    # ---------------- Earnings ----------------
    Ratio("ROAA", "E", +1, True, (-30, 30)),
    Ratio("ROAE", "E", +1, True, (-200, 100)),
    Ratio("NET INTEREST MARGIN", "E", +1, True, (-5, 25)),
    Ratio("PRE-PROVISION PROFIT / RWA", "E", +1, False, (-20, 30), "Loss absorption before capital"),
    Ratio("BOOKVALUE PER SHARE GROWTH", "E", +1, True, (-100, 200)),
    Ratio("ROAA VOLATILITY 3Y", "E", -1, False, (0, 30),
          "Derived automatically from ROAA history when 3 years are available"),

    # ---------------- Liquidity and funding ----------------
    Ratio("LIQUIDITY COVERAGE RATIO", "L", +1, True, (0, 2000)),
    Ratio("LIQUID ASSETS/ TOTAL DEPOSITS & BORROWINGS", "L", +1, True, (0, 1000)),
    Ratio("NET STABLE FUNDING RATIO", "L", +1, False, (0, 500)),
    Ratio("LOANS / DEPOSITS", "L", -1, False, (0, 1000)),
    Ratio("CUSTOMER DEPOSITS / TOTAL FUNDING", "L", +1, False, (0, 100)),
    Ratio("ASSET ENCUMBRANCE RATIO", "L", -1, False, (0, 100)),

    # ---------------- Sensitivity to market risk (empty in the 2023 version) ----------------
    Ratio("EVE SENSITIVITY / TIER1", "S", -1, False, (0, 100),
          "IRRBB Pillar 3: worst-case change in economic value of equity / Tier 1, absolute value"),
    Ratio("NII SENSITIVITY", "S", -1, False, (0, 100), "IRRBB: worst-case change in NII, absolute %"),
    Ratio("FX LOANS / TOTAL LOANS", "S", -1, False, (0, 100),
          "Key for dollarised systems (TR, GE, AZ, BY, UA)"),
    Ratio("NET OPEN FX POSITION / CAPITAL", "S", -1, False, (0, 200), "Absolute value"),
    Ratio("SECURITIES / TOTAL ASSETS", "S", -1, False, (0, 100), "Market and rate exposure of the book"),
    Ratio("UNREALISED SECURITIES LOSSES / CET1", "S", -1, False, (0, 200),
          "Unrealised HTM/AC losses as a share of CET1 (the SVB lesson); losses as positive numbers"),
]

REGISTRY = {r.name: r for r in RATIOS}

# Kept in the registry so the 2023 data loads and can be compared, but not scored.
LEGACY_ONLY = {"NON-OPERATING EXPENSE RATIO"}

# Columns that describe the bank, not its soundness
ID_COLS = ["BANK NAME", "YEAR", "ID", "TYPE", "COUNTRY", "CCODE", "GEOGRAPHY"]

# Operating environment column. 1 = lowest risk, 10 = highest (same scale as BICRA).
# BICRA is proprietary to S&P; any 1-10 country score with the same orientation can be used.
OE_COL_CANDIDATES = ["OE_SCORE", "BICRA"]

# Optional: 1 if the bank is a subsidiary or branch of a stronger foreign group.
PARENT_SUPPORT_COL = "PARENT_SUPPORT"


def pillar_of(name: str) -> str:
    return REGISTRY[name].pillar
