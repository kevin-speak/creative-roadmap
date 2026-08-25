# TW Meta Ad Fatigue Report — 2026-08-25

**Account:** Speak ZH (1148917790153640) · **Campaigns:** `winning` / `winning2` / `winning3`
**Meta ad-level metrics:** last_7d (Aug 18–24) / yesterday (2026-08-24)
**Funnel economics:** anchored to funnel table MAX(date) = **2026-08-23** (~2-day lag) · current 7d = Aug 17–23 · prior 7d = Aug 10–16 · trailing 3d = Aug 21–23
**LTV per converted user:** $105.36 (Taiwan · app_store · cohort 2026-08 · month_index 35)

Of the ads with yesterday spend across `winning` / `winning2` / `winning3` (7 of ~215 ads; `winning3` had zero yesterday spend), **1 tripped a fatigue trigger** and its funnel economics confirm it as a pause candidate.

---

## 🚨 Pause Candidates (1)

| Campaign | Ad Set | Ad | 7d Spend | ΔCTI | ΔIPM | 7d Freq | 7d LTV:CAC | LTV:CAC WoW Δ | CPFT (7d) | Verdict |
|---|---|---|---:|---:|---:|---:|---:|---:|---:|---|
| winning2 | volume_scaling | dachien · police-conversation | $5,454.59 | +9.6% | **−19.8%** | 1.27 | **0.96** (sufficient, n=59) | −8.8% (1.05 → 0.96) | $83.43 | 🚨 **Pause candidate** — IPM decay trigger confirmed by sub-1.0 LTV:CAC and negative WoW trend |

👀 **Watch (non-pause):** none — the only ad that tripped a trigger this cycle already escalated straight to pause-candidate.

## ✅ Healthy (>$50 7d spend, no trigger tripped)

| Campaign | Ad Set | Ad | 7d Spend | ΔCTI | ΔIPM | 7d Freq | 7d LTV:CAC | LTV:CAC WoW Δ | CPFT (7d) |
|---|---|---|---:|---:|---:|---:|---:|---:|---:|
| winning | AEM_Product | na · ThreadsPost-Career-AITutor | $2,716.76 | +97.3% | +92.7% | 1.63 | 0.99 (moderate, n=17) | +40% (0.71 → 0.99, prior n=4) | $152.89 |
| winning2 | volume_scaling | Qing · 2026NYR-v2-PutOffForYears (scaling) | $4,150.44 | +23.8% | +23.3% | 1.50 | 0.51 (moderate, n=23) | insufficient history | $158.65 |
| winning2 | volume_scaling | illyandlean · outro-promo-long | $2,424.24 | +169.2% | +138.1% | 1.55 | 0.40 (low, n=11) | insufficient history | $200.49 |
| winning | AEM_Winning | morning.jason · og-video (app-cpr) | $1,913.46 | +149.3% | +134.1% | 1.36 | 1.13 (low, n=14) | insufficient history | $133.39 |
| winning2 | volume_scaling | Sophia · OutputInputAndSpeakMethod-v2-cut | $1,787.75 | +84.0% | +157.7% | 1.43 | 0.39 (low, n=8) | insufficient history | $202.80 |
| winning | AEM_Winning | Qing · 2026NYR-v2-PutOffForYears (cpr) | $1,300.09 | +19.8% | +21.6% | 1.30 | 0.75 (low, n=6) | insufficient history | $195.63 |

> **Notes:** CPFT shown for reference against the $55 TW target only — it moves in lockstep with LTV:CAC by construction (same underlying conversion math), not an independent signal. 5 of the 7 ads launched 2026-08-20, so the prior-7d funnel window doesn't exist yet ("insufficient history"), and their current-7d trial-start volume is under the 30-start reliability floor — treat those LTV:CAC reads as directional, not conclusive.

---

## Summary

- **1 ad on the watch list, 1 pause candidate** → `dachien · police-conversation` (winning2 / volume_scaling) — IPM decay (−19.8% yesterday vs 7d avg) confirmed by sub-1.0 LTV:CAC (0.96, sufficient volume n=59) and negative WoW trend (1.05 → 0.96). Its trailing-3d CPFT ($78.82) is actually improving vs the 7d avg ($83.43), so the decay is on the Meta delivery side, not the funnel side.
- **Top performer by LTV:CAC:** `morning.jason · og-video` at 1.13 (directional only, low volume, n=14); best *reliable* read is `na · ThreadsPost-Career-AITutor` at 0.99 (moderate, n=17).
- **No frequency alerts** — the 7 actively-spending ads range 1.27–1.63, well under the 2.5 cap.
- **6 other spending ads are healthy** (no trigger tripped).

---

## Appendix — raw inputs

### Meta ad-level (yesterday 2026-08-24 vs last_7d Aug 18–24)

| Ad | Ad ID | Yest Spend | Yest Clicks | Yest Installs | Yest CTI | Yest IPM | 7d Spend | 7d Clicks | 7d Installs | 7d CTI | 7d IPM | 7d Freq |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| Qing · 2026NYR-v2-PutOffForYears (cpr) | 120249917976060167 | $311.09 | 736 | 15 | 2.04% | 0.218 | $1,300.09 | 3,762 | 64 | 1.70% | 0.179 | 1.30 |
| na · ThreadsPost-Career-AITutor | 120246913787420167 | $394.17 | 1,441 | 18 | 1.25% | 0.211 | $2,716.76 | 12,481 | 79 | 0.63% | 0.109 | 1.63 |
| dachien · police-conversation | 120249784194200167 | $927.36 | 2,084 | 47 | 2.26% | 0.273 | $5,454.59 | 14,475 | 298 | 2.06% | 0.340 | 1.27 |
| Qing · 2026NYR-v2-PutOffForYears (scaling) | 120249918254160167 | $1,511.26 | 3,101 | 52 | 1.68% | 0.140 | $4,150.44 | 9,966 | 135 | 1.35% | 0.113 | 1.50 |
| Sophia · OutputInputAndSpeakMethod-v2-cut | 120249918145530167 | $331.83 | 1,243 | 17 | 1.37% | 0.263 | $1,787.75 | 6,324 | 47 | 0.74% | 0.102 | 1.43 |
| illyandlean · outro-promo-long | 120249918291540167 | $379.20 | 881 | 11 | 1.25% | 0.115 | $2,424.24 | 7,976 | 37 | 0.46% | 0.048 | 1.55 |
| morning.jason · og-video (app-cpr) | 120249918296230167 | $281.30 | 592 | 24 | 4.05% | 0.502 | $1,913.46 | 5,843 | 95 | 1.63% | 0.214 | 1.36 |

### Funnel economics (Hex/BigQuery, AS_OF 2026-08-23)

| Ad | Cur-7d Spend | Cur-7d Trials | Est Conv | CAC | LTV:CAC | CPFT (7d) | Prior-7d LTV:CAC | 3d CPFT vs 7d avg |
|---|---:|---:|---:|---:|---:|---:|---:|---|
| dachien · police-conversation | $4,922.35 | 59 | 44.75 | $110.01 | 0.96 | $83.43 | 1.05 (n=84) | $78.82 — improving |
| na · ThreadsPost-Career-AITutor | $2,599.08 | 17 | 24.46 | $106.26 | 0.99 | $152.89 | 0.71 (n=4) | $159.56 — worsening |
| Qing · 2026NYR (scaling) | $3,648.89 | 23 | 17.53 | $208.13 | 0.51 | $158.65 | — | $151.36 — improving |
| illyandlean · outro-promo-long | $2,205.40 | 11 | 8.40 | $262.69 | 0.40 | $200.49 | — | $181.56 — improving |
| morning.jason · og-video (app-cpr) | $1,867.43 | 14 | 20.09 | $92.95 | 1.13 | $133.39 | — | $127.99 — improving |
| Sophia · OutputInputAndSpeakMethod-v2-cut | $1,622.41 | 8 | 6.07 | $267.12 | 0.39 | $202.80 | — | $149.91 — improving |
| Qing · 2026NYR (cpr) | $1,173.77 | 6 | 8.36 | $140.47 | 0.75 | $195.63 | — | $172.88 — improving |

### Methodology

- **Fatigue triggers** (any one → watch item): CTI drop > 15% (yesterday vs 7d avg; CTI = installs ÷ clicks), IPM drop > 15% (yesterday vs 7d avg; IPM = installs ÷ impressions × 1000), 7d frequency > 2.5.
- **Pause gate** (watch item → pause candidate): 7d LTV:CAC < 1.0, or meaningfully negative WoW LTV:CAC decay with sufficient volume.
- **est_conversions** = adj_initial_purchases + adj_trial_starts × campaign trial-convert rate (Meta Ads TW, matured cohorts, attribution_date ≤ AS_OF − 4d).
- **LTV:CAC** = LTV-per-user ÷ CAC, where CAC = spend ÷ est_conversions. LTV-per-user is blended TW iOS (app_store) cohort LTV at month_index 35 — a conversion-efficiency ranking, not a creative-specific monetization signal.
- **Reliability floors:** sufficient ≥ 30 trial starts · moderate 15–30 · low/directional < 15 · new ads (< 7 days running) report "insufficient history" for WoW.
- **CPFT** = spend ÷ trial_starts, reference only vs the $55 TW target (algebraically redundant with LTV:CAC).

*Packed from the Daily Ad Fatigue Report posted to #marketing-alert-tw on 2026-08-25 10:11 KST; table data rebuilt from Meta Ads + BigQuery using the routine's methodology (values reconcile with the posted summary).*
