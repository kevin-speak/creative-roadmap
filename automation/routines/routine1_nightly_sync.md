Reconcile the Notion TW Creative Roadmap against live Meta ads and BigQuery SP scores every night, and report the deltas to #tw-creative.

## Setup — exact IDs

- Notion Roadmap data source: `collection://46a9a0c5-2240-4576-8574-ce81793d224b` ("(WIP) TW Creative Roadmap")
- Meta ad account: Speak ZH, ID `1148917790153640` (Meta MCP — load with ToolSearch, use `ads_get_ad_entities`)
- BigQuery project: `speak-v2-2a1f1` (use `mcp__BigQuery__execute_sql_readonly`)
- Slack channel #tw-creative = `C0ASFA5F1B3`. Paid marketer fallback tag: Kevin Mo `<@U0A1E7WENQ6>`
- Notion tools: `notion-query-data-sources` (SQL mode), `notion-fetch`, `notion-update-page`, `notion-create-pages`, `notion-get-comments`, `notion-create-comment`

**SAMPLE-ROW GUARD (read first, applies to every step).** ~99 rows in the roadmap are seeded sample data — they sit in Production Status Pause/Archive and carry fake ad IDs like `S55`. Never update, archive, comment on, or report them. A row is *real* only if at least one comma-separated token in `Meta ad ID(s)` matches `^[0-9]{15,}$` (a 15+ digit pure-numeric Meta ad ID), OR the row has no ad ID yet but is in an active status (Plan / Production / Ready-to-Test / On Air / Scale) **and** was created after 2026-08-16. Everything else is off-limits. Apply the regex per token, not to the whole cell.

**Checkbox convention:** Notion checkboxes read/write as the strings `"__YES__"` (checked) and `"__NO__"` (unchecked).
**Date convention:** date properties are written through expanded properties — `date:Last synced:start`, `date:Launch date:start`, `date:Paused date:start` — as ISO `YYYY-MM-DD`.

## STEP 1 — Pull the roadmap

Query the roadmap in SQL mode:

```sql
SELECT url, "Name", "Ad Name", "Meta ad ID(s)", "Production Status", "SP score", "SP status",
       "CPFT", "Spend to date", "Watch flag", "Hit ad", "Pause reason", "Owner", "Learnings",
       "date:Launch date:start", "date:Paused date:start", "date:Last synced:start", createdTime
FROM "collection://46a9a0c5-2240-4576-8574-ce81793d224b"
WHERE "Production Status" IN ('On Air','Scale','Pause','Ready-to-Test')
```

Then apply the sample-row guard in memory. Include Ready-to-Test rows — some go live without anyone flipping the status. Keep a map `ad_id -> roadmap row url`, expanding comma-separated `Meta ad ID(s)` into individual keys.

Note: the rollup `License days left` is **not queryable in SQL** (it is in the data source's `notAvailableInQuerySql` list). When you need it (Step 6), `notion-fetch` that individual page and read the rollup from the page properties.

## STEP 2 — Pull live Meta ads and create missing rows

`ads_get_ad_entities` on account `1148917790153640`, ad level, fields: `id, name, effective_status, created_time, spend` — pull twice: `date_preset: maximum` (lifetime spend) and `date_preset: last_7d`. Keep only `effective_status = ACTIVE` for the "live" set, but keep the full result so Step 6 can see paused/archived ads.

For every ACTIVE Meta ad whose `id` is not in the roadmap map: create a roadmap page in `collection://46a9a0c5-2240-4576-8574-ce81793d224b` with

- `Name` = the Meta ad name verbatim (Name is the join key and must equal the Meta ad name)
- `Ad Name` = same string
- `Meta ad ID(s)` = the ad id
- `Production Status` = `On Air`
- `Channel` = `["Meta"]`
- `SP status` = `Testing`
- `date:Launch date:start` = the ad's `created_time` date (date only, Taipei calendar day)
- `date:Last synced:start` = today

Count these as "new rows created" for the report. Do not guess Category, Format, Source or Owner — leave them empty for a human.

If two live ads share the same name (relaunch), do **not** create a second row: append the new ad id to the existing row's `Meta ad ID(s)` as a comma-separated list and keep the earliest Launch date.

## STEP 3 — Run the SP score query in BigQuery

Run this verbatim with `execute_sql_readonly` against project `speak-v2-2a1f1`. The funnel table lags real time by ~2 days; every date in this query is derived from the data itself, never `CURRENT_DATE()` — do not "modernize" it.

```sql
-- SP score for Taiwan Meta ads, replicated from Hex "[TW] Meta Ads SP Dashboard"
-- (default baseline: Launch → 10-install, 7-day floor).
WITH daily_per_ad AS (
    SELECT ad_id, ad_name, country, os, campaign_name, date,
        SUM(installs) AS installs,
        SUM(checkouts_initiated) AS checkouts_initiated
    FROM `speak-v2-2a1f1.analytics.meta_ads_creative_report_funnel`
    WHERE date >= DATE '2025-01-01' AND country = 'Taiwan'
    GROUP BY ad_id, ad_name, country, os, campaign_name, date
),
daily_cumulative AS (
    SELECT ad_id, ad_name, country, os, campaign_name, date,
        SUM(CASE WHEN os = 'web' THEN checkouts_initiated ELSE installs END)
            OVER (PARTITION BY ad_id, country, os ORDER BY date ROWS UNBOUNDED PRECEDING) AS cumulative_activity
    FROM daily_per_ad
    WHERE installs > 0 OR checkouts_initiated > 0
),
ten_install_ads AS (
    SELECT ad_id, ad_name, country, os, campaign_name, date AS ten_install_date
    FROM daily_cumulative
    WHERE cumulative_activity >= 10
    QUALIFY ROW_NUMBER() OVER (PARTITION BY ad_id, country, os ORDER BY date) = 1
),
launch_dates AS (
    SELECT ad_id, country, os, MIN(date) AS launch_date
    FROM `speak-v2-2a1f1.analytics.meta_ads_creative_report_funnel`
    WHERE date >= DATE '2025-01-01' AND spend > 0 AND country = 'Taiwan'
    GROUP BY ad_id, country, os
),
qualifying_ads AS (
    SELECT t.*, l.launch_date
    FROM ten_install_ads t
    INNER JOIN launch_dates l ON t.ad_id = l.ad_id AND t.country = l.country AND t.os = l.os
),
raw_daily AS (
    SELECT ad_id, country, os, placement, date,
        SUM(spend) AS spend, SUM(impressions) AS impressions, SUM(clicks) AS clicks,
        SUM(installs) AS installs, SUM(trial_starts) AS trial_starts,
        SUM(initial_purchases) AS initial_purchases, SUM(checkouts_initiated) AS checkouts_initiated
    FROM `speak-v2-2a1f1.analytics.meta_ads_creative_report_funnel`
    WHERE date >= DATE '2025-01-01' AND country = 'Taiwan' AND placement IS NOT NULL AND spend > 0
    GROUP BY ad_id, country, os, placement, date
),
ad_placement_metrics AS (
    SELECT q.ad_id, q.country, q.os, q.launch_date, q.ten_install_date, r.placement,
        SUM(r.spend) AS spend, SUM(r.impressions) AS impressions, SUM(r.clicks) AS clicks,
        SUM(r.installs) AS installs, SUM(r.checkouts_initiated) AS checkouts_initiated,
        SAFE_DIVIDE(SUM(r.clicks), SUM(r.impressions)) AS ctr,
        CASE
            WHEN q.os = 'web' THEN SAFE_DIVIDE(SUM(r.checkouts_initiated), SUM(r.clicks))
            WHEN q.os IN ('ios','android') THEN SAFE_DIVIDE(SUM(r.installs), SUM(r.clicks))
            ELSE 0
        END AS cti
    FROM qualifying_ads q
    INNER JOIN raw_daily r
        ON q.ad_id = r.ad_id AND q.country = r.country AND q.os = r.os
       AND r.date BETWEEN q.launch_date AND q.ten_install_date
    WHERE r.clicks > 0
    GROUP BY q.ad_id, q.country, q.os, q.launch_date, q.ten_install_date, r.placement
),
ad_total_spend AS (
    SELECT ad_id, country, os, SUM(spend) AS total_ad_spend
    FROM ad_placement_metrics GROUP BY ad_id, country, os
),
placement_benchmarks AS (
    SELECT a.ad_id, a.country, a.os, a.placement, a.spend, a.ctr, a.cti,
        t.total_ad_spend,
        SAFE_DIVIDE(SUM(b.clicks) - a.clicks, SUM(b.impressions) - a.impressions) AS benchmark_ctr,
        CASE
            WHEN a.os = 'web' THEN SAFE_DIVIDE(SUM(b.checkouts_initiated) - a.checkouts_initiated, SUM(b.clicks) - a.clicks)
            WHEN a.os IN ('ios','android') THEN SAFE_DIVIDE(SUM(b.installs) - a.installs, SUM(b.clicks) - a.clicks)
            ELSE 0
        END AS benchmark_cti
    FROM ad_placement_metrics a
    INNER JOIN raw_daily b
        ON a.placement = b.placement AND a.country = b.country AND a.os = b.os
       AND b.date BETWEEN LEAST(a.launch_date, DATE_SUB(a.ten_install_date, INTERVAL 6 DAY)) AND a.ten_install_date
       AND b.clicks > 0
    INNER JOIN ad_total_spend t ON a.ad_id = t.ad_id AND a.country = t.country AND a.os = t.os
    GROUP BY a.ad_id, a.country, a.os, a.placement, a.spend, a.ctr, a.cti,
        a.clicks, a.impressions, a.installs, a.checkouts_initiated, t.total_ad_spend
),
placement_sp AS (
    SELECT ad_id, country, os,
        SUM(SAFE_DIVIDE(spend, total_ad_spend)
            * (COALESCE(SAFE_DIVIDE(ctr, benchmark_ctr), 0) + COALESCE(SAFE_DIVIDE(cti, benchmark_cti), 0))) AS sp_score
    FROM placement_benchmarks
    WHERE total_ad_spend > 10
    GROUP BY ad_id, country, os
),
phase2 AS (
    -- Taiwan Phase 2: cumulative trial_starts; CPFT threshold $58 (<=58 wins, >58 loses)
    SELECT f.ad_id, f.country, f.os,
        SUM(f.trial_starts) AS trial_starts_total,
        SUM(f.spend) AS spend_total,
        SAFE_DIVIDE(SUM(f.spend), NULLIF(SUM(f.trial_starts),0)) AS cpft
    FROM `speak-v2-2a1f1.analytics.meta_ads_creative_report_funnel` f
    WHERE f.date >= DATE '2025-01-01' AND f.country = 'Taiwan'
    GROUP BY f.ad_id, f.country, f.os
)
SELECT
    q.ad_id, q.ad_name, q.os, q.campaign_name, q.launch_date, q.ten_install_date,
    p.sp_score,
    p2.trial_starts_total, p2.spend_total, p2.cpft,
    CASE
        WHEN p.sp_score IS NULL THEN 'Insufficient spend'
        WHEN p.sp_score >= 2.5 THEN 'Strong'
        WHEN p.sp_score >= 2.0 THEN 'Validated'
        ELSE 'Below Baseline'
    END AS sp_tier,
    CASE
        WHEN p.sp_score >= 2.0 AND p2.trial_starts_total >= 10 AND p2.cpft <= 58 THEN 'P2 Winner'
        WHEN p.sp_score >= 2.0 AND p2.trial_starts_total >= 10 AND p2.cpft > 58 THEN 'CPFT Loser'
        ELSE NULL
    END AS phase2_result
FROM qualifying_ads q
LEFT JOIN placement_sp p ON q.ad_id = p.ad_id AND q.country = p.country AND q.os = p.os
LEFT JOIN phase2 p2 ON q.ad_id = p2.ad_id AND q.country = p2.country AND q.os = p2.os
ORDER BY p.sp_score DESC
```

Rows come back per (ad_id, os). Collapse to one row per ad_id: sum `trial_starts_total` and `spend_total`, take the **best (highest) `sp_score`**, and recompute `cpft = summed spend_total / summed trial_starts_total` (NULL when trial starts are 0). Join to roadmap rows by ad_id.

## STEP 4 — Write metrics back (only what changed)

For each matched roadmap row, compute:

- **SP score** = sp_score rounded to 2 decimals
- **SP status** by this mapping, in order:
  - `Hit Ad` — sp_score >= 2.0 AND trial_starts_total >= 10 AND cpft <= 58
  - `P2 Loser` — sp_score >= 2.0 AND trial_starts_total >= 10 AND cpft > 58
  - `Winner` — sp_score >= 2.0 and fewer than 10 trial starts
  - `Mid-tier` — 1.5 <= sp_score < 2.0
  - `Pause` — sp_score < 1.5
  - `Testing` — no sp_score (insufficient spend)
- **CPFT** = cpft rounded to 2 decimals (leave untouched if NULL)
- **Spend to date** = lifetime spend from Meta (Step 2), summed across all ad IDs on the row

Call `notion-update-page` once per row and include **only properties whose value actually differs** from what Step 1 returned — this keeps the Notion edit history readable. Always set `date:Last synced:start` = today, even when nothing else changed. If a row has multiple ad IDs, sum spend across them and use the best SP among them (as collapsed above).

## STEP 5 — Hit Ad transitions

If a row's new SP status is `Hit Ad` **and** its `Hit ad` checkbox is currently `__NO__`/empty:

1. Set `Hit ad` = `"__YES__"`.
2. Invoke the Skill tool with skill name `hit-ad-to-slack`, passing the Meta ad ID and the SP score, so the win is posted to #hit-ads-library. Use the highest-spend ad ID if the row has several.

Only fire this on the transition — never re-fire for a row already checked.

## STEP 6 — Pause detection

A roadmap row currently `On Air` or `Scale` whose **every** listed Meta ad ID is no longer ACTIVE in the Step 2 pull (paused, archived, deleted, or absent from the account):

**Before acting, verify absence individually.** An ad missing from the bulk pull may be a pagination/API artifact, not a paused ad. For each ad ID about to be declared inactive, make one direct `ads_get_ad_entities` call filtered to that specific ad ID and confirm its `effective_status` is genuinely not ACTIVE (or the ad truly does not exist). Only pause the row when every ID is individually confirmed. If the verification call errors, skip the row this run and note it in the report instead of pausing.

1. Set `Production Status` = `Pause` and `date:Paused date:start` = today.
2. Prefill `Pause reason` only when confident:
   - `License Expired` — `notion-fetch` the page and read the `License days left` rollup; use this if it is <= 0.
   - `SP Threshold` — if the freshly-written SP status is `Pause`.
   - Otherwise leave `Pause reason` **empty**.
3. When you left it empty, post to `C0ASFA5F1B3` tagging the row's `Owner` (resolve the person via `notion-get-users`; fall back to `<@U0A1E7WENQ6>` if Owner is empty or unresolvable) asking them to fill in Pause reason + Learnings, with a link to the Notion page.

If some but not all of a row's ad IDs went inactive, do nothing — the creative is still running.

## STEP 7 — Watch flags

For rows that are still live (`On Air`/`Scale`):

- sp_score < 1.5 → `Watch flag` = `Pause-candidate`
- CPFT worsened by more than 30% versus the row's trailing average CPFT (compare today's computed CPFT against the last stored `CPFT` value from Step 1 as the trailing reference), or 7-day frequency is a concern in the Meta pull → `Watch flag` = `Watch List`
- Neither condition and the flag is currently set → reset to `None`

`Pause-candidate` outranks `Watch List` when both apply.

## STEP 8 — Archive hygiene

- Row in `Pause` with `date:Paused date:start` more than 14 days ago **and** `Pause reason` filled → set `Production Status` = `Archive`. (Sample rows are excluded by the guard — check it again here, this is where they are most tempting.)
- Row in `Pause` for 3+ days with `Pause reason` still empty → re-ping the Owner. Ping **at most once**: call `notion-get-comments` on the page first and skip if a ping comment already exists from within the last 7 days. When you do ping, post to Slack **and** leave a Notion comment `pause-ping-sent <YYYY-MM-DD>` on the page to mark it.

## STEP 9 — Slack report

Post one compact message to `C0ASFA5F1B3`. **If nothing changed at all — no new rows, no status changes, no hit ads, no pings — post nothing and end silently.**

```
🌙 *TW Creative Roadmap sync — <YYYY-MM-DD>*
Synced: X ads · Created: X new rows · Updated: X rows

*New rows* (need Category/Format/Owner)
• <ad name> — <Notion link>

*Status changes*
• <name>: SP <old> → <new> · <old SP status> → <new SP status>
• <name>: On Air → Pause (reason: <reason or "needs owner input">)

*🏆 Hit ads* — <name> (SP <score>, CPFT $<cpft>) → posted to #hit-ads-library

*Watch flags* — X pause-candidates, X watch list

*Waiting on owners* — <@owner> <name> needs Pause reason + Learnings <link>
```

Then report the same summary as your task output. Do not touch any roadmap row that fails the sample-row guard, do not delete rows, and do not write anything to Meta or BigQuery.
