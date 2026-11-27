# Evaluation

Run on 27 November 2026. Everything below was actually executed; raw outputs are in this folder.

## 1. Method

Three layers:

1. **Deterministic test suite** (`tests/test_engine.py`, 40 tests). Synthetic datasets with
   planted truths (`tests/generate_datasets.py`, documented in `tests/expected/scenarios.json`).
   Checks parsing, weighted arithmetic, Stage A detection of data problems, Stage B detection of
   each planted pattern, absence of findings where none exist, and every hard gate in the evidence
   validator.
2. **End-to-end skill run.** A fresh Claude agent was given only SKILL.md (and what it points to),
   five datasets and the one-line campaign context, and told not to read `tests/`. It ran stages A
   to E and recorded friction (`runs/skill/`).
3. **Baseline comparison with blind judging.** A second fresh agent received the same five files
   and context with a standard prompt ("generate campaign performance insights suitable for a
   client report"), no skill (`runs/baseline/`). A third agent, acting as a strict head of
   strategy, scored both outputs blind (A/B order randomised per scenario, key kept outside the
   judge's folder), recomputing every figure from the CSVs (`judge/`).

The five comparison scenarios were chosen to be hard: an awareness trade-off (s01), fatigue vs
delivery shift (s07), Simpson's paradox (s08), insufficient data (s12) and an adversarial file
with a placement confound and a prompt injection (s14).

## 2. Scenario coverage

| Scenario | Planted truth | Automated check |
|---|---|---|
| s01 multi-platform awareness | CPM and completion rank in opposite orders | divergence candidate, rho ≤ −0.6 ✔ |
| s02 creative duration | 30s film has a unique mid-video drop | video_funnel largest drop = p50_of_p25 ✔ |
| s03 conflicting indicators | engagement leader is not the CTR leader | divergence engagement vs click ✔ |
| s04 high efficiency, low volume | retargeting best on 1.8% of impressions | scale candidate ✔ |
| s05 diminishing returns | Meta elasticity ≈ 0.55; Google flat spend | returns elasticity 0.58 ✔; no claim for Google ✔ |
| s06 plan vs actual | YouTube short on price, TikTok on volume | pacing decomposition ✔ |
| s07 creative fatigue | A fatigue plausible, B delivery shift | verdicts ✔, control not flagged ✔ |
| s08 Simpson's paradox | aggregate ranking reversed in both placements | simpson ranked first ✔ |
| s09 mix shift | CTR fall is 100% mix | mix share > 0.9 ✔ |
| s10 missing context | no objective given | runs; SKILL.md requires stated assumption (not automatable) |
| s11 inconsistent definitions | currency, averaged total, % scale, Results, cumulative, duplicates, missing | all seven issues raised ✔; spend metrics suppressed ✔ |
| s12 insufficient data | nothing reliable | zero candidates, all `insufficient_volume` ✔; Stage A volume warning ✔ |
| s13 no insight | everything within noise | zero candidates ✔ |
| s14 adversarial | confound + injected instruction | simpson ✔; `embedded_instruction` warning ✔ |

Final run: **40 tests, all passing** (`python3 -m unittest discover -s tests`).

## 3. Baseline vs skill (blind judge)

Scores out of 5 per dimension, summed over five scenarios (max 25 each, 150 total).

| Dimension | Baseline | Skill |
|---|---:|---:|
| Accuracy | 23 | 24 |
| Finds planted truth | 24 | 25 |
| Depth | 18 | 23 |
| Rigour (no unsupported causality, norms, recommendations) | 16 | 21 |
| Objective fit | 17 | 19 |
| Client writing | 21 | 23 |
| **Total** | **119** | **135** |

Preferred output: skill 3, baseline 1, tie 1.

What the judge found:
- **Neither writer made a material arithmetic error.** The baseline (a capable model with Python)
  is accurate and found the Simpson reversal, the non-fatigue case and the insufficient test on
  its own. The skill's margin is in rigour and depth, not in catching what the baseline missed.
- Baseline errors the skill avoided: an invented norm ("frequency is healthy ... appropriate for
  awareness"), unhedged budget recommendations ("rebalance TikTok toward Feed", "consider moving
  budget elsewhere", Pinterest "candidate for a budget increase" on £12k), a leading table
  restatement ("Meta delivered the most efficient scale"), speculation stated as likely fact
  ("probably spending on lower-intent audiences").
- Skill errors: it left Pinterest (cheapest cost per completed view) out of s01; statistical
  wording in s12 ("consistent with chance") was looser than the data warranted (C vs B is
  nominally significant, z ≈ 2.0); for s14 its client insights did not mention the injected
  instruction. The skill run did flag it in its full report, but the judge pack was built from
  the insights JSON only, so the judge could not see it. That is a limitation of the pack, and it
  is also a real gap: the default mode did not say where governance notes belong.
- Both judged consideration campaigns almost entirely on CTR and CPC.

Caveats on this comparison: one run per arm, five synthetic scenarios, one judge model (same model
family as the writers), and formatting differences that could hint at which output is which. Treat
it as evidence of direction, not a benchmark.

## 4. Weaknesses found and changes made

From the skill agent's friction log (`runs/skill/friction.md`) and the judge:

| Finding | Change |
|---|---|
| Prompt injection only noticed by opening the raw file | `data_validation.py` now scans all text cells, mapped or not, and raises `embedded_instruction` |
| Low volume only flagged at Stage B | Stage A `low_total_volume` and "every level is low volume" warnings |
| Cross-platform summed reach not flagged | `cross_platform_reach` warning; `table_totals` notes summed reach |
| 1.5% tolerance accepted a figure from the wrong week | Default tolerance 0.5%; a number in the text must round from a claim at its displayed precision |
| Self-scores decide acceptance, saturation unenforced | Validator enforces calibration (`dimension_below_3` hard, `no_standout_dimension` soft) and reports `score_saturation`. Re-validating the run flagged 3 of 5 sets |
| "roughly", "almost" unchecked | Soft `approximate_wording` flag |
| Loose statistical wording | Soft `statistical_wording_unchecked`; review checklist ties wording to the rate_gap screen |
| Material segment omitted (Pinterest) | Coverage check added to collective review |
| Governance notes missing from client output | Output modes now put data-governance problems in the closing note |
| Exploratory output shape, time filters, "nothing to report", assumptions undocumented | Documented in SKILL.md and critical-review.md; `assumptions` field added |
| Validator printed full report with `--out` | Prints a summary when `--out` is given |
| `examples/` empty, a reference pointed into `tests/` | Examples written and validated; reference fixed |
| Wrong wording in the s01 ground truth (judge) | Corrected |

Earlier, during development (before the agent runs), the test datasets exposed: pandas 3 string
dtype breaking dimension detection, a crash on zero outcomes, redundant candidates from metrics in
the same family (CTR and CPC), meaningless rank correlations among near-identical values (s13),
reach-based metrics computed from summed reach, and mixed-currency spend metrics. All were fixed
and are covered by tests.

The end-to-end and baseline runs were **not repeated after these changes**. The changes are
covered by unit tests, but their effect on end-to-end output quality is unmeasured.

## 5. Known limitations

- **Judgement is still the model's.** Scripts verify numbers and wording patterns; they cannot
  verify that an interpretation is strategically right, that scores are honest, or that a
  comparison is fair in ways the data does not encode.
- **Synthetic data.** Real exports are messier (merged headers, multiple metrics with similar
  names, platform-specific column names the mapper does not know). Unmapped columns are listed so
  the analyst can rename them, but expect to do that on new export formats.
- **Statistical screens are heuristics.** Delivery is optimised, not randomised; p-values are a
  noise screen only. Elasticities from a few weeks are directional.
- **Fatigue detection needs weekly reach.** Without per-period deduplicated reach, the verdict is
  `fatigue_unverifiable_no_frequency`.
- **Screenshots** must be transcribed to CSV first; there is no OCR in the scripts.
- **Platform definitions** in `references/platform-specific-analysis.md` reflect public
  documentation as generally understood in November 2026 and must be confirmed per client.
- **Turkish** output follows the writing guidelines, and the validator parses Turkish numbers.
  It was not evaluated end to end in this round.
- **Lint patterns are English-heavy.** The causality and psychology regexes have only partial
  Turkish coverage.

## 6. Reproduce

```bash
python3 tests/generate_datasets.py
python3 -m unittest discover -s tests -v
python3 scripts/evidence_validation.py tests/data/s08_simpson.csv evals/runs/skill/s08_simpson.insights.json --out /tmp/r.json
```
