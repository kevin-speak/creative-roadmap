# TW Creative Review — Sep 2026: 26Q3 LateBird (web) + ongoing app

Data: BigQuery `meta_ads_creative_report_funnel` through 2026-09-29 (lags ~2 days). SP and P1/P2 come from [`automation/sp_score.sql`](../automation/sp_score.sql). LTV/CAC uses the [`automation/ltv_cac.sql`](../automation/ltv_cac.sql) method over a Sep 1–29 window. Creative and engagement metrics come from Motion (workspace Speak_ZH), and age/gender comes from Meta. Scope: **Taiwan only** (`tw_meta_*` campaigns, Taiwan delivery). Ads with less than $50 of spend are excluded.

**Rules:** an ad passes P1 at SP ≥ 2.0. P2 needs SP ≥ 2.0, at least 10 trials and a CPFT of $58 or less.

## 1. LTV/CAC

| Line | Spend | Trials | Meta purchases | CPFT | LTV/CAC |
|---|---|---|---|---|---|
| **LateBird total (purchase)** | **$54,993** | 507 | 720 | $108 | **0.63** |
| · `26q3_latebird` (ASC prospecting) | $40,735 | 322 | 416 | $127 | 0.53 |
| · `26q3_latebird_rtg` | $14,258 | 185 | 304 | $77 | 0.91 |
| · `latebird_reach` (awareness) | $2,500 | 3 | 0 | — | n/a |
| **TW app total** | **$97,836** | 1,233 | 62 | $79 | **0.94** |
| · `trial_ongoing_winning` | $18,689 | 287 | 15 | $65 | 1.19 |
| · `trial_ongoing_scaling2` | $61,909 | 824 | 39 | $75 | 0.89 |
| · `purchase_ongoing_no-disc_testing` | $17,238 | 122 | 8 | $141 | 0.83 |

- LateBird prospecting (0.53) is the weakest paid line. Retargeting (0.91) is close to break-even with the app.
- Rough benchmark: the August 26Q3 main promo (ASC + RTG) scores about 0.47 using the same method with the blended TW convert rate. LateBird beat the main promo.

## 2. SP and P1 status — LateBird (48 purchase-campaign ads)

**P2 winners (5).** These are the same five ads that rank highest by LTV/CAC.

| Ad | Adset | SP | Trials | CPFT | LTV/CAC |
|---|---|---|---|---|---|
| Countdown-Day1 static 1200x628 | RTG | 9.12 | 10 | $10 | (under $300 spend) |
| Countdown-Day3 static 1080x1080 | RTG | 7.01 | 17 | $49 | 1.31 |
| CrazyHands motion 10s | RTG | 4.74 | 41 | $32 | 1.78 |
| Countdown-Day1 static 1200x628 | ASC | 3.88 | 40 | $38 | 1.59 |
| Shasha77 × Andrew interview "business-english-shift" | ASC | 3.63 | 10 | $40 | 1.59 |

**P2 losers (10).** These passed SP but CPFT is above $58: 88off RTG ($68, LTV/CAC 1.08), 12poff RTG ($71, 1.08), coupon-$699 ($81), Countdown-Day3 ASC ($96), 2026timecurve motion RTG ($141), coupon-yearly5291 ($159), AI-Miso shadowing UGC ($195), EaglishFamily reels ($198), Audrey workplace UGC ($230), 12poff initial-checkout ($278).

**P1, still under 10 trials (12).** Threadspost (RTG 2.77, ASC 2.27), 88off motion ×3 (4.71 / 2.76 / 2.55), Chuchushoe speak-ai-tutor 3.66, Shasha77 open-ai-funding 3.00, Qing solo-travel 2.72, 2026timecurve static RTG 2.43, CrazyHands ASC 2.38, compareboba motion 2.08, 12poff static ASC 2.06.

**Mid-tier (3).** purchasepage 1.85, timecurve-100days 1.86, 88off static ASC 1.88.

**No SP (18).** These never reached 10 checkouts: the blog statics, comparecoffee/compareboba statics, most Chuchushoe cuts and the Sophia UGC.

## 3. Win rates

| | Launched | Scored | P1 pass | P1 rate | Reached P2 gate | P2 win | P2 rate |
|---|---|---|---|---|---|---|---|
| LateBird web | 48 | 30 | 27 | **56%** (90% of scored) | 15 | 5 | **10%** (33% of gated) |
| TW app, new in Sep | 36 | 20 | 12 | **33%** (60% of scored) | 5 | 0 | **0%** |

- The TW app ads that reached the P2 gate but failed CPFT are Jenny interview v1 ($109), Eaglish app-scaling relaunch ($65), Jenny v2 ($119), Qing solo-travel ($77, LTV/CAC 1.48) and Christine english-environment ($111).
- Two app ads are close to P2 at 8 trials each: Shasha77 *no-embarrassment* (SP 4.07, CPFT $18) and *spaced-repetition* (SP 2.57, CPFT $55).
- The only P2 Hit Ad among incumbent app ads is Eaglish.fam OG video (`…_winning`). It has a lifetime CPFT of $57.99, a Sep CPFT of $48 and LTV/CAC 1.54.

## 4. P2 deep-dive (Motion + Meta)

**Audience.** This comes from Meta's per-ad age/gender split of spend, which shows who Meta delivered to, not who converted. The winners reached 25–44 year-olds (63–73% of spend) and skewed female (57–63%). The Countdown-Day3 RTG ad leaned older, with 27% of spend at 45–54. Three of the five winners ran in retargeting, so these are warm, deal-ready visitors.

| Ad | Why it won | Hook | CTR | Video | Click→checkout |
|---|---|---|---|---|---|
| Countdown-Day1 (RTG + ASC; the same asset won in both) | A mascot checking its watch with "2026 最後機會 / 最後 1 天" and "現折 $699". It uses pure urgency and says nothing about the product, so it closes people who were already interested | "2026 最後機會" | 0.95% RTG / 0.45% ASC | static | **35.6%** RTG / 6.5% ASC; Meta CPA $7 / $31 |
| Countdown-Day3 RTG | Same template, "只剩最後 3 天". Copy pre-empts objections: "我很忙 / 怕講錯 / 有沒有用" | "2026 最後機會" | 0.76% | static | 13.5%, CPA $33 |
| CrazyHands motion RTG | A 10-second screen recording of the pricing page, with animated hands pointing at the plan, the discount and the countdown. It shows exactly what you get and the price, which suits warm traffic | pointer on the price | 0.72% | thumbstop 13%, sustain 24%, average watch 2s, 100% view 3.7% | 12.8%, ROAS 2.04 (best in LateBird) |
| Shasha77 × Andrew Hsu interview "business-english-shift" | Uses the Speak founder as an authority and frames English as career capital ("員工英文不夠好…拖累整體表現"). It ends on "優惠倒數四天" | "如果員工英文不夠好、進步不夠快…" | 1.04% (outbound 0.67%) | thumbstop 16%, sustain 30%, Motion hold 74 | 7.3%, CPA $31 |

**Pattern.** For a promo, price and urgency statics are the best at converting to checkout, even though their CTR is below the LateBird average of 0.67%. UGC stories get the most clicks (1.1–1.9% CTR for AI-Miso, Audrey and Qing), but they posted CPFTs of $133–230 and LTV/CAC of 0.3–0.5. They create attention without purchase intent.

## 5. Iterate / amplify

1. **Turn the countdown set into a standard kit for every promo.** Launch D-7, D-3, D-1 and "last hours" versions on day 1 into RTG, with ASC as a second step. Test a 1080x1920 story size (both winners were feed sizes) and a monthly-price headline ("平均每月 $258") against "現折 $699".
2. **Keep CrazyHands in retargeting and iterate the first second.** It is a warm-audience asset: in prospecting it scored SP 2.38 with 5 trials. Put the discount number on screen in frame 1 to lift the 13% thumbstop. Make versions that point at the annual plan plus the 7-day trial, and one for the Premium Plus tier.
3. **Scale the Shasha77 × Andrew interview series.** It is the one concept winning on both web and app (see below). Move *no-embarrassment* and *spaced-repetition* into `scaling2` once they reach 10 trials. Cut web/promo versions of *no-embarrassment* with a countdown end-card. Recut *fear-to-speak* (CTR 1.55% but CPFT $173) so it opens on the career line.
4. **Take long UGC out of promo purchase campaigns.** Keep AI-Miso, Audrey and Qing for app trial campaigns, and test them there under ongoing no-disc pricing.
5. **Rebalance prospecting against retargeting.** Prospecting (0.53) is the drag on LateBird, and RTG was 26% of purchase spend. For the next promo, raise the RTG share or add countdown statics to ASC from day 1: the ASC Countdown-Day1 ad was the only prospecting P2.

## Winners on both web and app

| Concept | Web (LateBird) | App (Sep) | Verdict |
|---|---|---|---|
| **Shasha77 × Andrew Hsu interview** | *business-english-shift* **P2** (SP 3.63, $40, LTV/CAC 1.59); *open-ai-funding* P1 3.00 | *no-embarrassment* SP 4.07 / $18; *replace-human-tutor* SP 3.91; *spaced-repetition* SP 2.57 / $55 (all P1, close to P2) | **Winning on both. Top priority to amplify.** |
| **Qing solo-travel rescue v2** | P1 (SP 2.72, 6 trials) | testing SP 2.80, 20 trials, $77, LTV/CAC 1.48; scaling SP 3.34 | Passes P1 on both; CPFT is the gap |
| **Eaglish family** | reels SP 2.66, but $198 CPFT and LTV/CAC 0.31 | OG video **P2 Hit Ad** ($48 Sep CPFT, LTV/CAC 1.54) | App-only winner; does not carry to web |

## Caveats

- LTV/CAC uses one LTV per user for the TW cohort ($129.8). It does not discount for the lower LTV of discounted annual plans.
- Meta "purchases" differ from the funnel table's adjusted purchases (about 10% of raw on both LateBird and the main 26Q3 promo).
- LateBird was live Sep 13–29. Several P1 ads stopped before reaching 10 trials.
