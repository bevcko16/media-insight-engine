# Media-specific strategic interpretation

How to turn a validated pattern into a media judgement. Read with campaign-objectives.md and
platform-specific-analysis.md.

## 1. Every line has a job

Before judging any number, name the job the line, platform or asset was bought to do. Typical jobs:

| Job | Judge on | Do not judge on |
|---|---|---|
| Mass reach at low cost | Cost per thousand reached, deduplicated reach, frequency distribution, viewability | CTR, CPA |
| Attention / message delivery | Completion and quartile retention, average watch time, cost per completed view | CTR (low CTR can be a sign the content is being watched, not skipped) |
| Consideration / traffic | Landing page views, CTR on link clicks, cost per quality visit, engagement on site | Platform engagement alone |
| Conversion | Deduplicated conversions, CPA, ROAS, against the source of truth | Platform-reported totals summed across platforms |
| Retargeting / closing | Incremental conversion (if tested), CPA, audience pool size | Efficiency compared with prospecting lines |
| Brand building (luxury, premium) | Quality of environment, attention, reach in the right audience, brand lift if measured | Lowest CPM; mass engagement |

A platform with a lower CTR is not underperforming if its job was reach or attention. A higher
CPM is not inefficient if it buys attention, premium placements or a scarcer audience.

## 2. Auction and delivery mechanics that explain patterns

Patterns in delivery data are often produced by how platforms buy, not by how people respond.

- **Optimisation sets the audience.** An ad set optimising for reach buys the cheapest available
  impressions; one optimising for ThruPlay or clicks buys users the platform predicts will watch or
  click. Comparing their CTRs compares two different audiences the algorithm chose.
- **Cheapest inventory first.** Small budgets and broad targeting fill low-cost placements
  (Audience Network, Stories, Reels, in-feed video, open exchange) before premium ones. Efficiency at
  small spend rarely holds at large spend.
- **Learning phases.** After launch or significant edits, delivery is less stable and costs are
  usually higher. Lines that spend in a learning phase for much of the window are not comparable
  with stable ones. Meta's guidance is around 50 optimisation events within a week to exit learning;
  check current documentation for each platform.
- **Auction pressure.** CPMs rise in competitive periods (Q4, Black Friday, Christmas, local
  holidays, major sporting events). A CPM rise in such a period is context, not a finding about the
  campaign.
- **Frequency builds when the pool is small.** Narrow audiences and retargeting pools saturate
  quickly; rising frequency with flat reach is the signature.
- **Placement mix drives rates.** Feed, Stories, Reels, in-stream, Shorts and CTV have structurally
  different CTRs, view rates and CPMs. A change in placement mix moves every aggregate rate.
- **Budget allocation algorithms** (Advantage+ campaign budget, Performance Max, DV360 automated
  bidding) move spend to what they predict will hit the optimisation goal, which may not be the
  client's goal.

## 3. Interpreting common tensions

| Pattern | Possible meanings | What to check |
|---|---|---|
| High CTR, low completion | Asset stops scroll or prompts action but does not hold attention; or short asset vs long asset | Duration, placement, quartile curve, whether completion was a goal |
| High engagement, low CTR | Content entertains but does not move intent; or placement favours engagement | Engagement type, link click definition, landing traffic |
| Cheap reach, low attention | Low-cost inventory; viewability or attention trade-off | Placement mix, viewability, completion |
| CPM up, CTR up | Different, more selective audience or premium inventory | Audience and placement mix |
| CTR down over time | Fatigue, delivery shift to cheaper inventory, audience expansion, seasonality | Frequency trend, CPM trend, placement mix by week |
| Under-delivery vs plan | Price (CPM above plan) or volume (spend below plan) | Decompose impressions ratio into spend ratio x price factor |
| Spend up, results up less | Diminishing returns; or results lag; or seasonality | Elasticity across weeks, marginal cost, timing |
| One asset takes most spend | Algorithm prefers it (predicted performance) or plan intended it | Whether others had enough budget to be judged |

## 4. Creative roles

Assets in one campaign often have different jobs: a bumper for frequency and recall, a 15s for the
message, a 30s+ for story and brand, a static for click-through. Evaluate each against its job, and
evaluate the set for whether the roles are covered. Compare like with like: completion within a
duration band, CTR within a placement.

Quartile curves are diagnostic. An early drop (before 25%) is a hook problem or an autoplay
artefact. A mid-video cliff is usually a content or pacing moment in that asset, which is something
the creative team can act on. A gentle decay is normal.

## 5. Attribution and measurement

- Platform-reported conversions are self-attributed with platform-specific windows and view-through
  rules. They are useful for relative comparison within a platform, not for cross-platform totals.
- Modelled conversions (privacy-driven) are estimates.
- Incrementality is only established by tests: conversion lift, brand lift, geo holdouts, matched
  market tests, MMM. Without one, avoid "drove", "generated" and "delivered" when you mean
  "was credited with".
- Upper-funnel effects (brand search lift, direct traffic) are real but cannot be read from
  platform delivery data alone.

## 6. Turning a finding into an implication

A good implication answers one of these:

- **Allocation:** does this change where the next pound should go, or the case for testing a move?
- **Role:** does it change what we should ask each platform or asset to do?
- **Creative:** does it change what we brief or how we rotate?
- **Measurement:** does it change what we need to measure to know whether it worked?
- **Expectation:** does it change what the client should expect from next flight?

If none applies, the finding may still be worth stating as context, but it is rarely a headline.
