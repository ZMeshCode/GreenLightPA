-- GreenLightPA Database Initialization Script
-- This script runs automatically when PostgreSQL container starts for the first time

-- Create the main application database if it doesn't exist
SELECT 'CREATE DATABASE greenlightpa_dev'
WHERE NOT EXISTS (SELECT FROM pg_database WHERE datname = 'greenlightpa_dev')\gexec

-- Create N8n database if it doesn't exist
SELECT 'CREATE DATABASE n8n'
WHERE NOT EXISTS (SELECT FROM pg_database WHERE datname = 'n8n')\gexec

-- Connect to the main database
\c greenlightpa_dev;

-- Install required extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "vector";
CREATE EXTENSION IF NOT EXISTS "pg_stat_statements";

-- Create application schemas
CREATE SCHEMA IF NOT EXISTS healthcare;
CREATE SCHEMA IF NOT EXISTS workflows;
CREATE SCHEMA IF NOT EXISTS analytics;
CREATE SCHEMA IF NOT EXISTS audit;

-- Grant permissions to application user
GRANT ALL PRIVILEGES ON DATABASE greenlightpa_dev TO greenlight_user;
GRANT ALL PRIVILEGES ON SCHEMA healthcare TO greenlight_user;
GRANT ALL PRIVILEGES ON SCHEMA workflows TO greenlight_user;
GRANT ALL PRIVILEGES ON SCHEMA analytics TO greenlight_user;
GRANT ALL PRIVILEGES ON SCHEMA audit TO greenlight_user;

-- Create basic tables for healthcare data
CREATE TABLE IF NOT EXISTS healthcare.patients (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    patient_id VARCHAR(255) UNIQUE NOT NULL,
    first_name VARCHAR(255),
    last_name VARCHAR(255),
    date_of_birth DATE,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS healthcare.prior_auth_requests (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    patient_id UUID REFERENCES healthcare.patients(id),
    request_data JSONB,
    status VARCHAR(50),
    payer_id VARCHAR(255),
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Create vector storage table for policy embeddings
CREATE TABLE IF NOT EXISTS healthcare.policy_embeddings (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    payer_id VARCHAR(255),
    policy_text TEXT,
    embedding vector(1536),
    metadata JSONB,
    created_at TIMESTAMP DEFAULT NOW()
);

-- Create workflow tracking tables
CREATE TABLE IF NOT EXISTS workflows.executions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    workflow_id VARCHAR(255),
    execution_data JSONB,
    status VARCHAR(50),
    started_at TIMESTAMP DEFAULT NOW(),
    completed_at TIMESTAMP
);

-- Create audit logging table
CREATE TABLE IF NOT EXISTS audit.audit_log (
    id SERIAL PRIMARY KEY,
    user_id VARCHAR(255),
    action VARCHAR(50),
    table_name VARCHAR(100),
    record_id VARCHAR(255),
    details JSONB,
    ip_address INET,
    user_agent TEXT,
    timestamp TIMESTAMP DEFAULT NOW()
);

-- Create indexes for performance
CREATE INDEX IF NOT EXISTS idx_patients_patient_id ON healthcare.patients(patient_id);
CREATE INDEX IF NOT EXISTS idx_prior_auth_patient_id ON healthcare.prior_auth_requests(patient_id);
CREATE INDEX IF NOT EXISTS idx_prior_auth_status ON healthcare.prior_auth_requests(status);
CREATE INDEX IF NOT EXISTS idx_policy_embeddings_payer ON healthcare.policy_embeddings(payer_id);
CREATE INDEX IF NOT EXISTS idx_audit_log_timestamp ON audit.audit_log(timestamp);
CREATE INDEX IF NOT EXISTS idx_audit_log_user_id ON audit.audit_log(user_id);

-- Connect to N8n database and set up permissions
\c n8n;

-- Grant permissions for N8n database
GRANT ALL PRIVILEGES ON DATABASE n8n TO greenlight_user;

-- Create N8n user if doesn't exist
DO $$
BEGIN
    IF NOT EXISTS (SELECT FROM pg_user WHERE usename = 'n8n_user') THEN
        CREATE USER n8n_user WITH PASSWORD 'n8n_password_123';
    END IF;
END
$$;

GRANT ALL PRIVILEGES ON DATABASE n8n TO n8n_user;

-- Return to main database
\c greenlightpa_dev;

-- Insert sample data for development (only if tables are empty)
INSERT INTO healthcare.patients (patient_id, first_name, last_name, date_of_birth)
SELECT 'PAT001', 'John', 'Doe', '1980-01-15'
WHERE NOT EXISTS (SELECT 1 FROM healthcare.patients WHERE patient_id = 'PAT001');

INSERT INTO healthcare.patients (patient_id, first_name, last_name, date_of_birth)
SELECT 'PAT002', 'Jane', 'Smith', '1975-06-20'
WHERE NOT EXISTS (SELECT 1 FROM healthcare.patients WHERE patient_id = 'PAT002');

-- Create development roles
DO $$
BEGIN
    IF NOT EXISTS (SELECT FROM pg_roles WHERE rolname = 'greenlightpa_readonly') THEN
        CREATE ROLE greenlightpa_readonly;
    END IF;
END
$$;

GRANT CONNECT ON DATABASE greenlightpa_dev TO greenlightpa_readonly;
GRANT USAGE ON SCHEMA healthcare, workflows, analytics, audit TO greenlightpa_readonly;
GRANT SELECT ON ALL TABLES IN SCHEMA healthcare, workflows, analytics, audit TO greenlightpa_readonly;

-- Print success message
\echo 'GreenLightPA database initialization completed successfully!'
\echo 'Created schemas: healthcare, workflows, analytics, audit'
\echo 'Installed extensions: uuid-ossp, vector, pg_stat_statements'
\echo 'Sample data inserted for development' 