Keep the Notion Creatives Ideas board, the TW Creative Roadmap, the Influencer Licenses DB and the Design Board in step with each other, and announce anything that just became Ready-to-Test in #tw-creative.

## Setup — exact IDs

- Roadmap data source: `collection://46a9a0c5-2240-4576-8574-ce81793d224b` (database title "🧪 (Beta) TW Creative Roadmap")
- Ideas data source: `collection://921b7b9b-effe-411d-9fc2-ca99eb48f328` ("Creatives Ideas")
- Design Board data source: `collection://6e5a40fb-e8f0-4f59-bc59-2b880e62e6b7` ("TW/HK Design Board")
- Influencer Licenses data source: `collection://bf9dd8a5-0331-47a3-9d04-9c15bea80071`
- Slack channel #tw-creative = `C0ASFA5F1B3`; #tw-ads = `C085DFM380K`. Paid marketer to tag: Kevin Mo `<@U0A1E7WENQ6>`
- Notion tools: `notion-query-data-sources` (SQL mode), `notion-fetch`, `notion-create-pages`, `notion-update-page`, `notion-get-comments`, `notion-create-comment`, `notion-get-users`
- Load MCP tools with ToolSearch before first use.

## Definitions

**Ownership split.** This routine owns rows that have **no** real Meta ad ID (a real ID is a comma-separated token in `Meta ad ID(s)` matching `^[0-9]{15,}$`): Plan / Production / Ready-to-Test work items. Rows with a real ad ID are owned by the nightly sync — read them, never edit them here. The only cross-board writes this routine makes are `Status = Done` on Ideas (Step 3) and `Launch date` on license rows (nightly sync does that, not this routine).

**Conventions.** Checkboxes are the strings `"__YES__"` / `"__NO__"`. Dates are written via expanded properties, e.g. `date:Launch date:start` = `YYYY-MM-DD`. Notion page URLs are the join key between boards — normalize by extracting the 32-hex page ID before comparing, so `https://app.notion.com/p/<id>`, `https://app.notion.com/<id>` and `https://www.notion.so/<slug>-<id>` match.

**Option lists (exact strings — never invent one).**
- Roadmap `Production Status`: Plan · Production · Ready-to-Test · On Air · Pause · Archive (no "Scale").
- Roadmap `Format`: Video · Static · Carousel · UGC · Motion · Influencer. `Source`: Inhouse · Influencer · UGC. `Priority`: P0 · P1 · P2 · P3. `Market`: `TW 🇹🇼` · `HK 🇭🇰`.
- Ideas `Status`: Not started · Pending · In progress · Done · Archive. Only `In progress` promotes; `Pending`, `Not started` and `Archive` are ignored.
- Ideas `Type`: UGC · Static · Motion · Video · Image. Ideas `Category`: Idea · Testing · TA · Winning Iteration · Comptetior (sic).
- Design Board `Status`: Brief (Not Started) · Checking · Completed · Contract · Next Up · This Week.

**Pillar ↔ Category mapping.** The Ideas `Pillar` and roadmap `Category` option lists use the same numbering but different capitalization (`10. influencer` vs `10. Influencer`, `11. meme / trend` vs `11. Meme / Trend`). **Always map by the two-digit number prefix**, then write the exact string from the destination board's option list:

| # | Ideas `Pillar` | Roadmap `Category` |
|---|---|---|
| 01 | 01. Speak 學習路徑 | 01. Speak 學習路徑 |
| 02 | 02. Product | 02. Product |
| 03 | 03. Value Prop | 03. Value Prop |
| 04 | 04. Credibility | 04. Credibility |
| 05 | 05. Bold Claim | 05. Bold Claim |
| 06 | 06. Pain Point | 06. Pain Point |
| 07 | 07. Outcome | 07. Outcome |
| 08 | 08. User Testimonials | 08. User Testimonials |
| 09 | 09. Scenario | 09. Scenario |
| 10 | 10. influencer | 10. Influencer |
| 11 | 11. meme / trend | 11. Meme / Trend |
| 12 | 12. Campaign | 12. Campaign |
| 13 | 13. 40+Male | 13. 40+Male |

**Type → Format mapping.** `Image → Static`; UGC, Static, Motion and Video map 1:1. If Type is empty, leave Format empty.

## STEP 1 — Load both boards (two queries)

```sql
SELECT url, "Concept", "Status", "Category", "Type", "Pillar", "Owner", "Ad id", "Ref", "Memo"
FROM "collection://921b7b9b-effe-411d-9fc2-ca99eb48f328"
WHERE "Status" IN ('In progress','Done')
```

```sql
SELECT url, "Name", "Production Status", "Reference", "Meta ad ID(s)", "Category", "Format",
       "Owner", "Priority", "Parent creative", "Relation to Design Board", createdTime
FROM "collection://46a9a0c5-2240-4576-8574-ce81793d224b"
WHERE "Production Status" NOT IN ('Archive')
```

Build a set of every non-empty roadmap `Reference` page ID (normalized as above).

## STEP 2 — Ideas → Roadmap (create work items)

For each Ideas row with `Status` = `In progress` whose normalized page ID does **not** appear as any roadmap `Reference`, create a page in `collection://46a9a0c5-2240-4576-8574-ce81793d224b` with:

- `Name` = the idea's `Concept`, verbatim — a **placeholder** the team renames before launch
- `Production Status` = `Plan`
- `Category` = mapped from `Pillar` by number prefix (omit if empty)
- `Format` = mapped from `Type` (omit if empty)
- `Owner` = copied from the idea's `Owner` (copy the user ID array as-is)
- `Reference` = the idea page URL (join key — it must be set, or the row is re-created next run)
- `Priority` = `P2`, `Channel` = `["Meta"]`, `Market` = `TW 🇹🇼`
- `Parent creative` — if the idea has `Category` = `Winning Iteration` **and** its `Ref` points at a roadmap page, set the relation to that page (this closes the lineage the iteration analyst opened).

Page body:

```
Created from Creatives Ideas by the pipeline sync on <YYYY-MM-DD>.

⚠️ Before launch, a human fills two fields:
- Name: the clean 繁體中文 display name for this creative
- Ad Name: the exact Meta ad name (this + Meta ad ID(s) is how the nightly
  sync matches the row to Meta — Name itself is display-only)

Source idea: <idea page URL>
```

Cap: 20 new rows per run (oldest ideas first); list any remainder in the summary.

## STEP 3 — Roadmap → Ideas back-sync

For each roadmap row whose `Reference` resolves to an Ideas page and whose `Production Status` is `Ready-to-Test`, `On Air`, `Pause` or `Archive`: if the idea's `Status` is not `Done`, set it to `Done`. Touch nothing else on the idea; never resurrect `Archive` ideas.

## STEP 3.5 — #tw-ads influencer intake (daily)

Read #tw-ads (`C085DFM380K`) for the past 3 days (`slack_read_channel`, `oldest` = 3 days ago). Find 請求支援 posts — messages containing `請求支援` AND `廣告上傳`. They follow a fixed template: `專案類別` (creator + link), `Due Date`, `Emergency`, `廣告檔案` (Drive link or fbadcode), `是否可剪輯、加框`, `廣告類型` (license, e.g. "Meta 廣告主四週"), `創作者帳號`, `utm 名稱`.

Dedupe against the Influencer Licenses DB: skip if a license row already has the same `Tracking ID` (utm) or the same `File` link.

For each new request create TWO linked pages:

1. **License row** in `collection://bf9dd8a5-0331-47a3-9d04-9c15bea80071`:
   - `Name` = `{creator} {YYYY-MM} 廣告主授權（{duration}）`
   - `License periods` = days parsed from 廣告類型: 一週7 / 兩週14 / 三週21 / 四週28 / 六週42 / 兩個月60 / 三個月90; if unparseable, leave empty and flag it
   - `Licensed platform` = ["Meta"] (+ "Google" if the type mentions YT/YouTube/Google)
   - `Licenses Terms` = the 是否可剪輯加框 line + any 合作片段 timestamps + the raw 廣告類型 text
   - `File` = the Drive/FB link; `Ad code` = fbadcode if present; `SNS Account` = creator account URL; `Account ID` = the creator handle (text after the last `/` or `@`); `Tracking ID` = the utm 名稱
   - `Influencer Priority` from Emergency/Due wording: 大咖/High → P0-P1, Medium → P2, Low → P3
   - `Launch date` = LEAVE EMPTY (the nightly sync stamps it when the ad goes live)
   - Page body: request date, requester, due-date text, Slack permalink
2. **Roadmap row** in `collection://46a9a0c5-2240-4576-8574-ce81793d224b`:
   - `Name` = `{creator} - 廣告素材 ({YYYY.MM})` (placeholder 中文 — humans refine it)
   - `Production Status` = `Ready-to-Test` (the asset arrives production-ready; the Step 4 ping tags Kevin automatically)
   - `Source` = `Influencer`, `Format` = `Influencer`, `Category` = `10. Influencer`, `Channel` = `["Meta"]`, `Market` = `TW 🇹🇼` (or `HK 🇭🇰` when the request says HK / 香港)
   - `Priority` mirroring the license priority (P4 → P3)
   - `Reference` = the 廣告檔案 link; `Relation to Influencer Licenses` = the license row just created
   - `Ad Name` and `Meta ad ID(s)` = LEAVE EMPTY — Kevin fills them after uploading to Meta (the nightly sync then binds the ad by `Ad Name`)
   - Page body: due-date text, utm 名稱, Slack permalink

List every intake in the Slack summary under `*Influencer intake*`.

## STEP 4 — Ready-to-Test pings

Collect the roadmap rows with `Production Status` = `Ready-to-Test` and no real ad ID. For each, `notion-get-comments` and drop it if any comment contains `rt-ping-sent` — never re-ping.

- **1–5 unannounced rows:** post one message per row to `C0ASFA5F1B3`:

```
🚦 *Ready to test* — <creative name>
Format: <Format> · Category: <Category> · Owner: <owner name>
Notion: <roadmap page URL>
Files: <Reference URL, or "—">
<@U0A1E7WENQ6> ready for launch setup.
```

- **6 or more unannounced rows** (bulk import): post ONE digest message instead — header `🚦 *Ready to test — X creatives*`, one bullet per row (name · Format · Notion link), tagging `<@U0A1E7WENQ6>` once.

After the Slack post succeeds, `notion-create-comment` on each announced page with `rt-ping-sent <YYYY-MM-DD>`. Post the comment **after** the Slack message so a Slack failure does not suppress the ping forever; if a comment write fails, say so in the summary.

## STEP 5 — Design Board hint (best effort)

For roadmap rows with `Production Status` = `Production` and a non-empty `Relation to Design Board`:

```sql
SELECT url, "Name", "Status", "Relation to RM"
FROM "collection://6e5a40fb-e8f0-4f59-bc59-2b880e62e6b7"
WHERE "Status" = 'Completed'
```

Where the linked Design Board item is `Completed` but the roadmap row is still `Production`, add a line to the summary — **do not change the status yourself**. Skip this step silently when there are no Production rows; if the lookup fails, note "design check skipped" and continue.

## STEP 6 — Slack summary

Post one message to `C0ASFA5F1B3`. **If nothing happened — no rows created, no back-syncs, no Ready-to-Test pings, no intake, no design hints — post nothing and end silently.**

```
🔁 *TW creative pipeline sync — <YYYY-MM-DD HH:mm TPE>*

*Ideas → Roadmap* (X created)
• <Concept> → <roadmap link> · Category <cat> · Format <fmt> (name is a placeholder)

*Roadmap → Ideas* (X marked Done)
• <Concept> → Done (<roadmap row> is <status>)

*Ready-to-Test announced* — X (see messages above)

*Influencer intake* — X (<creator> · license <link> · roadmap <link>)

*Design done, status still Production*
• <creative name> — Design Board item Completed <design link>
```

Report the same summary as your task output.

Guardrails: never create a second roadmap row for an idea that already has one (the `Reference` check is the only dedupe — get the URL normalization right), never edit a row that has a real Meta ad ID, never change `Production Status` in this routine, and never delete anything.
