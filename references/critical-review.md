# Critical review and evidence validation

Stage D. Change role: you are the reviewer whose reputation depends on nothing weak, wrong or
generic reaching the client.

## 1. Ten questions for every candidate

1. What exactly is happening, in numbers, with the denominator?
2. Is it materially significant (size of gap × share of budget affected), not just statistically?
3. What evidence supports it? Which script output, which rows?
4. What are the alternative explanations? List at least two and check them.
5. Could volume, audience, placement mix, optimisation, learning, timing, seasonality or a
   definition explain it?
6. Is the comparison like-for-like?
7. Why does it matter for this campaign's objective?
8. Does it say something beyond the reporting table?
9. What strategic implication follows, if any?
10. What evidence would strengthen or overturn it?

## 2. Challenge list (automatic rejection if true)

| Failure | Test |
|---|---|
| Incorrect calculation | `evidence_validation.py` recomputes every claim |
| Number in text with no verified claim | Script flags `unbacked_number` |
| Causal claim without causal evidence | Script flags causal verbs in confirmed/supported tiers |
| Consumer psychology claim | Script flags common forms; you catch the rest |
| Fabricated or unsourced external figure | `external` claims must carry a source |
| Materially misleading comparison | Different jobs, definitions, windows or mixes compared as equal |
| Simple restatement of the table | One quantity, no relationship; script flags `restates_table` |

## 3. Challenge list (fix or downgrade)

- Correlation presented as causation → reword as association; move causal reading to hypothesis.
- Generic marketing assumption ("video drives engagement") → delete or evidence it.
- Cherry-picked metric → show the metric that matters for the objective alongside.
- Insignificant difference emphasised → drop it, or say "no meaningful difference".
- Incompatible cross-platform metric → align definitions or remove the comparison.
- Conclusion ignoring the objective → reframe against the objective or drop.
- Recommendation not supported → turn it into a proposed test.
- Redundant insight → merge.
- Contradiction between insights → resolve with data, or present both with the tension explained.
- Speculation presented as fact → hedge and move to the hypothesis tier.

### Fatigue, specifically
Do not call a decline "fatigue" unless: the same asset and audience ran across the period,
frequency rose, and CPM and placement mix did not shift enough to explain the decline. The
`trend` candidate's `fatigue_verdict` is `fatigue_plausible`, `fatigue_unlikely_frequency_flat`
or `fatigue_unverifiable_no_frequency`. Respect it.

## 4. Evidence tiers

| Tier | Meaning | Wording |
|---|---|---|
| `confirmed` | Directly computed from the data; no interpretation needed to be true | Plain statement |
| `supported` | Interpretation consistent with the data, alternatives checked and weaker | "indicates", "is consistent with", "points to" |
| `hypothesis` | Plausible, not verified; names what would test it | "may", "could", "one explanation is", plus the test |
| `question` | Matters, cannot be answered with the data supplied | "We cannot yet tell whether…; [data] would show it" |

## 5. insights.json schema

```json
{
  "language": "en-GB",
  "insights": [
    {
      "id": "I1",
      "tier": "supported",
      "text": "Client-facing paragraph exactly as it will appear.",
      "claims": [
        {"metric": "ctr", "filters": {"platform": "Meta"}, "value": 0.0081},
        {"type": "share", "metric": "impressions", "filters": {"placement": "Feed"},
         "within": {"platform": "Meta"}, "value": 0.85},
        {"type": "ratio", "metric": "cpm", "a": {"platform": "YouTube"}, "b": {"platform": "Meta"}, "value": 3.03},
        {"type": "rel_diff", "metric": "completion_rate", "a": {"ad": "A"}, "b": {"ad": "B"}, "value": 0.42},
        {"type": "rel_diff", "metric": "cpm", "metric_b": "planned_cpm", "a": {"platform": "YouTube"}, "b": {"platform": "YouTube"}, "value": 0.3625},
        {"type": "external", "source": "Client brief, 2026-09, p.3", "value": 0.65}
      ],
      "causal_evidence": null,
      "candidate_ids": ["C009"],
      "alternatives_considered": ["placement mix", "different weeks"],
      "assumptions": ["Completion definitions assumed comparable across platforms (not stated in file)"],
      "scores": {"evidence": 5, "strategic": 4, "depth": 4, "objective_fit": 5, "decision": 4, "writing": 4}
    }
  ]
}
```

Rules:
- Every number that appears in `text` must correspond to a claim (as a fraction, percent, ratio,
  difference or relative difference). Counts like "three platforms" and years are ignored.
- `value` is the unrounded figure from the script output; tolerance is 0.5% relative by default
  (`"tolerance"` overrides per claim). A number in the text is accepted only if some claim, as a
  fraction, percent, ratio or percentage change, rounds to exactly the displayed figure at the
  displayed precision (0.81% is backed by 0.008102; 0.814% is not).
- Time filters use the exact label in the data: `{"week": "2026-09-07"}`, `{"period": "P2 Sep"}`.
  Dates and years in the text are not treated as claims.
- `filters` use canonical dimension names (`platform`, `ad`, `placement`, ...) and exact level
  labels from the data.
- Multi-sheet workbooks: run once per sheet with `--sheet`.

## 6. Collective review

After individual review:
- Remove overlaps (script reports `overlapping_accepted`).
- Order by strategic importance to the objective, not by script materiality.
- Check balance: a set of only positives or only negatives should be justified by the data.
- Vary structure: not every paragraph should end with a recommendation (script warns).
- Check consistency: one insight's assumption must not contradict another's.
- Check coverage: every segment with a material share of budget (roughly 10% or more) is either
  addressed or deliberately left out for a reason you could state. Omitting the cheapest or most
  expensive line without comment looks like cherry-picking.
- Check statistical wording: "consistent with chance", "within noise", "overlapping intervals",
  "too small to call" and "significant" must match the script's `rate_gap` screen (p-value and
  Wilson intervals). If the screen says a gap is nominally significant but volume is tiny, say
  that, rather than "consistent with chance".
