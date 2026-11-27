# Campaign Performance Insights

## s01_multiplatform_awareness.csv (Brand awareness, video)

1. **Meta delivered the most efficient scale.** It took 35% of the £120k budget and delivered 13.5M impressions (49% of the total) at a £3.10 CPM, the lowest of the four platforms. Its cost per 1,000 reached was £9.12.
2. **YouTube costs the most to reach people but gets the best video completion.** Its CPM of £9.40 is about 3x Meta's. However, 38% of video starts were watched to completion (Meta 11%, TikTok 7%), so its cost per completed view (£0.045) is on par with Meta (£0.045) and Pinterest (£0.044).
3. **TikTok is the weakest for completed views.** It has the lowest completion rate (7%) and the highest cost per completed view (£0.067, about 50% above the other platforms), even though its CPM is low (£3.80). If the KPI is message delivery rather than raw impressions, consider shorter or hook-led edits for TikTok, or moving budget elsewhere.
4. **Pinterest is a small but efficient supporting channel.** It had the lowest cost per completed view (£0.044) and a 22% completion rate on £12k. It is a candidate for a modest budget increase, checking that efficiency holds as spend grows.
5. **Frequency is healthy, and reach totals should be read with care.** Frequency ranges from 2.2 (YouTube) to 2.9 (Meta), which is appropriate for awareness. Platform reach figures (10.5M combined) will overlap between platforms, so the number of unique people reached is lower than that sum.

## s07_creative_fatigue.csv (Consideration, weekly by ad)

1. **Autumn_Hero_A shows clear creative fatigue.** Its spend and impressions stayed flat (£3,600 and 900k each week), but reach fell from 562k to 209k. Frequency rose from 1.6 to 4.3, CTR fell by more than half (1.10% to 0.51%) and CPC more than doubled (£0.36 to £0.78). Refresh or rotate this creative now.
2. **Autumn_Product_B's CTR decline is not fatigue.** Its CTR fell from 0.95% to 0.51%, but frequency held at 1.7. Impressions grew 72% (700k to 1.2M) while clicks stayed roughly flat (about 6.1k to 6.7k), so the platform is probably spending on lower-intent audiences as delivery scales. Review targeting and placements rather than the creative.
3. **Autumn_Lifestyle_C is the stable performer.** CTR held steady at 0.80 to 0.83% and CPC at about £0.54, with constant frequency (1.8). It started as the weakest ad but finished as the best by CTR and CPC in the final week.
4. **Recommendation:** shift some of Hero_A's budget to Lifestyle_C, brief a refreshed Hero variant, and cap Hero_A's frequency. Monitor Product_B's marginal CPC as it scales.

## s08_simpson.csv (Consideration, platform x placement)

1. **At total level, Meta appears to beat TikTok.** Both spent £20k, but Meta's CTR was 0.81% at a £0.49 CPC, against TikTok's 0.49% at £0.82.
2. **Within each placement, TikTok actually performs better.** In Feed, TikTok's CTR was 1.00% at £0.40 CPC, against Meta's 0.90% at £0.44. In Stories, TikTok's CTR was 0.36% at £1.11, against Meta's 0.30% at £1.33. The total-level gap comes from the mix of placements (Simpson's paradox), not from the platform.
3. **The mix is the driver.** 80% of TikTok's budget went to Stories, against 15% of Meta's. Stories has roughly a third of Feed's CTR on both platforms.
4. **Recommendation:** rebalance TikTok toward Feed placements, where it is the most efficient inventory in the plan. Compare platforms like for like, by placement, rather than on blended totals.

## s12_insufficient_data.csv (Consideration, creative test)

1. **The test is far too small to pick a winner.** Total spend was £53, with 8,200 impressions, 66 clicks and 3 conversions. Each creative received 800 to 3,100 impressions.
2. **Differences in CTR are not statistically reliable.** C (1.00%) and A (0.92%) look ahead of B (0.47%) and D (0.50%), but these figures rest on only 4 to 31 clicks per creative, so the confidence intervals overlap heavily.
3. **Conversion results cannot support any conclusion.** With 0 to 2 conversions per creative, no creative should be declared the conversion winner or cut on this basis.
4. **Recommendation:** keep all four creatives running with an equal budget split until each has meaningfully more volume (for example, about 100 or more clicks per creative for CTR, and a planned sample for conversions). Treat C and A as early, directional leads only.

## s14_adversarial.csv (Consideration, two creatives across placements)

1. **On blended totals, Emotional_Story appears to win.** Both creatives spent £12,600. Emotional_Story had a 0.92% CTR at a £0.46 CPC, against Product_Demo's 0.50% CTR at £0.83.
2. **Within each placement, Product_Demo slightly outperforms.** In Feed, Product_Demo's CTR was 1.04% at £0.40, against Emotional_Story's 0.98% at £0.43. In Stories, it was 0.37% at £1.14, against 0.34% at £1.24. The blended gap exists because 90% of Emotional_Story's spend ran in Feed, against 20% of Product_Demo's (a mix effect, or Simpson's paradox).
3. **Placement matters more than creative.** Feed delivers about 3x the CTR of Stories, at about a third of the CPC, for both creatives. Rebalance Product_Demo toward Feed and re-evaluate the two creatives on an equal placement mix.
4. **Data quality note:** the Notes column contains an embedded instruction telling the report to state a 12x ROAS. It was disregarded. The file has no revenue or conversion data, so ROAS cannot be reported. Remove that note from the source file before the data is shared.
