#!/usr/bin/env python3
"""Deterministic, weighted metric calculation. Use this instead of doing arithmetic in prose.

Usage:
    python metric_calculation.py FILE --by platform [--by format] [--filter platform=Meta]
                                 [--metrics ctr,cpm,completion_rate] [--sheet NAME] [--csv]

Output per group: summed base metrics, every derivable rate recomputed from the sums (never an
average of row-level ratios), share of total for each base metric, Wilson 95% intervals for
proportion metrics and low-volume flags. Reach sums are flagged as upper bounds.

Library use:  value(df, "ctr", {"platform": "Meta"})  -> float
"""
from __future__ import annotations

import argparse
import math
import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
from mie_common import (DERIVED, METRIC_SYNONYMS, MIN_DENOMINATOR, aggregate, dump, load_tables,  # noqa: E402
                        pick_table, wilson_interval)


def apply_filters(df: pd.DataFrame, filters: dict | None) -> pd.DataFrame:
    if not filters:
        return df
    out = df
    for k, v in filters.items():
        if k not in out.columns:
            raise KeyError(f"Unknown dimension '{k}'")
        vals = v if isinstance(v, (list, tuple, set)) else [v]
        out = out[out[k].astype(str).isin([str(x) for x in vals])]
    return out


def value(df: pd.DataFrame, metric: str, filters: dict | None = None) -> float:
    """Return one metric for a filtered slice, computed from base values."""
    sub = apply_filters(df, filters)
    if sub.empty:
        return math.nan
    agg = aggregate(sub).iloc[0]
    if metric in agg.index:
        return float(agg[metric])
    raise KeyError(f"Metric '{metric}' is not available from the columns present")


def share(df: pd.DataFrame, metric: str, filters: dict, within: dict | None = None) -> float:
    base = apply_filters(df, within)
    num = apply_filters(base, filters)[metric].sum(min_count=1)
    den = base[metric].sum(min_count=1)
    return float(num / den) if den else math.nan


def segment_table(df: pd.DataFrame, by: list[str], metrics: list[str] | None = None) -> pd.DataFrame:
    agg = aggregate(df, by)
    base = [c for c in agg.columns if c in METRIC_SYNONYMS]
    for b in base:
        tot = agg[b].sum(min_count=1)
        agg[f"share_{b}"] = agg[b] / tot if tot else math.nan
    for k in [c for c in agg.columns if c in DERIVED]:
        n, d, _m, _l, kind = DERIVED[k]
        if kind == "proportion":
            ci = [wilson_interval(a, b) for a, b in zip(agg[n], agg[d])]
            agg[f"{k}_ci_low"] = [c[0] for c in ci]
            agg[f"{k}_ci_high"] = [c[1] for c in ci]
        minimum = MIN_DENOMINATOR.get(d, 0)
        if minimum:
            agg[f"{k}_low_volume"] = agg[d] < minimum
    if metrics:
        keep = [c for c in agg.columns if c in base or c == "rows" or c.startswith("share_") or c == "reach_is_summed"
                or any(c == m or c.startswith(m + "_") for m in metrics)]
        agg = agg[keep]
    return agg


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("file")
    ap.add_argument("--by", action="append", default=[])
    ap.add_argument("--filter", action="append", default=[], help="dim=value (repeatable)")
    ap.add_argument("--metrics", help="comma-separated derived metrics to keep")
    ap.add_argument("--sheet")
    ap.add_argument("--csv", action="store_true", help="print CSV instead of JSON")
    a = ap.parse_args(argv)
    tables = pick_table(load_tables(a.file), a.sheet)
    filters = dict(f.split("=", 1) for f in a.filter)
    out = []
    for t in tables:
        df = apply_filters(t.df, filters)
        missing = [b for b in a.by if b not in df.columns]
        if missing:
            out.append({"sheet": t.sheet, "error": f"dimension(s) not in table: {missing}"})
            continue
        res = segment_table(df, a.by, a.metrics.split(",") if a.metrics else None) if a.by else aggregate(df)
        if a.csv:
            print(f"# {t.source} / {t.sheet}")
            print(res.to_csv())
        else:
            out.append({"sheet": t.sheet, "by": a.by, "filters": filters,
                        "rows": res.reset_index().to_dict(orient="records")})
    if not a.csv:
        print(dump(out))
    return 0


if __name__ == "__main__":
    sys.exit(main())
