# Daily Ad Fatigue Report — Speak ZH (TW iOS) — 2026-11-17

Meta windows: yesterday = 2026-11-16, 7d = 2026-11-10 → 2026-11-16.
Funnel (Hex, anchored to MAX(date)): as-of 2026-11-16; current 11-10 → 11-16; prior 11-03 → 11-09; attribution cutoff 11-12; cohort month 2026-11.
Blended TW iOS Nov LTV/user: $80.88. Campaign trial-convert rate (winning): 37.1%. adj_initial_purchases = 0 for all ads.
5 ads had yesterday spend; all are in campaign `winning`. No spend in winning2 / winning3.

## ⚠️ Watch List

| Campaign | Ad Set | Ad | 7d Spend | ΔCTI | ΔIPM | 7d Freq | 7d LTV:CAC | LTV:CAC WoW Δ | CPFT (7d) | Verdict |
|---|---|---|---|---|---|---|---|---|---|---|
| winning | AEM_Winning | shasha77 · og-reels-no-embarrassment | $657 | −40% (2.03% → 1.23%) | −53% (0.449 → 0.212) | 1.26 | 0.84 (low vol, 8 FT) | −20% (prior 1.05, 40 FT) | $66 · 3d $128 worsening | 🔴 Pause candidate — CTI and IPM both tripped; 7d LTV:CAC < 1.0 |
| winning | AEM_Product | Qing · winner | $115 | −100% (1.50% → 0%) | −100% (0.362 → 0) | 1.31 | 0.59 (low vol, 1 FT) | −48% (prior 1.13, 7 FT) | $97 · 3d no signal (0 FT) | 🔴 Pause candidate — 0 installs yesterday on 116 clicks; 7d LTV:CAC < 1.0 |

## ✅ Healthy (>$50 7d spend, no triggers)

| Campaign | Ad Set | Ad | 7d Spend | ΔCTI | ΔIPM | 7d Freq | 7d LTV:CAC | LTV:CAC WoW Δ | CPFT (7d) |
|---|---|---|---|---|---|---|---|---|---|
| winning | AEM_Winning | AI-gen · TedStyle-man | $1,040 | +315% (2.51% → 10.42%) | +45% (0.365 → 0.530) | 1.36 | 0.97 (moderate, 19 FT) | insufficient history (first spend 11-10) | $58 · 3d $44 improving |
| winning | AEM_Winning | MIP-mittynomad · cost-efficiency | $189 | +65% | +14% | 1.18 | 0.43 (low vol, 1 FT) | −64% (prior 1.21, 35 FT) | $129 · 3d $38 improving (1 FT) |
| winning | AEM_Winning | Jay · RecruiterEngInterview-v1-3Tips | $71 | +90% | +379% | 1.20 | no signal (0 FT) | n/a (prior 0.95, 6 FT) | no signal |

Notes
- Funnel 7d spend on shasha77 ($527 vs $2,316 prior) and mittynomad ($129 vs $1,766 prior) fell 75–90% WoW; WoW LTV:CAC decay on both is low-volume and directional only.
- mittynomad has no fatigue trigger but 7d economics are weak (LTV:CAC 0.43 on 1 trial start); keep an eye on it.
- CPFT is reference only against the $55 TW target; it moves in lockstep with LTV:CAC.

**Summary:** Watch list 2 · Pause candidates 2 (shasha77 · og-reels-no-embarrassment, Qing · winner) · Top performer by LTV:CAC: AI-gen · TedStyle-man (0.97, moderate volume) · Frequency alerts: none (max 1.36).

Data sources: Meta Ads MCP (ad-level last_7d + yesterday, mobile_app_install), Hex thread https://app.hex.tech/019c0c49-ab2d-7003-aa7a-3b9870aa8d91/thread/01a1e70e-5740-771c-aea1-661d2fdb2a0c
