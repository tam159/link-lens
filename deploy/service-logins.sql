-- The login the Dagster services use on the application's database. Run with
-- psql as an administrator, on that server, after the migrations, with
-- -v password=...
--
-- It can do nothing by itself: it does not inherit, and may only become
-- linklens_orchestrator (what the assets work as; it cannot record an approval,
-- a promotion or a release) or linklens_transform (what dbt works as). It is
-- created when missing; an existing login is left as it is.
DO $do$
BEGIN
    IF (SELECT count(*) FROM pg_roles
        WHERE rolname IN ('linklens_orchestrator', 'linklens_transform')) < 2 THEN
        RAISE EXCEPTION 'Run the migrations first: the roles linklens_orchestrator and linklens_transform do not exist yet';
    END IF;
END
$do$;

SELECT format(
    'CREATE ROLE linklens_orchestration LOGIN NOINHERIT PASSWORD %L '
    'IN ROLE linklens_orchestrator, linklens_transform', :'password')
WHERE NOT EXISTS (SELECT FROM pg_roles WHERE rolname = 'linklens_orchestration') \gexec
