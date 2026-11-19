"""Read-only audits of a roadmap export. Every command prints a JSON plan; nothing
here talks to Notion. A session applies a plan with the Notion tools after a
human has looked at it.

Input: a JSON list of roadmap rows keyed by the Notion SQL column names used in
sql/notion_roadmap_export.sql (url, Item, Production Status, Description,
Ad ID(s), Reference, Market, Format, ..., date:Paused date:start, createdTime).

    python3 -m roadmap.audit summary  rows.json
    python3 -m roadmap.audit dupes    rows.json
    python3 -m roadmap.audit backfill rows.json [--creator-options creators.json]
    python3 -m roadmap.audit pauses   rows.json --today 2026-11-19
"""
from __future__ import annotations

import argparse
import collections
import datetime as dt
import json
import re
import sys

from . import naming

AD_ID = re.compile(r"^\d{15,}$")
STATUS_RANK = {"On Air": 5, "Ready-to-Test": 4, "Production": 3, "Pause": 2, "Plan": 1,
               "Archive": 0, None: 1}
NAMING_PROPS = ("Market", "date:Production Date:start", "Campaign Type", "Format",
                "Production Type", "Version", "Creator Name", "Language Pair",
                "Legacy Cate.", "Element", "Product Feature")
STALE_PAUSE_DAYS = 7


def ad_ids(row: dict) -> list[str]:
    return [t for t in re.split(r"[,\s]+", row.get("Ad ID(s)") or "") if AD_ID.match(t)]


def page_id(url: str | None) -> str | None:
    m = re.search(r"([0-9a-f]{32})", (url or "").replace("-", ""))
    return m.group(1) if m else None


def _empty(v) -> bool:
    return v is None or v == "" or v == "[]" or v == []


def _filled(row: dict) -> int:
    return sum(0 if _empty(v) else 1 for v in row.values())


def _brief(row: dict) -> dict:
    return {"url": row["url"], "Item": row.get("Item"),
            "Production Status": row.get("Production Status"),
            "Ad ID(s)": row.get("Ad ID(s)"), "created": (row.get("createdTime") or "")[:10]}


def dupes(rows: list[dict]) -> dict:
    """Two kinds of duplicates, each with one keeper and the rows to archive.

    idea:  several open rows whose Reference is the same Notion idea page.
    ad_id: rows connected by a shared Meta ad ID (merged transitively).
    """
    plan = {"idea": [], "ad_id": [], "manual": []}

    by_ref = collections.defaultdict(list)
    for r in rows:
        ref = r.get("Reference") or ""
        if "notion" in ref and r.get("Production Status") != "Archive":
            by_ref[page_id(ref)].append(r)
    for ref, group in by_ref.items():
        if ref is None or len(group) < 2:
            continue
        group.sort(key=lambda r: (-STATUS_RANK.get(r.get("Production Status"), 1),
                                  -_filled(r), r.get("createdTime") or ""))
        keep, rest = group[0], group[1:]
        safe = [r for r in rest if r.get("Production Status") in ("Plan", None) and not ad_ids(r)]
        for r in rest:
            if r not in safe:
                plan["manual"].append({"why": "duplicate idea row is past Plan",
                                       "keep": _brief(keep), "row": _brief(r)})
        if safe:
            plan["idea"].append({"keep": _brief(keep), "archive": [_brief(r) for r in safe]})

    parent = {r["url"]: r["url"] for r in rows}

    def find(u):
        while parent[u] != u:
            parent[u] = parent[parent[u]]
            u = parent[u]
        return u

    owner: dict[str, str] = {}
    for r in rows:
        for i in ad_ids(r):
            if i in owner:
                parent[find(r["url"])] = find(owner[i])
            else:
                owner[i] = r["url"]
    comps = collections.defaultdict(list)
    for r in rows:
        if ad_ids(r):
            comps[find(r["url"])].append(r)
    for group in comps.values():
        if len(group) < 2:
            continue
        group.sort(key=lambda r: (-STATUS_RANK.get(r.get("Production Status"), 1),
                                  -(r.get("Spend to date") or 0), -len(ad_ids(r)),
                                  r.get("createdTime") or ""))
        keep, rest = group[0], group[1:]
        union = naming._dedupe(i for r in group for i in ad_ids(r))
        plan["ad_id"].append({
            "keep": _brief(keep), "keep_ad_ids": ",".join(union),
            "archive": [_brief(r) for r in rest],
        })
    plan["counts"] = {
        "idea_groups": len(plan["idea"]),
        "idea_rows_to_archive": sum(len(g["archive"]) for g in plan["idea"]),
        "ad_id_groups": len(plan["ad_id"]),
        "ad_id_rows_to_archive": sum(len(g["archive"]) for g in plan["ad_id"]),
        "manual": len(plan["manual"]),
    }
    return plan


def backfill(rows: list[dict], creator_options=None) -> dict:
    """Naming fields the row's own ad name states but the row leaves empty."""
    updates, new_creators = [], collections.Counter()
    per_prop = collections.Counter()
    unparsed = 0
    options = None if creator_options is None else list(creator_options)
    for r in rows:
        desc = r.get("Description") or ""
        if not desc:
            continue
        parsed = naming.parse(desc)
        if parsed["convention"] == "unknown":
            unparsed += 1
            continue
        mapped = naming.to_notion(parsed, options)
        if mapped["new_creator_option"]:      # later rows reuse the first spelling
            options.append(mapped["properties"]["Creator Name"][0])
        props = {k: v for k, v in mapped["properties"].items()
                 if k in NAMING_PROPS and _empty(r.get(k))}
        if not props:
            continue
        if "Creator Name" in props and mapped["new_creator_option"]:
            new_creators[props["Creator Name"][0]] += 1
        per_prop.update(props.keys())
        updates.append({"url": r["url"], "Item": r.get("Item"),
                        "convention": parsed["convention"], "set": props})
    return {"updates": updates,
            "counts": {"rows": len(updates), "unparsed_descriptions": unparsed,
                       "by_property": dict(per_prop.most_common())},
            "new_creator_options": dict(new_creators.most_common())}


def pauses(rows: list[dict], today: dt.date) -> dict:
    """Pause rows the stale-reason rule would close (see docs/process.md)."""
    stamp, close, waiting = [], [], []
    for r in rows:
        if r.get("Production Status") != "Pause":
            continue
        paused = r.get("date:Paused date:start")
        if not paused:
            stamp.append(_brief(r))
            continue
        age = (today - dt.date.fromisoformat(paused[:10])).days
        if _empty(r.get("Pause reason")):
            (close if age > STALE_PAUSE_DAYS else waiting).append({**_brief(r), "paused": paused[:10]})
    return {"stamp_paused_date_today": stamp, "set_reason_other": close, "still_waiting": waiting,
            "counts": {"stamp": len(stamp), "close": len(close), "waiting": len(waiting)}}


def summary(rows: list[dict]) -> dict:
    by_status = collections.Counter(r.get("Production Status") or "(none)" for r in rows)
    shapes = collections.Counter(naming.parse(r.get("Description") or "")["convention"]
                                 if r.get("Description") else "empty" for r in rows)
    nameable = sum(1 for r in rows if naming.from_notion(r)["ad_name"])
    return {"rows": len(rows), "by_status": dict(by_status),
            "description_convention": dict(shapes), "rows_with_complete_v2_fields": nameable}


def _cli(argv=None) -> int:
    ap = argparse.ArgumentParser(prog="roadmap.audit", description=__doc__.split("\n")[0])
    ap.add_argument("cmd", choices=("summary", "dupes", "backfill", "pauses"))
    ap.add_argument("rows")
    ap.add_argument("--creator-options", help="JSON list of existing Creator Name options")
    ap.add_argument("--today", help="YYYY-MM-DD (Taipei), required for pauses")
    args = ap.parse_args(argv)
    with open(args.rows, encoding="utf-8") as fh:
        rows = json.load(fh)
    if isinstance(rows, dict):
        rows = rows.get("results", [])
    if args.cmd == "summary":
        out = summary(rows)
    elif args.cmd == "dupes":
        out = dupes(rows)
    elif args.cmd == "backfill":
        opts = None
        if args.creator_options:
            with open(args.creator_options, encoding="utf-8") as fh:
                opts = json.load(fh)
        out = backfill(rows, opts)
    else:
        if not args.today:
            ap.error("pauses needs --today")
        out = pauses(rows, dt.date.fromisoformat(args.today))
    print(json.dumps(out, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(_cli())
