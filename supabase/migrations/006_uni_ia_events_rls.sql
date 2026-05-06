-- ===== RLS: UNI IA EVENTS =====
-- A tabela uni_ia_events foi criada na migration 003 sem políticas de RLS.
-- Sem esta migration, qualquer requisição anônima pode inserir eventos A/B,
-- corrompendo os dados de analytics e enviesando decisões de produto.

ALTER TABLE uni_ia_events ENABLE ROW LEVEL SECURITY;

-- Leitura: apenas o backend autenticado (service_role) pode ler eventos.
-- O frontend consome o resumo via API Route /api/events/summary (server-side),
-- nunca consultando a tabela diretamente pelo cliente.
DROP POLICY IF EXISTS "Servidor IA lê eventos uni_ia" ON uni_ia_events;
CREATE POLICY "Servidor IA lê eventos uni_ia"
ON uni_ia_events FOR SELECT
TO service_role
USING (true);

-- Inserção: apenas o backend (service_role) pode inserir eventos.
-- A API Route /api/events do Next.js usa createAdminClient() com service_role_key.
DROP POLICY IF EXISTS "Servidor IA insere eventos uni_ia" ON uni_ia_events;
CREATE POLICY "Servidor IA insere eventos uni_ia"
ON uni_ia_events FOR INSERT
TO service_role
WITH CHECK (true);
