# 🦄 UNI IA — Release v1.0.0-alpha

**Data**: 05 de Maio de 2026
**Branch**: `main`
**Tipo**: Alpha — ambiente de desenvolvimento e testes

---

## 🎯 O que é esta release?

A **v1.0.0-alpha** é a primeira versão oficial documentada do UNI IA — sistema de inteligência artificial para análise e sinalização de mercado cripto, construído com arquitetura multi-agente, auditoria completa e governança de risco institucional.

Esta versão é indicada para **desenvolvedores e early adopters** que queiram explorar, testar e contribuir com o projeto.

> ⚠️ **Alpha significa**: funcionalidades principais implementadas, mas ainda em fase de validação. Não use com capital real sem entender os riscos.

---

## ✅ O que foi entregue nesta versão

### 🏗️ Infraestrutura & Banco de Dados
- **`schema.sql`** — Schema consolidado com todas as 5 tabelas:
  - `zairyx_users` — clientes assinantes
  - `zairyx_alerts_history` — memória institucional de alertas
  - `uni_ia_events` — eventos de A/B testing
  - `uni_ia_operational_audit` — auditoria operacional completa
  - `uni_ia_desk_requests` — fila de execução com aprovação manual
- RLS Policies configuradas em todas as tabelas sensíveis
- Triggers automáticos de `updated_at`
- Índices otimizados para queries críticas

### 🔐 Segurança & Configuração
- **`.env.example`** — Template com 80+ variáveis de ambiente documentadas em 16 seções temáticas
- Zero valores sensíveis no repositório
- Proteção via `CRON_SECRET` no endpoint de cron

### 🔄 Cron Job — Supabase Keep-Alive
- **`/api/cron/supabase-keep-alive`** — Endpoint que previne auto-pausa do Supabase free tier
- Execução automática a cada 6 dias via Vercel Cron
- Autenticação via Bearer token
- Monitoramento de latência em tempo real

### 📚 Documentação
- **`INSTALLATION.md`** — Guia completo passo a passo (professor → aluno iniciante)
  - Pré-requisitos com tabelas claras
  - Instruções para Windows, Mac e Linux
  - Como obter credenciais dos serviços externos
  - Checklist de validação
  - 10+ problemas comuns resolvidos
- **`README.md`** atualizado com:
  - Quick Start (5 minutos)
  - Estratégia PhD (arquitetura de decisão multi-agente)
  - Estratégia MBA (governança e capital allocation)
  - Estratégia DBA (trilhas de auditoria e compliance)
  - Roadmap de 4 fases
  - Guia de contribuição com Conventional Commits

### 🤖 Backend IA (ai-sentinel)
- Executor de Gap Trading com modo Hedge e trailing stop
- 8+ agentes especializados com pesos estatísticos
- Sistema de votação por consenso (auditável)
- Integração Bybit API (paper trading)
- Kill switch de segurança

---

## 📊 Estatísticas da Release

| Métrica | Valor |
|---------|-------|
| Arquivos modificados/criados | 6 |
| Linhas de documentação adicionadas | 900+ |
| Tabelas no banco de dados | 5 |
| Variáveis de ambiente documentadas | 80+ |
| Commits incluídos | 3 |

---

## 🔧 Como usar esta release

### Opção 1 — Clonar diretamente

```bash
git clone https://github.com/TiagoIA-UX/UNI-IA.git
cd UNI-IA
```

### Opção 2 — Baixar o arquivo ZIP

Na página da release no GitHub, clique em **"Source code (zip)"** para baixar.

### Opção 3 — GitHub CLI

```bash
gh repo clone TiagoIA-UX/UNI-IA
```

Depois siga o **[INSTALLATION.md](./INSTALLATION.md)** para configurar e rodar.

---

## 🗺️ Roadmap — Próximas versões

| Versão | Fase | Foco |
|--------|------|------|
| **v1.0.0-alpha** ← *você está aqui* | Fundação | Infraestrutura, documentação, segurança |
| **v1.1.0-beta** | Eficiência | CI/CD, testes automatizados, dashboard de métricas |
| **v1.2.0** | Escala | Multi-exchange, backtesting avançado, otimização de agentes |
| **v2.0.0** | Monetização | Planos premium, API pública, white-label |

---

## ⚠️ Avisos Importantes

- Este software é para fins **educacionais e de pesquisa**
- Operações com capital real envolvem **risco de perda total**
- Sempre teste em modo **paper trading** antes de qualquer operação real
- Mantenha suas chaves de API e `.env.local` **seguros e privados**

---

## 👤 Créditos

**Desenvolvedor**: Tiago Rocha
**Assistência IA**: GitHub Copilot + Claude (Anthropic)
**Stack**: Next.js 14, Python/FastAPI, Supabase, Groq, Vercel

---

*UNI IA — Inteligência Artificial com Governança Institucional* 🦄
