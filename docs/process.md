# The creative process

How a TW/HK creative moves from an idea to an archived learning, who moves it, and what the automation does at each step.

## Lifecycle

| # | Stage | Who | What happens | Roadmap status |
|---|---|---|---|---|
| 1 | Idea | Anyone | Post in #tw-creative, with a screenshot or screen recording when sharing a link. The Wednesday intake files it in the Ideas board. On the morning of each bi-weekly roadmap meeting (Thursday 16:00) the brief writes a preview on every new idea — a description of the image or video, Motion's analysis for a winning ad, a suggested priority — and posts the pre-read. | — |
| 2 | Prioritise | Lead | Set the idea's `Status` to **In progress**. | — |
| 3 | Plan | Daily sync | Creates one roadmap row per idea (`Reference` = the idea). | Plan |
| 4 | Produce | Designer / creator owner | Fill the naming fields as they become known, attach files, move the status. | Production |
| 5 | Hand off | Designer / creator owner | Set **Ready-to-Test**. The daily sync builds the ad name and file name from the naming fields and posts them in #tw-creative, or says which fields are missing. | Ready-to-Test |
| 6 | Launch | Paid marketer | Upload to Meta using that exact ad name. | Ready-to-Test |
| 7 | Bind | Daily sync (22:00) | Matches the live ad to the row by name, writes the ad ID, stamps the launch date, marks the idea Done. | On Air |
| 8 | Track | Daily sync (22:00) | SP score, SP status, CPFT, LTV/CAC, spend. Hit ads go to #hit-ads-library. | On Air |
| 9 | Pause | Paid marketer (in Meta) | The sync notices, stamps the paused date and fills the reason when a rule fits. | Pause |
| 10 | Close | Daily sync | 14 days after pausing, with a reason, the row is archived. | Archive |
| 11 | Iterate | Weekly review (Mon) | Proven ads get an iteration brief as a new idea, linked back through `Parent creative`. | — |

Influencer licences skip steps 1–4: a 請求支援 / 廣告上傳 post in #tw-ads becomes a licence row plus a Ready-to-Test roadmap row.

## What people fill in

- **Naming fields** (Market, Production Date, Campaign Type, Format, Production Type, Version, Creator Name, Description, Language Pair) — before Ready-to-Test. See [naming-convention.md](naming-convention.md).
- **Category, Owner, Hook, Element, Product Feature** — whenever known.
- **Pause reason** — within 7 days of a pause, when no rule filled it.

Everything else on the row (`Ad ID(s)`, SP fields, CPFT, LTV/CAC, Spend to date, Launch date, Paused date, Last synced) belongs to the sync. Automation never overwrites a field a person has filled.

## Pause reasons

The sync fills the first rule that fits when an ad stops:

| Reason | Rule |
|---|---|
| License Expired | linked licence has 0 days left |
| Budget Capped | testing campaign, $140–300 lifetime, under 10 installs or no SP score |
| SP Threshold | SP score under 1.5 |
| Graduate (Winning) | the same creative went live in a scaling / winning / CPR campaign in the last 14 days |
| Fatigue | scaling campaign and 7-day CPFT more than 30% worse than lifetime on 5+ trials |
| Campaign End | five or more rows paused at once and the whole campaign is off |

When no rule fits the reason stays empty. The Monday log lists open reasons with their owners. A reason still empty 7 days after the pause is set to **Other** and the row archives on schedule. There are no nightly pings.

## SP score

Replicated from the Hex "[TW] Meta Ads SP Dashboard" by [`sql/sp_score.sql`](../sql/sp_score.sql): SP = Σ over placements of spend share × (CTR ÷ benchmark CTR + CTI ÷ benchmark CTI), with leave-one-out benchmarks per placement × country × OS. Taiwan and Hong Kong are scored separately. The source table lags about two days.

| SP status | Rule |
|---|---|
| P2 Hit Ad | Taiwan, SP ≥ 2.0, 10+ trial starts, CPFT ≤ $58 |
| P2 Loser | Taiwan, SP ≥ 2.0, 10+ trial starts, CPFT > $58 |
| P1 Winner | SP ≥ 2.0 (Taiwan under 10 trials; every HK winner — HK has no CPFT threshold yet) |
| Mid-tier | 1.5 ≤ SP < 2.0 |
| Pause | SP < 1.5 |
| Testing | no score yet |

CPFT, LTV/CAC (cohort LTV month 35), market and the trailing 7-day window come from [`sql/ltv_cac.sql`](../sql/ltv_cac.sql). Brand and awareness campaigns have no meaningful SP or CPFT and stay at Testing.

## Scheduled runs

| Run | Taipei time | Runbook |
|---|---|---|
| Ideas intake (Slack → Ideas board) | Wed 17:00 | [`routines/ideas_intake.md`](../routines/ideas_intake.md) |
| Ideas brief (previews + pre-read for the bi-weekly roadmap meeting) | every second Thu 09:45, from 2026-11-26 | [`routines/ideas_brief.md`](../routines/ideas_brief.md) |
| Daily sync — intake | 07:00, 15:00 | [`routines/daily_sync.md`](../routines/daily_sync.md), Part A |
| Daily sync — full | 22:00 | same runbook, Parts B then A |
| Weekly review | Mon 10:30 | [`routines/weekly_review.md`](../routines/weekly_review.md) |

Each run posts at most one message to #tw-creative (the weekly review posts two) and stays silent when nothing changed.
