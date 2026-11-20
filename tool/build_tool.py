"""Build the browser tool with a calibration embedded.

  python tool/build_tool.py --calibration ../results/calibration.json --out ../results/camels_new_bank_tool.html

The built page holds the calibration's medians, scales and cut-offs (aggregate statistics of
the calibration panel). Keep it next to the other results; the template in this folder holds none.
"""
import argparse
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent


def build(calibration, out):
    calib = json.loads(Path(calibration).read_text())
    if "new_bank" not in calib["params"]:
        raise SystemExit("calibration.json has no new_bank section: re-run run_pipeline.py (v0.7 or later)")
    page = (HERE / "template.html").read_text()
    page = page.replace("/*__ENGINE__*/", (HERE / "camels_tool.js").read_text())
    page = page.replace("/*__CALIB__*/null", json.dumps(calib, separators=(",", ":")))
    Path(out).write_text(page)
    return out


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--calibration", required=True)
    ap.add_argument("--out", required=True)
    a = ap.parse_args()
    print("written", build(a.calibration, a.out))
