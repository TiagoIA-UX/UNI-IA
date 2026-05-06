# Especificacao Tecnica - Risk Filter UNI IA

## Objetivo

Definir a camada de governanca que valida um sinal antes da execucao simulada ou operacional.

## Contrato

```python
class RiskFilter:
    def evaluate(self, portfolio_state: PortfolioState, signal: Signal) -> RiskDecision:
        ...
```

## Decisoes Possiveis

- `APPROVED`: sinal liberado sem ajuste
- `REJECTED`: sinal barrado por regra de risco
- `REDUCED_SIZE`: sinal liberado com reducao de exposicao
- `BLOCKED_SYSTEM`: sistema institucionalmente impedido de operar

## Entradas de Governanca

- drawdown corrente do portfolio
- streak de perdas acumulado
- risco-base por trade
- limite maximo de risco por trade
- modo institucional: `paper`, `approval`, `live`
- status do sistema: `locked`, `ready`, `degraded`, `halted`

## Regras Iniciais

1. `locked` ou `halted` geram `BLOCKED_SYSTEM`.
2. drawdown acima do limite configurado gera `REJECTED`.
3. streak negativo acima do limite configurado gera `REJECTED`.
4. modo `approval` reduz tamanho de posicao.
5. status `degraded` reduz tamanho de posicao.
6. risco por trade acima do teto configurado e convertido em reducao proporcional de tamanho.

## Integracao com o Backtest Engine

- O `BacktestEngine` chama `RiskFilter.evaluate(...)` logo apos gerar um sinal.
- A decisao do filtro e registrada em `decisions.json`.
- Em caso de `REDUCED_SIZE`, o sinal segue com `position_size_multiplier` ajustado.
- Em caso de `REJECTED`, o sinal e descartado.
- Em caso de `BLOCKED_SYSTEM`, o loop e interrompido de forma auditavel.

## Telemetria de Governanca

O backtest deve consolidar no `summary.json`:

- `total_signals`: total de sinais antes do filtro
- `signals_blocked_by_risk`: total de `REJECTED` e `BLOCKED_SYSTEM`
- `signals_reduced_by_risk`: total de `REDUCED_SIZE`
- `discipline_ratio`: `(signals_blocked_by_risk + signals_reduced_by_risk) / total_signals`
- `capital_protected_estimate`: soma do risco teorico nao exposto em sinais bloqueados

## Regras de Evolucao

- Novas politicas devem entrar no filtro sem acoplar o motor a fontes externas.
- Criticos institucionais devem continuar separados de logica de alpha.
- Qualquer mudanca de criterio exige atualizacao deste documento e testes dedicados.
