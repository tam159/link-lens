#!/bin/sh
# The backup of scripts/backup_databases.sh, on a timer, for the `backup` service
# (`docker compose --profile backups up -d backup`). It runs in a PostgreSQL
# image beside the server, so the client matches the server, and needs no
# Docker socket and no person at a terminal.
#
# Every LINK_LENS_BACKUP_INTERVAL_SECONDS (a day by default) it writes
# linklens-<time>.dump and dagster-<time>.dump to /backups, checks that each
# lists, and writes a .sha256 beside each. The same rule as the script: it never
# deletes a `linklens` dump, which may be the only copy of the application's
# data; it removes its own `dagster` dumps older than LINK_LENS_DAGSTER_BACKUP_DAYS.
# A failed dump is logged and tried again at the next interval; a partial file
# never takes a dump's name.
set -u

interval=${LINK_LENS_BACKUP_INTERVAL_SECONDS:-86400}
keep_days=${LINK_LENS_DAGSTER_BACKUP_DAYS:-7}
cd /backups

while true; do
    stamp=$(date -u +%Y%m%dT%H%M%S)
    for database in linklens dagster; do
        exists=$(psql -h postgres -U linklens -d postgres -Atc \
            "SELECT 1 FROM pg_database WHERE datname = '$database'" 2>/dev/null)
        if [ "$exists" != "1" ]; then
            echo "$stamp $database: no such database, skipped"
            continue
        fi
        file="$database-$stamp.dump"
        if pg_dump -h postgres -U linklens -d "$database" -Fc -f "$file.partial"; then
            entries=$(pg_restore --list "$file.partial" | wc -l | tr -d ' ')
            if [ "$entries" -ge 10 ]; then
                mv "$file.partial" "$file"
                sha256sum "$file" > "$file.sha256"
                echo "$stamp $database: $file ($entries entries)"
                continue
            fi
            echo "$stamp $database: the archive lists only $entries entries; not trusting it" >&2
        else
            echo "$stamp $database: pg_dump failed" >&2
        fi
        rm -f "$file.partial"
    done
    find . -maxdepth 1 -type f \( -name 'dagster-*.dump' -o -name 'dagster-*.dump.sha256' \) \
        -mtime +"$keep_days" -print -delete | sed "s/^/$stamp pruned: /"
    sleep "$interval"
done
