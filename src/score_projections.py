"""Score the MoJ central projections against outturn (WP2, Q1 part a).

Outturn comes from the weekly bulletin series, interpolated to each projection reference date.

Definitional care: the projections cover the prison population of England and Wales. The weekly
bulletin total INCLUDES HMPPS-operated Immigration Removal Centres up to about 2022 (pop_irc,
between roughly 100 and 800 people). Where the bulletin publishes the split, pop_prisons is the
prisons-only figure. Several projection editions publish their own base-year actual, which gives a
direct calibration test of which bulletin definition the projections match; that test is run first
and reported, and the better-matching definition is used for scoring.

Benchmark: a forecaster with no model, who at publication simply carries the current population
forward unchanged. That is the fair comparison, because it is available at the same moment with
the same information.

Outputs:
  projection_scorecard.csv         one row per edition x horizon: projected, actual, error
  projection_scorecard_summary.csv error by horizon, and by publication era
"""
import sys
import numpy as np
import pandas as pd


def outturn_series(weekly_csv):
    w = pd.read_csv(weekly_csv, parse_dates=['date']).sort_values('date')
    w = w[w.pop_total.notna()]
    return w


def interp(w, dates, col):
    """Linear interpolation of the weekly series onto arbitrary dates. Returns NaN outside range."""
    x = w.date.values.astype('datetime64[D]').astype(float)
    y = w[col].values.astype(float)
    ok = ~np.isnan(y)
    xd = pd.DatetimeIndex(dates).values.astype('datetime64[D]').astype(float)
    out = np.interp(xd, x[ok], y[ok], left=np.nan, right=np.nan)
    out[(xd < x[ok].min()) | (xd > x[ok].max())] = np.nan
    return out


def main(proj_csv, weekly_csv, outdir):
    L = pd.read_csv(proj_csv, parse_dates=['ref_date'])
    w = outturn_series(weekly_csv)

    # ---- calibration: editions that publish their own base actual
    base = L[(L.horizon_years == 0) & L.total.notna()][['edition', 'ref_date', 'total']].copy()
    base = base.drop_duplicates('edition')
    base['bulletin_total'] = interp(w, base.ref_date, 'pop_total')
    base['bulletin_prisons'] = interp(w, base.ref_date, 'pop_prisons')
    base['diff_total'] = base.total - base.bulletin_total
    base['diff_prisons'] = base.total - base.bulletin_prisons
    print('Calibration: MoJ-published base actual vs weekly bulletin, same date')
    print(base[['edition', 'ref_date', 'total', 'bulletin_total', 'diff_total', 'bulletin_prisons', 'diff_prisons']].round(0).to_string(index=False))
    mt = base.diff_total.abs().mean(); mp = base.diff_prisons.abs().mean()
    use = 'pop_total' if (np.isnan(mp) or mt <= mp) else 'pop_prisons'
    print(f'\nmean |gap| vs pop_total {mt:.0f}, vs pop_prisons {mp:.0f} -> scoring against {use}\n')
    base.round(1).to_csv(f'{outdir}/projection_calibration.csv', index=False)

    # ---- scorecard
    c = L[(L.scenario == 'central') & (L.horizon_years > 0) & L.total.notna()].copy()
    c['actual'] = interp(w, c.ref_date, use)
    c = c[c.actual.notna()].copy()
    c['error'] = c.total - c.actual
    c['pct_error'] = 100 * c.error / c.actual

    # benchmark: population at the edition's own base date, carried forward
    b = base.set_index('edition')
    c['base_date'] = c.edition.map(b.ref_date)
    c['naive'] = interp(w, c.base_date.fillna(c.ref_date), use)
    # editions with no published base actual: use the bulletin value at 30 June of the edition year
    miss = c.base_date.isna()
    if miss.any():
        alt = pd.to_datetime(c.loc[miss, 'edition'].str[:4] + '-06-30')
        c.loc[miss, 'naive'] = interp(w, alt, use)
        c.loc[miss, 'base_date'] = alt.values
    # editions whose base year predates the weekly series take a sourced base from
    # data/manual/base_actuals_pre2011.csv (Population in Custody bulletins, June 2009 and 2010)
    import os
    mp = os.path.join(os.path.dirname(outdir.rstrip('/')), 'data', 'manual', 'base_actuals_pre2011.csv')
    if os.path.exists(mp):
        pre = pd.read_csv(mp)
        for _, r in pre.iterrows():
            m = c.edition == r.edition
            c.loc[m, 'naive'] = r.base_population
            c.loc[m, 'base_date'] = pd.Timestamp(r.base_date)
    c['naive_error'] = c.naive - c.actual

    cols = ['edition', 'horizon_years', 'ref_date', 'total', 'actual', 'error', 'pct_error', 'naive', 'naive_error']
    c[cols].round(1).to_csv(f'{outdir}/projection_scorecard.csv', index=False)

    def agg(g):
        return pd.Series({'n': len(g),
                          'mean_pct_error': g.pct_error.mean(),
                          'MAE': g.error.abs().mean(),
                          'MAPE': g.pct_error.abs().mean(),
                          'pct_too_high': 100 * (g.error > 0).mean(),
                          'naive_MAE': g.naive_error.abs().mean()})

    by_h = c.groupby('horizon_years').apply(agg).reset_index().round(1)
    print('By horizon (central path vs outturn):')
    print(by_h.to_string(index=False))

    c['era'] = np.where(c.edition.str[:4].astype(int) >= 2020, '2020 onward',
               np.where(c.edition.str[:4].astype(int) >= 2015, '2015 to 2019', '2008 to 2014'))
    by_era = c.groupby('era').apply(agg).reset_index().round(1)
    print('\nBy publication era:')
    print(by_era.to_string(index=False))

    by_he = c.groupby(['era', 'horizon_years']).apply(agg).reset_index().round(1)
    pd.concat([by_h.assign(cut='horizon'), by_era.assign(cut='era')], ignore_index=True).to_csv(f'{outdir}/projection_scorecard_summary.csv', index=False)
    by_he.to_csv(f'{outdir}/projection_scorecard_era_horizon.csv', index=False)
    print(f'\nscorecard rows: {len(c)}, editions scored: {c.edition.nunique()}')
    return c


if __name__ == '__main__':
    main(sys.argv[1], sys.argv[2], sys.argv[3])
