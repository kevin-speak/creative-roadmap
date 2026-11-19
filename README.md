# TW Creative Roadmap hub

The home of Speak Taiwan / Hong Kong's paid-creative roadmap: how a creative is named, how it moves from idea to archive, what the Notion boards look like, and the runbooks the scheduled tasks execute.

The roadmap itself lives in Notion ([TW Creative Roadmap 正式版](https://app.notion.com/p/b44d9c2c3834497d9f1dcb3e140170c8)). This repository is the rulebook and the automation around it.

> **Status, 2026-11-19:** the roadmap tasks are paused while the process is rebuilt for the new naming convention. See [docs/operations.md](docs/operations.md) for the go-live checklist.

## Start here

| I want to… | Read |
|---|---|
| Name a creative, or read an ad name | [docs/naming-convention.md](docs/naming-convention.md) |
| Know who does what, and when | [docs/process.md](docs/process.md) |
| Look up a Notion property or option | [docs/notion-schema.md](docs/notion-schema.md) |
| Change what the automation does | [routines/](routines/) — the runbooks are the source of truth |
| Switch tasks on or off, or debug a run | [docs/operations.md](docs/operations.md) |

## The naming convention in one line

```
c1:tw_c2:261116_c3:ongoing_c4:video_c5:creator_c6:original_c7:mip-jenny_c8:peelfruit-phonespeak-v1_c9:app-testing_c10:tw-en
   country date    campaign   format   production  version    creator      description               note           language
```

Fill the naming fields on the Notion row; the daily sync builds this string when the row reaches Ready-to-Test and posts it to #tw-creative. Launch the ad in Meta under that exact name and the sync binds it to the row the same night.

## What runs

| Run | Taipei time | What it does |
|---|---|---|
| Daily sync — intake | 07:00, 15:00 | Ideas → Plan rows, influencer licence intake from #tw-ads, Ready-to-Test names and pings |
| Daily sync — full | 22:00 | Binds live Meta ads to rows, pause / relaunch detection, SP score, CPFT, LTV/CAC, spend, hit ads, archive |
| Weekly review | Mon 10:30 | Iteration briefs for proven ads, weekly log, pause reasons closing soon, naming hygiene |
| Ideas intake | Wed 17:00 | #tw-creative posts → Ideas board |
| Ideas brief | every second Thu 09:45 | Preview and suggested priority on each new idea, plus the pre-read for the bi-weekly roadmap meeting |

## Layout

```
docs/        process, naming convention, Notion schema, operations
routines/    ideas_intake.md · ideas_brief.md · daily_sync.md · weekly_review.md · cleanup_2026-11.md (one-time)
roadmap/     naming.py (parse / build / match names) · audit.py (duplicates, backfill, pause backlog)
sql/         sp_score.sql · ltv_cac.sql (BigQuery) · notion_roadmap_export.sql (Notion)
meta_api/    read-only Marketing API client
tests/       python3 -m unittest discover -s tests -t .
```

## Ground rules

- Automation writes to Notion and Slack only. Meta and BigQuery are read-only.
- Automation never deletes a page and never overwrites a field a person filled.
- This repository is public: no exports, creator lists or performance data in commits.
