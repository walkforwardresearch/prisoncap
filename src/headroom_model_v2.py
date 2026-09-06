"""Headroom projection with capacity endogenous to population, honest specification (WP5).

Estimated on weekly data 2011-2026 using 13-week changes:

    d_cap(t) = a + b * headroom(t-26) + c * d_pop(t)

Both terms are needed and both survive the obvious robustness checks. The headroom term is lagged
26 weeks so that the capacity level inside headroom is a full 13 weeks clear of the capacity change
on the left, which removes most of the mechanical negative correlation. The population term is
clean by construction (no capacity on the right hand side) and also holds when lagged a further 13
weeks, which gives temporal precedence: past population change predicts future capacity change.

Interpretation: when the estate fills up, places are brought online and maintenance is deferred;
when it empties, deferred work is finally done and places go offline. Roughly 40% of any population
movement is absorbed by capacity moving the same way, so headroom is partly self-limiting and a
release tranche buys less than its face value.

The relationship is far stronger since 2020 (coefficient on d_pop +0.57, R2 0.68) than before
(+0.21, R2 0.06), consistent with capacity being actively managed under crisis conditions.
"""
import sys, warnings
import numpy as np
import pandas as pd

sys.path.insert(0, '/home/claude/prisoncap/src')
from headroom_model import load

warnings.filterwarnings('ignore')
H = 13


def estimate(w, start=None):
    d = w.set_index('date')[['gross_cap', 'headroom', 'pop_total']].asfreq('7D').interpolate(limit=3)
    d['d_cap'] = d.gross_cap.diff(H)
    d['d_pop'] = d.pop_total.diff(H)
    d['hr26'] = d.headroom.shift(2 * H)
    d = d.dropna()
    if start:
        d = d[d.index >= start]
    X = d[['hr26', 'd_pop']].copy(); X['const'] = 1.0
    y = d.d_cap.values
    b, *_ = np.linalg.lstsq(X.values, y, rcond=None)
    r = y - X.values @ b
    n, k = X.shape
    se = np.sqrt(np.diag((r ** 2).sum() / (n - k) * np.linalg.inv(X.values.T @ X.values)))
    r2 = 1 - (r ** 2).sum() / ((y - y.mean()) ** 2).sum()
    return dict(zip(['hr26', 'd_pop', 'const'], b)), dict(zip(['hr26', 'd_pop', 'const'], se)), r2, n


def project(w, coef, events_csv, pop_slope, weeks=95, label=''):
    ev = pd.read_csv(events_csv, parse_dates=['date'])
    rel = ev[ev.population_effect != 0][['date', 'population_effect']]
    hist = (w.set_index('date')[['gross_cap', 'headroom', 'pop_total']]
              .asfreq('7D').interpolate(limit=6).ffill().dropna())
    last = hist.index[-1]
    dates = pd.date_range(last, periods=weeks, freq='7D')
    pop = list(hist.pop_total.values); cap = list(hist.gross_cap.values); hr = list(hist.headroom.values)
    margin = w.iloc[-1].margin
    out = []
    for i, dt in enumerate(dates):
        if i > 0:
            step = rel[(rel.date > dates[i - 1]) & (rel.date <= dt)].population_effect.sum()
            pop.append(pop[-1] + pop_slope + step)
            dpop13 = pop[-1] - pop[-1 - H]
            hr26 = hr[-1 - 2 * H]
            dcap13 = coef['const'] + coef['hr26'] * hr26 + coef['d_pop'] * dpop13
            cap.append(cap[-1] + dcap13 / H)
            hr.append(cap[-1] - margin - pop[-1])
        out.append({'date': dt, 'pop': pop[-1], 'uoc': cap[-1] - margin, 'headroom': cap[-1] - margin - pop[-1]})
    r = pd.DataFrame(out); r['scenario'] = label
    return r


def main():
    w = load('/home/claude/prisoncap/data/processed/weekly_population_capacity.csv')
    for lab, st in [('full sample 2011-2026', None), ('crisis era 2020 onward', '2020-01-01')]:
        b, se, r2, n = estimate(w, st)
        print(f'{lab:24s} d_cap13 = {b["const"]:+7.0f} {b["hr26"]:+.3f}*headroom(t-26) {b["d_pop"]:+.3f}*d_pop13'
              f'   t: {b["hr26"]/se["hr26"]:+.1f}, {b["d_pop"]/se["d_pop"]:+.1f}   R2={r2:.3f}  n={n}')
    coef, se, r2, n = estimate(w)
    eq = -coef['const'] / coef['hr26']
    print(f'\nequilibrium headroom with population flat: {eq:,.0f}')
    print(f'absorption: {coef["d_pop"]:.0%} of any population change is matched by capacity moving the same way')

    base = w.iloc[-1]
    print(f'\nbase: {base.date:%d %b %Y}  pop {base.pop_total:,.0f}  UOC {base.uoc_total:,.0f}  headroom {base.headroom:,.0f}')
    runs = []
    for lab, sl in [('central +143/wk', 143.0), ('slower +85/wk', 85.0), ('faster +180/wk', 180.0)]:
        r = project(w, coef, '/home/claude/prisoncap/data/manual/policy_events_2026.csv', sl, label=lab)
        runs.append(r)
        band = r[r.headroom <= 1671]; trig = r[r.headroom <= 557]; zero = r[r.headroom <= 0]
        f = lambda x: f'{x.date.min():%d %b %y}' if len(x) else 'never'
        print(f'  {lab:16s} min {r.headroom.min():6.0f} ({r.loc[r.headroom.idxmin(),"date"]:%b %y}) | '
              f'trigger band {f(band)} | <=557 {f(trig)} | zero {f(zero)}')
    R = pd.concat(runs, ignore_index=True)
    R.round(0).to_csv('/home/claude/prisoncap/outputs/headroom_projection_v2.csv', index=False)
    c = runs[0]
    print('\ncentral path:')
    for d in ['2026-09-28', '2026-10-19', '2026-11-16', '2026-12-14', '2027-01-18', '2027-03-15', '2027-05-31']:
        row = c[c.date <= d].tail(1)
        if len(row):
            print(f'  {row.date.dt.date.iloc[0]}  pop {row["pop"].iloc[0]:,.0f}  UOC {row.uoc.iloc[0]:,.0f}  headroom {row.headroom.iloc[0]:,.0f}')
    return c


if __name__ == '__main__':
    main()
