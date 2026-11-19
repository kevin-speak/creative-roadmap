# Weekly review — Mondays 10:30 Taipei

Two jobs, two messages in #tw-creative: iteration briefs for last week's proven ads, and the weekly log the team reads on Monday. This routine never edits roadmap rows and never writes to Meta.

## IDs and rules

- Roadmap: `collection://46a9a0c5-2240-4576-8574-ce81793d224b` · Ideas: `collection://921b7b9b-effe-411d-9fc2-ca99eb48f328`
- Motion Creative Analytics: `get_auth_context` first, then `get_creative_insights` with `insightType=SPEND` before any other insight call
- Slack #tw-creative `C0ASFA5F1B3` · Kevin Mo `<@U0A1E7WENQ6>`
- **Notion SQL returns at most 100 rows per call** — every query ends with `ORDER BY url LIMIT 100 OFFSET 0`; repeat with OFFSET 100, 200, … until a page has fewer than 100 rows.
- Property names (2026-11 schema): title `Item`, `Ad ID(s)`, `Description`. A real ad ID is a comma-separated token matching `^[0-9]{15,}$`.
- `DRY RUN` payload: do every read, print both messages, write nothing.

## Part 1 — Iteration briefs

### 1. Candidates

```sql
SELECT url, "Item", "Ad ID(s)", "Description", "SP status", "SP score", "CPFT", "Spend to date",
       "Market", "Format", "Legacy Cate.", "Production Type", "Creator Name", "Hook", "Category",
       "Production Status", "Pause reason", "Parent creative", "Owner", "date:Paused date:start"
FROM "collection://46a9a0c5-2240-4576-8574-ce81793d224b"
WHERE "SP status" IN ('P2 Hit Ad','P2 Loser') AND "Production Status" IN ('On Air','Pause')
ORDER BY url LIMIT 100 OFFSET 0
```

Keep rows with a real ad ID. Drop Pause rows whose reason is `Campaign End`, `SP Threshold` or `Other`.

### 2. Skip ads that already have a brief

```sql
SELECT url, "Concept", "Ad id", "Ref", "Status"
FROM "collection://921b7b9b-effe-411d-9fc2-ca99eb48f328"
WHERE "Category" = 'Winning Iteration'
ORDER BY url LIMIT 100 OFFSET 0
```

Drop a candidate when an existing idea's `Ad id` (split on commas, trimmed) equals one of its ad IDs, or its `Ref` is that roadmap page (compare the 32-hex page ID). This is the only dedupe.

### 3. Analyse at most 5

On Air first, then Pause; within each by `Spend to date` descending. For each ad pull what Motion has (`get_creative_summary`, `get_creative_transcript` for video, `get_creative_insights` HOOK). Motion coverage is partial: when it has nothing, write the brief from the row's `Hook`, its parsed name (`python3 -m roadmap.naming parse "<Description>"`) and its metrics, and say so in the brief.

### 4. Write the brief (page body of the new idea)

```
## Parent creative
<Item> · <roadmap page URL>
SP <score> · CPFT $<cpft> · Spend $<spend> · <SP status> · <Market> · <Format> · <Production Type>
Meta ad ID: <id>

## What's working
- Hook: <opening line / visual and why it lands>
- Angle: <the persuasion angle>
- Format: <what the execution does — pacing, on-screen text, talking head…>

## Keep
- <2–4 bullets: what must survive any variant>

## Iteration directions
1. <what changes, what stays, what it tests>
2. …
3. …

## Notes
<data caveats: Motion coverage, low trial volume, BigQuery lag, paused since…>

Pipeline note: when this idea becomes a roadmap row, set that row's `Parent creative`
relation to <roadmap page URL>.
```

- **P2 Hit Ad:** keep the winning body and vary the surface — new hooks, length cuts, audience variants, a still or carousel cutdown, the same angle with another creator.
- **P2 Loser:** the creative works (SP ≥ 2 on 10+ trials) and the economics do not (CPFT > $58). Every direction fixes conversion: offer clarity in the last three seconds, a more explicit CTA, ad-to-landing-page message match. Do not rebuild the hook.
- Be concrete: "open on the failed job interview instead of the app UI, same VO", not "test a new hook".

### 5. Create the idea

One page per ad in the Ideas data source: `Concept` = `[Iteration] <3–6 specific words>` · `Category` = `Winning Iteration` · `Status` = `Not started` · `Type` from the parent (`Legacy Cate.` UGC / Static / Motion / Video as is, Influencer → Video, AI-Gen → UGC; else `Format` Video → Video, Image / Carousel → Image) · `Ad id` = the primary ad ID · `Ref` = the roadmap page URL · `Memo` = one line of why · `Owner` copied.

### 6. Message 1 (skip when there were no candidates)

```
🔬 *Winning creative iteration review — week of <YYYY-MM-DD>*
Analysed X of Y eligible ads (live first, then highest spend; 5 per week).

*P2 Hit Ads*
• <Item> — SP <score> · CPFT $<cpft> · $<spend> · <On Air / paused since>
  → <idea Concept> <idea link> · Top direction: <one line>
*P2 Losers* (SP passes, CPFT over $58)
• …
*Next week* — X more: <names>
<@U0A1E7WENQ6> briefs are in the Ideas board.
```

## Part 2 — Weekly log (always posted)

```sql
SELECT url, "Item", "Production Status", "SP status", "SP score", "CPFT", "LTV/CAC", "Spend to date",
       "Market", "Format", "Production Type", "Version", "Campaign Type", "Creator Name", "Description",
       "Owner", "Pause reason", "Ad ID(s)", "date:Production Date:start",
       "date:Launch date:start", "date:Paused date:start"
FROM "collection://46a9a0c5-2240-4576-8574-ce81793d224b"
WHERE "Production Status" IN ('Ready-to-Test','On Air','Pause')
ORDER BY url LIMIT 100 OFFSET 0
```

"This week" = the 7 days ending today (Taipei).

1. **Winning creatives** — On Air rows with SP ≥ 2, by SP descending: top 8, 🆕 when launched in the last 14 days, plus totals.
2. **Pause reasons closing soon** — Pause rows with an empty reason: the daily sync sets them to `Other` once they are more than 7 days old. List each with the date it closes and tag its Owner (`notion-get-users`; fallback Kevin). This is the only reminder — there are no nightly pings.
3. **Creative online log** — rows launched this week, rows paused this week (with reason).
4. **Naming hygiene** — Ready-to-Test rows that cannot be named yet (list the missing naming fields; `python3 -m roadmap.naming build …` reports them) and On Air rows with no ad ID.

Views to link (they exist on the database — recreate with `notion-create-view` only if a fetch of database `b44d9c2c3834497d9f1dcb3e140170c8` shows one missing):

| View | Filter | URL |
|---|---|---|
| 🏆 Winning creatives | `SP score` ≥ 2, by SP | https://www.notion.so/b44d9c2c3834497d9f1dcb3e140170c8?v=3d6792ec2f10811aad8d000c465a7a27 |
| ⏸️ Pause reason needed | Pause and reason empty | https://www.notion.so/b44d9c2c3834497d9f1dcb3e140170c8?v=3d6792ec2f1081fe9731000c626e0325 |
| 🚀 Creative online log | Launch date set, newest first | https://www.notion.so/b44d9c2c3834497d9f1dcb3e140170c8?v=3d6792ec2f1081829fbb000ccd17b9fb |

```
📋 *TW Creative weekly log — week of <YYYY-MM-DD>*

*🏆 Winning creatives* — X on air (X P2 Hit Ads) · <view link>
• 🆕 <Item> — SP <score> · CPFT $<cpft> · $<spend> · <SP status> · <Market>

*⏸️ Pause reasons closing soon* — X open · <view link>
• <Item> — paused <date> · $<spend> · becomes Other on <date> · <@owner>
(none → "every paused row has a reason ✅")

*🚀 Creative online log* — X launched · X paused · <view link>
Launched: • <Item> — <Market> · <Format> · <Production Type> · $<spend> · <SP status>
Paused:   • <Item> — <reason or "open"> · $<spend>

*🔤 Naming hygiene* — X Ready-to-Test rows missing fields · X On Air rows without an ad ID
• <Item> — missing <fields> · <@owner>
```

End your task output with both messages.
