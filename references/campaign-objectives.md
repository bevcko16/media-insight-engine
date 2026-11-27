# Campaign objectives and KPI frames

Choose the frame before choosing the metrics. Pass the frame to `exploratory_analysis.py
--objective` so materiality is weighted toward what the campaign was bought to do.

| Frame | `--objective` | Primary KPIs | Secondary / diagnostic | Usually irrelevant as success measures |
|---|---|---|---|---|
| Reach / awareness | `awareness` | Deduplicated reach, cost per thousand reached, frequency, CPM | Completion, view rate, viewability, brand lift if measured | CTR, CPA, ROAS |
| Video / message delivery | `video` | Completion rate, cost per completed view, quartile retention, ThruPlay or 6s views | Reach, frequency | CTR, CPA |
| Consideration / traffic / engagement | `consideration` | CTR (link), CPC, landing page views, engagement rate, saves | Completion, onsite quality if supplied | ROAS |
| Conversion / performance | `conversion` | CPA, conversions (deduplicated where possible), ROAS, CVR | CTR, CPC, frequency on retargeting | Engagement |

## Recognising the objective when it is not stated

- Metrics supplied: reach and frequency columns, completion columns, no conversions → awareness or
  video. Conversions and values → performance.
- Buying type: reach and frequency or CPM buying (TrueView for reach, Meta reach objective) →
  awareness. CPV buying → video. oCPM toward purchase/lead → conversion.
- Meta "Results" column: its meaning depends on the ad set's optimisation event. Check before using.
- Campaign naming conventions often encode objective (AWR, CONS, CONV, BRD, PERF).

State the inferred objective and the evidence for it. If lines in one file have different
objectives, analyse them as separate groups.

## Campaign types

### Brand awareness (mass)
The question is whether the campaign reached enough of the right people often enough, at a
sensible cost, and held attention. Look at reach build over time, frequency distribution (if
available), cost per reach, completion by asset and placement. Diminishing reach returns
(frequency rising while incremental reach slows) is the key efficiency signal.

### Luxury and premium
Environment and attention matter more than cost. A low CPM may indicate the wrong environment.
Judge reach within the target audience, premium placement share, completion of longer brand films,
and brand lift where available. Small, high-quality audiences mean high CPMs are expected; avoid
calling them inefficient. Be careful with engagement: mass engagement can be off-brand for luxury.

### FMCG
Broad reach and frequency against a wide audience, often with retail or seasonal timing. Judge
reach and cost per reach, frequency within effective ranges agreed with the client, completion,
and retail or sales data if supplied (with attribution caveats). Flight timing vs promotional
calendar is often the most strategic context.

### Performance / direct response
CPA, ROAS and conversion volume against target, with deduplication caveats. Look for marginal cost
vs average cost, saturation of retargeting pools, prospecting vs retargeting roles, conversion lag,
and the gap between platform-attributed and source-of-truth conversions.

### Full-funnel
Evaluate each stage on its own frame, then the hand-offs: does upper-funnel reach show up in
retargeting pool size or branded search? Without connective data, state the hand-off as a
question, not a claim.
