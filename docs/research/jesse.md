# Estudo Tecnico - Jesse

Licenca: MIT  
Objetivo do estudo: modelagem de estrategia e ciclo de backtest

## Pontos Observados

### Strategy Model

- Estrategias orientadas a classe
- Metodos previsiveis para entrada e saida

### Backtest Loop

- Loop sequencial
- Entrada no proximo candle

### Position Lifecycle

- Abertura
- Atualizacao
- Fechamento

## O que Aproveitar Conceitualmente

- Separacao clara entre estrategia e engine
- Ciclo deterministico

## O que Nao Reproduzir

- Estrutura de classes especifica
- Organizacao de arquivos
- Convencoes internas do projeto

## Decisao Arquitetural UNI IA

- Manter `SignalProvider` desacoplado do motor de execucao
- Manter `BacktestEngine` proprio em `ai-sentinel/core/backtest_engine.py`
- Manter `ExecutionSimulator` separado para custos, slippage e fechamento
