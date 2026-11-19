# Notion boards and schema

Snapshot of 2026-11-19, after the naming-convention update. The runbooks depend on the property names and option strings below; `routines/daily_sync.md` STEP 0 stops the run if a column it needs is gone. When the schema changes, update this page and the runbooks in the same commit.

## Boards

| Board | Data source | Used for |
|---|---|---|
| TW Creative Roadmap 正式版 | `collection://46a9a0c5-2240-4576-8574-ce81793d224b` (database `b44d9c2c3834497d9f1dcb3e140170c8`) | One row per creative, from Plan to Archive |
| 🗺️ Creatives Ideas | `collection://921b7b9b-effe-411d-9fc2-ca99eb48f328` | Idea backlog; `In progress` promotes an idea to the roadmap |
| Influencer Licenses | `collection://bf9dd8a5-0331-47a3-9d04-9c15bea80071` | Licence terms and days left per influencer asset |
| 🥯 TW/HK Design Board | `collection://6e5a40fb-e8f0-4f59-bc59-2b880e62e6b7` | Designer queue (not touched by automation) |
| 🗃️ Creative Projects | `collection://3c3792ec-2f10-8011-8cdf-000bbc38ad01` | Project grouping (`Project` relation; not touched) |

All sit under Speak OS → TW/HK Market → Creative.

## Roadmap properties

**Identity**

| Property | Type | Written by | Notes |
|---|---|---|---|
| `Item` | title | people; sync for rows it creates | Short 繁體中文 display name |
| `Ad ID(s)` | text | sync | Comma-separated Meta ad IDs; the join key to Meta and BigQuery |
| `Reference` | url | sync / people | Source idea page (dedupe key for Plan rows) or the asset link |
| `Parent creative` | relation → roadmap | sync | Lineage for iteration ideas |

**Naming convention** (the page layout's first section; see [naming-convention.md](naming-convention.md))

| Property | Type | Options |
|---|---|---|
| `Market` | select | `TW 🇹🇼` · `HK 🇭🇰` |
| `Production Date` | date | |
| `Campaign Type` | select | Ongoing · Promo |
| `Format` | select | Video · Image · Carousel |
| `Production Type` | select | Creator · Licensed · Inhouse · Agency · Freelancer · Actor |
| `Version` | select | original · recut · whitelist · na |
| `Creator Name` | multi-select | open list; new creators may be added |
| `Description` | text | c8 of the name. On rows launched before the convention it holds the full legacy Meta ad name |
| `Language Pair` | select | TW-EN · TW-JP |

**Classification** (people)

| Property | Type | Options |
|---|---|---|
| `Category` | select | 💼 商務職場 · 🧠 學習理論 · 🌱生活 · ✈️ 旅遊 · 📑 考試/學術 · 🧑‍🏫 英文教學 · 🎓 留學/打度/移居 · 🌱自我成長/生活 · Campaign |
| `Legacy Cate.` | select | Static · Video · Influencer · AI-Gen · Motion · UGC |
| `Product Feature` | multi-select | Video Lesson · Free Talk · Phone Speak · Speak System · Discussion Unit · Custom Course |
| `Element` | multi-select | B/A · Walking · Live proof · Theory · AI illu · Creator Cred · Full Eng · Urgency · Challenge · Grateful · Tips · Makeup · Testimonial · Peel Fruit · OpenAI · Interview cut |
| `Hook` | text | |
| `Channel` | multi-select | Meta · Google · Other |
| `Owner` | person | |
| `Project`, `Relation to Design Board`, `Relation to Influencer Licenses` | relations | |
| `Files & media` | files | |

**Lifecycle and performance** (sync)

| Property | Type | Options / notes |
|---|---|---|
| `Production Status` | select | Plan · Production · Ready-to-Test · On Air · Pause · Archive |
| `Launch date`, `Paused date`, `Last synced` | date | |
| `Pause reason` | select | Budget Capped · SP Threshold · License Expired · Graduate (Winning) · Fatigue · Campaign End · Other |
| `SP score` | number | |
| `SP status` | select | Testing · Pause · Mid-tier · P1 Winner · P2 Loser · P2 Hit Ad |
| `CPFT`, `Spend to date` | number ($) | |
| `LTV/CAC` | number | |
| `Influencer Priority`, `License days left` | rollups | Not queryable by SQL; fetch the page to read them |

**Removed in the 2026-11 update** — do not reference: `Name` (now `Item`), `Meta ad ID(s)` (now `Ad ID(s)`), `Ad Name` (legacy names moved to `Description`), `Watch flag`, `Hit ad`, `Learnings`, `Priority`, `Source`. The numbered pillars (`01. Speak 學習路徑` …) no longer exist on the roadmap `Category`; they remain on the Ideas board as `Pillar`.

## Markers the automation leaves as page comments

| Comment | Meaning |
|---|---|
| `rt-ping-sent <date>` | The Ready-to-Test announcement (with the ad name) was posted |
| `hit-ad-posted <date>` | The win was posted to #hit-ads-library |
| `relaunch-detected <date> · previous reason: …` | A paused row came back On Air |
| `duplicate-of <url>` / `duplicate-merged <date> → <url>` | Archived as a duplicate in the 2026-11 cleanup |

## Views the reports link to

| View | Filter | URL |
|---|---|---|
| 🏆 Winning creatives | `SP score` ≥ 2 | https://www.notion.so/b44d9c2c3834497d9f1dcb3e140170c8?v=3d6792ec2f10811aad8d000c465a7a27 |
| ⏸️ Pause reason needed | Pause and reason empty | https://www.notion.so/b44d9c2c3834497d9f1dcb3e140170c8?v=3d6792ec2f1081fe9731000c626e0325 |
| 🚀 Creative online log | Launch date set | https://www.notion.so/b44d9c2c3834497d9f1dcb3e140170c8?v=3d6792ec2f1081829fbb000ccd17b9fb |

Other views: Master View, Active, Pipeline, Waitlist (Ready-to-Test), Live / Scale (still filters on the removed `Scale` status), Watch / Pause candidates, Launch Calendar, Archive / Learnings.

## Notion SQL limits

- A query returns at most **100 rows**. Page with `ORDER BY url LIMIT 100 OFFSET n`.
- Dates are queried as `"date:<Property>:start"`; multi-selects and relations come back as JSON-array strings.
- Rollups and formulas are not queryable.
