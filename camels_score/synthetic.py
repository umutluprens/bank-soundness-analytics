"""
Synthetic panel shaped like merged_data.xlsx, for testing only.
A latent health factor drives every ratio in its true direction plus noise, and next-year
distress is more likely for unhealthy banks. Results on this data prove the code works,
not that the method works on real banks.
"""
import numpy as np
import pandas as pd

from .ratios import REGISTRY

COUNTRIES = {"Ireland": 3, "Germany": 2, "France": 3, "Spain": 4, "Italy": 5, "Greece": 7,
             "Poland": 5, "Hungary": 6, "Turkey": 8, "Georgia": 8, "Ukraine": 9, "Belarus": 10}

# typical level and spread for each ratio (percent, or multiple)
LEVELS = {
    "TOTAL CAPITAL RATIO": (17, 4), "TIER1 RATIO": (15, 4), "CET1 RATIO": (14, 3.5),
    "LEVERAGE RATIO": (7, 2), "TANGIBLE EQUITY / TANGIBLE ASSETS": (8, 3),
    "TOTAL DEBT/ TOTAL EQUITY": (120, 60), "RWA DENSITY": (45, 12),
    "PROBLEM LOANS RATIO": (5, 4), "TEXAS RATIO": (30, 20),
    "LOAN LOSS RESERVE TO PROBLEM LOANS": (60, 20), "COST OF RISK": (0.6, 0.5),
    "STAGE 2 LOANS RATIO": (9, 5), "FORBORNE LOANS RATIO": (3, 2), "LOAN GROWTH": (5, 10),
    "COST TO INCOME RATIO": (60, 12), "NON-OPERATING EXPENSE RATIO": (55, 20),
    "OPERATING RETURN ON ASSETS": (1.0, 0.7), "NON-INTEREST INCOME SHARE": (30, 10),
    "ROAA": (0.7, 0.6), "ROAE": (7, 6), "NET INTEREST MARGIN": (2.2, 1.0),
    "PRE-PROVISION PROFIT / RWA": (2.5, 1.2), "BOOKVALUE PER SHARE GROWTH": (4, 8),
    "LIQUIDITY COVERAGE RATIO": (180, 50),
    "LIQUID ASSETS/ TOTAL DEPOSITS & BORROWINGS": (30, 12),
    "NET STABLE FUNDING RATIO": (125, 15), "LOANS / DEPOSITS": (90, 20),
    "CUSTOMER DEPOSITS / TOTAL FUNDING": (65, 15), "ASSET ENCUMBRANCE RATIO": (20, 10),
    "EVE SENSITIVITY / TIER1": (6, 4), "NII SENSITIVITY": (4, 3), "FX LOANS / TOTAL LOANS": (15, 15),
    "NET OPEN FX POSITION / CAPITAL": (5, 4), "SECURITIES / TOTAL ASSETS": (18, 8),
    "UNREALISED SECURITIES LOSSES / CET1": (4, 4),
}


def make_panel(n_banks=600, years=range(2010, 2022), extended=True, seed=7, missing=0.08):
    rng = np.random.default_rng(seed)
    names = list(COUNTRIES)
    bank_country = rng.choice(names, n_banks)
    base_health = rng.normal(0, 1, n_banks)
    rows = []
    for i in range(n_banks):
        h = base_health[i]
        oe = COUNTRIES[bank_country[i]]
        start = rng.choice(list(years)[:4])
        for y in years:
            if y < start:
                continue
            h = 0.85 * h + 0.15 * rng.normal(0, 1) - 0.08 * (oe - 5)   # weaker countries drag
            row = {"BANK NAME": f"Bank {i:04d}", "YEAR": y, "ID": 100000 + i,
                   "TYPE": rng.choice(["Diversified Commercial Banks", "Regional Banks"]),
                   "COUNTRY": bank_country[i], "BICRA": oe, "LATENT_HEALTH": h,
                   "PARENT_SUPPORT": int(rng.random() < 0.1)}
            for r, (mu, sd) in LEVELS.items():
                if not extended and not REGISTRY[r].core:
                    continue
                d = REGISTRY[r].direction
                row[r] = mu + sd * (0.7 * d * h + 0.7 * rng.normal())
            rows.append(row)
    df = pd.DataFrame(rows)
    ratio_cols = [c for c in df.columns if c in REGISTRY]
    mask = rng.random((len(df), len(ratio_cols))) < missing
    df[ratio_cols] = df[ratio_cols].mask(mask)
    df["TOTAL CAPITAL RATIO"] = df["TOTAL CAPITAL RATIO"].astype(object)
    df.loc[df.sample(frac=0.01, random_state=seed).index, "TOTAL CAPITAL RATIO"] = "NM"
    df = df.rename(columns={"LIQUID ASSETS/ TOTAL DEPOSITS & BORROWINGS":
                            "LIQUID ASSETS/ TOTAL DEPOSITS & BORROWINGS "})   # as in 2023 file
    # External events: failure risk rises as latent health falls
    p = 1 / (1 + np.exp(4.0 + 1.6 * df["LATENT_HEALTH"]))
    ev = df[rng.random(len(df)) < p][["ID", "YEAR"]].copy()
    ev["YEAR"] = ev["YEAR"] + 1
    ev["EVENT"] = "synthetic distress"
    return df, ev.drop_duplicates("ID")
