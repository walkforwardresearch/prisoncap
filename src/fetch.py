"""Fetch every source from gov.uk via the content API. Deterministic routes only, no page scraping.

Routes:
  weekly + monthly bulletins   collection /government/collections/prison-population-statistics
                               -> each annual page -> details.attachments
  projections                  /government/statistics/prison-population-projections-ns (2008-2019 direct)
                               plus one page per edition from 2020
  OMSQ                         /government/collections/offender-management-statistics-quarterly -> latest
  CJS quarterly                /government/collections/criminal-justice-statistics-quarterly -> latest
  workforce                    latest hm-prison-probation-service-workforce-quarterly-* page
  safety in custody            latest safety-in-custody-quarterly-update-* page
  capacity statement           /government/publications/annual-statement-on-prison-capacity-YYYY

Downloads are idempotent: a file already present with size > 0 is not re-fetched.
"""
import sys, os, re, json, csv, time, urllib.request, datetime as dt

API = 'https://www.gov.uk/api/content'
UA = {'User-Agent': 'prisoncap-research/0.1'}


def api(bp):
    req = urllib.request.Request(API + bp, headers=UA)
    return json.load(urllib.request.urlopen(req, timeout=60))


def get(url, path):
    if os.path.exists(path) and os.path.getsize(path) > 0:
        return 'cached'
    os.makedirs(os.path.dirname(path), exist_ok=True)
    for _ in range(3):
        try:
            req = urllib.request.Request(url, headers=UA)
            open(path, 'wb').write(urllib.request.urlopen(req, timeout=120).read())
            return 'ok'
        except Exception as e:
            err = e; time.sleep(2)
    return f'FAIL {err}'


def latest_in_collection(collection_bp, title_regex):
    docs = api(collection_bp).get('links', {}).get('documents', [])
    docs = [d for d in docs if re.search(title_regex, d.get('title', ''), re.I)]
    docs.sort(key=lambda d: d.get('public_updated_at', ''), reverse=True)
    return docs[0]['base_path'] if docs else None


def fetch_bulletins(root):
    docs = api('/government/collections/prison-population-statistics')['links']['documents']
    rows = []
    for d in docs:
        j = api(d['base_path'])
        for a in j.get('details', {}).get('attachments', []):
            t = a.get('title', ''); u = a.get('url', '')
            if not u:
                continue
            kind = 'weekly' if re.search(r'week', t, re.I) or 'Population bulletin: 4 November 2016' in t else \
                   'monthly' if re.search(r'month', t, re.I) else 'other'
            if kind == 'other':
                continue
            mid = re.search(r'/media/([0-9a-f]+)/|/file/(\d+)/', u)
            tag = (mid.group(1) or mid.group(2)) if mid else 'x'
            ext = u.rsplit('.', 1)[-1].lower()
            path = f"{root}/raw/{kind}/{tag}_{u.rsplit('/', 1)[-1]}"
            rows.append(dict(kind=kind, title=t, page=d['title'], url=u, ext=ext, local=path, status=get(u, path)))
        time.sleep(0.2)
    with open(f'{root}/manifests/bulletins.csv', 'w', newline='') as f:
        w = csv.DictWriter(f, fieldnames=rows[0].keys()); w.writeheader(); w.writerows(rows)
    print(f"bulletins: {sum(r['kind']=='weekly' for r in rows)} weekly, {sum(r['kind']=='monthly' for r in rows)} monthly, "
          f"{sum(r['status'].startswith('FAIL') for r in rows)} failed")


def fetch_projections(root):
    rows = []
    ns = api('/government/statistics/prison-population-projections-ns')
    pages = [('ns', ns)]
    for d in ns.get('links', {}).get('related_statistical_data_sets', []) + ns.get('links', {}).get('documents', []):
        pass
    for yr in range(2020, dt.date.today().year + 1):
        for slug in (f'prison-population-projections-{yr}-to-{yr + 6}', f'prison-population-projections-{yr}-to-{yr + 5}'):
            try:
                pages.append((slug, api('/government/statistics/' + slug)))
                break
            except Exception:
                continue
    for slug, j in pages:
        for a in j.get('details', {}).get('attachments', []):
            u = a.get('url', ''); t = a.get('title', '')
            if 'assets.publishing' not in u or not u.lower().endswith(('.ods', '.xls', '.xlsx')):
                continue
            m = re.search(r'(20\d\d)\s*(?:to|-|–)\s*(20\d\d)', t)
            ed = f'{m.group(1)}-{m.group(2)}' if m else slug
            path = f"{root}/raw/projections/{ed}.{u.rsplit('.', 1)[-1].lower()}"
            rows.append(dict(edition=ed, title=t, url=u, local=path, status=get(u, path)))
    with open(f'{root}/manifests/projections.csv', 'w', newline='') as f:
        w = csv.DictWriter(f, fieldnames=rows[0].keys()); w.writeheader(); w.writerows(rows)
    print(f'projections: {len(set(r["edition"] for r in rows))} editions')


def fetch_latest(root, collection_bp, title_regex, subdir, file_regex):
    bp = latest_in_collection(collection_bp, title_regex)
    if not bp:
        print(f'{subdir}: nothing found'); return
    j = api(bp)
    n = 0
    for a in j.get('details', {}).get('attachments', []):
        u = a.get('url', '')
        if re.search(file_regex, u, re.I):
            get(u, f"{root}/raw/{subdir}/{u.rsplit('/', 1)[-1]}"); n += 1
    print(f'{subdir}: {n} files from {bp}')


def main(root):
    os.makedirs(f'{root}/manifests', exist_ok=True)
    fetch_bulletins(root)
    fetch_projections(root)
    fetch_latest(root, '/government/collections/offender-management-statistics-quarterly',
                 r'offender management statistics quarterly', 'omsq', r'\.(ods|zip)$')
    fetch_latest(root, '/government/collections/criminal-justice-statistics-quarterly',
                 r'criminal justice statistics quarterly', 'cjs', r'overview-tables.*\.ods$')
    for yr in range(dt.date.today().year, 2023, -1):
        try:
            j = api(f'/government/publications/annual-statement-on-prison-capacity-{yr}')
            for a in j['details']['attachments']:
                get(a['url'], f"{root}/raw/capacity_statement/{a['url'].rsplit('/', 1)[-1]}")
            print(f'capacity statement: {yr}'); break
        except Exception:
            continue


if __name__ == '__main__':
    main(sys.argv[1] if len(sys.argv) > 1 else '.')
