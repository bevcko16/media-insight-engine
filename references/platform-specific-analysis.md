# Platform-specific analysis

Definitions and behaviours change. Everything below reflects public platform documentation as
generally understood at the time of writing (reviewed November 2026). When a conclusion depends on
an exact definition, confirm it in the platform's current help centre or with the client's
platform reps, and say in the report which definition you used. Record confirmed definitions in
`knowledge/<client>/terminology.md`.

## Meta (Facebook, Instagram, Messenger, Audience Network)

- **Video views**: "3-second video plays" (or 2 continuous seconds in some reports); **ThruPlay**
  is 15 seconds or completion if shorter. Completion metrics are video plays at 25/50/75/95/100%.
- **Clicks**: "Clicks (all)" includes profile, likes, expands; "Link clicks" is the usual CTR
  numerator. Confirm which the file uses.
- **Reach**: deduplicated within the reporting level selected. Ad-set reach does not sum to campaign
  reach. Newer reports may show Accounts Center accounts reach.
- **Results**: depends on the optimisation event. Not comparable across ad sets with different
  goals.
- **Attribution**: default is commonly 7-day click and 1-day view for conversion campaigns.
  Modelled conversions are included for some users.
- **Behaviours**: Advantage+ placements and budget allocation move delivery to cheaper inventory
  (Reels, Stories, Audience Network) unless constrained; learning phase after significant edits.

## TikTok

- **Video views** reported at 2 seconds and 6 seconds; **focused view** (6s or engagement) is the
  basis for some buying. Quartile plays and average watch time are available.
- **Engagement** is high relative to other platforms by nature of the feed; do not read high
  engagement rate as intent without click or onsite evidence.
- Creative fatigue in TikTok is often faster than on other platforms; but test for it with
  frequency and delivery data before saying so.

## Pinterest

- **Video views** commonly 2 seconds with at least 50% in view. Saves and outbound clicks are the
  distinctive signals. Users are often in planning mode; long consideration windows.
- **Outbound clicks** vs **pin clicks**: confirm which the file uses.

## YouTube (Google Ads and DV360)

- **Skippable in-stream view**: 30 seconds (or full ad if shorter) or an interaction; views and view
  rate are therefore not comparable with social 2-3s views.
- Bumpers (6s, non-skippable) are bought on CPM; completion is near-structural.
- **Reach planning** and **unique users** are modelled in places.
- Shorts, in-feed and CTV placements behave very differently on CTR and completion.

## Google Ads (Search, Performance Max, Demand Gen, Display)

- Search CTR and CPC reflect intent and keyword mix; not comparable with social CTR.
- Performance Max blends inventory and hides much of the placement detail; attribution includes
  conversions a brand search would have captured.
- Conversion window defaults are longer than social; view-through conversions are separate.

## DV360 and programmatic

- Exchange, deal and inventory source mix drive CPM and viewability. Open exchange is cheaper and
  noisier; PMP and programmatic guaranteed cost more for quality and control.
- Viewability (MRC standard: 50% of pixels for 1 second for display, 2 seconds for video) and
  invalid traffic should be read alongside CTR.
- CTR on display is low by nature; judge display on reach, viewability and attention if those are
  the objectives.

## LinkedIn

- High CPMs and CPCs reflect professional targeting; judge on lead quality where available.
- Video views are typically 2 seconds at 50% in view. Engagement includes social actions and
  clicks; confirm the CTR numerator.

## Cross-platform rules

1. Compare platforms on **the job each was bought for**, not on a single metric.
2. Do not rank platforms on view rate, CPV or "video views" unless definitions are aligned.
3. Do not sum platform-reported conversions as a deduplicated total.
4. Do not sum reach across platforms; say "combined platform reach (not deduplicated)".
5. Where platforms play complementary roles (one cheap reach, one attention, one action), describe
   the system they form rather than ranking them.
