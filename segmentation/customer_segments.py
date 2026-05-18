"""
ICP Customer Segmentation using K-Means Clustering
Identifies high-value customer segments for targeted marketing.
"""
import os
import pandas as pd
import numpy as np
from typing import Optional


SEGMENT_LABELS = {
    0: "Retail Forex Traders",
    1: "EA / Algo Traders",
    2: "Prop Firm Traders",
    3: "Brokers / IBs",
    4: "Fund Managers / Fintech",
    5: "High-Frequency / Low-Latency",
}

FEATURE_COLS = ["plan_value_usd", "sessions_per_month", "days_since_signup",
                "support_tickets", "feature_usage_score", "country_tier"]


def generate_demo_customers(n: int = 800) -> pd.DataFrame:
    """Generate demo customer database for segmentation testing."""
    np.random.seed(99)
    records = []
    for i in range(n):
        segment = np.random.choice([0,1,2,3,4,5], p=[0.35,0.20,0.18,0.12,0.08,0.07])
        base_plans = [29, 79, 149, 499, 999, 2499]
        records.append({
            "customer_id": f"C{i:05d}",
            "plan_value_usd": base_plans[segment] * np.random.uniform(0.8, 1.5),
            "sessions_per_month": int(np.random.normal([8,25,18,5,12,40][segment], 3)),
            "days_since_signup": int(np.random.exponential([200,150,90,400,300,60][segment])),
            "support_tickets": max(0, int(np.random.poisson([1,2,1,3,2,0.5][segment]))),
            "feature_usage_score": np.random.beta([2,4,3,2,3,5][segment], [3,2,2,4,2,1][segment]),
            "country_tier": np.random.choice([1,2,3], p=[0.4,0.4,0.2]),
            "true_segment": segment,
        })
    return pd.DataFrame(records)


def preprocess(df: pd.DataFrame) -> np.ndarray:
    """Scale features for clustering."""
    from sklearn.preprocessing import StandardScaler
    scaler = StandardScaler()
    X = df[FEATURE_COLS].fillna(0).values
    return scaler.fit_transform(X)


def run_icp_segmentation(output_dir: str = "reports/", demo: bool = True,
                          n_clusters: int = 6):
    """Run K-Means clustering and produce ICP segment report."""
    from sklearn.cluster import KMeans
    from sklearn.metrics import silhouette_score

    os.makedirs(output_dir, exist_ok=True)

    if demo:
        print("  [Segmentation] Using demo customer data")
        df = generate_demo_customers()
    else:
        print("  [Segmentation] Load your customer export CSV as df")
        raise NotImplementedError("Connect to your customer DB or CRM export")

    X = preprocess(df)

    # Fit K-Means
    km = KMeans(n_clusters=n_clusters, random_state=42, n_init=20)
    df["cluster"] = km.fit_predict(X)

    sil = silhouette_score(X, df["cluster"])
    print(f"  Silhouette score: {sil:.3f}")

    # Profile each segment
    profile = df.groupby("cluster").agg(
        n_customers=("customer_id", "count"),
        avg_plan_usd=("plan_value_usd", "mean"),
        avg_sessions=("sessions_per_month", "mean"),
        avg_tenure_days=("days_since_signup", "mean"),
        avg_usage=("feature_usage_score", "mean"),
    ).reset_index()

    profile["segment_name"] = profile["cluster"].map(SEGMENT_LABELS)
    profile["ltv_estimate"] = profile["avg_plan_usd"] * 12
    profile["priority"] = pd.cut(profile["ltv_estimate"],
                                  bins=[0,500,2000,10000,999999],
                                  labels=["Low","Medium","High","Enterprise"])

    out_path = os.path.join(output_dir, "icp_segments.csv")
    profile.to_csv(out_path, index=False)
    print(f"  Saved: {out_path}")
    print(profile[["segment_name","n_customers","avg_plan_usd","ltv_estimate","priority"]].to_string(index=False))
    return profile
