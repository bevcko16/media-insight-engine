# Weak insights (what the skill must not produce)

Each was run through `scripts/evidence_validation.py` against tests/data/s02_creative_duration.csv.
The rejection reasons are the validator's actual output (`examples/validated/weak.validation.json`).

| Id | Text | Validator decision |
|---|---|---|
| W1 | The 6-second bumper was the best-performing asset, with an impressive CTR of 0.94% and a strong completion rate. | Rejected: `restates_table`, `adjective_padding`, `too_short`. One number plus adjectives. |
| W2 | Short-form video generated a 0.94% CTR against 0.52% for the 30-second film because consumers have shorter attention spans and prefer snackable content. | Rejected: `unsupported_causality`, `unsupported_psychology`. Campaign data cannot show attention spans. |
| W3 | The bumper's CTR of 0.94% was almost double the film's 0.52%, and this underscores the need for a short-first creative strategy moving forward, delivering 25% more value per pound. | Rejected: `unbacked_number` ("25% more value" has no basis), `banned_phrase` ("underscores the need"). |
| W4 | The film's completion rate of 31% trailed the bumper's 56%, while its cost per completed view was four times higher; long-form video is therefore an expensive way to buy attention. | Rejected: `incorrect_calculation` (film completion rate is 23.9%, not 31%) and `unbacked_number`. |

Also weak, but not machine-detectable, so the reviewer must catch them:

- Comparing platforms on "video views" when the view definitions differ.
- Calling a CTR decline "fatigue" without frequency evidence.
- Ranking assets that ran in different weeks or placements as if in a test.
- Judging an awareness platform on CPA.
- A true, verified, well-written point that would not change any decision (scores low on
  strategic significance and should be dropped).
