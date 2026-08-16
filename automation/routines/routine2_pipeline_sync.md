Keep the Notion Creatives Ideas board, the TW Creative Roadmap, and the Design Board in step with each other, and announce anything that just became Ready-to-Test in #tw-creative.

## Setup — exact IDs

- Roadmap data source: `collection://46a9a0c5-2240-4576-8574-ce81793d224b` ("(WIP) TW Creative Roadmap")
- Ideas data source: `collection://921b7b9b-effe-411d-9fc2-ca99eb48f328` ("Creatives Ideas")
- Design Board data source: `collection://6e5a40fb-e8f0-4f59-bc59-2b880e62e6b7` ("TW/HK Design Board")
- Slack channel #tw-creative = `C0ASFA5F1B3`. Paid marketer to tag: Kevin Mo `<@U0A1E7WENQ6>`
- Notion tools: `notion-query-data-sources` (SQL mode), `notion-fetch`, `notion-create-pages`, `notion-update-page`, `notion-get-comments`, `notion-create-comment`, `notion-get-users`

**SAMPLE-ROW GUARD.** ~99 roadmap rows are seeded sample data — Production Status Pause/Archive with fake ad IDs like `S55`. Never update, comment on, or report them. Treat a roadmap row as real only if a comma-separated token in `Meta ad ID(s)` matches `^[0-9]{15,}$`, OR the row has no ad ID but sits in an active status (Plan / Production / Ready-to-Test / On Air / Scale) **and** `createdTime` is after 2026-08-16. Every row this routine creates satisfies the second condition, so newly created rows are in scope on later runs.

**Conventions.** Checkboxes are the strings `"__YES__"` / `"__NO__"`. Dates are written via expanded properties, e.g. `date:Launch date:start` = `YYYY-MM-DD`. Notion page URLs are the join key between the two boards — always compare full URLs, not titles.

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

**Type → Format mapping.** Ideas `Type` is one of UGC / Static / Motion / Video / Image. Roadmap `Format` is one of Video / Static / Carousel / UGC / Motion / Influencer. Map `Image → Static`; UGC, Static, Motion and Video map 1:1. If Type is empty, leave Format empty.

## STEP 1 — Load both boards

```sql
SELECT url, "Concept", "Status", "Category", "Type", "Pillar", "Owner", "Ad id", "Ref", "Memo"
FROM "collection://921b7b9b-effe-411d-9fc2-ca99eb48f328"
```

```sql
SELECT url, "Name", "Production Status", "Reference", "Meta ad ID(s)", "Category", "Format",
       "Owner", "Priority", "Parent creative", "Relation to Design Board", createdTime
FROM "collection://46a9a0c5-2240-4576-8574-ce81793d224b"
```

Build a set of every non-empty roadmap `Reference` URL. Notion page URLs come back in several equivalent forms — normalize by extracting the 32-hex page ID from each URL before comparing, so `https://app.notion.com/p/<id>` and `https://www.notion.so/<slug>-<id>` match.

## STEP 2 — Ideas → Roadmap (create work items)

For each Ideas row with `Status` = `In progress` whose page URL does **not** appear as any roadmap `Reference`:

Create a page in `collection://46a9a0c5-2240-4576-8574-ce81793d224b` with:

- `Name` = the idea's `Concept`, verbatim — this is a **placeholder**
- `Production Status` = `Plan`
- `Category` = mapped from the idea's `Pillar` by number prefix (omit if Pillar is empty)
- `Format` = mapped from the idea's `Type` (omit if empty)
- `Owner` = copied from the idea's `Owner` (person property; copy the user ID array as-is)
- `Reference` = the idea page URL (this is the join key — it must be set, or the row will be re-created on the next run)
- `Priority` = `P2`
- `Channel` = `["Meta"]`
- `Parent creative` — see the iteration rule below

**Iteration rule:** if the source idea has `Category` = `Winning Iteration` **and** its `Ref` points at a roadmap page, set the new row's `Parent creative` relation to that roadmap page. (Routine 3 writes those ideas; this is how the lineage gets closed.)

Page body for the new roadmap row:

```
Created from Creatives Ideas by the pipeline sync on <YYYY-MM-DD>.

⚠️ Before launch, a human fills two fields:
- Name: the clean 繁體中文 display name for this creative
- Ad Name: the exact Meta ad name (this + Meta ad ID(s) is how the nightly
  sync matches the row to Meta — Name itself is display-only)

Source idea: <idea page URL>
```

## STEP 3 — Roadmap → Ideas back-sync

For each roadmap row (passing the sample-row guard) whose `Reference` resolves to a page in the Ideas data source, and whose `Production Status` is `Ready-to-Test`, `On Air`, `Pause`, `Scale`, or `Archive` (i.e. Ready-to-Test **or later**):

- If that idea's `Status` is not already `Done`, set it to `Done` with `notion-update-page`.
- Leave every other idea property alone.

Ideas with Status `Archive` are also left alone — do not resurrect them.

## STEP 4 — Ready-to-Test pings

For each roadmap row with `Production Status` = `Ready-to-Test` (sample-row guard applies):

1. Call `notion-get-comments` on the page. If any comment contains the marker `rt-ping-sent`, skip — it has already been announced. Never re-ping.
2. Otherwise post to `C0ASFA5F1B3`:

```
🚦 *Ready to test* — <creative name>
Format: <Format> · Category: <Category> · Owner: <owner name>
Notion: <roadmap page URL>
Files: <Reference URL, or "—">
<@U0A1E7WENQ6> ready for launch setup.
```

3. Then `notion-create-comment` on that page with the text `rt-ping-sent <YYYY-MM-DD>`. Post the comment **after** the Slack message succeeds, so a Slack failure does not silently suppress the ping forever. If the comment write fails, say so in the summary.

## STEP 5 — Design Board hint (best effort)

For roadmap rows with `Production Status` = `Production` and a non-empty `Relation to Design Board`, look up the related Design Board pages:

```sql
SELECT url, "Name", "Status", "Relation to RM"
FROM "collection://6e5a40fb-e8f0-4f59-bc59-2b880e62e6b7"
WHERE "Status" = 'Completed'
```

Match the relation URLs (normalize page IDs as in Step 1). Where the linked Design Board item is `Completed` but the roadmap row is still `Production`, add a line to the Slack summary — **do not change the status yourself**; the human decides when it becomes Ready-to-Test. This step is best effort: if the relation is empty or the lookup fails, note "design check skipped" and continue.

## STEP 6 — Slack summary

Post one message to `C0ASFA5F1B3`. **If nothing happened — no rows created, no back-syncs, no Ready-to-Test pings, no design hints — post nothing and end silently.** The Ready-to-Test pings from Step 4 are separate messages; this summary comes after them.

```
🔁 *TW creative pipeline sync — <YYYY-MM-DD HH:mm TPE>*

*Ideas → Roadmap* (X created)
• <Concept> → <roadmap link> · Category <cat> · Format <fmt> (name is a placeholder)

*Roadmap → Ideas* (X marked Done)
• <Concept> → Done (<roadmap row> is <status>)

*Ready-to-Test announced* — X (see messages above)

*Design done, status still Production*
• <creative name> — Design Board item Completed <design link>
```

Report the same summary as your task output.

Guardrails: never create a second roadmap row for an idea that already has one (the `Reference` check is the only dedupe — get the URL normalization right), never edit a roadmap row that fails the sample-row guard, never change Production Status in this routine, and never delete anything.
