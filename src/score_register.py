"""Score the forecast register against the weekly bulletins as they arrive.

The register (outputs/forecast_register.csv) holds dated headroom forecasts from each model
version, lodged on 3 September 2026 off the 24 August bulletin. Each refresh looks for a bulletin
on or after every target date, records the first one found, and marks the row scored. Forecasts
are never edited after lodging; a superseded model gets a new column, not a revised number.

Also appends a one-line weekly update to outputs/weekly_update.md, which is the brief's
'standing headroom forecast plus weekly one-line update' deliverable.
"""
import pandas as pd
import datetime as dt

ROOT = '/home/claude/prisoncap'


def main():
    w = pd.read_csv(f'{ROOT}/data/processed/weekly_population_capacity.csv', parse_dates=['date']).sort_values('date')
    R = pd.read_csv(f'{ROOT}/outputs/forecast_register.csv', parse_dates=['target_date'])
    models = [c for c in R.columns if c.startswith('v')]
    for i, r in R.iterrows():
        if bool(r.get('scored', False)):
            continue
        hit = w[w.date >= r.target_date].head(1)
        if len(hit):
            R.loc[i, 'actual_headroom'] = float(hit.headroom.iloc[0])
            R.loc[i, 'bulletin_date'] = hit.date.iloc[0].strftime('%Y-%m-%d')
            R.loc[i, 'scored'] = True
            for m in models:
                R.loc[i, f'err_{m}'] = float(r[m]) - float(hit.headroom.iloc[0])
    R.to_csv(f'{ROOT}/outputs/forecast_register.csv', index=False)

    done = R[R.scored == True]
    last = w.iloc[-1]
    line = (f"{dt.date.today():%Y-%m-%d} | bulletin {last.date:%d %b %Y}: population {last.pop_total:,.0f}, "
            f"useable capacity {last.uoc_total:,.0f}, headroom {last.headroom:,.0f}")
    if len(done):
        d = done.iloc[-1]
        errs = ', '.join(f'{m} {d[f"err_{m}"]:+.0f}' for m in models if pd.notna(d.get(f'err_{m}')))
        line += f" | last scored target {d.target_date:%d %b}: actual {d.actual_headroom:,.0f} ({errs})"
    with open(f'{ROOT}/outputs/weekly_update.md', 'a') as f:
        f.write(line + '\n')
    print(line)
    print(f'register: {len(done)}/{len(R)} targets scored')


if __name__ == '__main__':
    main()
