# Metric definitions

How the scripts compute each metric (see `DERIVED` in `scripts/mie_common.py`) and the traps.

| Metric | Formula used | Notes and traps |
|---|---|---|
| CTR | clicks / impressions | Which clicks? Link vs all. Search CTR is not social CTR |
| CPM | spend / impressions × 1000 | Driven by placement, audience, season, buying model |
| CPC | spend / clicks | Same click-definition trap as CTR |
| Frequency | impressions / reach | Only valid with deduplicated reach for the same rows. Summed reach gives a lower bound |
| Cost per thousand reached | spend / reach × 1000 | Same reach caveat |
| View rate | video_views / impressions | Definitions of a view differ by platform |
| CPV | spend / video_views | Same caveat; YouTube views ≠ Meta 3s plays |
| Completion rate | completions / video starts | Preferred for asset comparison; needs starts |
| Completion per impression | completions / impressions | Mixes start rate and holding power; useful for cost of attention |
| CPCV | spend / completions | Cost of a completed view |
| Quartile retention | p25/starts, p50/p25, p75/p50, p100/p75 | Locates where viewers are lost |
| Engagement rate | engagements / impressions | Definition of engagement differs by platform |
| CVR | conversions / clicks | View-through conversions inflate it |
| CPA | spend / conversions | Platform-attributed unless stated |
| ROAS | conversion value / spend | Platform-attributed; not incremental |
| Save rate | saves / impressions | Pinterest-specific signal |
| Spend pacing | spend / planned spend | Check plan version and flight dates |
| Impression delivery | impressions / planned impressions | Decompose into spend pacing × CPM effect |

## Base metric mapping

`scripts/mie_common.py` maps common export headers (English and Turkish) to canonical names. If a
header is not mapped it appears in `unmapped_columns`; rename it in a working copy if it is a metric
you need. Where two columns map to the same canonical metric, the first is kept and a
`column_collision` warning is raised: decide which is correct before analysis.

## Video duration and completion

Completion is structurally higher for shorter assets. Do not compare a 6s and a 30s completion
rate as if they measured the same thing. Compare within duration bands, or compare quartile
retention shapes, or compare cost per completed view when the business question is "cost of a
fully delivered message" (and say that is the question).

## Thresholds the scripts use

Minimum denominators for treating a rate as comparable (`MIN_DENOMINATOR`): 5,000 impressions,
100 clicks, 1,000 video starts, 500 video views, 20 conversions, 2,000 reach. These are screening
floors, not standards. Raise them for noisy metrics, or lower them knowingly and say so.
