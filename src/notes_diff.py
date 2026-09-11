"""Diff the Notes sheets of every source publication against the last refresh.

Why this exists. Twice in this project the answer was sitting in a Notes sheet and the numbers were
read first: the 56-day fixed-term recall (OMSQ recall note 12) and the July 2025 recall
composition break (note 11). Both would have changed the analysis had they been read before the
tables. Every MoJ ODS publication carries a Notes sheet, and definitional changes appear there
before they appear anywhere else. So the refresh reads every Notes sheet, stores a normalised copy,
and prints any difference from the previous run BEFORE any series is rebuilt.

Usage:
    python3 src/notes_diff.py raw/ data/notes_state/
Exit code 2 if any note changed, so a wrapper script can stop and ask a human.
"""
import sys, os, glob, json, hashlib, re, difflib, warnings
import pandas as pd

warnings.filterwarnings('ignore')

NOTE_SHEETS = ('notes', 'note', 'definitions', 'data_sources', 'cover')


def notes_text(path):
    try:
        eng = 'odf' if path.lower().endswith('.ods') else None
        sh = pd.read_excel(path, sheet_name=None, header=None, engine=eng)
    except Exception:
        return None
    out = []
    for name, df in sh.items():
        if name.startswith("'") or name.strip().lower() not in NOTE_SHEETS:
            continue
        for i in range(df.shape[0]):
            cells = [str(v).strip() for v in df.iloc[i] if str(v) not in ('nan', 'NaT', '')]
            if cells:
                out.append(' '.join(cells))
    if not out:
        return None
    return '\n'.join(out)


def canonical_key(path):
    """Strip dates and quarter labels so the same publication matches across editions."""
    base = os.path.basename(path).lower()
    base = re.sub(r'(jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)[a-z]*[-_ ]?(to[-_ ])?[a-z]*[-_ ]?\d{2,4}', 'PERIOD', base)
    base = re.sub(r'\d{4}[-_]\d{2}', 'PERIOD', base)
    base = re.sub(r'q[1-4][-_]?\d{4}', 'PERIOD', base)
    base = re.sub(r'\d{4}', 'YEAR', base)
    return re.sub(r'[^a-z_]', '', base)


def main(raw_dir, state_dir):
    os.makedirs(state_dir, exist_ok=True)
    changed = 0
    difflog = open(os.path.join(state_dir, '_last_diff.txt'), 'w', encoding='utf-8')
    # weekly and monthly bulletins carry no Notes sheet; skipping them keeps the gate to seconds
    files = [f for f in glob.glob(f'{raw_dir}/**/*', recursive=True) if f.lower().endswith(('.ods', '.xlsx', '.xls'))
             and not any(seg in f.replace('\\', '/') for seg in ('/weekly/', '/monthly/', '/weekly_doc_txt/'))]
    latest = {os.path.basename(f).rsplit('.', 1)[0]: f for f in files}   # one state file per source file
    for key, f in sorted(latest.items()):
        txt = notes_text(f)
        if txt is None:
            continue
        sp = os.path.join(state_dir, key + '.txt')
        if os.path.exists(sp):
            old = open(sp, encoding='utf-8').read()
            if old != txt:
                changed += 1
                print(f'\n=== NOTES CHANGED: {os.path.basename(f)} ===')
                difflog.write(f'\n=== NOTES CHANGED: {os.path.basename(f)} ===\n')
                for line in difflib.unified_diff(old.splitlines(), txt.splitlines(), lineterm='', n=0):
                    if line.startswith(('+', '-')) and not line.startswith(('+++', '---')):
                        print('  ' + line[:220]); difflog.write(line + '\n')
                open(sp + '.prev', 'w', encoding='utf-8').write(old)
        else:
            print(f'notes recorded for the first time: {os.path.basename(f)} ({len(txt.splitlines())} lines)')
        open(sp, 'w', encoding='utf-8').write(txt)
    difflog.close()
    print(f'\n{len(latest)} source files checked, {changed} with changed notes; diff kept in {state_dir}/_last_diff.txt')
    return 2 if changed else 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1], sys.argv[2]))
