"""Headroom projection v3: seasonality, endogenous capacity, dated releases (WP5).

Corrections over v2:

  1. SEASONALITY. The population has a strong and stable annual cycle, amplitude 772 people:
     trough in January (-407 against the 53-week centred mean), peak in November (+365). The
     +143/week slope used in v1 and v2 was fitted over April to August, when the seasonal is
     rising fastest, and roughly half of it was seasonal. Worse, it was being extrapolated from
     late August, i.e. from just before the seasonal peak, so the projection carried a rising
     seasonal forward indefinitely instead of letting it reverse.

  2. UNDERLYING TREND. Once the seasonal is removed, the rise since the April 2026 trough is
     about +20/week, not +143.

  3. CAPACITY FEEDBACK. Retained from v2 but re-estimated on the corrected weekly grid:
     d_cap(13wk) = 627 - 0.284*headroom(t-26) + 0.386*d_pop(13wk).

  4. RELEASE TRANCHES. Dated from data/manual/policy_events_2026.csv.

  What v3 still does NOT contain: any recall feedback. The FTR56 change of 31 March 2026 is a
  known upward pressure of up to +3,570 places that cannot be separated from the seasonal with
  the data available, because the shape of the observed rise (flat to June, then linear) does not
  match a saturating recall stock. The Apr-Jun 2026 OMSQ, due about 29 October, is the first
  release that can settle it. Until then the underlying trend term absorbs whatever FTR56 is
  doing, which is an honest but not a structural treatment.
"""
import sys, json, warnings
import numpy as np
import pandas as pd

sys.path.insert(0, '/home/claude/prisoncap/src')
from weekly_grid import weekly_grid

warnings.filterwarnings('ignore')
H = 13
MARGIN = [('2011-01-01', 2000), ('2020-05-01', 3000), ('2021-12-01', 2750), ('2022-04-01', 2500),
          ('2022-07-01', 2250), ('2022-09-01', 2000), ('2023-03-01', 1950), ('2023-04-01', 1830),
          ('2023-06-01', 1680), ('2023-07-01', 1480), ('2023-09-01', 1340), ('2023-11-01', 1350),
          ('2025-07-01', 1640)]


def load():
    w = pd.read_csv('/home/claude/prisoncap/data/processed/weekly_population_capacity.csv', parse_dates=['date'])
    w = w[w.pop_total.notna() & w.uoc_total.notna()]
    g = weekly_grid(w, ['pop_total', 'uoc_total'])
    m = pd.Series(np.nan, index=g.date)
    for d, v in MARGIN:
        m[m.index >= pd.Timestamp(d)] = v
    g['margin'] = m.values
    g['gross_cap'] = g.uoc_total + g.margin
    g['headroom'] = g.uoc_total - g.pop_total
    return g


def seasonal_profile(g):
    """Week-of-year deviation from a 53-week centred mean, smoothed and re-centred to zero."""
    s = g.set_index('date').copy()
    s['dev'] = s.pop_total - s.pop_total.rolling(53, center=True).mean()
    s['woy'] = s.index.isocalendar().week.astype(int)
    prof = s.dropna(subset=['dev']).groupby('woy').dev.mean()
    prof = prof.reindex(range(1, 54)).interpolate().bfill().ffill()
    # circular smooth then centre
    ext = pd.concat([prof, prof, prof])
    prof = ext.rolling(5, center=True).mean().iloc[len(prof):2 * len(prof)]
    return prof - prof.mean()


def cap_coef(g):
    d = g.copy()
    d['d_cap'] = d.gross_cap.diff(H); d['d_pop'] = d.pop_total.diff(H)
    d['hr26'] = d.headroom.shift(2 * H)
    d = d.dropna(subset=['d_cap', 'd_pop', 'hr26'])
    X = d[['hr26', 'd_pop']].copy(); X['const'] = 1.0
    b, *_ = np.linalg.lstsq(X.values, d.d_cap.values, rcond=None)
    return dict(zip(['hr26', 'd_pop', 'const'], b))


def underlying_trend(g, prof, start='2026-04-20'):
    s = g[g.date >= start].copy()
    s['woy'] = pd.DatetimeIndex(s.date).isocalendar().week.astype(int).values
    s['deseas'] = s.pop_total - s.woy.map(prof).values
    wk = (s.date - s.date.iloc[0]).dt.days / 7
    slope = np.polyfit(wk, s.deseas, 1)[0]
    return slope, s


def project(g, prof, coef, trend, weeks=95, label='', tranche_scale=1.0):
    ev = pd.read_csv('/home/claude/prisoncap/data/manual/policy_events_2026.csv', parse_dates=['date'])
    rel = ev[ev.population_effect != 0][['date', 'population_effect']]
    hist = g.set_index('date')
    dates = pd.date_range(hist.index[-1], periods=weeks, freq='7D')
    margin = hist.margin.iloc[-1]
    woy_now = dates[0].isocalendar().week
    # deseasonalised level at the base date
    base_deseas = hist.pop_total.iloc[-1] - prof.get(woy_now, 0.0)
    pop = list(hist.pop_total.values); cap = list(hist.gross_cap.values); hr = list(hist.headroom.values)
    out, cum_rel = [], 0.0
    for i, dt in enumerate(dates):
        if i > 0:
            cum_rel += rel[(rel.date > dates[i - 1]) & (rel.date <= dt)].population_effect.sum() * tranche_scale
            lvl = base_deseas + trend * i + cum_rel
            pop.append(lvl + prof.get(dt.isocalendar().week, 0.0))
            dpop13 = pop[-1] - pop[-1 - H]
            dcap13 = coef['const'] + coef['hr26'] * hr[-1 - 2 * H] + coef['d_pop'] * dpop13
            cap.append(cap[-1] + dcap13 / H)
            hr.append(cap[-1] - margin - pop[-1])
        out.append({'date': dt, 'pop': pop[-1], 'uoc': cap[-1] - margin, 'headroom': hr[-1]})
    r = pd.DataFrame(out); r['scenario'] = label
    return r


def main():
    g = load()
    prof = seasonal_profile(g)
    coef = cap_coef(g)
    trend, s = underlying_trend(g, prof)
    print(f'seasonal amplitude {prof.max() - prof.min():.0f} (peak wk {prof.idxmax()}, trough wk {prof.idxmin()})')
    print(f'underlying deseasonalised trend since 20 Apr 2026: {trend:+.1f}/week (raw slope was +45 to +143 depending on window)')
    print(f'capacity feedback: {coef["const"]:+.0f} {coef["hr26"]:+.3f}*headroom(t-26) {coef["d_pop"]:+.3f}*d_pop')
    base = g.iloc[-1]
    print(f'base {base.date:%d %b %Y}: pop {base.pop_total:,.0f} UOC {base.uoc_total:,.0f} headroom {base.headroom:,.0f}\n')

    runs = []
    for lab, tr, sc in [('central (trend +20/wk)', trend, 1.0),
                        ('no underlying trend', 0.0, 1.0),
                        ('FTR56 still landing (+60/wk)', 60.0, 1.0),
                        ('central, tranches 25% smaller', trend, 0.75)]:
        r = project(g, prof, coef, tr, label=lab, tranche_scale=sc)
        runs.append(r)
        f = lambda x: f'{x.date.min():%d %b %y}' if len(x) else 'never'
        print(f'  {lab:30s} min {r.headroom.min():6.0f} ({r.loc[r.headroom.idxmin(), "date"]:%b %y}) | '
              f'<=1671 {f(r[r.headroom <= 1671])} | <=557 {f(r[r.headroom <= 557])} | <=0 {f(r[r.headroom <= 0])}')
    R = pd.concat(runs, ignore_index=True)
    R.round(0).to_csv('/home/claude/prisoncap/outputs/headroom_projection_v3.csv', index=False)
    c = runs[0]
    print('\ncentral path:')
    for d in ['2026-09-28', '2026-10-26', '2026-11-30', '2026-12-28', '2027-01-25', '2027-03-29', '2027-05-31']:
        row = c[c.date <= d].tail(1)
        if len(row):
            print(f'  {row.date.dt.date.iloc[0]}  pop {row["pop"].iloc[0]:,.0f}  UOC {row.uoc.iloc[0]:,.0f}  headroom {row.headroom.iloc[0]:,.0f}')
    prof.round(0).to_csv('/home/claude/prisoncap/outputs/seasonal_profile.csv')


if __name__ == '__main__':
    main()
