#!/usr/bin/env python3
"""Stage D gate: verify every number, lint the writing and apply the rubric with hard gates.

Usage:
    python evidence_validation.py DATA_FILE INSIGHTS.json [--sheet NAME] [--out report.json]

INSIGHTS.json schema (see references/critical-review.md for how to fill it):
{
  "language": "en-GB" | "tr",
  "insights": [{
     "id": "I1",
     "text": "client-facing paragraph",
     "tier": "confirmed" | "supported" | "hypothesis" | "question",
     "claims": [
        {"metric": "ctr", "filters": {"platform": "Meta"}, "value": 0.0124},
        {"type": "share", "metric": "spend", "filters": {"platform": "Meta"}, "within": {}, "value": 0.41},
        {"type": "ratio", "metric": "ctr", "a": {"format": "6s"}, "b": {"format": "30s"}, "value": 1.32},
        {"type": "rel_diff", "metric": "cpm", "metric_b": "planned_cpm", "a": {...}, "b": {...}, "value": 0.36},
        {"type": "diff", "metric": "cpm", "a": {...}, "b": {...}, "value": -1.2},
        {"type": "external", "source": "client brief p.3", "value": 0.02}     # not recomputable; must cite a source
     ],
     "causal_evidence": "optional: the test or design that supports a causal reading",
     "scores": {"evidence": 0-5, "strategic": 0-5, "depth": 0-5, "objective_fit": 0-5, "decision": 0-5, "writing": 0-5},
     "candidate_ids": ["C004"], "alternatives_considered": ["..."]
  }]
}

Exit code 0 when the file was processed (accepted or not); 2 on schema errors.
"""
from __future__ import annotations

import argparse
import json
import math
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from mie_common import dump, load_tables, pick_table  # noqa: E402
from metric_calculation import apply_filters, share, value  # noqa: E402

WEIGHTS = {"evidence": 25, "strategic": 25, "depth": 20, "objective_fit": 15, "decision": 10, "writing": 5}
THRESHOLD = 80
DEFAULT_TOLERANCE = 0.005  # 0.5% relative: claim values must be the unrounded figure

BANNED_PHRASES = [
    r"this highlights the importance of", r"this underscores", r"underscores the need", r"in today'?s .*landscape",
    r"this demonstrates the power of", r"moving forward,? it is essential", r"these results showcase",
    r"it is worth noting that", r"it'?s important to note", r"a testament to", r"game[- ]changer", r"leverag(e|ing) the power",
    r"unlock(ing)? (the )?(full )?potential", r"\bsynerg(y|ies)\b", r"in conclusion", r"delve", r"\bholistic\b",
    r"paving the way", r"at the end of the day", r"needle[- ]moving", r"robust performance", r"\bseamless(ly)?\b",
    r"strong performance", r"performed (very )?well", r"impressive (results|performance)",
]
BANNED_TR = [r"önemini vurgul", r"altını çiz", r"günümüzün rekabetçi", r"gücünü göster", r"ileriye dönük olarak .* kritik"]
HYPE = r"\b(strong|impressive|excellent|outstanding|remarkable|successful|efficient|great|fantastic|stellar|solid)\b"
CAUSAL = (r"\b(because|caused|causes|drove|drives|driven by|due to|led to|leads to|resulted in|results in|thanks to|"
          r"as a result of|attributable to|was responsible for|is responsible for|triggered|made (users|people|audiences))\b")
HEDGES = r"\b(may|might|could|suggests?|indicates?|likely|possibly|appears?|seems?|consistent with|points? to|hypothes)"
RELATIONAL = (r"\b(than|while|whereas|despite|although|relative|compared|versus|vs\.?|but|only|yet|rather|"
              r"against|ahead of|behind|outpaced|lagged|share|index|for every|per|mix|trade-?off|not reflected|diverge|"
              r"oran|karşın|rağmen|göre|ise|kıyasla)\b")
PSYCHOLOGY = r"\b(attention spans?|consumers (want|prefer|love|feel)|people (prefer|want|love)|audiences? (loved|felt|wanted)|emotional(ly)? (resonat|connect)|resonated)\b"
STATS_WORDS = r"\b(statistically|significan|consistent with chance|by chance|within (the )?noise|confidence interval|intervals? overlap|overlap heavily|too small to call)"
VAGUE = r"\b(roughly|almost|nearly|around|approximately|about half|near-flat|close to|the bulk of|most of|majority of)\b"
US_SPELLING = {"optimize": "optimise", "optimization": "optimisation", "analyze": "analyse", "behavior": "behaviour",
               "color": "colour", "center": "centre", "favorite": "favourite", "prioritize": "prioritise",
               "utilize": "use", "program ": "programme ", "labeled": "labelled", "modeling": "modelling"}

NUM_RE = re.compile(r"(?<![\w.])([£$€₺]?)(\d{1,3}(?:,\d{3})+|\d+(?:\.\d+)?)\s*(%|pp|x|×|k|m|bn|million|billion|thousand|milyon|milyar|bin)?(?![\w])", re.I)


def compute_claim(df, c):
    t = c.get("type", "value")
    m = c.get("metric")
    if t == "value":
        return value(df, m, c.get("filters"))
    if t == "share":
        return share(df, m, c.get("filters", {}), c.get("within"))
    if t in ("ratio", "diff", "rel_diff"):
        a, b = value(df, m, c["a"]), value(df, c.get("metric_b", m), c["b"])
        if t == "ratio":
            return a / b if b else math.nan
        if t == "diff":
            return a - b
        return (a - b) / b if b else math.nan
    if t == "count":
        return float(len(apply_filters(df, c.get("filters"))))
    raise ValueError(f"unknown claim type {t}")


def numbers_in_text(text, lang="en-GB"):
    if lang == "tr":
        # Turkish: 1.234.567 thousands, 1,24 decimal, %1,24 percent prefix
        text = re.sub(r"(?<=\d)\.(?=\d{3}(?!\d))", "", text)
        text = re.sub(r"(?<=\d),(?=\d)", ".", text)
        text = re.sub(r"%\s?(\d+(?:\.\d+)?)", r"\1%", text)
    # durations and asset labels ("30-second film", "6s bumper", "15 sec") are names, not claims
    text = re.sub(r"\b\d+(\.\d+)?\s?(-|\s)?(seconds?|secs?|s)\b", " ", text, flags=re.I)
    out = []
    for cur, num, unit in NUM_RE.findall(text):
        try:
            v = float(num.replace(",", ""))
        except ValueError:
            continue
        unit = (unit or "").lower()
        scale = {"k": 1e3, "thousand": 1e3, "bin": 1e3, "m": 1e6, "million": 1e6, "milyon": 1e6,
                 "bn": 1e9, "billion": 1e9, "milyar": 1e9}.get(unit, 1.0)
        v *= scale
        decimals = len(num.split(".")[1]) if "." in num else 0
        out.append((v, unit if scale == 1.0 else "", cur, (decimals, scale)))
    return out


def number_backed(v, unit, claim_values, decimals=None):
    """A displayed number is backed when some claim, in some natural presentation (fraction, percent,
    ratio, percentage change), rounds to exactly the displayed figure at the displayed precision."""
    candidates = []
    for cv in claim_values:
        if cv is None or (isinstance(cv, float) and math.isnan(cv)):
            continue
        candidates += [cv, cv * 100, abs(cv), abs(cv) * 100, (cv - 1) * 100 if unit == "%" else cv, abs(cv - 1) * 100]
    dec, scale = decimals if isinstance(decimals, tuple) else (decimals or 0, 1.0)
    half = 0.5 * 10 ** (-dec) * scale + 1e-9
    for cand in candidates:
        if abs(v - cand) <= half:
            return True
        if decimals is None and cand and abs(v - cand) / abs(cand) <= 0.01:
            return True
    return False


def lint(ins, lang):
    text = ins.get("text", "")
    low = text.lower()
    issues = []
    if "—" in text or " – " in text or " -- " in text:
        issues.append(("hard", "em_dash", "Uses an em/en dash as punctuation."))
    for p in BANNED_PHRASES + (BANNED_TR if lang == "tr" else []):
        if re.search(p, low):
            issues.append(("soft", "banned_phrase", f"Generic filler: /{p}/"))
    if re.search(PSYCHOLOGY, low):
        issues.append(("hard", "unsupported_psychology", "Claims about consumer psychology that campaign data cannot establish."))
    causal = re.findall(CAUSAL, low)
    tier = ins.get("tier")
    if causal and not ins.get("causal_evidence"):
        if tier in ("confirmed", "supported"):
            issues.append(("hard", "unsupported_causality",
                           f"Causal wording {sorted(set(causal))} in a {tier} insight with no causal_evidence."))
        elif not re.search(HEDGES, low):
            issues.append(("hard", "unhedged_causality", "Causal wording without hedging in a hypothesis."))
    if tier == "hypothesis" and not re.search(HEDGES, low):
        issues.append(("soft", "hypothesis_not_hedged", "Hypothesis tier but the text reads as established fact."))
    if re.search(STATS_WORDS, low) and not ins.get("statistical_evidence"):
        issues.append(("soft", "statistical_wording_unchecked",
                       "Statistical wording (significance, chance, noise, intervals) with no statistical_evidence field; "
                       "check it against the rate_gap screen."))
    vague = re.findall(VAGUE, low)
    if vague:
        issues.append(("soft", "approximate_wording",
                       f"Approximate wording {sorted(set(vague))} is not checked by the script; confirm each against a computed figure."))
    hype = re.findall(HYPE, low)
    if len(hype) >= 2:
        issues.append(("soft", "adjective_padding", f"Evaluative adjectives doing the work: {hype}."))
    if len(re.findall(RELATIONAL, low)) == 0 or len(ins.get("claims", [])) < 2:
        issues.append(("hard", "restates_table",
                       "Reads as a single observation: fewer than two evidenced quantities or no relationship between them."))
    if lang != "tr":
        for us, uk in US_SPELLING.items():
            if re.search(r"\b" + us, low):
                issues.append(("soft", "us_spelling", f"'{us.strip()}' -> '{uk.strip()}' (British English)."))
    words = len(text.split())
    if words > 140:
        issues.append(("soft", "too_long", f"{words} words; client paragraphs should rarely exceed ~110."))
    if words < 25:
        issues.append(("soft", "too_short", f"{words} words; likely an observation without interpretation."))
    sentences = [s for s in re.split(r"(?<=[.!?])\s+", text) if s]
    if sentences and max(len(s.split()) for s in sentences) > 45:
        issues.append(("soft", "long_sentence", "A sentence exceeds 45 words."))
    return issues


def calibration_issues(scores):
    """Rubric calibration: 80+ needs no dimension below 3 and a 5 in evidence, strategic or depth."""
    if not scores:
        return []
    out = []
    low = [k for k in WEIGHTS if scores.get(k) is not None and scores[k] < 3]
    if low:
        out.append(("hard", "dimension_below_3", f"Dimensions scored below 3: {low}."))
    if not any(scores.get(k) == 5 for k in ("evidence", "strategic", "depth")):
        out.append(("soft", "no_standout_dimension",
                    "No 5 in evidence, strategic or depth; per the rubric this is unlikely to be an 80+ insight."))
    return out


def rubric(scores):
    if not scores:
        return None
    total = 0.0
    for k, w in WEIGHTS.items():
        s = scores.get(k)
        if s is None:
            return None
        total += w * max(0, min(5, float(s))) / 5
    return round(total, 1)


def similarity(a, b):
    def keyset(i):
        return {(c.get("type", "value"), c.get("metric"), json.dumps(c.get("filters", c.get("a", {})), sort_keys=True))
                for c in i.get("claims", [])}
    ka, kb = keyset(a), keyset(b)
    claim_j = len(ka & kb) / len(ka | kb) if ka | kb else 0
    def sh(t):
        w = re.findall(r"\w+", t.lower())
        return {tuple(w[i:i + 3]) for i in range(len(w) - 2)}
    sa, sb = sh(a.get("text", "")), sh(b.get("text", ""))
    text_j = len(sa & sb) / len(sa | sb) if sa | sb else 0
    return max(claim_j, text_j)


def validate(df, payload):
    lang = payload.get("language", "en-GB")
    results = []
    insights = payload.get("insights", [])
    for ins in insights:
        r = {"id": ins.get("id"), "tier": ins.get("tier"), "claims": [], "issues": []}
        claim_values = []
        for c in ins.get("claims", []):
            entry = {"claim": c}
            if c.get("type") == "external":
                entry["status"] = "external_cited" if c.get("source") else "external_uncited"
                if not c.get("source"):
                    r["issues"].append(("hard", "fabrication_risk", "External figure without a source."))
                claim_values.append(c.get("value"))
            else:
                try:
                    actual = compute_claim(df, c)
                except Exception as e:  # noqa: BLE001
                    entry.update(status="error", error=str(e))
                    r["issues"].append(("hard", "claim_not_computable", f"{c}: {e}"))
                    r["claims"].append(entry)
                    continue
                stated = c.get("value")
                tol = c.get("tolerance", DEFAULT_TOLERANCE)
                ok = (stated is not None and not math.isnan(actual)
                      and (abs(stated - actual) <= tol * max(abs(actual), 1e-12) or abs(stated - actual) < 1e-9))
                entry.update(actual=actual, status="verified" if ok else "mismatch")
                if not ok:
                    r["issues"].append(("hard", "incorrect_calculation", f"Stated {stated} but data gives {actual:.6g} for {c}."))
                claim_values.append(actual)
            r["claims"].append(entry)
        for v, unit, _cur, dec in numbers_in_text(ins.get("text", ""), lang):
            if 1900 <= v <= 2100 and not unit:
                continue  # years
            if v <= 10 and not unit and float(v).is_integer():
                continue  # small counts like "three platforms"
            if not number_backed(v, unit, claim_values, dec):
                r["issues"].append(("hard", "unbacked_number", f"'{v:g}{unit}' in the text matches no verified claim."))
        r["issues"] += lint(ins, lang)
        r["issues"] += calibration_issues(ins.get("scores"))
        if ins.get("assumptions"):
            r["assumptions"] = ins["assumptions"]
        score = rubric(ins.get("scores"))
        r["score"] = score
        hard = [i for i in r["issues"] if i[0] == "hard"]
        if hard:
            r["decision"] = "reject"
            r["reason"] = "hard gate: " + ", ".join(sorted({i[1] for i in hard}))
        elif score is None:
            r["decision"] = "needs_scores"
        elif score < THRESHOLD:
            r["decision"] = "reject"
            r["reason"] = f"score {score} below {THRESHOLD}"
        else:
            r["decision"] = "accept"
        r["issues"] = [{"gate": g, "code": c, "message": m} for g, c, m in r["issues"]]
        results.append(r)
    # Collective checks
    accepted = [i for i, r in zip(insights, results) if r["decision"] == "accept"]
    overlaps = []
    for i in range(len(accepted)):
        for j in range(i + 1, len(accepted)):
            s = similarity(accepted[i], accepted[j])
            if s >= 0.5:
                overlaps.append({"a": accepted[i]["id"], "b": accepted[j]["id"], "similarity": round(s, 2)})
    openings = {}
    for ins in insights:
        key = " ".join(re.findall(r"\w+", ins.get("text", "").lower())[:3])
        openings.setdefault(key, []).append(ins.get("id"))
    repeated = {k: v for k, v in openings.items() if len(v) > 1 and k}
    structure = [ins.get("id") for ins in insights if re.search(r"\b(we recommend|recommend(ed)? that|should consider)\b", ins.get("text", "").lower())]
    acc_scores = [r["score"] for r in results if r["decision"] == "accept" and r["score"] is not None]
    saturation = (len(acc_scores) >= 2 and min(acc_scores) >= 85)
    collective = {
        "score_saturation": ("Every accepted insight scored 85 or more. Re-score against the calibration notes; "
                             "the set is probably being flattered." if saturation else None),
        "overlapping_accepted": overlaps,
        "repeated_openings": repeated,
        "insights_ending_in_recommendation": structure,
        "warning": ("Every insight closes with a recommendation; vary structure." if insights and len(structure) == len(insights) and len(insights) > 2 else None),
    }
    return {"results": results, "collective": collective,
            "summary": {"accepted": sum(r["decision"] == "accept" for r in results),
                        "rejected": sum(r["decision"] == "reject" for r in results),
                        "needs_scores": sum(r["decision"] == "needs_scores" for r in results)}}


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("data")
    ap.add_argument("insights")
    ap.add_argument("--sheet")
    ap.add_argument("--out", help="write the full report here and print only a summary")
    a = ap.parse_args(argv)
    tables = pick_table(load_tables(a.data), a.sheet)
    if len(tables) > 1 and not a.sheet:
        print(dump({"error": f"Data has several tables {[t.sheet for t in tables]}; pass --sheet."}))
        return 2
    try:
        payload = json.loads(Path(a.insights).read_text(encoding="utf-8"))
    except json.JSONDecodeError as e:
        print(dump({"error": f"Invalid insights JSON: {e}"}))
        return 2
    report = validate(tables[0].df, payload)
    if a.out:
        dump(report, a.out)
        brief = {"summary": report["summary"],
                 "decisions": [{"id": r["id"], "decision": r["decision"], "score": r["score"], "reason": r.get("reason"),
                                "soft_issues": [i["code"] for i in r["issues"] if i["gate"] == "soft"]} for r in report["results"]],
                 "collective": {k: v for k, v in report["collective"].items() if v}, "full_report": a.out}
        print(dump(brief))
    else:
        print(dump(report))
    return 0


if __name__ == "__main__":
    sys.exit(main())
