Turn last week's winning and near-miss Meta ads into concrete iteration briefs in the Notion Creatives Ideas board, one idea per ad, and report them to #tw-creative.

## Setup — exact IDs

- Roadmap data source: `collection://46a9a0c5-2240-4576-8574-ce81793d224b` (database title "🧪 (Beta) TW Creative Roadmap")
- Ideas data source: `collection://921b7b9b-effe-411d-9fc2-ca99eb48f328` ("Creatives Ideas")
- Meta ad account: Speak ZH, ID `1148917790153640`
- Motion Creative Analytics MCP: `get_auth_context`, `get_creative_insights`, `get_creative_summary`, `get_creative_transcript`
- Slack channel #tw-creative = `C0ASFA5F1B3`. Tag Kevin Mo `<@U0A1E7WENQ6>`
- Notion tools: `notion-query-data-sources` (SQL mode), `notion-fetch`, `notion-create-pages`
- Load MCP tools with ToolSearch before first use.

**Real ad IDs only.** Analyze rows where a comma-separated token in `Meta ad ID(s)` matches `^[0-9]{15,}$` (Motion needs the ad ID). Skip everything else silently.

**Conventions.** Checkboxes are the strings `"__YES__"` / `"__NO__"`. Dates use expanded properties (`date:Due:start`, `date:Launch:start`). Page URLs are the join key between boards — normalize by 32-hex page ID before comparing.

**SP status option names** (renamed 2026-08-21): `P2 Hit Ad` (was "Hit Ad"), `P2 Loser`, `P1 Winner` (was "Winner"), `Mid-tier`, `Pause`, `Testing`.

**Format → Type mapping** (roadmap `Format` → Ideas `Type`): Video→Video, Static→Static, UGC→UGC, Motion→Motion, Carousel→Static, Influencer→Video. If Format is empty, leave Type empty.

**Category → Pillar mapping**: map by the two-digit number prefix, then write the exact Ideas option string. The lists differ only in capitalization at 10 and 11: roadmap `10. Influencer` → Ideas `10. influencer`; roadmap `11. Meme / Trend` → Ideas `11. meme / trend`. All others are identical strings (`01. Speak 學習路徑`, `02. Product`, `03. Value Prop`, `04. Credibility`, `05. Bold Claim`, `06. Pain Point`, `07. Outcome`, `08. User Testimonials`, `09. Scenario`, `12. Campaign`, `13. 40+Male`).

## STEP 1 — Find the candidates

```sql
SELECT url, "Name", "Meta ad ID(s)", "SP status", "SP score", "CPFT", "Spend to date", "Market",
       "Learnings", "Category", "Format", "Source", "Hook", "Production Status", "Pause reason",
       "Parent creative", "Owner", "date:Paused date:start"
FROM "collection://46a9a0c5-2240-4576-8574-ce81793d224b"
WHERE "SP status" IN ('P2 Hit Ad','P2 Loser')
  AND "Production Status" IN ('On Air','Pause')
```

Then drop rows that are `Pause` with `Pause reason` = `Campaign End` or `SP Threshold` (promo-window artefacts and rejected creatives are not worth a brief). For rows with several ad IDs, use the first real numeric ID as the primary and note the others.

## STEP 2 — Skip ads that already have an iteration

```sql
SELECT url, "Concept", "Category", "Ad id", "Ref", "Status"
FROM "collection://921b7b9b-effe-411d-9fc2-ca99eb48f328"
WHERE "Category" = 'Winning Iteration'
```

Drop any candidate where an existing `Winning Iteration` idea has `Ad id` equal to one of that row's Meta ad IDs, **or** `Ref` pointing at that roadmap page. This is the only dedupe — it runs weekly, so getting it wrong duplicates the board fast. Match `Ad id` on exact string equality after trimming whitespace; a cell may hold a comma-separated list, so split it too.

## STEP 3 — Analyze (cap at 5 per run)

Rank the remaining candidates: `On Air` rows first, then `Pause` rows; within each group by `Spend to date` descending. Take **at most 5**. Note the skipped remainder for the summary — they resurface next week.

For each selected ad:

1. Call `get_auth_context` **first** (once per session). Use `defaultWorkspaceId` if there is exactly one workspace; if there are several, pick the Speak / Speak_ZH workspace and say which one you used in the summary.
2. Call `get_creative_insights` with `insightType=SPEND` **before any other insight type** — that response carries `goalMetric` and `spendThreshold`, which the other calls need to be interpretable. Then pull what's available for this ad: `get_creative_summary`, `get_creative_transcript` (video/UGC only), and a second `get_creative_insights` with `insightType=HOOK`.
3. Motion coverage is incomplete — an ad may have no summary, no transcript, or not be in Motion at all. That is not a failure: fall back to the ad's `Hook` field, the roadmap `Learnings` text, and the Meta ad name (the `c1!…c9!` segments encode format, angle, creator and campaign) and mark the brief "Motion data unavailable — brief written from roadmap fields only."
4. Combine with the row's SP score, CPFT, Spend to date, `Market` and `Learnings`.

## STEP 4 — Write the iteration brief

Compose the brief as the page body of the new idea (Step 5). Structure it exactly:

```
## Parent creative
<roadmap Name> · <roadmap page URL>
SP <score> · CPFT $<cpft> · Spend $<spend> · <SP status> · <Market> · Format <format> · Category <category>
Meta ad ID: <id>

## What's working
- Hook: <the opening line/visual and why it lands — from Motion transcript/summary or the Hook field>
- Angle: <the persuasion angle>
- Format: <what the execution does mechanically — pacing, on-screen text, talking head, etc.>

## Keep
- <2–4 bullets: the creative DNA that must survive any variant>

## Iteration directions
1. <direction — what changes, what stays, what it tests>
2. <direction>
3. <direction>

## Notes
<data caveats: Motion coverage, low trial volume, BigQuery ~2-day lag, paused since <date>, etc.>
<If the parent has a Parent creative itself, name the grandparent.>
```

Rules for the directions:

- **P2 Hit Ad parents:** keep the winning DNA and vary the surface — new hooks on the same body, length cuts (e.g. 30s → 15s → 6s), audience-specific variants (40+ male, working professionals, students), a static/carousel cutdown of a winning video, a same-angle recut with a different creator.
- **P2 Loser parents:** these already cleared SP ≥ 2.0 with 10+ trial starts — the creative works, the **conversion economics** do not (CPFT > $58). Focus every direction on fixing CPFT while preserving the high-SP creative DNA: sharper offer clarity in the last 3 seconds, a more explicit CTA, landing-page alignment (the promise in the ad matching the page headline), removing friction claims that attract non-converting curiosity clicks. Do **not** propose rebuilding the hook — the hook is the part that is working.
- Be concrete. "Test a new hook" is useless; "open on the failed job-interview moment instead of the app UI, keeping the same VO" is a brief.

Also add this line at the end of the brief, so the pipeline routine can close the lineage:

```
Pipeline note: when this idea becomes a roadmap row, set that row's `Parent creative`
relation to <roadmap page URL>.
```

## STEP 5 — Create the idea row

Create one page per analyzed ad in `collection://921b7b9b-effe-411d-9fc2-ca99eb48f328`:

- `Concept` = `[Iteration] <short descriptor>` — 3–6 words, specific, English. e.g. `[Iteration] Police Conversation — Hook Variants`, `[Iteration] Brick Hook — CPFT Fix`
- `Category` = `Winning Iteration`
- `Status` = `Not started`
- `Type` = mapped from the parent's `Format`
- `Pillar` = mapped from the parent's `Category` by number prefix
- `Ad id` = the parent's primary Meta ad ID
- `Ref` = the parent **roadmap page URL** (this is what Step 2 dedupes on next week — it must be set)
- `Memo` = one line of why, e.g. `P2 Hit Ad SP 8.5, iterate hooks` or `P2 Loser SP 2.4 CPFT $71, fix conversion`
- `Owner` = copy the parent row's Owner if set

Page body = the brief from Step 4.

Do **not** modify the parent roadmap row in this routine — no status changes, no relation writes. The pipeline routine sets `Parent creative` when the idea graduates into a roadmap row.

## STEP 6 — Slack summary

Post one message to `C0ASFA5F1B3`. If no candidates were left after dedupe, post nothing and end silently.

```
🔬 *Winning creative iteration review — week of <YYYY-MM-DD>*
Analyzed X of Y eligible ads (live first, then highest spend; cap 5/run).

*P2 Hit Ads*
• <ad name> — SP <score> · CPFT $<cpft> · $<spend> spend · <On Air / paused since>
  → <idea Concept> <idea page link>
  Top direction: <one line>

*P2 Losers* (SP passes, CPFT over $58)
• <ad name> — SP <score> · CPFT $<cpft> · $<spend> spend · <On Air / paused since>
  → <idea Concept> <idea page link>
  Top direction: <one line>

*Deferred to next run* — X ads: <names>
*Data notes* — <ads with no Motion coverage, any workspace ambiguity>

<@U0A1E7WENQ6> briefs are in the Ideas board, ready for prioritization.
```

## STEP 7 — Weekly update log (always posted, even when Step 6 was silent)

This is the human-inspection log for the week. It is a second, separate message in `C0ASFA5F1B3`, posted after the Step 6 summary (or on its own when there were no iteration candidates). It reads the roadmap only — no writes.

**Views (already exist on the roadmap database — link to them, do not create duplicates):**

| Section | View | URL |
|---|---|---|
| Winning creatives (SP ≥ 2) | 🏆 Winning creatives | https://www.notion.so/b44d9c2c3834497d9f1dcb3e140170c8?v=3d6792ec2f10811aad8d000c465a7a27 |
| Pause reason needed | ⏸️ Pause reason needed | https://www.notion.so/b44d9c2c3834497d9f1dcb3e140170c8?v=3d6792ec2f1081fe9731000c626e0325 |
| Creative online log | 🚀 Creative online log | https://www.notion.so/b44d9c2c3834497d9f1dcb3e140170c8?v=3d6792ec2f1081829fbb000ccd17b9fb |

If a `notion-fetch` of the database shows one of these views missing (someone deleted it), recreate it with `notion-create-view` on database `b44d9c2c3834497d9f1dcb3e140170c8`, data source `collection://46a9a0c5-2240-4576-8574-ce81793d224b`, using exactly these configurations, then use the new URL:
- 🏆 Winning creatives — `FILTER "SP score" >= 2; SORT BY "SP score" DESC`
- ⏸️ Pause reason needed — `FILTER "Production Status" = "Pause" AND "Pause reason" IS EMPTY; SORT BY "Paused date" DESC`
- 🚀 Creative online log — `FILTER "Launch date" IS NOT EMPTY; SORT BY "Launch date" DESC`

**Data (one query):**

```sql
SELECT url, "Name", "Production Status", "SP status", "SP score", "CPFT", "LTV/CAC", "Spend to date",
       "Market", "Format", "Owner", "Pause reason", "Hit ad",
       "date:Launch date:start" AS launch, "date:Paused date:start" AS paused
FROM "collection://46a9a0c5-2240-4576-8574-ce81793d224b"
WHERE "Production Status" IN ('On Air','Pause')
   OR date("date:Launch date:start") >= date('now','-7 days')
```

Compute, with "this week" = the 7 days ending today (Taipei):

1. **Winning creatives** — rows with `SP score` ≥ 2 and `Production Status` = `On Air`, sorted by SP desc. List the top 8 (Name · SP · CPFT · spend · SP status · Market); mark rows whose Launch date is within the last 14 days as `🆕`. Add the total count of winners on air and the number of `P2 Hit Ad` rows among them.
2. **Pause reason needed** — `Pause` rows with an empty `Pause reason`, newest Paused date first. List up to 10 (Name · paused date · spend · Owner mention via `notion-get-users`, fallback `<@U0A1E7WENQ6>`), then the total count. This is the back-fill queue; the view link is the working list.
3. **Creative online log** — (a) rows whose Launch date is within the last 7 days: Name · Market · Format · spend · SP status; (b) rows whose Paused date is within the last 7 days: Name · reason (or "reason needed") · spend. Include counts for both.

Post exactly this shape (Traditional Chinese labels are fine if the channel is mostly zh-TW; keep the structure):

```
📋 *TW Creative weekly log — week of <YYYY-MM-DD>*

*🏆 Winning creatives* — X on air (X P2 Hit Ads) · <view link>
• 🆕 <Name> — SP <score> · CPFT $<cpft> · $<spend> · <SP status> · <Market>
• <Name> — …

*⏸️ Pause reason needed* — X rows waiting · <view link>
• <Name> — paused <date> · $<spend> · <@owner>
• …
(none this week → "all paused rows have a reason ✅")

*🚀 Creative online log* — X launched · X paused this week · <view link>
Launched:
• <Name> — <Market> · <Format> · $<spend> · <SP status>
Paused:
• <Name> — <reason or "reason needed"> · $<spend>
```

Report the same summary as your task output. Never create more than one idea per parent ad in a single run, never write to Meta, and never touch roadmap rows.
