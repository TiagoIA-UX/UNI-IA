-- ===== TABLE: UNI IA DESK REQUESTS =====
CREATE TABLE IF NOT EXISTS uni_ia_desk_requests (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    request_id TEXT NOT NULL UNIQUE,
    asset TEXT NOT NULL,
    score NUMERIC NOT NULL,
    classification TEXT NOT NULL,
    status TEXT NOT NULL CHECK (status IN ('pending_approval', 'executed', 'rejected')),
    alert JSONB NOT NULL DEFAULT '{}'::jsonb,
    execution JSONB,
    reason TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    executed_at TIMESTAMPTZ,
    rejected_at TIMESTAMPTZ
);

CREATE INDEX IF NOT EXISTS idx_uni_ia_desk_requests_status ON uni_ia_desk_requests(status);
CREATE INDEX IF NOT EXISTS idx_uni_ia_desk_requests_created_at ON uni_ia_desk_requests(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_uni_ia_desk_requests_asset ON uni_ia_desk_requests(asset);

CREATE OR REPLACE FUNCTION uni_ia_set_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS trg_uni_ia_desk_requests_updated_at ON uni_ia_desk_requests;
CREATE TRIGGER trg_uni_ia_desk_requests_updated_at
BEFORE UPDATE ON uni_ia_desk_requests
FOR EACH ROW
EXECUTE FUNCTION uni_ia_set_updated_at();

ALTER TABLE uni_ia_desk_requests ENABLE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS "Servidor IA gerencia desk requests" ON uni_ia_desk_requests;
CREATE POLICY "Servidor IA gerencia desk requests"
ON uni_ia_desk_requests
FOR ALL
TO service_role
USING (true)
WITH CHECK (true);
