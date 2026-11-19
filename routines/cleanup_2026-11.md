# One-time cleanup — November 2026

Run once, by hand, after the 2026-11 schema change. It archives duplicate rows, fills the new naming fields from the ad names the rows already carry, and closes the pause-reason backlog. Nothing is deleted. Every step first produces a JSON plan from `roadmap/audit.py`; apply a plan only after Kevin has seen its counts.

## 1. Export

Run `sql/notion_roadmap_export.sql` against the roadmap, paging OFFSET 0, 100, 200 … until a page has fewer than 100 rows. Concatenate the `results` arrays into one JSON list, `rows.json`, in your scratchpad (never in the repo — it is public). Save the current `Creator Name` option names (from `notion-fetch` of the data source) as a JSON list, `creators.json`.

```bash
python3 -m roadmap.audit summary  rows.json
python3 -m roadmap.audit dupes    rows.json > plan_dupes.json
python3 -m roadmap.audit backfill rows.json --creator-options creators.json > plan_backfill.json
python3 -m roadmap.audit pauses   rows.json --today <YYYY-MM-DD> > plan_pauses.json
```

Post the three `counts` blocks and the `new_creator_options` list to Kevin and wait for a go.

## 2. Duplicates (`plan_dupes.json`)

- `idea` groups — several Plan rows created from the same idea. For each row under `archive`: `Production Status` = `Archive`, and comment `duplicate-of <keep url>`.
- `ad_id` groups — rows that share a Meta ad ID. On the keeper set `Ad ID(s)` = `keep_ad_ids`. On each row under `archive`: comment `duplicate-merged <YYYY-MM-DD> → <keep url> · ad IDs: <its IDs>`, then clear `Ad ID(s)` and set `Production Status` = `Archive`.
- `manual` — list them for Kevin; do not touch.

## 3. Naming backfill (`plan_backfill.json`)

For each entry in `updates`, write the properties under `set`. They are, by construction, empty on the row today. `Creator Name` values listed in `new_creator_options` create a new option; skip those rows' `Creator Name` if Kevin said not to create options.

How legacy names map to the new fields is documented in `docs/naming-convention.md` ("Reading legacy names"). The production-source mapping is a best guess (`ugc` → Creator, `influencer` → Licensed, `whitelist` → Creator + whitelist, `generic` / AI → Inhouse); a human can change any of it afterwards, and the daily sync never overwrites a filled field.

## 4. Pause backlog (`plan_pauses.json`)

- `stamp_paused_date_today` — set `Paused date` = today.
- `set_reason_other` — set `Pause reason` = `Other`.

The daily sync then archives them on its normal 14-day rule, 40 per night.

## 5. Report

Reply with counts applied per step, any page that failed to update, and the `manual` list.
