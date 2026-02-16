-- Create audio_assistant database and user for ai-audio-assistant project
-- This runs automatically on first PostgreSQL initialization

DO $$
BEGIN
    IF NOT EXISTS (SELECT FROM pg_catalog.pg_roles WHERE rolname = 'user') THEN
        CREATE ROLE "user" WITH LOGIN PASSWORD 'pass';
    END IF;
END
$$;

SELECT 'CREATE DATABASE audio_assistant OWNER "user"'
WHERE NOT EXISTS (SELECT FROM pg_database WHERE datname = 'audio_assistant')\gexec

GRANT ALL PRIVILEGES ON DATABASE audio_assistant TO "user";
