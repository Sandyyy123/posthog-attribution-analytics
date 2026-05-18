#!/usr/bin/env python3
"""
PostHog Attribution Analytics - Main entry point
Usage: python main.py --mode [attribution|segmentation|seo]
"""
import argparse
import sys
from attribution.posthog_setup import run_attribution_report
from segmentation.customer_segments import run_icp_segmentation
from seo_audit.gsc_audit import run_seo_audit


def main():
    parser = argparse.ArgumentParser(description="Growth Analytics Pipeline")
    parser.add_argument("--mode", choices=["attribution", "segmentation", "seo", "all"],
                        default="all", help="Which analysis to run")
    parser.add_argument("--output", default="reports/", help="Output directory")
    parser.add_argument("--demo", action="store_true", help="Run with demo/sample data")
    args = parser.parse_args()

    print(f"[Growth Analytics] Mode: {args.mode} | Demo: {args.demo}")

    if args.mode in ("attribution", "all"):
        print("\n=== Attribution Report ===")
        run_attribution_report(output_dir=args.output, demo=args.demo)

    if args.mode in ("segmentation", "all"):
        print("\n=== ICP Segmentation ===")
        run_icp_segmentation(output_dir=args.output, demo=args.demo)

    if args.mode in ("seo", "all"):
        print("\n=== SEO Audit ===")
        run_seo_audit(output_dir=args.output, demo=args.demo)

    print("\n[Done] Reports written to", args.output)


if __name__ == "__main__":
    main()
