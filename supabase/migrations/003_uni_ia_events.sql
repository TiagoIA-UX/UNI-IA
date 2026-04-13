-- ===== TABLE: UNI IA EVENTS (A/B TRACKING) =====
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

CREATE INDEX IF NOT EXISTS idx_uni_ia_events_page_date ON uni_ia_events(page, created_at DESC);
CREATE INDEX IF NOT EXISTS idx_uni_ia_events_variant ON uni_ia_events(variant);
CREATE INDEX IF NOT EXISTS idx_uni_ia_events_event ON uni_ia_events(event);
