# Especificacao Tecnica - Backtest Engine UNI IA

## Objetivo

Definir a arquitetura-base do motor de backtest da UNI IA para garantir determinismo, auditabilidade e independencia arquitetural.

## Escopo

Este documento cobre os componentes internos atualmente usados pelo backtest:

- `ai-sentinel/core/signal_provider.py`
- `ai-sentinel/core/risk_filter.py`
- `ai-sentinel/core/backtest_engine.py`
- `ai-sentinel/core/execution_simulator.py`
- `ai-sentinel/core/portfolio_state.py`
- `ai-sentinel/adapters/strategy_engine_adapter.py`

## Principios Arquiteturais

1. O backtest deve ser deterministico para a mesma serie de candles e a mesma configuracao.
2. O runtime operacional nao deve depender do loop de backtest.
3. A geracao de sinal deve ocorrer por contrato formal, nunca por acoplamento estrutural.
4. A simulacao de execucao deve ser separada da estrategia.
5. O estado de portfolio deve ser observavel e auditavel durante toda a execucao.

## Componentes

### SignalProvider

Contrato de entrada do motor.

Responsabilidades:

- Receber `MarketData` com `asset`, janela historica e indice atual.
- Produzir `Signal` ou `None`.
- Permanecer desacoplado das regras de execucao.

Observacao:

- O engine aceita tambem um provider legado baseado em funcao para compatibilidade controlada.

### BacktestEngine

Orquestrador do loop principal.

Responsabilidades:

- Iterar candle a candle.
- Solicitar sinal apenas quando nao houver trade aberto.
- Submeter cada sinal a governanca de risco antes de criar entrada pendente.
- Agendar entrada para o candle seguinte.
- Registrar decisoes operacionais para auditoria.
- Consolidar trades, equity curve e metricas finais.

### RiskFilter

Camada institucional entre sinal e execucao.

Responsabilidades:

- Avaliar se o sinal pode seguir para execucao.
- Bloquear o sistema quando status institucional impedir operacao.
- Rejeitar sinais em condicoes de drawdown ou streak negativo acima do limite.
- Reduzir tamanho de posicao quando o modo ou o estado do sistema exigir prudencia.
- Emitir decisoes auditaveis: `approved`, `rejected`, `reduced_size` e `blocked_system`.

### ExecutionSimulator

Camada de execucao simulada.

Responsabilidades:

- Abrir operacoes no open do candle seguinte.
- Aplicar spread, slippage e fees.
- Dimensionar posicao por risco.
- Avaliar stop loss e take profit.
- Marcar PnL em aberto entre eventos de fechamento.

### PortfolioState

Ledger de capital e drawdown.

Responsabilidades:

- Atualizar caixa e PnL realizado apos fechamento.
- Registrar snapshots de equity.
- Calcular pico de equity, drawdown absoluto e drawdown percentual.
- Bloquear a execucao quando o limite maximo de drawdown for excedido.

### StrategyEngine Adapter

Adaptador entre estrategia institucional e contrato de backtest.

Responsabilidades:

- Traduzir a decisao da estrategia para o contrato `SignalProvider`.
- Isolar a logica de sinal do loop de execucao.
- Preservar compatibilidade sem contaminar o core do backtest.

## Fluxo Operacional

1. Carregar serie historica de candles.
2. Inicializar `BacktestEngine` com `SignalProvider`, `ExecutionSimulator` e `PortfolioState`.
3. Para cada candle:
   - verificar bloqueio de portfolio;
   - abrir sinal pendente no candle atual;
   - atualizar ou fechar trade aberto;
   - gerar novo sinal apenas se nao houver trade aberto e houver candle seguinte;
   - submeter o sinal ao `RiskFilter` antes de transformalo em entrada pendente.
4. Encerrar operacao remanescente no fim da serie com marcacao de mercado.
5. Consolidar metricas, decisoes e curva de equity.
6. Exportar artefatos auditaveis quando solicitado.

## Garantias de Determinismo

- Entrada sempre ocorre no candle seguinte ao sinal.
- Fechamento depende apenas de OHLC, custos configurados e regras internas.
- Nao ha dependencia de LLM, rede ou contexto externo durante a execucao do backtest.
- Parametros de custo e risco devem ser explicitamente configurados por ambiente ou construtor.

## Artefatos de Auditoria

O motor deve ser capaz de produzir:

- `trades.csv`
- `equity_curve.csv`
- `decisions.json`
- `summary.json`

O `summary.json` deve incluir:

- metricas de performance
- metricas de governanca

Metricas minimas de governanca:

- `total_signals`
- `signals_blocked_by_risk`
- `signals_reduced_by_risk`
- `discipline_ratio`
- `capital_protected_estimate`

## Regras de Evolucao

- Novos filtros, como `RiskFilterAdapter`, devem entrar como camada composicional antes da execucao, sem romper o contrato do `SignalProvider`.
- Mudancas no loop de execucao exigem atualizacao desta especificacao antes da implementacao definitiva.
- Qualquer inspiracao externa deve ser registrada primeiro em `docs/research/`.
