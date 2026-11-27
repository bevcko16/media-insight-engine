# Analytical methodology

The end-to-end method, and the arithmetic rules every stage depends on.

## Contents
1. Principles
2. Stage A: data understanding and validation
3. Arithmetic rules
4. Valid and invalid comparisons
5. Statistical screening (and its limits)
6. Stage B to E in brief

## 1. Principles

- **Compute, then interpret.** The model reasons; Python counts. If a number is not in a script
  output or the source file, it does not go in a report.
- **Explain variance, not levels.** "CTR was 0.8%" is a level. The analytical work is explaining
  differences: between segments, between periods, between plan and actual, between metrics.
- **Every difference has a denominator.** Ask "out of what?" before "how big?".
- **Prefer the disconfirming cut.** The quickest way to a robust insight is trying hard to break it.
- **Aggregate numbers hide segment behaviour.** Always ask what the mix underneath looks like.

## 2. Stage A: data understanding and validation

`scripts/data_validation.py` automates most of this. Confirm in your own words:

| Question | Why it matters |
|---|---|
| What does one row represent? (unique key) | Determines what can be summed and what cannot |
| What is the reporting period? Equal comparison windows? | Unequal windows invalidate total-based comparisons |
| Which dimensions exist, and are they nested? (ad inside ad set inside campaign) | Nested dims double-report the same rows |
| Which metrics are base counts vs rates? | Rates must be rebuilt from counts |
| Are reported rates consistent with recomputed ones? | Reveals hidden definitions (all clicks vs link clicks) |
| Zero vs missing | A 0 is a fact; a blank is an absence of data |
| Cumulative or incremental? | Running totals look like growth |
| Totals row present? Does it reconcile? Is its ratio a simple average? | Agency summary rows often average ratios |
| Currency and units consistent? | Mixed currency invalidates spend sums |
| Platform definitions compatible? | Video views, conversions and clicks differ by platform |
| Volume adequate for each comparison? | Small denominators produce large, meaningless gaps |

Fixes you may make deterministically, stating each one: drop exact duplicate rows; difference a
cumulative series; exclude total rows; convert percent scale; convert currency using a rate the
user supplies. Fixes you may not make: guessing a missing value, choosing a currency rate, deciding
which of two conflicting columns is "right" without asking.

**Clarify only when it matters.** Ask when a missing fact would change the conclusion (objective
unknown in a mixed file; two click columns with different values; currency rate). Otherwise
proceed and write the assumption into the analysis.

## 3. Arithmetic rules

1. **Rebuild every ratio from sums.** CTR of a group = Σclicks / Σimpressions. Never the mean of
   row CTRs. The difference can reverse rankings (see examples/annotated-examples.md).
2. **Costs are spend / volume of the same rows.** CPM = Σspend / Σimpressions × 1000 over rows
   where both are present.
3. **Reach is not additive** across days, ad sets, placements, audiences or platforms. A sum of
   reach is an upper bound on unique reach; frequency from it is a lower bound. Use deduplicated
   reach from the platform for the level being discussed, or say "at least".
4. **Percentage points vs percent.** 1.0% to 1.2% CTR is +0.2 pp and +20%. Say which.
5. **Shares need a common base.** Share of spend and share of outcome must be over the same rows.
6. **Period comparisons need equal windows** or per-day normalisation, and the same day-of-week
   mix where weekly cycles matter.
7. **Decompose aggregate changes** into rate effect and mix effect before explaining them:
   ΔR = Σ(w₁−w₀)·r₀ [mix] + Σw₁·(r₁−r₀) [rate] (+ effect of segments entering or leaving).
   `exploratory_analysis.py` does this as `mix_shift` when a `period` column exists.
8. **Plan vs actual impressions decompose into budget and price:**
   impressions ratio = spend ratio × (planned CPM / actual CPM). A shortfall from price is an
   auction or buying issue; a shortfall from spend is a pacing or delivery issue.
9. **Rounding** only at presentation. Keep three significant figures in text unless precision
   matters.

## 4. Valid and invalid comparisons

| Comparison | Valid when | Invalid or risky when |
|---|---|---|
| Platform vs platform on CTR/CPM | Same objective and similar placements; as a role description | Used to declare a "winner" across different jobs |
| Video view rate across platforms | Same view definition | Default platform definitions (2s vs 3s vs 30s) |
| Conversions across platforms | Same attribution window and deduplicated source | Summing platform-reported conversions |
| Creative A vs B | Same audience, placement, period and budget, or a proper test | Different weeks or placements; one in learning |
| Period vs period | Equal windows, same mix or mix-adjusted | Holiday vs non-holiday without mention |
| Plan vs actual | Plan figures are the final agreed version | Plan revised mid-flight but old plan used |
| Short vs long video on completion | Normalised to role or compared within duration | Raw completion rate across very different lengths |

## 5. Statistical screening and its limits

The scripts screen proportions with a two-proportion z-test and Wilson intervals, and use rank
correlation, robust z-scores and log-log slopes elsewhere. Treat them as **noise screens**:

- Ad impressions are not independent random trials, and delivery is optimised, not randomised.
  p-values understate true uncertainty.
- With millions of impressions almost every difference is "significant". Materiality (size of the
  gap and share of budget affected) decides importance, not the p-value.
- With fewer than about five segments, a rank correlation is directional only.
- An elasticity from a handful of weeks with co-moving seasonality is a hypothesis, not a curve.
- Never claim a test result is "statistically significant" in client text unless an actual
  controlled test (A/B split, brand lift, conversion lift, geo holdout) was run.

## 6. Stages B to E in brief

- **B** generate many candidate questions, test each, keep rejected ones in the log
  (hypothesis-generation.md).
- **C** interpret survivors against objective and platform role (media-strategy.md).
- **D** review as an adversary; validate numbers and wording with the script (critical-review.md).
- **E** write in the requested mode (output-modes.md, writing-guidelines.md).
