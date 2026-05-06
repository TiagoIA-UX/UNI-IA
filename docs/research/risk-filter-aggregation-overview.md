# Risk Filter - Aggregation Overview

## Objetivo

Definir a camada formal de agregacao institucional para sinais, classificacoes, timeframes e mandatos, com saida deterministica e auditavel.

## Problema Resolvido

Sem agregacao formal, o sistema consegue mostrar comportamento local, mas nao estatistica institucional.

Esta camada existe para evitar:

- leitura manual de artefatos dispersos
- conclusao por amostra isolada
- comparacao informal entre carteiras ou mandatos
- divergencia entre painel visual e pipeline oficial

## Dimensoes Minimas

Cada registro agregado deve expor, no minimo:

- `day`
- `classification`
- `timeframe`
- `strategy`
- `mandate`

O `day` nao e apenas informativo: ele permite consolidacao diaria e leitura de comportamento operacional por janela de calendario.

## Metricas Minimas

- `raw_signals_per_day`
- `executed_signals_per_day`
- `blocked_rate`
- `execution_rate`
- `drawdown_reduction_pct`
- `net_profit_delta_pct`
- `capital_protected`

## Agrupamentos Institucionais

Para evitar leitura isolada, a camada formal deve disponibilizar agregados combinados:

- `by_day`
- `by_classification`
- `by_timeframe`
- `by_mandate`
- `by_strategy`
- `by_day_classification`
- `by_timeframe_mandate`
- `by_classification_timeframe`
- `by_classification_timeframe_mandate`

## Fonte de Verdade

Os dados agregados devem ser derivados de reports congelados da serie.

Regras:

- hash do dataset valida integridade da amostra
- hash do runner valida integridade do experimento
- hash da estrategia valida integridade do gerador de sinais
- qualquer mudanca de hash abre nova serie

## Integridade do Snapshot

Cada snapshot agregado deve registrar:

- `generated_at`
- `run_id`
- `schema_version`
- `risk_filter_version`
- `dataset_sha256`
- `strategy_sha256`
- `runner_sha256`
- `report_sha256`
- `snapshot_checksum`

O checksum deve ser calculado sobre a representacao canonica do snapshot antes da insercao do proprio checksum. Isso permite verificacao externa sem ambiguidade.

## Saida Institucional

O agregador produz:

- um snapshot para documento institucional
- um snapshot para consumo do frontend

## Relacao com o Painel

O painel institucional pode exibir:

- status geral dos gates
- KPIs agregados
- distribuicao por janela
- agregacao por classificacao, timeframe, mandato e dia
- agregacoes combinadas para leitura operacional por regime e carteira
- identificacao da rodada e checksum do snapshot

Sem essa camada, o painel mostra observacao.
Com essa camada, o painel mostra governanca consolidada.

## Status Atual

Na serie atual, a agregacao formal pode responder:

- quantos sinais brutos por dia o sistema emitiu
- quantos sinais foram executados apos filtro
- qual foi a taxa de bloqueio
- qual foi o comportamento por classificacao
- qual foi o comportamento combinado por classificacao, timeframe e mandato

## Proximo Passo

Executar o agregador deterministico sobre os reports congelados e expor o snapshot no painel institucional.
