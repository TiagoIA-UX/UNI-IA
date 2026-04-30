-- ===== TABLE: UNI IA OPERATIONAL AUDIT =====
CREATE TABLE IF NOT EXISTS uni_ia_operational_audit (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    event_type TEXT NOT NULL,
    status TEXT NOT NULL,
    source TEXT NOT NULL DEFAULT 'ai-sentinel',
    asset TEXT,
    request_id TEXT,
    classification TEXT,
    score NUMERIC,
    details JSONB NOT NULL DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_uni_ia_operational_audit_created_at ON uni_ia_operational_audit(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_uni_ia_operational_audit_event_type ON uni_ia_operational_audit(event_type);
CREATE INDEX IF NOT EXISTS idx_uni_ia_operational_audit_request_id ON uni_ia_operational_audit(request_id);
CREATE INDEX IF NOT EXISTS idx_uni_ia_operational_audit_asset ON uni_ia_operational_audit(asset);

ALTER TABLE uni_ia_operational_audit ENABLE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS "Clientes autenticados podem ver auditoria operacional" ON uni_ia_operational_audit;
CREATE POLICY "Clientes autenticados podem ver auditoria operacional"
ON uni_ia_operational_audit FOR SELECT
TO authenticated
USING (true);

DROP POLICY IF EXISTS "Servidor IA insere auditoria operacional" ON uni_ia_operational_audit;
CREATE POLICY "Servidor IA insere auditoria operacional"
ON uni_ia_operational_audit FOR INSERT
TO service_role
WITH CHECK (true);