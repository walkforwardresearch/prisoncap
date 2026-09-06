"""Turn parsed bulletin records into the public weekly series plus QA outputs.

Outputs (data/processed/):
  weekly_population_capacity.csv   one row per reference date, sorted, with provenance flags
  weekly_consistency_report.csv    bulletin-to-bulletin cross-checks (last-week block vs prior bulletin)
  operating_margin_log.csv         dated changes in the published operating margin (definitions log seed)
"""
import sys, os, datetime as dt
import pandas as pd
import numpy as np

FRI_TO_MON_SWITCH = pd.Timestamp('2024-10-21')   # first Monday-dated bulletin

def expected_weekday(d):
    return 0 if d >= FRI_TO_MON_SWITCH else 4    # Monday after the switch, Friday before

def resolve_date(r):
    """Prefer the title date when it sits on the era's reporting weekday; otherwise the in-file date
    if that does, otherwise the title date. Fixes the known gov.uk title typos and stale in-file dates."""
    cands = [c for c in [r['date_title'], r['date_in_file'], r['date_from_last_week']] if pd.notna(c)]
    for c in cands:
        if c.dayofweek == expected_weekday(c):
            return c, 'title' if c == r['date_title'] else ('in_file' if c == r['date_in_file'] else 'last_week+7')
    return cands[0], 'fallback'

def main(parsed, outdir):
    df = pd.read_csv(parsed, parse_dates=['date_title', 'date_in_file', 'date_from_last_week'])
    res = df.apply(resolve_date, axis=1, result_type='expand')
    df['date'], df['date_source'] = res[0], res[1]
    df = df.sort_values('date').reset_index(drop=True)
    assert not df.date.duplicated().any(), df[df.date.duplicated(keep=False)][['title', 'date']]

    # ---- harmonised columns
    # population: total as published (era A totals include HMPPS-operated IRCs; column pop_irc gives the IRC part)
    df['pop_male_est'] = df['pop_male'].fillna(df['pop_adult_male'].add(df['pop_ycs'], fill_value=0).where(df['pop_adult_male'].notna()))
    df['irc_in_total'] = df['pop_irc'].notna()
    df['headroom_calc'] = df['uoc_total'] - df['pop_total']   # capacity minus population, before any margin
    # published headroom exists only in layout B; before that headroom_calc is the only definition
    df['headroom'] = df['headroom_published'].fillna(df['headroom_calc'])

    # ---- cross-check: 'last week' block vs prior bulletin (7-day gaps only)
    df['prev_date'] = df['date'].shift(1); df['prev_pop'] = df['pop_total'].shift(1); df['prev_uoc'] = df['uoc_total'].shift(1)
    df['gap_days'] = (df['date'] - df['prev_date']).dt.days
    chk = df[df.gap_days == 7].copy()
    chk['pop_lw_diff'] = chk['lw_pop_total'] - chk['prev_pop']
    chk['uoc_lw_diff'] = chk['lw_uoc_total'] - chk['prev_uoc']
    rep = chk[['date', 'prev_date', 'pop_total', 'prev_pop', 'lw_pop_total', 'pop_lw_diff', 'uoc_total', 'prev_uoc', 'lw_uoc_total', 'uoc_lw_diff', 'title']]
    rep.to_csv(f'{outdir}/weekly_consistency_report.csv', index=False)
    mism = rep[(rep.pop_lw_diff.abs() > 0) | (rep.uoc_lw_diff.abs() > 0)]
    print(f'consistency: {len(rep)} consecutive pairs checked, {len(mism)} with a last-week mismatch')
    if len(mism):
        print(mism[['date', 'prev_pop', 'lw_pop_total', 'pop_lw_diff', 'prev_uoc', 'lw_uoc_total', 'uoc_lw_diff']].to_string())

    # ---- recover skipped weeks from the next bulletin's 'last week' block (14-day gaps)
    rec = []
    for i, r in df[df.gap_days == 14].iterrows():
        if pd.notna(r.lw_pop_total) and pd.notna(r.lw_uoc_total):
            rec.append({'date': r.date - pd.Timedelta(days=7), 'pop_total': r.lw_pop_total, 'uoc_total': r.lw_uoc_total,
                        'headroom_calc': r.lw_uoc_total - r.lw_pop_total, 'headroom': r.lw_uoc_total - r.lw_pop_total,
                        'source': 'recovered_from_next_bulletin_last_week_block', 'url': r.url, 'title': r.title})
    rec = pd.DataFrame(rec)
    print(f'recovered {len(rec)} skipped weeks from last-week blocks')

    keep = ['date', 'pop_total', 'pop_prisons', 'pop_irc', 'pop_male', 'pop_female', 'pop_adult_male', 'pop_ycs', 'irc_in_total',
            'uoc_total', 'uoc_prisons', 'uoc_irc', 'uoc_adult_male', 'uoc_female', 'uoc_ycs',
            'headroom', 'headroom_published', 'headroom_calc', 'operating_margin', 'operating_margin_adult_male', 'operating_margin_female', 'operating_margin_ycs',
            'hdc', 'layout', 'date_source', 'title', 'url']
    out = df[keep].copy(); out['source'] = 'bulletin'

    # ---- 2011 Word bulletins (parse_weekly_doc.py), if present
    doc_path = f'{outdir}/weekly_2011_doc.csv'
    if os.path.exists(doc_path):
        doc = pd.read_csv(doc_path, parse_dates=['date'])
        doc['date_source'] = 'title'; doc['source'] = 'bulletin_word_2011'
        doc['irc_in_total'] = doc['pop_irc'].notna()
        doc_cols = list(dict.fromkeys(keep + ['source', 'police_cells']))
        doc = doc[[c for c in doc_cols if c in doc.columns]]
        doc = doc[~doc.date.isin(out.date)]
        out = pd.concat([out, doc], ignore_index=True)
        print(f'merged {len(doc)} Word-format 2011 bulletins')

    out = pd.concat([out, rec], ignore_index=True).sort_values('date').reset_index(drop=True)
    out['week_gap_days'] = out['date'].diff().dt.days
    out.to_csv(f'{outdir}/weekly_population_capacity.csv', index=False)
    print(f'series: {len(out)} rows, {out.date.min().date()} to {out.date.max().date()}')

    # ---- operating margin log
    om = df[['date', 'operating_margin', 'operating_margin_adult_male', 'operating_margin_female', 'operating_margin_ycs', 'lw_operating_margin', 'ya_operating_margin']].copy()
    # A2-era bulletins state the margin only in the last-week/12-months-ago block; shift 'last week' to the prior date
    lw = om.dropna(subset=['lw_operating_margin']).assign(date=lambda x: x.date - pd.Timedelta(days=7))[['date', 'lw_operating_margin']].rename(columns={'lw_operating_margin': 'operating_margin'})
    ya = om.dropna(subset=['ya_operating_margin']).assign(date=lambda x: x.date - pd.Timedelta(days=364))[['date', 'ya_operating_margin']].rename(columns={'ya_operating_margin': 'operating_margin'})
    cur = om.dropna(subset=['operating_margin'])[['date', 'operating_margin', 'operating_margin_adult_male', 'operating_margin_female', 'operating_margin_ycs']]
    allm = pd.concat([cur.assign(basis='stated_current'), lw.assign(basis='stated_as_last_week'), ya.assign(basis='stated_as_12_months_ago')]).sort_values(['date', 'basis'])
    allm = allm.drop_duplicates('date', keep='first')
    changes = allm[allm.operating_margin != allm.operating_margin.shift(1)]
    changes.to_csv(f'{outdir}/operating_margin_log.csv', index=False)
    print('operating margin changes:'); print(changes.to_string(index=False))

if __name__ == '__main__':
    main(sys.argv[1], sys.argv[2])
