# Regras do Projeto - UNI IA

Este projeto pertence ao grupo **UNI IA**. O sistema ("UNI IA" / Sentinel Markets AI) deve seguir rigorosamente os padrões de arquitetura e boas práticas estabelecidos, herdados do sucesso do Cardápio Digital.

## Regra Mestra de Execucao (Obrigatoria)
- **Compliance legal total e inegociavel**: toda implementacao e toda execucao devem obedecer a legislacao aplicavel, termos de provedores, regras de mercado e politicas de plataforma.
- **Proibido operar no limite da legalidade**: qualquer comportamento de risco juridico, bypass regulatorio ou ambiguidade legal deve ser rejeitado no design e na execucao.
- **Dados reais obrigatorios**: sinais, analises e execucoes devem usar dados reais de mercado e fontes verificaveis.
- **Sem placeholders e sem fallback operacional**: para fluxo de negocio, proibido usar dado fake, mock oculto, resposta simulada ou fallback que altere decisao de trading.
- **Rastreabilidade completa**: cada decisao relevante precisa de log auditavel com timestamp, origem dos dados, versao de estrategia e resultado.

## Politica de Validacao por Camadas (Gate de Producao)
Nenhuma funcionalidade de execucao pode entrar em producao sem aprovacao em todas as camadas abaixo:

1. **Camada de Dados**
- Validar latencia, consistencia, integridade e disponibilidade das fontes reais.
- Rejeitar execucao quando o dado estiver incompleto, atrasado ou inconsistente.

2. **Camada de Estrategia**
- Validar regras de entrada/saida, risco e sizing com criterios objetivos.
- Exigir reprodutibilidade dos resultados em janelas historicas definidas.

3. **Camada de Risco**
- Aplicar limites obrigatorios: risco por ordem, exposicao agregada, perda diaria e travas de emergencia.
- Bloquear execucao fora dos limites aprovados.

4. **Camada de Integracao (Broker/Exchange)**
- Confirmar idempotencia de ordens, reconciliacao de posicao e tratamento de rejeicao/timeout.
- Exigir confirmacao de status de ordem antes de propagar resultado ao cliente.

5. **Camada de Observabilidade e Auditoria**
- Logs estruturados, metricas de execucao, alertas de falha e trilha de auditoria.
- Capacidade de reconstruir evento a evento para revisao tecnica e compliance.

6. **Camada de Producao**
- Liberacao progressiva (paper trading -> canario -> producao completa).
- Rollback documentado e testado.

## Regra de Execucao para Novas Demandas
- Toda nova solicitacao tecnica deve ser implementada seguindo esta politica como padrao.
- Se a solicitacao conflitar com compliance, seguranca ou governanca de risco, a implementacao deve ser ajustada para manter conformidade.
- Respostas e implementacoes devem deixar explicito quando uma etapa ainda nao atende o gate de producao.

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
- Todo alerta segue o padrão estrito de schema da UNI IA (Score, Classificação, Explicação, Fontes).

## Módulos de Telegram (Free e Premium)
- **Robô Free**: Dita os sinais essenciais para todos os usuários cadastrados.
- **Robô Premium**: Transmite sinais **exclusivos para Dólar (USD), Euro (EUR) e Real (BRL)**.
