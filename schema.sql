-- ========================================================
-- ZAIRYX IA / UNI IA - DATABASE SCHEMA
-- ========================================================
-- Schema consolidado de todas as migrações Supabase
-- Este arquivo define a estrutura completa do banco de dados

-- ===== EXTENSIONS =====
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- ===== FUNCTION: SET UPDATED_AT =====
CREATE OR REPLACE FUNCTION set_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE OR REPLACE FUNCTION uni_ia_set_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- ===== TABLE: ZAIRYX USERS (CLIENTES ASSINANTES) =====
CREATE TABLE IF NOT EXISTS zairyx_users (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    email TEXT UNIQUE NOT NULL,
    full_name TEXT NOT NULL,
    stripe_customer_id TEXT UNIQUE,
    subscription_plan TEXT DEFAULT 'FREE' CHECK (subscription_plan IN ('FREE', 'PREMIUM', 'ENTERPRISE')),
    subscription_status TEXT DEFAULT 'INACTIVE' CHECK (subscription_status IN ('ACTIVE', 'INACTIVE', 'PAST_DUE', 'CANCELED')),
    telegram_chat_id TEXT,
    preferences JSONB DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Índices para ZAIRYX_USERS
CREATE INDEX IF NOT EXISTS idx_users_email ON zairyx_users(email);
CREATE INDEX IF NOT EXISTS idx_users_telegram ON zairyx_users(telegram_chat_id);

-- Trigger para atualizar updated_at em ZAIRYX_USERS
CREATE TRIGGER IF NOT EXISTS trg_zairyx_users_updated_at
BEFORE UPDATE ON zairyx_users
FOR EACH ROW EXECUTE FUNCTION set_updated_at();

-- ===== TABLE: ZAIRYX ALERTS HISTORY (MEMÓRIA INSTITUCIONAL DO UNICÓRNIO) =====
CREATE TABLE IF NOT EXISTS zairyx_alerts_history (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    asset TEXT NOT NULL,
    score NUMERIC NOT NULL,
    classification TEXT NOT NULL,
    signal_agents JSONB NOT NULL DEFAULT '[]'::jsonb,
    explanation TEXT NOT NULL,
    target_channels TEXT[] DEFAULT ARRAY['FREE']::TEXT[],
    dispatched_at TIMESTAMPTZ DEFAULT NOW()
);

-- Índices para ZAIRYX_ALERTS_HISTORY
CREATE INDEX IF NOT EXISTS idx_alerts_asset ON zairyx_alerts_history(asset);
CREATE INDEX IF NOT EXISTS idx_alerts_date ON zairyx_alerts_history(dispatched_at DESC);

-- ===== TABLE: UNI IA EVENTS (A/B TESTING) =====
CREATE TABLE IF NOT EXISTS uni_ia_events (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    event TEXT NOT NULL,
    page TEXT NOT NULL,
    variant TEXT NOT NULL CHECK (variant IN ('A', 'B')),
    locale TEXT NOT NULL DEFAULT 'en',
    session_id TEXT,
    event_ts TIMESTAMPTZ,
    details JSONB NOT NULL DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Índices para UNI_IA_EVENTS
CREATE INDEX IF NOT EXISTS idx_uni_ia_events_page_date ON uni_ia_events(page, created_at DESC);
CREATE INDEX IF NOT EXISTS idx_uni_ia_events_variant ON uni_ia_events(variant);
CREATE INDEX IF NOT EXISTS idx_uni_ia_events_event ON uni_ia_events(event);

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

-- Índices para UNI_IA_OPERATIONAL_AUDIT
CREATE INDEX IF NOT EXISTS idx_uni_ia_operational_audit_created_at ON uni_ia_operational_audit(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_uni_ia_operational_audit_event_type ON uni_ia_operational_audit(event_type);
CREATE INDEX IF NOT EXISTS idx_uni_ia_operational_audit_request_id ON uni_ia_operational_audit(request_id);
CREATE INDEX IF NOT EXISTS idx_uni_ia_operational_audit_asset ON uni_ia_operational_audit(asset);

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

-- Índices para UNI_IA_DESK_REQUESTS
CREATE INDEX IF NOT EXISTS idx_uni_ia_desk_requests_status ON uni_ia_desk_requests(status);
CREATE INDEX IF NOT EXISTS idx_uni_ia_desk_requests_created_at ON uni_ia_desk_requests(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_uni_ia_desk_requests_asset ON uni_ia_desk_requests(asset);

-- Trigger para atualizar updated_at em UNI_IA_DESK_REQUESTS
CREATE TRIGGER IF NOT EXISTS trg_uni_ia_desk_requests_updated_at
BEFORE UPDATE ON uni_ia_desk_requests
FOR EACH ROW
EXECUTE FUNCTION uni_ia_set_updated_at();

-- ===== ROW LEVEL SECURITY (RLS) =====
-- Habilitar RLS nas tabelas essenciais
ALTER TABLE zairyx_users ENABLE ROW LEVEL SECURITY;
ALTER TABLE zairyx_alerts_history ENABLE ROW LEVEL SECURITY;
ALTER TABLE uni_ia_operational_audit ENABLE ROW LEVEL SECURITY;
ALTER TABLE uni_ia_desk_requests ENABLE ROW LEVEL SECURITY;

-- ===== POLICIES: ZAIRYX USERS =====
-- Usuários só podem acessar seu próprio perfil
DROP POLICY IF EXISTS "Usuários podem ver o próprio perfil" ON zairyx_users;
CREATE POLICY "Usuários podem ver o próprio perfil"
ON zairyx_users FOR SELECT
USING (auth.uid() = id);

DROP POLICY IF EXISTS "Usuários podem atualizar o próprio perfil" ON zairyx_users;
CREATE POLICY "Usuários podem atualizar o próprio perfil"
ON zairyx_users FOR UPDATE
USING (auth.uid() = id);

-- ===== POLICIES: ZAIRYX ALERTS HISTORY =====
-- Clientes autenticados podem ler o histórico de alertas
DROP POLICY IF EXISTS "Clientes autenticados podem ver histórico" ON zairyx_alerts_history;
CREATE POLICY "Clientes autenticados podem ver histórico"
ON zairyx_alerts_history FOR SELECT
TO authenticated
USING (true);

-- Apenas o Backend de IA (service_role) pode inserir alertas
DROP POLICY IF EXISTS "Servidor IA insere os alertas fechados" ON zairyx_alerts_history;
CREATE POLICY "Servidor IA insere os alertas fechados"
ON zairyx_alerts_history FOR INSERT
TO service_role
WITH CHECK (true);

-- ===== POLICIES: UNI IA OPERATIONAL AUDIT =====
-- Clientes autenticados podem ver auditoria operacional
DROP POLICY IF EXISTS "Clientes autenticados podem ver auditoria operacional" ON uni_ia_operational_audit;
CREATE POLICY "Clientes autenticados podem ver auditoria operacional"
ON uni_ia_operational_audit FOR SELECT
TO authenticated
USING (true);

-- Servidor IA insere eventos de auditoria
DROP POLICY IF EXISTS "Servidor IA insere auditoria operacional" ON uni_ia_operational_audit;
CREATE POLICY "Servidor IA insere auditoria operacional"
ON uni_ia_operational_audit FOR INSERT
TO service_role
WITH CHECK (true);

-- ===== POLICIES: UNI IA DESK REQUESTS =====
-- Servidor IA gerencia desk requests com permissão total
DROP POLICY IF EXISTS "Servidor IA gerencia desk requests" ON uni_ia_desk_requests;
CREATE POLICY "Servidor IA gerencia desk requests"
ON uni_ia_desk_requests
FOR ALL
TO service_role
USING (true)
WITH CHECK (true);
