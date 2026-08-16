# Speak TW Creative Lifecycle Automation

End-to-end automation for the TW creative pipeline: idea intake → production → launch → performance tracking → pause/archive → winning-ad iteration → back to ideas.

## The boards

| Board | Notion data source | Role |
|---|---|---|
| 🗺️ Creatives Ideas | `collection://921b7b9b-effe-411d-9fc2-ca99eb48f328` | Idea backlog (fed by Slack #tw-creative bot, weekly Wed) |
| 🚧 TW Creative Roadmap | `collection://46a9a0c5-2240-4576-8574-ce81793d224b` | Production pipeline + live performance tracking |
| 🥯 TW/HK Design Board | `collection://6e5a40fb-e8f0-4f59-bc59-2b880e62e6b7` | Designer work queue (read-only for automation) |

## The routines (Claude Routines, fresh session per fire)

| Routine | Trigger ID | Schedule (Taipei) | What it does |
|---|---|---|---|
| Creative Ideas Sync to Notion | `trig_01CtXgi8zb5PzTXAMPzaAdwr` | Wed 17:00 | (pre-existing) Slack #tw-creative → Ideas board |
| TW Creative pipeline sync | `trig_011YVskPFCio6a2FqD5Pxx2o` | Daily 09:00 & 15:00 | Ideas (Status=In progress) → Roadmap rows (Plan); Roadmap (Ready-to-Test+) → Ideas marked Done; Ready-to-Test Slack ping tagging Kevin; design-done hints |
| TW Creative Roadmap nightly sync | `trig_01DeeYQ1LhpKj3dnq3xJavbW` | Daily 10:00 | Meta live ads + BigQuery SP scores → Roadmap (SP score/status, CPFT, spend, Last synced); creates rows for unknown live ads; pause detection + owner pings; Hit-ad → #hit-ads-library; watch flags; archive hygiene |
| TW winning creative iteration analyst | `trig_019r4irHEvw8tm7fmDcoZgJQ` | Mon 10:30 | Hit Ad / P2 Loser rows → Motion analysis → iteration brief → "Winning Iteration" idea in Ideas board (cap 5/week) |

Routine prompts (the source of truth for what each fired session does) are in [`routines/`](routines/). To change a routine's behavior, edit the prompt there and apply it with `update_trigger`.

## The lifecycle

```
Slack idea → Ideas board (Not started)
  → human sets Status = In progress
  → pipeline sync creates Roadmap row (Plan)          [row Name is a placeholder]
  → designer works it through Production; human renames row to the final Meta ad name
  → status Ready-to-Test → Slack ping tags the paid marketer
  → marketer launches in Meta → nightly sync matches the ad (by ad ID / name),
    flips the source idea to Done, stamps Launch date
  → nightly sync tracks SP score, CPFT, spend while live
      SP ≥ 2.0 + 10 trials + CPFT ≤ $58  → Hit Ad  (checkbox + #hit-ads-library post)
      SP ≥ 2.0 + 10 trials + CPFT > $58  → P2 Loser
      SP ≥ 2.0, <10 trials               → Winner
      1.5 ≤ SP < 2.0                     → Mid-tier
      SP < 1.5                           → Pause (SP status) + Pause-candidate flag
  → ad paused in Meta → row → Pause, Paused date stamped,
    Pause reason prefilled when knowable (License Expired / SP Threshold),
    otherwise the owner is pinged to fill Pause reason + Learnings
  → 14 days paused with reason filled → Archive
  → weekly: Hit Ads & P2 Losers get a Motion-informed iteration brief
    → new "Winning Iteration" idea → the loop restarts, with Parent creative lineage
```

## SP score

Not materialized anywhere — replicated from the Hex "[TW] Meta Ads SP Dashboard" (default baseline: Launch → 10-install, 7-day floor). The exact SQL is in [`sp_score.sql`](sp_score.sql), run nightly against BigQuery project `speak-v2-2a1f1`, source table `analytics.meta_ads_creative_report_funnel` (lags ~2 days; all date logic anchors to MAX(date)).

- SP = Σ over placements of spend_share × (CTR/benchmark_CTR + CTI/benchmark_CTI), leave-one-out benchmarks per placement × country × os
- Hex tiers: Strong ≥ 2.5 · Validated ≥ 2.0 · Below Baseline < 2.0; "winning" = SP ≥ 2.0
- TW Phase 2: at 10 cumulative trial starts, CPFT ≤ $58 → P2 Winner, > $58 → CPFT Loser
- The Mid-tier (1.5–2.0) and Pause (<1.5) cuts on the roadmap are our own convention, not Hex's

## Conventions & guardrails

- **Join key**: Roadmap row `Name` = exact Meta ad name; `Meta ad ID(s)` = comma-separated real ad IDs (15+ digits). Rows created from ideas carry a placeholder name that must be replaced before launch.
- **Sample rows**: the ~99 rows dated pre-2026-08-16 with fake ad IDs (`S55`, `UGC9`, …) are ignored by every routine.
- **Dedupe markers**: Ready-to-Test pings leave an `rt-ping-sent` Notion comment; pause-reason nags leave `pause-ping-sent`. Iteration ideas dedupe on `Ad id`/`Ref`.
- Routines only write to Notion and Slack. Nothing ever writes to Meta or BigQuery.
- Slack reports go to #tw-creative (`C0ASFA5F1B3`); silent when nothing changed. Paid marketer: Kevin Mo (`U0A1E7WENQ6`).

## Where to intervene

- **Prioritize ideas**: set Ideas Status = In progress (that's the promotion trigger).
- **Rename before launch**: give the roadmap row the final Meta ad name when handing to the marketer.
- **Fill Pause reason + Learnings** when pinged — Learnings feed the weekly iteration briefs.
- **Pause a routine**: `update_trigger` with `enabled: false`, or the claude.ai Routines UI.

## Known limitations (v1)

- `LTV/CAC` on the roadmap is not yet auto-filled (the Daily Ad Fatigue Report computes it but doesn't write to Notion) — candidate for v2.
- Watch-flag CPFT trend compares against yesterday's stored CPFT, not a true trailing average.
- Brand/awareness campaigns (Reach/Thruplay/Traffic) have no meaningful SP; their rows stay "Testing".
- Ads renamed in Meta after launch still match by ad ID, but the row name will drift from the Meta name until someone updates it.
