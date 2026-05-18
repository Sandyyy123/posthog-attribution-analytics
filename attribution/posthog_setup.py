"""
PostHog Attribution Engine
- Captures first-touch and last-touch attribution
- Tracks UTM params, referrer, landing page, and conversion path
"""
import os
import json
from datetime import datetime, timedelta
from typing import Optional
import pandas as pd

try:
    import posthog
    POSTHOG_AVAILABLE = True
except ImportError:
    POSTHOG_AVAILABLE = False


# Event schema — every conversion event must include these properties
REQUIRED_PROPERTIES = [
    "utm_source", "utm_medium", "utm_campaign", "utm_content", "utm_term",
    "referrer", "landing_page", "device_type", "country",
    "$session_id", "user_id"
]

CONVERSION_EVENTS = [
    "website_visit",
    "pricing_page_view",
    "signup_started",
    "signup_completed",
    "demo_booking",
    "contact_form_submit",
    "whatsapp_click",
    "checkout_started",
    "order_completed",
]

# Channel classification rules (applied in priority order)
CHANNEL_RULES = [
    {"channel": "paid_search",   "condition": lambda r: r.get("utm_medium") in ("cpc","ppc","paid")},
    {"channel": "paid_social",   "condition": lambda r: r.get("utm_source") in ("linkedin","facebook","meta","twitter")},
    {"channel": "email",         "condition": lambda r: r.get("utm_medium") in ("email","newsletter")},
    {"channel": "organic_search","condition": lambda r: r.get("utm_medium") == "organic"},
    {"channel": "referral",      "condition": lambda r: bool(r.get("referrer")) and "google" not in str(r.get("referrer",""))},
    {"channel": "direct",        "condition": lambda r: not r.get("utm_source") and not r.get("referrer")},
]


def classify_channel(event_properties: dict) -> str:
    """Classify a visit into a marketing channel."""
    for rule in CHANNEL_RULES:
        try:
            if rule["condition"](event_properties):
                return rule["channel"]
        except Exception:
            continue
    return "other"


def build_first_last_touch(events_df: pd.DataFrame) -> pd.DataFrame:
    """
    Build first-touch and last-touch attribution from a DataFrame of events.
    
    Expected columns: user_id, event, timestamp, utm_source, utm_medium,
                      utm_campaign, referrer, landing_page
    Returns: DataFrame with one row per converting user, with first/last touch columns.
    """
    conversions = events_df[events_df["event"].isin(CONVERSION_EVENTS)].copy()
    if conversions.empty:
        return pd.DataFrame()

    # Sort by user + timestamp
    events_df = events_df.sort_values(["user_id", "timestamp"])

    first_touch = (
        events_df.groupby("user_id")
        .first()
        .reset_index()
        .rename(columns={
            "utm_source": "first_utm_source",
            "utm_medium": "first_utm_medium",
            "landing_page": "first_landing_page",
            "referrer": "first_referrer",
        })
    )

    last_touch = (
        events_df[events_df["event"].isin(CONVERSION_EVENTS)]
        .groupby("user_id")
        .last()
        .reset_index()
        .rename(columns={
            "utm_source": "last_utm_source",
            "utm_medium": "last_utm_medium",
            "landing_page": "last_landing_page",
        })
    )

    merged = conversions.merge(first_touch[["user_id","first_utm_source","first_utm_medium","first_landing_page","first_referrer"]], on="user_id", how="left")
    merged = merged.merge(last_touch[["user_id","last_utm_source","last_utm_medium","last_landing_page"]], on="user_id", how="left")

    merged["first_touch_channel"] = merged.apply(
        lambda r: classify_channel({"utm_source": r.get("first_utm_source"), "utm_medium": r.get("first_utm_medium"), "referrer": r.get("first_referrer")}), axis=1
    )
    merged["last_touch_channel"] = merged.apply(
        lambda r: classify_channel({"utm_source": r.get("last_utm_source"), "utm_medium": r.get("last_utm_medium")}), axis=1
    )

    return merged


def generate_demo_events(n_users: int = 500) -> pd.DataFrame:
    """Generate realistic demo attribution events for testing."""
    import numpy as np
    np.random.seed(42)

    sources = ["google","linkedin","twitter","direct","email","referral"]
    source_weights = [0.35, 0.20, 0.10, 0.15, 0.12, 0.08]
    mediums = {"google":"organic","linkedin":"social","twitter":"social","direct":None,"email":"email","referral":"referral"}
    pages = ["/","pricing","/features","/compare","/blog/top-mt4-brokers","/signup"]
    events_list = []

    for uid in range(n_users):
        n_sessions = np.random.randint(1, 6)
        for s in range(n_sessions):
            src = np.random.choice(sources, p=source_weights)
            ts = datetime.now() - timedelta(days=np.random.randint(0,90), hours=np.random.randint(0,24))
            events_list.append({
                "user_id": f"user_{uid:04d}",
                "event": "website_visit" if s < n_sessions-1 else np.random.choice(CONVERSION_EVENTS[2:], p=[0.3,0.35,0.15,0.1,0.05,0.03,0.02]),
                "timestamp": ts,
                "utm_source": src,
                "utm_medium": mediums.get(src,""),
                "landing_page": np.random.choice(pages),
                "referrer": "https://google.com" if src=="google" else "",
                "country": np.random.choice(["SG","US","UK","AU","DE","AE"], p=[0.25,0.20,0.15,0.12,0.08,0.20]),
            })

    return pd.DataFrame(events_list)


def run_attribution_report(output_dir: str = "reports/", demo: bool = True):
    """Run full attribution analysis and save report."""
    import os
    os.makedirs(output_dir, exist_ok=True)

    if demo:
        print("  [PostHog] Using demo data (set demo=False with live PostHog credentials)")
        df = generate_demo_events()
    else:
        print("  [PostHog] Fetching live events via PostHog API...")
        df = fetch_posthog_events()  # requires POSTHOG_API_KEY in .env

    attribution_df = build_first_last_touch(df)

    if attribution_df.empty:
        print("  No conversion events found.")
        return

    # Channel summary
    summary = attribution_df.groupby("first_touch_channel").agg(
        conversions=("user_id","count"),
    ).reset_index().sort_values("conversions", ascending=False)

    out_path = os.path.join(output_dir, "attribution_report.csv")
    summary.to_csv(out_path, index=False)
    print(f"  Saved: {out_path}")
    print(summary.to_string(index=False))


def fetch_posthog_events():
    """Fetch events from PostHog API (requires POSTHOG_API_KEY and POSTHOG_PROJECT_ID in .env)."""
    from dotenv import dotenv_values
    import requests
    d = dotenv_values(".env")
    api_key = d.get("POSTHOG_API_KEY","")
    project_id = d.get("POSTHOG_PROJECT_ID","")
    if not api_key:
        raise ValueError("POSTHOG_API_KEY not set in .env")
    headers = {"Authorization": f"Bearer {api_key}"}
    url = f"https://app.posthog.com/api/projects/{project_id}/events/?event=signup_completed&limit=1000"
    resp = requests.get(url, headers=headers, timeout=30)
    resp.raise_for_status()
    data = resp.json().get("results",[])
    return pd.DataFrame(data)
