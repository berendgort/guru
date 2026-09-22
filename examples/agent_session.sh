#!/usr/bin/env bash
# Cursor/agent session — profile + home range, then weekend / best --advise.
set -euo pipefail

guru setup --sport kitefoil --weight 78 \
  --kites 7,9,12 --wetsuits "3/2,4/3" --session-hours 3 \
  --home-lat 41.39 --home-lon 2.17 --drive-km 200 \
  --range-label "Trabucador → Leucate" --json

guru profile --json
guru weekend --json
guru best 201 -H 24 --advise --json
