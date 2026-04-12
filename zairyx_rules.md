# Regras do Projeto - Uni IA (Zairyx IA)

Este projeto pertence ao grupo **Zairyx IA**. O sistema ("Uni IA" / Sentinel Markets AI) deve seguir rigorosamente os padrões de arquitetura e boas práticas estabelecidos, herdados do sucesso do Cardápio Digital.

## Padrões de Stack (Frontend / Fullstack)
Se o frontend evoluir para React/Next.js, os seguintes padrões são LEI:

### Supabase Migrations
- **Padrão**: Numerado sequencialmente (001_, 002_, ..., 027_)
- **Formato**: `NNN_nome_descritivo.sql`
- **Estilo SQL**: 
  - Comments em português com `-- =====`
  - UUID primary keys: `DEFAULT uuid_generate_v4()`
  - Timestamps: `TIMESTAMPTZ DEFAULT NOW()`
  - JSONB para dados flexíveis
- **RLS Pattern**: Arquivo separado `002_rls_policies.sql` com policies DROP/CREATE

### API Routes (Next.js)
- **Validação**: Schemas Zod com `z.object()` para actions
- **Supabase**: `createAdminClient()` para operações privilegiadas, `createClient()` para browser
- **Rate Limit**: Obrigatório com retry headers
- **Erro Handling**: Retornar `NextResponse.json({ error: 'msg' }, { status: 4xx|5xx })`

### Next.js App Router
- **'use client'**: APENAS para features interativas, hooks e state.
- **Server Components**: Padrão do projeto. Componentes server não podem receber event handlers (onSubmit/onClick). Mover para client se necessário.
- **Dynamic Routes**: Await em `params: Promise<{ slug: string }>` e `searchParams`.

### Padrões de Estado (Zustand)
- **Setup**: `create<State & Actions>()(persist(immer((set, get) => ({...}))))`

## Padrões do Backend de IA (Python)
- A integração com IA e orquestração de agentes ocorre via **Groq API**.
- Todo alerta segue o padrão estrito de schema da Zairyx IA (Score, Classificação, Explicação, Fontes).

## Módulos de Telegram (Free e Premium)
- **Robô Free**: Dita os sinais essenciais para todos os usuários cadastrados.
- **Robô Premium**: Transmite sinais **exclusivos para Dólar (USD), Euro (EUR) e Real (BRL)**.
