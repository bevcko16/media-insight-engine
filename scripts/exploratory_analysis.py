#!/usr/bin/env python3
"""Stage B: generate candidate findings deterministically.

Usage:
    python exploratory_analysis.py FILE [--sheet NAME] [--objective awareness|consideration|conversion]
                                   [--primary-kpi completion_rate] [--out candidates.json]

This script does not write insights. It produces *candidates*: numerical patterns worth a
hypothesis, each with the evidence, a materiality score, a noise screen and the specific
alternative explanations that must be checked before anything is said to a client. Patterns
that fail the noise screen are still returned (status "noise") so the evidence report can show
what was examined and dismissed.

Analyses run when the data supports them:
  contribution   share of spend vs share of each outcome per segment (efficiency index)
  rate_gap       leader vs rest on each rate, with a two-proportion screen and Wilson CIs
  divergence     rank disagreement between rates across segments (trade-offs)
  simpson        aggregate ranking reversed inside every stratum of a second dimension
  mix_shift      period-over-period change split into rate effect and mix effect
  trend          weekly CTR / CPM / frequency trajectories per creative or ad set (fatigue screen)
  returns        spend elasticity of outcomes across time within an entity (diminishing returns)
  pacing         planned vs actual delivery
  outlier        robust z-score outliers among adequately sized segments
  scale          high efficiency on low volume
  video_funnel   where in the quartile funnel viewers are lost, per segment
  concentration  how concentrated delivery or outcomes are
"""
from __future__ import annotations

import argparse
import itertools
import math
import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
from mie_common import (DERIVED, METRIC_SYNONYMS, MIN_DENOMINATOR, aggregate, dump, load_tables,  # noqa: E402
                        ols_slope, pick_table, robust_z, spearman, two_proportion_test, wilson_interval)

OUTCOMES = ["impressions", "reach", "clicks", "video_views", "video_completions", "engagements",
            "conversions", "conversion_value", "landing_page_views", "saves"]
SEGMENT_EXCLUDE = {"date", "currency", "week", "month"}
TIME_DIMS = ("week", "month", "period")

OBJECTIVE_KPIS = {
    "awareness": ["cpm", "cost_per_reach_k", "frequency", "completion_rate", "completion_rate_of_impr", "view_rate", "cpcv"],
    "video": ["completion_rate", "completion_rate_of_impr", "cpcv", "view_rate", "cpv", "p100_of_p75"],
    "consideration": ["ctr", "cpc", "engagement_rate", "view_rate", "completion_rate", "save_rate"],
    "conversion": ["cpa", "cvr", "roas", "ctr", "cpc"],
}
LOWER_IS_BETTER = {"cpm", "cpc", "cpv", "cpcv", "cpa", "cost_per_reach_k"}

# Metrics in one family share a mechanism; comparing them with each other says nothing new.
FAMILY = {"cpm": "price", "cost_per_reach_k": "price", "ctr": "click", "cpc": "click", "cvr": "conversion",
          "cpa": "conversion", "roas": "value", "view_rate": "view", "cpv": "view", "completion_rate": "completion",
          "completion_rate_of_impr": "completion", "cpcv": "completion", "p100_of_p75": "completion",
          "p25_retention": "early_retention", "p50_of_p25": "mid_retention", "p75_of_p50": "mid_retention",
          "engagement_rate": "engagement", "save_rate": "engagement", "frequency": "frequency",
          "reach_rate_of_impr": "frequency"}
OUTCOME_KPI = {"impressions": "cpm", "clicks": "ctr", "video_views": "view_rate", "video_completions": "completion_rate",
               "engagements": "engagement_rate", "conversions": "cpa", "conversion_value": "roas",
               "landing_page_views": "ctr", "saves": "save_rate"}

ALT_EXPLANATIONS = {
    "placement": "placement or inventory mix differs between the segments",
    "audience": "audiences differ in size, temperature or targeting breadth",
    "optimisation": "segments optimise toward different events, so the algorithm buys different users",
    "budget": "budget levels differ; small budgets often buy the cheapest pockets of inventory first",
    "timing": "segments ran in different weeks or for different lengths of time",
    "definition": "the metric is defined differently on each platform or format",
    "learning": "one segment spent part of the window in a learning phase",
    "creative": "the creative or message differs, not only the format or platform",
    "format": "format or duration differs between the segments",
    "attribution": "conversion windows and view-through rules differ",
}


class Ctx:
    def __init__(self, df, objective, primary):
        self.df = df
        self.objective = objective
        self.primary = primary
        self.cands: list[dict] = []
        self.n = 0
        self.rates = [k for k in DERIVED if DERIVED[k][0] in df.columns and DERIVED[k][1] in df.columns
                      and k not in ("spend_pacing", "impression_delivery", "reach_delivery", "planned_cpm")]
        self.total = aggregate(df).iloc[0]

    def add(self, analysis, **kw):
        self.n += 1
        c = {"id": f"C{self.n:03d}", "analysis": analysis, "status": kw.pop("status", "candidate")}
        c.update(kw)
        c.setdefault("materiality", 0.0)
        seg = c.get("segment")
        if seg and all(not isinstance(v, (list, tuple)) for v in seg.values()):
            mask = pd.Series(True, index=self.df.index)
            for k, v in seg.items():
                if k in self.df.columns:
                    mask &= self.df[k].astype(str) == str(v)
            c["_rows"] = tuple(self.df.index[mask].tolist())
        c["materiality"] = round(min(1.0, float(c["materiality"])), 3)
        self.cands.append(c)
        return c

    def objective_weight(self, metric):
        metric = OUTCOME_KPI.get(metric, metric)
        if not self.objective:
            return 1.0
        kpis = OBJECTIVE_KPIS.get(self.objective, [])
        if self.primary and metric == self.primary:
            return 1.3
        return 1.15 if metric in kpis else 0.65


def segment_dims(df):
    return [c for c in df.columns if c not in SEGMENT_EXCLUDE and c not in METRIC_SYNONYMS
            and not c.startswith("reported_") and not pd.api.types.is_numeric_dtype(df[c])
            and not pd.api.types.is_datetime64_any_dtype(df[c]) and 2 <= df[c].nunique() <= 40]


REACH_METRICS = {"frequency", "cost_per_reach_k", "reach_rate_of_impr", "reach_delivery"}


def reach_ok(agg, m):
    """Reach-based rates are only valid when each group is one deduplicated reach row."""
    return m not in REACH_METRICS or ("rows" in agg.columns and agg["rows"].max() <= 1)


def _better(metric, a, b):
    return a < b if metric in LOWER_IS_BETTER else a > b


# ---------------------------------------------------------------------------------------------

def contribution(ctx: Ctx, dim):
    if "spend" not in ctx.df.columns:
        return
    agg = aggregate(ctx.df, [dim])
    tot_spend = agg["spend"].sum()
    if not tot_spend:
        return
    for out in [o for o in OUTCOMES if o in agg.columns]:
        if out == "reach":
            continue  # reach shares are not additive
        tot_out = agg[out].sum(min_count=1)
        if not tot_out or math.isnan(tot_out) or tot_out < 2 * MIN_DENOMINATOR.get(out, 0):
            continue  # too little volume for shares to mean anything
        for level, row in agg.iterrows():
            ss, os_ = row["spend"] / tot_spend, row[out] / tot_out if not math.isnan(row[out]) else math.nan
            if math.isnan(os_) or ss < 0.05 or os_ <= 0:
                continue
            idx = os_ / ss
            if idx >= 1.3 or idx <= 0.7:
                ctx.add("contribution", dimension=dim, segment={dim: level}, metric=out,
                        numbers={"spend_share": ss, "outcome_share": os_, "efficiency_index": idx,
                                 "spend": row["spend"], out: row[out]},
                        observation=f"{level} takes {ss:.1%} of spend and delivers {os_:.1%} of {out} (index {idx:.2f}).",
                        materiality=min(1.0, abs(math.log(idx)) * math.sqrt(ss) * 1.5) * ctx.objective_weight(out),
                        checks=[ALT_EXPLANATIONS["optimisation"], ALT_EXPLANATIONS["placement"],
                                "whether the segment was meant to deliver this outcome at all (role in plan)"])


def concentration(ctx: Ctx, dim):
    agg = aggregate(ctx.df, [dim])
    for out in [o for o in ("spend", "impressions", "video_completions", "conversions", "clicks") if o in agg.columns]:
        s = agg[out].dropna()
        if len(s) < 4 or not s.sum() or s.sum() < 2 * MIN_DENOMINATOR.get(out, 0):
            continue
        shares = (s / s.sum()).sort_values(ascending=False)
        hhi = float((shares ** 2).sum())
        top_n = max(1, math.ceil(len(shares) * 0.2))
        top_share = float(shares.iloc[:top_n].sum())
        if top_share >= 0.6:
            ctx.add("concentration", dimension=dim, metric=out,
                    numbers={"levels": len(shares), "top_20pct_levels": top_n, "top_share": top_share, "hhi": hhi,
                             "top_levels": {str(k): float(v) for k, v in shares.iloc[:top_n].items()}},
                    observation=f"The top {top_n} of {len(shares)} {dim} levels account for {top_share:.0%} of {out}.",
                    materiality=min(1.0, (top_share - 0.4) * 1.5),
                    checks=["whether concentration was planned (hero asset, always-on line) or emerged from algorithmic allocation",
                            "whether the long tail had enough budget to exit learning"])


def rate_gaps(ctx: Ctx, dim):
    agg = aggregate(ctx.df, [dim])
    if len(agg) < 2:
        return
    for m in [r for r in ctx.rates if reach_ok(agg, r)]:
        n_col, d_col, mult, _label, kind = DERIVED[m]
        sub = agg[agg[d_col].notna() & agg[m].notna()]
        if len(sub) < 2:
            continue
        minimum = MIN_DENOMINATOR.get(d_col, 0)
        adequate = sub[sub[d_col] >= minimum] if minimum else sub
        if len(adequate) < 2:
            ctx.add("rate_gap", status="insufficient_volume", dimension=dim, metric=m,
                    numbers={"levels_with_adequate_volume": len(adequate), "min_denominator": minimum},
                    observation=f"Too few {dim} levels have {minimum:,}+ {d_col} to compare {m}.", materiality=0)
            continue
        best = adequate[m].idxmin() if m in LOWER_IS_BETTER else adequate[m].idxmax()
        worst = adequate[m].idxmax() if m in LOWER_IS_BETTER else adequate[m].idxmin()
        rest = ctx.df[ctx.df[dim].astype(str) != str(best)]
        rest_agg = aggregate(rest).iloc[0]
        b = adequate.loc[best]
        rel_gap = (b[m] - rest_agg[m]) / rest_agg[m] if rest_agg[m] else math.nan
        stats = {}
        if kind == "proportion":
            stats = two_proportion_test(b[n_col], b[d_col], rest_agg[n_col], rest_agg[d_col])
            stats["ci_best"] = wilson_interval(b[n_col], b[d_col])
            stats["ci_rest"] = wilson_interval(rest_agg[n_col], rest_agg[d_col])
            noisy = not (stats["p_value"] < 0.01) if not math.isnan(stats.get("p_value", math.nan)) else True
        else:
            # cost metrics: no sampling model; treat small relative gaps as immaterial
            noisy = False
        material = abs(rel_gap) >= 0.10 if not math.isnan(rel_gap) else False
        status = "candidate" if (material and not noisy) else ("noise" if noisy else "immaterial")
        spend_share = (b["spend"] / ctx.total["spend"]) if "spend" in b.index and ctx.total.get("spend") else math.nan
        ctx.add("rate_gap", status=status, dimension=dim, segment={dim: best}, metric=m,
                numbers={"best_level": best, "best_value": b[m], "rest_value": rest_agg[m], "relative_gap": rel_gap,
                         "worst_level": worst, "worst_value": adequate.loc[worst, m],
                         "best_denominator": b[d_col], "spend_share_best": spend_share, **stats},
                observation=f"{best} leads on {m}: {b[m]:.4g} vs {rest_agg[m]:.4g} for the rest ({rel_gap:+.0%}).",
                materiality=(min(1.0, abs(rel_gap)) * (0.5 + 0.5 * (spend_share if not math.isnan(spend_share) else 0.3))
                             * ctx.objective_weight(m)) if status == "candidate" else 0.0,
                checks=[ALT_EXPLANATIONS["placement"], ALT_EXPLANATIONS["audience"], ALT_EXPLANATIONS["budget"],
                        ALT_EXPLANATIONS["definition"] if dim == "platform" else ALT_EXPLANATIONS["creative"]])


def divergence(ctx: Ctx, dim):
    agg = aggregate(ctx.df, [dim])
    if len(agg) < 3:
        return
    rates = [m for m in ctx.rates if agg[m].notna().sum() >= 3 and m not in ("reach_rate_of_impr",) and reach_ok(agg, m)]
    # Use "goodness" direction so a negative rho always means a trade-off
    def good(m):
        return -agg[m] if m in LOWER_IS_BETTER else agg[m]
    redundant = {frozenset(p) for p in [("cpm", "cost_per_reach_k"), ("ctr", "cpc"), ("view_rate", "cpv"),
                                         ("completion_rate", "cpcv"), ("completion_rate_of_impr", "cpcv"),
                                         ("cvr", "cpa"), ("completion_rate", "p100_of_p75"),
                                         ("completion_rate", "completion_rate_of_impr")]}
    def spread(m):
        v = agg[m].dropna()
        return v.std() / v.mean() if len(v) > 1 and v.mean() else 0
    best_by_family = {}
    for a, b in itertools.combinations(rates, 2):
        if frozenset((a, b)) in redundant or FAMILY.get(a) == FAMILY.get(b):
            continue
        if spread(a) < 0.10 or spread(b) < 0.10:
            continue  # rank order among near-identical values is noise
        if (a == "cpm" and b == "cpc") or (a == "cpc" and b == "cpm"):
            continue
        rho = spearman(good(a).tolist(), good(b).tolist())
        if math.isnan(rho):
            continue
        lead_a = good(a).idxmax()
        lead_b = good(b).idxmax()
        if rho <= -0.4 or (lead_a != lead_b and rho < 0.2):
            fam = frozenset((FAMILY.get(a, a), FAMILY.get(b, b)))
            prev = best_by_family.get(fam)
            if prev is not None and prev <= rho:
                continue
            best_by_family[fam] = rho
            ctx.add("divergence", dimension=dim, metrics=[a, b],
                    numbers={"spearman_rho": rho, "levels": len(agg), "leader_" + a: lead_a, "leader_" + b: lead_b,
                             a: agg[a].to_dict(), b: agg[b].to_dict()},
                    observation=f"Across {dim}, {a} and {b} disagree (rho {rho:+.2f}); {lead_a} leads {a}, {lead_b} leads {b}.",
                    materiality=min(1.0, (abs(rho) if rho < 0 else 0.3) * 0.8 + 0.2) * max(ctx.objective_weight(a), ctx.objective_weight(b)),
                    checks=["whether the two metrics measure different jobs (attention vs action) for these segments",
                            ALT_EXPLANATIONS["placement"], "whether n is large enough: rank correlation on few segments is fragile"])


def simpson(ctx: Ctx, a_dim, b_dim):
    df = ctx.df
    for m in [r for r in ctx.rates if DERIVED[r][4] in ("proportion", "cost")]:
        n_col, d_col = DERIVED[m][0], DERIVED[m][1]
        agg_a = aggregate(df, [a_dim])
        if agg_a[m].notna().sum() < 2:
            continue
        levels = agg_a[m].dropna().index.tolist()
        for x, y in itertools.combinations(levels, 2):
            overall_x_better = _better(m, agg_a.loc[x, m], agg_a.loc[y, m])
            strata = aggregate(df, [b_dim, a_dim])[[m, d_col]].reset_index()
            wins, comps = 0, 0
            detail = {}
            for s, g in strata.groupby(b_dim):
                gx, gy = g[g[a_dim] == x], g[g[a_dim] == y]
                if gx.empty or gy.empty or gx[m].isna().all() or gy[m].isna().all():
                    continue
                mn = MIN_DENOMINATOR.get(d_col, 0)
                if gx[d_col].iloc[0] < mn / 4 or gy[d_col].iloc[0] < mn / 4:
                    continue
                comps += 1
                xb = _better(m, gx[m].iloc[0], gy[m].iloc[0])
                wins += int(xb == overall_x_better)
                detail[str(s)] = {str(x): float(gx[m].iloc[0]), str(y): float(gy[m].iloc[0])}
            if comps >= 2 and wins == 0:
                mix = (df.groupby([a_dim, b_dim])[d_col].sum() / df.groupby(a_dim)[d_col].sum()).unstack().loc[[x, y]]
                ctx.add("simpson", dimension=a_dim, stratified_by=b_dim, metric=m, segment={a_dim: [x, y]},
                        numbers={"aggregate": {str(x): float(agg_a.loc[x, m]), str(y): float(agg_a.loc[y, m])},
                                 "within_strata": detail, "mix_of_" + d_col: mix.round(4).to_dict(orient="index")},
                        observation=(f"In aggregate {x if overall_x_better else y} looks better on {m}, but "
                                     f"{y if overall_x_better else x} is better within every {b_dim} ({comps} strata). "
                                     f"The aggregate gap comes from a different {b_dim} mix."),
                        materiality=0.9 * ctx.objective_weight(m),
                        checks=[f"whether the {b_dim} mix was a planning choice or algorithmic", "volume within each stratum"])


def mix_shift(ctx: Ctx, period_dim, seg_dim):
    df = ctx.df
    periods = sorted(df[period_dim].dropna().astype(str).unique())
    if len(periods) != 2:
        return
    p0, p1 = periods
    for m in [r for r in ctx.rates if DERIVED[r][4] == "proportion" or r in ("cpm", "cpc", "cpa", "cpcv", "cpv")]:
        n_col, d_col, mult = DERIVED[m][0], DERIVED[m][1], DERIVED[m][2]
        g = df.groupby([period_dim, seg_dim])[[n_col, d_col]].sum(min_count=1).reset_index()
        g[period_dim] = g[period_dim].astype(str)
        w = {}
        r = {}
        for p in (p0, p1):
            gp = g[g[period_dim] == p].set_index(seg_dim)
            w[p] = gp[d_col] / gp[d_col].sum()
            r[p] = gp[n_col] / gp[d_col] * mult
        segs = sorted(set(w[p0].index) & set(w[p1].index))
        if len(segs) < 2:
            continue
        R0 = (g[g[period_dim] == p0][n_col].sum() / g[g[period_dim] == p0][d_col].sum()) * mult
        R1 = (g[g[period_dim] == p1][n_col].sum() / g[g[period_dim] == p1][d_col].sum()) * mult
        mix_eff = sum((w[p1][s] - w[p0][s]) * r[p0][s] for s in segs)
        rate_eff = sum(w[p1][s] * (r[p1][s] - r[p0][s]) for s in segs)
        total = R1 - R0
        if not R0 or abs(total / R0) < 0.05:
            continue
        unexplained = total - mix_eff - rate_eff  # segments present in only one period
        mix_share = mix_eff / total if total else math.nan
        ctx.add("mix_shift", dimension=seg_dim, period_dim=period_dim, metric=m,
                numbers={"from": p0, "to": p1, "value_from": R0, "value_to": R1, "change": total, "relative_change": total / R0,
                         "mix_effect": mix_eff, "rate_effect": rate_eff, "new_or_dropped_segments_effect": unexplained,
                         "mix_share_of_change": mix_share,
                         "weights": {s: [float(w[p0][s]), float(w[p1][s])] for s in segs},
                         "segment_rates": {s: [float(r[p0][s]), float(r[p1][s])] for s in segs}},
                observation=(f"{m} moved {total / R0:+.0%} from {p0} to {p1}; {mix_share:.0%} of that movement is "
                             f"explained by a change in {seg_dim} mix rather than performance within {seg_dim}s."),
                materiality=min(1.0, abs(total / R0) * 3) * (1.3 if abs(mix_share) >= 0.5 else 0.8) * ctx.objective_weight(m),
                checks=["why delivery mix changed (budget moves, bid strategy, inventory availability)", "seasonality between periods"])


def _time_col(df):
    if "week" in df.columns:
        return "week"
    if "date" in df.columns and df["date"].notna().any():
        return "_week"
    return None


def trend(ctx: Ctx):
    df = ctx.df.copy()
    tc = _time_col(df)
    if not tc:
        return
    if tc == "_week":
        df["_week"] = df["date"].dt.to_period("W-SUN").dt.start_time
    ent = next((d for d in ("ad", "ad_set", "campaign", "platform") if d in df.columns and df[d].nunique() >= 1), None)
    if not ent:
        return
    for level, g in df.groupby(ent):
        w = aggregate(g, [tc]).sort_index()
        # drop partial edge weeks with under 3 days when built from dates
        if tc == "_week":
            days = g.groupby("_week")["date"].nunique()
            w = w[days.reindex(w.index).fillna(7) >= 5]
        if len(w) < 4:
            continue
        x = list(range(len(w)))
        res = {"weeks": len(w)}
        for m in ("ctr", "cpm", "completion_rate", "frequency", "engagement_rate", "cpa"):
            if m in w.columns and w[m].notna().sum() >= 4:
                mean = w[m].mean()
                slope, r2 = ols_slope(x, w[m].tolist())
                res[m] = {"first": float(w[m].iloc[0]), "last": float(w[m].iloc[-1]),
                          "weekly_slope_rel": slope / mean if mean else math.nan, "r2": r2}
        if "ctr" not in res:
            continue
        ctr_t = res["ctr"]
        decline = ctr_t["weekly_slope_rel"] <= -0.05 and (ctr_t["r2"] or 0) >= 0.6
        if not decline:
            continue
        freq_evidence = "frequency" in res and res["frequency"]["weekly_slope_rel"] > 0.03
        cpm_rise = "cpm" in res and res["cpm"]["weekly_slope_rel"] > 0.05 and (res["cpm"]["r2"] or 0) >= 0.5
        share_trend = None
        if tc in w.columns or True:
            tot_w = aggregate(df, [tc])["impressions"] if "impressions" in df.columns else None
            if tot_w is not None:
                s = (w["impressions"] / tot_w.reindex(w.index)).tolist()
                share_trend = ols_slope(x, s)[0]
        evidence = {
            "ctr_declining": True,
            "frequency_available": "frequency" in res,
            "frequency_rising": bool(freq_evidence) if "frequency" in res else None,
            "cpm_rising_alongside": bool(cpm_rise),
            "delivery_share_slope": share_trend,
        }
        if evidence["frequency_available"] and freq_evidence:
            verdict = "fatigue_plausible"
        elif evidence["frequency_available"] and not freq_evidence:
            verdict = "fatigue_unlikely_frequency_flat"
        else:
            verdict = "fatigue_unverifiable_no_frequency"
        ctx.add("trend", dimension=ent, segment={ent: level}, metric="ctr",
                numbers={**res, "fatigue_evidence": evidence, "fatigue_verdict": verdict},
                observation=(f"{level}: CTR fell from {ctr_t['first']:.3%} to {ctr_t['last']:.3%} over {len(w)} weeks "
                             f"({ctr_t['weekly_slope_rel']:+.0%} per week)."),
                materiality=min(1.0, abs(ctr_t["weekly_slope_rel"]) * 4) * ctx.objective_weight("ctr"),
                checks=["frequency trajectory for the same audience", "placement or audience mix change over the weeks",
                        "CPM movement (auction pressure lowers CTR via cheaper or different inventory)",
                        "whether a new creative was introduced into the same ad set", "seasonality or end-of-flight effects"])


def returns(ctx: Ctx):
    df = ctx.df.copy()
    tc = _time_col(df)
    if not tc or "spend" not in df.columns:
        return
    if tc == "_week":
        df["_week"] = df["date"].dt.to_period("W-SUN").dt.start_time
    ent_dims = [d for d in ("platform", "campaign", "ad_set") if d in df.columns]
    ent = ent_dims[0] if ent_dims else None
    groups = df.groupby(ent) if ent else [("all", df)]
    for out in [o for o in ("conversions", "clicks", "video_completions", "impressions") if o in df.columns]:
        for level, g in groups:
            w = aggregate(g, [tc])
            w = w[(w["spend"] > 0) & (w[out] > 0)]
            if len(w) < 5:
                continue
            spend_cv = w["spend"].std() / w["spend"].mean()
            if spend_cv < 0.25:
                continue  # spend barely varied; elasticity unidentifiable
            ls = [math.log(v) for v in w["spend"]]
            lo = [math.log(v) for v in w[out]]
            slope, r2 = ols_slope(ls, lo)
            if math.isnan(slope):
                continue
            ws = w.sort_values("spend")
            half = len(ws) // 2
            low, high = ws.iloc[:half], ws.iloc[-half:]
            avg_cost_low = low["spend"].sum() / low[out].sum()
            marginal = ((high["spend"].sum() - low["spend"].sum()) / (high[out].sum() - low[out].sum())
                        if high[out].sum() != low[out].sum() else math.nan)
            status = "candidate" if slope < 0.8 and (r2 or 0) >= 0.5 else "immaterial"
            ctx.add("returns", status=status, dimension=ent or "all", segment={ent: level} if ent else {}, metric=out,
                    numbers={"elasticity": slope, "r2": r2, "periods": len(w), "spend_cv": spend_cv,
                             "avg_cost_low_spend_periods": avg_cost_low, "marginal_cost_high_vs_low": marginal},
                    observation=(f"{level}: a 10% rise in weekly spend went with roughly {slope * 10:.1f}% more {out} "
                                 f"(elasticity {slope:.2f}, R² {r2:.2f}); marginal cost {marginal:.4g} vs {avg_cost_low:.4g} average in low-spend weeks."),
                    materiality=(min(1.0, (1 - slope)) * 0.9 * ctx.objective_weight(out)) if status == "candidate" else 0,
                    checks=["whether higher-spend weeks coincided with seasonality or a different audience/placement",
                            "reverse causality: budgets raised because demand was already rising",
                            "few observations: elasticity from a handful of weeks is directional only"])


def pacing(ctx: Ctx):
    df = ctx.df
    pairs = [(a, p) for a, p in (("spend", "planned_spend"), ("impressions", "planned_impressions"), ("reach", "planned_reach"))
             if a in df.columns and p in df.columns]
    if not pairs:
        return
    dims = [d for d in ("platform", "campaign", "ad_set", "market") if d in df.columns]
    for a, p in pairs:
        for dim in dims[:2] or [None]:
            agg = aggregate(df, [dim]) if dim else aggregate(df)
            for level, row in agg.iterrows():
                if not row[p] or math.isnan(row[p]):
                    continue
                ratio = row[a] / row[p]
                if abs(ratio - 1) >= 0.10:
                    ctx.add("pacing", dimension=dim, segment={dim: level} if dim else {}, metric=a,
                            numbers={"actual": row[a], "planned": row[p], "delivery_ratio": ratio,
                                     "cpm_actual": row.get("cpm"), "reach_is_summed": bool(row.get("reach_is_summed", False))},
                            observation=f"{level if dim else 'Total'} delivered {ratio:.0%} of planned {a}.",
                            materiality=min(1.0, abs(ratio - 1) * 1.5),
                            checks=["whether the plan was revised in flight", "whether spend under-delivery came from price (CPM) or from volume",
                                    "flight dates: a late start reads as under-delivery"])
    # Price vs volume decomposition of impression shortfall
    if {"spend", "planned_spend", "impressions", "planned_impressions"} <= set(df.columns):
        for dim in dims[:1]:
            agg = aggregate(df, [dim])
            for level, row in agg.iterrows():
                if not row["planned_impressions"] or not row["planned_spend"]:
                    continue
                plan_cpm = row["planned_spend"] / row["planned_impressions"] * 1000
                act_cpm = row["spend"] / row["impressions"] * 1000 if row["impressions"] else math.nan
                imp_ratio = row["impressions"] / row["planned_impressions"]
                spend_ratio = row["spend"] / row["planned_spend"]
                price_ratio = plan_cpm / act_cpm if act_cpm else math.nan
                if abs(imp_ratio - 1) >= 0.10:
                    ctx.add("pacing", dimension=dim, segment={dim: level}, metric="impressions_vs_plan_decomposed",
                            numbers={"impression_delivery": imp_ratio, "spend_delivery": spend_ratio,
                                     "planned_cpm": plan_cpm, "actual_cpm": act_cpm, "price_factor": price_ratio,
                                     "check_product": spend_ratio * price_ratio},
                            observation=(f"{level}: impressions at {imp_ratio:.0%} of plan = spend at {spend_ratio:.0%} of plan "
                                         f"x CPM effect {price_ratio:.2f} (planned CPM {plan_cpm:.2f}, actual {act_cpm:.2f})."),
                            materiality=min(1.0, abs(imp_ratio - 1) * 1.8),
                            checks=["whether planned CPMs were realistic for the market and period", "inventory competition in the period"])


def outliers(ctx: Ctx, dim):
    agg = aggregate(ctx.df, [dim])
    if len(agg) < 6:
        return
    for m in [r for r in ctx.rates if reach_ok(agg, r)]:
        d_col = DERIVED[m][1]
        sub = agg[agg[d_col] >= MIN_DENOMINATOR.get(d_col, 0)][m].dropna()
        if len(sub) < 6:
            continue
        z = robust_z(sub)
        for level, zv in z.items():
            if abs(zv) >= 3.5:
                ctx.add("outlier", dimension=dim, segment={dim: level}, metric=m,
                        numbers={"value": float(sub[level]), "median": float(sub.median()), "robust_z": float(zv)},
                        observation=f"{level} is an outlier on {m}: {sub[level]:.4g} vs median {sub.median():.4g} (robust z {zv:+.1f}).",
                        materiality=min(1.0, abs(zv) / 8),
                        checks=["tracking or definition error on that row", "a placement or audience the others did not use",
                                "very short flight or tiny budget"])


def scale(ctx: Ctx, dim):
    agg = aggregate(ctx.df, [dim])
    if "impressions" not in agg.columns or len(agg) < 3:
        return
    tot = agg["impressions"].sum()
    for m in [r for r in ctx.rates if ctx.objective_weight(r) >= 1.0 and reach_ok(agg, r)]:
        d_col = DERIVED[m][1]
        sub = agg[(agg[d_col] >= MIN_DENOMINATOR.get(d_col, 0)) & agg[m].notna()]
        if len(sub) < 3:
            continue
        best = sub[m].idxmin() if m in LOWER_IS_BETTER else sub[m].idxmax()
        share = agg.loc[best, "impressions"] / tot
        median = sub[m].median()
        rel = (sub.loc[best, m] - median) / median if median else math.nan
        if share < 0.10 and abs(rel) >= 0.2:
            ctx.add("scale", dimension=dim, segment={dim: best}, metric=m,
                    numbers={"value": sub.loc[best, m], "median_of_segments": median, "relative_to_median": rel,
                             "impression_share": share, "spend": agg.loc[best].get("spend")},
                    observation=f"{best} has the best {m} ({sub.loc[best, m]:.4g}, {rel:+.0%} vs median) on only {share:.1%} of impressions.",
                    materiality=min(1.0, abs(rel)) * 0.7 * ctx.objective_weight(m),
                    checks=["whether efficiency holds at higher spend (small budgets buy the cheapest, most responsive users first)",
                            "whether the segment's audience pool is large enough to scale", "learning-phase status"])


def video_funnel(ctx: Ctx, dim):
    need = ["video_p25", "video_p50", "video_p75", "video_completions"]
    if not all(c in ctx.df.columns for c in need):
        return
    agg = aggregate(ctx.df, [dim])
    steps = [s for s in ("p25_retention", "p50_of_p25", "p75_of_p50", "p100_of_p75") if s in agg.columns]
    if len(agg) < 2:
        return
    table = agg[steps].to_dict(orient="index")
    worst_step = {str(k): min(steps, key=lambda s: v[s] if not math.isnan(v[s]) else 9) for k, v in table.items()}
    distinct = len(set(worst_step.values()))
    ctx.add("video_funnel", dimension=dim, metric="quartile_retention",
            numbers={"retention_by_step": table, "largest_drop_step": worst_step,
                     "completion_rate": agg["completion_rate"].to_dict() if "completion_rate" in agg.columns else None},
            observation=f"Quartile retention by {dim}; the step losing the most viewers differs across levels ({distinct} distinct)."
            if distinct > 1 else f"Quartile retention by {dim}; every level loses most viewers at the same step ({list(worst_step.values())[0]}).",
            materiality=0.5 * ctx.objective_weight("completion_rate") if distinct > 1 else 0.25,
            checks=["asset length differences (a 6s and a 30s asset are not comparable on completion)",
                    "auto-play vs user-initiated starts by placement", "how each platform defines a start"])


def dedupe(cands):
    """Within one analysis/dimension/segment keep the strongest candidate per metric family."""
    keep, seen = [], {}
    def prio(c):
        ms = c.get("metrics") or [c.get("metric")]
        prop = any(m in DERIVED and DERIVED[m][4] == "proportion" for m in ms if m)
        return -c["materiality"] * (1.3 if prop else 1.0)
    for c in sorted(cands, key=prio):
        if c["status"] != "candidate":
            keep.append(c)
            continue
        metrics = c.get("metrics") or [c.get("metric")]
        fam = tuple(sorted(FAMILY.get(m, m) for m in metrics if m))
        where = c.get("_rows") or (c.get("dimension"), json_key(c.get("segment")))
        key = (c["analysis"], c.get("stratified_by"), where, fam)
        if key in seen:
            seen[key].setdefault("same_family_variants", []).append(c["id"])
            continue
        seen[key] = c
        keep.append(c)
    return keep


def json_key(o):
    import json
    return json.dumps(o, sort_keys=True, default=str)


def run(df: pd.DataFrame, objective=None, primary=None) -> dict:
    guards = []
    if "currency" in df.columns and df["currency"].nunique() > 1:
        drop = [c for c in ("spend", "planned_spend", "conversion_value") if c in df.columns]
        df = df.drop(columns=drop)
        guards.append(f"Mixed currencies {sorted(df['currency'].dropna().unique().tolist())}: spend-based metrics suppressed until converted.")
    ctx = Ctx(df, objective, primary)
    dims = segment_dims(df)
    for d in dims:
        if d in TIME_DIMS:
            continue
        contribution(ctx, d)
        concentration(ctx, d)
        rate_gaps(ctx, d)
        divergence(ctx, d)
        outliers(ctx, d)
        scale(ctx, d)
        video_funnel(ctx, d)
    non_time = [d for d in dims if d not in TIME_DIMS]
    for a, b in itertools.permutations(non_time, 2):
        simpson(ctx, a, b)
    for pd_ in [d for d in ("period",) if d in df.columns]:
        for seg in non_time:
            mix_shift(ctx, pd_, seg)
    trend(ctx)
    returns(ctx)
    pacing(ctx)
    ranked = sorted(dedupe(ctx.cands), key=lambda c: (c["status"] != "candidate", -c["materiality"]))
    for c in ranked:
        c.pop("_rows", None)
    return {
        "objective": objective, "primary_kpi": primary,
        "segment_dimensions": dims, "rates_available": ctx.rates,
        "totals": ctx.total.to_dict(),
        "counts": {s: sum(1 for c in ranked if c["status"] == s) for s in {c["status"] for c in ranked}},
        "guards": guards,
        "candidates": ranked,
        "note": ("Candidates are patterns, not insights. Each must pass hypothesis testing and critical review "
                 "(references/critical-review.md) before it can appear in client output."),
    }


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("file")
    ap.add_argument("--sheet")
    ap.add_argument("--objective", choices=sorted(OBJECTIVE_KPIS))
    ap.add_argument("--primary-kpi")
    ap.add_argument("--out")
    ap.add_argument("--top", type=int, default=0, help="only print the top N candidates")
    a = ap.parse_args(argv)
    tables = pick_table(load_tables(a.file), a.sheet)
    results = []
    for t in tables:
        r = run(t.df, a.objective, a.primary_kpi)
        r["sheet"] = t.sheet
        if a.top:
            r["candidates"] = r["candidates"][:a.top]
        results.append(r)
    print(dump(results, a.out))
    return 0


if __name__ == "__main__":
    sys.exit(main())
