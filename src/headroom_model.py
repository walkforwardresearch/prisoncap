"""Headroom model with capacity endogenous to population (WP4/WP5).

The Annual Statement's Annex B projects places offline for maintenance, fire safety and LTHSE
security work. The IfG observation is that a full estate PREVENTS that work: spaces cannot be taken
out of use when there is nowhere to put the prisoners. So capacity should respond to headroom, with
places brought online when the estate is tight and taken offline when it loosens.

That makes headroom partly self-limiting, and means a projection treating population and capacity
as independent will overstate the benefit of a release tranche.

Step 1 estimates the feedback on the weekly series. Two adjustments are needed first:

  margin steps   Useable operational capacity moves when the operating margin is redefined, with no
                 physical change. The margin history derived from the monthly Total row is applied
                 to reconstruct gross operational capacity (UOC + margin), which is what actually
                 responds to maintenance decisions.
  new prisons    Openings are exogenous supply, not a response to headroom, so weeks containing a
                 known opening or major re-role are flagged from the MoJ change log.

Step 2 projects headroom forward with the estimated feedback plus the announced release schedule.
"""
import sys, warnings
import numpy as np
import pandas as pd

warnings.filterwarnings('ignore')

# Operating margin step function. 2018 onward is derived from the monthly bulletin Total row
# (sum of establishment op cap minus published useable operational capacity). Before that the
# weekly and monthly definitions text states 2,000 places.
MARGIN_STEPS = [
    ('2011-01-01', 2000), ('2020-05-01', 3000), ('2021-12-01', 2750), ('2022-04-01', 2500),
    ('2022-07-01', 2250), ('2022-09-01', 2000), ('2023-03-01', 1950), ('2023-04-01', 1830),
    ('2023-06-01', 1680), ('2023-07-01', 1480), ('2023-09-01', 1340), ('2023-11-01', 1350),
    ('2025-07-01', 1640),
]


def margin_series(dates):
    m = pd.Series(np.nan, index=dates)
    for d, v in MARGIN_STEPS:
        m[m.index >= pd.Timestamp(d)] = v
    return m


def load(weekly_csv):
    w = pd.read_csv(weekly_csv, parse_dates=['date']).sort_values('date').reset_index(drop=True)
    w = w[w.pop_total.notna() & w.uoc_total.notna()].copy()
    w['margin'] = w.operating_margin.fillna(pd.Series(margin_series(pd.DatetimeIndex(w.date)).values, index=w.index))
    w['gross_cap'] = w.uoc_total + w.margin
    w['headroom'] = w.uoc_total - w.pop_total
    return w


def estimate(w, h=13, openings=None):
    """Regress the h-week change in gross capacity on headroom h weeks earlier."""
    d = w.set_index('date')[['gross_cap', 'headroom', 'pop_total']].asfreq('7D').interpolate(limit=3)
    d['d_cap'] = d.gross_cap.diff(h)
    d['headroom_lag'] = d.headroom.shift(h)
    d['d_pop'] = d.pop_total.diff(h)
    d['open_flag'] = 0
    if openings is not None:
        for t in openings:
            d.loc[(d.index >= t - pd.Timedelta(weeks=h)) & (d.index <= t + pd.Timedelta(weeks=h)), 'open_flag'] = 1
    d = d.dropna(subset=['d_cap', 'headroom_lag'])
    ex = d[d.open_flag == 0]

    def fit(frame, cols):
        X = frame[cols].copy(); X['const'] = 1.0
        y = frame.d_cap.values
        b, *_ = np.linalg.lstsq(X.values, y, rcond=None)
        res = y - X.values @ b
        n, k = X.shape
        se = np.sqrt(np.diag((res ** 2).sum() / (n - k) * np.linalg.inv(X.values.T @ X.values)))
        r2 = 1 - (res ** 2).sum() / ((y - y.mean()) ** 2).sum()
        return dict(zip(list(cols) + ['const'], b)), dict(zip(list(cols) + ['const'], se)), r2, n

    print(f'\nCapacity feedback, {h}-week changes (weeks near a prison opening excluded: '
          f'{len(d) - len(ex)} of {len(d)})')
    for label, frame in [('all weeks', d), ('excluding openings', ex)]:
        b, se, r2, n = fit(frame, ['headroom_lag'])
        print(f'  {label:20s} d_cap = {b["const"]:+7.0f} {b["headroom_lag"]:+.3f} * headroom(t-{h})   '
              f't={b["headroom_lag"] / se["headroom_lag"]:+5.2f}  R2={r2:.3f}  n={n}')
    b, se, r2, n = fit(ex, ['headroom_lag', 'd_pop'])
    print(f'  with d_pop control:  headroom {b["headroom_lag"]:+.3f} (t={b["headroom_lag"] / se["headroom_lag"]:+.2f}), '
          f'd_pop {b["d_pop"]:+.3f} (t={b["d_pop"] / se["d_pop"]:+.2f}), R2={r2:.3f}')

    b, se, r2, n = fit(ex, ['headroom_lag'])
    return b['headroom_lag'] / h, b['const'] / h, r2      # per-week coefficients


def project(w, beta, alpha, events_csv, weeks_out=95, pop_slope=143.0, label=''):
    ev = pd.read_csv(events_csv, parse_dates=['date'])
    rel = ev[ev.population_effect != 0][['date', 'population_effect']]
    last = w.iloc[-1]
    dates = pd.date_range(last.date, periods=weeks_out, freq='7D')
    pop, cap, margin = last.pop_total, last.uoc_total + last.margin, last.margin
    rows = []
    for i, dt in enumerate(dates):
        if i > 0:
            pop += pop_slope
            step = rel[(rel.date > dates[i - 1]) & (rel.date <= dt)].population_effect.sum()
            pop += step
            hr_prev = rows[-1]['headroom']
            cap += alpha + beta * hr_prev          # capacity responds to last period's headroom
        rows.append({'date': dt, 'pop': pop, 'gross_cap': cap, 'uoc': cap - margin,
                     'headroom': cap - margin - pop})
    r = pd.DataFrame(rows)
    r['scenario'] = label
    return r


def main(weekly_csv, events_csv, changelog_csv, outdir):
    w = load(weekly_csv)
    print(f'weekly series {w.date.min():%Y-%m-%d} to {w.date.max():%Y-%m-%d}, n={len(w)}')

    ch = pd.read_csv(changelog_csv)
    ch = ch[ch.year >= 2011]
    openings = pd.to_datetime(dict(year=ch.year.astype(int),
                                   month=ch.month.map({m: i for i, m in enumerate(
                                       ['January', 'February', 'March', 'April', 'May', 'June', 'July',
                                        'August', 'September', 'October', 'November', 'December'], 1)}).fillna(6).astype(int),
                                   day=1)).tolist()

    beta, alpha, r2 = estimate(w, 13, openings)
    print(f'\nadopted per-week feedback: d_cap = {alpha:+.1f} {beta:+.4f} * headroom')
    print(f'  implied equilibrium headroom (where capacity is stable): {-alpha / beta:,.0f}')

    base = w.iloc[-1]
    print(f"\ncurrent: {base.date:%d %b %Y}  population {base.pop_total:,.0f}  UOC {base.uoc_total:,.0f}  "
          f"headroom {base.headroom:,.0f}  margin {base.margin:,.0f}")

    runs = []
    for lab, slope in [('central pop +143/wk', 143.0), ('slower pop +85/wk', 85.0), ('faster pop +180/wk', 180.0)]:
        r = project(w, beta, alpha, events_csv, pop_slope=slope, label=lab)
        runs.append(r)
        trig = r[r.headroom <= 557]; zero = r[r.headroom <= 0]; band = r[r.headroom <= 1671]
        print(f'  {lab:22s} min headroom {r.headroom.min():6.0f} on {r.loc[r.headroom.idxmin(), "date"]:%d %b %y} | '
              f'trigger band {band.date.min():%d %b %y} | <=557 {trig.date.min():%d %b %y}' if len(trig) else
              f'  {lab:22s} min headroom {r.headroom.min():6.0f} on {r.loc[r.headroom.idxmin(), "date"]:%d %b %y} | '
              f'trigger band {band.date.min():%d %b %y} | <=557 never')
    R = pd.concat(runs, ignore_index=True)
    R.round(0).to_csv(f'{outdir}/headroom_projection_endogenous.csv', index=False)

    c = runs[0]
    print('\ncentral path (endogenous capacity):')
    for d in ['2026-09-28', '2026-10-19', '2026-11-16', '2026-12-14', '2027-01-18', '2027-03-15', '2027-05-31']:
        row = c[c.date <= d].tail(1)
        if len(row):
            print(f"  {row.date.dt.date.iloc[0]}  pop {row['pop'].iloc[0]:,.0f}  UOC {row.uoc.iloc[0]:,.0f}  "
                  f"headroom {row.headroom.iloc[0]:,.0f}")
    return w, R


if __name__ == '__main__':
    main(sys.argv[1], sys.argv[2], sys.argv[3], sys.argv[4])
