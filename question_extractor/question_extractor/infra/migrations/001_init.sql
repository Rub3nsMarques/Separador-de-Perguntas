CREATE TABLE IF NOT EXISTS extraction_jobs (
    job_id SERIAL PRIMARY KEY,
    doc_source_id VARCHAR(255) NOT NULL,
    status VARCHAR(50) NOT NULL, -- 'pending', 'processing', 'completed', 'failed'
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    error_message TEXT
);

CREATE TABLE IF NOT EXISTS extracted_questions (
    id SERIAL PRIMARY KEY,
    job_id INTEGER REFERENCES extraction_jobs(job_id),
    question_identifier VARCHAR(100), -- q_0001
    status VARCHAR(50), -- 'extracted', 'needs_review', 'error'
    confidence_score INTEGER,
    question_path VARCHAR(500),
    alternatives_json JSONB, -- Stores paths to A, B, C...
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    error_note TEXT
);
