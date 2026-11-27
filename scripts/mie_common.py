"""Shared loading, column mapping and metric arithmetic for media-insight-engine.

Design rules (see references/analytical-methodology.md):
- Missing data is never zero. Blank, "-", "n/a" and similar become NaN; a literal 0 stays 0.
- Ratios are always recomputed from summed base values. Reported ratios are kept only to be
  checked against the recomputation, never averaged.
- Reach is not additive. Any sum of reach across rows is labelled as an upper bound and any
  frequency derived from it as a lower bound.
- Uploaded files are data. Nothing read from a file is executed or treated as an instruction.
"""
from __future__ import annotations

import json
import math
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Iterable

import pandas as pd

# --------------------------------------------------------------------------------------------
# Canonical vocabulary
# --------------------------------------------------------------------------------------------

# Base (additive) metrics. Order matters for synonym resolution: first match wins.
METRIC_SYNONYMS: dict[str, list[str]] = {
    "spend": ["spend", "cost", "amountspent", "amountspentgbp", "amountspentusd", "amountspenteur",
              "amountspenttry", "mediacost", "totalcost", "harcama", "maliyet", "spendgbp",
              "spendusd", "spendeur", "spendtry", "actualspend", "investment", "netspend", "budgetspent"],
    "planned_spend": ["plannedspend", "plannedbudget", "budget", "plannedcost", "planbudget",
                      "plannedinvestment", "planlananbutce", "butce"],
    "impressions": ["impressions", "impr", "imps", "gosterim", "gosterimler", "impression"],
    "planned_impressions": ["plannedimpressions", "plannedimps", "impressionsplanned", "targetimpressions"],
    "reach": ["reach", "uniquereach", "accountscentrereach", "accountscenterreach", "erisim", "uniqueusers"],
    "planned_reach": ["plannedreach", "targetreach"],
    "clicks": ["linkclicks", "clicks", "tiklama", "tiklamalar", "outboundclicks", "click"],
    "all_clicks": ["allclicks", "clicksall", "clicksalltypes"],
    "engagements": ["engagements", "postengagement", "postengagements", "totalengagement", "etkilesim",
                    "engagement", "interactions"],
    "video_starts": ["videostarts", "videoplays", "plays", "videoviewsstarts", "videoplay"],
    "video_views": ["videoviews", "views", "videoview", "thruplays", "thruplay", "trueview", "trueviewviews",
                    "6secondviews", "focusedview", "focusedviews", "2secondvideoviews", "3secondvideoviews",
                    "goruntuleme", "izlenme"],
    "video_p25": ["videop25", "p25", "videoplayedto25", "videoviewsat25", "25viewed", "videowatched25",
                  "videoplaysat25", "quartile1", "firstquartile"],
    "video_p50": ["videop50", "p50", "videoplayedto50", "videoviewsat50", "50viewed", "videowatched50",
                  "videoplaysat50", "midpoint", "quartile2"],
    "video_p75": ["videop75", "p75", "videoplayedto75", "videoviewsat75", "75viewed", "videowatched75",
                  "videoplaysat75", "thirdquartile", "quartile3"],
    "video_completions": ["videocompletions", "completions", "videop100", "p100", "videoplayedto100",
                          "videoviewsat100", "100viewed", "videowatched100", "completedviews",
                          "videoplaysat100", "completeviews"],
    "conversions": ["purchases", "conversions", "results", "leads", "donusum", "donusumler", "sales",
                    "acquisitions", "signups", "actions"],
    "conversion_value": ["purchasesconversionvalue", "purchaseconversionvalue", "conversionvalue", "revenue", "purchasevalue", "sales value", "salesvalue",
                         "gelir", "ciro", "convvalue", "totalconversionvalue"],
    "landing_page_views": ["landingpageviews", "lpv", "sessions"],
    "saves": ["saves", "pinsaves", "kaydetme"],
}

# Rates as they may appear in reports. Kept only for cross-checking.
REPORTED_RATE_SYNONYMS: dict[str, list[str]] = {
    "ctr": ["ctr", "clickthroughrate", "linkctr", "ctrlink", "ctrall", "tiklamaorani"],
    "cpm": ["cpm", "costperthousand", "cpmcostper1000impressions", "ecpm"],
    "cpc": ["cpc", "costperclick", "cpclink", "avgcpc", "averagecpc"],
    "cpv": ["cpv", "costperview", "avgcpv", "averagecpv"],
    "vtr": ["vtr", "viewthroughrate", "completionrate", "videocompletionrate", "vcr", "viewrate"],
    "frequency": ["frequency", "freq", "siklik", "frekans"],
    "cpa": ["cpa", "costperresult", "costperconversion", "cpl", "costperlead", "costperacquisition"],
    "roas": ["roas", "returnonadspend", "purchaseroas"],
    "engagement_rate": ["engagementrate", "er", "etkilesimorani"],
}

DIMENSION_SYNONYMS: dict[str, list[str]] = {
    "date": ["date", "day", "reportingstarts", "reportingdate", "tarih", "gun"],
    "week": ["week", "weekstarting", "weekcommencing", "wc", "hafta", "isoweek"],
    "month": ["month", "ay"],
    "period": ["period", "reportingperiod", "donem", "phase", "flight", "wave"],
    "platform": ["platform", "channel", "network", "publisher", "source", "kanal", "mecra", "media"],
    "campaign": ["campaign", "campaignname", "kampanya", "kampanyaadi"],
    "ad_set": ["adset", "adsetname", "adgroup", "adgroupname", "lineitem", "insertionorder", "adsquad",
               "reklamseti", "adgroups"],
    "ad": ["ad", "adname", "creative", "creativename", "asset", "assetname", "reklam", "kreatif", "pin",
           "pinname", "video", "videoname"],
    "format": ["format", "adformat", "creativeformat", "creativetype", "adtype", "mediatype", "type"],
    "duration": ["duration", "length", "videolength", "videoduration", "assetlength", "sure", "seconds"],
    "placement": ["placement", "position", "placementname", "yerlesim", "inventory", "surface"],
    "audience": ["audience", "audiencename", "segment", "targeting", "kitle", "hedefkitle", "audiencetype"],
    "objective": ["objective", "campaignobjective", "buyingtype", "goal", "amac", "hedef"],
    "market": ["market", "country", "region", "geo", "pazar", "ulke"],
    "device": ["device", "devicetype", "cihaz"],
    "age": ["age", "agegroup", "yas"],
    "gender": ["gender", "cinsiyet"],
    "currency": ["currency", "parabirimi", "curr"],
    "buying_model": ["buyingmodel", "buymodel", "costmodel", "bidstrategy", "bidtype"],
}

TOTAL_ROW_PATTERN = re.compile(r"^\s*(grand\s+)?(total|totals|sum|toplam|genel toplam|all)\s*$", re.I)
MISSING_TOKENS = {"", "-", "--", "—", "n/a", "na", "nan", "none", "null", "#n/a", "#div/0!", "#value!",
                  "not available", "unavailable", "yok", "?"}


def norm_name(name: object) -> str:
    s = str(name).strip().lower()
    s = (s.replace("ı", "i").replace("ş", "s").replace("ğ", "g").replace("ü", "u").replace("ö", "o")
          .replace("ç", "c").replace("%", "").replace("(", " ").replace(")", " "))
    return re.sub(r"[^a-z0-9]", "", s)


def _lookup(normed: str, table: dict[str, list[str]]) -> str | None:
    for canon, syns in table.items():
        if normed in {norm_name(x) for x in syns}:
            return canon
    return None


# --------------------------------------------------------------------------------------------
# Number parsing
# --------------------------------------------------------------------------------------------

def parse_number(value: object) -> tuple[float, bool]:
    """Return (number or NaN, was_percent). Handles currency symbols, thousands separators,
    European decimal commas and percent signs. NaN means unavailable, not zero."""
    if value is None:
        return math.nan, False
    if isinstance(value, bool):
        return float(value), False
    if isinstance(value, (int, float)):
        return (float(value) if not (isinstance(value, float) and math.isnan(value)) else math.nan), False
    s = str(value).strip()
    if s.lower() in MISSING_TOKENS:
        return math.nan, False
    pct = s.endswith("%")
    s = re.sub(r"[£$€₺¥\s%]|GBP|USD|EUR|TRY|TL", "", s, flags=re.I)
    neg = s.startswith("(") and s.endswith(")")
    s = s.strip("()")
    if "," in s and "." in s:
        if s.rfind(",") > s.rfind("."):
            s = s.replace(".", "").replace(",", ".")
        else:
            s = s.replace(",", "")
    elif "," in s:
        parts = s.split(",")
        # 1,234 or 1,234,567 -> thousands; 1,5 -> decimal comma
        if all(len(p) == 3 for p in parts[1:]) and len(parts[0]) <= 3:
            s = s.replace(",", "")
        else:
            s = s.replace(",", ".")
    try:
        x = float(s)
    except ValueError:
        return math.nan, False
    return (-x if neg else x), pct


# --------------------------------------------------------------------------------------------
# Loading
# --------------------------------------------------------------------------------------------

@dataclass
class Table:
    source: str               # file name
    sheet: str                # sheet name or "csv"
    header_row: int           # 1-based row in the source where the header sits
    df: pd.DataFrame          # canonical columns, numeric metrics parsed
    column_map: dict          # original header -> canonical name
    unmapped: list            # original headers we could not map
    total_rows: pd.DataFrame  # rows that look like totals, removed from df
    percent_columns: list = field(default_factory=list)
    notes: list = field(default_factory=list)

    @property
    def dimensions(self) -> list[str]:
        return [c for c in self.df.columns if c in DIMENSION_SYNONYMS and c != "currency"]

    @property
    def metrics(self) -> list[str]:
        return [c for c in self.df.columns if c in METRIC_SYNONYMS]

    @property
    def reported_rates(self) -> list[str]:
        return [c for c in self.df.columns if c.startswith("reported_")]


def _syn_rank(h: object, canon: str) -> int:
    n = norm_name(h)
    syns = METRIC_SYNONYMS.get(canon, [])
    return syns.index(n) if n in syns else len(syns)


def classify_header(h: object) -> tuple[str | None, str | None]:
    """Return (kind, canonical) where kind is metric|rate|dimension or None."""
    n = norm_name(h)
    if not n:
        return None, None
    for kind, table in (("metric", METRIC_SYNONYMS), ("rate", REPORTED_RATE_SYNONYMS),
                        ("dimension", DIMENSION_SYNONYMS)):
        c = _lookup(n, table)
        if c:
            return kind, c
    # loose contains-matching for long platform export headers, metrics first
    loose = [("video_completions", ["100"]), ("video_p75", ["75"]), ("video_p50", ["50"]),
             ("video_p25", ["25"])]
    if "video" in n or "watched" in n or "played" in n or "play" in n:
        for canon, keys in loose:
            if any(k in n for k in keys):
                return "metric", canon
    if n.startswith("amountspent") or n.startswith("spend") or (n.startswith("cost") and not n.startswith("costper")):
        return "metric", "spend"
    return None, None


def _detect_header_row(raw: pd.DataFrame, max_scan: int = 15) -> int:
    best, best_score = 0, -1
    for i in range(min(max_scan, len(raw))):
        row = raw.iloc[i].tolist()
        score = sum(1 for v in row if isinstance(v, str) and classify_header(v)[0])
        if score > best_score:
            best, best_score = i, score
    return best


def _tableify(raw: pd.DataFrame, source: str, sheet: str) -> Table | None:
    raw = raw.dropna(how="all").dropna(axis=1, how="all")
    if raw.empty or raw.shape[1] < 2:
        return None
    original_rows = raw.index.tolist()
    raw = raw.reset_index(drop=True)
    h = _detect_header_row(raw)
    headers = [str(x).strip() if not (isinstance(x, float) and math.isnan(x)) else f"unnamed_{j}"
               for j, x in enumerate(raw.iloc[h].tolist())]
    body = raw.iloc[h + 1:].reset_index(drop=True)
    body.columns = headers
    column_map, unmapped, out, pct_cols, notes = {}, [], {}, [], []
    seen: dict[str, str] = {}
    for col in headers:
        kind, canon = classify_header(col)
        if kind is None:
            unmapped.append(col)
            continue
        target = f"reported_{canon}" if kind == "rate" else canon
        if target in seen and kind == "metric" and _syn_rank(col, canon) < _syn_rank(seen[target], canon):
            notes.append(f"Columns '{seen[target]}' and '{col}' both map to '{target}'; kept '{col}' "
                         f"(preferred synonym). Check whether they measure the same thing.")
            unmapped.append(seen[target])
            column_map.pop(seen[target], None)
            seen.pop(target)
        if target in seen:
            notes.append(f"Columns '{seen[target]}' and '{col}' both map to '{target}'; kept the first. "
                         f"Check whether they measure the same thing (for example link vs all clicks).")
            unmapped.append(col)
            continue
        seen[target] = col
        column_map[col] = target
        series = body[col]
        if kind == "dimension":
            out[target] = series.map(lambda v: None if (v is None or (isinstance(v, float) and math.isnan(v))
                                                       or str(v).strip().lower() in MISSING_TOKENS)
                                     else (v if target in ("date",) else str(v).strip()))
        else:
            parsed = [parse_number(v) for v in series.tolist()]
            vals = [p[0] for p in parsed]
            if any(p[1] for p in parsed):
                pct_cols.append(target)
                vals = [v / 100.0 if not math.isnan(v) else v for v in vals]
            out[target] = pd.Series(vals, dtype="float64")
    if not any(k in METRIC_SYNONYMS for k in out):
        return None
    df = pd.DataFrame(out)
    if "date" in df.columns:
        df["date"] = pd.to_datetime(df["date"], errors="coerce", dayfirst=_looks_dayfirst(df["date"]))
    # Separate total rows
    dim_cols = [c for c in df.columns if c in DIMENSION_SYNONYMS and c != "date"]
    is_total = pd.Series(False, index=df.index)
    for c in dim_cols:
        is_total |= df[c].astype(str).str.match(TOTAL_ROW_PATTERN)
    if dim_cols:
        all_dims_blank = df[dim_cols].isna().all(axis=1)
        metric_cols = [c for c in df.columns if c in METRIC_SYNONYMS]
        has_metrics = df[metric_cols].notna().any(axis=1)
        # A trailing row with metrics but no labels is usually a total
        trailing = all_dims_blank & has_metrics & (df.index == df.index.max())
        is_total |= trailing
    totals = df[is_total].copy()
    df = df[~is_total].reset_index(drop=True)
    metric_cols = [c for c in df.columns if c in METRIC_SYNONYMS or c.startswith("reported_")]
    df = df[df[metric_cols].notna().any(axis=1)].reset_index(drop=True)
    return Table(source=source, sheet=sheet, header_row=int(original_rows[h]) + 1, df=df, column_map=column_map,
                 unmapped=unmapped, total_rows=totals, percent_columns=pct_cols, notes=notes)


def _looks_dayfirst(series: pd.Series) -> bool:
    for v in series.dropna().astype(str).head(50):
        m = re.match(r"^(\d{1,2})[/.](\d{1,2})[/.]\d{2,4}", v)
        if m and int(m.group(1)) > 12:
            return True
    return True if any(re.match(r"^\d{1,2}\.\d{1,2}\.\d{4}", v) for v in series.dropna().astype(str).head(5)) else False


def _split_blocks(raw: pd.DataFrame, min_blank: int = 1) -> list[pd.DataFrame]:
    """Split a sheet into stacked tables separated by fully blank rows (common in agency summaries)."""
    blank = raw.isna().all(axis=1).tolist()
    blocks, start = [], None
    for i, b in enumerate(blank + [True]):
        if not b and start is None:
            start = i
        elif b and start is not None:
            blocks.append(raw.iloc[start:i])
            start = None
    # merge a title-only block (1 non-empty row with <=2 cells) into the following block
    merged, carry = [], None
    for blk in blocks:
        if carry is not None:
            blk = pd.concat([carry, blk])
            carry = None
        if len(blk) == 1 and blk.notna().sum(axis=1).iloc[0] <= 2:
            carry = blk
            continue
        merged.append(blk)
    return merged


def _block_title(blk: pd.DataFrame) -> str | None:
    first = blk.iloc[0].dropna().tolist()
    if len(first) == 1 and isinstance(first[0], str) and not classify_header(first[0])[0]:
        return first[0].strip()
    return None


def _sheet_tables(raw: pd.DataFrame, source: str, sheet: str) -> list[Table]:
    whole = _tableify(raw, source, sheet)
    blocks = _split_blocks(raw)
    if len(blocks) <= 1:
        return [whole] if whole else []
    out = []
    for blk in blocks:
        title = _block_title(blk)
        t = _tableify(blk, source, f"{sheet} / {title}" if title else f"{sheet} / rows {blk.index[0] + 1}-{blk.index[-1] + 1}")
        if t is not None and len(t.df) >= 1:
            out.append(t)
    # Prefer the split when more than one block carries metrics; otherwise keep the whole sheet
    return out if len(out) > 1 else ([whole] if whole else out)


def load_tables(path: str | Path) -> list[Table]:
    path = Path(path)
    tables: list[Table] = []
    if path.suffix.lower() in (".csv", ".tsv", ".txt"):
        sep = "\t" if path.suffix.lower() == ".tsv" else None
        raw = pd.read_csv(path, header=None, sep=sep, engine="python", dtype=object)
        tables += _sheet_tables(raw, path.name, "csv")
    elif path.suffix.lower() in (".xlsx", ".xlsm", ".xls"):
        sheets = pd.read_excel(path, sheet_name=None, header=None, dtype=object)
        for name, raw in sheets.items():
            tables += _sheet_tables(raw, path.name, str(name))
    else:
        raise ValueError(f"Unsupported file type: {path.suffix}")
    return tables


# --------------------------------------------------------------------------------------------
# Derived metrics (always from base values)
# --------------------------------------------------------------------------------------------

# name: (numerator, denominator, multiplier, label, kind)
DERIVED: dict[str, tuple[str, str, float, str, str]] = {
    "ctr": ("clicks", "impressions", 1.0, "Click-through rate (clicks / impressions)", "proportion"),
    "cpm": ("spend", "impressions", 1000.0, "Cost per thousand impressions", "cost"),
    "cpc": ("spend", "clicks", 1.0, "Cost per click", "cost"),
    "frequency": ("impressions", "reach", 1.0, "Average frequency (impressions / reach)", "ratio"),
    "cost_per_reach_k": ("spend", "reach", 1000.0, "Cost per thousand reached", "cost"),
    "reach_rate_of_impr": ("reach", "impressions", 1.0, "Reach per impression", "ratio"),
    "view_rate": ("video_views", "impressions", 1.0, "Video views / impressions", "proportion"),
    "cpv": ("spend", "video_views", 1.0, "Cost per (platform-defined) video view", "cost"),
    "completion_rate": ("video_completions", "video_starts", 1.0, "Completions / video starts", "proportion"),
    "completion_rate_of_impr": ("video_completions", "impressions", 1.0, "Completions / impressions", "proportion"),
    "cpcv": ("spend", "video_completions", 1.0, "Cost per completed view", "cost"),
    "p25_retention": ("video_p25", "video_starts", 1.0, "Share of starts reaching 25%", "proportion"),
    "p50_of_p25": ("video_p50", "video_p25", 1.0, "Share of 25% viewers reaching 50%", "proportion"),
    "p75_of_p50": ("video_p75", "video_p50", 1.0, "Share of 50% viewers reaching 75%", "proportion"),
    "p100_of_p75": ("video_completions", "video_p75", 1.0, "Share of 75% viewers completing", "proportion"),
    "engagement_rate": ("engagements", "impressions", 1.0, "Engagements / impressions", "proportion"),
    "cvr": ("conversions", "clicks", 1.0, "Conversions / clicks", "proportion"),
    "cpa": ("spend", "conversions", 1.0, "Cost per conversion", "cost"),
    "roas": ("conversion_value", "spend", 1.0, "Conversion value / spend", "ratio"),
    "aov": ("conversion_value", "conversions", 1.0, "Average order value (value / conversions)", "cost"),
    "cost_per_lpv": ("spend", "landing_page_views", 1.0, "Cost per landing page view", "cost"),
    "save_rate": ("saves", "impressions", 1.0, "Saves / impressions", "proportion"),
    "planned_cpm": ("planned_spend", "planned_impressions", 1000.0, "Planned CPM", "cost"),
    "spend_pacing": ("spend", "planned_spend", 1.0, "Actual / planned spend", "ratio"),
    "impression_delivery": ("impressions", "planned_impressions", 1.0, "Actual / planned impressions", "ratio"),
    "reach_delivery": ("reach", "planned_reach", 1.0, "Actual / planned reach", "ratio"),
}

# Minimum denominators below which a rate is flagged as low-volume for comparison purposes.
MIN_DENOMINATOR = {"impressions": 5000, "clicks": 100, "video_starts": 1000, "video_views": 500,
                   "video_p25": 300, "video_p50": 200, "video_p75": 150, "conversions": 20,
                   "reach": 2000, "spend": 0, "planned_spend": 0, "planned_impressions": 0, "planned_reach": 0}


def available_derived(columns: Iterable[str]) -> list[str]:
    cols = set(columns)
    return [k for k, (n, d, *_r) in DERIVED.items() if n in cols and d in cols]


def safe_div(n: float, d: float, mult: float = 1.0) -> float:
    if d is None or n is None or (isinstance(d, float) and math.isnan(d)) or (isinstance(n, float) and math.isnan(n)) or d == 0:
        return math.nan
    return n / d * mult


def aggregate(df: pd.DataFrame, by: list[str] | None = None, reach_dims_ok: bool = False) -> pd.DataFrame:
    """Sum base metrics (min_count=1 keeps all-missing groups as NaN) and recompute derived metrics.

    reach_dims_ok=True only when the caller knows each group is a single reach-deduplicated row.
    Otherwise summed reach is marked as an upper bound in column `reach_is_summed`."""
    base = [c for c in df.columns if c in METRIC_SYNONYMS]
    if by:
        g = df.groupby(by, dropna=False)
        out = g[base].sum(min_count=1)
        out["rows"] = g.size()
    else:
        out = df[base].sum(min_count=1).to_frame().T
        out["rows"] = len(df)
    for k in available_derived(out.columns):
        n, d, m, *_ = DERIVED[k]
        out[k] = [safe_div(a, b, m) for a, b in zip(out[n], out[d])]
    if "reach" in out.columns:
        out["reach_is_summed"] = (out["rows"] > 1) & (not reach_dims_ok)
    return out


# --------------------------------------------------------------------------------------------
# Statistics without scipy
# --------------------------------------------------------------------------------------------

def norm_cdf(z: float) -> float:
    return 0.5 * (1.0 + math.erf(z / math.sqrt(2.0)))


def wilson_interval(successes: float, n: float, z: float = 1.96) -> tuple[float, float]:
    if not n or n <= 0 or math.isnan(n) or math.isnan(successes):
        return math.nan, math.nan
    p = successes / n
    denom = 1 + z * z / n
    centre = (p + z * z / (2 * n)) / denom
    half = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / denom
    return max(0.0, centre - half), min(1.0, centre + half)


def two_proportion_test(x1: float, n1: float, x2: float, n2: float) -> dict:
    """Two-sided z-test. Ad delivery is not a random sample and impressions are not independent
    trials, so p-values here are a noise screen, not proof. Very large n makes everything
    'significant'; materiality is judged separately."""
    if min(n1, n2) <= 0 or any(math.isnan(v) for v in (x1, n1, x2, n2)):
        return {"z": math.nan, "p_value": math.nan}
    p1, p2 = x1 / n1, x2 / n2
    p = (x1 + x2) / (n1 + n2)
    se = math.sqrt(p * (1 - p) * (1 / n1 + 1 / n2))
    if se == 0:
        return {"z": math.nan, "p_value": math.nan}
    z = (p1 - p2) / se
    return {"z": z, "p_value": 2 * (1 - norm_cdf(abs(z)))}


def spearman(x: list[float], y: list[float]) -> float:
    pairs = [(a, b) for a, b in zip(x, y) if not (math.isnan(a) or math.isnan(b))]
    if len(pairs) < 3:
        return math.nan
    xs = pd.Series([p[0] for p in pairs]).rank()
    ys = pd.Series([p[1] for p in pairs]).rank()
    return float(xs.corr(ys))


def robust_z(values: pd.Series) -> pd.Series:
    med = values.median()
    mad = (values - med).abs().median()
    if not mad or math.isnan(mad):
        return pd.Series([0.0] * len(values), index=values.index)
    return 0.6745 * (values - med) / mad


def ols_slope(x: list[float], y: list[float]) -> tuple[float, float]:
    """Return (slope, r_squared)."""
    pts = [(a, b) for a, b in zip(x, y) if not (math.isnan(a) or math.isnan(b))]
    if len(pts) < 3:
        return math.nan, math.nan
    xs = [p[0] for p in pts]
    ys = [p[1] for p in pts]
    mx, my = sum(xs) / len(xs), sum(ys) / len(ys)
    sxx = sum((a - mx) ** 2 for a in xs)
    if sxx == 0:
        return math.nan, math.nan
    sxy = sum((a - mx) * (b - my) for a, b in zip(xs, ys))
    slope = sxy / sxx
    ss_tot = sum((b - my) ** 2 for b in ys)
    ss_res = sum((b - (my + slope * (a - mx))) ** 2 for a, b in zip(xs, ys))
    r2 = 1 - ss_res / ss_tot if ss_tot else math.nan
    return slope, r2


# --------------------------------------------------------------------------------------------
# JSON helpers
# --------------------------------------------------------------------------------------------

def clean(o):
    """Make numpy/pandas values JSON-safe and round floats for readability."""
    if isinstance(o, dict):
        return {str(k): clean(v) for k, v in o.items()}
    if isinstance(o, (list, tuple)):
        return [clean(v) for v in o]
    if isinstance(o, (pd.Timestamp,)):
        return o.strftime("%Y-%m-%d")
    if hasattr(o, "item") and not isinstance(o, (str, bytes)):
        try:
            o = o.item()
        except Exception:
            pass
    if isinstance(o, float):
        if math.isnan(o) or math.isinf(o):
            return None
        return round(o, 6)
    return o


def dump(obj, path: str | Path | None = None) -> str:
    text = json.dumps(clean(obj), indent=2, ensure_ascii=False, default=str)
    if path:
        Path(path).write_text(text, encoding="utf-8")
    return text


def pick_table(tables: list[Table], sheet: str | None = None) -> list[Table]:
    if sheet:
        sel = [t for t in tables if t.sheet == sheet]
        if not sel:
            raise SystemExit(f"Sheet '{sheet}' not found. Available: {[t.sheet for t in tables]}")
        return sel
    return tables
