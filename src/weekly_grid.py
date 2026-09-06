"""Build a correct regular weekly grid from the bulletin series.

The naive approach, df.set_index('date').asfreq('7D'), is WRONG for this series. The grid is
anchored on the first observation (a Friday in January 2011), but the bulletin reporting day moved
from Friday to Monday on 21 October 2024. From that point no observation lands on the Friday grid,
so asfreq returns all-NaN and any subsequent fill produces a flat line. Anything estimated that way
silently drops or fabricates the last two years.

Instead the grid is built from the observation sequence itself: consecutive bulletins are one step
apart regardless of weekday, and genuinely skipped weeks (bank holidays, 14 and 21 day gaps) are
inserted by interpolation and flagged.
"""
import numpy as np
import pandas as pd


def weekly_grid(df, cols, date_col='date'):
    d = df.sort_values(date_col).reset_index(drop=True)
    rows = []
    for i in range(len(d)):
        cur = d.iloc[i]
        if i > 0:
            prev = d.iloc[i - 1]
            gap = (cur[date_col] - prev[date_col]).days
            if gap >= 12:                      # 12+ days means at least one bulletin was skipped
                n = int(round(gap / 7)) - 1
                for k in range(1, n + 1):
                    f = k / (n + 1)
                    r = {date_col: prev[date_col] + pd.Timedelta(days=7 * k), 'filled': True}
                    for c in cols:
                        r[c] = prev[c] + f * (cur[c] - prev[c])
                    rows.append(r)
        r = {date_col: cur[date_col], 'filled': False}
        for c in cols:
            r[c] = cur[c]
        rows.append(r)
    g = pd.DataFrame(rows)
    g['t'] = np.arange(len(g))
    return g
