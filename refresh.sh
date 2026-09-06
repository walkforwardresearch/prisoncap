#!/usr/bin/env bash
# Weekly refresh for the prison capacity model.
#
# Order matters. The notes diff runs BEFORE any series is rebuilt and stops the run if a source
# publication has changed its definitions. That is deliberate: every material error in this
# project came from reading numbers before reading the notes that qualified them.
#
#   ./refresh.sh            full refresh
#   ./refresh.sh --force    continue past a notes change (after a human has read the diff)

set -euo pipefail
cd "$(dirname "$0")"
FORCE="${1:-}"

echo "== 1. fetch"
python3 src/fetch.py .

echo "== 2. notes gate"
if ! python3 src/notes_diff.py raw data/notes_state; then
  if [ "$FORCE" != "--force" ]; then
    echo "STOP: a source publication changed its notes. Read the diff above, then rerun with --force."
    exit 2
  fi
  echo "continuing past notes change (--force)"
fi

echo "== 3. weekly series"
python3 src/parse_weekly.py manifests/bulletins.csv data/processed/weekly_parsed_raw.csv
python3 src/build_series.py data/processed/weekly_parsed_raw.csv data/processed

echo "== 4. monthly establishment panel"
python3 src/parse_monthly.py manifests/bulletins.csv data/processed/monthly_establishments.csv

echo "== 5. projections and scorecard"
python3 src/parse_projections.py raw/projections data/processed
python3 src/score_projections.py data/processed/projections_long.csv data/processed/weekly_population_capacity.csv outputs
python3 src/decompose_projections.py data/processed/projections_long.csv outputs

echo "== 6. benchmarks"
python3 src/benchmarks.py data/processed/weekly_population_capacity.csv outputs/benchmark_table.csv

echo "== 7. headroom projection and register"
python3 src/headroom_model_v3.py
python3 src/score_register.py

echo "== done $(date -u +%FT%TZ)"
