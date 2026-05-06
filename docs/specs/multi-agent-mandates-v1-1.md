# Arquitetura v1.1 - Multi-Agent por Mandato

## Objetivo

Definir a evolucao institucional da UNI IA de engine de decisao governada para sistema de gestao de capital multi-mandato.

O objetivo da v1.1 nao e multiplicar estilos de trader.
O objetivo e compartimentalizar risco e capital por mandato institucional.

## Principio Estrutural

Agentes devem ser separados por mandato de risco, nao por timeframe ou estilo narrativo.

Mandato define:

- objetivo de capital
- limite de perda
- faixa de exposicao
- severidade do `RiskFilter`
- criterio de interrupcao

## Mandatos Iniciais

### Core

Funcao:

- preservar sobrevivencia do portfolio
- operar com baixa rotatividade
- absorver o menor risco relativo

Diretrizes:

- maior parcela de capital
- alavancagem zero ou minima
- drawdown tolerado menor
- disciplina mais conservadora

### Alpha Controlado

Funcao:

- gerar retorno incremental com risco controlado

Diretrizes:

- risco fixo por operacao
- stop obrigatorio
- exposicao intermediaria
- disciplina equilibrada entre retorno e prudencia

### Tatico

Funcao:

- buscar assimetria em estrategias agressivas ou experimentais

Diretrizes:

- menor parcela de capital
- kill switch mais rapido
- drawdown maximo mais severo
- `RiskFilter` mais restritivo

## Componentes Novos

### MandateAgent

Representa um mandato institucional com politica propria de risco e capital.

Contrato proposto:

```python
class MandateAgent(Protocol):
    mandate_id: str

    def can_accept(self, signal: Signal) -> bool:
        ...

    def build_context(self, portfolio_state: PortfolioState) -> dict:
        ...

    def position_policy(self, signal: Signal, portfolio_state: PortfolioState) -> "AllocationDecision":
        ...
```

Responsabilidades:

- declarar elegibilidade do sinal para o mandato
- informar politica de alocacao
- expor limites proprios para governanca

### AgentRouter

Decide qual mandato pode absorver o sinal.

Contrato proposto:

```python
class AgentRouter:
    def route(self, signal: Signal, agents: list[MandateAgent]) -> "RoutingDecision":
        ...
```

Responsabilidades:

- escolher o mandato elegivel
- rejeitar sinais sem mandato valido
- registrar decisao de roteamento para auditoria

### PortfolioAllocator

Aplica o orcamento institucional antes do `RiskFilter`.

Contrato proposto:

```python
class PortfolioAllocator:
    def allocate(
        self,
        signal: Signal,
        mandate_agent: MandateAgent,
        portfolio_state: PortfolioState,
    ) -> "AllocationDecision":
        ...
```

Responsabilidades:

- definir exposicao maxima por mandato
- reduzir capital disponivel conforme o budget do mandato
- impedir concentracao excessiva

### MandateContext

Estrutura de contexto passada ao `RiskFilter`.

Campos minimos sugeridos:

- `mandate_id`
- `mandate_type`
- `capital_budget`
- `drawdown_pct_limit`
- `risk_multiplier`
- `kill_switch_status`

## Fluxo v1.1 Proposto

`SignalProvider -> AgentRouter -> PortfolioAllocator -> RiskFilter -> ExecutionSimulator -> PortfolioState`

Descricao:

1. `SignalProvider` gera um sinal formal.
2. `AgentRouter` escolhe o mandato elegivel.
3. `PortfolioAllocator` aplica orcamento e limite de exposicao do mandato.
4. `RiskFilter` avalia o sinal com contexto institucional do mandato.
5. `ExecutionSimulator` executa apenas o sinal governado.
6. `PortfolioState` consolida a visao global.

## Activation Criteria

A v1.1 so pode ser ativada se todos os criterios abaixo forem satisfeitos em ambiente de backtest e replay deterministico:

- `discipline_ratio >= 0.25` ou valor superior definido por politica institucional vigente
- minimo de `300 trades` consolidados em amostra relevante
- `max_drawdown_pct <= 20.0` ou limite institucional vigente
- estabilidade de metricas em janelas rolling, sem degradacao estrutural nao explicada
- `0` inconsistencias de governanca nos artefatos `summary.json` e `decisions.json`

Regra institucional:

> A ativacao da v1.1 e decisao executiva baseada em evidencia, nao decisao tecnica baseada em entusiasmo.

Sem o cumprimento integral do gate acima, a v1.1 permanece apenas como especificacao arquitetural.

## Modelo de Capital v1.1

### Politica Inicial

A v1.1 inicia com capital unico e sub-orcamentos formais por mandato.

Isto significa:

- existe uma unica equity global
- cada mandato opera sob `budget_limit` proprio
- drawdown sistemico continua afetando toda a estrutura
- metricas agregadas permanecem naturais no nivel do portfolio

### Justificativa

Esta abordagem reduz superficie de erro, preserva comparabilidade com a v1 e evita complexidade prematura de segregacao total de capital.

Segregacao plena por mandato fica reservada para evolucao posterior, potencialmente v1.2.

### Politica de Alocacao Inicial

Distribuicao inicial sugerida:

- `Core`: `60%` a `70%`
- `Alpha Controlado`: `20%` a `30%`
- `Tatico`: `5%` a `10%`

Os percentuais definitivos devem ser definidos por politica de risco antes da implementacao.

### Politica de Rebalanceamento

- rebalanceamento nao sera continuo por trade
- ajustes de budget devem ocorrer por evento formal de revisao, nao por improviso intraday
- qualquer rebalanceamento deve ser auditavel e registrado como evento de governanca

### Politica de Suspensao de Mandato

- um mandato pode ser suspenso sem paralisar os demais
- suspensao deve ocorrer por drawdown, falha de disciplina ou decisao executiva formal
- mandato suspenso nao recebe novas alocacoes ate revisao explicita

## Compatibilidade com a v1

A v1.1 deve preservar:

- o `BacktestEngine` como orquestrador do loop
- o `ExecutionSimulator` como camada de execucao
- o `RiskFilter` como autoridade final de disciplina
- o `summary.json` como artefato auditavel

A v1.1 nao deve:

- acoplar estrategia diretamente a execucao
- quebrar o contrato atual de `SignalProvider`
- remover as metricas de governanca existentes
- impedir rollback limpo para o modo single-agent da v1

## Telemetria Adicional Prevista

Cada mandato deve poder produzir:

- `mandate_total_signals`
- `mandate_blocked_signals`
- `mandate_reduced_signals`
- `mandate_discipline_ratio`
- `mandate_capital_allocated`
- `mandate_capital_protected`
- `mandate_max_drawdown_pct`

## Decisoes de Projeto

### Decisao 1

Mandato e unidade primaria de risco.

### Decisao 2

`RiskFilter` continua obrigatorio mesmo apos roteamento e alocacao.

### Decisao 3

Portfolio global continua sendo a verdade contábil final, mesmo com submandatos.

### Decisao 4

Implementacao deve ser incremental, com simulacao first e sem tocar no runtime live antes da validacao estatistica.

## Critérios de Entrada para Implementacao

A implementacao da v1.1 so deve comecar apos:

1. baseline v1 congelada
2. backtest longo comparativo executado
3. evidencia de que a governanca atual e estatisticamente util
4. aprovacao explicita do modelo de capital unico com sub-orcamentos
5. validacao formal de que rollback para v1 permanece disponivel

## Fora de Escopo da v1.1

- integracao com noticias
- LLM como decisor de alocacao
- regime adaptativo opaco
- execucao live multi-broker

## Resultado Esperado

Ao fim da v1.1, a UNI IA deixa de operar apenas como engine de sinais governados e passa a operar como estrutura de gestao de capital segmentada por mandato institucional.
