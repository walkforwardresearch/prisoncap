"""Walk-forward benchmarks for the weekly population series (WP3, Q2).

Benchmarks (all use only data available at the forecast origin):
  naive            y[t+h] = y[t]
  drift52          y[t] + h * mean weekly change over the previous 52 weeks
  seasonal_naive   y[t+h-52]                          (same week last year, level ignored)
  seasonal_delta   y[t] + (y[t+h-52] - y[t-52])       (current level plus last year's seasonal change)
  ets              statsmodels ETS (additive trend, damped, 52-week seasonality) refit at every origin
                   -- only if statsmodels is installed; skipped otherwise

Scoring: MAE and RMSE at h = 13, 26, 52 weeks, origins from 2016-01-01 to the last date that still has
an h-week outcome. A regular 7-day grid is built first; the 22 skipped weeks are linearly interpolated
and flagged so they can be excluded from scoring (they are, by default).
"""
import sys
import numpy as np
import pandas as pd

HORIZONS = (13, 26, 52)
TEST_START = pd.Timestamp('2016-01-01')

def regular_grid(s):
    """Insert the skipped weeks so that each step is one bulletin week; interpolate and flag."""
    s = s.sort_values('date').reset_index(drop=True)
    rows = [s.iloc[0].to_dict() | {'interpolated': False}]
    for i in range(1, len(s)):
        prev, cur = s.iloc[i - 1], s.iloc[i]
        gap = (cur.date - prev.date).days
        if gap >= 14:
            n = round(gap / 7) - 1
            for k in range(1, n + 1):
                f = k / (n + 1)
                rows.append({'date': prev.date + pd.Timedelta(days=7 * k), 'pop_total': prev.pop_total + f * (cur.pop_total - prev.pop_total),
                             'uoc_total': prev.uoc_total + f * (cur.uoc_total - prev.uoc_total), 'interpolated': True})
        rows.append(cur.to_dict() | {'interpolated': False})
    g = pd.DataFrame(rows)
    g['t'] = np.arange(len(g))
    return g

def forecasts(y, t, h):
    out = {'naive': y[t]}
    if t >= 52:
        out['drift52'] = y[t] + h * (y[t] - y[t - 52]) / 52
        if t + h - 52 <= t:            # always true for h <= 52
            out['seasonal_naive'] = y[t + h - 52]
            out['seasonal_delta'] = y[t] + (y[t + h - 52] - y[t - 52])
    return out

def run(series_csv, out_csv, use_ets=True):
    s = pd.read_csv(series_csv, parse_dates=['date'])[['date', 'pop_total', 'uoc_total']]
    g = regular_grid(s)
    y = g.pop_total.values
    ets_ok = False
    if use_ets:
        try:
            from statsmodels.tsa.holtwinters import ExponentialSmoothing
            ets_ok = True
        except ImportError:
            print('statsmodels not available; ETS benchmark skipped')
    rows = []
    origins = g[(g.date >= TEST_START) & (~g.interpolated)].t.values
    ets_cache = {}
    for t in origins:
        ets_fc = None
        if ets_ok and t % 4 == 0:   # refit every 4 weeks to keep runtime sane; reuse in between
            try:
                m = ExponentialSmoothing(y[:t + 1], trend='add', damped_trend=True, seasonal='add', seasonal_periods=52).fit(optimized=True)
                ets_cache = {'t': t, 'fc': m.forecast(max(HORIZONS) + 4)}   # +4 covers the refit interval
            except Exception:
                ets_cache = {}
        for h in HORIZONS:
            if t + h >= len(y) or g.interpolated.iloc[t + h]:
                continue
            fc = forecasts(y, t, h)
            if ets_ok and ets_cache.get('fc') is not None:
                off = t - ets_cache['t']
                if off + h - 1 < len(ets_cache['fc']):
                    fc['ets'] = ets_cache['fc'][off + h - 1]
            for name, v in fc.items():
                rows.append({'origin': g.date.iloc[t], 'h': h, 'model': name, 'forecast': v, 'actual': y[t + h], 'err': v - y[t + h]})
    r = pd.DataFrame(rows)
    tab = r.groupby(['h', 'model']).agg(n=('err', 'size'), MAE=('err', lambda e: e.abs().mean()), RMSE=('err', lambda e: np.sqrt((e ** 2).mean())),
                                      bias=('err', 'mean')).reset_index()
    # relative to naive
    naive = tab[tab.model == 'naive'].set_index('h').MAE
    tab['MAE_vs_naive'] = tab.apply(lambda x: x.MAE / naive[x.h], axis=1)
    tab = tab.round(1)
    tab.to_csv(out_csv, index=False)
    r.to_csv(out_csv.replace('.csv', '_all_forecasts.csv'), index=False)
    print(f'origins {len(origins)}, test window {g.date.iloc[origins[0]].date()} to {g.date.iloc[origins[-1]].date()}')
    print(tab.to_string(index=False))
    # same table restricted to origins from 2022 (the crisis era)
    r2 = r[r.origin >= '2022-01-01']
    tab2 = r2.groupby(['h', 'model']).agg(n=('err', 'size'), MAE=('err', lambda e: e.abs().mean()), bias=('err', 'mean')).reset_index().round(1)
    print('\nOrigins from 2022 only:'); print(tab2.to_string(index=False))
    tab2.to_csv(out_csv.replace('.csv', '_from2022.csv'), index=False)

if __name__ == '__main__':
    run(sys.argv[1], sys.argv[2])
