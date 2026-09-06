"""Parse the 46 Word-format weekly bulletins from 2011 (converted to HTML by libreoffice).

Two sub-layouts:
  D1  Jan to Mar 2011   'PRISON POPULATION & ACCOMMODATION BRIEFING'
                        Male / Female / police cells / TOTAL / Useable Operational Capacity / HDC,
                        then the same block for 12 months ago.
  D2  Apr to Dec 2011   'Population and Capacity Briefing for <date>'
                        table: Total | Prisons | NOMS Operated IRCs, rows Population, Male, Female, UOC, HDC.
                        Matches the later XLS layout A1.

Both state the operating margin in the definitions text ('less 2,000 places'), which is captured.

Convert first:
  libreoffice --headless --convert-to html --outdir raw/weekly_doc_txt raw/weekly/*.doc
"""
import re, sys, csv, glob, html, os, datetime as dt

MONTHS = {m.lower(): i for i, m in enumerate(['january','february','march','april','may','june','july',
          'august','september','october','november','december'], 1)}
ABBR = {'jan':1,'feb':2,'mar':3,'apr':4,'may':5,'jun':6,'jul':7,'aug':8,'sep':9,'sept':9,'oct':10,'nov':11,'dec':12}

def clean(path):
    t = open(path, encoding='utf-8', errors='replace').read()
    t = re.sub(r'<style.*?</style>', ' ', t, flags=re.S | re.I)
    t = re.sub(r'<[^>]+>', ' ', t)
    t = html.unescape(t)
    t = re.sub(r'[\x00-\x08\x0b\x0c\x0e-\x1f]', '', t)   # strip Word field markers
    return re.sub(r'\s+', ' ', t).strip()

def num(s):
    return float(s.replace(',', '')) if s else None

def find_date(txt):
    m = re.search(r'BRIEFING\s*(?:FOR)?\s*[-–]?\s*(\d{1,2})\s*(?:st|nd|rd|th)?\s+([A-Za-z]+)\s+(\d{4})', txt, re.I)
    if not m:
        m = re.search(r'Briefing for\s+(\d{1,2})\s*(?:st|nd|rd|th)?\s+([A-Za-z]+)\s+(\d{4})', txt, re.I)
    if not m:
        return None
    d, mon, y = int(m.group(1)), m.group(2).lower(), int(m.group(3))
    mo = MONTHS.get(mon) or ABBR.get(mon[:4]) or ABBR.get(mon[:3])
    try:
        return dt.date(y, mo, d)
    except (ValueError, TypeError):
        return None

def title_date(title):
    m = re.search(r'(\d{1,2})\s+([A-Za-z]+)\s+(\d{4})', title)
    if not m:
        return None
    d, mon, y = int(m.group(1)), m.group(2).lower(), int(m.group(3))
    mo = MONTHS.get(mon) or ABBR.get(mon[:3])
    try:
        return dt.date(y, mo, d)
    except (ValueError, TypeError):
        return None

N = r'([\d,]{3,8})'

def parse(path, title=''):
    txt = clean(path)
    rec = {'date_in_file': find_date(txt), 'date_title': title_date(title)}

    if 'ACCOMMODATION BRIEFING' in txt.upper():
        rec['layout'] = 'D1'
        # current block runs up to 'Definition'; the 12-months-ago block follows
        cur = txt.split('Definition')[0]
        m = re.search(rf'Male\s+{N}.*?Female\s+{N}.*?TOTAL\s+{N}.*?Useable Operational Capacity\**\s+{N}', cur, re.I | re.S)
        if m:
            rec['pop_male'], rec['pop_female'], rec['pop_total'], rec['uoc_total'] = [num(g) for g in m.groups()]
        pc = re.search(rf'police cells[^0-9]{{0,80}}{N}', cur, re.I)
        if pc:
            rec['police_cells'] = num(pc.group(1))
        hd = re.search(rf'Home Detention Curfew supervision\s+{N}', cur, re.I)
        if hd:
            rec['hdc'] = num(hd.group(1))
        ya = txt[txt.find('12 months ago'):] if '12 months ago' in txt else ''
        m2 = re.search(rf'Male\s+{N}.*?Female\s+{N}.*?TOTAL\s+{N}.*?Useable Operational Capacity\**\s+{N}', ya, re.I | re.S)
        if m2:
            rec['ya_pop_total'] = num(m2.group(3)); rec['ya_uoc_total'] = num(m2.group(4))
    else:
        rec['layout'] = 'D2'
        m = re.search(rf'Population\s+{N}\s+{N}\s+{N}', txt)
        if m:
            rec['pop_total'], rec['pop_prisons'], rec['pop_irc'] = [num(g) for g in m.groups()]
        m = re.search(rf'Male population\s+{N}\s+{N}\s+{N}', txt, re.I)
        if m:
            rec['pop_male'] = num(m.group(1))
        m = re.search(rf'Female population\s+{N}\s+{N}', txt, re.I)
        if m:
            rec['pop_female'] = num(m.group(1))
        m = re.search(rf'Useable Operational Capacity\s+{N}\s+{N}\s+{N}', txt, re.I)
        if m:
            rec['uoc_total'], rec['uoc_prisons'], rec['uoc_irc'] = [num(g) for g in m.groups()]
        m = re.search(rf'Home Detention Curfew caseload\s+{N}', txt, re.I)
        if m:
            rec['hdc'] = num(m.group(1))

    m = re.search(rf'less\s+{N}\s+places', txt, re.I)
    if m:
        rec['operating_margin'] = num(m.group(1))
    rec['headroom_calc'] = (rec.get('uoc_total') - rec['pop_total']) if rec.get('uoc_total') and rec.get('pop_total') else None
    rec['headroom'] = rec['headroom_calc']
    rec['date'] = rec['date_title'] or rec['date_in_file']
    return rec

FIELDS = ['date','date_in_file','date_title','layout','pop_total','pop_prisons','pop_irc','pop_male','pop_female',
          'uoc_total','uoc_prisons','uoc_irc','headroom','headroom_calc','operating_margin','hdc','police_cells',
          'ya_pop_total','ya_uoc_total','title','url','local','error']

def main(manifest, htmldir, out):
    man = {os.path.basename(r['local']).rsplit('.', 1)[0]: r for r in csv.DictReader(open(manifest)) if r['ext'] in ('doc', 'docx')}
    recs = []
    for f in sorted(glob.glob(f'{htmldir}/*.html')):
        key = os.path.basename(f).rsplit('.', 1)[0]
        r = man.get(key, {})
        rec = {'title': r.get('title', ''), 'url': r.get('url', ''), 'local': f}
        try:
            rec.update(parse(f, r.get('title', '')))
        except Exception as e:
            rec['error'] = f'{type(e).__name__}: {e}'
        recs.append(rec)
    with open(out, 'w', newline='') as fh:
        w = csv.DictWriter(fh, fieldnames=FIELDS, extrasaction='ignore')
        w.writeheader(); w.writerows(recs)
    bad = [x for x in recs if x.get('error') or not x.get('pop_total') or not x.get('uoc_total') or not x.get('date')]
    print(f'parsed {len(recs)} Word bulletins -> {out}; {len(bad)} incomplete')
    for x in bad:
        print('  ', x.get('title'), '|', x.get('layout'), '| pop', x.get('pop_total'), 'uoc', x.get('uoc_total'), '|', x.get('error', ''))

if __name__ == '__main__':
    main(sys.argv[1], sys.argv[2], sys.argv[3])
