Reconcile the Notion TW Creative Roadmap against live Meta ads and BigQuery every night, write the deltas back in priority order, and report to #tw-creative.

This runbook is written so that an interrupted run still leaves the board consistent: status transitions are written first, metrics second, hygiene last. Keep the number of tool calls small — the previous version of this routine died repeatedly in the middle of refreshing ~130 rows.

## Setup — exact IDs

- Notion Roadmap data source: `collection://46a9a0c5-2240-4576-8574-ce81793d224b` (database title "🧪 (Beta) TW Creative Roadmap")
- Notion Influencer Licenses data source: `collection://bf9dd8a5-0331-47a3-9d04-9c15bea80071`
- Meta ad account: Speak ZH, ID `1148917790153640` (Meta Ads MCP, `ads_get_ad_entities`; generate one 20-character `client_conversation_id` and reuse it for every Meta call in the run)
- BigQuery project: `speak-v2-2a1f1` (use `execute_sql_readonly` only)
- Slack channel #tw-creative = `C0ASFA5F1B3`. Paid marketer fallback tag: Kevin Mo `<@U0A1E7WENQ6>`
- Notion tools: `notion-query-data-sources` (SQL mode), `notion-fetch`, `notion-update-page`, `notion-create-pages`, `notion-get-comments`, `notion-create-comment`, `notion-get-users`
- Load MCP tools with ToolSearch before first use.

## Definitions (read first, they apply to every step)

**TRACKED ROW.** A roadmap row is tracked by this routine only if at least one comma-separated token in `Meta ad ID(s)` matches `^[0-9]{15,}$` (apply the regex per token, not to the whole cell). Rows without a real ad ID belong to the pipeline routine (Plan / Production / Ready-to-Test work items) — this routine never edits them, with one exception: Step 2c may write the first ad ID onto a Ready-to-Test / On Air row whose `Ad Name` matches a newly-live Meta ad.

**REFRESH SCOPE.** Metric writes (SP score, SP status, CPFT, LTV/CAC, Spend to date, Watch flag, Market, Launch date) go only to tracked rows that are:
- `Production Status` = `On Air` or `Ready-to-Test`, or
- `Production Status` = `Pause` **and** (`Paused date` is within the last 14 days **or** `Pause reason` is empty).

`Archive` rows and rows paused more than 14 days ago with a reason are frozen — never write metrics to them. They are touched only by the relaunch rule (Step 5.1c) and the archive rule (Step 5.4).

**Option lists (exact strings — never invent an option; if none fits, leave the field empty and say so in the report):**
- `Production Status`: Plan · Production · Ready-to-Test · On Air · Pause · Archive. (There is no "Scale" any more.)
- `SP status`: Testing · Pause · Mid-tier · P1 Winner · P2 Loser · P2 Hit Ad. (Renamed 2026-08-21: old `Winner` → `P1 Winner`, old `Hit Ad` → `P2 Hit Ad`.)
- `Pause reason`: Budget Capped · SP Threshold · License Expired · Graduate (Winning) · Fatigue · Campaign End · Other.
- `Watch flag`: None · Watch List · Pause-candidate.
- `Market`: `TW 🇹🇼` · `HK 🇭🇰` (map BigQuery `market` Taiwan → `TW 🇹🇼`, Hong Kong → `HK 🇭🇰`).

**Conventions.** Checkboxes are the strings `"__YES__"` / `"__NO__"`. Dates are written through expanded properties (`date:Last synced:start`, `date:Launch date:start`, `date:Paused date:start`) as ISO `YYYY-MM-DD` (Taipei calendar day). Rollups `License days left`, `Influencer Priority`, formulas `Verdict` and `Win flag` are **not** SQL-queryable — `notion-fetch` the page when you need a rollup, and only for the rows that need it.

**JOIN KEY.** Match rows to Meta ads by `Meta ad ID(s)` (primary) and `Ad Name` = exact Meta ad name (secondary). The row `Name` is a clean 繁體中文 display name for humans; never overwrite a human-set `Name`.

**CAMPAIGN SCOPE.** Current campaigns only (26Q3 + ongoing trial/purchase testing/scaling/winning in TW and HK). Do not create rows for ads in legacy 2025-era campaigns (campaign `TW_Meta_N/A_M3_Q3Reach_brandmarketing` id `120229358097810167`, or any campaign whose name marks a 25Qx quarter) — skip them silently even if ACTIVE.

**WRITE DISCIPLINE.** One `notion-update-page` per row, containing only properties whose value actually differs from what Step 1 returned, plus `date:Last synced:start` = today. A row with no differing property is skipped entirely (no write, no Last synced stamp). Never write `0` for CPFT or LTV/CAC — leave the field untouched when the value is NULL.

## STEP 1 — Pull the roadmap (one query)

```sql
SELECT url, "Name", "Ad Name", "Meta ad ID(s)", "Production Status", "SP score", "SP status",
       "CPFT", "LTV/CAC", "Spend to date", "Watch flag", "Hit ad", "Pause reason", "Owner",
       "Market", "Relation to Influencer Licenses", "Learnings",
       "date:Launch date:start", "date:Paused date:start", "date:Last synced:start", createdTime
FROM "collection://46a9a0c5-2240-4576-8574-ce81793d224b"
WHERE "Production Status" IN ('On Air','Ready-to-Test','Pause')
```

Apply the TRACKED ROW and REFRESH SCOPE definitions in memory. Build `ad_id -> row` by expanding comma-separated `Meta ad ID(s)`. Also keep the list of Ready-to-Test / On Air rows that have **no** ad ID yet together with their `Ad Name` (for Step 2c matching).

## STEP 2 — Pull Meta (two targeted calls, never the whole account)

The account holds ~2,900 ads; only ~60 are ACTIVE. Do not page through everything.

**2a — ACTIVE ads.** `ads_get_ad_entities`, `level: ad`, `filtering: [{"field":"ad.effective_status","operator":"IN","value":["ACTIVE"]}]`, `fields: ["id","name","effective_status","created_time","campaign_id","campaign_name","spend"]`, `date_preset: last_7d`, `limit: 500`. Follow `pagination.next_cursor` until it is absent, resending every parameter unchanged. This is the "live" set; `spend` here is 7-day spend.

**2b — Tracked ads.** `ads_get_ad_entities`, `level: ad`, `object_ids: [every ad ID from Step 1]` (chunk at 1000), `fields: ["id","name","effective_status","spend"]`, `date_preset: maximum`. This returns lifetime spend and current status for every tracked ID in one call — it *is* the per-ID verification, so no extra per-ad calls are needed. An ID missing from the response is "not found" (deleted). If this call errors, retry once; if it still errors, skip pause detection (Step 5.1a) for this run and say so in the report.

**2c — New live ads.** For every ACTIVE ad from 2a whose `id` is not in the Step 1 map and that passes CAMPAIGN SCOPE:

1. If its `name` equals the `Ad Name` of a Step 1 row that has no ad ID yet (Ready-to-Test / On Air) → write `Meta ad ID(s)` = the id onto that row, set `Production Status` = `On Air`, `date:Launch date:start` = the ad's `created_time` (Taipei day). Count as "went live".
2. Else if another ACTIVE or tracked ad with the same `name` already maps to a row (relaunch) → append the id to that row's `Meta ad ID(s)` (comma-separated), keep the earliest Launch date. Count as "relaunch merged".
3. Else create a roadmap page in `collection://46a9a0c5-2240-4576-8574-ce81793d224b` with:
   - `Name` = a clean 繁體中文 display name built from the ad-name segments, format `[創作者/類型] - 主題` (e.g. `Camel UGC - 職場英文溝通・AI 主管模擬`, `26Q3 促銷靜圖 - P1 倒數 Day1`). Translate the c4 angle (painpoint 痛點 / testimonial 見證 / productdemo 產品示範 / speakmethod 學習方法 / valueprop 價值主張 / scenario 情境 / campaign 檔期 / discount 折扣), use the c6 creator handle, the c8 descriptor in natural zh-TW, keep v1/v2 markers, drop pixel sizes, keep unique vs existing names. Traditional Chinese only.
   - `Ad Name` = the Meta ad name verbatim
   - `Meta ad ID(s)` = the id
   - `Production Status` = `On Air`, `SP status` = `Testing`, `Channel` = `["Meta"]`
   - `Market` = `HK 🇭🇰` if the campaign name starts with `hk_` / `HK_`, else `TW 🇹🇼`
   - `date:Launch date:start` = created_time (Taipei day); `date:Last synced:start` = today
   - Leave Category / Format / Source / Owner empty for a human.
   - Cap: at most 20 new rows per run (highest 7-day spend first); list any remainder in the report — they are picked up tomorrow.

## STEP 3 — BigQuery (two queries, run verbatim from the repo files)

Read `automation/sp_score.sql` and `automation/ltv_cac.sql` from this repo and run each once with `execute_sql_readonly` against project `speak-v2-2a1f1`. Do not edit, "modernize" or re-anchor them to `CURRENT_DATE()`; every date inside is derived from `MAX(date)` because the funnel table lags ~2 days. Do not paste the SQL into your summary.

- `sp_score.sql` returns one row per (ad_id, country, os) for **Taiwan and Hong Kong**. Collapse to one row per ad_id: best (highest) `sp_score`, summed `trial_starts_total` and `spend_total`, `cpft` recomputed as summed spend / summed trials (NULL when trials = 0). `phase2_result` is populated for Taiwan only (no HK CPFT threshold yet).
- `ltv_cac.sql` returns exactly one row per ad_id with `market`, `launch_date`, `cpft`, `ltv_cac`, `spend_7d`, `trial_starts_7d`, `cpft_7d`. It is market-aware (TW vs HK, cohort LTV month 35) and pre-suppresses `cpft` / `ltv_cac` to NULL for awareness-dominant ads, zero trials, or < 1 estimated conversion. Never "fix" the `'Hong Kong / Macau'` mapping inside it.

For rows with several ad IDs, sum spend / trials / spend_7d / trial_starts_7d across IDs before computing ratios, and take the best SP.

## STEP 4 — Compute the target state for every row in REFRESH SCOPE

- **SP score** = best sp_score, 2 decimals (untouched if NULL).
- **SP status**, first match wins:
  - `P2 Hit Ad` — Taiwan, sp_score ≥ 2.0, trial_starts_total ≥ 10, cpft ≤ 58
  - `P2 Loser` — Taiwan, sp_score ≥ 2.0, trial_starts_total ≥ 10, cpft > 58
  - `P1 Winner` — sp_score ≥ 2.0 (Taiwan with < 10 trials, or any HK ad — HK has no Phase-2 threshold yet, so HK rows stop at P1)
  - `Mid-tier` — 1.5 ≤ sp_score < 2.0
  - `Pause` — sp_score < 1.5
  - `Testing` — no sp_score
- **CPFT** = ltv_cac.sql `cpft` (2 decimals); **LTV/CAC** = ltv_cac.sql `ltv_cac` (2 decimals). Both written whenever non-NULL, SP score or not.
- **Spend to date** = lifetime spend from Step 2b summed across the row's IDs (integer dollars). Fall back to BigQuery `spend_total` only if 2b failed.
- **Market** = mapped from ltv_cac.sql `market` — write only when the row's `Market` is empty (humans may override).
- **Launch date** = ltv_cac.sql `launch_date` — write only when the row's `Launch date` is empty (the `Win flag` formula needs it).
- **Watch flag** (live rows only, i.e. On Air):
  - `Pause-candidate` when sp_score < 1.5
  - else `Watch List` when `trial_starts_7d` ≥ 5 and `cpft_7d` > 1.3 × lifetime `cpft`
  - else `None` if a flag is currently set (leave empty rows empty)

## STEP 5 — Write, in this order

### 5.1 Status transitions (do these before any metric write)

**a. Pause detection.** A row currently `On Air` whose **every** listed ad ID is non-ACTIVE or not found in Step 2b → `Production Status` = `Pause`, `date:Paused date:start` = today. If some IDs are still ACTIVE, do nothing. Prefill `Pause reason` only when confident, in this order:
1. `License Expired` — the row has a `Relation to Influencer Licenses`; `notion-fetch` the row and read the `License days left` rollup; use this if ≤ 0.
2. `SP Threshold` — the freshly computed SP status is `Pause`.
3. `Graduate (Winning)` — an ACTIVE ad from Step 2a has the same c6 creator segment **and** the same c8 descriptor as this row's `Ad Name`, sits in a campaign whose name contains `scaling`, `winning` or `cpr`, and was created within the last 14 days (the test version was promoted).
4. `Campaign End` — five or more rows are being paused in this run **and** every ad of this row's `campaign_id` is now non-ACTIVE (the campaign was switched off). Apply to all rows of that campaign; do not ping owners for them.
5. Otherwise leave `Pause reason` empty and add the row to the "needs reason" list (one batched ping in Step 5.5, marked with a `pause-ping-sent <YYYY-MM-DD>` comment on each row).

**b. Went live / relaunch merged / new rows** from Step 2c.

**c. Relaunch detection.** A `Pause` row (any age, any reason) with at least one ad ID that is ACTIVE in Step 2b **and** has `spend_7d` > 0 in ltv_cac.sql (or 7-day Meta spend > 0 in 2a) is running again → `Production Status` = `On Air`, clear `date:Paused date:start` (write null), clear `Pause reason` (null), and leave a comment `relaunch-detected <YYYY-MM-DD> · previous reason: <reason or none>` on the page. Report under *Relaunched*. ACTIVE-but-not-delivering ads do **not** trigger this — they stay paused and are not listed night after night; report only the count.

**d. Hit Ad transitions.** If the new SP status is `P2 Hit Ad` and `Hit ad` is `__NO__`/empty: set `Hit ad` = `"__YES__"`, then invoke the Skill tool `hit-ad-to-slack` with the highest-spend ad ID and the SP score so the win is posted to #hit-ads-library. If the Skill tool is unavailable, post a short card to #hit-ads-library yourself (name, ad ID, SP, CPFT, spend, Notion link). Fire only on the transition, never for a row already checked.

### 5.2 Metrics on live rows (On Air / Ready-to-Test with IDs)

Write the Step 4 target state, changed properties only.

### 5.3 Metrics on recently paused rows in REFRESH SCOPE

Same as 5.2. These are rows paused ≤ 14 days ago or still missing a reason — their final numbers are what the iteration review and Learnings rely on.

### 5.4 Hygiene

- **Archive:** `Pause` rows with `Paused date` more than 14 days ago **and** `Pause reason` filled → `Production Status` = `Archive`. Oldest first, at most 40 per run (the rest tomorrow). Skip rows without a `Paused date` and list them once under *Data notes*.
- **Re-ping missing reasons:** `Pause` rows 3+ days old with an empty `Pause reason`. Before pinging, `notion-get-comments` on the page and skip if a `pause-ping-sent` comment exists from the last 7 days. Add the rest to the batched ping (5.5) and comment `pause-ping-sent <YYYY-MM-DD>` after the Slack post succeeds.
- **Influencer license upkeep** (live rows with `Relation to Influencer Licenses`): if the related license's `Launch date` is empty, set it to the row's Launch date so the `License end day` / `License days left` formulas start. If a live row's `License days left` rollup is ≤ 3, add it to *⚠️ License expiring* in the report. When Step 2c creates a row whose c6 creator matches an influencer license created in the last 60 days (`SNS Account` / `Name`), set `Relation to Influencer Licenses` on the new row.

### 5.5 Slack

Post at most two messages to `C0ASFA5F1B3`, in this order:

1. **Owner ping** (only if the "needs reason" list is non-empty): one message tagging each row's Owner (resolve via `notion-get-users`; fall back to `<@U0A1E7WENQ6>`), one bullet per row with spend / CPFT and the Notion link, and the exact allowed `Pause reason` options. Never one message per row.
2. **Nightly report.** If nothing changed at all — no new rows, no status changes, no hit ads, no archives, no pings — post nothing and end silently.

```
🌙 *TW Creative Roadmap sync — <YYYY-MM-DD>*
Meta ACTIVE: X · tracked rows refreshed: X · new rows: X · archived: X

*New rows* (need Category/Format/Owner)
• <Name> — <Notion link> · $<7d spend>

*Went live / relaunched*
• <Name>: Ready-to-Test → On Air (ad <id>)
• <Name>: Pause → On Air (relaunch, $<7d spend>)

*Paused*
• <Name>: On Air → Pause (<reason or "needs owner input">)
• <campaign name>: X rows → Campaign End

*SP changes*
• <Name>: SP <old> → <new> · <old status> → <new status>

*🏆 Hit ads* — <Name> (SP <score>, CPFT $<cpft>) → posted to #hit-ads-library

*Watch flags* — X pause-candidates, X watch list (<names>)
*⚠️ License expiring* — <Name>: <days> days left (<end day>)
*Waiting on owners* — X paused rows still need a Pause reason (see ping above)
*Data notes* — <BigQuery MAX(date)>, skipped legacy ads, capped work carried to tomorrow, errors>
```

Report the same summary as your task output. Never delete rows, never write to Meta or BigQuery, never touch rows outside TRACKED ROW / REFRESH SCOPE except through rules 5.1c and 5.4.
