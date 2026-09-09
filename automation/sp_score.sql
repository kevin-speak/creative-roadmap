-- SP score for Taiwan + Hong Kong Meta ads, replicated from Hex "[TW] Meta Ads SP Dashboard"
-- (default baseline: Launch → 10-install, 7-day floor). Source of truth confirmed 2026-08-16.
-- BigQuery project: speak-v2-2a1f1
--
-- 2026-09-08: extended from Taiwan-only to Taiwan + Hong Kong. Every CTE is already
-- partitioned by (ad_id, country, os) and the leave-one-out benchmarks are computed per
-- placement × country × os, so HK ads are scored against HK ads only — the two markets never
-- mix. The Phase-2 CPFT verdict ($58 threshold) is Taiwan-specific and is emitted for Taiwan
-- rows only; HK rows get sp_score / sp_tier but phase2_result = NULL until an HK threshold
-- is agreed (see automation/README.md "SP score").
--
-- The funnel table lags real time by ~2 days; every date here is derived from the data
-- itself, never CURRENT_DATE() — do not "modernize" it.
WITH markets AS (
    SELECT 'Taiwan' AS country UNION ALL SELECT 'Hong Kong'
),
daily_per_ad AS (
    SELECT ad_id, ad_name, country, os, campaign_name, date,
        SUM(installs) AS installs,
        SUM(checkouts_initiated) AS checkouts_initiated
    FROM `speak-v2-2a1f1.analytics.meta_ads_creative_report_funnel`
    WHERE date >= DATE '2025-01-01' AND country IN (SELECT country FROM markets)
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
    WHERE date >= DATE '2025-01-01' AND spend > 0 AND country IN (SELECT country FROM markets)
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
    WHERE date >= DATE '2025-01-01' AND country IN (SELECT country FROM markets)
      AND placement IS NOT NULL AND spend > 0
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
    -- Phase 2: cumulative trial_starts and lifetime CPFT per (ad, country, os).
    -- The $58 win/lose threshold below is Taiwan-only.
    SELECT f.ad_id, f.country, f.os,
        SUM(f.trial_starts) AS trial_starts_total,
        SUM(f.spend) AS spend_total,
        SAFE_DIVIDE(SUM(f.spend), NULLIF(SUM(f.trial_starts),0)) AS cpft
    FROM `speak-v2-2a1f1.analytics.meta_ads_creative_report_funnel` f
    WHERE f.date >= DATE '2025-01-01' AND f.country IN (SELECT country FROM markets)
    GROUP BY f.ad_id, f.country, f.os
)
SELECT
    q.ad_id, q.ad_name, q.country, q.os, q.campaign_name, q.launch_date, q.ten_install_date,
    p.sp_score,
    p2.trial_starts_total, p2.spend_total, p2.cpft,
    CASE
        WHEN p.sp_score IS NULL THEN 'Insufficient spend'
        WHEN p.sp_score >= 2.5 THEN 'Strong'
        WHEN p.sp_score >= 2.0 THEN 'Validated'
        ELSE 'Below Baseline'
    END AS sp_tier,
    CASE
        WHEN q.country <> 'Taiwan' THEN NULL   -- no agreed HK CPFT threshold yet
        WHEN p.sp_score >= 2.0 AND p2.trial_starts_total >= 10 AND p2.cpft <= 58 THEN 'P2 Winner'
        WHEN p.sp_score >= 2.0 AND p2.trial_starts_total >= 10 AND p2.cpft > 58 THEN 'CPFT Loser'
        ELSE NULL
    END AS phase2_result
FROM qualifying_ads q
LEFT JOIN placement_sp p ON q.ad_id = p.ad_id AND q.country = p.country AND q.os = p.os
LEFT JOIN phase2 p2 ON q.ad_id = p2.ad_id AND q.country = p2.country AND q.os = p2.os
ORDER BY p.sp_score DESC
