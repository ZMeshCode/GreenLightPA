-- Enable pgvector extension
CREATE EXTENSION IF NOT EXISTS vector;

-- Create synthetic patients table
CREATE TABLE IF NOT EXISTS synthetic_patients (
    id SERIAL PRIMARY KEY,
    patient_id VARCHAR(255) UNIQUE NOT NULL,
    fhir_bundle JSONB NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create clinical notes table
CREATE TABLE IF NOT EXISTS clinical_notes (
    id SERIAL PRIMARY KEY,
    patient_id VARCHAR(255) NOT NULL,
    note_id VARCHAR(255) UNIQUE NOT NULL,
    original_text TEXT NOT NULL,
    deidentified_text TEXT,
    extracted_codes JSONB,
    specialty VARCHAR(100),
    prior_auth_required BOOLEAN DEFAULT FALSE,
    prior_auth_status VARCHAR(50), -- 'approved', 'denied', 'pending'
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (patient_id) REFERENCES synthetic_patients(patient_id)
);

-- Create policy chunks table for RAG
CREATE TABLE IF NOT EXISTS policy_chunks (
    id SERIAL PRIMARY KEY,
    payer_id VARCHAR(100) NOT NULL,
    policy_id VARCHAR(255) NOT NULL,
    specialty VARCHAR(100),
    chunk_text TEXT NOT NULL,
    chunk_embedding vector(384), -- all-MiniLM-L6-v2 produces 384-dim vectors
    metadata JSONB,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create indexes for performance
CREATE INDEX IF NOT EXISTS idx_clinical_notes_patient_id ON clinical_notes(patient_id);
CREATE INDEX IF NOT EXISTS idx_clinical_notes_specialty ON clinical_notes(specialty);
CREATE INDEX IF NOT EXISTS idx_clinical_notes_prior_auth ON clinical_notes(prior_auth_required);
CREATE INDEX IF NOT EXISTS idx_policy_chunks_payer_specialty ON policy_chunks(payer_id, specialty);
CREATE INDEX IF NOT EXISTS idx_policy_chunks_embedding ON policy_chunks USING ivfflat (chunk_embedding vector_cosine_ops);

-- Insert sample payer policies for testing
INSERT INTO policy_chunks (payer_id, policy_id, specialty, chunk_text, metadata) VALUES
('BCBS', 'ONCO-001', 'oncology', 'Prior authorization required for chemotherapy regimens exceeding $10,000 per cycle. Required documentation: pathology report, staging information, performance status.', '{"category": "chemotherapy", "cost_threshold": 10000}'),
('AETNA', 'RHEUM-001', 'rheumatology', 'Biologic DMARDs require prior authorization. Patient must have failed at least two conventional DMARDs. Required: disease activity scores, previous treatment history.', '{"category": "biologics", "prior_failures_required": 2}'),
('HUMANA', 'IMG-001', 'imaging', 'Advanced imaging (MRI, CT with contrast) requires prior authorization for non-emergency cases. Clinical indication and previous imaging results must be provided.', '{"category": "advanced_imaging", "emergency_exempt": true}');

-- Create a function to search similar policy chunks
CREATE OR REPLACE FUNCTION search_similar_policies(
    query_embedding vector(384),
    match_threshold float DEFAULT 0.8,
    match_count int DEFAULT 10,
    filter_specialty text DEFAULT NULL
)
RETURNS TABLE (
    id int,
    payer_id varchar,
    policy_id varchar,
    specialty varchar,
    chunk_text text,
    similarity float,
    metadata jsonb
)
LANGUAGE sql
AS $$
    SELECT
        pc.id,
        pc.payer_id,
        pc.policy_id,
        pc.specialty,
        pc.chunk_text,
        1 - (pc.chunk_embedding <=> query_embedding) as similarity,
        pc.metadata
    FROM policy_chunks pc
    WHERE 
        (filter_specialty IS NULL OR pc.specialty = filter_specialty)
        AND (1 - (pc.chunk_embedding <=> query_embedding)) > match_threshold
    ORDER BY pc.chunk_embedding <=> query_embedding
    LIMIT match_count;
$$; 