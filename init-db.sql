-- Database initialization script for GivSimple
-- This file is executed when the PostgreSQL container starts for the first time

-- Create the database if it doesn't exist (though it should already exist from POSTGRES_DB)
-- The database is created automatically by the PostgreSQL container using POSTGRES_DB environment variable

-- Create any necessary extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- The application will handle table creation through SQLAlchemy migrations
-- This file serves as a placeholder for any custom initialization that might be needed
