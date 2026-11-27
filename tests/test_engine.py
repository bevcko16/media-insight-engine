#!/usr/bin/env python3
"""Deterministic test suite. Run:  python3 -m unittest discover -s tests -v

Covers: parsing, weighted arithmetic, Stage A validation on adversarial files, Stage B detection of
every planted pattern, absence of findings where none exist, and the Stage D evidence gate.
"""
from __future__ import annotations

import json
import math
import subprocess
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "tests" / "data"
sys.path.insert(0, str(ROOT / "scripts"))

from mie_common import aggregate, load_tables, parse_number, two_proportion_test, wilson_interval  # noqa: E402
import data_validation as dv  # noqa: E402
import exploratory_analysis as ea  # noqa: E402
import evidence_validation as evv  # noqa: E402
from metric_calculation import value  # noqa: E402


def setUpModule():
    subprocess.run([sys.executable, str(ROOT / "tests" / "generate_datasets.py")], check=True, capture_output=True)


def table(name, sheet=None):
    ts = load_tables(DATA / name)
    return next(t for t in ts if sheet is None or t.sheet == sheet)


def cands(name, objective=None, status="candidate"):
    r = ea.run(table(name).df, objective)
    return [c for c in r["candidates"] if status is None or c["status"] == status]


class TestParsing(unittest.TestCase):
    def test_numbers(self):
        self.assertEqual(parse_number("£12,400.00"), (12400.0, False))
        self.assertEqual(parse_number("1.234,56"), (1234.56, False))
        self.assertEqual(parse_number("1,5"), (1.5, False))
        self.assertEqual(parse_number("1.24%"), (1.24, True))
        self.assertEqual(parse_number("(300)"), (-300.0, False))
        self.assertTrue(math.isnan(parse_number("-")[0]))
        self.assertTrue(math.isnan(parse_number("n/a")[0]))
        self.assertEqual(parse_number("0"), (0.0, False))  # zero is not missing

    def test_header_detection_and_total_rows(self):
        t = table("s11_inconsistent_definitions.xlsx", "Summary")
        self.assertEqual(t.header_row, 3)
        self.assertEqual(len(t.df), 4)
        self.assertEqual(len(t.total_rows), 1)

    def test_weighted_not_averaged(self):
        df = table("s08_simpson.csv").df
        weighted = value(df, "ctr", {"platform": "Meta"})
        rows = df[df.platform == "Meta"]
        naive = (rows.clicks / rows.impressions).mean()
        self.assertAlmostEqual(weighted, (4_250_000 * 0.009 + 750_000 * 0.003) / 5_000_000, places=5)
        self.assertGreater(abs(weighted - naive), 0.001)

    def test_missing_stays_missing(self):
        t = table("s11_inconsistent_definitions.xlsx", "Summary")
        agg = aggregate(t.df[t.df.platform == "Pinterest"]).iloc[0]
        self.assertTrue(math.isnan(agg["impressions"]))
        self.assertTrue(math.isnan(agg["ctr"]))

    def test_reach_sum_flagged(self):
        agg = aggregate(table("s07_creative_fatigue.csv").df, ["ad"])
        self.assertTrue(agg["reach_is_summed"].all())

    def test_stats(self):
        lo, hi = wilson_interval(50, 1000)
        self.assertTrue(lo < 0.05 < hi)
        self.assertLess(two_proportion_test(120, 10000, 80, 10000)["p_value"], 0.01)
        self.assertGreater(two_proportion_test(51, 1000, 49, 1000)["p_value"], 0.5)


class TestValidation(unittest.TestCase):
    def codes(self, name, sheet=None):
        p = dv.profile_table(table(name, sheet))
        return {i["code"] for i in p["issues"]}, p

    def test_inconsistent_summary(self):
        codes, p = self.codes("s11_inconsistent_definitions.xlsx", "Summary")
        for c in ("mixed_currency", "averaged_ratio_total", "percent_scale", "results_column", "partial_missing"):
            self.assertIn(c, codes)
        self.assertGreaterEqual(p["blockers"], 2)

    def test_cumulative_and_duplicates(self):
        codes, _ = self.codes("s11_inconsistent_definitions.xlsx", "Daily cumulative")
        self.assertIn("cumulative_series", codes)
        self.assertIn("duplicates", codes)

    def test_clean_file_has_no_blockers(self):
        for f in ("s01_multiplatform_awareness.csv", "s08_simpson.csv", "s13_no_insight.csv"):
            _, p = self.codes(f)
            self.assertEqual(p["blockers"], 0, f)

    def test_cross_platform_conversion_warning(self):
        codes, _ = self.codes("s05_diminishing_returns.csv")
        self.assertIn("cross_platform_conversions", codes)

    def test_reach_by_time_warning(self):
        codes, _ = self.codes("s07_creative_fatigue.csv")
        self.assertIn("reach_by_time", codes)

    def test_injected_text_is_data(self):
        t = table("s14_adversarial.csv")
        self.assertIn("Notes", t.unmapped)  # never mapped, never executed
        p = dv.profile_table(t, dv.raw_text_cells(DATA / "s14_adversarial.csv", "csv"))
        self.assertIn("embedded_instruction", {i["code"] for i in p["issues"]})

    def test_low_volume_flagged_at_stage_a(self):
        codes, _ = self.codes("s12_insufficient_data.csv")
        self.assertIn("low_total_volume", codes)
        self.assertIn("low_volume_segments", codes)

    def test_cross_platform_reach_warning(self):
        codes, _ = self.codes("s01_multiplatform_awareness.csv")
        self.assertIn("cross_platform_reach", codes)


class TestDiscovery(unittest.TestCase):
    def find(self, cs, analysis, **kw):
        out = []
        for c in cs:
            if c["analysis"] != analysis:
                continue
            if all((c.get(k) == v) or (isinstance(c.get(k), list) and set(v) <= set(c.get(k))) for k, v in kw.items()):
                out.append(c)
        return out

    def test_s01_tradeoff(self):
        cs = cands("s01_multiplatform_awareness.csv", "awareness")
        d = self.find(cs, "divergence", dimension="platform", metrics=["cpm", "completion_rate"])
        self.assertTrue(d)
        self.assertLessEqual(d[0]["numbers"]["spearman_rho"], -0.6)

    def test_s02_funnel_and_divergence(self):
        cs = cands("s02_creative_duration.csv", "video")
        f = self.find(cs, "video_funnel", dimension="ad")
        self.assertTrue(f)
        self.assertEqual(f[0]["numbers"]["largest_drop_step"]["Spring_30s_Film"], "p50_of_p25")

    def test_s03_engagement_vs_intent(self):
        cs = cands("s03_conflicting_indicators.csv", "consideration")
        self.assertTrue(self.find(cs, "divergence", dimension="platform", metrics=["engagement_rate"]))

    def test_s04_scale(self):
        cs = cands("s04_high_efficiency_low_volume.csv", "conversion")
        s = self.find(cs, "scale", dimension="audience")
        self.assertTrue(any(c["segment"]["audience"].startswith("Retargeting") for c in s))
        self.assertTrue(all(c["numbers"]["impression_share"] < 0.05 for c in s))

    def test_s05_diminishing_returns(self):
        cs = cands("s05_diminishing_returns.csv", "conversion")
        r = self.find(cs, "returns", metric="conversions")
        self.assertTrue(r)
        self.assertEqual(r[0]["segment"], {"platform": "Meta"})
        self.assertTrue(0.4 < r[0]["numbers"]["elasticity"] < 0.7)
        # Google spend was flat: must not produce an elasticity claim
        allc = cands("s05_diminishing_returns.csv", "conversion", status=None)
        self.assertFalse([c for c in allc if c["analysis"] == "returns" and c.get("segment") == {"platform": "Google Ads"}])

    def test_s06_price_vs_volume(self):
        cs = cands("s06_plan_vs_actual.csv", "awareness")
        dec = {c["segment"]["platform"]: c["numbers"] for c in self.find(cs, "pacing", metric="impressions_vs_plan_decomposed")}
        self.assertLess(dec["YouTube"]["price_factor"], 0.8)
        self.assertGreater(dec["YouTube"]["spend_delivery"], 0.95)
        self.assertGreater(dec["TikTok"]["price_factor"], 0.95)
        self.assertLess(dec["TikTok"]["spend_delivery"], 0.75)

    def test_s07_fatigue_discrimination(self):
        cs = cands("s07_creative_fatigue.csv", "consideration")
        verdicts = {c["segment"]["ad"]: c["numbers"]["fatigue_verdict"] for c in self.find(cs, "trend")}
        self.assertEqual(verdicts.get("Autumn_Hero_A"), "fatigue_plausible")
        self.assertEqual(verdicts.get("Autumn_Product_B"), "fatigue_unlikely_frequency_flat")
        self.assertNotIn("Autumn_Lifestyle_C", verdicts)

    def test_s08_simpson(self):
        cs = cands("s08_simpson.csv")
        s = self.find(cs, "simpson", dimension="platform", stratified_by="placement", metric="ctr")
        self.assertTrue(s)
        self.assertEqual(cs[0]["analysis"], "simpson")  # ranked first

    def test_s09_mix(self):
        cs = cands("s09_mix_shift.csv")
        m = self.find(cs, "mix_shift", metric="ctr")
        self.assertTrue(m)
        self.assertGreater(m[0]["numbers"]["mix_share_of_change"], 0.9)

    def test_s11_currency_guard(self):
        r = ea.run(table("s11_inconsistent_definitions.xlsx", "Summary").df)
        self.assertTrue(r["guards"])
        self.assertFalse([c for c in r["candidates"] if c.get("metric") in ("cpm", "cpc", "cpa")])

    def test_s12_insufficient(self):
        self.assertEqual(cands("s12_insufficient_data.csv"), [])
        allc = cands("s12_insufficient_data.csv", status=None)
        self.assertTrue(all(c["status"] == "insufficient_volume" for c in allc))

    def test_s13_no_insight(self):
        self.assertEqual(cands("s13_no_insight.csv", "consideration"), [])

    def test_s14_confound_found(self):
        cs = cands("s14_adversarial.csv")
        self.assertTrue(self.find(cs, "simpson", dimension="ad", stratified_by="placement", metric="ctr"))


class TestEvidenceGate(unittest.TestCase):
    df = None

    @classmethod
    def setUpClass(cls):
        cls.df = table("s08_simpson.csv").df

    def run_one(self, ins):
        return evv.validate(self.df, {"language": "en-GB", "insights": [ins]})["results"][0]

    GOOD_SCORES = {"evidence": 5, "strategic": 4, "depth": 4, "objective_fit": 4, "decision": 4, "writing": 4}

    def test_good_insight_accepted(self):
        r = self.run_one({
            "id": "G1", "tier": "confirmed", "scores": self.GOOD_SCORES,
            "text": ("Meta's aggregate CTR of 0.81% sits well ahead of TikTok's 0.49%, yet TikTok is ahead inside both placements "
                     "it shares with Meta. The gap reflects where each platform's impressions were bought: 85% of Meta's delivery "
                     "ran in Feed against 20% of TikTok's, so platform-level CTR here is a reading of placement mix rather than of "
                     "platform quality."),
            "claims": [{"metric": "ctr", "filters": {"platform": "Meta"}, "value": 0.0081},
                       {"metric": "ctr", "filters": {"platform": "TikTok"}, "value": 0.00488},
                       {"type": "share", "metric": "impressions", "filters": {"placement": "Feed"}, "within": {"platform": "Meta"}, "value": 0.85},
                       {"type": "share", "metric": "impressions", "filters": {"placement": "Feed"}, "within": {"platform": "TikTok"}, "value": 0.20}]})
        self.assertEqual(r["decision"], "accept", r)

    def test_observation_rejected(self):
        r = self.run_one({"id": "B1", "tier": "confirmed", "scores": self.GOOD_SCORES,
                          "text": "Meta delivered a strong CTR of 0.81%, an impressive result for the campaign this month overall.",
                          "claims": [{"metric": "ctr", "filters": {"platform": "Meta"}, "value": 0.0081}]})
        self.assertEqual(r["decision"], "reject")
        self.assertIn("restates_table", r["reason"])

    def test_wrong_number_rejected(self):
        r = self.run_one({"id": "B2", "tier": "confirmed", "scores": self.GOOD_SCORES,
                          "text": "Meta's CTR of 0.95% was ahead of TikTok's 0.49%, while Feed carried most of Meta's delivery against a minority of TikTok's.",
                          "claims": [{"metric": "ctr", "filters": {"platform": "Meta"}, "value": 0.0095},
                                     {"metric": "ctr", "filters": {"platform": "TikTok"}, "value": 0.00488}]})
        self.assertIn("incorrect_calculation", r["reason"])

    def test_unbacked_number_rejected(self):
        r = self.run_one({"id": "B3", "tier": "supported", "scores": self.GOOD_SCORES,
                          "text": "Meta's CTR of 0.81% was ahead of TikTok's 0.49%, and the gap is worth roughly 12,000 extra clicks per month versus plan.",
                          "claims": [{"metric": "ctr", "filters": {"platform": "Meta"}, "value": 0.0081},
                                     {"metric": "ctr", "filters": {"platform": "TikTok"}, "value": 0.00488}]})
        self.assertIn("unbacked_number", r["reason"])

    def test_causal_and_psychology_rejected(self):
        r = self.run_one({"id": "B4", "tier": "supported", "scores": self.GOOD_SCORES,
                          "text": ("Meta's CTR of 0.81% beat TikTok's 0.49% because Meta users have longer attention spans, "
                                   "which drove more clicks than the TikTok audience."),
                          "claims": [{"metric": "ctr", "filters": {"platform": "Meta"}, "value": 0.0081},
                                     {"metric": "ctr", "filters": {"platform": "TikTok"}, "value": 0.00488}]})
        self.assertIn("unsupported_causality", r["reason"])
        self.assertIn("unsupported_psychology", r["reason"])

    def test_em_dash_rejected(self):
        r = self.run_one({"id": "B5", "tier": "confirmed", "scores": self.GOOD_SCORES,
                          "text": "Meta's CTR of 0.81% led TikTok's 0.49% — but only because of placement mix, which differed sharply between them.",
                          "claims": [{"metric": "ctr", "filters": {"platform": "Meta"}, "value": 0.0081},
                                     {"metric": "ctr", "filters": {"platform": "TikTok"}, "value": 0.00488}]})
        self.assertIn("em_dash", r["reason"])

    def test_low_score_rejected(self):
        low = {k: 3 for k in self.GOOD_SCORES}
        r = self.run_one({"id": "B6", "tier": "confirmed", "scores": low,
                          "text": "Meta's CTR of 0.81% was ahead of TikTok's 0.49%, although TikTok led within each placement where the two overlapped.",
                          "claims": [{"metric": "ctr", "filters": {"platform": "Meta"}, "value": 0.0081},
                                     {"metric": "ctr", "filters": {"platform": "TikTok"}, "value": 0.00488}]})
        self.assertEqual(r["decision"], "reject")
        self.assertIn("below 80", r["reason"])

    def test_dimension_below_3_rejected(self):
        r = self.run_one({"id": "B7", "tier": "confirmed", "scores": dict(self.GOOD_SCORES, strategic=2),
                          "text": "Meta's CTR of 0.81% was ahead of TikTok's 0.49%, although TikTok led within each placement where the two overlapped.",
                          "claims": [{"metric": "ctr", "filters": {"platform": "Meta"}, "value": 0.0081},
                                     {"metric": "ctr", "filters": {"platform": "TikTok"}, "value": 0.00488}]})
        self.assertIn("dimension_below_3", r["reason"])

    def test_displayed_number_must_round_from_claim(self):
        # 0.804% shown, claim is 0.8025%: rounding 0.8025 to 3 dp gives 0.803 (or 0.802), not 0.804
        r = self.run_one({"id": "B8", "tier": "confirmed", "scores": self.GOOD_SCORES,
                          "text": "Meta's CTR of 0.814% was ahead of TikTok's 0.49%, although TikTok led within each placement where the two overlapped.",
                          "claims": [{"metric": "ctr", "filters": {"platform": "Meta"}, "value": 0.0081},
                                     {"metric": "ctr", "filters": {"platform": "TikTok"}, "value": 0.00488}]})
        self.assertIn("unbacked_number", r["reason"])

    def test_score_saturation_warned(self):
        a = {"id": "A", "tier": "confirmed", "scores": {k: 5 for k in self.GOOD_SCORES},
             "text": "Meta's CTR of 0.81% was ahead of TikTok's 0.49% in aggregate, yet TikTok led inside both placements they shared.",
             "claims": [{"metric": "ctr", "filters": {"platform": "Meta"}, "value": 0.0081},
                        {"metric": "ctr", "filters": {"platform": "TikTok"}, "value": 0.00488}]}
        b = dict(a, id="B", text="Feed carried 85% of Meta's impressions against 20% of TikTok's, while Stories CTR trailed Feed on both platforms.",
                 claims=[{"type": "share", "metric": "impressions", "filters": {"placement": "Feed"}, "within": {"platform": "Meta"}, "value": 0.85},
                         {"type": "share", "metric": "impressions", "filters": {"placement": "Feed"}, "within": {"platform": "TikTok"}, "value": 0.20}])
        res = evv.validate(self.df, {"insights": [a, b]})
        self.assertTrue(res["collective"]["score_saturation"])

    def test_hedged_hypothesis_allowed(self):
        r = self.run_one({"id": "H1", "tier": "hypothesis", "scores": self.GOOD_SCORES,
                          "text": ("TikTok's lead within both placements, 1.00% against 0.90% in Feed, suggests the platform may be "
                                   "under-credited by its aggregate CTR, though two placements are a thin base and a split test would be needed to confirm it."),
                          "claims": [{"metric": "ctr", "filters": {"platform": "TikTok", "placement": "Feed"}, "value": 0.01},
                                     {"metric": "ctr", "filters": {"platform": "Meta", "placement": "Feed"}, "value": 0.009}]})
        self.assertEqual(r["decision"], "accept", r)

    def test_collective_overlap(self):
        a = {"id": "A", "tier": "confirmed", "scores": self.GOOD_SCORES,
             "text": "Meta's CTR of 0.81% was ahead of TikTok's 0.49% in aggregate, yet TikTok led inside both placements they shared.",
             "claims": [{"metric": "ctr", "filters": {"platform": "Meta"}, "value": 0.0081},
                        {"metric": "ctr", "filters": {"platform": "TikTok"}, "value": 0.00488}]}
        b = dict(a, id="B")
        res = evv.validate(self.df, {"insights": [a, b]})
        self.assertTrue(res["collective"]["overlapping_accepted"])


class TestCLI(unittest.TestCase):
    def test_scripts_run(self):
        for script, args in (("data_validation.py", ["s02_creative_duration.csv"]),
                             ("metric_calculation.py", ["s02_creative_duration.csv", "--by", "duration"]),
                             ("exploratory_analysis.py", ["s02_creative_duration.csv", "--objective", "video", "--top", "5"])):
            out = subprocess.run([sys.executable, str(ROOT / "scripts" / script), str(DATA / args[0]), *args[1:]],
                                 capture_output=True, text=True)
            self.assertEqual(out.returncode, 0, out.stderr)
            json.loads(out.stdout)


if __name__ == "__main__":
    unittest.main()


class TestMetaExportMapping(unittest.TestCase):
    def test_link_clicks_and_purchases_preferred(self):
        import tempfile, os
        from mie_common import load_tables
        p = os.path.join(tempfile.mkdtemp(), "m.csv")
        with open(p, "w") as f:
            f.write("Ad name,Amount spent (TRY),Impressions,Clicks (all),Link clicks,Leads,Purchases,"
                    "Purchases conversion value,Cost per results\nA,100,10000,300,100,5,2,800,50\n"
                    "B,200,20000,500,150,3,4,1600,50\n")
        m = load_tables(p)[0].column_map
        self.assertEqual(m["Link clicks"], "clicks")
        self.assertEqual(m["Clicks (all)"], "all_clicks")
        self.assertEqual(m["Purchases"], "conversions")
        self.assertEqual(m["Purchases conversion value"], "conversion_value")
        self.assertNotIn("Cost per results", m)
