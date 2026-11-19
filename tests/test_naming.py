import datetime as dt
import unittest

from roadmap import audit, naming

SHEET_EXAMPLE = "c1:tw_c2:261116_c3:ongoing_c4:image_c5:creator_c6:original_c7:na_c8:krjp-launch-01-1920x1080_c9:_c10:"
LEGACY = "c1!UGC_c2!video_c3!ugc_c4!testimonial_c5!ongoing_c6!Hua_c7!method.walking.PhoneSpeak_c8!GRWM-v2-ToeicGold_c9!"


class ParseTest(unittest.TestCase):
    def test_v2_sheet_example(self):
        p = naming.parse(SHEET_EXAMPLE)
        self.assertEqual(p["convention"], "v2")
        self.assertEqual(p["errors"], [])
        self.assertEqual(p["fields"][8], "krjp-launch-01-1920x1080")
        self.assertEqual(p["fields"][10], "")

    def test_v2_file_name_uses_bang(self):
        p = naming.parse(SHEET_EXAMPLE.replace(":", "!"))
        self.assertEqual(p["convention"], "v2")
        self.assertEqual(naming.creative_key(SHEET_EXAMPLE),
                         naming.creative_key(SHEET_EXAMPLE.replace(":", "!")))

    def test_v2_reports_bad_option(self):
        p = naming.parse(SHEET_EXAMPLE.replace("c5:creator", "c5:ugc"))
        self.assertEqual(p["convention"], "v2")
        self.assertTrue(any("c5" in e for e in p["errors"]))

    def test_legacy(self):
        p = naming.parse(LEGACY)
        self.assertEqual(p["convention"], "legacy")
        self.assertEqual(p["fields"][6], "Hua")

    def test_legacy_underscore_inside_last_field(self):
        p = naming.parse("c1!260901_c2!video_c3!ugc_c4!problemsolution_c5!b2b_c6!audrey_c7!reels_c8!tw-how-to_hktext-2")
        self.assertEqual(p["convention"], "legacy")
        self.assertEqual(p["fields"][8], "tw-how-to_hktext-2")

    def test_free_text_is_unknown(self):
        self.assertEqual(naming.parse("Static - 方案比較")["convention"], "unknown")
        self.assertIsNone(naming.creative_key("Static - 方案比較"))


class NotionMappingTest(unittest.TestCase):
    def test_v2_to_notion(self):
        name = "c1:hk_c2:261203_c3:promo_c4:video_c5:licensed_c6:recut_c7:Qing_c8:phonespeak-walking_c9:app-testing_c10:tw-en"
        props = naming.to_notion(naming.parse(name), ["Qing", "Hua"])["properties"]
        self.assertEqual(props["Market"], "HK 🇭🇰")
        self.assertEqual(props["date:Production Date:start"], "2026-12-03")
        self.assertEqual(props["Campaign Type"], "Promo")
        self.assertEqual(props["Format"], "Video")
        self.assertEqual(props["Production Type"], "Licensed")
        self.assertEqual(props["Version"], "recut")
        self.assertEqual(props["Creator Name"], ["Qing"])
        self.assertEqual(props["Description"], "phonespeak-walking")
        self.assertEqual(props["Language Pair"], "TW-EN")

    def test_legacy_to_notion(self):
        mapped = naming.to_notion(naming.parse(LEGACY), ["hua"])
        props = mapped["properties"]
        self.assertEqual(props["Format"], "Video")
        self.assertEqual(props["Campaign Type"], "Ongoing")
        self.assertEqual(props["Production Type"], "Creator")
        self.assertEqual(props["Legacy Cate."], "UGC")
        self.assertEqual(props["Creator Name"], ["hua"])      # existing option spelling wins
        self.assertEqual(props["Element"], ["Walking"])
        self.assertEqual(props["Product Feature"], ["Phone Speak"])
        self.assertFalse(mapped["new_creator_option"])
        self.assertNotIn("Description", props)

    def test_legacy_sources(self):
        def pt(name):
            return naming.to_notion(naming.parse(name))["properties"]
        static = pt("c1!Static-HK_c2!image_c3!generic_c4!campaign_c5!ongoing_c6!na_c7!OneCoin_c8!Line")
        self.assertEqual((static["Production Type"], static["Version"], static["Market"]),
                         ("Inhouse", "na", "HK 🇭🇰"))
        self.assertNotIn("Creator Name", static)
        wl = pt("c1!UGC_c2!video_c3!whitelist_c4!problemsolution_c5!ongoing_c6!MIP-x_c7!vlog_c8!y_c9!app-cpr")
        self.assertEqual((wl["Production Type"], wl["Version"]), ("Creator", "whitelist"))
        inf = pt("c1!na_c2!video_c3!influencer_c4!testimonial_c5!ongoing_c6!Kapo_c7!holliestyle_c8!story")
        self.assertEqual((inf["Production Type"], inf["Legacy Cate."]), ("Licensed", "Influencer"))
        ai = pt("c1!UGC_c2!video_c3!ugc_c4!productdemo_c5!ongoing_c6!AI-gen_c7!Outcome_c8!z_c9!web")
        self.assertEqual((ai["Production Type"], ai["Legacy Cate."]), ("Inhouse", "AI-Gen"))
        self.assertNotIn("Creator Name", ai)


class BuildTest(unittest.TestCase):
    def test_build_matches_sheet(self):
        res = naming.build({1: "tw", 2: "261116", 3: "ongoing", 4: "image", 5: "creator",
                            6: "original", 7: "na", 8: "krjp-launch-01-1920x1080"})
        self.assertEqual(res["ad_name"], SHEET_EXAMPLE)
        self.assertEqual(res["file_name"], SHEET_EXAMPLE.replace(":", "!"))

    def test_build_slugs_and_blocks_missing(self):
        res = naming.build({1: "TW", 2: "261116", 3: "Ongoing", 4: "Video", 5: "Inhouse",
                            6: "na", 7: "", 8: "Phone Speak_walking v2"})
        self.assertEqual(res["fields"][8], "phone-speak-walking-v2")
        self.assertEqual(res["fields"][7], "na")
        self.assertIsNotNone(res["ad_name"])
        self.assertIsNone(naming.build({1: "tw", 2: "261116"})["ad_name"])

    def test_from_notion_row_round_trip(self):
        row = {"Market": "TW 🇹🇼", "date:Production Date:start": "2026-11-16",
               "Campaign Type": "Ongoing", "Format": "Video", "Production Type": "Creator",
               "Version": "original", "Creator Name": '["MIP-Jenny"]',
               "Description": "peelfruit-phonespeak-v1", "Language Pair": "TW-EN"}
        built = naming.from_notion(row, note="app-testing")
        self.assertEqual(
            built["ad_name"],
            "c1:tw_c2:261116_c3:ongoing_c4:video_c5:creator_c6:original_c7:mip-jenny"
            "_c8:peelfruit-phonespeak-v1_c9:app-testing_c10:tw-en")
        # the note (c9) does not change which creative it is
        self.assertEqual(naming.row_key(row), naming.creative_key(built["ad_name"]))

    def test_row_with_legacy_description_keys_on_it(self):
        row = {"Description": LEGACY, "Market": "TW 🇹🇼"}
        self.assertIsNone(naming.from_notion(row)["ad_name"])
        self.assertEqual(naming.row_key(row), naming.creative_key(LEGACY.replace(" ", "")))
        self.assertEqual(naming.creative_key(LEGACY.replace("c4!testimonial", "c4!testimonial ")),
                         naming.creative_key(LEGACY))


def _row(url, **kw):
    base = {"url": url, "Item": url, "Production Status": "Plan", "createdTime": "2026-10-01"}
    base.update(kw)
    return base


class AuditTest(unittest.TestCase):
    def test_idea_dupes_keep_most_advanced_then_oldest(self):
        ref = "https://app.notion.com/p/" + "a" * 32
        rows = [_row("u1", Reference=ref, createdTime="2026-10-03"),
                _row("u2", Reference=ref, createdTime="2026-10-01"),
                _row("u3", Reference=ref, **{"Production Status": "Production"}),
                _row("u4", Reference="https://drive.google.com/x")]
        plan = audit.dupes(rows)
        self.assertEqual(plan["idea"][0]["keep"]["url"], "u3")
        self.assertEqual([r["url"] for r in plan["idea"][0]["archive"]], ["u2", "u1"])

    def test_ad_id_dupes_merge_transitively(self):
        a, b, c = "1" * 17, "2" * 17, "3" * 17
        rows = [_row("u1", **{"Ad ID(s)": f"{a},{b}", "Production Status": "Pause", "Spend to date": 10}),
                _row("u2", **{"Ad ID(s)": b + "\n" + c, "Production Status": "On Air"}),
                _row("u3", **{"Ad ID(s)": c, "Production Status": "Archive"}),
                _row("u4", **{"Ad ID(s)": "9" * 17})]
        plan = audit.dupes(rows)
        self.assertEqual(len(plan["ad_id"]), 1)
        g = plan["ad_id"][0]
        self.assertEqual(g["keep"]["url"], "u2")
        self.assertEqual(set(g["keep_ad_ids"].split(",")), {a, b, c})
        self.assertEqual({r["url"] for r in g["archive"]}, {"u1", "u3"})

    def test_backfill_only_fills_empty(self):
        rows = [_row("u1", Description=LEGACY, Format="Image", **{"Creator Name": "[]"})]
        out = audit.backfill(rows, ["Hua"])
        self.assertNotIn("Format", out["updates"][0]["set"])
        self.assertEqual(out["updates"][0]["set"]["Creator Name"], ["Hua"])
        self.assertEqual(out["new_creator_options"], {})

    def test_pauses(self):
        rows = [_row("u1", **{"Production Status": "Pause", "date:Paused date:start": "2026-11-01"}),
                _row("u2", **{"Production Status": "Pause", "date:Paused date:start": "2026-11-15"}),
                _row("u3", **{"Production Status": "Pause"}),
                _row("u4", **{"Production Status": "Pause", "date:Paused date:start": "2026-10-01",
                              "Pause reason": "Fatigue"})]
        out = audit.pauses(rows, dt.date(2026, 11, 19))
        self.assertEqual([r["url"] for r in out["set_reason_other"]], ["u1"])
        self.assertEqual([r["url"] for r in out["still_waiting"]], ["u2"])
        self.assertEqual([r["url"] for r in out["stamp_paused_date_today"]], ["u3"])


if __name__ == "__main__":
    unittest.main()
