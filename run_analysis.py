"""Command-line entry point for the bank soundness analysis."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent / "src"))

from bank_soundness.pipeline import generate_demo_data, load_bank_data, run_analysis


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    source = parser.add_mutually_exclusive_group(required=True)
    source.add_argument("--input", type=Path, help="Authorised bank-ratio CSV")
    source.add_argument("--demo", action="store_true", help="Run with synthetic data")
    parser.add_argument("--output", type=Path, default=Path("results"))
    parser.add_argument("--capital-threshold", type=float, default=12.0)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    frame = generate_demo_data() if args.demo else load_bank_data(args.input)
    metrics = run_analysis(frame, args.output, threshold=args.capital_threshold)
    print(metrics.to_string(index=False))


if __name__ == "__main__":
    main()

