# Pre-registration: prison headroom, England and Wales

Walkforward Research · open bench track · written 5 September 2026, before the first scoring event

*Target, metric, baselines and horizon written down first. The bar is set while it can still be missed.*

Version 1.0. Register file: `forecast_register.csv`, committed alongside this document.

---

## 1. Target

**Headroom** = useable operational capacity minus population, England and Wales prison estate, as published in the Ministry of Justice weekly prison population bulletin for the Monday reference date.

Official outcome. Fixed weekly cadence. Published on gov.uk. No arguing about the result.

## 2. Cadence

- A forecast is posted each Friday after the weekly bulletin publishes, before the next bulletin.
- Bank-holiday weeks with no bulletin are skipped; nothing is interpolated in the archive.
- Each post carries the bulletin it was made from, the posting date, and a point forecast with an 80% interval at each horizon.

## 3. Horizons

4, 13 and 26 weeks ahead, resolved against the bulletin nearest the target date.

## 4. Baselines, named now

1. **Naive:** the last published headroom, carried forward.
2. **Seasonal naive:** the last published headroom plus the mean seasonal change over the horizon from the 2011 to 2026 weekly profile.
3. **Official path**, where a dated point exists: the Annual Statement on Prison Capacity supply-minus-demand figure for the nearest published date.

Every score is reported beside all three. On the weeks a baseline wins, that is stated.

## 5. Metric

Absolute error in prisoners at each horizon; running mean absolute error; share of outcomes inside the 80% interval. Model beats a baseline only if its running MAE is lower over at least 13 resolved forecasts.

## 6. Model, and how it may change

Version 3 as of this document: annual seasonal profile, capacity endogenous to population, dated release tranches from a hand-maintained policy file. Any change produces a new version column. **No past forecast is ever edited.** Superseded versions stay in the archive and keep being scored until their horizons resolve.

## 7. Stated expectation, in advance

Walk-forward testing on 2016 to 2026 says a model beats the naive forecast by 2 to 3% at 13 weeks. The honest expectation is that this track will show a small edge at short horizons and none at 26 weeks, and that the two shock levers not in the model (recall of early-release cohorts; the 56-day fixed-term recall) will produce an optimistic bias from about November 2026. If that happens the archive will say so.

## 8. Forecasts already lodged

From the 24 August 2026 bulletin (headroom 2,094), lodged 3 September 2026, baselines and intervals added 6 September before any scoring event.

| Target | Weeks | Naive | Seasonal naive | Official | v1 | v2 | v3 | v3 80% interval |
|---|---|---|---|---|---|---|---|---|
| 2026-09-28 | 5 | 2,094 | 2,025 |  | 1,139 | 1,183 | **2,076** | 1,505 to 2,672 |
| 2026-10-26 | 9 | 2,094 | 1,927 |  | 1,725 | 1,975 | **3,170** | 2,414 to 3,869 |
| 2026-11-30 | 14 | 2,094 | 2,069 | 1,499 | 1,420 | 1,912 | **3,509** | 2,655 to 4,392 |
| 2026-12-28 | 18 | 2,094 | 2,728 |  | 1,206 | 1,827 | **4,226** | 3,280 to 5,255 |
| 2027-01-25 | 22 | 2,094 | 2,548 |  | 1,042 | 1,867 | **4,210** | 3,197 to 5,499 |
| 2027-03-01 | 27 | 2,094 | 2,165 |  | 587 | 1,687 | **3,957** | 2,936 to 5,210 |
| 2027-03-29 | 31 | 2,094 | 2,289 |  | 23 | 1,442 | **4,109** | 3,032 to 5,445 |
| 2027-05-31 | 40 | 2,094 | 2,515 | 2,099 | -1,496 | 735 | **4,048** | 2,864 to 5,456 |

The 80% interval is the v3 point forecast plus the 10th and 90th percentiles of the historical no-change forecast error at that horizon, 2016 to 2026. It is deliberately a baseline-derived interval, not a model-derived one: if v3 is no better than naive, its interval will be honestly wide. The official baseline is the Annual Statement 2025 adult-estate supply less demand, plus the YCS headroom at the base date (99), and exists only where the Statement publishes a dated point.

v1 and v2 are retained as superseded columns and will be scored alongside v3. First scoring event: the bulletin for 28 September 2026.

## 9. Second product on the same track: official forecasts, scored

The Ministry of Justice publishes an annual prison population projection. Each edition is scored on publication day against the same naive baseline, at every horizon, and added to a running record covering all editions since 2008. This is the harness pointed at an institution rather than at ourselves. Next edition expected December 2026.

## 10. Exit rule

The track is dropped, without shame, if forecasts go unposted for four consecutive bulletin weeks, or if the MoJ stops publishing the weekly bulletin. Whatever has been scored by then stays in the archive.

## 11. Cost

One script, `refresh.sh`, run after each bulletin. A few minutes a week. The research that found the target is done and lives in the repository; the track is only what is in this document.

---

*Analysis produced alongside this track (the composition of the prison population, the justice-held population series, the capacity feedback estimate) is measurement, not forecasting. It is published under Notes, labelled as such, and makes no claim the archive supports.*
