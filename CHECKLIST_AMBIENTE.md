# Checklist operacional — Boitata / UNI IA

Documento de referência na raiz do repositório: o que já está configurado em termos de **modo** e o que ainda precisa ser feito manualmente. **Não commite arquivos `.env.local` com valores reais** (já devem estar no `.gitignore`).

## 1. Após qualquer alteração em `.env.local`

1. **Salvar** o arquivo (Cursor/IDE).
2. **Reiniciar** o processo da API (`ai-sentinel`, porta usada no seu `start-local`, em geral `8010`) e, se necessário, o frontend (`3000`), para recarregar variáveis de ambiente.
3. Conferir a saúde da stack: `GET /api/health` ou `/api/readiness` na API (conforme sua instalação).

## 2. Modo live e execução automática (resumo)

A mesa usa principalmente:

| Variável | Função |
|----------|--------|
| `UNI_IA_MODE` | `paper` \| `approval` \| `live` — define se ordens reais podem ser enviadas ao broker. |
| `COPY_TRADE_ENABLED` | `true` habilita o serviço de copy trade / execução automática ligada aos sinais. |
| `UNI_IA_REQUIRE_APPROVAL` | `true` = mais sinais ficam em fila de aprovação; `false` = caminho mais automatizado em `live` (maior risco operacional). |
| `DESK_MODE` | Alias legado; mantenha **alinhado** ao `UNI_IA_MODE` para evitar confusão. |
| `DESK_ALLOWED_ASSETS` | Whitelist — símbolos devem bater com o que a UI e o broker usam (ex.: `BTCBRL` no Mercado Bitcoin). |

**Risco:** com `UNI_IA_MODE=live`, broker válido e `COPY_TRADE_ENABLED=true`, o sistema pode **enviar ordens reais**. Revise tamanho de posição, janelas (`MB_TRADE_*`), limites de risco (`COPY_TRADE_*`) e **kill switch** (`KILL_SWITCH_*`).

## 3. Mercado Bitcoin

1. Confirmar `BROKER_PROVIDER=mercadobitcoin` e URL base correta da TAPI.
2. **Credenciais** apenas em `.env.local` (ou segredo no deploy); rotacionar se houve vazamento.
3. Ajustar `DESK_ALLOWED_ASSETS` para incluir os pares **BRL** que você negocia.
4. Harmonizar scanner (se for usar) com os mesmos ativos — ver secção 6.

## 4. Telegram

1. **Dispatch (alertas para canais):** `TELEGRAM_BOT_TOKEN` (ou tokens Free/Premium), `TELEGRAM_FREE_CHANNEL`, `TELEGRAM_PREMIUM_CHANNEL` — IDs/canais válidos.
2. **Bot de controle admin:** `TELEGRAM_CONTROL_ENABLED` e preenchimento real de `TELEGRAM_ADMIN_CHAT_IDS` e/ou `TELEGRAM_ADMIN_USER_IDS` (placeholders impedem comandos `/status`, `/approve`, etc.).
3. Validar na API: `GET /api/telegram/status`.
4. Mensagens de alerta usam **HTML** com escape (menos falhas 400 do Telegram); mensagens admin seguem em texto simples.

## 5. Frontend e API

1. `NEXT_PUBLIC_AI_API_URL` e `BOITATA_AI_SENTINEL_ORIGIN` devem apontar para a **mesma origem** da API (ex.: `http://127.0.0.1:8010` em local).
2. Pode existir `zairyx-frontend/.env.local` — ele **sobrescreve** defaults; alinhar portas com a API.

## 6. Signal scanner (sinais em background)

1. `SIGNAL_SCANNER_ENABLED` — ligue só quando quiser o loop automático de varredura.
2. `SIGNAL_SCAN_ASSETS` — idealmente alinhado aos ativos BRL/USDT que você monitora.
3. Timeframes e deduplicação: ver `SIGNAL_SCAN_TIMEFRAMES` e variáveis `SIGNAL_*` no `.env`/documentação interna.
4. Logs opcionais: `SIGNAL_DISPATCH_LOG_PATH`.

## 7. Segurança e governança

1. Lista formal: `docs/governance/environment-checklist.md` (se existir no repositório).
2. Rotacione qualquer chave que tenha ido para chat, print ou commit acidental.
3. Git pode exibir `Permission denied` em pastas locais (ex.: export de backtest); corrija permissões ou remova/ignore a pasta — não bloqueia o commit se os arquivos do projeto não dependem dela.

## 8. Testes rápidos (desenvolvimento)

Na pasta `ai-sentinel`, com o venv ativo:

```bash
python -m unittest discover -s tests -p "test_*.py"
```

## 9. Voltar para simulação (paper)

- `UNI_IA_MODE=paper`
- `COPY_TRADE_ENABLED=false` (se não quiser risco de integração automática)
- Reiniciar a API.

---

**Última orientação:** este `.md` descreve **processos**; valores secretos ficam **apenas** em `.env.local` ou no provedor de deploy, nunca neste arquivo.
