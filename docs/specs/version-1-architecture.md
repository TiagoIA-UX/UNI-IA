# Arquitetura v1 - Baseline Institucional

## Status

Baseline congelada em 2026-04-16 como referencia institucional da UNI IA.

Esta versao representa:

- backtest deterministico
- governanca observavel
- separacao formal entre sinal, risco e execucao
- telemetria minima de disciplina

Esta versao nao representa:

- validacao estatistica de longo prazo
- arquitetura multi-agent de alocacao
- runtime live multi-mandato

## Objetivo

Congelar a arquitetura-base atual para evitar drift silencioso e servir como referencia oficial antes da evolucao para portfólio multi-mandato.

## Componentes Congelados

- `ai-sentinel/core/signal_provider.py`
- `ai-sentinel/core/backtest_engine.py`
- `ai-sentinel/core/risk_filter.py`
- `ai-sentinel/core/execution_simulator.py`
- `ai-sentinel/core/portfolio_state.py`
- `ai-sentinel/core/system_state.py`
- `ai-sentinel/core/runtime_config.py`
- `ai-sentinel/adapters/strategy_engine_adapter.py`
- `ai-sentinel/run_backtest.py`

## Fluxo Oficial v1

`SignalProvider -> RiskFilter -> BacktestEngine -> ExecutionSimulator -> PortfolioState`

Descricao operacional:

1. `SignalProvider` gera um sinal formal ou retorna `None`.
2. `RiskFilter` avalia bloqueio, rejeicao ou reducao de tamanho.
3. `BacktestEngine` agenda a entrada para o candle seguinte.
4. `ExecutionSimulator` aplica custos, slippage e regras de fechamento.
5. `PortfolioState` consolida equity, drawdown e bloqueios do portfolio.

## Contratos Institucionais

### Contrato de Sinal

- Entrada via `SignalProvider.generate(MarketData) -> Optional[Signal]`
- Sinal formal com `asset`, `side`, `score`, `stop_loss`, `take_profit` opcional e `position_size_multiplier`

### Contrato de Risco

- Entrada via `RiskFilter.evaluate(PortfolioState, Signal) -> RiskDecision`
- Decisoes permitidas:
  - `approved`
  - `rejected`
  - `reduced_size`
  - `blocked_system`

### Contrato de Execucao

- Entrada ocorre no open do candle seguinte ao sinal aprovado
- Fechamento depende exclusivamente de OHLC, custos e regras internas

## Garantias v1

- determinismo para mesma serie e mesma configuracao
- auditabilidade por `decisions.json`
- metricas de governanca no `summary.json`
- separacao entre logica de alpha e logica de disciplina
- clean room documentado em `docs/governance/clean-room-study.md`

## Backward Compatibility Guarantee

A arquitetura v1 e o nucleo imutavel da UNI IA.

Garantias:

- a v1.1 sera camada superior opcional, nunca substituicao do nucleo
- se a v1.1 for desativada, o fluxo retorna para `SignalProvider -> RiskFilter -> BacktestEngine -> ExecutionSimulator -> PortfolioState`
- nenhum contrato executavel da v1 pode ser quebrado pela presenca ou ausencia da v1.1
- o `BacktestEngine` deve manter modo single-agent nativo como comportamento padrao
- rollback da v1.1 nao pode exigir migracao de contrato no core v1

## Telemetria Minima v1

### Performance

- `total_trades`
- `wins`
- `losses`
- `win_rate`
- `profit_factor`
- `avg_rr`
- `max_drawdown`
- `max_drawdown_pct`
- `sharpe_ratio`
- `expectancy`
- `longest_losing_streak`
- `net_profit`

### Governanca

- `total_signals`
- `signals_blocked_by_risk`
- `signals_reduced_by_risk`
- `discipline_ratio`
- `capital_protected_estimate`

## Limites Conhecidos da v1

- portfolio unico, sem segmentacao por mandato
- um fluxo de execucao por vez no loop principal
- sem comparativo estatistico longo consolidado
- sem alocador institucional de capital
- sem roteamento multi-agent

## Regra de Mudanca

Qualquer alteracao em contratos, loop principal ou telemetria minima exige:

1. atualizacao de `docs/specs/`
2. testes dedicados
3. justificativa arquitetural antes da implementacao definitiva

## Proxima Evolucao Prevista

A v1.1 introduzira arquitetura multi-agent por mandato de risco, preservando o core da v1 como camada de execucao governada.
