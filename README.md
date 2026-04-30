# UNI IA

Plataforma de analise e execucao para ativos com governanca de mesa privada.

## Principios operacionais
- Dados reais obrigatorios.
- Sem placeholder e sem fallback operacional em execucao.
- Gate por camadas: dados, estrategia, risco, integracao e auditoria.
- Modo `paper` por padrao e liberacao gradual para `live`.

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
