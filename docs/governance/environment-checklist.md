# Environment Checklist - UNI IA

## Objetivo

Checklist minimo para validar que um ambiente local ou de homologacao atende ao baseline operacional da UNI IA.

## Backend

- Python `3.11.x` instalado e acessivel no terminal
- ambiente virtual ativado antes da instalacao
- `pip install -r ai-sentinel/requirements.txt` executado sem erro
- `python -c "import pydantic_core"` executa sem erro
- `python -m unittest discover -s tests` em `ai-sentinel/` retorna `OK`
- sem `DeprecationWarning` critico no fluxo validado

## Backtest

- `python run_backtest.py --asset BTCUSDT --csv tests/sample_backtest.csv --strategy tests.sample_strategy:generate_signal --output-dir backtest_output`
  executa sem erro
- `summary.json` e artefatos de exportacao sao gerados
- metricas de governanca aparecem no `summary.json`

## Frontend

- Node.js `20.x` ativo no ambiente
- `npm install` em `zairyx-blog/` executa sem erro
- `npm run build` em `zairyx-blog/` conclui com sucesso
- warnings nao bloqueantes devem ser registrados e tratados em hardening subsequente

## Governanca

- specs em `docs/specs/` refletem o estado atual do sistema
- baseline de runtime em `docs/governance/runtime-baseline.md` corresponde ao ambiente validado
- slogan e discurso institucional continuam sustentados por contratos e codigo reais

## Criterio de Aprovacao

O ambiente so deve ser considerado apto quando todos os itens obrigatorios estiverem conformes.
