"""Decompose MoJ projection error by sentence-type component (WP2, Q1 part b, first pass).

Two analyses, both using only the projection editions themselves:

1. ERROR DECOMPOSITION. Editions publish an unrounded base-year actual broken down by custody
   type. Where an earlier edition projected that same reference month, the difference can be
   decomposed component by component. This answers which component the miss came from, without
   needing OMSQ.

   Matching is on (year, month) rather than exact day, because editions vary between the 1st and
   the last day of the reference month. The day gap is recorded.

2. REVISION DECOMPOSITION. Successive editions restate the same future reference date. Comparing
   edition E and edition E+1 for a common target shows which component the MoJ revised and by how
   much. This has far more observations than analysis 1 and, since later vintages are on average
   closer to outturn, it points the same way.

Both are a first pass. A full demand-versus-policy split needs the OMSQ flow tables and a dated
policy-change log; this narrows down where in the stock the error sits before that work starts.
"""
import sys
import numpy as np
import pandas as pd

COMPONENTS = ['remand', 'determinate', 'indeterminate', 'recall', 'non-criminal', 'fine_defaulters']


def tidy(L):
    """Normalise component columns; older editions call fine defaulters 'fine'."""
    L = L.copy()
    if 'fine' in L.columns:
        L['fine_defaulters'] = L.get('fine_defaulters').fillna(L['fine']) if 'fine_defaulters' in L.columns else L['fine']
    for c in COMPONENTS:
        if c not in L.columns:
            L[c] = np.nan
    L['ym'] = L.ref_date.dt.year * 100 + L.ref_date.dt.month
    return L


def error_decomposition(L):
    act = L[(L.scenario == 'actual') & L[COMPONENTS].notna().any(axis=1)].copy()
    act = act.drop_duplicates('ym', keep='last')
    proj = L[(L.scenario == 'central') & (L.horizon_years > 0) & L[COMPONENTS].notna().any(axis=1)].copy()

    a = act.set_index('ym')
    rows = []
    for _, p in proj.iterrows():
        if p.ym not in a.index:
            continue
        r = a.loc[p.ym]
        rec = {'target': p.ref_date.strftime('%b %Y'), 'edition': p.edition, 'horizon_years': p.horizon_years,
               'actual_from': r.edition, 'day_gap': abs((p.ref_date - r.ref_date).days),
               'proj_total': p.total, 'actual_total': r.total, 'error_total': p.total - r.total}
        for c in COMPONENTS:
            if pd.notna(p[c]) and pd.notna(r[c]):
                rec[f'err_{c}'] = p[c] - r[c]
        rows.append(rec)
    return pd.DataFrame(rows)


def revision_decomposition(L):
    p = L[(L.scenario == 'central') & (L.horizon_years > 0) & L[COMPONENTS].notna().any(axis=1)].copy()
    p['vintage'] = p.edition.str[:4].astype(int)
    rows = []
    for ym, g in p.groupby('ym'):
        g = g.sort_values('vintage')
        for i in range(1, len(g)):
            older, newer = g.iloc[i - 1], g.iloc[i]
            rec = {'target': newer.ref_date.strftime('%b %Y'), 'from_edition': older.edition,
                   'to_edition': newer.edition, 'rev_total': newer.total - older.total}
            for c in COMPONENTS:
                if pd.notna(older[c]) and pd.notna(newer[c]):
                    rec[f'rev_{c}'] = newer[c] - older[c]
            rows.append(rec)
    return pd.DataFrame(rows)


def contribution_table(df, prefix, total_col):
    """Mean contribution of each component, in people and as a share of the total movement."""
    cols = [f'{prefix}{c}' for c in COMPONENTS if f'{prefix}{c}' in df.columns]
    out = []
    for c in cols:
        s = df[c].dropna()
        if not len(s):
            continue
        paired = df.loc[s.index, total_col]
        out.append({'component': c.replace(prefix, ''), 'n': len(s), 'mean': s.mean(),
                    'mean_abs': s.abs().mean(),
                    'share_of_total_pct': 100 * s.sum() / paired.sum() if paired.sum() else np.nan,
                    'largest_contributor_pct': np.nan})
    t = pd.DataFrame(out)
    # how often each component is the biggest single contributor to that row's movement
    if cols:
        biggest = df[cols].abs().idxmax(axis=1).dropna().str.replace(prefix, '', regex=False)
        freq = biggest.value_counts(normalize=True) * 100
        t['largest_contributor_pct'] = t.component.map(freq).fillna(0)
    return t.round(1)


def main(proj_csv, outdir):
    L = tidy(pd.read_csv(proj_csv, parse_dates=['ref_date']))

    E = error_decomposition(L)
    E.round(1).to_csv(f'{outdir}/error_decomposition.csv', index=False)
    print(f'ERROR DECOMPOSITION: {len(E)} matched projection/actual pairs\n')
    show = ['target', 'edition', 'horizon_years', 'day_gap', 'proj_total', 'actual_total', 'error_total'] + [f'err_{c}' for c in COMPONENTS]
    print(E[[c for c in show if c in E.columns]].round(0).to_string(index=False))

    print('\nContribution to total error, all pairs:')
    print(contribution_table(E, 'err_', 'error_total').to_string(index=False))

    for h in sorted(E.horizon_years.unique()):
        sub = E[E.horizon_years == h]
        if len(sub) >= 2:
            print(f'\nHorizon {h} year(s), n={len(sub)}, mean total error {sub.error_total.mean():.0f}:')
            print(contribution_table(sub, 'err_', 'error_total').to_string(index=False))

    R = revision_decomposition(L)
    R.round(1).to_csv(f'{outdir}/revision_decomposition.csv', index=False)
    print(f'\n\nREVISION DECOMPOSITION: {len(R)} successive-edition pairs on a common target date')
    print(contribution_table(R, 'rev_', 'rev_total').to_string(index=False))

    ct = contribution_table(E, 'err_', 'error_total')
    ct.to_csv(f'{outdir}/error_contribution_summary.csv', index=False)
    contribution_table(R, 'rev_', 'rev_total').to_csv(f'{outdir}/revision_contribution_summary.csv', index=False)
    return E, R


if __name__ == '__main__':
    main(sys.argv[1], sys.argv[2])
