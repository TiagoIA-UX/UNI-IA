# ═══════════════════════════════════════════════════════════════════
# APLICAR_LEGAL_E_DEPLOY.ps1 — UNI IA
# Boas práticas legais no GitHub + preparação de deploy
# Execute: cd E:\UNI.IA && .\APLICAR_LEGAL_E_DEPLOY.ps1
# ═══════════════════════════════════════════════════════════════════

Set-Location "E:\UNI.IA"
Write-Host "`n🦄 Iniciando boas práticas legais e deploy UNI IA...`n" -ForegroundColor Cyan

# ═══════════════════════════════════════════════════════════════════
# ARQUIVO 1 — LICENSE (Proprietário — sem open source)
# Motivo: UNI IA é produto comercial, não open source.
# Sem licença = qualquer um pode copiar legalmente.
# Com licença proprietária = uso restrito ao autor.
# ═══════════════════════════════════════════════════════════════════
Write-Host "📌 [1/7] Criando LICENSE..." -ForegroundColor White

@'
Copyright (c) 2024-2026 Tiago Rocha — UNI IA / Zairyx IA

All rights reserved.

This software and its source code are proprietary and confidential.
Unauthorized copying, distribution, modification, public display,
or use of this software, in whole or in part, is strictly prohibited
without the prior written permission of the copyright holder.

This software is provided for internal development and evaluation
purposes only. It is NOT open source and may NOT be used, copied,
modified, merged, published, distributed, sublicensed, or sold
without explicit written authorization from the author.

For licensing inquiries, contact: oficialuni.iabrasil@gmail.com

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND.
IN NO EVENT SHALL THE AUTHORS BE LIABLE FOR ANY CLAIM, DAMAGES
OR OTHER LIABILITY ARISING FROM THE USE OF THIS SOFTWARE.
'@ | Set-Content "LICENSE" -Encoding UTF8
Write-Host "  ✅ LICENSE criado" -ForegroundColor Green

# ═══════════════════════════════════════════════════════════════════
# ARQUIVO 2 — SECURITY.md
# Motivo: GitHub recomenda para qualquer repositório público.
# Informa como reportar vulnerabilidades sem expô-las publicamente.
# ═══════════════════════════════════════════════════════════════════
Write-Host "📌 [2/7] Criando SECURITY.md..." -ForegroundColor White

@'
# 🔐 Política de Segurança — UNI IA

## Versões suportadas

| Versão | Suporte de segurança |
|--------|----------------------|
| v1.1.x | ✅ Suportada         |
| v1.0.x | ⚠️ Somente críticos  |
| < v1.0 | ❌ Sem suporte        |

## Reportando uma vulnerabilidade

**NÃO abra uma Issue pública para reportar vulnerabilidades de segurança.**

Se você descobriu uma vulnerabilidade de segurança no UNI IA, reporte
de forma responsável pelo canal privado abaixo:

📧 **E-mail**: oficialuni.iabrasil@gmail.com  
📱 **WhatsApp**: +55 (19) 99688-7993

### O que incluir no reporte

- Descrição clara da vulnerabilidade
- Passos para reproduzir o problema
- Impacto potencial estimado
- Versão afetada
- Sugestão de correção (se houver)

### O que esperar

- **Confirmação de recebimento**: até 48 horas
- **Avaliação inicial**: até 7 dias úteis
- **Correção e divulgação**: conforme criticidade

## Escopo

Este repositório cobre:
- Backend FastAPI (`ai-sentinel/`)
- Frontend Next.js (`zairyx-blog/`)
- Integração Bybit API
- Integração Telegram Bot
- Fluxo de governança e auditoria

## Reconhecimentos

Agradecemos a todos que reportam vulnerabilidades de forma responsável.
'@ | Set-Content "SECURITY.md" -Encoding UTF8
Write-Host "  ✅ SECURITY.md criado" -ForegroundColor Green

# ═══════════════════════════════════════════════════════════════════
# ARQUIVO 3 — CONTRIBUTING.md
# Motivo: Define regras claras de contribuição.
# Protege o projeto de PRs indesejados ou problemáticos.
# ═══════════════════════════════════════════════════════════════════
Write-Host "📌 [3/7] Criando CONTRIBUTING.md..." -ForegroundColor White

@'
# 🤝 Contribuindo com o UNI IA

Obrigado pelo interesse em contribuir! Antes de abrir uma Issue ou PR,
leia estas diretrizes com atenção.

## ⚠️ Projeto proprietário em fase de desenvolvimento

O UNI IA é um software proprietário. Contribuições externas são
bem-vindas, mas sujeitas à aprovação explícita do mantenedor.
Ao contribuir, você concorda que seus aportes passam a ser propriedade
intelectual do projeto, conforme os termos do arquivo LICENSE.

## Como reportar bugs

1. Verifique se o bug já foi reportado nas [Issues](../../issues)
2. Abra uma nova Issue com o template de bug
3. Inclua: sistema operacional, versões, logs completos e passos para reproduzir

## Como sugerir features

1. Abra uma Issue descrevendo **o problema que a feature resolve**
2. Descreva o **impacto de negócio** (por que é importante agora)
3. Aguarde aprovação antes de iniciar qualquer desenvolvimento

## Fluxo de desenvolvimento

```bash
# 1. Crie uma branch descritiva
git checkout -b feat/nome-da-feature
# ou
git checkout -b fix/descricao-do-bug

# 2. Faça commits pequenos e descritivos
git commit -m "feat: descrição breve da mudança"

# 3. Abra um Pull Request para a branch main
# Descreva claramente o que foi feito e por quê
```

## Padrão de commits (Conventional Commits)

| Tipo | Uso |
|------|-----|
| `feat:` | Nova funcionalidade |
| `fix:` | Correção de bug |
| `docs:` | Documentação |
| `refactor:` | Reestruturação sem mudança de comportamento |
| `perf:` | Melhoria de performance |
| `test:` | Testes |
| `chore:` | Tarefas de manutenção |

## O que NÃO fazer

- ❌ Não commite `.env.local` ou qualquer arquivo com chaves reais
- ❌ Não altere arquivos de governança (`SENTINEL`, `AEGIS`, `desk.py`) sem aprovação
- ❌ Não altere o modo `live` ou configurações de broker sem autorização
- ❌ Não adicione dependências sem justificativa de negócio documentada

## Contato

📧 oficialuni.iabrasil@gmail.com  
💬 WhatsApp: +55 (19) 99688-7993
'@ | Set-Content "CONTRIBUTING.md" -Encoding UTF8
Write-Host "  ✅ CONTRIBUTING.md criado" -ForegroundColor Green

# ═══════════════════════════════════════════════════════════════════
# ARQUIVO 4 — CODE_OF_CONDUCT.md
# Motivo: Exigido pelo GitHub para repositórios saudáveis.
# Protege o mantenedor de interações abusivas.
# ═══════════════════════════════════════════════════════════════════
Write-Host "📌 [4/7] Criando CODE_OF_CONDUCT.md..." -ForegroundColor White

@'
# 📋 Código de Conduta — UNI IA

## Nosso compromisso

Nos comprometemos a manter um ambiente respeitoso, profissional
e livre de assédio para todos os participantes deste projeto.

## Comportamentos esperados

- Comunicação respeitosa e construtiva
- Foco técnico e de negócio nas discussões
- Aceitação de feedback com profissionalismo
- Respeito à propriedade intelectual do projeto

## Comportamentos inaceitáveis

- Assédio, insultos ou ataques pessoais
- Divulgação não autorizada de informações confidenciais
- Uso indevido de acesso ao repositório
- Tentativas de contornar gates de segurança ou governança

## Aplicação

Violações devem ser reportadas para:  
📧 oficialuni.iabrasil@gmail.com

O mantenedor reserva o direito de remover comentários, fechar Issues
e bloquear usuários que violem este código, sem aviso prévio.

## Referência

Baseado no [Contributor Covenant](https://www.contributor-covenant.org/), versão 2.1.
'@ | Set-Content "CODE_OF_CONDUCT.md" -Encoding UTF8
Write-Host "  ✅ CODE_OF_CONDUCT.md criado" -ForegroundColor Green

# ═══════════════════════════════════════════════════════════════════
# ARQUIVO 5 — .github/ISSUE_TEMPLATE/bug_report.md
# Motivo: Padroniza reports de bug com informações mínimas úteis.
# ═══════════════════════════════════════════════════════════════════
Write-Host "📌 [5/7] Criando templates de Issue..." -ForegroundColor White

New-Item -ItemType Directory -Force -Path ".github\ISSUE_TEMPLATE" | Out-Null

@'
---
name: 🐛 Bug Report
about: Reporte um comportamento inesperado no UNI IA
title: "[BUG] "
labels: bug
assignees: TiagoIA-UX
---

## Descrição do bug
Descreva claramente o que aconteceu.

## Passos para reproduzir
1. Vá para '...'
2. Execute '...'
3. Veja o erro

## Comportamento esperado
O que deveria ter acontecido?

## Logs e screenshots
Cole aqui os logs relevantes (sem dados sensíveis ou chaves de API).

## Ambiente
- OS: [ex: Windows 11]
- Node.js: [ex: 18.x]
- Python: [ex: 3.11]
- Branch/Versão: [ex: main / v1.1.0]

## Contexto adicional
Qualquer informação extra que possa ajudar.
'@ | Set-Content ".github\ISSUE_TEMPLATE\bug_report.md" -Encoding UTF8

@'
---
name: 💡 Feature Request
about: Sugira uma nova funcionalidade para o UNI IA
title: "[FEAT] "
labels: enhancement
assignees: TiagoIA-UX
---

## Problema que esta feature resolve
Descreva claramente qual problema ou limitação você identificou.

## Solução proposta
Como você imagina que essa feature funcionaria?

## Impacto de negócio
Por que essa feature é importante para o projeto agora?

## Alternativas consideradas
Você considerou outras abordagens? Por que esta é a melhor?

## Contexto adicional
Qualquer referência, mockup ou exemplo que ajude a entender.
'@ | Set-Content ".github\ISSUE_TEMPLATE\feature_request.md" -Encoding UTF8
Write-Host "  ✅ Templates de Issue criados" -ForegroundColor Green

# ═══════════════════════════════════════════════════════════════════
# ARQUIVO 6 — .github/PULL_REQUEST_TEMPLATE.md
# Motivo: Garante que todo PR tenha contexto mínimo antes de revisão.
# ═══════════════════════════════════════════════════════════════════
Write-Host "📌 [6/7] Criando template de Pull Request..." -ForegroundColor White

@'
## 📋 Descrição

O que foi feito e por quê?

## 🔗 Issue relacionada

Closes #(número da issue)

## ✅ Checklist

- [ ] Testei localmente em modo `paper`
- [ ] Não há chaves de API ou dados sensíveis no código
- [ ] Commits seguem o padrão Conventional Commits
- [ ] Documentação atualizada (se necessário)
- [ ] Sem alterações em arquivos de governança sem aprovação prévia

## 🧪 Como testar

Passos para validar as mudanças:

1. ...
2. ...

## 📸 Screenshots (se aplicável)
'@ | Set-Content ".github\PULL_REQUEST_TEMPLATE.md" -Encoding UTF8
Write-Host "  ✅ Template de PR criado" -ForegroundColor Green

# ═══════════════════════════════════════════════════════════════════
# ARQUIVO 7 — vercel.json (configuração de deploy)
# Motivo: Garante que o Vercel aponte para a pasta correta
# e aplica headers de segurança HTTP obrigatórios.
# ═══════════════════════════════════════════════════════════════════
Write-Host "📌 [7/7] Criando vercel.json com headers de segurança..." -ForegroundColor White

@'
{
  "version": 2,
  "buildCommand": "npm run build",
  "outputDirectory": ".next",
  "installCommand": "npm install",
  "framework": "nextjs",
  "headers": [
    {
      "source": "/(.*)",
      "headers": [
        {
          "key": "X-Content-Type-Options",
          "value": "nosniff"
        },
        {
          "key": "X-Frame-Options",
          "value": "DENY"
        },
        {
          "key": "X-XSS-Protection",
          "value": "1; mode=block"
        },
        {
          "key": "Referrer-Policy",
          "value": "strict-origin-when-cross-origin"
        },
        {
          "key": "Permissions-Policy",
          "value": "camera=(), microphone=(), geolocation=()"
        },
        {
          "key": "Strict-Transport-Security",
          "value": "max-age=63072000; includeSubDomains; preload"
        }
      ]
    }
  ]
}
'@ | Set-Content "zairyx-blog\vercel.json" -Encoding UTF8
Write-Host "  ✅ vercel.json criado com headers de segurança HTTP" -ForegroundColor Green

# ═══════════════════════════════════════════════════════════════════
# COMMIT E PUSH
# ═══════════════════════════════════════════════════════════════════
Write-Host "`n🚀 Commitando e enviando ao GitHub..." -ForegroundColor Cyan

git add LICENSE
git add SECURITY.md
git add CONTRIBUTING.md
git add CODE_OF_CONDUCT.md
git add .github/
git add zairyx-blog/vercel.json

git commit -m "chore: boas práticas legais GitHub e configuração de deploy

- LICENSE: licença proprietária — uso restrito ao autor
- SECURITY.md: política de divulgação responsável de vulnerabilidades
- CONTRIBUTING.md: regras de contribuição com proteção IP
- CODE_OF_CONDUCT.md: código de conduta baseado em Contributor Covenant
- .github/ISSUE_TEMPLATE: templates de bug report e feature request
- .github/PULL_REQUEST_TEMPLATE: checklist de PR com gate de segurança
- vercel.json: headers HTTP de segurança (HSTS, XSS, CSP, Referrer)"

git push origin main

Write-Host "`n✅ Boas práticas legais aplicadas e enviadas ao GitHub!" -ForegroundColor Green
Write-Host "`n📋 PRÓXIMO PASSO — Deploy no Vercel:" -ForegroundColor Yellow
Write-Host "   1. Acesse: https://vercel.com/tiagoiaux/uni-ia" -ForegroundColor White
Write-Host "   2. Confirme que Root Directory = 'zairyx-blog'" -ForegroundColor White
Write-Host "   3. Em Settings > General > desative 'Require Verified Commits' se necessário" -ForegroundColor White
Write-Host "   4. Clique em 'Redeploy' no último deployment" -ForegroundColor White
Write-Host "`n🦄 UNI IA com governança legal completa no GitHub!`n" -ForegroundColor Cyan
