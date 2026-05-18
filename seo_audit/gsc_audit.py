"""
Google Search Console Top-Pages Audit
- Fetches top pages by clicks, impressions, CTR, and position
- Identifies high-traffic / low-conversion gaps
- Outputs actionable improvement recommendations
"""
import os
from datetime import datetime, timedelta
import pandas as pd
import numpy as np


def generate_demo_gsc_data(n_pages: int = 60) -> pd.DataFrame:
    """Generate demo GSC data for testing."""
    np.random.seed(77)
    pages = [
        "/", "/pricing", "/features/mt4-bridge", "/compare/mt4-vs-mt5",
        "/blog/best-forex-vps", "/blog/prop-firm-rules-2024", "/ea-hosting",
        "/solutions/brokers", "/solutions/prop-firms", "/low-latency-vps",
        "/signup", "/contact", "/blog/metatrader-vs-ctrader", "/affiliate",
        "/api-docs", "/blog/algo-trading-setup", "/blog/ea-optimization",
    ]
    records = []
    for i in range(n_pages):
        page = pages[i % len(pages)] + (f"-{i//len(pages)}" if i >= len(pages) else "")
        impressions = int(np.random.lognormal(7, 1.5))
        ctr = np.random.beta(2, 20)
        clicks = max(0, int(impressions * ctr))
        records.append({
            "page": page,
            "clicks": clicks,
            "impressions": impressions,
            "ctr": round(ctr * 100, 2),
            "position": round(np.random.uniform(1, 50), 1),
            "conversions": max(0, int(clicks * np.random.beta(1, 15))),
        })
    df = pd.DataFrame(records).sort_values("clicks", ascending=False)
    df["conversion_rate"] = (df["conversions"] / df["clicks"].replace(0, np.nan) * 100).round(2)
    return df


def classify_page_opportunity(row: pd.Series) -> str:
    """Tag each page with its primary opportunity type."""
    if row["clicks"] > 500 and row["conversion_rate"] < 1.0:
        return "CRO - High traffic, low conversion"
    elif row["impressions"] > 5000 and row["ctr"] < 2.0:
        return "CTR - High impressions, poor click-through"
    elif row["position"] < 10 and row["clicks"] > 200:
        return "TOP - Strong performer, protect & scale"
    elif row["position"] > 20 and row["impressions"] > 1000:
        return "SEO PUSH - Ranking gap, optimization needed"
    elif row["conversions"] > 10:
        return "CONVERT - Already converting, needs more traffic"
    return "REVIEW"


def run_seo_audit(output_dir: str = "reports/", demo: bool = True):
    """Run GSC top-pages audit and export recommendations."""
    os.makedirs(output_dir, exist_ok=True)

    if demo:
        print("  [SEO] Using demo GSC data")
        df = generate_demo_gsc_data()
    else:
        print("  [SEO] Connect Google Search Console API credentials")
        raise NotImplementedError("Set up GSC OAuth credentials in .env")

    df["opportunity"] = df.apply(classify_page_opportunity, axis=1)
    df_sorted = df.sort_values("clicks", ascending=False)

    out_path = os.path.join(output_dir, "seo_audit.csv")
    df_sorted.to_csv(out_path, index=False)
    print(f"  Saved: {out_path}")
    print("\nTop 10 pages by clicks:")
    print(df_sorted.head(10)[["page","clicks","impressions","ctr","position","opportunity"]].to_string(index=False))

    # Summary by opportunity type
    summary = df.groupby("opportunity")["page"].count().sort_values(ascending=False)
    print("\nOpportunity breakdown:")
    print(summary.to_string())
    return df_sorted
