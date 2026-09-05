# Meta Marketing API setup

Direct, read-only access to the **Speak ZH** ad account (`act_1148917790153640`, Speak business `1228002260697334`) through the Graph API — independent of the Meta Ads MCP connector. Use it when a routine, script, or fresh session needs Meta data and the MCP grant isn't available (see the architecture note in [`../automation/README.md`](../automation/README.md)).

```
meta_api/
├── .env.example      # config template → copy to .env (git-ignored)
├── requirements.txt  # requests + python-dotenv
├── meta_client.py    # MetaClient: auth, retries, pagination, ads/insights helpers
├── check_setup.py    # 6-point verification — run this first
└── fetch_ads.py      # routine1 STEP 2 equivalent: ads + lifetime/7d spend → JSON/CSV
```

## Step 1 — Create (or pick) a Meta app

1. Go to <https://developers.facebook.com/apps> and click **Create App**.
2. Use case: **Other** → type **Business**. Name it e.g. `Speak TW Creative Automation`. Attach it to the **Speak** business portfolio.
3. In the app dashboard, **Add product → Marketing API**.
4. Note the **App ID** and **App Secret** (Settings → Basic). You need them for `appsecret_proof` and for inspecting token scopes.

The app can stay in Development mode. Development mode only restricts *user* tokens of people without a role on the app; a System User token from your own business works fine.

## Step 2 — Create a System User and token (Business Manager)

A System User token doesn't expire and isn't tied to a person's login, which is what an automation needs.

1. <https://business.facebook.com/settings> → **Users → System users → Add**. Name: `tw-creative-automation`, role: **Employee** (Admin is not needed for read).
2. Select the system user → **Add assets**:
   - **Ad accounts → Speak ZH** → grant **View performance** (read-only). Only tick *Manage campaigns* if you deliberately want write access — nothing in this repo needs it.
   - **Apps →** the app from Step 1 → **Develop app**.
3. **Generate new token** → choose the app → token expiration **Never** → permissions: **`ads_read`** (add `business_management` only if you'll call business-level endpoints). Copy the token now; it is shown once.

## Step 3 — Configure this repo

```bash
cd meta_api
pip install -r requirements.txt
cp .env.example .env
```

Fill in `.env`:

| Variable | Value |
|---|---|
| `META_ACCESS_TOKEN` | the System User token from Step 2 |
| `META_AD_ACCOUNT_ID` | `1148917790153640` (no `act_` prefix) |
| `META_APP_ID` / `META_APP_SECRET` | from Step 1 — optional, but enables `appsecret_proof` and the scope check |
| `META_API_VERSION` | `v21.0` unless you have a reason to change it |

`.env` is git-ignored. Never paste the token into a runbook, Notion, or Slack.

## Step 4 — Verify

```bash
python3 meta_api/check_setup.py
```

Expected output:

```
Meta API setup check

  PASS  config — account 1148917790153640, API v21.0, appsecret_proof on
  PASS  token — authenticated as tw-creative-automation (id 1…)
  PASS  scopes — ads_read; expires never
  PASS  account — Speak ZH (act_1148917790153640), status 1, USD, tz Asia/Taipei, business Speak (1228002260697334)
  PASS  ads — 67 ACTIVE ads
         120230…  c1!ugc_c2!…
  PASS  insights — 67 ad rows in last_7d, total spend 12,345.67 USD

All checks passed. The Meta API is set up.
```

Common failures:

| Message | Fix |
|---|---|
| `code=190` on the token check | Token invalid/expired → regenerate (Step 2.3). |
| `code=100`/`200` on the account check | System user not assigned to Speak ZH → Step 2.2. |
| `FAIL scopes — token lacks ads_read` | Regenerate the token with `ads_read` ticked. |
| `code=4` / `17` / `32` | Rate limited; the client already retries with backoff — wait a minute. |
| `CONNECT tunnel failed … 403` | Network policy blocks `graph.facebook.com`. Claude Code on the web sandboxes block it by default; run locally or allow the host in the environment's network settings. |

## Step 5 — Use it

```bash
# All current-campaign ads with lifetime + 7-day spend, sorted by spend
python3 meta_api/fetch_ads.py --active --csv meta_api/out/ads.csv

# Verify specific ads (the "individually confirm inactive" step in routine1 STEP 6)
python3 meta_api/fetch_ads.py --ad-id 120230000000000001 120230000000000002
```

From Python:

```python
from meta_client import MetaClient, load_config

client = MetaClient(**load_config())
live = client.get_ads(effective_status=["ACTIVE"])
spend = {r["ad_id"]: float(r["spend"]) for r in client.get_ad_insights("maximum")}
```

`MetaClient.get(path, params)` and `paginate(path, params)` reach any other GET endpoint.

## Step 6 — Wire it into the routines (optional)

The runbooks in `automation/routines/` currently call the Meta Ads MCP tool `ads_get_ad_entities`. To make them MCP-independent, replace that step with `python3 meta_api/fetch_ads.py --json /tmp/ads.json` and read the file — the columns map 1:1 to what STEP 2 of the nightly sync needs (`ad_id`, `ad_name`, `effective_status`, `created_time`, `spend_lifetime`, `spend_last_7d`, `frequency_last_7d`). The session running the routine must have `.env` available (or `META_*` set as environment variables in the Claude Code environment settings).

## Operating notes

- **Read-only.** The client exposes only GET helpers; the token should only carry `ads_read`. This matches the repo rule that nothing ever writes to Meta.
- **Rate limits.** Marketing API limits are per ad account per hour. The client retries codes 1/2/4/17/32/613 with exponential backoff (max 4 retries). Keep `limit=200` pagination (the default) rather than many small calls.
- **Insights attribution.** `spend` from the Insights API uses the account's default attribution window and is reported in the account currency (USD). BigQuery's `meta_ads_creative_report_funnel` may differ slightly and lags ~2 days; Meta is the source for spend-to-date, BigQuery for funnel metrics.
- **API versions** are retired ~2 years after release. Bump `META_API_VERSION` deliberately and re-run `check_setup.py`.
- **Token rotation.** If the token leaks, revoke it in Business Manager → System users → the user → tokens, then regenerate and update `.env`.
