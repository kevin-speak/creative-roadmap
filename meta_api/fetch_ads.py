#!/usr/bin/env python3
"""Pull the ad list + spend the nightly sync needs and write it as JSON / CSV.

This reproduces "STEP 2 — Pull live Meta ads" from routines/routine1_nightly_sync.md
using the direct Marketing API instead of the Meta Ads MCP:

  * every ad in the account with id, name, effective_status, created_time, campaign
  * lifetime spend   (date_preset=maximum)
  * last-7-day spend, impressions, frequency (date_preset=last_7d)

Examples:
    python3 meta_api/fetch_ads.py                       # all ads → stdout JSON
    python3 meta_api/fetch_ads.py --active --csv out.csv
    python3 meta_api/fetch_ads.py --ad-id 120230000000000001 120230000000000002
"""

from __future__ import annotations

import argparse
import csv
import json
import sys
from pathlib import Path
from typing import Any, Dict, List

sys.path.insert(0, str(Path(__file__).resolve().parent))

from meta_client import MetaClient, load_config  # noqa: E402

LEGACY_CAMPAIGN_IDS = {"120229358097810167"}  # TW_Meta_N/A_M3_Q3Reach_brandmarketing (excluded per CAMPAIGN SCOPE)


def is_legacy_campaign(ad: Dict[str, Any]) -> bool:
    cid = ad.get("campaign_id", "")
    name = (ad.get("campaign") or {}).get("name", "")
    return cid in LEGACY_CAMPAIGN_IDS or "25Q" in name


def build_rows(client: MetaClient, active_only: bool, ad_ids: List[str] | None,
               include_legacy: bool) -> List[Dict[str, Any]]:
    if ad_ids:
        ads = [client.get_ad(a) for a in ad_ids]
    else:
        ads = client.get_ads(effective_status=["ACTIVE"] if active_only else None)

    lifetime = {r["ad_id"]: r for r in client.get_ad_insights("maximum", ad_ids=ad_ids)}
    last7 = {r["ad_id"]: r for r in client.get_ad_insights("last_7d", ad_ids=ad_ids)}

    rows: List[Dict[str, Any]] = []
    for ad in ads:
        if not include_legacy and is_legacy_campaign(ad):
            continue
        lt = lifetime.get(ad["id"], {})
        l7 = last7.get(ad["id"], {})
        rows.append({
            "ad_id": ad["id"],
            "ad_name": ad.get("name"),
            "effective_status": ad.get("effective_status"),
            "created_time": ad.get("created_time"),
            "campaign_id": ad.get("campaign_id"),
            "campaign_name": (ad.get("campaign") or {}).get("name"),
            "adset_id": ad.get("adset_id"),
            "spend_lifetime": float(lt.get("spend", 0) or 0),
            "spend_last_7d": float(l7.get("spend", 0) or 0),
            "impressions_last_7d": int(l7.get("impressions", 0) or 0),
            "frequency_last_7d": float(l7.get("frequency", 0) or 0),
        })
    rows.sort(key=lambda r: r["spend_lifetime"], reverse=True)
    return rows


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--active", action="store_true", help="only effective_status=ACTIVE ads")
    ap.add_argument("--ad-id", nargs="+", metavar="ID", help="fetch only these ad ids")
    ap.add_argument("--include-legacy", action="store_true", help="keep 25Qx / legacy-campaign ads")
    ap.add_argument("--csv", metavar="PATH", help="write CSV here instead of JSON to stdout")
    ap.add_argument("--json", metavar="PATH", help="write JSON here instead of stdout")
    args = ap.parse_args()

    client = MetaClient(**load_config())
    rows = build_rows(client, args.active, args.ad_id, args.include_legacy)

    if args.csv:
        with open(args.csv, "w", newline="", encoding="utf-8") as fh:
            writer = csv.DictWriter(fh, fieldnames=list(rows[0].keys()) if rows else ["ad_id"])
            writer.writeheader()
            writer.writerows(rows)
        print(f"wrote {len(rows)} rows to {args.csv}", file=sys.stderr)
    elif args.json:
        Path(args.json).write_text(json.dumps(rows, ensure_ascii=False, indent=2), encoding="utf-8")
        print(f"wrote {len(rows)} rows to {args.json}", file=sys.stderr)
    else:
        json.dump(rows, sys.stdout, ensure_ascii=False, indent=2)
        print()
    return 0


if __name__ == "__main__":
    sys.exit(main())
