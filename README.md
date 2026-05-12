# Boitatá IA — Suporte institucional à decisão em investimentos

**Repositório:** [TiagoIA-UX/UNI-IA](https://github.com/TiagoIA-UX/UNI-IA)

---

## 1. Sumário para auditoria e due diligence

| Domínio | Descrição |
|--------|-----------|
| **Natureza do software** | Sistema de suporte à decisão (orquestração de agentes, governança, registo auditável). **Não** constitui recomendação financeira automatizada nem substitui assessoria jurídica, contábil ou tributária. |
| **Estado de maturidade** | **Desenvolvimento ativo.** Antes de operação relevante em **conta real**, deve existir **release** documentado com notas de risco e checklist operacional. |
| **Rastreabilidade** | Eventos operacionais persistidos (ex.: auditoria, mesa, *logs* JSONL conforme configuração). Módulo **DOC** (`boitata-doc/`) e *ledger* opcional (`DOC_LEDGER_*`) destinam-se a **evidência técnica pré-contábil**, sem integração automática com programas oficiais da RFB. |
| **Dados pessoais** | Conformidade com bases legais aplicáveis (ex.: LGPD 13.709/2018), políticas do *deploy* e contratos de subscrição de serviços utilizados. |
| **Mercado de valores mobiliários / criptoativos** | Referências regulatórias indicativas no aviso de risco (secção 12). O operador mantém responsabilidade pelo enquadramento da atividade e pelas obrigações acessórias. |

---

## 2. Visão geral do produto

Boitatá IA é uma plataforma de **governança e orquestração** de múltiplos agentes analíticos (macro, técnico, notícias, sentimento, risco, etc.), com **fluxos de aprovação**, **modos operacionais** (*paper* / *approval* / *live*) e **trilhas de auditoria**.

**Princípios declarados:**

- Operação com **capital preservado**: limites por posição e mecanismos de *kill-switch*, conforme configuração.
- **Transparência operacional**: rejeições e estados registados quando os subsistemas estão ativos.
- **P&D condicionado a governança** e disponibilidade de caixa institucional (objetivos de produto).

---

## 3. Transparência fiscal e módulo DOC (experimental)

- **`boitata-doc/`** — pacote com modelos documentais (`EntradaDOC`, exportações CSV/JSON, NAO conceitual) para trabalho paralelo ao motor de execução.
- **`DOC_LEDGER_ENABLED` / `DOC_LEDGER_PATH`** — *ledger* JSONL **opcional** no `ai-sentinel` (`core/doc_ledger.py`): regista, após execuções bem-sucedidas no broker, metadados com **indício** de contexto temporal (*hint* DAY/SWING). A **matéria de facto tributária** (abertura/fecho, competência mensal, isenções) exige **conferência** com extratos da corretora e **profissional habilitado** (contador/advogado tributarista conforme caso).
- Procedimentos operacionais: `boitata-doc/docs/PROCEDIMENTOS-TESTE-AUDITORIA.md`.
- Script de permissões pasta `C:\` (uso administrativo local): `boitata-doc/scripts/win/ensure-boitatadoc-admin-c-drive.ps1`.

---

## 4. Identidade institucional: Conselho Guardião (metáfora analítica)

**Conselho Guardião** designa uma **estrutura lógica** de especialização: cada agente **associa nomenclatura** inspirada na **fauna-símbolo** dos Estados brasileiros unicamente como **rótulos de papel analítico** (macro, técnico, liquidez, narrativa etc.).

**Não se infere obrigação jurídica** de destinarem-se automaticamente valores a instituições de conservação pela mera nomenclatura. Qualquer política **voluntária** de financiamento a causas sociais ou ambientais é **atitude da entidade operadora**, **posterior ao cumprimento de obrigações legais, trabalhistas e fiscais**, e **sujeita a documentação própria** (contratos, recibos, pareceres).

### 4.1 Política de destinação a proteção animal (marco institucional)

Alinhável a objetivos corporativos de responsabilidade social, o projeto trabalha internamente com **meta facultativa de destinação de até 6% (seis por cento)** de recursos **líquidos disponíveis** (após impostos, encargos e reservas legais exigíveis) a **entidades ou mecanismos competentes** dedicados à **proteção animal**, **desde que** (i) haja **base legal e regulamentação vigentes** que permitam a operação; (ii) exista **due diligence** da entidade beneficiária; (iii) a **contabilidade** reconheça o dispêndio nos termos aplicáveis.

**Referência legislativa em tramitação (consulta obrigatória ao texto e situação atual no site oficial):**

- **PL 3.726/2023** (Senado Federal) — projeto que, conforme relatórios parlamentares e imprensa especializada em trâmite até 2026, objetiva autorizar deduções no âmbito do IRPF relacionadas a doações para fins de proteção animal.  
  **Página oficial da matéria:** [Senado Federal — materia 158929](https://www25.senado.leg.br/web/atividade/materias/-/materia/158929).

**Aclarações:**

- Projeto não sancionado **não gera direito nem obrigação** automática; o texto pode ser alterado na tramitação.
- O software **não automatiza pagamentos** nem concilia obrigações acessórias perante a RFB relativamente a essa meta; eventual implementação será **explicitada em versão estável**, com registos compatíveis com auditoria.

---

## 5. Provedores de IA externa (incl. Forge Ops AI)

- **Groq:** utilizado através de cliente configurável no *backend* (`GROQ_API_KEY` etc.), conforme `ai-sentinel` e `.env.example`.
- **Forge Ops AI / ForgeOps:** **não existe integração técnica** (dependências, chamadas SDK ou URLs) nos pacotes `ai-sentinel` e `zairyx-frontend` deste repositório. Menções passadas a “proveedor alternativo” constituem **referência de roadmap ou documentação legada** e **não** representam funcionalidade ativa até implementação e documentação de release.

---

## 6. Quick start (desenvolvimento local)

```bash
git clone https://github.com/TiagoIA-UX/UNI-IA.git
cd UNI-IA
cp .env.example .env.local
# Preencha chaves (Supabase, Groq, Telegram, broker, etc.)

cd ai-sentinel
python -m venv venv
# Windows: venv\Scripts\activate
source venv/bin/activate
pip install -r requirements.txt
python run_local_api.py

cd ../zairyx-frontend
npm install
npm run dev
# http://localhost:3000
```

---

## 7. Releases e política de versionamento

```bash
git tag
git checkout v1.2.0
```

- **Cadência desejada:** *patch* (correção), *minor* (funcionalidades), *major* (*breaking* ou governança).
- Marcos do módulo DOC: tags `v*-doc-*` (ex.: pré-release **`v1.3.0-doc-beta`**) indicam estado do **instrumento documental**, **não** homologação de investimento nem certificação regulatória.
- Lista e notas em: [GitHub Releases](https://github.com/TiagoIA-UX/UNI-IA/releases).

---

## 8. Arquitetura resumida: fluxo decisório

```
ENTRADA (dados de mercado e operador)
       ↓
┌──────────────────────────────────────────────────────────────┐
│  CONSELHO GUARDIÃO — agentes analíticos (metáfora regional) │
│  (ex.: harpia/macroeconomia, onça/técnico, boto/sentimento) │
└──────────────────────────────────────────────────────────────┘
       ↓ ponderação agregada
┌──────────────────────────────────────────────────────────────┐
│  ORQUESTRADOR — score, classificação, direção sugerida       │
└──────────────────────────────────────────────────────────────┘
       ↓ *gates* de risco e modo operacional
┌──────────────────────────────────────────────────────────────┐
│  MESA / COPY TRADE — conforme UNI_IA_MODE e configuração   │
└──────────────────────────────────────────────────────────────┘
       ↓
SAÍDA (ordem vetada, pendente de aprovação ou executada com log)
```

Documentação detalhada dos agentes: `AGENTES_GUARDIAO.md`.

---

## 9. Resiliência de LLM

Em falha repetida do provedor primário:

- Fluxo pode ser interrompido conforme política implementada (*Mandato Zero Bug* onde aplicável).
- Alertas para canal administrativo (Telegram), quando parametrizados.
- Registo em tabela/eventos de auditoria com tipo explícito (ex.: falha LLM).

Variáveis de exemplo: `LLM_FALLBACK_*` em `.env.example`.

---

## 10. Governança em camadas (resumo)

- **Capital / risco:** limites por posição e circuit breakers parametrizados.
- **Gates decisórios:** score mínimo, *whitelist*, modo operacional (*paper* vs *live*), aprovação manual opcional.

---

## 11. Rastreabilidade e artefactos típicos

| Artefacto | Conteúdo indicativo |
|-----------|---------------------|
| `uni_ia_operational_audit` | Decisões, rejeições, execuções, falhas sistémicas (quando integração BD ativa) |
| Mesas (*desk*) | Pedidos de aprovação, histórico de decisões |
| `signal_dispatch` (JSONL) | Sinais transmitidos (retenção conforme política) |
| `risk_events` (JSONL) | Eventos de *kill-switch* e limites |
| `doc_ledger.jsonl` (opcional) | Metadados pós-ordem para cruzamento com DOC |

---

## 12. Documentação complementar

| Recurso | Público-alvo |
|---------|----------------|
| `INSTALLATION.md` | Primeira instalação |
| `AGENTES_GUARDIAO.md` | Conselho e papéis |
| `boitata-doc/README.md` | Módulo DOC |
| `schema.sql` | Base de dados |
| `.env.example` | Variáveis de ambiente |

---

## 13. Roadmap (indicativo)

| Fase | Itens |
|------|--------|
| **Atual** | Conselho multi-agente, governança em camadas, modos *paper* / *approval* / *live*, auditoria, alertas de LLM, módulo DOC experimental |
| **Curto prazo** | Latência, cobertura de ativos, refino de pesos com *feedback* |
| **Médio prazo** | Estratégias e *multi-timeframe* documentados em release |
| **Futuro** | APIs B2B / analytics (sujeito a licenciamento BUSL) |

---

## 14. Contribuição e padrão de commits

```bash
git checkout -b fix/descricao-curta
# PR para main; *issues* para *features* com impacto de negócio
```

Padrões: `feat:` · `fix:` · `docs:` · `refactor:` · `perf:` · `test:` · `chore:`

---

## 15. Princípios operacionais

- Dados reais em execução (sem *placeholders* em caminho crítico).
- Modo *paper* por defeito na configuração de exemplo; transição para *live* documentada.
- Falhas comunicadas; estados explicitamente nomeados (`paper`, `approval`, `live`).

---

## 16. Licença

**Business Source License 1.1 (BUSL-1.1)** — uso comercial mediante autorização. Conversão OSS prevista conforme arquivo de licença. Titular conforme registo do repositório.

---

## 17. Aviso de risco

Este software **não é recomendação de investimento.** Mercados financeiros e criptoativos comportam **perda de capital**. Responsabilidade do operador. Consulte profissionais e normas aplicáveis (ex.: Bacen/CVM conforme caso, LGPD para dados pessoais). **Ausência de garantia tributária** quanto a tratamento de DAY TRADE ou GANHO DE CAPITAL até análise individualizada.

---

## 18. Tese institucional (atenção ao risco e à disciplina)

- Estratégia sustentável exige governança, não apenas sinalização.
- Diversificação sem controlo de risco não equivale a proteção de capital.
- P&D institucional deve estar subordinado a critérios de caixa e compliance.
