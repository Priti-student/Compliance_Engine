-- LMPC Compliance Platform - database bootstrap (run as superuser)
-- Usage: psql -U postgres -h localhost -d postgres -f create_databases.sql
-- The application creates its tables automatically at startup (see seed.py),
-- so this script only needs to create the databases.

CREATE DATABASE lmpc_platform;
CREATE DATABASE lmpc_platform_test;