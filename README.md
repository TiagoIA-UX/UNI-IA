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

## Variaveis obrigatorias (execucao real)
No `.env.local`:
- `TELEGRAM_BOT_TOKEN` ou `TELEGRAM_FREE_BOT_TOKEN` e `TELEGRAM_PREMIUM_BOT_TOKEN`
- `TELEGRAM_FREE_CHANNEL`
- `TELEGRAM_PREMIUM_CHANNEL`
- `BROKER_API_BASE_URL`
- `BROKER_API_KEY`
- `BROKER_ACCOUNT_ID`
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
uvicorn api.main:app --host 0.0.0.0 --port 8000 --reload
```

### Frontend (zairyx-blog)
```bash
cd zairyx-blog
npm install
npm run dev
```
