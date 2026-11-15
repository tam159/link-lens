#!/bin/sh
# Back up the two databases of the local Compose stack to a directory.
#
#   scripts/backup_databases.sh DIRECTORY [DAGSTER_KEEP_DAYS]
#
# Writes linklens-<time>.dump and dagster-<time>.dump in pg_dump's custom format,
# each with a .sha256 beside it, and checks that each archive lists.
#
# The two are kept differently on purpose. `linklens` is the application's data
# and may be the only copy: this script never deletes one of its dumps. `dagster`
# is Dagster's own run history, which can be lost without losing anything of
# the product: its dumps older than DAGSTER_KEEP_DAYS (7 by default) are removed.
# Nothing else in DIRECTORY is touched. Artifact bytes are not in either dump;
# copy the artifact directory or the bucket separately.
#
# Run from the repository root, with the `postgres` service up. It reads; it
# changes nothing in either database.
set -eu

directory=${1:?Give the directory to write the backups to}
keep_days=${2:-7}
stamp=$(date -u +%Y%m%dT%H%M%S)
mkdir -p "$directory"

for database in linklens dagster; do
    exists=$(docker compose exec -T postgres psql -U linklens -d postgres -Atc \
        "SELECT 1 FROM pg_database WHERE datname = '$database'")
    if [ "$exists" != "1" ]; then
        echo "$database: no such database, skipped"
        continue
    fi
    file="$directory/$database-$stamp.dump"
    docker compose exec -T postgres pg_dump -U linklens -d "$database" -Fc > "$file"
    entries=$(docker compose exec -T postgres pg_restore --list < "$file" | wc -l | tr -d ' ')
    if [ "$entries" -lt 10 ]; then
        echo "$database: the archive lists only $entries entries; not trusting it" >&2
        exit 1
    fi
    shasum -a 256 "$file" > "$file.sha256"
    echo "$database: $file ($entries entries)"
done

# Only Dagster's history is pruned, and only by this script's own file names.
find "$directory" -maxdepth 1 -type f \( -name 'dagster-*.dump' -o -name 'dagster-*.dump.sha256' \) \
    -mtime +"$keep_days" -print -delete | sed 's/^/pruned: /'
