# 🦄 UNI IA

> **Inteligência Operacional com Governança em Nível PhD, Estratégia em MBA e Auditoria em DBA**

UNI IA é o laboratorio de inteligência artificial financeira que automatiza análise de mercados com **rigor institucional**, **controle de risco obsessivo** e **transparência completa**.

- 🧠 **Motor de Decisão Cognitivo** (PhD-grade): 8+ agentes especializados que votam e chegam a consenso
- 📊 **Governança Corporativa** (MBA-grade): Fluxo de aprovação, auditoria contínua, ciclos de risco
- 🔐 **Auditoria de Dados** (DBA-grade): Rastreabilidade 100% de cada decisão, cada transação, cada erro
- 📈 **Escalabilidade Lucrativa**: Financiado pelo produto principal (Cardapio-Digital), reinvestimento estratégico em P&D

**Produto que paga a conta**: `Cardapio-Digital`  
**Laboratório que acelera vantagem tecnológica**: `UNI IA`

### Princípio Fundador
- ✅ **Caixa primeiro** (operação lucrativa é obrigação)
- ✅ **Pesquisa aplicada depois** (P&D com ROI definido)
- ✅ **Risco sempre controlado** (nunca supera 1-3% por posição)

**UNI IA - Crescimento com Governança, não com Improviso**

---

## 🚀 Quick Start (5 minutos para iniciantes)

Nunca usou UNI IA? Comece aqui:

```bash
# 1. Clone
git clone https://github.com/TiagoIA-UX/UNI-IA.git
cd UNI-IA

# 2. Configure
cp .env.example .env.local
# Abra .env.local e preencha com suas chaves (Supabase, Groq, Telegram)

# 3. Backend (IA)
cd ai-sentinel
python -m venv venv
source venv/bin/activate  # ou venv\Scripts\activate no Windows
pip install -r requirements.txt
python run_local_api.py   # Deixe rodando

# 4. Frontend (novo terminal)
cd zairyx-blog
npm install
npm run dev

# 5. Abra http://localhost:3000 no navegador ✅
```

**Novo em programação?** Veja o [Guia Completo de Instalação](./INSTALLATION.md) - escrito para iniciantes.

---

## 📦 Releases Oficiais

Use **releases estáveis** para ambiente de produção:

```bash
# Listar versões disponíveis
git tag

# Clonar versão específica (ex: v1.0.0)
git clone --branch v1.0.0 https://github.com/TiagoIA-UX/UNI-IA.git

# Ou mudar para release no repositório existente
git checkout v1.0.0
```

**Cadência de releases**:
- **Patch** (v1.0.x): Correções de bug, hotfix de risco
- **Minor** (v1.x.0): Novos agentes, novos mercados, nova UI
- **Major** (vX.0.0): Mudança de arquitetura, gates de governança revistos

Veja todas as [releases aqui](https://github.com/TiagoIA-UX/UNI-IA/releases).

---

---

## 💡 Por que UNI IA? (Estratégia Diferenciada)

### Vs. Robo-traders genéricos
- ❌ Genéricos: "Compra quando X cruza Y" → Sem contexto, sem risco
- ✅ **UNI IA**: Analisa macroeconômico, notícias, sentimento + técnico → Score robusto

### Vs. "Black boxes" de IA
- ❌ Black box: "A máquina decidiu" → Sem auditoria, sem responsabilidade legal
- ✅ **UNI IA**: Cada decisão é **rastreável**, cada voto de agente documentado, cada rejeição explicada

### Vs. Startups de trading sem governance
- ❌ Sem governança: Crescer rápido, falhar misteriosamente
- ✅ **UNI IA**: Gates obrigatórios de risco, ciclos auditáveis, controle de capital por posição

---

## 🏗️ Arquitetura: PhD-Level Decision Making

```
ENTRADA (Mercado Real)
    ↓
┌─────────────────────────────────────────────┐
│  AGENTS LAYER (Especialistas Independentes) │
├─────────────────────────────────────────────┤
│  MacroAgent    → Regime market (risk-on?)   │
│  ATLAS         → Estrutura técnica          │
│  ORION         → Narrativa econômica        │
│  NewsAgent     → Eventos recentes           │
│  SentimentAgent→ Emoção de mercado          │
│  TrendsAgent   → Anomalias de volume        │
│  Fundamentalist→ Fundamentos firmes         │
│  ARGUS         → Monitoramento de posição  │
└─────────────────────────────────────────────┘
    ↓ (Ponderação com pesos variáveis)
┌─────────────────────────────────────────────┐
│  DECISION FUSION (AEGIS)                    │
│  → Score agregado com peso estatístico      │
│  → Classificação: BUY / HOLD / SELL         │
│  → Confiança: 0-100%                        │
└─────────────────────────────────────────────┘
    ↓
┌─────────────────────────────────────────────┐
│  GOVERNANCE LAYER (SENTINEL Risk Gate)      │
│  ✓ Validação de score                       │
│  ✓ Limite de risco por posição              │
│  ✓ Aprovação manual (quando ativado)        │
│  ✓ Auditoria em tempo real                  │
└─────────────────────────────────────────────┘
    ↓
SAÍDA (Operação Aprovada ou Rejeitada)
```

**Cada passo é auditável. Nada é silencioso.**

---

## 📊 Governança em Camadas (MBA Strategic Framework)

### Capital Allocation (Gestão de Risco - MBA)
```
Portfolio Total: R$ 100.000
├─ Max por posição: R$ 1.000-3.000 (1-3%)
├─ Max por dia: Drawdown 5% antes de kill-switch
├─ Max por semana: 10% drawdown antes de revisão estratégica
└─ Rebalanceio: Semanal com aprovação manual
```

### Decision Gates (Governança)
```
Nível 1: Score ≥ 75 → Passa para Nível 2
         Score < 75 → Rejeitado automaticamente (sem exceção)

Nível 2: ✓ Ativo está em whitelist?
         ✓ Modo não é "paper"?
         ✓ Drawdown semanal < limite?
         
         Se SIM → Nível 3
         Se NÃO → Rejeitado

Nível 3: ✓ Aprovação manual requerida?
         
         Se SIM → Aguarda humano (Telegram)
         Se NÃO → Executado (com log de auditoria)

Nível 4: ✓ Auditoria pós-execução
         ✓ Reconciliação com broker
         ✓ Outcome rastreado para feedback
```

---

## 🔐 Auditoria em DBA-Grade

Toda **transação, decisão e erro** é registrado em tabelas independentes:

| Tabela | O que rastreia | Retenção |
|--------|---------------|----------|
| `uni_ia_events` | A/B testing de UI/UX | 12 meses |
| `uni_ia_operational_audit` | Decisões, rejeições, execuções | Indefinida (compliance) |
| `uni_ia_desk_requests` | Fila de aprovação com timestamps | Indefinida |
| `zairyx_alerts_history` | Score e classificação final | 12 meses |
| `signal_dispatch` (log JSONL) | Cada sinal transmitido ao Telegram | 6 meses |
| `risk_events` (log JSONL) | Kill-switch, limite violado | Indefinida |
| `feedback_store` (log JSONL) | Outcome real vs. esperado | 24 meses (ML training) |

**Consulta auditoria**:
```sql
SELECT * FROM uni_ia_operational_audit
WHERE created_at > NOW() - INTERVAL '7 days'
AND event_type IN ('decision', 'rejection', 'approval', 'execution')
ORDER BY created_at DESC;
```

---

## 📖 Documentação Completa

| Recurso | Público-alvo | Leia quando |
|---------|-------------|-----------|
| [INSTALLATION.md](./INSTALLATION.md) | **Iniciantes, devs novos** | Primeira vez instalando |
| [README.md](./README.md) | **Devs experientes** | Entender arquitetura |
| [schema.sql](./schema.sql) | **DBAs, devs backend** | Customizar banco de dados |
| [.env.example](./.env.example) | **Todos** | Configurar variáveis |
| [Releases](https://github.com/TiagoIA-UX/UNI-IA/releases) | **Ops, produção** | Deploy em staging/prod |

---

## 🎓 Roadmap: Evolução Estratégica

### Fase 1 - Fundação (Agora ✅)
- ✅ Robusto de dados, risco e auditoria
- ✅ 8+ agentes especializados votando
- ✅ Modo paper + approval + live
- ✅ Rastreabilidade completa
- **Objetivo**: Permanecer (não virar mais uma startup falida)

### Fase 2 - Eficiência (Q3 2026)
- 📅 Reduzir latência de análise (atual: ~5s → target: <1s)
- 📅 Aumentar cobertura de ativos (3x+ pares)
- 📅 Fine-tuning de pesos dos agentes com feedback real
- **Objetivo**: Lucro por transação mais previsível

### Fase 3 - Escala (Q4 2026+)
- 📅 Múltiplas estratégias (swing, scalping, mean reversion)
- 📅 Multi-timeframe (1h, 4h, daily)
- 📅 Liquidez automática com proteção de drawdown
- **Objetivo**: AUM crescente com controle de risco

### Fase 4 - Monetização Adjacente (2027)
- 📅 API pública de sinais (B2B)
- 📅 Dashboard de analytics (SaaS)
- 📅 Consultoria de operação para fundos
- **Objetivo**: Receita recorrente sem aumentar risco

---

## 🤝 Contribuindo

### Para reportar bugs
```bash
git checkout -b bugfix/descricao-breve
# Faça as correções
git push origin bugfix/descricao-breve
# Abra PR para main
```

### Para sugerir features
1. Abra uma **Issue** descrevendo a feature
2. Descreva o **problema que resolve**
3. Descreva o **impacto de negócio** (por que é importante)
4. Aguarde aprovação antes de começar a codar

### Padrão de commits
```bash
git commit -m "type: descrição breve

Descrição detalhada se necessário.
Referencia: #123 (número da issue)
"

# Types válidos:
# feat:   nova feature
# fix:    correção de bug
# docs:   atualização de documentação
# refactor: reestruturação de código
# perf:   melhoria de performance
# test:   testes unitários
# chore:  tarefas de manutenção
```

---

1. O Cardapio-Digital gera caixa.
2. Uma parcela fixa do lucro liquido mensal e reservada para P&D.
3. Essa reserva financia apenas entregas da UNI IA com KPI claro.
4. Cada ciclo fecha com auditoria de resultado (tecnico + financeiro).

Politica sugerida de alocacao (ajustavel):
- 70% do lucro liquido: operacao, aquisicao e resiliencia do Cardapio;
- 20% do lucro liquido: investimento incremental na UNI IA;
- 10% do lucro liquido: reserva estrategica de seguranca.

Gates obrigatorios para liberar investimento no ciclo seguinte:
- disponibilidade operacional estavel;
- custos sob controle;
- backlog priorizado por impacto;
- entrega mensuravel no ciclo anterior.

## Mapa de maturidade

Fase 1 - Fundacao (atual):
- robustez de dados, risco, auditoria e execucao controlada.

Fase 2 - Eficiencia:
- reduzir custo por analise e aumentar confiabilidade do pipeline.

Fase 3 - Escala:
- ampliar cobertura de ativos e automacoes com controles mais fortes.

Fase 4 - Monetizacao adjacente:
- empacotar capacidades maduras como novos produtos/servicos.

## Principios operacionais
- Dados reais obrigatorios.
- Sem placeholder e sem fallback operacional em execucao.
- Gate por camadas: dados, estrategia, risco, integracao e auditoria.
- Modo `paper` por padrao e liberacao gradual para `live`.
- Toda evolucao de feature deve ter impacto de negocio definido antes da implementacao.

## Mandato Zero Bug
- Zero comportamento silencioso: falha de LLM, auditoria ou notificacao obrigatoria deve interromper o fluxo operacional.
- Zero fallback operacional: score, classificacao e direcao so existem com payload valido e verificavel.
- Zero placeholder em producao: o pipeline usa dados reais de mercado, noticias e volume; resposta sintetica de erro nao pode virar sinal.
- Zero execucao sem validacao: contexto, score, classificacao, governanca, auditoria e aprovacao manual precisam estar consistentes antes de qualquer ordem real.
- Zero ambiguidade de estado: `paper`, `approval` e `live` possuem gates explicitos de prontidao e bloqueio.

## Arquitetura de decisao em camadas
- MacroAgent: regime risk-on, risk-off ou neutro do ambiente amplo.
- ATLAS: estrutura tecnica, volatilidade, volume, momentum e niveis.
- ORION: narrativa e contexto de noticias com sintese cognitiva.
- NewsAgent: leitura objetiva das manchetes recentes e impacto direto.
- SentimentAgent: tom emocional das manchetes, medo, euforia ou incerteza.
- TrendsAgent: anomalia de volume e tracao de atencao do mercado.
- FundamentalistAgent: protecao de capital via fundamentos quando aplicavel.
- AEGIS: fusao ponderada das especialidades em score, classificacao e direcao.
- SENTINEL: gate de risco e governanca antes de dispatch ou execucao.
- ARGUS: monitoramento de posicao, reversao e outcome real.

## Modulos principais
- `ai-sentinel/`: backend FastAPI de orquestracao, Telegram e mesa privada.
- `zairyx-blog/`: frontend comercial e paginas institucionais da plataforma.
- `app.js`, `data.js`, `ai.js`: cockpit analitico com gate de execucao.

## Mesa privada (backend)
Endpoints em `ai-sentinel/api/main.py`:
- `POST /api/analyze/{asset}`: analisa e passa pelo gate da mesa.
- `GET /api/desk/status`: status de modo, copy trade e pendencias.
- `GET /api/desk/pending`: fila de aprovacao manual.
- `POST /api/desk/approve/{request_id}`: aprova e executa em live.
- `POST /api/desk/reject/{request_id}`: rejeita request pendente.
- `GET /api/signals/status`: status do scanner continuo de sinais.
- `POST /api/signals/start`: inicia o scanner continuo.
- `POST /api/signals/stop`: interrompe o scanner continuo.
- `POST /api/signals/run-cycle`: executa uma rodada imediata de varredura.
- `GET /api/telegram/status`: status do polling administrativo do Telegram.

## Auditoria operacional
- Migration dedicada em `supabase/migrations/004_uni_ia_operational_audit.sql`.
- Eventos persistidos: geracao de sinal, paper log, pendencia, execucao aprovada, execucao automatica e rejeicao.
- Persistencia feita pelo backend Python via REST Admin do Supabase usando `SUPABASE_SERVICE_ROLE_KEY`.

## Variaveis obrigatorias (execucao real)
No `.env.local`:
- `TELEGRAM_BOT_TOKEN` ou `TELEGRAM_FREE_BOT_TOKEN` e `TELEGRAM_PREMIUM_BOT_TOKEN`
- `TELEGRAM_FREE_CHANNEL`
- `TELEGRAM_PREMIUM_CHANNEL`
- `TELEGRAM_CONTROL_ENABLED=true` para ativar comandos administrativos por polling
- `TELEGRAM_ADMIN_CHAT_IDS=123456789`
- `TELEGRAM_ADMIN_USER_IDS=123456789`
- `SIGNAL_SCANNER_ENABLED=true` para varredura automatica
- `SIGNAL_SCAN_ASSETS=BTCUSDT,ETHUSDT,SOLUSDT`
- `SIGNAL_SCAN_INTERVAL_SECONDS=60`
- `SIGNAL_SCAN_STAGGER_SECONDS=2`
- `SIGNAL_MIN_SCORE=75`
- `SIGNAL_ALLOWED_CLASSIFICATIONS=OPORTUNIDADE`
- `SIGNAL_DEDUPE_TTL_SECONDS=300`
- `STRATEGY_DEFAULT_MODE=swing`
- `BROKER_API_BASE_URL`
- `BROKER_API_KEY`
- `BROKER_API_SECRET` (Bybit)
- `BROKER_ACCOUNT_ID` (apenas para adapter HTTP generico, nao para Bybit)
- `COPY_TRADE_ENABLED=true` (somente apos homologacao)
- `DESK_MODE=live`
- `DESK_REQUIRE_MANUAL_APPROVAL=true`

## Fluxo recomendado de entrada em producao
1. Homologar em `paper` com dados reais e logs auditaveis.
2. Ativar `live` com aprovacao manual e whitelist de ativos.
3. Validar latencia, rejeicoes e reconciliacao por 24h.
4. Escalar gradualmente risco e universo de ativos.

## Tese institucional

- Estrategia sem governanca e aposta.
- Mercado nao elimina o iniciante. Elimina o indisciplinado.
- Diversificacao sem controle de risco nao e protecao.
- A prioridade do sistema e permanencia, nao euforia operacional.
- P&D sem caixa e hobby; P&D com governanca vira ativo.

## Execucao local
### Backend (ai-sentinel)
```bash
cd ai-sentinel
pip install -r requirements.txt
python run_local_api.py
```

Observacao:
- O launcher `run_local_api.py` usa `h11` e desabilita WebSocket para evitar dependencias quebradas do ambiente local do Windows.
- Em `live`, a mesa continua exigindo aprovacao manual quando `DESK_REQUIRE_MANUAL_APPROVAL=true`.
- Para automacao continua, habilite `SIGNAL_SCANNER_ENABLED=true` e defina a lista de ativos em `SIGNAL_SCAN_ASSETS`.
- Comandos suportados no Telegram administrativo: `/status`, `/pending`, `/approve <request_id>`, `/reject <request_id> [motivo]`, `/cycle`.
- Para descobrir `TELEGRAM_ADMIN_CHAT_IDS` ou `TELEGRAM_ADMIN_USER_IDS`, envie uma mensagem para o bot `@uni_ia_bot` e depois consulte `/api/telegram/status` para ler `last_seen_chat_id` e `last_seen_user_id`.

### Frontend (zairyx-blog)
```bash
cd zairyx-blog
npm install
npm run dev
```

## Deploy Vercel (anti-incidentes)

### Root Directory correto
- Projeto no Vercel deve apontar para `zairyx-blog`.
- Se ficar em `./`, o build nao encontra o app Next.js.

### Causa do erro mais comum
- Erro: `Build Canceled` com mensagem `created with an unverified commit`.
- Isso ocorre quando `Require Verified Commits` esta ativo no Vercel e o commit no `main` nao esta verificado.

### Prevencao
1. Manter `Require Verified Commits` desativado, ou
2. Garantir que os commits no `main` sejam `Verified`.

### Recuperacao rapida (quando bloquear)
1. Criar branch de trigger e push:
```bash
git checkout -b deploy/verified-trigger
git commit --allow-empty -m "chore: trigger deploy via github verified merge"
git push -u origin deploy/verified-trigger
```
2. Abrir PR para `main` e fazer merge pelo GitHub (squash/merge).
3. O commit gerado pelo GitHub tende a sair como `Verified`.
4. O Vercel volta a aceitar o deploy automaticamente.

### Validacao
- Commit: verificar no GitHub se aparece `Verified`.
- Vercel: status do contexto `Vercel` deve sair de `pending` para `success`.
