# TW Creative Review — Sep 2026: 26Q3 LateBird (web) + ongoing app

Data: BigQuery `meta_ads_creative_report_funnel` through 2026-09-29 (lags ~2 days). SP and P1/P2 come from [`automation/sp_score.sql`](../automation/sp_score.sql). LTV/CAC follows the **Mode Paid Optimization Dash** method: attributed LTV from `marketing_attribution_aggregate_attribution_date_cohort` (attributed trial converts + initial purchases × 35-month cohort LTV per user by platform and language pair) divided by spend from `marketing_spend_daily`, by attribution date, Sep 1–29. Creative and engagement metrics come from Motion (workspace Speak_ZH), and age/gender comes from Meta. Scope: **Taiwan only** (`tw_meta_*` campaigns, Taiwan delivery). Ads with less than $50 of spend are excluded.

**Rules:** an ad passes P1 at SP ≥ 2.0. P2 needs SP ≥ 2.0, at least 10 trials and a CPFT of $58 or less.

## 1. LTV/CAC

| Line | Spend | Attributed converters | LTV | LTV per converter | LTV/CAC |
|---|---|---|---|---|---|
| **LateBird total (purchase)** | **$54,993** | 234 | $44,117 | $188 | **0.80** |
| · `26q3_latebird` (ASC prospecting) | $40,735 | 156 | $29,432 | $188 | 0.72 |
| · `26q3_latebird_rtg` | $14,258 | 78 | $14,685 | $188 | **1.03** |
| · `latebird_reach` (awareness) | $2,500 | 0 | $0 | — | n/a |
| **TW app total** | **$98,099** | 607 | $63,375 | $104.5 | **0.65** |
| · `trial_ongoing_winning` | $18,952 | 141 | $14,755 | $104.5 | 0.78 |
| · `trial_ongoing_scaling2` | $61,909 | 365 | $38,102 | $104.5 | 0.62 |
| · `purchase_ongoing_no-disc_testing` | $17,238 | 101 | $10,518 | $104.5 | 0.61 |

- **LateBird beat the ongoing app in September (0.80 vs 0.65).** Retargeting paid back above 1.0. Prospecting (0.72) was lower but still ahead of every app campaign.
- A web converter is worth $188 against $104.5 on iOS (annual-plan mix), so the web promo can carry a much higher CPFT than the app and still return more.
- TW app at 0.65 is the bigger problem. The two largest app spenders are weak at ad level (see section 5).

## 2. SP and P1 status — LateBird (48 purchase-campaign ads)

**P2 winners (5).** Per-ad LTV/CAC is not available for web ads: web conversions are attributed at campaign level only (ad name reads "No Ad Name"), in the Paid Opt Dash as well. Meta-reported CPA is shown instead.

| Ad | Adset | SP | Trials | CPFT | Meta CPA |
|---|---|---|---|---|---|
| Countdown-Day1 static 1200x628 | RTG | 9.12 | 10 | $10 | $7 |
| Countdown-Day3 static 1080x1080 | RTG | 7.01 | 17 | $49 | $33 |
| CrazyHands motion 10s | RTG | 4.74 | 41 | $32 | $21 |
| Countdown-Day1 static 1200x628 | ASC | 3.88 | 40 | $38 | $31 |
| Shasha77 × Andrew interview "business-english-shift" | ASC | 3.63 | 10 | $40 | $31 |

**P2 losers (10).** These passed SP but CPFT is above $58: 88off RTG ($68), 12poff RTG ($71), coupon-$699 ($81), Countdown-Day3 ASC ($96), 2026timecurve motion RTG ($141), coupon-yearly5291 ($159), AI-Miso shadowing UGC ($195), EaglishFamily reels ($198), Audrey workplace UGC ($230), 12poff initial-checkout ($278).

**P1, still under 10 trials (12).** Threadspost (RTG 2.77, ASC 2.27), 88off motion ×3 (4.71 / 2.76 / 2.55), Chuchushoe speak-ai-tutor 3.66, Shasha77 open-ai-funding 3.00, Qing solo-travel 2.72, 2026timecurve static RTG 2.43, CrazyHands ASC 2.38, compareboba motion 2.08, 12poff static ASC 2.06.

**Mid-tier (3).** purchasepage 1.85, timecurve-100days 1.86, 88off static ASC 1.88.

**No SP (18).** These never reached 10 checkouts: the blog statics, comparecoffee/compareboba statics, most Chuchushoe cuts and the Sophia UGC.

## 3. Win rates

| | Launched | Scored | P1 pass | P1 rate | Reached P2 gate | P2 win | P2 rate |
|---|---|---|---|---|---|---|---|
| LateBird web | 48 | 30 | 27 | **56%** (90% of scored) | 15 | 5 | **10%** (33% of gated) |
| TW app, new in Sep | 36 | 20 | 12 | **33%** (60% of scored) | 5 | 0 | **0%** |

- The TW app ads that reached the P2 gate but failed CPFT are Jenny interview v1 ($109), Eaglish app-scaling relaunch ($65), Jenny v2 ($119), Qing solo-travel ($77, LTV/CAC 0.57) and Christine english-environment ($111).
- Two app ads are close to P2 at 8 trials each: Shasha77 *no-embarrassment* (SP 4.07, CPFT $18) and *spaced-repetition* (SP 2.57, CPFT $55).
- The only P2 Hit Ad among incumbent app ads is Eaglish.fam OG video (`…_winning`). It has a lifetime CPFT of $57.99, a Sep CPFT of $48 and Sep LTV/CAC 0.92, the best of the large app ads.

## 4. P2 deep-dive (Motion + Meta)

**Audience.** This comes from Meta's per-ad age/gender split of spend, which shows who Meta delivered to, not who converted. The winners reached 25–44 year-olds (63–73% of spend) and skewed female (57–63%). The Countdown-Day3 RTG ad leaned older, with 27% of spend at 45–54. Three of the five winners ran in retargeting, so these are warm, deal-ready visitors.

| Ad | Why it won | Hook | CTR | Video | Click→checkout | Preview |
|---|---|---|---|---|---|---|
| Countdown-Day1 (RTG + ASC; the same asset won in both) | A mascot checking its watch with "2026 最後機會 / 最後 1 天" and "現折 $699". It uses pure urgency and says nothing about the product, so it closes people who were already interested | "2026 最後機會" | 0.95% RTG / 0.45% ASC | static | **35.6%** RTG / 6.5% ASC; Meta CPA $7 / $31 | [RTG post](https://www.facebook.com/508370042351961_122338621154639347) · [ASC post](https://www.facebook.com/508370042351961_122338618544639347) · [AM RTG](https://www.facebook.com/adsmanager/manage/ads/edit?act=1148917790153640&selected_ad_ids=120250283811450167) · [AM ASC](https://www.facebook.com/adsmanager/manage/ads/edit?act=1148917790153640&selected_ad_ids=120250283696830167) |
| Countdown-Day3 RTG | Same template, "只剩最後 3 天". Copy pre-empts objections: "我很忙 / 怕講錯 / 有沒有用" | "2026 最後機會" | 0.76% | static | 13.5%, CPA $33 | [Post](https://www.facebook.com/508370042351961_122338620956639347) · [Ads Manager](https://www.facebook.com/adsmanager/manage/ads/edit?act=1148917790153640&selected_ad_ids=120250283810100167) |
| CrazyHands motion RTG | A 10-second screen recording of the pricing page, with animated hands pointing at the plan, the discount and the countdown. It shows exactly what you get and the price, which suits warm traffic | pointer on the price | 0.72% | thumbstop 13%, sustain 24%, average watch 2s, 100% view 3.7% | 12.8%, ROAS 2.04 (best in LateBird) | [Post](https://www.facebook.com/508370042351961_122342762624639347) · [Ads Manager](https://www.facebook.com/adsmanager/manage/ads/edit?act=1148917790153640&selected_ad_ids=120250445740910167) |
| Shasha77 × Andrew Hsu interview "business-english-shift" | Uses the Speak founder as an authority and frames English as career capital ("員工英文不夠好…拖累整體表現"). It ends on "優惠倒數四天" | "如果員工英文不夠好、進步不夠快…" | 1.04% (outbound 0.67%) | thumbstop 16%, sustain 30%, Motion hold 74 | 7.3%, CPA $31 | [Post](https://www.facebook.com/508370042351961_1414984677425151) · [Ads Manager](https://www.facebook.com/adsmanager/manage/ads/edit?act=1148917790153640&selected_ad_ids=120250424355630167) |

**Pattern.** For a promo, price and urgency statics are the best at converting to checkout, even though their CTR is below the LateBird average of 0.67%. UGC stories get the most clicks (1.1–1.9% CTR for AI-Miso, Audrey and Qing), but they posted CPFTs of $133–230 and Meta CPAs of $79–209. They create attention without purchase intent.

## 4b. P2 near-misses (passed SP, missed the $58 CPFT bar)

These are not losers. They cleared SP ≥ 2.0 with 10+ trials, beat most of the account, and missed only the CPFT bar.

**LateBird web (10)**

| Ad | Why it nearly made it | Hook | CTR | Video | Click→checkout | Preview |
|---|---|---|---|---|---|---|
| 88off static RTG (SP 3.70, CPFT $68) | Same mascot + "2026 最後機會" template as the winners, led by the discount number. Converts warm traffic, but "最高 88 折" is a weaker trigger than a countdown | "2026 最後優惠機會 / 最高 88 折" | 0.57% | static | 6.0%, CPA $47 | [Post](https://www.facebook.com/508370042351961_122338621136639347) · [Ads Manager](https://www.facebook.com/adsmanager/manage/ads/edit?act=1148917790153640&selected_ad_ids=120250283811430167) |
| 12% OFF static RTG (SP 3.51, $71) | Same template with "12% OFF". Best Meta ROAS of the near-misses (1.13) | "2026 最後優惠機會 12% OFF" | 0.60% | static | 5.9%, CPA $43 | [Post](https://www.facebook.com/508370042351961_122338621112639347) · [Ads Manager](https://www.facebook.com/adsmanager/manage/ads/edit?act=1148917790153640&selected_ad_ids=120250283810920167) |
| Coupon-$699 static ASC (SP 2.70, $81) | Original vs discounted price anchor, shown to cold prospecting traffic | "2026 最後機會!" | 0.42% | static | 2.7%, CPA $55 | [Post](https://www.facebook.com/508370042351961_122338618814639347) · [Ads Manager](https://www.facebook.com/adsmanager/manage/ads/edit?act=1148917790153640&selected_ad_ids=120250283695670167) |
| Countdown-Day3 static ASC (SP 3.16, $96) | **The same asset won in RTG ($49).** Urgency alone does not close a cold audience | "2026 最後機會" | 0.53% | static | 3.4%, CPA $59 | [Post](https://www.facebook.com/508370042351961_122338618562639347) · [Ads Manager](https://www.facebook.com/adsmanager/manage/ads/edit?act=1148917790153640&selected_ad_ids=120250283697110167) |
| 2026TimeCurve motion RTG (SP 5.42, $141) | Highest SP of the near-misses: a 15s progress-curve animation plus the offer stops the scroll, but the progress story delays the price | progress graph + "2026 最後機會" | 0.60% | thumbstop 16%, sustain 22%, avg watch 3s | 3.5%, CPA $84 | [Post](https://www.facebook.com/508370042351961_122338621550639347) · [Ads Manager](https://www.facebook.com/adsmanager/manage/ads/edit?act=1148917790153640&selected_ad_ids=120250283809070167) |
| Coupon-Yearly5291 static, Initial-Checkout adset (SP 3.04, $159) | Coupon graphic quoting "平均每月 $441" — a worse monthly number than the "$258" used elsewhere. Skewed older (45+ = 45% of spend) | "Speak 快閃優惠 2026 最後機會!" | 0.69% | static | 2.4%, CPA $121 | [Post](https://www.facebook.com/508370042351961_122339098964639347) · [Ads Manager](https://www.facebook.com/adsmanager/manage/ads/edit?act=1148917790153640&selected_ad_ids=120250308029240167) |
| AI-Miso shadowing UGC 67s ASC (SP 2.43, $195) | Relatable pain (shadowing didn't help in a cross-border meeting). Strong scroll-stop, but viewers leave long before the offer | "以為狂練 Shadowing 就夠了 直到跨國會議被問到..." | 1.10% | thumbstop 24%, sustain 16%, avg watch 4s of 67s | 1.2%, CPA $181 | [Post](https://www.facebook.com/508370042351961_122339109104639347) · [Ads Manager](https://www.facebook.com/adsmanager/manage/ads/edit?act=1148917790153640&selected_ad_ids=120250308300000167) |
| EaglishFamily reels 27s ASC (SP 2.66, $198) | Influencer contrasts Speak with translation apps, then tours foreigners around Taiwan. Entertaining, low purchase intent | "學好英文就交給Speak" | 0.93% | thumbstop 30%, sustain 18% | 1.7%, CPA $156 | [Post](https://www.facebook.com/508370042351961_122340493742639347) · [Ads Manager](https://www.facebook.com/adsmanager/manage/ads/edit?act=1148917790153640&selected_ad_ids=120250363675790167) |
| Audrey workplace-manners UGC 58s ASC (SP 3.41, $230) | Best attention asset in LateBird: an office skit about the 1-on-1 after an English meeting, then an app demo. The skit earns the click; the promo ask comes too late | "每次跟外國同事開完會 主管就馬上約我 1 on 1...?" | **1.86%** | thumbstop **34%**, sustain 21%, Motion hold 72 | 0.4%, CPA $209 | [Post](https://www.facebook.com/508370042351961_122339109080639347) · [Ads Manager](https://www.facebook.com/adsmanager/manage/ads/edit?act=1148917790153640&selected_ad_ids=120250308298740167) |
| 12% OFF static, Initial-Checkout adset (SP 2.16, $278) | Same asset as the RTG 12% OFF ($71), here in a cold Initial-Checkout ASC adset | "2026 最後優惠機會 12% OFF" | 0.53% | static | 1.8%, CPA $175 | [Post](https://www.facebook.com/508370042351961_122339098496639347) · [Ads Manager](https://www.facebook.com/adsmanager/manage/ads/edit?act=1148917790153640&selected_ad_ids=120250308029210167) |

**TW app (5)**

| Ad | Why it nearly made it | Hook | CTR | Video | Click→install / install→trial, CPI | LTV/CAC (Paid Opt) | Preview |
|---|---|---|---|---|---|---|---|
| Eaglish.fam OG relaunch, `scaling2` (SP 2.59, 52 trials, $65) | **Same asset as the P2 Hit Ad in `winning` ($48).** Only $7 over the bar; broader scaling audience raised CPFT | "最重要的就是要開始開口說英文。" | 1.57% | thumbstop 15%, sustain 25% | 2.2% / 23%, CPI $14.23 | 0.61x | [Post](https://www.facebook.com/111921510253023_2143686826359348) · [Ads Manager](https://www.facebook.com/adsmanager/manage/ads/edit?act=1148917790153640&selected_ad_ids=120250329291480167) |
| Qing solo-travel rescue v2, testing (SP 2.80, 20, $77) | First-person travel fear → app scenarios. Also P1 on web | "出國獨旅前 我做過最棒的準備就是…" | **3.24%** | thumbstop 25%, sustain 22% | 0.9% / 28%, CPI $18.72 | 0.57x | [Post](https://www.facebook.com/508370042351961_122339109602639347) · [Ads Manager](https://www.facebook.com/adsmanager/manage/ads/edit?act=1148917790153640&selected_ad_ids=120250308343730167) |
| Jenny salary-negotiation v1, `scaling2` (SP 2.44, 34, $109) | Real-scene, full-English interview opener; viewers drop fast in a 73s cut | "Negotiating salary in English" | 1.25% | thumbstop 20%, sustain 9% | 1.5% / 23%, CPI $24.66 | 0.36x | [Post](https://www.facebook.com/508370042351961_122334365672639347) · [Ads Manager](https://www.facebook.com/adsmanager/manage/ads/edit?act=1148917790153640&selected_ad_ids=120250115000200167) |
| Jenny salary-negotiation v2 cut, testing (SP 2.36, 19, $119) | Shorter cut opening on the recruiter's line; higher CTR, same drop-off | "在我們結束之前 你有期望的工資嗎" | 1.86% | thumbstop 22%, sustain 10% | 1.0% / 28%, CPI $26.32 | 0.45x | [Post](https://www.facebook.com/508370042351961_122334365666639347) · [Ads Manager](https://www.facebook.com/adsmanager/manage/ads/edit?act=1148917790153640&selected_ad_ids=120250114986240167) |
| Christine english-environment, whitelisted creator, testing (SP 3.06, 12, $111) | Creator voice ("most rewarding thing as a creator") with app screen recordings; best install→trial of the group | "You know what's one of the most rewarding things as a creator?" | **3.29%** | thumbstop **32%**, sustain 14% | 1.7% / **34%**, CPI $28.33 | 0.45x | [Post](https://www.facebook.com/252903364583837_1708088390282627) · [Ads Manager](https://www.facebook.com/adsmanager/manage/ads/edit?act=1148917790153640&selected_ad_ids=120250212023880167) |

**What to do with them**

- **Same creative, different audience.** Three of the near-misses are winners run in the wrong place: Countdown-Day3 ($49 RTG vs $96 ASC), 12% OFF ($71 RTG vs $278 Initial-Checkout) and Eaglish OG ($48 `winning` vs $65 `scaling2`). Judge an asset on its best audience and keep it there instead of retiring it.
- **Discount statics in RTG (88off, 12% OFF) are $10–13 over the bar** with Meta ROAS 0.8–1.1. Keep them as RTG rotation next to the countdown set.
- **The attention assets fail after the click.** Audrey, AI-Miso, EaglishFamily reels and TimeCurve have the best CTR and scroll-stop in LateBird but 0.4–3.5% click→checkout. Cut them under 30s, bring the price into the first 5 seconds, and add the countdown end-card. Audrey's skit hook is the strongest opener we have; reuse it.
- **App near-misses lose on CPI, not on interest.** Qing and Christine have 3.2–3.3% CTR but only 0.9–1.7% click→install. Test app-store-oriented cuts (show the app icon and "免費下載" early) and trim the Jenny cuts to ~30s to fix the 9–10% sustain.

## 5. Iterate / amplify

1. **Turn the countdown set into a standard kit for every promo.** Launch D-7, D-3, D-1 and "last hours" versions on day 1 into RTG, with ASC as a second step. Test a 1080x1920 story size (both winners were feed sizes) and a monthly-price headline ("平均每月 $258") against "現折 $699".
2. **Keep CrazyHands in retargeting and iterate the first second.** It is a warm-audience asset: in prospecting it scored SP 2.38 with 5 trials. Put the discount number on screen in frame 1 to lift the 13% thumbstop. Make versions that point at the annual plan plus the 7-day trial, and one for the Premium Plus tier.
3. **Scale the Shasha77 × Andrew interview series.** It is the one concept winning on both web and app (see below). Move *no-embarrassment* and *spaced-repetition* into `scaling2` once they reach 10 trials. Cut web/promo versions of *no-embarrassment* with a countdown end-card. Recut *fear-to-speak* (CTR 1.55% but CPFT $173) so it opens on the career line.
4. **Take long UGC out of promo purchase campaigns.** Keep AI-Miso, Audrey and Qing for app trial campaigns, and test them there under ongoing no-disc pricing.
5. **Rebalance prospecting against retargeting.** RTG returned 1.03 against 0.72 for prospecting, yet RTG was only 26% of purchase spend. For the next promo, raise the RTG share or add countdown statics to ASC from day 1: the ASC Countdown-Day1 ad was the only prospecting P2.
6. **Move app budget off the weakest big spenders.** In September the two largest app ads returned well under target: Harryspeaks OG ($19.3K, LTV/CAC 0.46) and Dodomen *speak-without-fear* ($13.6K, 0.56). The best app ads were Shasha77 *no-embarrassment* (1.96), *spaced-repetition* (1.06), Eaglish.fam OG (0.92) and Threadspost-career (0.84). Shift `scaling2` budget toward these.

## Winners on both web and app

| Concept | Web (LateBird) | App (Sep) | Verdict |
|---|---|---|---|
| **Shasha77 × Andrew Hsu interview** | *business-english-shift* **P2** (SP 3.63, CPFT $40); *open-ai-funding* P1 3.00 | *no-embarrassment* SP 4.07, CPFT $18, LTV/CAC 1.96; *spaced-repetition* SP 2.57, $55, LTV/CAC 1.06; *replace-human-tutor* SP 3.91 (all P1, close to P2) | **Winning on both. Top priority to amplify.** |
| **Qing solo-travel rescue v2** | P1 (SP 2.72, 6 trials) | testing SP 2.80, 20 trials, $77, LTV/CAC 0.57; scaling SP 3.34 | Passes P1 on both; CPFT is the gap |
| **Eaglish family** | reels SP 2.66, but $198 CPFT | OG video **P2 Hit Ad** ($48 Sep CPFT, LTV/CAC 0.92) | App-only winner; does not carry to web |

## Caveats

- LTV/CAC includes Sep 17–29, which the Paid Opt Dash hides by default as not yet final. Late-September trials have not converted yet, so app figures are floors.
- An AppsFlyer conversion-event outage (incident 2026-09-28) may undercount late-September app attribution until it is backfilled.
- Web per-ad LTV/CAC is not available (campaign-level attribution only). $1.8K of LateBird LTV sits under a truncated campaign name (`26q3latebird`) and is excluded; including it, LateBird is about 0.84.
- Meta "purchases" differ from the funnel table's adjusted purchases (about 10% of raw on both LateBird and the main 26Q3 promo).
- LateBird was live Sep 13–29. Several P1 ads stopped before reaching 10 trials.
