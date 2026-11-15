#!/bin/sh
# Puts the instance configuration that came with the code into DAGSTER_HOME, then
# runs the command. DAGSTER_HOME is a volume that outlives the image, so a copy
# made once would go stale; this one is made at every start.
set -e
mkdir -p "$DAGSTER_HOME"
cp /app/orchestration/dagster.yaml "$DAGSTER_HOME/dagster.yaml"
exec "$@"
