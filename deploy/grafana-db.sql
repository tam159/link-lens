-- The login Grafana reads the reporting models with. Run with psql as an
-- administrator, with -v password=..., after migration 0025 has created the
-- linklens_analyst group. It creates the login when it is missing and changes
-- nothing that exists. The login can read what linklens_analyst can, which is
-- the granted models in `analytics`, and nothing else.
SELECT format('CREATE ROLE linklens_grafana LOGIN PASSWORD %L IN ROLE linklens_analyst', :'password')
WHERE NOT EXISTS (SELECT FROM pg_roles WHERE rolname = 'linklens_grafana') \gexec
