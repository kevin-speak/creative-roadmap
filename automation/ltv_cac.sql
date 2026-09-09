-- =====================================================================================
-- Creative Roadmap: lifetime CPFT and LTV/CAC per Meta ad, MARKET-AWARE (TW + HK)
-- Project: speak-v2-2a1f1   |   Built 2026-08-16
--
-- Emits exactly ONE ROW PER ad_id. Each ad is scored in the market where it actually
-- delivered: the roadmap is nominally "TW", but a large share of its live creatives run
-- entirely in Hong Kong (18 of 67 live rows as of 2026-08-16, including the four
-- highest-spend ones). Scoring every ad against Taiwan would leave those blank.
--
-- MARKET RESOLUTION
--   Per ad, spend is totalled per funnel country across the supported markets and the
--   highest-spend market wins (`ad_market`). Ads that split across TW and HK are scored
--   wholly in their dominant market rather than being blended, so spend, trials,
--   conversions, convert-rate and cohort LTV all come from one coherent market.
--
--   *** cohort_ltv MARKET-NAME TRAP ***
--   The three tables do not agree on market naming:
--       meta_ads_creative_report_funnel.country                     -> 'Taiwan' | 'Hong Kong'
--       marketing_attribution_..._date_cohort.country               -> 'Taiwan' | 'Hong Kong'
--       cohort_ltv.country                                          -> 'Taiwan' | 'Hong Kong / Macau'
--   Filtering cohort_ltv on 'Hong Kong' returns ZERO rows, which silently empties the
--   LTV join and drops every HK ad from the result set with no error. The `market_map`
--   CTE below is the single place that mapping lives -- extend it to add a market.
--
-- METHOD (replicates the production Daily Ad Fatigue Report's LTV/CAC definitions, but
-- over each ad's LIFETIME window -- launch -> MAX(date) -- instead of trailing 7d):
--
--   1. Grain: one row per ad_id, summed across os and placement within the ad's market.
--      Anchored to MAX(date) in the funnel table (data lags ~2 days); CURRENT_DATE is
--      never used.
--
--   2. est_conversions = adj_initial_purchases + adj_trial_starts * trial_convert_rate
--      The funnel table exposes adj_* columns, so those are used (not the raw ones).
--
--   3. trial_convert_rate: from marketing_attribution_aggregate_attribution_date_cohort
--      (channel = 'Meta Ads', the ad's own market, attribution_date <= MAX(date) - 4 days
--      so only matured trial cohorts count). Computed per campaign_id as
--      SUM(trial_converts)/SUM(trial_starts); campaigns with < 30 attributed trial starts
--      fall back to that market's blended Meta Ads rate (TW ~0.373). An ad that ran in
--      several campaigns gets the spend-weighted blend of its campaigns' rates.
--
--   4. LTV per converted user: cohort_ltv at month_index = 35, the ad's mapped market,
--      keyed on the ad's LAUNCH MONTH (first_transaction_month = launch month), as
--      SUM(revenue_ltv)/SUM(users_initial) across first_platform / first_duration /
--      first_tier / language_pair. Platform is deliberately BLENDED rather than joined to
--      the funnel's `os`: cohort_ltv keys on billing platform (app_store/play_store/
--      paddle/stripe) while the funnel keys on ad delivery os (ios/android/web), and the
--      two do not map 1:1 (web-delivered ads bill through several platforms). Falls back
--      to that market's most recent cohort month if the launch month has no row.
--
--   5. CAC = spend / est_conversions      (dollars per converted user)
--      ltv_total = est_conversions * ltv_per_user   (total dollars of LTV bought)
--      LTV/CAC = ltv_per_user / CAC        <-- unit-consistent ratio.
--      NOTE / DEVIATION: the brief's literal wording ("LTV = est_conv * LTV-per-user,
--      LTV/CAC = LTV / CAC") squares est_conversions and is dimensionally wrong -- it
--      scales with ad size rather than efficiency and blows past the stated 0.5-3 sanity
--      band. The per-unit ratio above is the standard (and the report's) meaning and
--      lands inside that band, so it is what ltv_cac reports.
--
--   6. CPFT = spend / trial_starts over the lifetime (raw trial_starts, matching
--      automation/sp_score.sql).
--
--   7. (added 2026-09-08) TRAILING-7-DAY WINDOW for the nightly watch flag: spend_7d,
--      trial_starts_7d and cpft_7d cover the 7 funnel days ending at MAX(date). The
--      nightly sync compares cpft_7d against lifetime cpft (Watch List when cpft_7d is
--      > 30% worse AND trial_starts_7d >= 5) instead of against yesterday's stored value.
--      spend_7d > 0 also tells the sync an ad is genuinely delivering (relaunch detection).
--
--   8. (added 2026-09-09) CAMPAIGN STAGE + ACTIVITY for Pause-reason prefill:
--      dominant_campaign_name = the campaign where the ad spent the most;
--      campaign_stage = 'testing' when that name contains "testing", 'scaling' when it
--      contains "scaling" / "winning" / "cpr", else 'other';
--      activity_total = lifetime installs (app os) or checkouts_initiated (web) — the same
--      "10-install" activity the SP baseline uses. The nightly sync prefills
--      `Budget Capped` for testing-stage ads that stopped at the $150 daily cap with
--      < 10 activity, and only allows `Fatigue` for scaling-stage ads.
--
-- SUPPRESSION -- the consumer must leave the Notion field EMPTY (never write 0) when:
--      cpft    IS NULL  -> trial_starts = 0
--      ltv_cac IS NULL  -> est_conversions < 1 (less than one estimated conversion)
--      is_awareness     -> ad is awareness-dominant (Reach/Thruplay/Traffic/brand); it
--                          buys impressions, not trials, so both fields are meaningless
--                          (brand video would otherwise post CPFT $6,873 / LTV:CAC 0.00).
--   cpft and ltv_cac are already forced to NULL for awareness ads below, so a consumer
--   can simply write whatever is non-NULL.
--
-- VALIDATION (2026-08-16): ad 120249481915460167 -> CPFT 58.67 (expected 58.67);
-- ad 120249481917410167 -> CPFT 127.95, matching the value the nightly sync had stored.
-- =====================================================================================

WITH anchor AS (
    SELECT MAX(date) AS max_date
    FROM `speak-v2-2a1f1.analytics.meta_ads_creative_report_funnel`
),

-- Supported markets + the funnel/attribution -> cohort_ltv name mapping. See trap above.
market_map AS (
    SELECT 'Taiwan'     AS funnel_country, 'Taiwan'            AS ltv_market
    UNION ALL
    SELECT 'Hong Kong'  AS funnel_country, 'Hong Kong / Macau' AS ltv_market
),

-- Funnel rows for every supported market
funnel AS (
    SELECT f.ad_id, f.campaign_id, f.campaign_name, f.ad_name, f.date, f.os,
           f.country, m.ltv_market,
           f.spend, f.trial_starts, f.adj_trial_starts,
           f.initial_purchases, f.adj_initial_purchases,
           f.installs, f.checkouts_initiated
    FROM `speak-v2-2a1f1.analytics.meta_ads_creative_report_funnel` f
    JOIN market_map m ON m.funnel_country = f.country
    WHERE f.date >= DATE '2025-01-01'
),

-- Each ad is scored in the single market where it spent the most
ad_market AS (
    SELECT ad_id, country, ltv_market
    FROM funnel
    GROUP BY ad_id, country, ltv_market
    QUALIFY ROW_NUMBER() OVER (PARTITION BY ad_id ORDER BY SUM(spend) DESC, country) = 1
),

-- Funnel rows restricted to each ad's own market
scoped AS (
    SELECT f.*
    FROM funnel f
    JOIN ad_market a ON a.ad_id = f.ad_id AND a.country = f.country
),

-- Lifetime totals per ad (launch -> MAX(date))
ad_lifetime AS (
    SELECT
        ad_id,
        ANY_VALUE(ad_name)          AS ad_name,
        ANY_VALUE(country)          AS market,
        ANY_VALUE(ltv_market)       AS ltv_market,
        MIN(IF(spend > 0, date, NULL)) AS launch_date,
        MAX(IF(spend > 0, date, NULL)) AS last_spend_date,
        STRING_AGG(DISTINCT os ORDER BY os) AS os_mix,
        SUM(spend)                  AS spend_total,
        SUM(trial_starts)           AS trial_starts_total,
        SUM(adj_trial_starts)       AS adj_trial_starts_total,
        SUM(initial_purchases)      AS initial_purchases_total,
        SUM(adj_initial_purchases)  AS adj_initial_purchases_total,
        -- SP-baseline activity: installs for app delivery, checkouts for web delivery
        SUM(CASE WHEN os = 'web' THEN checkouts_initiated ELSE installs END) AS activity_total,
        -- share of spend in awareness-objective campaigns (Reach / Thruplay / Traffic /
        -- brand-awareness)
        SAFE_DIVIDE(
            SUM(IF(REGEXP_CONTAINS(LOWER(campaign_name),
                    r'_awareness_|_reach_|_thruplay_|_traffic_'), spend, 0)),
            NULLIF(SUM(spend), 0))  AS awareness_spend_share
    FROM scoped
    GROUP BY ad_id
),

-- The campaign where the ad spent the most, and its lifecycle stage
ad_dominant_campaign AS (
    SELECT ad_id, campaign_name AS dominant_campaign_name,
        CASE
            WHEN REGEXP_CONTAINS(LOWER(campaign_name), r'testing')              THEN 'testing'
            WHEN REGEXP_CONTAINS(LOWER(campaign_name), r'scaling|winning|cpr')  THEN 'scaling'
            ELSE 'other'
        END AS campaign_stage
    FROM (
        SELECT ad_id, campaign_name, SUM(spend) AS spend
        FROM scoped
        GROUP BY ad_id, campaign_name
    )
    QUALIFY ROW_NUMBER() OVER (PARTITION BY ad_id ORDER BY spend DESC, campaign_name) = 1
),

-- Trailing 7 funnel days ending at MAX(date), in the ad's own market
ad_last7 AS (
    SELECT s.ad_id,
        SUM(s.spend)        AS spend_7d,
        SUM(s.trial_starts) AS trial_starts_7d
    FROM scoped s
    CROSS JOIN anchor
    WHERE s.date > DATE_SUB(anchor.max_date, INTERVAL 7 DAY)
    GROUP BY s.ad_id
),

-- ---- trial-convert rate (Meta Ads, per market, matured cohorts only) ----------------
attr AS (
    SELECT a.country, a.campaign_id, a.trial_starts, a.trial_converts
    FROM `speak-v2-2a1f1.analytics.marketing_attribution_aggregate_attribution_date_cohort` a
    CROSS JOIN anchor
    WHERE a.country IN (SELECT funnel_country FROM market_map)
      AND a.channel = 'Meta Ads'
      AND a.attribution_date >= DATE '2025-01-01'
      AND a.attribution_date <= DATE_SUB(anchor.max_date, INTERVAL 4 DAY)
),
cr_blended AS (
    SELECT country, SAFE_DIVIDE(SUM(trial_converts), SUM(trial_starts)) AS rate
    FROM attr
    GROUP BY country
),
cr_campaign AS (
    SELECT country, campaign_id,
           SUM(trial_starts) AS ts,
           SAFE_DIVIDE(SUM(trial_converts), SUM(trial_starts)) AS rate
    FROM attr
    GROUP BY country, campaign_id
),
ad_campaign_spend AS (
    SELECT ad_id, country, campaign_id, SUM(spend) AS spend
    FROM scoped
    GROUP BY ad_id, country, campaign_id
),
ad_convert_rate AS (
    SELECT s.ad_id,
           COALESCE(
               SAFE_DIVIDE(
                   SUM(s.spend * COALESCE(IF(c.ts >= 30, c.rate, NULL), b.rate)),
                   NULLIF(SUM(s.spend), 0)),
               ANY_VALUE(b.rate)
           ) AS convert_rate
    FROM ad_campaign_spend s
    JOIN cr_blended b ON b.country = s.country
    LEFT JOIN cr_campaign c ON c.country = s.country AND c.campaign_id = s.campaign_id
    GROUP BY s.ad_id
),

-- ---- LTV per converted user, cohort_ltv @ month_index 35, per market ---------------
ltv_by_month AS (
    SELECT country AS ltv_market,
           DATE_TRUNC(first_transaction_month, MONTH) AS cohort_month,
           SAFE_DIVIDE(SUM(revenue_ltv), SUM(users_initial)) AS ltv_per_user
    FROM `speak-v2-2a1f1.analytics.cohort_ltv`
    WHERE country IN (SELECT ltv_market FROM market_map)
      AND month_index = 35
    GROUP BY ltv_market, cohort_month
),
ltv_fallback AS (
    SELECT ltv_market, ltv_per_user
    FROM ltv_by_month
    QUALIFY ROW_NUMBER() OVER (PARTITION BY ltv_market ORDER BY cohort_month DESC) = 1
),

-- ---- assemble ----------------------------------------------------------------------
calc AS (
    SELECT
        l.ad_id,
        l.ad_name,
        l.market,
        l.launch_date,
        l.last_spend_date,
        l.os_mix,
        l.awareness_spend_share,
        l.awareness_spend_share >= 0.5 AS is_awareness,
        l.spend_total,
        l.trial_starts_total,
        l.initial_purchases_total,
        l.activity_total,
        c.dominant_campaign_name,
        c.campaign_stage,
        COALESCE(w.spend_7d, 0)        AS spend_7d,
        COALESCE(w.trial_starts_7d, 0) AS trial_starts_7d,
        r.convert_rate,
        COALESCE(m.ltv_per_user, f.ltv_per_user) AS ltv_per_user,
        l.adj_initial_purchases_total + l.adj_trial_starts_total * r.convert_rate
            AS est_conversions
    FROM ad_lifetime l
    LEFT JOIN ad_dominant_campaign c ON c.ad_id = l.ad_id
    LEFT JOIN ad_last7 w ON w.ad_id = l.ad_id
    LEFT JOIN ad_convert_rate r ON r.ad_id = l.ad_id
    LEFT JOIN ltv_by_month m
           ON m.ltv_market = l.ltv_market
          AND m.cohort_month = DATE_TRUNC(l.launch_date, MONTH)
    LEFT JOIN ltv_fallback f ON f.ltv_market = l.ltv_market
)

SELECT
    ad_id,
    ad_name,
    market,
    launch_date,
    last_spend_date,
    os_mix,
    is_awareness,
    ROUND(awareness_spend_share, 3)                         AS awareness_spend_share,
    ROUND(spend_total, 2)                                   AS spend_total,
    trial_starts_total,
    initial_purchases_total,
    activity_total,
    dominant_campaign_name,
    campaign_stage,
    ROUND(convert_rate, 4)                                  AS trial_convert_rate,
    ROUND(ltv_per_user, 2)                                  AS ltv_per_user,
    ROUND(est_conversions, 3)                               AS est_conversions,
    -- suppressed to NULL for awareness ads and zero-trial ads
    IF(is_awareness, NULL,
        ROUND(SAFE_DIVIDE(spend_total, NULLIF(trial_starts_total, 0)), 2)) AS cpft,
    -- trailing-7-day window (watch flag + delivery check); cpft_7d NULL when no trials
    ROUND(spend_7d, 2)                                      AS spend_7d,
    trial_starts_7d,
    IF(is_awareness, NULL,
        ROUND(SAFE_DIVIDE(spend_7d, NULLIF(trial_starts_7d, 0)), 2))       AS cpft_7d,
    ROUND(est_conversions * ltv_per_user, 2)                AS ltv,
    ROUND(SAFE_DIVIDE(spend_total, NULLIF(est_conversions, 0)), 2)         AS cac,
    -- suppressed to NULL for awareness ads and ads with < 1 estimated conversion
    IF(is_awareness OR est_conversions < 1, NULL,
        ROUND(SAFE_DIVIDE(est_conversions * ltv_per_user, NULLIF(spend_total, 0)), 2))
                                                            AS ltv_cac
FROM calc
WHERE spend_total > 0
ORDER BY spend_total DESC
