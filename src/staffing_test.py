"""Test whether prison officer staffing explains the fall in operational capacity (WP4, Q3).

Hypothesis: operational capacity is set by what an establishment can safely run, not by what it
physically holds. Since March 2026 the estate has lost about 900 places of operational capacity
while certified accommodation barely moved, so the loss is reduced crowding above CNA. If that is
staffing driven, establishments losing officers should be the ones losing capacity.

Source: HMPPS workforce quarterly, annex 'Prison and Probation Officer staffing levels against
targets', Table 4, which gives prison officer staff in post (FTE), target staffing and the gap by
establishment at eight quarterly dates from March 2023.

The test is cross-sectional: regress the change in operational capacity at each establishment on
the change in officer staff in post over the same window. A within-period cross-section removes
any common time trend, so a positive slope is evidence for the staffing channel rather than a
coincidence of two series both falling.
"""
import sys, re, warnings
import numpy as np
import pandas as pd

warnings.filterwarnings('ignore')


def parse_table4(path, sheet='Table_4_Prison_x_Establishment'):
    df = pd.read_excel(path, sheet_name=sheet, header=None, engine='odf')
    # row carrying the snapshot dates; each date spans a Staff in Post / Target / Difference triplet
    drow = next(i for i in range(min(6, df.shape[0]))
                if sum(isinstance(v, (pd.Timestamp,)) for v in df.iloc[i]) >= 3)
    dates = {j: pd.Timestamp(df.iat[drow, j]) for j in range(df.shape[1])
             if isinstance(df.iat[drow, j], pd.Timestamp)}
    hrow = drow + 1
    rows = []
    for i in range(hrow + 1, df.shape[0]):
        est = str(df.iat[i, 1]).strip()
        # Table 4 carries three aggregate rows inside the establishment column
        # ('All establishments', '... Establishment Total', 'HMPPS HQ and Area Services Total').
        # Counting them triples the estate total, so they are excluded here.
        if not est or est == 'nan' or re.match(r'^\d+\.', est) or len(est) > 45:
            continue
        if re.search(r'\ball establishments\b|\btotal\b', est, re.I):
            continue
        for j, d in dates.items():
            sip = df.iat[i, j] if j < df.shape[1] else None
            tgt = df.iat[i, j + 1] if j + 1 < df.shape[1] else None
            if isinstance(sip, (int, float)) and not pd.isna(sip):
                rows.append({'date': d, 'establishment': est, 'officers_fte': float(sip),
                             'target_fte': float(tgt) if isinstance(tgt, (int, float)) and not pd.isna(tgt) else np.nan})
    S = pd.DataFrame(rows)
    S['gap_fte'] = S.officers_fte - S.target_fte
    S['key'] = (S.establishment.str.replace(r'\s*\(.*?\)', '', regex=True)
                 .str.replace(r'[^A-Za-z ]', '', regex=True)
                 .str.strip().str.lower().str.replace(r'\s+', ' ', regex=True))
    return S


def nearest_month(P, target):
    months = P.month.unique()
    return pd.Timestamp(min(months, key=lambda m: abs((pd.Timestamp(m) - target).days)))


def ols(x, y):
    ok = ~(np.isnan(x) | np.isnan(y))
    x, y = x[ok], y[ok]
    if len(x) < 5:
        return None
    b, a = np.polyfit(x, y, 1)
    yhat = a + b * x
    ss_res = ((y - yhat) ** 2).sum(); ss_tot = ((y - y.mean()) ** 2).sum()
    r2 = 1 - ss_res / ss_tot if ss_tot else np.nan
    se = np.sqrt(ss_res / (len(x) - 2) / ((x - x.mean()) ** 2).sum())
    return {'n': len(x), 'slope': b, 'se': se, 't': b / se if se else np.nan, 'r2': r2,
            'corr': np.corrcoef(x, y)[0, 1]}


def main(workforce_ods, monthly_csv, outdir):
    S = parse_table4(workforce_ods)
    P = pd.read_csv(monthly_csv, parse_dates=['month'])
    print(f'staffing panel: {S.establishment.nunique()} establishments x {S.date.nunique()} dates '
          f'({S.date.min():%b %Y} to {S.date.max():%b %Y})')

    cap = P.pivot_table(index='prison_key', columns='month', values='op_cap', aggfunc='sum')
    cna = P.pivot_table(index='prison_key', columns='month', values='in_use_cna', aggfunc='sum')
    sip = S.pivot_table(index='key', columns='date', values='officers_fte', aggfunc='sum')

    matched = sorted(set(cap.index) & set(sip.index))
    print(f'matched on name: {len(matched)} establishments '
          f'(staffing {len(sip)}, capacity {len(cap)})')

    windows = [('2026-03-31', '2026-06-30', 'Mar to Jun 2026 (the recent fall)'),
               ('2025-06-30', '2026-06-30', 'Jun 2025 to Jun 2026 (twelve months)'),
               ('2025-03-31', '2026-03-31', 'Mar 2025 to Mar 2026 (prior year, placebo)'),
               ('2023-03-31', '2026-06-30', 'Mar 2023 to Jun 2026 (full span)')]
    out = []
    for a, b, label in windows:
        a, b = pd.Timestamp(a), pd.Timestamp(b)
        if a not in sip.columns or b not in sip.columns:
            continue
        ma, mb = nearest_month(P, a), nearest_month(P, b)
        d = pd.DataFrame({'d_officers': sip.loc[matched, b] - sip.loc[matched, a],
                          'd_opcap': cap.loc[matched, mb] - cap.loc[matched, ma],
                          'd_inuse': cna.loc[matched, mb] - cna.loc[matched, ma]}).dropna()
        r = ols(d.d_officers.values, d.d_opcap.values)
        r2 = ols(d.d_officers.values, d.d_inuse.values)
        print(f'\n{label}   capacity months used: {ma:%b %Y} to {mb:%b %Y}')
        print(f'  officers change  total {d.d_officers.sum():+8.0f} FTE   establishments falling {int((d.d_officers<0).sum())}/{len(d)}')
        print(f'  op cap change    total {d.d_opcap.sum():+8.0f}         establishments falling {int((d.d_opcap<0).sum())}/{len(d)}')
        if r:
            print(f'  op cap on officers: slope {r["slope"]:+.2f} places per FTE, t={r["t"]:.2f}, r={r["corr"]:+.2f}, R2={r["r2"]:.3f}, n={r["n"]}')
        if r2:
            print(f'  in-use CNA on officers (control): slope {r2["slope"]:+.2f}, t={r2["t"]:.2f}, r={r2["corr"]:+.2f}')
        if r:
            out.append({'window': label, **r, 'total_d_officers': d.d_officers.sum(), 'total_d_opcap': d.d_opcap.sum()})
        d.assign(window=label).to_csv(f'{outdir}/staffing_capacity_{a:%Y%m}_{b:%Y%m}.csv')
    pd.DataFrame(out).round(3).to_csv(f'{outdir}/staffing_capacity_tests.csv', index=False)

    # staffing gap against target, estate level
    g = S.groupby('date').agg(officers=('officers_fte', 'sum'), target=('target_fte', 'sum'))
    g['gap'] = g.officers - g.target
    g['pct_of_target'] = 100 * g.officers / g.target
    print('\nEstate-level prison officer staffing against target:')
    print(g.round(0).to_string())
    g.to_csv(f'{outdir}/officer_staffing_estate.csv')
    return S, P


if __name__ == '__main__':
    main(sys.argv[1], sys.argv[2], sys.argv[3])
