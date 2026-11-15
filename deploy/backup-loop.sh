#!/bin/sh
# The backup of scripts/backup_databases.sh, on a timer, for the `backup` service
# (`docker compose --profile backups up -d backup`). It runs in a PostgreSQL
# image beside the server, so the client matches the server, and needs no
# Docker socket and no person at a terminal.
#
# Every LINK_LENS_BACKUP_INTERVAL_SECONDS (a day by default) it writes
# linklens-<time>.dump and dagster-<time>.dump to /backups, checks that each
# lists, and writes a .sha256 beside each. It keeps the newest
# LINK_LENS_BACKUP_KEEP dumps of each database (7 by default) and removes older
# ones, but only after a new dump of that database has been written and checked,
# so a run of failures never leaves fewer good copies. It touches only files
# named <database>-<time>.dump and their checksums: a dump named otherwise, such
# as linklens-pre-<something>.dump taken before a migration, is never removed.
# A failed dump is logged and tried again at the next interval; a partial file
# never takes a dump's name.
set -u

interval=${LINK_LENS_BACKUP_INTERVAL_SECONDS:-86400}
keep=${LINK_LENS_BACKUP_KEEP:-7}
case "$keep" in ''|*[!0-9]*|0) echo "LINK_LENS_BACKUP_KEEP must be a whole number of at least 1" >&2; exit 2;; esac
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
                # Names sort by time; everything after the newest $keep goes.
                ls -1 | grep -E "^$database-[0-9]{8}T[0-9]{6}\.dump\$" | sort -r | tail -n +"$((keep + 1))" |
                    while read -r old; do
                        rm -f "$old" "$old.sha256"
                        echo "$stamp pruned: $old"
                    done
                continue
            fi
            echo "$stamp $database: the archive lists only $entries entries; not trusting it" >&2
        else
            echo "$stamp $database: pg_dump failed" >&2
        fi
        rm -f "$file.partial"
    done
    sleep "$interval"
done
