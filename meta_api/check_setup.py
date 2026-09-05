#!/usr/bin/env python3
"""Verify the Meta API setup end to end. Run this first after filling in meta_api/.env.

    python3 meta_api/check_setup.py

Each check prints PASS / FAIL with the reason. Nothing is written to Meta.
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from meta_client import MetaAPIError, MetaClient, load_config  # noqa: E402

EXPECTED_ACCOUNT = "1148917790153640"   # Speak ZH
EXPECTED_BUSINESS = "1228002260697334"  # Speak


def _ok(label: str, detail: str = "") -> None:
    print(f"  PASS  {label}" + (f" — {detail}" if detail else ""))


def _fail(label: str, detail: str) -> None:
    print(f"  FAIL  {label} — {detail}")


def main() -> int:
    print("Meta API setup check\n")
    failures = 0

    # 1. Config present
    try:
        cfg = load_config()
    except SystemExit as exc:
        _fail("config", str(exc))
        return 1
    _ok("config", f"account {cfg['ad_account_id']}, API {cfg['api_version']}, "
                  f"appsecret_proof {'on' if cfg['app_secret'] else 'off'}")
    client = MetaClient(**cfg)

    # 2. Token is valid
    try:
        me = client.me()
        _ok("token", f"authenticated as {me.get('name')} (id {me.get('id')})")
    except MetaAPIError as exc:
        _fail("token", str(exc))
        print("\n  A 190 error means the token is invalid or expired. Regenerate it in Business Manager"
              " → System Users → Generate token.")
        return 1

    # 3. Token scopes / expiry (optional, needs app id + secret)
    app_id = os.environ.get("META_APP_ID", "").strip()
    if app_id and cfg["app_secret"]:
        try:
            info = client.debug_token(app_id).get("data", {})
            scopes = info.get("scopes", [])
            expires = info.get("expires_at", 0)
            expiry = "never" if expires == 0 else f"unix {expires}"
            if "ads_read" in scopes or "ads_management" in scopes:
                _ok("scopes", f"{', '.join(scopes)}; expires {expiry}")
            else:
                failures += 1
                _fail("scopes", f"token lacks ads_read (has: {', '.join(scopes) or 'none'})")
        except MetaAPIError as exc:
            _fail("scopes", str(exc))
            failures += 1
    else:
        print("  SKIP  scopes — set META_APP_ID and META_APP_SECRET to inspect token scopes/expiry")

    # 4. Ad account reachable
    try:
        acct = client.account()
        biz = acct.get("business", {}) or {}
        detail = (f"{acct.get('name')} ({acct.get('id')}), status {acct.get('account_status')}, "
                  f"{acct.get('currency')}, tz {acct.get('timezone_name')}, business {biz.get('name')} ({biz.get('id')})")
        if cfg["ad_account_id"].replace("act_", "") == EXPECTED_ACCOUNT and biz.get("id") not in (None, EXPECTED_BUSINESS):
            failures += 1
            _fail("account", f"expected Speak business {EXPECTED_BUSINESS}; got {detail}")
        else:
            _ok("account", detail)
    except MetaAPIError as exc:
        failures += 1
        _fail("account", str(exc))
        if exc.code == 100 or exc.code == 200:
            print("  The system user probably isn't assigned to this ad account. Business Manager →"
                  " System Users → Add assets → Ad accounts → Speak ZH (View performance is enough).")
        return 1

    # 5. Ads are listable (the call the nightly sync depends on)
    try:
        ads = client.get_ads(effective_status=["ACTIVE"])
        _ok("ads", f"{len(ads)} ACTIVE ads")
        for ad in ads[:3]:
            print(f"         {ad['id']}  {ad['name'][:70]}")
    except MetaAPIError as exc:
        failures += 1
        _fail("ads", str(exc))

    # 6. Insights are readable
    try:
        rows = client.get_ad_insights(date_preset="last_7d")
        spend = sum(float(r.get("spend", 0) or 0) for r in rows)
        _ok("insights", f"{len(rows)} ad rows in last_7d, total spend {spend:,.2f} {acct.get('currency', '')}")
    except MetaAPIError as exc:
        failures += 1
        _fail("insights", str(exc))

    print()
    if failures:
        print(f"{failures} check(s) failed.")
        return 1
    print("All checks passed. The Meta API is set up.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
