# Annotated examples: from candidate to insight

Shows the path one finding takes through the stages, using tests/data/s08_simpson.csv.

## 1. Candidate (Stage B, script output, abridged)

```
C009 simpson  materiality 0.9  metric ctr
  In aggregate Meta looks better on ctr, but TikTok is better within every placement (2 strata).
  numbers: aggregate {Meta: 0.0081, TikTok: 0.00488}
           within_strata {Feed: {Meta: 0.009, TikTok: 0.010}, Stories: {Meta: 0.003, TikTok: 0.0036}}
           mix_of_impressions {Meta: {Feed: 0.85, Stories: 0.15}, TikTok: {Feed: 0.20, Stories: 0.80}}
  checks: whether the placement mix was a planning choice or algorithmic; volume within each stratum
```

## 2. Hypothesis and test (Stage B)

H: Meta's CTR lead is a placement-mix artefact.
Refutes if: Meta leads within Feed or within Stories, or volumes per stratum are too small.
Test: `metric_calculation.py tests/data/s08_simpson.csv --by platform --by placement` → TikTok
leads in both; each stratum has at least 750,000 impressions. Supported.

## 3. Interpretation (Stage C)

Consideration objective: CTR matters. The platform-level comparison would push budget towards
Meta on false grounds. The real lever is placement: Feed outperforms Stories on both platforms.

## 4. Review (Stage D)

- Causal? The claim is compositional (an identity), not causal. OK.
- Alternatives: audience differences between platforms remain possible within placement; say so
  if recommending a shift.
- Restates table? No, the table shows Meta ahead; the insight reverses it.

## 5. Client-ready text

> Meta's overall CTR of 0.81% is well ahead of TikTok's 0.49%, but the comparison is about
> placements rather than platforms. TikTok is ahead inside both Feed and Stories; it trails in
> aggregate only because 80% of its impressions ran in Stories, against 15% of Meta's. Any budget
> decision based on the platform-level CTR would reward a placement mix, not platform
> performance.

(The validator test `TestEvidenceGate.test_good_insight_accepted` checks an insight built from
the same claims.)
