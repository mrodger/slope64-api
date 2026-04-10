#!/bin/bash
set -e

PGDATA=/var/lib/postgresql/data
PGUSER=postgres
PGDB=slope64

# Initialise data directory on first boot
if [ ! -f "$PGDATA/PG_VERSION" ]; then
    echo "[entrypoint] Initialising PostgreSQL data directory..."
    mkdir -p "$PGDATA"
    chown postgres:postgres "$PGDATA"
    su -c "initdb -D $PGDATA --encoding=UTF8 --locale=C" postgres

    # Allow local connections without password
    echo "host all all 127.0.0.1/32 trust" >> "$PGDATA/pg_hba.conf"
    echo "local all all trust"              >> "$PGDATA/pg_hba.conf"

    # Start postgres briefly to create DB + schema
    su -c "pg_ctl start -D $PGDATA -w -t 30 -o '-c listen_addresses=127.0.0.1'" postgres
    su -c "createdb $PGDB" postgres
    su -c "psql -d $PGDB -f /app/init.sql" postgres
    su -c "pg_ctl stop -D $PGDATA -w" postgres

    echo "[entrypoint] Database initialised."
else
    echo "[entrypoint] Data directory exists, skipping init."
fi

exec supervisord -c /etc/supervisord.conf
