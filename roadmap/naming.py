"""Speak TW/HK creative naming convention (APAC builder, TW tab, 2026-11).

One creative = ten fields, c1..c10:

    c1 country · c2 production date (YYMMDD) · c3 campaign type · c4 format ·
    c5 production type · c6 version · c7 creator · c8 description ·
    c9 note (size / spec / stage / OS) · c10 language pair

    Meta ad name : c1:tw_c2:261116_c3:ongoing_c4:image_c5:creator_c6:original_c7:na_c8:..._c9:_c10:
    File name    : same string with "!" instead of ":" (colons are not allowed in file names)

This module parses both the new names and the pre-2026-11 "legacy" names
(c1 type · c2 media · c3 source · c4 angle · c5 campaign type · c6 creator ·
c7 elements · c8 descriptor · c9 stage), maps them onto the Notion roadmap
properties, and builds new names from Notion properties.

Standard library only. CLI:

    python3 -m roadmap.naming parse "<ad name>" ["<ad name>" ...]
    python3 -m roadmap.naming build --market tw --date 2026-11-16 --campaign ongoing \
        --format image --production creator --version original --creator na \
        --description "phonespeak-walking-1080x1920" [--note app-testing] [--language tw-en]
"""
from __future__ import annotations

import argparse
import json
import re
import sys

FIELD_NAMES = {
    1: "country", 2: "production_date", 3: "campaign_type", 4: "format",
    5: "production_type", 6: "version", 7: "creator", 8: "description",
    9: "note", 10: "language_pair",
}
REQUIRED = (1, 2, 3, 4, 5, 6, 7, 8)          # c9 and c10 may be empty

COUNTRIES = ("tw", "hk", "kr", "jp")
CAMPAIGN_TYPES = ("promo", "ongoing")
FORMATS = ("video", "image", "carousel")
PRODUCTION_TYPES = ("creator", "licensed", "inhouse", "agency", "freelancer", "actor")
VERSIONS = ("original", "recut", "whitelist", "na")
LANGUAGE_PAIRS = ("tw-en", "tw-jp")

# Notion option strings (exact) -------------------------------------------------
MARKET_OPTION = {"tw": "TW 🇹🇼", "hk": "HK 🇭🇰"}
CAMPAIGN_OPTION = {"promo": "Promo", "ongoing": "Ongoing"}
FORMAT_OPTION = {"video": "Video", "image": "Image", "carousel": "Carousel"}
PRODUCTION_OPTION = {
    "creator": "Creator", "licensed": "Licensed", "inhouse": "Inhouse",
    "agency": "Agency", "freelancer": "Freelancer", "actor": "Actor",
}
LANGUAGE_OPTION = {"tw-en": "TW-EN", "tw-jp": "TW-JP"}

# Legacy c1 (creative type) -> Notion "Legacy Cate."
LEGACY_CATE = {"static": "Static", "video": "Video", "motion": "Motion", "ugc": "UGC",
               "ai-ugc": "AI-Gen"}
# Legacy c7 tokens (dot separated) -> Notion "Element" / "Product Feature"
ELEMENT_TOKENS = {
    "ba": "B/A", "walking": "Walking", "realproof": "Live proof", "livedemo": "Live proof",
    "theory": "Theory", "aiillu": "AI illu", "credibility": "Creator Cred",
    "fulleng": "Full Eng", "allenglish": "Full Eng", "urgency": "Urgency",
    "challenge": "Challenge", "grateful": "Grateful", "tip": "Tips", "tips": "Tips",
    "testimonial": "Testimonial", "peelfruit": "Peel Fruit", "openai": "OpenAI",
    "interviewcut": "Interview cut",
}
FEATURE_TOKENS = {
    "phonespeak": "Phone Speak", "freetalk": "Free Talk", "videolesson": "Video Lesson",
    "customcourses": "Custom Course", "customcourse": "Custom Course",
}
AI_CREATORS = ("ai-gen", "aigen", "ai-miso", "miso")

_SPLIT = re.compile(r"_(?=\s*c\d{1,2}[!:])")
_PART = re.compile(r"\s*c(\d{1,2})[!:](.*)", re.S)


def parse(name: str) -> dict:
    """Parse an ad / file name into {'convention', 'fields', 'errors'}.

    convention is 'v2' (APAC 2026-11), 'legacy' (old c1!type_c2!media…) or 'unknown'.
    fields is {1: 'tw', 2: '261116', ...} keyed by the c-number, values stripped.
    """
    raw = (name or "").strip()
    fields: dict[int, str] = {}
    for part in _SPLIT.split(raw):
        m = _PART.match(part)
        if m:
            fields[int(m.group(1))] = m.group(2).strip()
    out = {"name": raw, "convention": "unknown", "fields": fields, "errors": []}
    if not fields:
        return out
    c1, c2 = fields.get(1, "").lower(), fields.get(2, "").lower()
    if c1 in COUNTRIES and re.fullmatch(r"\d{6}", c2):
        out["convention"] = "v2"
        out["errors"] = validate(fields)
    elif c2 in ("video", "image"):
        out["convention"] = "legacy"
    return out


def validate(fields: dict[int, str]) -> list[str]:
    """Return the list of problems with a v2 field set (empty list = valid)."""
    errs = []
    low = {k: (v or "").strip().lower() for k, v in fields.items()}
    for k in REQUIRED:
        if not low.get(k):
            errs.append(f"c{k} {FIELD_NAMES[k]} is empty")
    for k, v in fields.items():
        if "_" in (v or ""):
            errs.append(f"c{k} {FIELD_NAMES[k]} contains an underscore")
    checks = ((1, COUNTRIES), (3, CAMPAIGN_TYPES), (4, FORMATS),
              (5, PRODUCTION_TYPES), (6, VERSIONS))
    for k, allowed in checks:
        if low.get(k) and low[k] not in allowed:
            errs.append(f"c{k} {FIELD_NAMES[k]} '{fields[k]}' is not one of {'/'.join(allowed)}")
    if low.get(2) and not _valid_yymmdd(low[2]):
        errs.append(f"c2 production_date '{fields[2]}' is not YYMMDD")
    if low.get(10) and low[10] not in LANGUAGE_PAIRS:
        errs.append(f"c10 language_pair '{fields[10]}' is not one of {'/'.join(LANGUAGE_PAIRS)}")
    return errs


def _valid_yymmdd(s: str) -> bool:
    if not re.fullmatch(r"\d{6}", s):
        return False
    mm, dd = int(s[2:4]), int(s[4:6])
    return 1 <= mm <= 12 and 1 <= dd <= 31


def slug(text: str) -> str:
    """Lowercase free text for a name field: no underscores, spaces or separators."""
    s = (text or "").strip().lower()
    s = re.sub(r"[_\s/\\:!|]+", "-", s)
    s = re.sub(r"[()\[\]{}'\"`,;]+", "", s)
    s = re.sub(r"-{2,}", "-", s).strip("-")
    return s


def build(fields: dict[int, str]) -> dict:
    """Build the two final names from c1..c10 values. Values are slugged first."""
    clean = {k: slug(fields.get(k, "")) for k in range(1, 11)}
    if not clean[7]:
        clean[7] = "na"
    errs = validate(clean)
    body = "_".join(f"c{k}:{clean[k]}" for k in range(1, 11))
    return {
        "ad_name": None if errs else body,
        "file_name": None if errs else body.replace(":", "!"),
        "fields": clean,
        "errors": errs,
    }


def from_notion(row: dict, note: str = "") -> dict:
    """Build names from a roadmap row keyed by Notion property names.

    Accepts the SQL column spelling too ('date:Production Date:start', JSON-array
    strings for multi-selects).
    """
    market = (row.get("Market") or "").split(" ")[0].lower()
    date = row.get("date:Production Date:start") or row.get("Production Date") or ""
    m = re.match(r"(\d{4})-(\d{2})-(\d{2})", date)
    creators = _as_list(row.get("Creator Name"))
    creators = [c for c in creators if c.lower() not in ("n/a", "na")]
    description = row.get("Description") or ""
    if parse(description)["convention"] != "unknown":
        description = ""            # a full legacy name is not a c8 description
    return build({
        1: market,
        2: f"{m.group(1)[2:]}{m.group(2)}{m.group(3)}" if m else "",
        3: row.get("Campaign Type") or "",
        4: row.get("Format") or "",
        5: row.get("Production Type") or "",
        6: row.get("Version") or "",
        7: "+".join(slug(c) for c in creators),
        8: description,
        9: note,
        10: row.get("Language Pair") or "",
    })


def _as_list(value) -> list[str]:
    if value is None or value == "":
        return []
    if isinstance(value, (list, tuple)):
        return [str(v) for v in value]
    try:
        loaded = json.loads(value)
        if isinstance(loaded, list):
            return [str(v) for v in loaded]
    except (TypeError, ValueError):
        pass
    return [str(value)]


def match_option(value: str, options) -> str | None:
    """Case-insensitive exact match of value against existing Notion option names."""
    want = (value or "").strip().lower()
    for opt in options or ():
        if opt.strip().lower() == want:
            return opt
    return None


def to_notion(parsed: dict, creator_options=None) -> dict:
    """Map a parsed name onto Notion roadmap properties (only what the name states).

    Returns {'properties': {...}, 'new_creator_option': bool, 'notes': [...]}.
    Callers write a property only when the row's current value is empty.
    """
    f = {k: (v or "").strip() for k, v in parsed["fields"].items()}
    low = {k: v.lower() for k, v in f.items()}
    props: dict = {}
    notes: list[str] = []
    new_creator = False

    def creator(handle: str):
        nonlocal new_creator
        if not handle or handle.lower() in ("na", "n/a"):
            return
        hit = match_option(handle, creator_options)
        if hit is None and creator_options is not None:
            new_creator = True
        props["Creator Name"] = [hit or handle]

    if parsed["convention"] == "v2":
        if low.get(1) in MARKET_OPTION:
            props["Market"] = MARKET_OPTION[low[1]]
        if _valid_yymmdd(low.get(2, "")):
            props["date:Production Date:start"] = f"20{low[2][:2]}-{low[2][2:4]}-{low[2][4:]}"
        for k, prop, table in ((3, "Campaign Type", CAMPAIGN_OPTION), (4, "Format", FORMAT_OPTION),
                               (5, "Production Type", PRODUCTION_OPTION)):
            if low.get(k) in table:
                props[prop] = table[low[k]]
        if low.get(6) in VERSIONS:
            props["Version"] = low[6]
        creator(f.get(7, ""))
        if f.get(8):
            props["Description"] = f[8]
        if low.get(10) in LANGUAGE_OPTION:
            props["Language Pair"] = LANGUAGE_OPTION[low[10]]
        notes.extend(parsed.get("errors", []))

    elif parsed["convention"] == "legacy":
        c1, c3, c6 = low.get(1, ""), low.get(3, ""), low.get(6, "")
        props["Format"] = FORMAT_OPTION[low[2]]
        if low.get(5) in CAMPAIGN_OPTION:
            props["Campaign Type"] = CAMPAIGN_OPTION[low[5]]
        if c1.endswith("-hk"):
            props["Market"] = MARKET_OPTION["hk"]
        is_ai = c6 in AI_CREATORS or c1 == "ai-ugc"
        # Production source, inferred from the legacy c3 "source" slot.
        if c3 in ("generic", "motion") or is_ai:
            props["Production Type"], props["Version"] = "Inhouse", "na"
        elif c3 == "influencer":
            props["Production Type"] = "Licensed"
        elif c3 == "whitelist":
            props["Production Type"], props["Version"] = "Creator", "whitelist"
        elif c3 == "ugc":
            props["Production Type"] = "Creator"
        # Legacy Cate.
        base = re.sub(r"-hk$", "", re.sub(r"\d+$", "", c1))
        if is_ai:
            props["Legacy Cate."] = "AI-Gen"
        elif c3 == "influencer":
            props["Legacy Cate."] = "Influencer"
        elif base in LEGACY_CATE:
            props["Legacy Cate."] = LEGACY_CATE[base]
        if not is_ai:
            creator(f.get(6, ""))
        tokens = [t for t in re.split(r"[.\s]+", low.get(7, "")) if t]
        elements = _dedupe(ELEMENT_TOKENS[t] for t in tokens if t in ELEMENT_TOKENS)
        features = _dedupe(FEATURE_TOKENS[t] for t in tokens if t in FEATURE_TOKENS)
        if elements:
            props["Element"] = elements
        if features:
            props["Product Feature"] = features
    return {"properties": props, "new_creator_option": new_creator, "notes": notes}


def _dedupe(items) -> list[str]:
    seen, out = set(), []
    for i in items:
        if i not in seen:
            seen.add(i)
            out.append(i)
    return out


def creative_key(name: str) -> str | None:
    """Stable key for "is this Meta ad the same creative as that row?".

    v2 names: c1..c8 lowercased (c9 note and c10 language pair ignored), so the
    app-testing and web-scaling copies of one creative share a key.
    Legacy names: the whole name, lowercased, whitespace removed, ':' == '!'.
    """
    p = parse(name)
    if p["convention"] == "v2":
        return "v2|" + "|".join(p["fields"].get(k, "").strip().lower() for k in range(1, 9))
    if p["convention"] == "legacy":
        return "legacy|" + re.sub(r"\s+", "", p["name"].lower()).replace(":", "!")
    return None


def row_key(row: dict) -> str | None:
    """creative_key for a roadmap row: from its naming fields, else its legacy Description."""
    legacy = creative_key(row.get("Description") or "")
    if legacy:
        return legacy
    built = from_notion(row)
    if built["ad_name"]:
        return creative_key(built["ad_name"])
    return None


def _cli(argv=None) -> int:
    ap = argparse.ArgumentParser(prog="roadmap.naming", description=__doc__.split("\n")[0])
    sub = ap.add_subparsers(dest="cmd", required=True)
    p = sub.add_parser("parse", help="parse ad names into fields + Notion properties")
    p.add_argument("names", nargs="+")
    b = sub.add_parser("build", help="build the Meta ad name and the file name")
    b.add_argument("--market", required=True)
    b.add_argument("--date", required=True, help="production date, YYYY-MM-DD or YYMMDD")
    b.add_argument("--campaign", required=True)
    b.add_argument("--format", required=True)
    b.add_argument("--production", required=True)
    b.add_argument("--version", required=True)
    b.add_argument("--creator", default="na")
    b.add_argument("--description", required=True)
    b.add_argument("--note", default="")
    b.add_argument("--language", default="")
    args = ap.parse_args(argv)

    if args.cmd == "parse":
        out = []
        for n in args.names:
            parsed = parse(n)
            mapped = to_notion(parsed)
            out.append({
                "name": parsed["name"], "convention": parsed["convention"],
                "fields": {f"c{k}": v for k, v in sorted(parsed["fields"].items())},
                "notion": mapped["properties"], "errors": parsed["errors"],
                "creative_key": creative_key(n),
            })
        print(json.dumps(out, ensure_ascii=False, indent=2))
        return 0

    d = args.date
    m = re.fullmatch(r"(\d{4})-(\d{2})-(\d{2})", d)
    if m:
        d = m.group(1)[2:] + m.group(2) + m.group(3)
    res = build({1: args.market, 2: d, 3: args.campaign, 4: args.format, 5: args.production,
                 6: args.version, 7: args.creator, 8: args.description, 9: args.note,
                 10: args.language})
    print(json.dumps(res, ensure_ascii=False, indent=2))
    return 1 if res["errors"] else 0


if __name__ == "__main__":
    sys.exit(_cli())
