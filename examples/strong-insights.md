# Strong insights (calibration)

Generated from the synthetic test datasets and passed through `scripts/evidence_validation.py`
(inputs and validator output in `examples/validated/`). Use them to calibrate depth and tone.
**Do not reuse their sentence structures.** Each is strong for a different reason.

## Plan vs actual, decomposed (tests/data/s06_plan_vs_actual.csv)

**Two similar shortfalls with different causes**

YouTube and TikTok both finished around 30% short of planned impressions, but for unrelated reasons. YouTube spent 98% of its budget and still delivered only 72% of planned impressions because its CPM averaged 10.90 against 8.00 in the plan, 36% higher. TikTok's CPM was close to plan at 4.05 against 4.00; it fell short because only 71% of its budget was spent. The YouTube gap is a forecasting question about whether the planned price was achievable in the period, while TikTok's is a delivery question about why budget was not taken up, so the two need different owners.

Why it works: it splits one number (impressions vs plan) into budget and price, and the split
tells the client who can fix each problem. The causal word "because" is allowed only because the
relationship is an arithmetic identity, recorded in `causal_evidence`.

## Aggregate decline that is really mix (tests/data/s09_mix_shift.csv)

**The CTR drop is a placement story, not a creative one**

Click-through rate fell from 0.85% in August to 0.69% in September, yet CTR within each placement did not move: Feed held at 1.10%, Stories at 0.40% and Reels at 0.60% in both months. The decline is a change in where impressions ran rather than in how the ads performed. Feed's share of delivery fell from 60% to 35% as Stories and Reels took more of it, so the account-level CTR has become a poor guide to creative performance. Whether that shift was a deliberate reach decision or the algorithm finding cheaper inventory is the question for the buying team before anyone revisits the creative.

Why it works: it prevents a wrong decision (refreshing creative) by showing the rate effect is
zero and the mix effect is the whole change, then ends on the question that matters rather than a
recommendation.

## Where viewers leave (tests/data/s02_creative_duration.csv)

**The film has a mid-video problem, not a length problem**

The 30-second film loses viewers in a way the other three assets do not. Only 52% of those who reached the quarter mark carried on to halfway, against 73% to 86% for the shorter assets, and the curve then steadies, with 81% of halfway viewers going on to the three-quarter point. A cliff of this shape is consistent with something specific in the film's second quarter rather than length alone, which gives the edit team a precise place to look. It also means the film's cost per completed view of 0.041, against 0.011 for the bumper, is not a clean read on what long-form attention costs.

Why it works: it uses the quartile curve to locate a specific, actionable moment and qualifies an
easy but misleading conclusion about long-form cost. Tier is `supported`, so the wording says
"consistent with" rather than asserting the cause.
