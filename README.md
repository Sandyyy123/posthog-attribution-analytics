# PostHog Attribution Analytics

> Multi-touch attribution tracking, customer ICP segmentation, and top-pages SEO audit pipeline.

## Architecture

```
Data Sources                  Processing                    Output
──────────────────────────────────────────────────────────────────
PostHog Events  ──────────►  Attribution Engine  ──────►  Dashboard
GA4 Sessions    ──────────►  ICP Segmentation    ──────►  Looker Studio
Google Search   ──────────►  SEO Audit           ──────►  Reports
Console
```

## Modules

| Module | Purpose |
|--------|---------|
| `attribution/` | PostHog event schema + first/last-touch attribution |
| `segmentation/` | K-means ICP clustering on customer database |
| `seo_audit/` | GSC-powered top-pages analysis + gap detection |
| `dashboard/` | Looker Studio schema generator |
| `main.py` | CLI entry point for all modules |

## Setup

```bash
pip install -r requirements.txt
cp .env.example .env  # Fill in your API keys
python main.py --mode attribution   # Run attribution report
python main.py --mode segmentation  # Run ICP clustering
python main.py --mode seo           # Run SEO audit
```

## Sample Output

- **Attribution Report**: First/last-touch breakdown by channel (organic, paid, LinkedIn, direct, referral)
- **ICP Segments**: 5-8 clusters with LTV, conversion rate, and recommended landing pages
- **SEO Audit**: Top 50 pages by clicks + conversions + gap analysis

## Stack

- **Analytics**: PostHog Python SDK, GA4 Data API, Google Search Console API
- **Segmentation**: scikit-learn K-means + UMAP visualization
- **Dashboard**: Looker Studio / Google Sheets via gspread
- **Reporting**: pandas + plotly (static HTML exports)
