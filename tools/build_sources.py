"""Rebuild SOURCES.md from the input files and COMPARISON.md.  python tools/build_sources.py"""
from pathlib import Path
import pandas as pd

root = Path(__file__).resolve().parents[1]
e = pd.read_csv(root / "data/events.csv")
v = e[e.SOURCE.notna()].sort_values(["COUNTRY", "YEAR"])
u = e[e.SOURCE.isna()].sort_values(["COUNTRY", "YEAR"])
sov = pd.read_csv(root / "data/sovereign_ratings.csv")
links = sov[sov.STATUS.str.startswith("countryeconomy")].groupby("COUNTRY").SOURCE.first()
docs = root / "docs" if (root / "docs" / "COMPARISON.md").exists() else root
comp = (docs / "COMPARISON.md").read_text().split("## Sources", 1)[1].strip()
t = (root / "tools/sources_template.md").read_text()
out = (t.replace("{comp}", comp)
        .replace("{sv}", "\n".join(f"| {c} | {s} |" for c, s in links.items()))
        .replace("{ev}", "\n".join(f"| {r['BANK NAME']} | {r.COUNTRY} | {r.YEAR} | {r.EVENT} | {r.SOURCE} |"
                                   for _, r in v.iterrows()))
        .replace("{un}", "\n".join(f"| {r['BANK NAME']} | {r.COUNTRY} | {r.YEAR} | {r.EVENT} |"
                                   for _, r in u.iterrows()))
        .replace("{nv}", str(len(v))).replace("{nu}", str(len(u))))
(docs / "SOURCES.md").write_text(out)
print(f"SOURCES.md: {len(v)} verified events, {len(u)} to re-check, {len(links)} sovereign pages")
