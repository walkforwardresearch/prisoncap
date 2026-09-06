"""Parse the monthly by-establishment bulletins into one long panel (WP1 / WP4).

Each bulletin is a single sheet, MonthlyBulletin, with a stable four-column table:
    Prison Name | Baseline CNA | In Use CNA | Operational Capacity | Population

Definitions that matter for the supply model:
    Baseline CNA   certified normal accommodation, the uncrowded design capacity
    In Use CNA     the part of baseline CNA actually available; the gap is cells out of use
                   (maintenance, damage, decommissioning, staffing)
    Op Capacity    the maximum an establishment can safely hold, normally above CNA (crowding)

So Baseline CNA minus In Use CNA is the published measure of lost accommodation, and it is the
only routine public series that explains movements in estate capacity by establishment.

Rows after the establishment table are footnotes and a list of establishments exceeding their
CNA; parsing stops at the first non-establishment row.
"""
import sys, glob, os, re, warnings
import pandas as pd
import numpy as np

warnings.filterwarnings('ignore')

COLS = ['baseline_cna', 'in_use_cna', 'op_cap', 'population']


def report_date(df):
    for i in range(min(4, df.shape[0])):
        for j in range(df.shape[1]):
            t = str(df.iat[i, j])
            m = re.search(r'Report Date\s*:?\s*(\d{1,2})[/\-](\d{1,2})[/\-](\d{2,4})', t, re.I)
            if m:
                d, mth, y = int(m.group(1)), int(m.group(2)), int(m.group(3))
                y = y + 2000 if y < 100 else y
                try:
                    return pd.Timestamp(y, mth, d)
                except ValueError:
                    return None
    return None


def parse(path, month):
    eng = 'odf' if path.lower().endswith('.ods') else None
    sh = pd.read_excel(path, sheet_name=None, header=None, engine=eng)
    name = next(n for n in sh if not n.startswith("'") and sh[n].shape[0] > 0)
    df = sh[name]

    hdr = None
    for i in range(min(10, df.shape[0])):
        row = ' '.join(str(v).lower() for v in df.iloc[i].tolist())
        if 'prison name' in row and 'cna' in row:
            hdr = i; break
    if hdr is None:
        raise ValueError('header row not found')

    rows, blanks, published_uoc, section = [], 0, np.nan, 'prison'
    NOTE = re.compile(r'^(notes?|footnote|where operational|establishments exceeding|governing governors|'
                      r'report produced|definitions of|certified normal|baseline cna|in.?use cna|'
                      r'operational capacity|useable operational|crowding|the report is compiled|'
                      r'\*|•|(his|her) majesty|this is published|population figures)', re.I)
    TOTAL = re.compile(r'^(sub[\s\-]?total|total)\b', re.I)

    def cell_num(v):
        if isinstance(v, (int, float)) and not pd.isna(v):
            return float(v)
        t = re.sub(r'[^\d.]', '', str(v))
        return float(t) if re.fullmatch(r'\d+(\.\d+)?', t) else np.nan

    for i in range(hdr + 1, df.shape[0]):
        vals = df.iloc[i].tolist()
        nm = str(vals[0]).strip() if vals and str(vals[0]) != 'nan' else ''
        nums = [cell_num(v) for v in vals[1:]]
        if not nm:
            blanks += 1
            continue
        blanks = 0
        if TOTAL.match(nm):
            # the final Total row reports USEABLE operational capacity in the op cap column,
            # i.e. the sum of establishment operational capacities less the operating margin
            if not re.match(r'^sub', nm, re.I) and not pd.isna(nums[2]):
                published_uoc = nums[2]
            continue
        if all(pd.isna(n) for n in nums[:4]):
            # section headings sit inside the table and can be long, so they are tested for
            # BEFORE the footnote rules; 'HMPPS Operated Immigration Removal Centres' would
            # otherwise trip the length rule and truncate the table before the Total row.
            if re.search(r'immigration removal', nm, re.I):
                section = 'irc'; continue
            if NOTE.match(nm) or len(nm) > 45:
                if rows:
                    break
            continue
        if NOTE.match(nm):
            if rows:
                break
            continue
        # establishments that are closed or mothballed publish a partial row (for example
        # Blantyre House in 2018-19, baseline CNA only). Keep them with NaNs.
        rows.append({'month': month, 'report_date': report_date(df), 'prison': nm, 'section': section,
                     'published_uoc': published_uoc,
                     **dict(zip(COLS, (nums[:4] + [np.nan] * 4)[:4]))})
    for r in rows:
        r['published_uoc'] = published_uoc
    return rows


def main(manifest, out):
    man = pd.read_csv(manifest, parse_dates=['month'])
    allrows, meta = [], []
    for _, r in man.iterrows():
        try:
            rows = parse(r.local, r.month)
        except Exception as e:
            print(f'FAIL {r.month:%Y-%m}: {type(e).__name__}: {e}'); continue
        allrows += rows
        meta.append({'month': r.month, 'n_prisons': len(rows),
                     'sum_op_cap': np.nansum([x['op_cap'] for x in rows]),
                     'sum_pop': np.nansum([x['population'] for x in rows]),
                     'sum_baseline_cna': np.nansum([x['baseline_cna'] for x in rows]),
                     'sum_in_use_cna': np.nansum([x['in_use_cna'] for x in rows]), 'published_uoc': rows[0]['published_uoc'] if rows else np.nan})
    P = pd.DataFrame(allrows)
    # normalise establishment names so a prison can be tracked through renames and spacing changes
    P['prison_key'] = (P.prison.str.replace(r'\s*\(.*?\)', '', regex=True)
                              .str.replace(r'[^A-Za-z ]', '', regex=True)
                              .str.strip().str.lower().str.replace(r'\s+', ' ', regex=True))
    P['cells_out_of_use'] = P.baseline_cna - P.in_use_cna
    P['crowding'] = P.op_cap - P.in_use_cna
    P.to_csv(out, index=False)
    M = pd.DataFrame(meta).sort_values('month')
    M['cells_out_of_use'] = M.sum_baseline_cna - M.sum_in_use_cna
    M.to_csv(out.replace('.csv', '_estate_totals.csv'), index=False)
    print(f'parsed {len(man)} bulletins -> {len(P)} establishment-months, '
          f'{P.month.min():%Y-%m} to {P.month.max():%Y-%m}, {P.prison_key.nunique()} distinct establishments')
    return P, M


if __name__ == '__main__':
    main(sys.argv[1], sys.argv[2])
