# Stress Test Series Protocol

## Objetivo

Congelar o protocolo institucional da serie de stress tests da UNI IA para garantir comparabilidade historica entre regimes, evitar ajuste oportunista e preservar integridade metodologica.

## Regras Congeladas

- mesmo `run_stress_test.py`
- mesma estrategia base
- mesma configuracao-base de risco e execucao
- mesmo criterio de classificacao
- mesma estrutura de relatorio
- nenhuma alteracao paramétrica entre regimes

Se qualquer item acima mudar, o experimento passa a ser classificado como nova serie e perde comparabilidade com a serie original.

## Registro de Integridade

### Runner congelado

- arquivo: `ai-sentinel/run_stress_test.py`
- SHA256: `90C2DDBCA905E41459BCA77B8902B983337ED32F9676E01B59753139A26A7D28`

### Estrategia-base congelada

- arquivo: `ai-sentinel/tests/sample_stress_strategy.py`
- SHA256: `495E937C44E9314EFBA4FCBAE6A2DCACBC4D5F09F99D2D2ACBACE82F44C0AE64`

### Datasets congelados

- `ai-sentinel/tests/sample_stress_backtest.csv`
  - SHA256: `E6436852D40BAC2D80F03860452D138AB6E732EC5A27934016E5CEA11EF8A901`
- `ai-sentinel/tests/sample_trend_backtest.csv`
  - SHA256: `C2DE0ED5CF4991AA85F739320EFA8046F1AFE651C90F467BCC9D4A77DED38FFD`
- `ai-sentinel/tests/sample_lateral_backtest.csv`
  - SHA256: `E64EC9B360F850D8359D998A4DA23A642ADB280C84C87EA339793E7419100D0E`
- `ai-sentinel/tests/sample_extreme_backtest.csv`
  - SHA256: `5D31EE81A6EFCB65EE72FCA9B3CC69B4D55B4BCCB5E101989C2276631C1144A7`

Qualquer alteracao de hash invalida a comparabilidade com a serie atual e exige abertura formal de nova serie experimental.

## Criterio de Classificacao Congelado

O `RiskFilter` sera classificado como `RISK_FILTER_PROTECTIVE` se:

- a reducao de `max_drawdown_pct` for igual ou superior a `20%`
- e a variacao de `net_profit` nao implicar deterioracao superior a `10%`

Caso contrario:

- `NEUTRAL`, quando a protecao for insuficiente para classificacao protetiva, mas sem dano estrutural claro
- `DETRIMENTAL`, quando houver dano estrutural de drawdown ou retorno acima do tolerado

## Regimes Declarados Antes da Execucao

### Regime v2 - Tendencial Favoravel

- arquivo proposto: `ai-sentinel/tests/sample_trend_backtest.csv`
- direcao predominante clara
- correcoes curtas
- baixa frequencia de reversao estrutural
- volatilidade moderada

Hipotese operacional:

- o `RiskFilter` nao deve destruir upside de forma desproporcional
- drawdown pode cair pouco, mas a degradacao de retorno nao deve ser excessiva

### Regime v3 - Lateral com Ruido

- arquivo proposto: `ai-sentinel/tests/sample_lateral_backtest.csv`
- range definido
- alta frequencia de falsos rompimentos
- oscilacao curta e erratica
- churn elevado

Hipotese operacional:

- o `RiskFilter` deve aumentar disciplina e reduzir desgaste progressivo de capital

### Regime v4 - Volatilidade Extrema

- arquivo proposto: `ai-sentinel/tests/sample_extreme_backtest.csv`
- movimentos abruptos
- ampliacao subita de range
- drawdowns rapidos
- recuperacoes agressivas ou colapsos prolongados

Hipotese operacional:

- o `RiskFilter` deve atuar como mecanismo de sobrevivencia estrutural, mesmo que sem preservar upside

## Ordem Recomendada de Execucao

1. `v1` - regime adverso ja executado e documentado
2. `v2` - tendencial favoravel
3. `v3` - lateral com ruido
4. `v4` - volatilidade extrema

## Estrutura Documental Congelada

Cada documento da serie deve repetir a mesma estrutura:

1. Hipotese
2. Metodologia
3. Dataset
4. Resultados comparativos
5. Analise
6. Conclusao objetiva
7. Proximos passos

Sem mudanca de linguagem, criterio ou forma de tabela entre versoes.
