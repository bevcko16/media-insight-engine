# Hypothesis generation and testing

Adapted in concept from Data Prospector's fan-out, judge and test design (see
THIRD_PARTY_NOTICES.md). No code or prompt text is reused. What is borrowed is the idea that
analysis improves when many independent angles are generated before any is pursued, each is judged
separately for novelty and for soundness, and refuted ideas are reported rather than hidden.

## 1. Why diverge first

Analysts and models both converge on the first obvious comparison (which platform had the best
CTR). Divergence forces coverage of the questions an experienced planner would ask and the ones
they would not think to ask.

## 2. Generate angles from several stances

For every analysis, generate at least two angles from each stance that applies. Each angle names
the data it uses and what it expects to find.

| Stance | Typical questions |
|---|---|
| **Sceptic** | Is the headline difference real? Could mix, volume, timing or definitions explain it? What does the aggregate hide? |
| **Planner** | Did each platform and line do the job it was planned for? Where did plan and delivery diverge, and was it price or volume? Is reach building or is frequency stacking? |
| **Buyer** | What drove cost? Auction pressure, inventory mix, audience narrowness, learning phases, bid strategy? Where is the marginal pound working hardest and where is it saturating? |
| **Creative strategist** | Are assets doing different jobs (stopping power vs message delivery vs action)? Where in the video do viewers leave, and does it differ by asset or placement? Is decline fatigue or delivery drift? |
| **Finance / client** | What share of budget produced what share of outcome? Is concentration intended? What is the cost of the inefficient part? |
| **Measurement** | Which numbers are comparable at all? What is modelled or self-attributed? What would a test need to look like? |

Use the candidates from `exploratory_analysis.py` as a starting set, not the whole set. Add
angles the script cannot see: brief vs delivery, creative content, market events, plan changes the
user mentioned.

## 3. Write each angle as a falsifiable hypothesis

```
H7  Short assets earn clicks; long assets earn completion. The two are not substitutes.
    Supports if: CTR and completion rank in opposite orders across assets of similar volume,
                 and the pattern holds within each placement.
    Refutes if:  the ordering flips within placements, or the long asset ran mostly on
                 low-CTR placements.
    Data:        ad x placement, clicks, impressions, starts, completions
    Method:      metric_calculation.py --by ad --by placement; compare within placement
```

## 4. Judge before testing (two independent judgements)

For each hypothesis decide separately:

- **Insight potential** (0 to 1): would a planner learn something not visible in the table? Is it
  linked to the objective? Is it a duplicate of another angle?
- **Soundness given the data**: `solid` (data can test it directly), `caveat` (testable with a
  stated limitation), `unsupportable` (the data cannot speak to it).

Test the `solid` and `caveat` angles with the highest insight potential first. An `unsupportable`
angle may still be useful as a **question requiring further investigation**.

Do not trust an angle's own claim to novelty. Many angles that feel different are the same
comparison seen from another metric in the same family (CTR and CPC, completion rate and CPCV).

## 5. Test

- Compute the supporting and refuting cuts. Volume first, then rate.
- Stratify by every available dimension that could confound the comparison.
- Check time: did the segments run in the same weeks?
- Check the denominator definition and platform definitions.
- Record the outcome: supported, supported with caveat, refuted, inconclusive.

## 6. Keep the refuted ones

Refuted and inconclusive hypotheses go into the Evidence and Validation Report with the reason.
They are also often the most useful thing to tell a client who believed the opposite ("the drop in
CTR is not fatigue; frequency was flat and delivery moved to cheaper placements").

## 7. Patterns worth checking every time (when the data allows)

- Share of spend vs share of the objective's outcome, by every dimension.
- Rank disagreement between metrics (cheap reach vs attention; engagement vs intent).
- Aggregate ranking that reverses inside strata (Simpson's paradox).
- Period change split into mix and rate.
- Plan vs actual split into budget and price.
- CTR or completion decline with frequency and CPM trajectories beside it.
- Spend elasticity across weeks where spend varied materially.
- Best rate on tiny volume (scalability unproven).
- Concentration of outcome in a few assets or lines.
- Video quartile drop-off location by asset and by placement.
- Outliers that are more likely tracking errors than performance.
