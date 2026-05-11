🔥 Boitatá IA Investimentos
> **Gestão de Investimentos com Governança Institucional, Auditoria Completa e Identidade Brasileira**
Boitatá IA é um sistema de inteligência artificial para gestão de investimentos que toma decisões com rigor institucional, controle de risco obsessivo e transparência total — guiado por um conselho de guardiões inspirados na fauna símbolo dos estados brasileiros.
🔥 Conselho Guardião: 8+ agentes especializados, cada um nomeado com o animal símbolo do seu estado
📊 Governança Corporativa: Fluxo de aprovação, auditoria contínua, ciclos de risco
🔐 Auditoria DBA-Grade: Rastreabilidade 100% de cada decisão, transação e erro
🌿 Dízimo Amazônia: 10% do lucro líquido destinado à conservação das espécies do conselho
Princípio Fundador
✅ Caixa primeiro — operação lucrativa é obrigação, não objetivo futuro
✅ Pesquisa aplicada depois — P&D com ROI definido antes de iniciar
✅ Risco sempre controlado — nunca supera 1–3% por posição
Boitatá IA — Crescimento com Governança, não com Improviso
---
🚀 Quick Start (5 minutos)
```bash
# 1. Clone
git clone https://github.com/TiagoIA-UX/UNI-IA.git
cd UNI-IA

# 2. Configure
cp .env.example .env.local
# Preencha com suas chaves (Supabase, Groq, Telegram)

# 3. Backend
cd ai-sentinel
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
python run_local_api.py

# 4. Frontend (novo terminal)
cd zairyx-frontend
npm install
npm run dev

# 5. Acesse http://localhost:3000 ✅
```
Primeira vez? Veja o Guia Completo de Instalação.
---
📦 Releases
```bash
git tag                          # listar versões
git checkout v1.2.0              # usar versão específica
```
Cadência: Patch (bug/hotfix) · Minor (novos agentes/mercados) · Major (arquitetura/governança)
---
💡 Diferenciais
Vs. robo-traders genéricos
❌ Genéricos: "Compra quando X cruza Y" — sem contexto, sem risco
✅ Boitatá IA: Conselho de 8 guardiões analisa macro, técnico, sentimento e notícias em consenso
Vs. "black boxes" de IA
❌ Black box: "A máquina decidiu" — sem auditoria, sem responsabilidade
✅ Boitatá IA: Cada voto de cada guardião é rastreável, cada rejeição explicada
Vs. sistemas sem governança
❌ Sem governança: crescer rápido, falhar misteriosamente
✅ Boitatá IA: Gates obrigatórios, ciclos auditáveis, kill-switch automático
---
🦅 O Conselho Guardião
Cada agente carrega o espírito do animal símbolo do seu estado. Cada operação lucrativa financia a preservação dessas espécies via Dízimo Amazônia.
```
ENTRADA (Mercado Real)
    ↓
┌──────────────────────────────────────────────────────┐
│  CONSELHO GUARDIÃO (Especialistas Independentes)     │
├──────────────────────────────────────────────────────┤
│  🦅 Harpia        · DF · Contexto macroeconômico    │
│  🐆 Onça-Pintada  · MT · Análise técnica            │
│  🐬 Boto          · AM · Sentimento de mercado      │
│  🦜 Arara Azul    · MS · Notícias e eventos         │
│  🦢 Tuiuiú        · MS · Volume e fluxo             │
│  🦃 Seriema       · MG · Narrativa econômica        │
│  🐜 Tamanduá      · GO · Fundamentos do ativo       │
│  🐟 Peixe-Boi     · AM · Monitoramento de posição   │
└──────────────────────────────────────────────────────┘
    ↓ (Ponderação com pesos variáveis)
┌──────────────────────────────────────────────────────┐
│  🔥 BOITATÁ — Orquestrador Supremo · AM             │
│  → Score agregado 0–100                             │
│  → Classificação: OPORTUNIDADE / NEUTRO / RISCO     │
│  → Direção: COMPRA / VENDA / AGUARDAR               │
└──────────────────────────────────────────────────────┘
    ↓
┌──────────────────────────────────────────────────────┐
│  🐢 JABUTI — Gate de Risco · PA                     │
│  ✓ Score ≥ 75                                       │
│  ✓ Ativo em whitelist                               │
│  ✓ Drawdown dentro do limite                        │
│  ✓ Aprovação manual (quando ativado)                │
│  ✓ Auditoria em tempo real                          │
└──────────────────────────────────────────────────────┘
    ↓
┌──────────────────────────────────────────────────────┐
│  🐦 Quero-Quero — Monitoramento · RS                │
│  → Acompanha outcome real vs. esperado              │
│  → Aciona reversão e feedback para o próximo ciclo  │
└──────────────────────────────────────────────────────┘
    ↓
SAÍDA (Operação Aprovada ou Vetada)
```
Referência completa: AGENTES_GUARDIAO.md
Cada passo é auditável. Nada é silencioso.
---
🌿 Dízimo Amazônia
10% do lucro líquido operacional é destinado à conservação das espécies que compõem o conselho. O sistema rastreia e exibe esse valor em tempo real na interface da plataforma.
Espécies do conselho ameaçadas: Harpia (vulnerável) · Onça-Pintada (vulnerável) · Boto (ameaçado) · Arara Azul (vulnerável) · Jabuti (vulnerável) · Peixe-Boi (criticamente ameaçado) · Tamanduá-Bandeira (vulnerável)
---
🔄 Resiliência de LLM
Quando o provedor de LLM primário (Groq) retorna erro consecutivo, o sistema não falha silenciosamente:
Pipeline interrompe o fluxo operacional (Mandato Zero Bug)
Alerta disparado via Telegram para o canal administrativo
Estado registrado em `uni_ia_operational_audit` com `event_type = 'llm_failure'`
Operações pendentes aguardam na fila até restabelecimento
```dotenv
LLM_FALLBACK_ALERT_ENABLED=true
LLM_FALLBACK_MAX_RETRIES=3
LLM_FALLBACK_RETRY_INTERVAL_SECONDS=30
```
Integração com provedor LLM alternativo rastreada em: ForgeOps-AI
---
📊 Governança em Camadas
Capital Allocation
```
Portfolio Total: [definido pelo operador]
├─ Max por posição: 1–3% do capital total
├─ Max por dia:     Drawdown 5% → kill-switch
├─ Max por semana:  Drawdown 10% → revisão estratégica
└─ Rebalanceio:     Semanal com aprovação manual
```
Decision Gates
```
Nível 1: Score ≥ 75 → Passa | Score < 75 → Rejeitado (sem exceção)
Nível 2: Whitelist + modo + drawdown → Passa | Falha → Rejeitado
Nível 3: Aprovação manual? → Aguarda Telegram | Não → Executa com log
Nível 4: Auditoria pós-execução + reconciliação + feedback
```
---
🔐 Auditoria DBA-Grade
Tabela	O que rastreia	Retenção
`uni_ia_operational_audit`	Decisões, rejeições, execuções, falhas de LLM	Indefinida
`uni_ia_desk_requests`	Fila de aprovação com timestamps	Indefinida
`zairyx_alerts_history`	Score e classificação final	12 meses
`uni_ia_events`	A/B testing de UI/UX	12 meses
`signal_dispatch` (JSONL)	Cada sinal transmitido	6 meses
`risk_events` (JSONL)	Kill-switch, limite violado	Indefinida
`feedback_store` (JSONL)	Outcome real vs. esperado	24 meses
```sql
SELECT * FROM uni_ia_operational_audit
WHERE created_at > NOW() - INTERVAL '7 days'
AND event_type IN ('decision', 'rejection', 'approval', 'execution', 'llm_failure')
ORDER BY created_at DESC;
```
---
📖 Documentação
Recurso	Para quem	Quando ler
INSTALLATION.md	Iniciantes	Primeira instalação
AGENTES_GUARDIAO.md	Todos	Entender o conselho
README.md	Devs experientes	Arquitetura geral
schema.sql	DBAs	Customizar banco
.env.example	Todos	Configurar variáveis
---
🎓 Roadmap
Fase 1 — Fundação (Atual ✅)
✅ Conselho Guardião com 8+ agentes votando
✅ Governança em camadas com gates obrigatórios
✅ Modo paper + approval + live
✅ Auditoria rastreável 100%
✅ Alerta de falha de LLM via Telegram
✅ Identidade Boitatá IA + Dízimo Amazônia
Fase 2 — Eficiência (Q3 2026)
📅 Latência de análise: ~5s → <1s
📅 Cobertura de ativos: 3x+ pares
📅 Fine-tuning de pesos com feedback real
Fase 3 — Escala (Q4 2026+)
📅 Múltiplas estratégias (swing, scalping, mean reversion)
📅 Multi-timeframe (1h, 4h, daily)
📅 Provedor LLM alternativo automatizado
Fase 4 — Monetização Adjacente (2027)
📅 API de análise B2B
📅 Dashboard de analytics SaaS
📅 Consultoria para fundos e family offices
---
🤝 Contribuindo
```bash
# Bug
git checkout -b bugfix/descricao-breve
git push origin bugfix/descricao-breve
# Abra PR para main

# Feature: abra uma Issue primeiro, descreva o problema e o impacto de negócio
```
Padrão de commits: `feat:` · `fix:` · `docs:` · `refactor:` · `perf:` · `test:` · `chore:`
---
⚙️ Princípios Operacionais e Mandato Zero Bug
Dados reais obrigatórios — sem placeholder em execução
Gate por camadas: dados → estratégia → risco → integração → auditoria
Modo `paper` por padrão; liberação gradual para `live`
Zero comportamento silencioso — falha de LLM dispara alerta imediato
Zero fallback operacional — score só existe com payload válido
Zero execução sem validação — todos os gates precisam estar consistentes
Zero ambiguidade de estado — `paper`, `approval` e `live` têm gates explícitos
---
⚖️ Licença
Business Source License 1.1 (BUSL-1.1)
✅ Uso pessoal, estudo e desenvolvimento interno: permitido
✅ Contribuições: bem-vindas
❌ Uso comercial sem autorização escrita: não permitido
📅 Conversão para open source: 1º de janeiro de 2028
Titular: desenvolvedor do repositório `TiagoIA-UX/UNI-IA`.
Licenciamento comercial: abra uma Issue no GitHub.
---
⚠️ Aviso de Risco
Boitatá IA é um sistema de suporte à decisão de investimentos. Não é recomendação de investimento. Operações em mercados financeiros envolvem risco de perda de capital. O uso é de responsabilidade exclusiva do operador. Leia o INSTALLATION.md antes de operar com capital real. BACEN Res. 519/2025 · CVM Res. 30 · LGPD 13.709/2018.
---
Tese Institucional
Estratégia sem governança é aposta
Mercado não elimina o iniciante — elimina o indisciplinado
Diversificação sem controle de risco não é proteção
A prioridade do sistema é permanência, não euforia operacional
P&D sem caixa é hobby; P&D com governança vira ativo
Cada guardião representa uma espécie. Cada lucro financia sua sobrevivência.
---
Execução Local
```bash
# Backend
cd ai-sentinel
pip install -r requirements.txt
python run_local_api.py
# → http://127.0.0.1:8000

# Frontend (novo terminal)
cd zairyx-frontend
npm install
npm run dev
# → http://localhost:3000
```
Comandos Telegram admin: `/status` · `/pending` · `/approve <id>` · `/reject <id>` · `/cycle`
Deploy Vercel
Root Directory: `zairyx-frontend`
Erro `Build Canceled` (unverified commit): crie branch → PR → merge pelo GitHub → commit sai como `Verified`

