-- ===== RLS POLICIES: ZAIRYX IA / UNI IA =====

-- Habilitar RLS nas tabelas essenciais
ALTER TABLE zairyx_users ENABLE ROW LEVEL SECURITY;
ALTER TABLE zairyx_alerts_history ENABLE ROW LEVEL SECURITY;

-- ===== POLICIES PARA USERS =====
-- Cliente só pode ler e atualizar ser próprio perfil (via uuid)
CREATE POLICY "Usuários podem ver o próprio perfil"
ON zairyx_users FOR SELECT
USING (auth.uid() = id);

CREATE POLICY "Usuários podem atualizar o próprio perfil"
ON zairyx_users FOR UPDATE
USING (auth.uid() = id);

-- ===== POLICIES PARA HISTORY DE ALERTAS =====
-- Todos os clientes (autenticados) podem ler o histórico de alertas (Restrição FREE/PREMIUM tratada na UI)
CREATE POLICY "Clientes autenticados podem ver histórico"
ON zairyx_alerts_history FOR SELECT
TO authenticated
USING (true);

-- Apenas o Backend de IA (Servidor Python com Role Admin/Service Role) pode Inserir
CREATE POLICY "Servidor IA insere os alertas fechados"
ON zairyx_alerts_history FOR INSERT
TO service_role
WITH CHECK (true);