# Speak TW Creative Lifecycle Automation

End-to-end automation for the TW (+ HK) creative pipeline: idea intake → production → launch → performance tracking → pause/archive → winning-ad iteration → back to ideas.

## The boards

| Board | Notion data source | Role |
|---|---|---|
| 🗺️ Creatives Ideas | `collection://921b7b9b-effe-411d-9fc2-ca99eb48f328` | Idea backlog (fed by Slack #tw-creative bot, weekly Wed) |
| 🧪 (Beta) TW Creative Roadmap | `collection://46a9a0c5-2240-4576-8574-ce81793d224b` | Production pipeline + live performance tracking (TW and HK ads) |
| Influencer Licenses Database | `collection://bf9dd8a5-0331-47a3-9d04-9c15bea80071` | License terms / countdown per influencer asset |
| 🥯 TW/HK Design Board | `collection://6e5a40fb-e8f0-4f59-bc59-2b880e62e6b7` | Designer work queue (read-only for automation) |

## The routines

Routine prompts (the source of truth for what each fired session does) are in [`routines/`](routines/). To change a routine's behavior, edit the runbook, push to the repo's default branch (`claude/speak-tw-creative-automation-1w6h9d`), and the next fire picks it up.

| Routine | Schedule (Taipei) | Runbook | What it does |
|---|---|---|---|
| Creative Ideas Sync to Notion | Wed 17:00 | (prompt lives in the Routine itself, `trig_01CtXgi8zb5PzTXAMPzaAdwr`) | Slack #tw-creative → Ideas board |
| TW Creative pipeline sync | 07:00 & 15:00 | `routine2_pipeline_sync.md` | Ideas (In progress) → Roadmap Plan rows; Roadmap (Ready-to-Test+) → Ideas Done; #tw-ads influencer intake → license + roadmap rows; Ready-to-Test pings (digest when 6+); design-done hints |
| TW Creative Roadmap nightly sync | 22:00 | `routine1_nightly_sync.md` | Meta (ACTIVE + tracked IDs) + BigQuery SP / LTV-CAC → Roadmap; pause / relaunch / went-live detection; reason prefill; Hit-ad → #hit-ads-library; watch flags; archive hygiene; batched owner ping |
| TW winning creative iteration analyst | Mon 10:30 | `routine3_winner_iteration.md` | P2 Hit Ad / P2 Loser rows → Motion analysis → iteration brief → "Winning Iteration" idea (cap 5/week, live rows first) |

### Two generations of triggers exist — which one is live

| Set | Trigger IDs (nightly / pipeline / iteration) | How it fires | Status (2026-09-09) |
|---|---|---|---|
| **A — persistent session** (created 2026-08-16) | `trig_01EZ44tzBdZfTfJy1scvf128` / `trig_011EhN2rJaHcNoAKHPAY8it3` / `trig_01JqGLRu34KTW38yFpWNpDDt` | Fires into session `session_014szRHcYSqZhSCd695DuyA9`, which holds the connectors | Enabled. Works, but the session runs in *auto* permission mode and regularly stalls on a permission prompt (Kevin has to approve in the app), and it is at ~70% of its context window. Its prompts cannot be edited from another session; they tell the session to `git fetch` the branch, so it does pick up runbook changes. |
| **B — fresh session per fire** (created 2026-09-03 from the Routines UI, so they carry connector grants) | `trig_01Mu2vcfPW9zXbT9N1s9nXn8` / `trig_01Bz5iWJZ9cBkXjhd2YeCaF4` / `trig_01NJznSip628rN38F1f1jHAL` | New session each time; the prompt clones this public repo first, then runs the runbook | Prompts and schedules updated 2026-09-09. Disabled until a DRY RUN fire completes without a permission stall — see "Switching to set B" below. |

**Why not a third set:** triggers created by an agent (`create_trigger` from a session) carry neither connector grants nor a repo source in this org — verified again 2026-09-09 (created and deleted the same day). Only Routines created from the claude.ai Routines UI store connector grants. If set B ever needs re-creating, do it from the UI and paste the prompt text from set B (it is self-contained: it clones the repo itself).

**Switching to set B:** a *scheduled* fire is the only valid test. Two `fire_trigger` DRY RUNs on 2026-09-09 ended idle within a minute and never reached Notion/Slack: sessions started by `fire_trigger` from an agent session get **no connector tools** at all, whereas the scheduled fire on 2026-09-03 did have them (it stalled on a Meta permission prompt, which is a different problem). So: the set-B nightly trigger is enabled alongside set A for its 22:00 Taipei scheduled fire; if that session ends idle and posts the 🌙 report to #tw-creative, enable the other two set-B triggers and disable set A. If it ends in *requires action* (permission prompt), the auto-mode classifier still blocks connector tools in fresh sessions — keep set A and approve its prompts in the app, and consider re-creating set B from the Routines UI (UI-created Routines are documented to run connector tools without prompting).

**Permissions:** [`.claude/settings.json`](../.claude/settings.json) pre-allows every Notion tool (reads and writes — `notion-update-page`, `notion-create-pages`, `notion-create-comment` are listed explicitly so the auto-mode classifier never has to judge them), all Slack and Motion tools, read-only BigQuery and read-only Meta tools, and *denies* Meta writes and non-read-only BigQuery. Any session that starts from this repo can therefore only ever write to Notion and Slack, and never waits on a prompt for a Notion write. Project settings are read at session start from the cloned default branch, so this only takes effect once the file is on `claude/speak-tw-creative-automation-1w6h9d`; the persistent session (set A) loaded its settings when it was created on 2026-08-16 and needs a fresh start (or an "always allow" on its next Notion prompt) to pick them up.

## The lifecycle

```
Slack idea → Ideas board (Not started)
  → human sets Status = In progress
  → pipeline sync creates Roadmap row (Plan)          [row Name is a placeholder]
  → designer works it through Production; human renames row + fills Ad Name
  → status Ready-to-Test → Slack ping tags the paid marketer
  → marketer launches in Meta → nightly sync binds the ad (by Ad Name, then by ID),
    flips the row to On Air, stamps Launch date, marks the idea Done
  → nightly sync tracks SP score, CPFT, LTV/CAC, spend, Market while live
      TW: SP ≥ 2.0 + 10 trials + CPFT ≤ $58  → P2 Hit Ad  (checkbox + #hit-ads-library post)
          SP ≥ 2.0 + 10 trials + CPFT > $58  → P2 Loser
          SP ≥ 2.0, <10 trials               → P1 Winner
      HK: SP ≥ 2.0                           → P1 Winner  (no HK CPFT threshold yet)
      1.5 ≤ SP < 2.0                         → Mid-tier
      SP < 1.5                               → Pause (SP status) + Pause-candidate flag
  → ad paused in Meta → row → Pause, Paused date stamped,
    Pause reason prefilled when knowable, in this order:
      License Expired · Budget Capped (testing campaign, $140–300 lifetime, <10 installs)
      · SP Threshold · Graduate (Winning) · Fatigue (scaling/winning campaigns only,
      CPFT decaying) · Campaign End (campaign switched off; humans also use it for
      promo-season end) — otherwise one batched owner ping
  → ad ACTIVE and spending again → row → On Air (relaunch detected, comment left)
  → 14 days paused with reason filled → Archive (≤ 40 per night)
  → weekly: P2 Hit Ads & P2 Losers (live first) get a Motion-informed iteration brief
    → new "Winning Iteration" idea → the loop restarts, with Parent creative lineage
```

## SP score

Not materialized anywhere — replicated from the Hex "[TW] Meta Ads SP Dashboard" (default baseline: Launch → 10-install, 7-day floor). The SQL is [`sp_score.sql`](sp_score.sql), run nightly against BigQuery project `speak-v2-2a1f1`, source table `analytics.meta_ads_creative_report_funnel` (lags ~2 days; all date logic anchors to MAX(date)).

- SP = Σ over placements of spend_share × (CTR/benchmark_CTR + CTI/benchmark_CTI), leave-one-out benchmarks per placement × country × os
- Since 2026-09-08 the query scores **Taiwan and Hong Kong**; markets never mix because every CTE is keyed by country. Before that HK rows sat at "Testing" forever.
- Hex tiers: Strong ≥ 2.5 · Validated ≥ 2.0 · Below Baseline < 2.0; "winning" = SP ≥ 2.0
- TW Phase 2: at 10 cumulative trial starts, CPFT ≤ $58 → P2 Hit Ad, > $58 → P2 Loser. **HK has no agreed CPFT threshold**, so HK rows stop at P1 Winner; add an HK threshold to `sp_score.sql` (`phase2_result` CASE) and to routine 1 Step 4 when one is decided.
- The Mid-tier (1.5–2.0) and Pause (<1.5) cuts on the roadmap are our own convention, not Hex's

## LTV/CAC, CPFT and the 7-day window

[`ltv_cac.sql`](ltv_cac.sql) emits one row per ad with lifetime `cpft`, `ltv_cac` (fatigue-report methodology, cohort LTV month 35), the ad's dominant `market` (Taiwan / Hong Kong — this is what fills the roadmap `Market` field), `launch_date`, and since 2026-09-08 a trailing-7-day window (`spend_7d`, `trial_starts_7d`, `cpft_7d`). The nightly sync uses `cpft_7d` vs lifetime `cpft` for the Watch List flag (> 30% worse on ≥ 5 trials) and `spend_7d > 0` to tell a relaunched ad from one that is merely ACTIVE.

## Conventions & guardrails

- **Join key**: `Meta ad ID(s)` (primary) + `Ad Name` = exact Meta ad name (secondary). Row `Name` is a clean 繁體中文 display name; the nightly sync generates one only for ads it discovers on its own. (The Notion property description of `Name` still says "must equal Meta ad name" — that text is stale.)
- **Ownership split** (replaces the old "sample-row guard" — the ~99 fake-ID sample rows are gone): rows with a real 15+ digit ad ID belong to the nightly sync; rows without one belong to the pipeline sync. The nightly sync only refreshes metrics on rows in *refresh scope* (On Air / Ready-to-Test, or paused ≤ 14 days ago or without a reason); older paused and archived rows are frozen.
- **Campaign scope**: current campaigns only (26Q3 + ongoing TW/HK trial/purchase testing/scaling/winning). Legacy 25Qx campaigns (e.g. `TW_Meta_N/A_M3_Q3Reach_brandmarketing`) are skipped.
- **Option lists are exact** and listed in each runbook. `Production Status` has no "Scale" any more; `SP status` options were renamed 2026-08-21 (`Winner` → `P1 Winner`, `Hit Ad` → `P2 Hit Ad`); `Pause reason` gained `Campaign End`, `Graduate (Winning)`, `Fatigue`, `Budget Capped`.
- **Dedupe markers**: Ready-to-Test pings leave an `rt-ping-sent` Notion comment; pause-reason nags leave `pause-ping-sent`; relaunches leave `relaunch-detected`. Iteration ideas dedupe on `Ad id`/`Ref`.
- **Per-run caps** so a run finishes: 20 new roadmap rows, 40 archives, 5 iteration briefs, at most two Slack messages from the nightly sync.
- Routines only write to Notion and Slack. Nothing ever writes to Meta or BigQuery (also enforced by `.claude/settings.json`).
- Slack reports go to #tw-creative (`C0ASFA5F1B3`); silent when nothing changed. Paid marketer: Kevin Mo (`U0A1E7WENQ6`).

## Where to intervene

- **Prioritize ideas**: set Ideas Status = In progress (that's the promotion trigger). `Pending` does nothing.
- **Before launch**: give the roadmap row its display `Name` and the exact Meta `Ad Name`; the nightly sync binds the ad ID by `Ad Name` when it goes live.
- **Fill Pause reason + Learnings** when pinged — Learnings feed the weekly iteration briefs (as of 2026-09-08 no row has Learnings yet).
- **Pause a routine**: `update_trigger` with `enabled: false`, or the claude.ai Routines UI.

## Known limitations

- Brand/awareness campaigns (Reach/Thruplay/Traffic) have no meaningful SP or CPFT; their rows stay "Testing" with empty CPFT / LTV/CAC (suppressed in `ltv_cac.sql`).
- Ads renamed in Meta after launch still match by ad ID, but `Ad Name` will drift until someone updates it.
- HK rows never reach P2 Hit Ad / P2 Loser until an HK CPFT threshold exists.
- The persistent-session routines (set A) need a human to approve permission prompts when the auto-mode classifier flags a Notion write; the fresh-session routines (set B) may hit the same classifier — the DRY RUN procedure above is how to find out.
