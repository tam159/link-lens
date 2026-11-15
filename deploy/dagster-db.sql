-- The login and the database that hold Dagster's own storage: runs, events and
-- schedules. Run with psql as an administrator, with -v password=...
-- It creates what is missing and changes nothing that exists. The login owns
-- its database and has no right on any schema of the application's database.
SELECT format('CREATE ROLE dagster LOGIN PASSWORD %L', :'password')
WHERE NOT EXISTS (SELECT FROM pg_roles WHERE rolname = 'dagster') \gexec

SELECT 'CREATE DATABASE dagster OWNER dagster'
WHERE NOT EXISTS (SELECT FROM pg_database WHERE datname = 'dagster') \gexec

-- Dagster expects its database to keep time in UTC.
ALTER DATABASE dagster SET timezone TO 'UTC';
