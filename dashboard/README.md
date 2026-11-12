# Creative Roadmap & Performance dashboard

Live page: https://claude.ai/artifact/E4u6PyGosRcQYPDvmh2DD5 (a Claude "Data" artifact; private until shared from its Share menu).

It reads two sources with each viewer's own claude.ai connectors (or the sharer's, once a connector is shared from the page's Sources panel):

| Dataset | Connector | What it is |
|---|---|---|
| `roadmap_pipeline`, `roadmap_live`, `roadmap_archive` | Notion | The 🧪 (Beta) TW Creative Roadmap database, split in three because one Notion SQL answer is capped at 100 rows; each query packs its rows into one JSON array (`rows_json`) that the page unpacks. |
| `bq_daily_market` | BigQuery | Daily spend / installs / trial starts for Taiwan + Hong Kong, last 90 days of `analytics.meta_ads_creative_report_funnel`. |
| `bq_ad_lifetime` | BigQuery | One row per Meta ad with spend since 2026-01-01, lifetime totals in its dominant market plus trailing 7 days. Joined to the roadmap by `Meta ad ID(s)`. |
| `bq_ad_daily` | BigQuery | Daily rows for the selected creative; the `{{ad_ids}}` filter is filled when a row is clicked (rule: digits and commas only). |

`index.html` is the page (d3 v7 + the dashboard runtime's `dash` helpers); every figure on it is marked with the dataset or calculation it comes from, and the calculations (`roadmap_rows`, `kpis`, `perf_rows`, `win_by_dim`, …) are declared at the top of its script.

## Updating

The artifact's store holds the live copy: `datasets/<id>`, `dash/params` and `files/index.html`. Edit the files here, then ask Claude to write them back to the artifact (ArtifactData `set` with the artifact URL), or edit the queries directly in the page's Sources panel. Keep this folder in sync so the next change starts from the current page.

Definitions follow `automation/README.md`: win = SP ≥ 2, P2 Hit Ad = SP ≥ 2 + 10 trials + CPFT ≤ $58 (TW), CPFT = spend ÷ trial starts.
