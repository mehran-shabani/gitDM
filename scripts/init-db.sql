-- Initialize database for GitDM
-- This script is used by docker-compose to set up the PostgreSQL database

-- Create the main database if it doesn't exist
-- (This is typically handled by the POSTGRES_DB environment variable)

-- Create extensions that might be useful for the application
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pg_trgm";

-- Set timezone
SET timezone = 'UTC';