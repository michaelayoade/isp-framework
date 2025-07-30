#!/bin/bash
set -e

# Create test database for running the test suite
psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" --dbname "$POSTGRES_DB" <<-EOSQL
    CREATE DATABASE IF NOT EXISTS ispframework_test;
    GRANT ALL PRIVILEGES ON DATABASE ispframework_test TO $POSTGRES_USER;
EOSQL

echo "Test database 'ispframework_test' created successfully"
