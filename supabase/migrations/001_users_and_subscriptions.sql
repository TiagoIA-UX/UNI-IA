-- ===== EXTENSIONS =====
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- ===== TABLE: USERS (CLIENTES ASSINANTES) =====
CREATE TABLE zairyx_users (
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

-- Index para buscas rápidas de clientes
CREATE INDEX idx_users_email ON zairyx_users(email);
CREATE INDEX idx_users_telegram ON zairyx_users(telegram_chat_id);

-- ===== TABLE: ALERTS HISTORY (MEMÓRIA INSTITUCIONAL DO UNICÓRNIO) =====
CREATE TABLE zairyx_alerts_history (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    asset TEXT NOT NULL,
    score NUMERIC NOT NULL,
    classification TEXT NOT NULL,
    signal_agents JSONB NOT NULL DEFAULT '[]'::jsonb,
    explanation TEXT NOT NULL,
    target_channels TEXT[] DEFAULT ARRAY['FREE']::TEXT[],
    dispatched_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_alerts_asset ON zairyx_alerts_history(asset);
CREATE INDEX idx_alerts_date ON zairyx_alerts_history(dispatched_at DESC);

-- ===== TRIGGER DE UPDATED_AT =====
CREATE OR REPLACE FUNCTION set_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trg_zairyx_users_updated_at
BEFORE UPDATE ON zairyx_users
FOR EACH ROW EXECUTE FUNCTION set_updated_at();