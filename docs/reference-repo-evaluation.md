# Reference repository evaluation

Inspected 27 November 2026 by cloning each repository (`git clone --depth 1`) and reading source,
skill files, prompts and tests. Claims in READMEs were checked against code where possible.

| | LangChain Paid Media Agent | Dataslayer Marketing Skills | Data Prospector (Francis Crick Institute) | rampstackco ads-performance-analytics |
|---|---|---|---|---|
| URL | github.com/langchain-ai/paid-media-agent | github.com/Dataslayer-AI/Marketing-skills | github.com/FrancisCrickInstitute/Data-Prospector | github.com/rampstackco/claude-skills (skills/ads-performance-analytics) |
| Accessible | Yes | Yes | Yes | Yes |
| Licence | Apache-2.0 | MIT | **GPL-3.0** | MIT |
| What it is | Slack-deployed Deep Agents analyst with live platform reads (via Pipeboard), deterministic compute tools, write-proposal workflow | 7+ Claude skills plus `ds_utils.py` helper library, MCP-first data fetching | Research pipeline: generate many analysis "angles", judge each for insight and soundness, realise top ones as sandboxed code | Single knowledge skill: how to read paid media dashboards without fooling yourself; seven reference files |
| Data input | Live APIs (Pipeboard), fixtures | Dataslayer MCP or pasted CSV/JSON | Configured dataset + report | None (knowledge only) |

## Strongest components

**Paid Media Agent**
- Deterministic compute is enforced: `tools/compute.py` sums base metrics and derives CTR, CPC,
  CPM, CVR, CPA, ROAS from sums (`aggregate()` docstring: "Sum raw metrics then derive ratios. A
  metric missing from every row stays None").
- Data hygiene rules that are actually coded: comparison windows must be equal length, an empty
  window is "unavailable data, never zero", cross-platform totals are suppressed when sources are
  incompatible (`compare_periods.py`).
- Clear separation of observation, explanation and hypothesis in `skills/paid-media-wiki/decision-model.md`;
  sensible benchmark discipline (`benchmarks.md`: own history first, external only as ranges with
  caveats).

**Dataslayer**
- Skills are written with a strong analyst persona and concrete diagnosis steps.
- Practical tracking sanity checks (e.g. `cpa_sanity_check`, `detect_conversion_event`) catch soft
  conversion events.
- A triggering-accuracy eval for skill descriptions (`skills/ds-eval/eval/triggering-tests.yaml`).

**Data Prospector**
- The most methodologically interesting: diverge (many angles, varied stances) before converging;
  judge insight and soundness *independently*; three-way soundness verdict
  (`solid`/`caveat`/`unsupportable`) instead of a boolean (`judging.py`).
- Explicit finding that self-assessed novelty is unreliable (comments in `judging.py`): judges must
  not trust an angle's own "why non-obvious" field.
- Reports refuted ideas rather than hiding them.

**rampstackco**
- Good catalogue of interpretation failures (`references/common-interpretation-failures.md`) and
  platform reporting quirks; attribution and reconciliation discipline.

## Limitations found

**Paid Media Agent**
- Metric model is conversion-centric: `aggregate()` derives CTR/CPC/CPM/CVR/CPA/ROAS only. No reach,
  frequency, video quartiles, completion or engagement, so awareness and video campaigns are
  poorly served.
- Requires LangSmith, a model key and a Pipeboard token; not designed for uploaded agency files.
- "Significance" is explicitly heuristic (day flagged when spend or conversions move by half).
- Interpretation quality relies on prompts; no evaluation of insight quality.

**Dataslayer**
- README states "113 tested functions" / "113 tests"; `scripts/ds_utils.py` defines 25 functions
  (including helpers) and `test_ds_utils.py` uses a custom harness. We could not reconcile the 113
  figure from the code we inspected; treat it as unverified.
- Hard-coded vertical CPA "benchmarks" inside code (`cpa_sanity_check`, e.g. B2B SaaS suspicious
  below €10) with no source or date: exactly the kind of universal benchmark this skill avoids.
- B2B SaaS / performance orientation; heavily dependent on the Dataslayer MCP.

**Data Prospector**
- GPL-3.0: code and prompt text cannot be incorporated into an MIT skill without relicensing.
  Concepts only were adopted.
- Generic scientific-data pipeline, no media knowledge; requires Docker, Anthropic API and
  configuration per dataset; its own README warns it "isn't an oracle" and documents generated code
  disregarding instructions.
- Ideation prompts are intentionally left as human-owned placeholders in `prompts.py`.

**rampstackco**
- Knowledge only: no scripts, no validation, no workflow for producing insights from a file.
- Performance-marketing framing (ROAS, LTV, CAC); thin on awareness, video and brand.
- Some unsourced numeric rules of thumb (e.g. "real performance changes are 30% or more").

## What was adopted, adapted or rejected

| Concept | Source | Decision | Where |
|---|---|---|---|
| Ratios derived from summed base metrics; missing stays missing | Paid Media Agent | **Adopted** (independently implemented, extended to reach, video, engagement, plan metrics) | `scripts/mie_common.py` |
| Equal-length comparison windows; unavailable ≠ zero | Paid Media Agent | **Adopted** | `data_validation.py` |
| Suppress cross-platform totals when incompatible | Paid Media Agent | **Adapted** into warnings for conversions, video views, clicks, currency | `data_validation.py` |
| Observation / explanation / hypothesis separation | Paid Media Agent | **Adapted** into four evidence tiers enforced by the validator | `critical-review.md`, `evidence_validation.py` |
| Live platform reads, write proposals, Slack runtime | Paid Media Agent | **Rejected**: out of scope (offline uploaded files) | |
| Analyst persona and diagnosis steps | Dataslayer | **Adapted** as stances in hypothesis generation | `hypothesis-generation.md` |
| Tracking sanity checks | Dataslayer | **Adapted** as definition checks (Results column, click type, reported vs recomputed rates) without hard-coded thresholds | `data_validation.py` |
| Hard-coded vertical benchmarks | Dataslayer | **Rejected** | `benchmarking-methodology.md` |
| Diverge-then-judge angle generation with stances | Data Prospector | **Adapted** (concept only; scripted candidates plus model-generated angles) | `exploratory_analysis.py`, `hypothesis-generation.md` |
| Independent insight and soundness judgements; three-way soundness | Data Prospector | **Adopted** (concept) | `hypothesis-generation.md` §4 |
| Do not trust self-assessed novelty | Data Prospector | **Adopted** (concept) | `insight-quality-rubric.md` |
| Report refuted ideas | Data Prospector | **Adopted** | Evidence and Validation mode; `noise`/`immaterial` statuses |
| Sandboxed generated code per angle | Data Prospector | **Rejected**: fixed, tested analyses are more reliable for this domain; arbitrary generated code is a correctness and safety risk | |
| Interpretation failure catalogue, attribution discipline | rampstackco | **Adapted** into challenge lists and platform notes, rewritten for awareness and video as well as performance | `critical-review.md`, `media-strategy.md` |
| Unsourced rules of thumb | rampstackco | **Rejected** | |

## What this skill adds that none of the four had

- Insight-vs-observation enforcement as code: every number in client text must be backed by a
  recomputed claim; table restatements, unhedged causality, psychology claims, filler and em dashes
  are hard or soft gates.
- Media-specific discovery analyses: Simpson reversal detection, rate-vs-mix decomposition, plan
  vs actual price-vs-volume decomposition, fatigue discrimination using frequency and CPM, spend
  elasticity, quartile funnel diagnostics, scale-vs-efficiency, concentration.
- Objective-weighted materiality, so awareness and video campaigns are not judged on CTR or CPA.
- Synthetic adversarial evaluation datasets with planted truths and a baseline comparison.
