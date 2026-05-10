# ================================================================
#  UNI IA — CHECKLIST DE REVOGACAO DE CREDENCIAIS
#  Gerado em: 20260509_113049
#  Arquivo: E:\UNI.IA\docs\governance\environment-checklist.md
# ================================================================

## STATUS: PENDENTE — Revogue TODAS as chaves abaixo

### Credenciais a revogar e regenerar

| Servico | Onde revogar | Status |
|---|---|---|
| GROQ_API_KEY | console.groq.com → API Keys → Delete | [ ] |
| VERCEL_TOKEN | vercel.com → Settings → Tokens → Delete | [ ] |
| TELEGRAM_BOT_TOKEN | @BotFather → /revoke | [ ] |
| TELEGRAM_FREE_BOT_TOKEN | @BotFather → /revoke | [ ] |
| TELEGRAM_PREMIUM_BOT_TOKEN | @BotFather → /revoke | [ ] |
| RESEND_API_KEY | resend.com → API Keys → Delete | [ ] |
| BYBIT_API_KEY | bybit.com → API Management → Delete | [ ] |
| SUPABASE_SERVICE_ROLE_KEY | supabase.com → Settings → API → Regenerate | [ ] |
| SUPABASE_ANON_KEY | supabase.com → Settings → API → Regenerate | [ ] |
| GOOGLE_CLIENT_SECRET | console.cloud.google.com → Credentials → Regenerate | [ ] |
| CRON_SECRET | Gerar novo: node -e "console.log(require('crypto').randomBytes(32).toString('hex'))" | [ ] |
| GOOGLE_ADMIN_PASSWORD | myaccount.google.com → Seguranca → Alterar senha | [ ] |

### Apos revogar

1. Gere as novas chaves em cada servico
2. Abra E:\UNI.IA\.env.local
3. Substitua cada valor REVOGAR_E_SUBSTITUIR_* pela nova chave
4. Salve o arquivo
5. Reinicie o backend: python run_local_api.py
6. Marque cada item acima como [x]

### Observacoes de seguranca

- O .env.local NUNCA deve ser commitado no GitHub
- O .gitignore ja esta configurado para bloquear
- As chaves do MT5 foram comentadas — MT5 nao sera usado com MB ativo
- COPY_TRADE_ENABLED=false ate as chaves do MB estarem configuradas
- DESK_MODE=paper ate validacao completa em paper por 7+ dias
