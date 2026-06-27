#!/usr/bin/env python3
"""luxe-pulse CLI — luxury brand social/review pulse.

    python3 analyze_pulse.py                          # synthetic demo
    python3 analyze_pulse.py --real reviews.csv --schema sephora
    python3 analyze_pulse.py --brand "Louis Vuitton" "Dior"
"""
import argparse
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from pulse import data, report
from pulse.sentiment import score_records


def main():
    ap = argparse.ArgumentParser(description="Luxury brand social/review pulse")
    ap.add_argument("--real", metavar="CSV", help="path to a real review/social CSV")
    ap.add_argument("--schema", default="generic", choices=["generic", "sephora", "womens"])
    ap.add_argument("--brand", nargs="*", help="filter to these brands")
    ap.add_argument("-n", type=int, default=4000, help="synthetic sample size")
    ap.add_argument("--out", default="out/pulse_report.md")
    args = ap.parse_args()

    if args.real:
        recs = data.load_csv(args.real, schema=args.schema)
        src = f"{args.real} ({args.schema}, {len(recs):,} rows)"
    else:
        recs = data.generate_synthetic(n=args.n)
        src = f"synthetic demo ({len(recs):,} rows)"
    if args.brand:
        want = set(args.brand)
        recs = [r for r in recs if r["brand"] in want]
    if not recs:
        print("No records after filtering.", file=sys.stderr)
        sys.exit(1)

    recs = score_records(recs)
    md = report.build(recs)
    print(f"Source: {src}\n")
    print(md)
    os.makedirs(os.path.dirname(args.out), exist_ok=True)
    with open(args.out, "w", encoding="utf-8") as f:
        f.write(f"<!-- source: {src} -->\n\n" + md)
    print(f"\n[written to {args.out}]")


if __name__ == "__main__":
    main()
