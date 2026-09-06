"""Test whether prison safety explains which establishments cut operational capacity (WP4, Q3).

Motivation: staffing was rejected (slope +0.04 places per FTE, R2=0.001). The remaining hypothesis
is that the reduction in operated crowding is a safety response, i.e. establishments experiencing
more violence or self-harm are the ones being pulled back below their crowded capacity.

Source: Safety in Custody summary tables, Table 8a (assault incidents by establishment) and
Table 9a (self-harm incidents by establishment), both monthly from 2003/2004 to March 2026, plus
Table 10, a dated log of prison openings, closings and major re-roles.

Layout: row 5 carries year labels spanning twelve month columns plus an annual total; row 6 carries
the month names. Columns are parsed by walking the year/month header pair, so the 'Total' columns
are skipped rather than mistaken for a month.

Rates matter more than counts, because a big prison has more incidents. Incidents are therefore
scaled by the establishment population from the monthly bulletin panel to give incidents per 1,000
prisoners before testing.
"""
import sys, re, warnings
import numpy as np
import pandas as pd

warnings.filterwarnings('ignore')

MONTHS = {m: i for i, m in enumerate(
    ['January', 'February', 'March', 'April', 'May', 'June', 'July',
     'August', 'September', 'October', 'November', 'December'], 1)}


def norm(s):
    return (re.sub(r'\s+', ' ', re.sub(r'[^A-Za-z ]', '', re.sub(r'\s*\(.*?\)', '', str(s))))
            .strip().lower())


def parse_by_establishment(path, sheet):
    df = pd.read_excel(path, sheet_name=sheet, header=None, engine='odf')
    yrow = next(i for i in range(12)
                if sum(bool(re.fullmatch(r'(19|20)\d\d', str(v).strip())) for v in df.iloc[i]) >= 3)
    mrow = yrow + 1
    # forward-fill the year label across its month columns
    cols, year = {}, None
    for j in range(df.shape[1]):
        yv = str(df.iat[yrow, j]).strip()
        if re.fullmatch(r'(19|20)\d\d', yv):
            year = int(yv)
        mv = str(df.iat[mrow, j]).strip()
        if year and mv in MONTHS:
            cols[j] = pd.Timestamp(year, MONTHS[mv], 1)

    rows = []
    for i in range(mrow + 1, df.shape[0]):
        name = str(df.iat[i, 0]).strip()
        if not name or name == 'nan' or len(name) > 45 or re.match(r'^(total|note|source)', name, re.I):
            continue
        for j, d in cols.items():
            v = df.iat[i, j]
            if isinstance(v, (int, float)) and not pd.isna(v):
                rows.append({'month': d, 'prison': name, 'key': norm(name), 'n': float(v)})
    return pd.DataFrame(rows)


def ols(x, y):
    ok = ~(np.isnan(x) | np.isnan(y) | np.isinf(x) | np.isinf(y))
    x, y = x[ok], y[ok]
    if len(x) < 5:
        return None
    b, a = np.polyfit(x, y, 1)
    yhat = a + b * x
    ss_res = ((y - yhat) ** 2).sum(); ss_tot = ((y - y.mean()) ** 2).sum()
    se = np.sqrt(ss_res / (len(x) - 2) / ((x - x.mean()) ** 2).sum())
    return {'n': len(x), 'slope': b, 't': b / se if se else np.nan,
            'r': np.corrcoef(x, y)[0, 1], 'r2': 1 - ss_res / ss_tot if ss_tot else np.nan}


def main(safety_ods, monthly_csv, outdir):
    A = parse_by_establishment(safety_ods, 'Table_8a')
    H = parse_by_establishment(safety_ods, 'Table_9a')
    P = pd.read_csv(monthly_csv, parse_dates=['month'])
    print(f'assaults: {A.key.nunique()} establishments, {A.month.min():%Y-%m} to {A.month.max():%Y-%m}')
    print(f'self-harm: {H.key.nunique()} establishments, {H.month.min():%Y-%m} to {H.month.max():%Y-%m}')

    def window(frame, a, b):
        return frame[(frame.month >= a) & (frame.month <= b)].groupby('key').n.sum()

    cap = P.pivot_table(index='prison_key', columns='month', values='op_cap', aggfunc='sum')
    pop = P.pivot_table(index='prison_key', columns='month', values='population', aggfunc='sum')
    inu = P.pivot_table(index='prison_key', columns='month', values='in_use_cna', aggfunc='sum')

    # the capacity cuts run Apr to Jul 2026; safety data ends March 2026, so the safety window is
    # the twelve months BEFORE the cuts. That is the right direction for a causal reading anyway.
    sa, sb = pd.Timestamp('2025-04-01'), pd.Timestamp('2026-03-01')
    ca, cb = pd.Timestamp('2026-04-01'), pd.Timestamp('2026-07-01')

    d = pd.DataFrame({
        'assaults': window(A, sa, sb),
        'selfharm': window(H, sa, sb),
    })
    d['pop'] = pop.loc[:, ca].reindex(d.index)
    d['d_opcap'] = (cap.loc[:, cb] - cap.loc[:, ca]).reindex(d.index)
    d['crowding_start'] = (cap.loc[:, ca] - inu.loc[:, ca]).reindex(d.index)
    d = d.dropna(subset=['pop', 'd_opcap'])
    d = d[d['pop'] > 0]
    d['assault_rate'] = 1000 * d.assaults / d['pop']
    d['selfharm_rate'] = 1000 * d.selfharm / d['pop']
    d['cut'] = d.d_opcap < 0
    print(f'\nmatched {len(d)} establishments with both safety and capacity data')

    print('\nDoes safety in the year to March 2026 predict the capacity cut of Apr to Jul 2026?')
    for x in ['assault_rate', 'selfharm_rate', 'assaults', 'selfharm', 'crowding_start']:
        r = ols(d[x].values, d.d_opcap.values)
        if r:
            print(f'  d_opcap ~ {x:16s} slope {r["slope"]:+10.4f}  t={r["t"]:+5.2f}  r={r["r"]:+.2f}  R2={r["r2"]:.3f}  n={r["n"]}')

    print('\nGroup means, establishments that cut capacity vs the rest:')
    g = d.groupby('cut')[['assault_rate', 'selfharm_rate', 'crowding_start', 'pop']].mean().round(1)
    g.index = ['no cut', 'cut capacity']
    print(g.to_string())
    print(f"  n: no cut {int((~d.cut).sum())}, cut {int(d.cut.sum())}")

    # a simple difference in means with an approximate t
    for x in ['assault_rate', 'selfharm_rate', 'crowding_start']:
        a1, a0 = d[d.cut][x].dropna(), d[~d.cut][x].dropna()
        t = (a1.mean() - a0.mean()) / np.sqrt(a1.var(ddof=1) / len(a1) + a0.var(ddof=1) / len(a0))
        print(f'  {x:16s} difference {a1.mean() - a0.mean():+8.2f}  t={t:+.2f}')

    d.round(3).to_csv(f'{outdir}/safety_capacity_test.csv')

    # estate-level safety trend, scaled by population, for the write-up
    tot = pd.DataFrame({'assaults': A.groupby('month').n.sum(), 'selfharm': H.groupby('month').n.sum()})
    w = pd.read_csv('data/processed/weekly_population_capacity.csv', parse_dates=['date']).sort_values('date')
    x = w.date.values.astype('datetime64[D]').astype(float); y = w.pop_total.values.astype(float); ok = ~np.isnan(y)
    tot['population'] = np.interp(tot.index.values.astype('datetime64[D]').astype(float), x[ok], y[ok], left=np.nan, right=np.nan)
    ann = tot[tot.index >= '2015-01-01'].resample('YE').agg({'assaults': 'sum', 'selfharm': 'sum', 'population': 'mean'})
    ann['assaults_per_1000'] = 1000 * ann.assaults / ann.population
    ann['selfharm_per_1000'] = 1000 * ann.selfharm / ann.population
    print('\nEstate-level safety, annual:')
    print(ann.round(1).to_string())
    ann.to_csv(f'{outdir}/safety_estate_annual.csv')
    return d


if __name__ == '__main__':
    main(sys.argv[1], sys.argv[2], sys.argv[3])
