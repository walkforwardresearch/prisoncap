"""Parse MoJ weekly prison population bulletins (ODS/XLS) into one flat record per bulletin.

Three layout eras are handled:
  A1  2011 to ~2022  'Headlines- PUBLISHED' sheet, columns Total / Prisons / IRCs,
                     rows Population, Male population, Female population, UOC, HDC.
  A2  ~2022 to early 2024  same sheet, single 'This week' column,
                     rows 'Population in male estate' etc; Operating Margin row appears late 2023.
  B   2024 onward    'Data' sheet, columns Total / Adult Male / Female / YCS,
                     rows Population, UOC, Headroom, HDC; operating margin table at the bottom.

Every field is read by label, never by fixed cell position, so minor drift does not break it.
"""
import re, sys, csv, datetime as dt, warnings
import pandas as pd
warnings.filterwarnings('ignore')

MONTHS = {m.lower(): i for i, m in enumerate(['January','February','March','April','May','June','July',
          'August','September','October','November','December'], 1)}

def title_date(title):
    """Date from the attachment title, e.g. 'Population bulletin: weekly 24 August 2026'."""
    m = re.search(r'(\d{1,2})\s+([A-Za-z]+)\s+(\d{4})', title)
    if not m:
        return None
    d, mon, y = int(m.group(1)), m.group(2).lower(), int(m.group(3))
    mon = MONTHS.get(mon) or MONTHS.get({'jnauary':'january','sept':'september'}.get(mon, mon))
    if not mon:
        return None
    try:
        return dt.date(y, mon, d)
    except ValueError:
        return None

def to_num(v):
    if v is None:
        return None
    if isinstance(v, (int, float)) and not pd.isna(v):
        return float(v)
    s = str(v).strip().replace(',', '')
    if re.fullmatch(r'-?\d+(\.\d+)?', s):
        return float(s)
    return None

def load_sheet(path):
    eng = 'odf' if path.lower().endswith('.ods') else 'xlrd'
    sheets = pd.read_excel(path, sheet_name=None, header=None, engine=eng)
    # prefer a sheet whose name looks like the headline sheet; ignore external-link ghost sheets
    for name, df in sheets.items():
        if name.startswith("'") or df.shape[0] == 0:
            continue
        if 'headline' in name.lower() or name.strip().lower() == 'data':
            return name, df
    for name, df in sheets.items():
        if df.shape[0] > 0 and not name.startswith("'"):
            return name, df
    raise ValueError('no usable sheet')

def cell_str(v):
    return '' if v is None or (isinstance(v, float) and pd.isna(v)) else str(v).strip()

def find_rows(df, pattern, start=0):
    rx = re.compile(pattern, re.I)
    out = []
    for i in range(start, df.shape[0]):
        first = ''
        for j in range(df.shape[1]):
            s = cell_str(df.iat[i, j])
            if s:
                first = s
                break
        if rx.search(first):
            out.append(i)
    return out

def numbers_in_row(df, i):
    vals = []
    for j in range(df.shape[1]):
        n = to_num(df.iat[i, j])
        if n is not None:
            vals.append(n)
    return vals

def strings_in_row(df, i):
    return [cell_str(df.iat[i, j]) for j in range(df.shape[1]) if cell_str(df.iat[i, j])]

def in_file_date(df):
    for i in range(min(3, df.shape[0])):
        for j in range(df.shape[1]):
            v = df.iat[i, j]
            if isinstance(v, (pd.Timestamp, dt.datetime)) and not pd.isna(v):
                return v.date()
    return None

def parse_text_date(s):
    m = re.search(r'(\d{1,2})\s+([A-Za-z]+)\s+(\d{4})', s)
    return title_date(m.group(0)) if m else None

def parse_file(path, title=''):
    name, df = load_sheet(path)
    rec = {'layout': None, 'sheet': name}
    txt = ' '.join(strings_in_row(df, 4)) if df.shape[0] > 4 else ''

    # ---- identify the current-period block: first 'Population' label row
    pop_rows = find_rows(df, r'^population$')
    if not pop_rows:
        raise ValueError('no Population row')
    p0 = pop_rows[0]
    hdr = strings_in_row(df, p0 - 1) if p0 > 0 else []
    hdr_l = [h.lower() for h in hdr]

    if any('adult male' in h for h in hdr_l):
        rec['layout'] = 'B'
        cols = ['total', 'adult_male', 'female', 'ycs']
    elif any('irc' in h for h in hdr_l):
        rec['layout'] = 'A1'
        cols = ['total', 'prisons', 'irc']
    else:
        rec['layout'] = 'A2'
        cols = ['total']

    def row_vals(pattern, start, cols_):
        rows = find_rows(df, pattern, start)
        if not rows:
            return {}, None
        i = rows[0]
        vals = numbers_in_row(df, i)
        return {f'{c}': v for c, v in zip(cols_, vals)}, i

    # current block
    pv, _ = row_vals(r'^population$', p0, cols)
    for c in cols:
        rec[f'pop_{c}'] = pv.get(c)
    uv, u_i = row_vals(r'^useable operational capacity$', p0, cols)
    for c in cols:
        rec[f'uoc_{c}'] = uv.get(c)
    # era A male/female rows (current block only: between p0 and the UOC row)
    limit = u_i if u_i else p0 + 6
    mv, _ = row_vals(r'^(male population|population in male estate)$', p0, cols)
    fv, _ = row_vals(r'^(female population|population in female estate)$', p0, cols)
    if mv: rec['pop_male'] = mv.get('total')
    if fv: rec['pop_female'] = fv.get('total')
    hv, _ = row_vals(r'^headroom$', p0, cols)
    if hv:
        rec['headroom_published'] = hv.get('total')
    hd, _ = row_vals(r'^home detention curfew caseload', p0, ['total'])
    rec['hdc'] = hd.get('total')

    # ---- previous-period block ('Last week' / 'Last Week: <date>' headers)
    lw = find_rows(df, r'^last week', p0 + 1)
    if lw:
        i = lw[0]
        rec['last_week_date_text'] = strings_in_row(df, i)[0]
        if rec['layout'] == 'B':
            pv2, _ = row_vals(r'^population$', i, cols)
            uv2, _ = row_vals(r'^useable operational capacity$', i, cols)
            rec['lw_pop_total'] = pv2.get('total'); rec['lw_uoc_total'] = uv2.get('total')
            # 12 months ago block
            ya = find_rows(df, r'^12 months ago', i + 1)
            if ya:
                pv3, _ = row_vals(r'^population$', ya[0], cols)
                uv3, _ = row_vals(r'^useable operational capacity$', ya[0], cols)
                rec['ya_pop_total'] = pv3.get('total'); rec['ya_uoc_total'] = uv3.get('total')
                rec['ya_date_text'] = strings_in_row(df, ya[0])[0]
        else:
            # A layouts: a two-column block headed 'Last week' / '12 months ago'. Read by column
            # position, because a skipped week leaves 'Data not available' in the last-week cell.
            hdr_cells = {cell_str(df.iat[i, j]).lower(): j for j in range(df.shape[1]) if cell_str(df.iat[i, j])}
            j_lw = next((j for h, j in hdr_cells.items() if h.startswith('last week')), None)
            j_ya = next((j for h, j in hdr_cells.items() if '12 months' in h), None)
            def col_vals(pattern):
                rows_ = find_rows(df, pattern, i)
                if not rows_:
                    return None, None
                r_ = rows_[0]
                return (to_num(df.iat[r_, j_lw]) if j_lw is not None else None,
                        to_num(df.iat[r_, j_ya]) if j_ya is not None else None)
            rec['lw_pop_total'], rec['ya_pop_total'] = col_vals(r'^population$')
            rec['lw_uoc_total'], rec['ya_uoc_total'] = col_vals(r'^useable operational capacity$')
            if find_rows(df, r'^operating margin$', i):
                rec['lw_operating_margin'], rec['ya_operating_margin'] = col_vals(r'^operating margin$')

    # ---- operating margin (layout B definitions table, or free text)
    om_rows = find_rows(df, r'operating margin')
    for i in om_rows:
        s = ' '.join(strings_in_row(df, i))
        m = re.search(r'operating margin[^0-9]{0,60}?([0-9][0-9,]{2,6})', s, re.I)
        if m and 'operating_margin' not in rec:
            rec['operating_margin'] = to_num(m.group(1))
        # table form: following rows 'Overall Estate ; 1640'
        oe = find_rows(df, r'^overall estate$', i)
        if oe:
            v = numbers_in_row(df, oe[0])
            if v:
                rec['operating_margin'] = v[0]
                for lab, key in [('adult male', 'operating_margin_adult_male'), ('female', 'operating_margin_female'), ('ycs', 'operating_margin_ycs')]:
                    r_ = find_rows(df, rf'^{lab}$', oe[0])
                    if r_ and r_[0] <= oe[0] + 4:
                        vv = numbers_in_row(df, r_[0])
                        if vv: rec[key] = vv[0]
            break

    # ---- dates
    rec['date_in_file'] = in_file_date(df)
    rec['date_title'] = title_date(title)
    lwd = parse_text_date(rec.get('last_week_date_text', '') or '')
    rec['date_from_last_week'] = (lwd + dt.timedelta(days=7)) if lwd else None
    # choose: in-file date if present, else title date, else last-week + 7
    rec['date'] = rec['date_in_file'] or rec['date_title'] or rec['date_from_last_week']
    return rec

FIELDS = ['date','date_in_file','date_title','date_from_last_week','layout','sheet',
          'pop_total','pop_prisons','pop_irc','pop_adult_male','pop_female','pop_ycs','pop_male',
          'uoc_total','uoc_prisons','uoc_irc','uoc_adult_male','uoc_female','uoc_ycs',
          'headroom_published','hdc','operating_margin','operating_margin_adult_male','operating_margin_female','operating_margin_ycs',
          'lw_pop_total','lw_uoc_total','lw_operating_margin','ya_pop_total','ya_uoc_total','ya_operating_margin',
          'last_week_date_text','ya_date_text','title','url','local','error']

def main(manifest, out):
    rows = list(csv.DictReader(open(manifest)))
    recs = []
    for r in rows:
        if r['ext'] in ('doc', 'docx'):
            continue
        rec = {'title': r['title'], 'url': r['url'], 'local': r['local']}
        try:
            rec.update(parse_file(r['local'], r['title']))
        except Exception as e:
            rec['error'] = f'{type(e).__name__}: {e}'
        recs.append(rec)
    with open(out, 'w', newline='') as f:
        w = csv.DictWriter(f, fieldnames=FIELDS, extrasaction='ignore')
        w.writeheader(); w.writerows(recs)
    n_err = sum(1 for x in recs if x.get('error'))
    print(f'parsed {len(recs)} files, {n_err} errors -> {out}')
    for x in recs:
        if x.get('error'):
            print('  ERR', x['title'], '|', x['error'])

if __name__ == '__main__':
    main(sys.argv[1], sys.argv[2])
