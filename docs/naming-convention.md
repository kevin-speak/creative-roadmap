# Naming convention

Source: [APAC Paid Marketing Naming Convention Builder](https://docs.google.com/spreadsheets/d/1E6WRPVDUh0fFNbWRoa9DxNiCHHQOQEU4KPzbXt9g3Bw/edit?gid=1579883954), tab **TW Name Builder**. Terms are defined in the Notion page "APAC Paid Creative Production – Shared Terms & Definitions". The code that implements this page is [`roadmap/naming.py`](../roadmap/naming.py); if the sheet changes, change the constants at the top of that file and this table together.

## The ten fields

| Code | Field | Values | Notion property |
|---|---|---|---|
| c1 | Country | `tw` · `hk` | `Market` |
| c2 | Production date | `YYMMDD` | `Production Date` |
| c3 | Campaign type | `promo` · `ongoing` | `Campaign Type` |
| c4 | Format | `video` · `image` · `carousel` | `Format` |
| c5 | Production type | `creator` · `licensed` · `inhouse` · `agency` · `freelancer` · `actor` | `Production Type` |
| c6 | Version | `original` · `recut` · `whitelist` · `na` | `Version` |
| c7 | Creator name | lowercase free text, `na` when there is none | `Creator Name` |
| c8 | Description | lowercase free text: elements, concept, variation | `Description` |
| c9 | Note | size, spec, stage, OS (`1080x1920`, `app-testing`) — may be empty | — (not stored) |
| c10 | Language pair | `tw-en` · `tw-jp` — may be empty | `Language Pair` |

No field may contain an underscore: `_` separates fields.

```
Meta ad name   c1:tw_c2:261116_c3:ongoing_c4:image_c5:creator_c6:original_c7:na_c8:krjp-launch-01-1920x1080_c9:_c10:
File name      c1!tw_c2!261116_c3!ongoing_c4!image_c5!creator_c6!original_c7!na_c8!krjp-launch-01-1920x1080_c9!_c10!
```

The file name is the ad name with `!` instead of `:`.

What the terms mean, in short: **creator** = made for our ads; **licensed** = existing creator content we got rights to; **original** = the creator's final delivery used as is; **recut** = re-edited by us; **whitelist** = run through the creator's account.

## Where the name lives

Notion holds the fields; nothing stores the final string. The daily sync builds it when a row reaches Ready-to-Test and posts it in #tw-creative, and anyone can build one locally:

```bash
python3 -m roadmap.naming build --market tw --date 2026-11-16 --campaign ongoing --format video \
  --production creator --version original --creator "MIP-Jenny" --description "peelfruit-phonespeak-v1" \
  --note app-testing --language tw-en
```

A row can be named once Market, Production Date, Campaign Type, Format, Production Type, Version and Description are filled. Until then the sync reports it as "can't be named yet" with the missing fields.

## One creative, one row

Two ads are the same creative when c1–c8 match. c9 (stage, size, OS) and c10 do not make a new creative, so the testing copy and the scaling copy of one asset share a roadmap row and its `Ad ID(s)` list. `roadmap.naming.creative_key` is the single definition of this.

## Reading legacy names

Ads launched before the new convention use the old nine slots. They are never renamed; rows keep the full legacy name in `Description`.

```
c1!UGC_c2!video_c3!ugc_c4!testimonial_c5!ongoing_c6!Hua_c7!method.walking.PhoneSpeak_c8!GRWM-v2-ToeicGold_c9!app-testing
   type   media    source  angle          campaign   creator  elements                  descriptor         stage
```

`python3 -m roadmap.naming parse "<name>"` maps them onto the new properties:

| Legacy slot | Becomes |
|---|---|
| c2 `video` / `image` | `Format` |
| c5 `ongoing` / `promo` | `Campaign Type` |
| c3 `generic` (or an AI creator) | `Production Type` Inhouse, `Version` na |
| c3 `influencer` | `Production Type` Licensed, `Legacy Cate.` Influencer |
| c3 `whitelist` | `Production Type` Creator, `Version` whitelist |
| c3 `ugc` | `Production Type` Creator |
| c1 `Static` / `Video` / `Motion` / `UGC` | `Legacy Cate.` (`-HK` suffix → `Market` HK) |
| c6 | `Creator Name` (matched to an existing option ignoring case) |
| c7 tokens | `Element` (ba, walking, urgency, …) and `Product Feature` (phonespeak, freetalk, …) |

The production-source rows are inferences, not facts: legacy names never said whether a UGC creator was commissioned or an actor. Automation only fills these on rows where the field is empty.

A legacy name is the same creative as another only when the whole name matches (ignoring case and spaces).
