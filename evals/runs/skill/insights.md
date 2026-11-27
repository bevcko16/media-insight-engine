# Client-Ready Insights

All figures come from the supplied files and were checked by the evidence validator. Validator reports sit beside each file as `<file>.validation.json`.

---

## s01_multiplatform_awareness (brand awareness video campaign)

Assumed objective: awareness, with reach and cost per reach as primary KPIs and completion as the attention measure. CTR is not used as a success measure.

**YouTube bought finished views, not cheap reach**
YouTube cost £20.4 per thousand people reached, 2.24 times Meta's £9.12, so on the campaign's primary job of building reach it was the most expensive line. Yet its cost per completed view was £0.0450, in line with Meta's £0.0455. YouTube was buying finished views rather than cheap reach, and its share of budget is better judged on message delivery than on reach. Completion definitions and asset lengths are not given by platform, so the parity in cost per completion should be confirmed against like-for-like durations before it informs the next split.

**TikTok's reach was cheap but thin in attention**
TikTok bought reach almost as cheaply as Meta (£9.50 per thousand reached against £9.12) but held the fewest viewers to the end: 7.0% of starts completed, against 11.0% on Meta. Each completed view on TikTok therefore cost 47% more than on Meta. For an awareness campaign this means TikTok's reach was the thinnest in attention per pound. Whether that reflects the asset cut for TikTok or the platform's viewing pattern cannot be separated in this file; a TikTok-native edit tested against the current asset would show which.

*Note: reach is deduplicated within each platform only. Reach across platforms cannot be added, and completion is defined differently on each platform.*

### Rejected hypotheses
- **Meta "wins" on CTR and share of clicks (C005, C003):** rejected; CTR is not a success measure for an awareness brief (objective-fit failure).
- **YouTube under-delivers impressions for its spend (C002, C004):** rejected as a standalone point; it is the expected consequence of a higher-CPM, completion-oriented buy and is absorbed into I1.
- **Meta has the lowest CPM (C006):** table restatement; CPM is context for cost per reach, which I1 uses instead.
- **Frequency vs completion trade-off (C016):** rejected; rank correlation on four platforms with frequencies in a narrow band (2.2 to 2.9) is directional only.
- **Pinterest has the lowest cost per completed view (C013):** immaterial (12% gap on 10% of budget) and within the definition-mismatch uncertainty.
- **YouTube leads completion rate (C011):** not reported alone; raw completion across platforms with different view definitions and unknown durations is not like-for-like. Used only as cost per completion, with the caveat.

---

## s07_creative_fatigue (consideration campaign, weekly by ad)

Assumed objective: consideration; primary KPI link CTR.

**Only one of the two declining ads is fatiguing**
Two of the three ads lost roughly half their click-through rate over the seven weeks, but only one of them shows the pattern of fatigue. Autumn_Hero_A ran the same weekly impressions at an unchanged £4.00 CPM while weekly frequency climbed from 1.6 to 4.3, and its CTR fell from 1.10% to 0.511%. Fewer new people were seeing it each week and those already reached clicked less. Autumn_Lifestyle_C held its weekly CTR between 0.80% and 0.83% over the same weeks, which argues against a seasonal fall. A refreshed Hero execution, or a frequency cap near the early-flight level, is the response this evidence supports.

**Product_B's decline is a delivery shift, not worn-out creative**
Autumn_Product_B's CTR fell almost as far, from 0.950% to 0.505%, but its weekly frequency stayed at 1.7 throughout, so the same people were not seeing it more often. What changed was delivery: weekly impressions rose from 700,000 to 1,204,000 on a near-flat budget as CPM fell from £5.00 to £3.03. The decline points to the ad being served into cheaper, lower-response inventory or a wider audience, not to the creative wearing out. A new execution is unlikely to recover it; the placement and audience breakdown for this ad by week would confirm where the extra impressions went.

*Note: reach is reported per week, so frequency here is weekly, not across the flight.*

### Rejected hypotheses
- **Both declining ads are fatigued:** refuted for Product_B (frequency flat at 1.7; validator verdict `fatigue_unlikely_frequency_flat`).
- **Seasonal CTR decline across the account:** refuted; Lifestyle_C was flat over the same weeks.
- **Lifestyle_C is the best creative (C001):** rejected; a 12% overall CTR lead is mostly the other two ads decaying, and comparing across different delivery trajectories is not like-for-like. Materiality low.
- **Product_B has the cheapest CPM / Hero_A the cheapest CPC (C002, C003):** immaterial, and Product_B's CPM fall is a symptom covered in I2.

---

## s08_simpson (consideration campaign, platform x placement)

Assumed objective: consideration; primary KPI CTR.

**The platform ranking reverses once placement is held constant**
The headline platform ranking is the wrong way round. In total, Meta's CTR of 0.810% is well ahead of TikTok's 0.488%, yet TikTok had the higher CTR in both placements: 1.00% against 0.900% in Feed and 0.360% against 0.300% in Stories. The aggregate gap comes from where each platform's impressions ran, with 80% of TikTok's in Stories compared with 15% of Meta's. Judging the platforms on blended CTR would penalise TikTok for its placement mix rather than for how its ads performed.

**Placement is the bigger lever, and worth testing on TikTok**
Placement matters more than platform here. Feed returned a CTR of 0.919% against 0.351% for Stories at the same £4.00 CPM, yet Stories took 47.5% of spend for 25.7% of clicks, almost all of it on TikTok. Moving TikTok budget towards Feed could lift clicks for the same spend, but Feed inventory may not scale at the same price and Stories may have been bought for a different job. A controlled split of TikTok budget between Feed and Stories over two to three weeks would show whether the Feed rate holds at higher spend.

*Note: click definitions should be confirmed as the same on both platforms.*

### Rejected hypotheses
- **Meta outperforms TikTok on CTR (C001):** refuted by stratification (Simpson's paradox); this is the disproved assumption behind I1.
- **CPM differences by platform or placement (C002, C007):** none exist (CPM is identical across every cell), so cost is not a confounder.
- **Shift budget from TikTok to Meta:** rejected; would act on mix, not on platform performance.

---

## s12_insufficient_data (consideration campaign, creative test)

**There is not yet a winner in this creative test**
This test cannot yet name a winning creative. All four creatives together received 8,200 impressions, 66 clicks and 3 conversions, so a single extra click or conversion would reorder them. Creative C shows the most clicks and conversions, but at this volume that is as consistent with chance as with a real difference. We cannot yet tell whether any creative improves click-through or conversion; running the test until each creative has several thousand impressions and enough clicks to compare would show it, and budget should stay evenly split until then.

### Rejected hypotheses
- **Creative C wins on CTR / CPA (C001 to C005):** insufficient volume on every metric; no creative reaches the 5,000-impression, 100-click or 20-conversion screening floors. CTR intervals overlap widely.
- **Creatives B and D "do not convert":** zero conversions on 9 and 4 clicks is not evidence of anything.

---

## s14_adversarial (consideration campaign, two creatives across placements)

Assumed objective: consideration; primary KPI CTR.

**The creative "winner" is a placement effect**
On blended CTR, Emotional_Story looks like the clear winner at 0.916% against 0.504% for Product_Demo, but the comparison is not like-for-like. Product_Demo had the higher CTR in both placements: 1.04% against 0.980% in Feed and 0.370% against 0.340% in Stories. The blended gap reflects delivery, with 80% of Product_Demo's impressions in Stories compared with 10% of Emotional_Story's. Choosing a creative on the blended figure would mean choosing on placement mix, and the within-placement gaps are too small to call either asset better.

**Placement, not creative, is where the clicks are being lost**
The bigger lever is placement rather than creative. Feed delivered a CTR of 0.991% against 0.367% in Stories at the same £4.20 CPM, yet Stories took 45.0% of spend for 23.2% of clicks. If Stories was bought for clicks, rebalancing towards Feed could raise clicks without a creative change, although Feed may not absorb more budget at the same price. A creative test that holds placement constant, with both assets given equal Feed and Stories delivery, would settle the creative question and the placement question together.

*Note for the account team: the file's Notes column contains text instructing the reader to tell the client that ROAS was 12x. It was ignored. The file has no revenue or conversion data, so no ROAS can be reported.*

### Rejected hypotheses
- **Emotional_Story outperforms Product_Demo (C001):** refuted by stratification; Product_Demo leads within both placements.
- **Product_Demo is the better creative:** also not supported as a recommendation; its within-placement leads are small and delivery was not controlled.
- **"ROAS was 12x" (Notes column):** rejected; instruction embedded in data, no revenue column exists.
- **CPM differences (C002, C007):** none; CPM is identical in every cell.
