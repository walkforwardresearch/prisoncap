"""Parse all 18 MoJ Prison Population Projection editions (2008 to 2025) into two long tables.

Layout families in the main projection table (sheet 'A1' / 'Table A1' / 'Table 1.1' / 'Table_1_1'):

  L1  2008-2015, 2009-2015     row label = calendar year integer; columns High | Medium | Low
  L2  2010-2016                row label = year integer; columns Increase | No change | Decrease
  L3  2011-2017 .. 2014-2020   row label = date; scenario columns, names vary
                               (Lower|Medium|Higher, Scenario 1|2|3, Scenario 1|Central|Scenario 2)
  L4  2015-2021 .. 2024-2029   row label = date; ONE central path, columns are sentence-type
                               components (Total, Remand, Determinate, Indeterminate, Recall, ...)
  L5  2025-2030                blocks labelled Actuals / Central / Low / High, each a date table
                               with sentence-type components

The reference month differs by edition (end June, 1 June, end Sept, end Nov, 1 July) and is taken
from the date cells where present, otherwise from the Contents sheet wording.

Scenario naming is normalised to central / low / high. For L1 'Medium', L2 'No change',
L3 'Medium'/'Scenario 2'/'Central' are the central path. Where an edition publishes only one path
it is labelled central.

Outputs:
  projections_long.csv     edition, scenario, ref_date, horizon_years, total + components
  projections_monthly.csv  edition, month_end, total   (from the monthly-values appendix table)
"""
import re, sys, glob, os, csv, datetime as dt
import pandas as pd
import numpy as np

MONTH_WORDS = {'january':1,'february':2,'march':3,'april':4,'may':5,'june':6,
               'july':7,'august':8,'september':9,'october':10,'november':11,'december':12}

CENTRAL = {'medium', 'no change', 'central', 'scenario 2', 'total'}
LOW = {'low', 'lower', 'decrease', 'scenario 1'}
HIGH = {'high', 'higher', 'increase', 'scenario 3'}

COMPONENTS = ['remand', 'determinate', 'indeterminate', 'recall', 'non-criminal', 'fine defaulters', 'fine']

def engine(f):
    return 'odf' if f.endswith('.ods') else ('xlrd' if f.endswith('.xls') else 'openpyxl')

def sheets(f):
    return pd.read_excel(f, sheet_name=None, header=None, engine=engine(f))

def s(v):
    return '' if v is None or (isinstance(v, float) and pd.isna(v)) else str(v).strip()

def num(v):
    if isinstance(v, (int, float)) and not pd.isna(v):
        return float(v)
    t = s(v).replace(',', '')
    return float(t) if re.fullmatch(r'-?\d+(\.\d+)?', t) else None

def pick_sheet(sh, *cands):
    keys = {k.lower().replace('_', ' ').replace('.', ' ').strip(): k for k in sh if not k.startswith("'")}
    for c in cands:
        c = c.lower().replace('_', ' ').replace('.', ' ').strip()
        if c in keys:
            return keys[c]
    return None

def ref_month(sh, default=6):
    """End-of-month convention, read from the Contents sheet wording."""
    cs = pick_sheet(sh, 'contents')
    if cs:
        txt = ' '.join(s(v) for v in sh[cs].values.ravel()).lower()
        m = re.search(r'end of (\w+) figures', txt)
        if m and m.group(1) in MONTH_WORDS:
            return MONTH_WORDS[m.group(1)]
    return default

def row_label_date(v, month, year_hint=None):
    """Row labels are either a real date or a bare calendar year."""
    if isinstance(v, (pd.Timestamp, dt.datetime)):
        return None if pd.isna(v) else pd.Timestamp(v).normalize()
    t = s(v)
    if re.fullmatch(r'(19|20)\d\d', t):
        y = int(t)
        return pd.Timestamp(y, month, 1) + pd.offsets.MonthEnd(0)
    m = re.match(r'([A-Za-z]+)\s+((?:19|20)\d\d)\*?$', t)     # 'September 2026'
    if m and m.group(1).lower() in MONTH_WORDS:
        return pd.Timestamp(int(m.group(2)), MONTH_WORDS[m.group(1).lower()], 1) + pd.offsets.MonthEnd(0)
    return None

def norm_scenario(name):
    n = name.lower().strip()
    if n in CENTRAL: return 'central'
    if n in LOW: return 'low'
    if n in HIGH: return 'high'
    if 'actual' in n: return 'actual'
    return None

def resolve_header(h, first_vals):
    """Map header labels to central/low/high.

    Explicit names win (Medium, Central, No change -> central; Higher, Increase -> high; etc).
    Generic 'Scenario N' is ambiguous: it is the central path in the 2012 and 2013 editions
    (Scenario 1|2|3) but the high path in the 2014 edition (Scenario 1|Central|Scenario 2).
    So when an explicit central column is present, generic labels are assigned by whether their
    first projected value sits below or above it; otherwise 1|2|3 maps to low|central|high.
    """
    EXPLICIT = {'medium': 'central', 'central': 'central', 'no change': 'central',
                'low': 'low', 'lower': 'low', 'decrease': 'low',
                'high': 'high', 'higher': 'high', 'increase': 'high'}
    out = [EXPLICIT.get(x.lower().strip()) for x in h]
    generic = [i for i, (x, o) in enumerate(zip(h, out)) if o is None and re.fullmatch(r'scenario\s*\d+', x.lower().strip())]
    if not generic:
        return out
    if 'central' in out and len(first_vals) == len(h):
        c = first_vals[out.index('central')]
        for i in generic:
            out[i] = 'low' if first_vals[i] < c else 'high'
    else:
        order = {'1': 'low', '2': 'central', '3': 'high'}
        for i in generic:
            out[i] = order.get(re.sub(r'\D', '', h[i]))
    return out


def parse_main(f, edition, sh):
    name = pick_sheet(sh, 'Table 1.1', 'Table_1_1', 'Table A1', 'A1')
    df = sh[name]
    month = ref_month(sh)
    rows = []

    LABELISH = {'year', 'date', ''}

    def scan_row(i):
        """Return (label_cell_index, label_cell, list_of_numbers_after_it)."""
        first = None
        for j in range(df.shape[1]):
            if s(df.iat[i, j]) or num(df.iat[i, j]) is not None:
                first = j; break
        if first is None:
            return None, None, []
        vals = [num(df.iat[i, j]) for j in range(first + 1, df.shape[1])]
        return first, df.iat[i, first], [v for v in vals if v is not None]

    data_rows, hdr, cur_block, started = [], None, None, False
    for i in range(df.shape[0]):
        first, lab, vals = scan_row(i)
        if first is None:
            continue
        d = row_label_date(lab, month)
        if d is not None and vals:
            data_rows.append((d, vals, hdr, cur_block)); started = True
            continue
        texts = [s(df.iat[i, j]) for j in range(df.shape[1]) if s(df.iat[i, j])]
        if not texts:
            continue
        if len(texts) == 1 and norm_scenario(texts[0]):
            cur_block = norm_scenario(texts[0])          # L5 block label (Actuals / Central / Low / High)
        elif any(norm_scenario(t) for t in texts) or any(t.lower() in COMPONENTS + ['total'] for t in texts):
            if started:
                break                                     # a second header means a second sub-table: stop
            hdr = [t for t in texts if t.lower() not in LABELISH]

    for d, vals, h, block in data_rows:
        h = h or []
        mapped = resolve_header(h, vals)
        is_scenario_layout = (sum(1 for x in mapped if x in ('central', 'low', 'high')) >= 2
                              and 'total' not in [x.lower() for x in h])
        if is_scenario_layout:
            for sc, v in zip(mapped, vals):
                if sc:
                    rows.append({'edition': edition, 'scenario': sc, 'ref_date': d, 'total': v})
        else:
            rec = {'edition': edition, 'scenario': block or 'central', 'ref_date': d, 'total': vals[0] if vals else None}
            for lab, v in zip(h[1:], vals[1:]):
                if lab.lower() in COMPONENTS:
                    rec[lab.lower().replace(' ', '_')] = v
            rows.append(rec)
    return rows, name, month

def parse_monthly(f, edition, sh):
    """Appendix 'Monthly values of the overall <edition> projected prison population' table.

    These carry Low | Central | High columns in recent editions and a single Population column in
    older ones. Editions also republish the PREVIOUS edition's monthly path in an adjacent sheet,
    so the edition string in the sheet title is used to pick the right one.
    """
    out = []
    for name, df in sh.items():
        if name.startswith("'") or df.shape[0] == 0:
            continue
        title = ' '.join(s(df.iat[i, j]) for i in range(min(3, df.shape[0])) for j in range(df.shape[1])).lower()
        if 'monthly values' not in title:
            continue
        yrs = re.findall(r'(20\d\d)\s*(?:to|-|–)\s*(20\d\d)', title)
        if yrs and f'{yrs[0][0]}-{yrs[0][1]}' != edition:
            continue                                   # this is the previous edition's path
        # header row: find the one naming the columns
        col, hdr_i = None, None
        for i in range(min(8, df.shape[0])):
            texts = {s(df.iat[i, j]).lower(): j for j in range(df.shape[1]) if s(df.iat[i, j])}
            if 'central' in texts:
                col, hdr_i = texts['central'], i; break
            if 'population' in texts or 'total' in texts:
                col, hdr_i = texts.get('population', texts.get('total')), i; break
        for i in range((hdr_i or 0) + 1, df.shape[0]):
            first = next((j for j in range(df.shape[1]) if s(df.iat[i, j]) or num(df.iat[i, j]) is not None), None)
            if first is None:
                continue
            d = row_label_date(df.iat[i, first], 6)
            if d is None:
                continue
            v = num(df.iat[i, col]) if col is not None else next((num(df.iat[i, j]) for j in range(first + 1, df.shape[1]) if num(df.iat[i, j]) is not None), None)
            if v:
                out.append({'edition': edition, 'month_end': d, 'total': v})
        if out:
            return out
    return out

def main(indir, outdir):
    long_rows, month_rows, meta = [], [], []
    for f in sorted(glob.glob(f'{indir}/*')):
        edition = os.path.basename(f).rsplit('.', 1)[0]
        sh = sheets(f)
        try:
            rows, sheet_used, month = parse_main(f, edition, sh)
        except Exception as e:
            print(f'MAIN FAIL {edition}: {type(e).__name__}: {e}'); continue
        long_rows += rows
        try:
            mr = parse_monthly(f, edition, sh)
        except Exception as e:
            mr = []; print(f'  monthly fail {edition}: {e}')
        month_rows += mr
        scen = sorted(set(r['scenario'] for r in rows))
        meta.append({'edition': edition, 'sheet': sheet_used, 'ref_month': month, 'n_rows': len(rows),
                     'scenarios': '|'.join(scen), 'n_monthly': len(mr)})
        print(f"{edition:12s} {sheet_used:12s} month={month:2d} rows={len(rows):3d} scen={'|'.join(scen):22s} monthly={len(mr)}")

    L = pd.DataFrame(long_rows)
    # base date = the edition's own first reference point; horizon in whole years from it
    base = L[L.scenario.isin(['central', 'actual'])].groupby('edition').ref_date.min().rename('base_date')
    L = L.merge(base, on='edition', how='left')
    L['edition_year'] = L.edition.str[:4].astype(int)
    L['horizon_years'] = L.ref_date.dt.year - L.edition_year
    L.loc[L.horizon_years == 0, 'scenario'] = L.loc[L.horizon_years == 0, 'scenario'].where(L.scenario == 'actual', 'actual')
    L = L.sort_values(['edition', 'scenario', 'ref_date'])
    L.to_csv(f'{outdir}/projections_long.csv', index=False)
    M = pd.DataFrame(month_rows).sort_values(['edition', 'month_end'])
    M.to_csv(f'{outdir}/projections_monthly.csv', index=False)
    pd.DataFrame(meta).to_csv(f'{outdir}/projections_editions.csv', index=False)
    print(f'\nlong: {len(L)} rows, {L.edition.nunique()} editions -> projections_long.csv')
    print(f'monthly: {len(M)} rows, {M.edition.nunique()} editions -> projections_monthly.csv')

if __name__ == '__main__':
    main(sys.argv[1], sys.argv[2])
