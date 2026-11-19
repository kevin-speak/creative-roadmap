# Daily sync — TW Creative Roadmap

One runbook, two modes. It keeps the Notion roadmap in step with #tw-ads, Meta and BigQuery, and closes ideas on the Ideas board once their creative is made, and posts **one** message to #tw-creative per run (nothing when nothing happened).

| Mode | When (Taipei) | Does |
|---|---|---|
| `INTAKE` | 07:00, 15:00 | Part A only: influencer intake, Ready-to-Test names and pings, closing ideas that reached the roadmap |
| `FULL` | 22:00 | Part B (Meta + BigQuery reconcile, statuses, metrics, hygiene), then Part A |

Pick the mode from the clock: `TZ=Asia/Taipei date +%H` ≥ 20 → `FULL`, otherwise `INTAKE`. A fire payload that starts with `MODE=FULL`, `MODE=INTAKE` or `DRY RUN` overrides the clock. In `DRY RUN` do every read and print the report you would have posted, but write nothing to Notion or Slack.

## IDs

- Roadmap: `collection://46a9a0c5-2240-4576-8574-ce81793d224b` ("TW Creative Roadmap 正式版", database `b44d9c2c3834497d9f1dcb3e140170c8`)
- Ideas: `collection://921b7b9b-effe-411d-9fc2-ca99eb48f328`
- Influencer Licenses: `collection://bf9dd8a5-0331-47a3-9d04-9c15bea80071`
- Meta ad account: Speak ZH `1148917790153640` (`ads_get_ad_entities`; reuse one 20-character `client_conversation_id` for the whole run)
- BigQuery project: `speak-v2-2a1f1` (`execute_sql_readonly` only)
- Slack: #tw-creative `C0ASFA5F1B3`, #tw-ads `C085DFM380K`. Paid marketer: Kevin Mo `<@U0A1E7WENQ6>`

Load connector tools with ToolSearch before first use.

## Rules that apply to every step

1. **Notion SQL returns at most 100 rows per call.** Every roadmap query in this runbook ends with `ORDER BY url LIMIT 100 OFFSET 0`; repeat with OFFSET 100, 200, … until a page has fewer than 100 rows. Never act on a single page of a paged query — a partial read is how duplicate rows were created before.
2. **Property names** (2026-11 schema): title `Item`, `Ad ID(s)`, `Description`. There is no `Name`, `Ad Name`, `Meta ad ID(s)`, `Watch flag`, `Hit ad`, `Learnings`, `Priority` or `Source`.
3. **Options are exact.** Never invent an option for a select. `Creator Name` is the one exception: a creator that is not in the list yet may be written as a new option, spelled as in the ad name.
   - `Production Status`: Plan · Production · Ready-to-Test · On Air · Pause · Archive
   - `SP status`: Testing · Pause · Mid-tier · P1 Winner · P2 Loser · P2 Hit Ad
   - `Pause reason`: Budget Capped · SP Threshold · License Expired · Graduate (Winning) · Fatigue · Campaign End · Other
   - `Market`: `TW 🇹🇼` · `HK 🇭🇰` · `Format`: Video · Image · Carousel · `Campaign Type`: Ongoing · Promo
   - `Production Type`: Creator · Licensed · Inhouse · Agency · Freelancer · Actor · `Version`: original · recut · whitelist · na
   - `Language Pair`: TW-EN · TW-JP · `Legacy Cate.`: Static · Video · Influencer · AI-Gen · Motion · UGC
4. **Names come from the repo, not from judgement.** To read an ad name, run `python3 -m roadmap.naming parse "<name>" …` (several names per call). It returns the convention (`v2` / `legacy` / `unknown`), the Notion properties the name states, validation errors and a `creative_key`. To produce a name for a row, run `python3 -m roadmap.naming build …`. See `docs/naming-convention.md`.
5. **Same creative = same `creative_key`.** A row's key comes from its `Description` when that holds a full legacy ad name, otherwise from its naming fields (Market, Production Date, Campaign Type, Format, Production Type, Version, Creator Name, Description). v2 keys ignore c9 (note) and c10, so the app-testing and web-scaling copies of one creative belong on one row.
6. **Tracked row** = at least one comma-separated token of `Ad ID(s)` matches `^[0-9]{15,}$`. **Refresh scope** = tracked rows that are On Air or Ready-to-Test, or Pause with (`Paused date` within 14 days or `Pause reason` empty). Archive rows and older paused rows are frozen.
7. **Write discipline.** One `notion-update-page` per row with only the properties that differ, plus `date:Last synced:start` = today (Taipei). No differing property → no write. Never write 0 for CPFT or LTV/CAC. Never overwrite a non-empty human field (`Item`, `Category`, `Owner`, naming fields, `Pause reason`). Dates go through `date:<Property>:start` as `YYYY-MM-DD`.
8. Never write to Meta or BigQuery. Never delete a page.

## STEP 0 — Preflight (both modes)

Run this contract query. If Notion rejects a column, the schema has changed: post `⚠️ TW roadmap sync stopped — Notion schema changed (<error>). Nothing was written. <@U0A1E7WENQ6>` to #tw-creative and stop.

```sql
SELECT url, "Item", "Production Status", "Description", "Ad ID(s)", "Reference", "Market",
       "Format", "Campaign Type", "Production Type", "Version", "Creator Name", "Language Pair",
       "Legacy Cate.", "Element", "Product Feature", "Channel", "Owner", "Pause reason",
       "SP status", "SP score", "CPFT", "LTV/CAC", "Spend to date", "Parent creative",
       "Relation to Influencer Licenses", "date:Production Date:start", "date:Launch date:start",
       "date:Paused date:start", "date:Last synced:start", createdTime, "Last edited time"
FROM "collection://46a9a0c5-2240-4576-8574-ce81793d224b"
WHERE "Production Status" IN ('Production','Ready-to-Test','On Air','Pause')
ORDER BY url LIMIT 100 OFFSET 0
```

Page it to the end (rule 1) and keep the result: it is the working set for both parts. Build `ad_id → row` from `Ad ID(s)`, and the list of **unbound rows** (Production / Ready-to-Test / On Air with no real ad ID).

---

# Part B — performance reconcile (`FULL` only)

## B1 — Meta (two targeted calls)

- **ACTIVE ads:** `level: ad`, `filtering: [{"field":"ad.effective_status","operator":"IN","value":["ACTIVE"]}]`, `fields: ["id","name","effective_status","created_time","campaign_id","campaign_name","spend"]`, `date_preset: last_7d`, `limit: 500`; follow `pagination.next_cursor` with every parameter unchanged. `spend` here is 7-day spend.
- **Tracked ads:** `level: ad`, `object_ids: [every tracked ID]` (chunks of 1000), `fields: ["id","name","effective_status","spend"]`, `date_preset: maximum` → lifetime spend and current status. An ID missing from the response is deleted. If the call fails twice, skip pause detection tonight and say so in the report.

Skip ads in legacy 2025 campaigns (campaign `120229358097810167`, or any campaign name marking a 25Qx quarter), and ignore rows the ACTIVE filter returns with another `effective_status`.

## B2 — BigQuery (two queries, verbatim)

Run `sql/sp_score.sql` and `sql/ltv_cac.sql` exactly as they are in the repo. Both anchor on the table's `MAX(date)` because the funnel table lags about two days; do not rewrite them.

- `sp_score.sql`: one row per (ad_id, country, os) for Taiwan and Hong Kong. Collapse per ad: best `sp_score`, summed trials and spend, CPFT = spend ÷ trials.
- `ltv_cac.sql`: one row per ad with `market`, `launch_date`, `cpft`, `ltv_cac`, `spend_7d`, `trial_starts_7d`, `cpft_7d`, `activity_total`, `dominant_campaign_name`, `campaign_stage` (`testing` / `scaling` / `other`).

For a row with several ad IDs: sum spend, trials, activity and 7-day figures before computing ratios, take the best SP, and take `campaign_stage` from the highest-spend ID.

## B3 — Status transitions (write these first)

**a. Went live, merged, or new.** For each ACTIVE ad whose ID is not on any row, parse its name (rule 4) and compare `creative_key`:

1. Key equals an **unbound row's** key → write the ID to `Ad ID(s)`, set `Production Status` = `On Air`, `Launch date` = the ad's `created_time` (Taipei day). *Went live.*
2. Key equals a **tracked row's** key → append the ID (comma-separated), keep the earliest Launch date. *Merged.* If that row is Pause or Archive, rule c below decides whether it comes back.
3. Otherwise create a row:
   - every property under `notion` in the parse output (for a v2 name that includes `Description` = c8; for a legacy name set `Description` = the full ad name instead)
   - `Item` = a short 繁體中文 display name, `[創作者/類型] - 主題`, unique among existing rows
   - `Ad ID(s)`, `Production Status` = `On Air`, `SP status` = `Testing`, `Channel` = `["Meta"]`
   - `Market` from the name, else `HK 🇭🇰` when the campaign name starts with `hk_`, else `TW 🇹🇼`
   - `Language Pair` from the name, else from `_tw-en_` / `_tw-jp_` in the campaign name
   - `Launch date` = created_time (Taipei day), `Last synced` = today
   - Leave `Category`, `Owner`, `Production Date` (unless the name states it) for a human.
   - At most 20 new rows per run, highest 7-day spend first; carry the rest to tomorrow.

Collect naming problems for the report: v2 names with `errors`, and names the parser calls `unknown`.

**b. Paused.** An On Air row whose every ad ID is non-ACTIVE or deleted → `Production Status` = `Pause`, `Paused date` = today. Prefill `Pause reason` with the first rule that fits; otherwise leave it empty (B5 closes it after 7 days):

1. `License Expired` — the row has a license relation and its `License days left` rollup (fetch the page) is ≤ 0.
2. `Budget Capped` — `campaign_stage` = `testing`, lifetime spend $140–300, and (`activity_total` < 10 or no SP score).
3. `SP Threshold` — tonight's SP status is `Pause`.
4. `Graduate (Winning)` — an ACTIVE ad with the same creative_key (or, for legacy names, the same c6 creator and c8 descriptor) runs in a campaign whose name contains `scaling`, `winning` or `cpr` and was created in the last 14 days.
5. `Fatigue` — `campaign_stage` = `scaling` and `trial_starts_7d` ≥ 5 with `cpft_7d` > 1.3 × lifetime CPFT. Never for testing-campaign ads.
6. `Campaign End` — five or more rows pause tonight and every ad of this row's `campaign_id` is non-ACTIVE.

**c. Relaunched.** A Pause row with an ad ID that is ACTIVE and has 7-day spend > 0 → `On Air`, clear `Paused date` and `Pause reason`, comment `relaunch-detected <YYYY-MM-DD> · previous reason: <reason or none>`.

**d. Hit ad.** When a row's SP status becomes `P2 Hit Ad` tonight and was something else before: read the page comments; if none contains `hit-ad-posted`, post the win with the `hit-ad-to-slack` skill (highest-spend ad ID + SP score; if the skill is unavailable post a short card to #hit-ads-library yourself), then comment `hit-ad-posted <YYYY-MM-DD>`.

## B4 — Metrics (rows in refresh scope)

- `SP score` = best sp_score, 2 decimals. `SP status`, first match: `P2 Hit Ad` (Taiwan, SP ≥ 2.0, ≥ 10 trials, CPFT ≤ 58) · `P2 Loser` (same, CPFT > 58) · `P1 Winner` (SP ≥ 2.0; all HK winners stop here) · `Mid-tier` (1.5–2.0) · `Pause` (< 1.5) · `Testing` (no score).
- `CPFT`, `LTV/CAC` from `ltv_cac.sql`, 2 decimals, only when non-NULL.
- `Spend to date` = lifetime Meta spend summed over the row's IDs, whole dollars.
- `Market` and `Launch date` only when the row's value is empty.
- **Naming backfill, in the same write:** if the row's `Description` parses as a name, add any property from its `notion` output that is empty on the row (Format, Campaign Type, Production Type, Version, Creator Name, Legacy Cate., Element, Product Feature, Language Pair).

Keep, for the report only (there is no field for it): **pause candidates** = On Air rows with SP < 1.5; **watch list** = On Air rows with `trial_starts_7d` ≥ 5 and `cpft_7d` > 1.3 × lifetime CPFT.

## B5 — Hygiene

- **Paused date missing:** a Pause row without `Paused date` gets today's date, so the clocks below start.
- **Stale pause reasons:** Pause rows whose `Pause reason` is empty and `Paused date` is more than 7 days ago → `Pause reason` = `Other`. No pings; the Monday review lists what is about to close.
- **Archive:** Pause rows paused more than 14 days ago with a reason → `Archive`. Oldest first, at most 40 per run.
- **Licenses:** on live rows with a license relation, set the license's empty `Launch date` to the row's Launch date; list rows with `License days left` ≤ 3 in the report. A new row whose creator matches a license created in the last 60 days gets the relation.

---

# Part A — intake (both modes)

## A1 — Close ideas that reached the roadmap

Ideas are **not** promoted to the roadmap automatically. An idea stays on the Ideas board until someone starts making it and creates the roadmap row themselves, with the idea's page URL in `Reference`. This step only closes the loop afterwards.

```sql
SELECT url, "Reference", "Production Status", "Ad ID(s)", "date:Launch date:start"
FROM "collection://46a9a0c5-2240-4576-8574-ce81793d224b"
WHERE "Reference" LIKE '%notion%' AND "Production Status" IN ('Ready-to-Test','On Air','Pause','Archive')
ORDER BY url LIMIT 100 OFFSET 0
```

```sql
SELECT url, "Concept", "Status"
FROM "collection://921b7b9b-effe-411d-9fc2-ca99eb48f328"
WHERE "Status" = 'In progress'
ORDER BY url LIMIT 100 OFFSET 0
```

Page both (rule 1) and compare by the 32-hex page ID inside each URL. An `In progress` idea that a roadmap row at Ready-to-Test or later points to → set the idea's `Status` to `Done`. An Archive row with no ad ID and no Launch date does not count: it is a placeholder that was archived without ever being made. Touch nothing else on the Ideas board, and never create a roadmap row here.

When a roadmap row's `Reference` is a `Winning Iteration` idea and its `Parent creative` is empty, set `Parent creative` to the roadmap page in that idea's `Ref`.

## A2 — #tw-ads influencer intake

Read #tw-ads for the last 3 days. A licence request is a message containing `請求支援` and `廣告上傳` that names a creator and a licence type (`廣告類型`). Skip requests whose `utm 名稱` or file link already exists on a licence row, and in-house upload requests (no creator, licence or utm).

For each new request create two linked pages:

1. **Licence** in the Influencer Licenses data source: `Name` = `{creator} {YYYY-MM} 廣告主授權（{duration}）` · `License periods` = days (一週 7 · 兩週 14 · 三週 21 · 四週 28 · 六週 42 · 兩個月 60 · 三個月 90; leave empty and flag if unclear) · `Licensed platform` = `["Meta"]` (+ `Google` when mentioned) · `Licenses Terms` = the 是否可剪輯、加框 line + the raw 廣告類型 · `File`, `Ad code`, `SNS Account`, `Account ID`, `Tracking ID` (utm) · `Influencer Priority` from the Emergency wording · `Launch date` empty. Body: request date, requester, due date, Slack permalink.
2. **Roadmap row**: `Item` = `{creator} - 廣告素材 ({YYYY.MM})` · `Production Status` = `Ready-to-Test` · `Production Type` = `Licensed` · `Version` = `original` · `Legacy Cate.` = `Influencer` · `Format` = `Video` (`Image` for a still) · `Campaign Type` = `Ongoing` · `Creator Name` = the creator · `Production Date` = the request date · `Language Pair` = `TW-EN` · `Channel` = `["Meta"]` · `Market` (`HK 🇭🇰` when the request says HK / 香港) · `Reference` = the file link · `Relation to Influencer Licenses` = the licence. Leave `Description` for the marketer.

## A3 — Ready-to-Test: name and ping

Candidates: Ready-to-Test rows with no real ad ID whose `Last edited time` is within the last 3 days. Read each candidate's comments and drop it if one contains `rt-ping-sent`.

For each remaining row, build its name from the row's fields:

```bash
python3 -m roadmap.naming build --market tw --date 2026-11-16 --campaign ongoing --format video \
  --production creator --version original --creator "MIP-Jenny" --description "peelfruit-phonespeak-v1" --language tw-en
```

(`--market` is `tw` / `hk`; `--creator` is the `Creator Name` values joined with `+`, or `na`; rows whose `Description` holds a full legacy name are announced with that name as it is.)

- `errors` empty → the row is **ready**: it goes in the report with its `ad_name` (Meta) and `file_name` (designer hand-off).
- `errors` non-empty → the row is **blocked**: list it with the missing fields. It is announced again once someone fills them (that edit puts it back in the 3-day window).

After the Slack message is posted, comment `rt-ping-sent <YYYY-MM-DD>` on each **ready** row. Blocked rows get no comment.

---

# Report (both modes)

Post one message to `C0ASFA5F1B3`. Include only sections that have content; if no section has any, post nothing.

```
🗺️ *TW Creative Roadmap — <YYYY-MM-DD HH:mm> · <FULL|INTAKE>*

*🚦 Ready to test* <@U0A1E7WENQ6>
• <Item> — <Notion link> · files <Reference or —>
  `<ad_name>`
*🧩 Ready-to-Test but can't be named yet*
• <Item> — <Notion link> · missing: <fields> · <@owner>

*🚀 Went live / merged / new*
• <Item>: went live (ad <id>)
• <Item>: new row — <Notion link> · needs Category / Owner
*⏸️ Paused*
• <Item>: <reason + evidence, or "no rule fits — defaults to Other on <date>">
*▶️ Relaunched* — <Item> ($<7d spend>)
*📈 SP changes*
• <Item>: SP <old> → <new> · <old status> → <new status>
*🏆 Hit ads* — <Item> (SP <score>, CPFT $<cpft>) → #hit-ads-library
*👀 Watch* — pause candidates: <names> · CPFT drifting: <names>
*⚠️ Licence expiring* — <Item>: <days> days left
*🧹 Housekeeping* — <n> archived · <n> pause reasons defaulted to Other · <n> ideas → Done · <n> licence intakes
*🔤 Naming issues* — <ad name>: <error>
*Data notes* — BigQuery through <MAX(date)> · skipped / capped work · errors
```

End your task output with the same report.
