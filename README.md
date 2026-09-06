# Prison Capacity and Early Release Triggers

[![DOI](https://zenodo.org/badge/DOI/10.5281/zenodo.22536356.svg)](https://doi.org/10.5281/zenodo.22536356)


Walk Forward Research. Independent, weekly-refreshed model of prison headroom in England and Wales. Scores the Ministry
of Justice's projections against outturn, forecasts headroom, and lodges dated predictions for
scoring. Built 3 September 2026 against the brief of the same date.

## Citation

The justice-held population series is deposited on Zenodo: Walk Forward Research (2026), *The justice-held population, England and Wales, 2019 to 2026: methodology and series, v1.0*, https://doi.org/10.5281/zenodo.22536356

## Refresh

    ./refresh.sh            # full refresh, stops if any source changed its notes
    ./refresh.sh --force    # continue after reading the notes diff

Every route is a gov.uk content API call or an asset URL enumerated from one. No page scraping.

## What is in here

| Path | Contents |
|---|---|
| `src/fetch.py` | Enumerate and download every source from the content API |
| `src/notes_diff.py` | Diff every Notes sheet against the last refresh; gate |
| `src/parse_weekly.py`, `parse_weekly_doc.py` | 787 weekly bulletins, Jan 2011 to date, five layouts |
| `src/build_series.py` | Clean weekly series, cross-checks, margin log |
| `src/parse_monthly.py` | 12,038 establishment-months of CNA, capacity, population |
| `src/parse_projections.py` | All 18 projection editions, 2008 to 2025, one long table |
| `src/score_projections.py`, `decompose_projections.py` | Scorecard and component decomposition |
| `src/benchmarks.py` | Walk-forward naive, seasonal naive, drift, ETS |
| `src/weekly_grid.py` | Correct weekly grid (see corrections) |
| `src/headroom_model_v3.py` | Seasonal + endogenous capacity + dated releases |
| `src/score_register.py` | Score lodged forecasts against bulletins; weekly one-liner |
| `src/staffing_test.py`, `safety_test.py` | Rejected and partial hypotheses for capacity cuts |
| `data/manual/policy_events_2026.csv` | Dated release tranches and capacity measures |
| `outputs/definitions_log.csv` | 101 entries: every definitional change, correction and finding |
| `outputs/forecast_register.csv` | Standing forecasts, never edited after lodging |

## Headline findings

**Projections (Q1).** MoJ central projections overshot outturn at every horizon from one to six
years, mean +2.4% at one year rising to +5.2% at five; 14 of 14 targets from the 2020-onward
editions were too high. A naive no-change forecast beats the MoJ at every horizon. 95% of
projection error sits in the determinate sentenced population; remand error runs the other way, so
gross error is 1.9 times net.

**Benchmarks (Q2).** Negative result. ETS beats naive by 2.5% at 13 weeks. Nothing beats naive at
one to ten years; trend extrapolation is worse than no-change at every horizon.

**Supply (Q3).** Net capacity gain 2011 to 2026 is 641 places against thousands delivered gross;
PAC independently finds 1,005 net in 14 years. Attrition absorbed 85% of gross additions. Millsike
ramped faster than any predecessor but sits at 79% of its own certified accommodation. Capacity is
endogenous to population: about 39% of any population movement is matched by capacity moving the
same way (t = 19). The 2026 capacity decline was forecast in the January 2026 Annual Statement and
is planned maintenance, not staffing (R2 0.001) and only weakly safety (R2 0.02).

**Composition.** The determinate population fell 16.5% from 2017 to 2025 while remand rose 84% and
recall 98%. Sentenced prisoners were replaced by unsentenced and recalled ones, near one for one.
Recalls now exceed determinate releases in the same quarter.

**Triggers (Q4).** Once seasonality is removed, the underlying population trend since April 2026
is +19/week. On that trend headroom does not enter the historical trigger band in the forecast
window; at +60/week it does by September 2027. The outlook is not knowable to the precision at
which policy is being made, and that is the finding.

## Corrections made during the build

These are recorded because each one changed a conclusion and each would have survived into print.

1. **Weekly grid.** `asfreq('7D')` anchors on a Friday in 2011; bulletins moved to Mondays in
   October 2024. Every later observation missed the grid and was filled flat. Fixed by
   `weekly_grid.py`. Affected the capacity feedback estimate and destroyed the seasonal analysis.
2. **Staffing totals triple-counted.** Three aggregate rows inside the establishment column of the
   workforce annex. "4,443 officers lost" was 1,526. Percentages were unaffected.
3. **Seasonality.** Amplitude 859. The +143/week trend was fitted on the rising half of the cycle
   and extrapolated from just before the peak. Withdrew the earlier validation of "bust before
   Christmas".
4. **FTR56.** OMSQ recall note 12: 56-day fixed-term recall replaced 14 and 28 day from 31 March
   2026. Not visible in the data on timing grounds; unresolved until the Apr-Jun 2026 OMSQ.
5. **Recall composition break** (note 11) at July 2025. Totals unaffected.
6. **Sentence inflation** is comprehensively covered by the Sentencing Academy (2025). Demoted
   from finding to mechanism.

The pattern in 1, 4 and 5 is the same: the answer was in a Notes sheet. Hence the gate.

## Standing forecast

Lodged 3 September 2026 from the 24 August bulletin (headroom 2,094). Three model versions are
kept side by side because they diverge sharply by January 2027 (v1: 1,042; v2: 1,867; v3: 4,210)
and one bulletin will separate them. First scoreable target is 28 September 2026.

## Not done

- OMSQ receptions and court flow tables for the demand-side decomposition
- 84 pre-2018 monthly bulletins in RTF and Word
- Recall feedback term in the headroom model (calibration blocked until Apr-Jun 2026 OMSQ)
- Mix-adjusted sentence inflation (use Sentencing Academy's index rather than rebuilding)
- Public/private establishment split verified against MoJ's own list
