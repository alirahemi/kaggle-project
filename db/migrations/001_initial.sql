-- Initial schema for German Bureaucracy AI Agent
-- Applied via docker-compose postgres init and Alembic baseline

CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS vector;

CREATE TABLE IF NOT EXISTS users (
    id VARCHAR(128) PRIMARY KEY,
    locale VARCHAR(8) NOT NULL DEFAULT 'en',
    bundesland VARCHAR(4) NOT NULL DEFAULT 'BE',
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS sessions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id VARCHAR(128) NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    locale VARCHAR(8) NOT NULL DEFAULT 'en',
    bundesland VARCHAR(4) NOT NULL DEFAULT 'BE',
    status VARCHAR(32) NOT NULL DEFAULT 'active',
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    ended_at TIMESTAMPTZ
);

CREATE INDEX IF NOT EXISTS idx_sessions_user_id ON sessions(user_id);

CREATE TABLE IF NOT EXISTS documents (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    session_id UUID NOT NULL REFERENCES sessions(id) ON DELETE CASCADE,
    filename VARCHAR(512) NOT NULL,
    content_type VARCHAR(128) NOT NULL,
    storage_path VARCHAR(1024) NOT NULL,
    page_count INTEGER NOT NULL DEFAULT 1,
    status VARCHAR(32) NOT NULL DEFAULT 'uploaded',
    pii_redacted BOOLEAN NOT NULL DEFAULT TRUE,
    redacted_preview TEXT,
    retention_expires_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    deleted_at TIMESTAMPTZ
);

CREATE INDEX IF NOT EXISTS idx_documents_session_id ON documents(session_id);

CREATE TABLE IF NOT EXISTS letter_analyses (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    session_id UUID NOT NULL REFERENCES sessions(id) ON DELETE CASCADE,
    document_id UUID NOT NULL REFERENCES documents(id) ON DELETE CASCADE,
    status VARCHAR(32) NOT NULL DEFAULT 'processing',
    authority VARCHAR(64),
    letter_type VARCHAR(64),
    confidence DOUBLE PRECISION,
    extraction JSONB,
    explanation JSONB,
    requires_review BOOLEAN NOT NULL DEFAULT FALSE,
    pipeline_stage VARCHAR(64),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    completed_at TIMESTAMPTZ
);

CREATE INDEX IF NOT EXISTS idx_letter_analyses_session_id ON letter_analyses(session_id);
CREATE INDEX IF NOT EXISTS idx_letter_analyses_document_id ON letter_analyses(document_id);

CREATE TABLE IF NOT EXISTS action_plans (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    analysis_id UUID NOT NULL UNIQUE REFERENCES letter_analyses(id) ON DELETE CASCADE,
    urgent JSONB NOT NULL DEFAULT '[]'::jsonb,
    this_week JSONB NOT NULL DEFAULT '[]'::jsonb,
    later JSONB NOT NULL DEFAULT '[]'::jsonb,
    optional JSONB NOT NULL DEFAULT '[]'::jsonb,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_action_plans_analysis_id ON action_plans(analysis_id);

CREATE TABLE IF NOT EXISTS audit_events (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id VARCHAR(128) REFERENCES users(id) ON DELETE SET NULL,
    session_id UUID,
    event_type VARCHAR(64) NOT NULL,
    resource_type VARCHAR(64),
    resource_id VARCHAR(128),
    payload JSONB,
    ip_address VARCHAR(64),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_audit_events_user_id ON audit_events(user_id);
CREATE INDEX IF NOT EXISTS idx_audit_events_session_id ON audit_events(session_id);
CREATE INDEX IF NOT EXISTS idx_audit_events_created_at ON audit_events(created_at DESC);

-- Knowledge embeddings table (used by RAG MCP)
CREATE TABLE IF NOT EXISTS knowledge_chunks (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    source_path VARCHAR(1024) NOT NULL,
    authority VARCHAR(64),
    chunk_text TEXT NOT NULL,
    embedding vector(768),
    metadata JSONB DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_knowledge_chunks_authority ON knowledge_chunks(authority);
