# Insight quality rubric

Score each dimension 0 to 5. Weighted total out of 100. Accept at **80** or above. Hard gates
reject regardless of score. `evidence_validation.py` applies the arithmetic and hard gates; the
scores are your judgement and must be honest.

| Dimension | Weight | 5 | 3 | 1 |
|---|---:|---|---|---|
| Evidence and analytical validity (`evidence`) | 25 | Every number verified; comparison like-for-like; alternatives checked and ruled out or stated | Numbers verified; one plausible confounder unchecked but disclosed | Weak base, unaligned definitions or cherry-picked |
| Strategic significance (`strategic`) | 25 | Changes how the client should think about allocation, role, creative or measurement | Useful context for a decision | True but would not change anything |
| Depth and novelty (`depth`) | 20 | Reveals a relationship, tension or mechanism not visible in the table | Connects two visible facts sensibly | Restates the table with adjectives |
| Relevance to objective (`objective_fit`) | 15 | Directly about the primary KPI or the job the line was bought for | About a secondary KPI | About a metric the objective does not care about |
| Decision value (`decision`) | 10 | Clear implication or a clearly framed test | Implication implicit | None |
| Writing (`writing`) | 5 | Natural, specific, concise; meaning carried by the argument | Clear but formulaic | Jargon, filler, or hard to follow |

Weighted score = Σ weight × score / 5.

**Calibration.** A typical sound but unremarkable insight scores 3s and 4s and lands in the low
70s: it should be rejected or merged. 80+ requires at least one 5 among evidence, strategic or
depth and no dimension below 3.

## Hard gates

- Incorrect calculation.
- Any number not backed by a verified claim.
- Unsupported causality (causal wording in a confirmed or supported insight with no causal evidence).
- Consumer psychology claims.
- Fabricated or unsourced external evidence.
- Materially misleading comparison (judged by you: different jobs, definitions, windows or mixes).
- Restating the table (single quantity, no relationship).
- Em dash in client text.

## Why this differs from a simple score

Changes from the starting framework in the brief, and why:

1. **Hard gates sit outside the score.** A well-written insight with one wrong number must not be
   rescued by its other dimensions.
2. **Novelty is judged against the table**, not against the model's own sense of originality.
   Data Prospector's development log notes that self-assessed novelty is unreliable; ask "could
   a planner read this off the table?"
3. **Collective review is a separate step.** Two individually strong insights that say the same
   thing count once.
4. **Score saturation check.** If every insight scores 85+, re-score: the set is probably being
   flattered.
