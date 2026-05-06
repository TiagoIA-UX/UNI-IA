# Stress Test Institucional - v1

**Projeto:** UNI IA  
**Objetivo:** Validar impacto estrutural do `RiskFilter` sob pressao real de mercado

---

## 1. Hipotese

O `RiskFilter` reduz exposicao destrutiva em cenarios adversos, preservando capital sem comprometer de forma desproporcional o retorno liquido.

---

## 2. Metodologia

### Configuracao Experimental

- Mesmo dataset
- Mesma estrategia base
- Mesma configuracao de risco
- Mesmo capital inicial
- Mesmas fees e slippage
- Mesma execucao deterministica
- Unica variavel alterada: `RiskFilter`

### Cenarios

- **Cenario A:** `RiskFilter` ativo
- **Cenario B:** `RiskFilter` inativo

### Metricas Avaliadas

- `max_drawdown_pct`
- `net_profit`
- `discipline_ratio`
- `capital_protected_estimate`

### Criterio de Classificacao Predefinido

O filtro seria classificado como `RISK_FILTER_PROTECTIVE` se:

- a reducao de `max_drawdown_pct` fosse igual ou superior a `20%`
- e a variacao de `net_profit` nao implicasse deterioracao superior a `10%`

Sem ajuste posterior de criterio apos a execucao.

---

## 3. Dataset

- **Arquivo:** `ai-sentinel/tests/sample_stress_backtest.csv`
- **Periodo:** `2026-02-01T00:00:00Z` a `2026-02-01T19:00:00Z`
- **Ativo:** `BTCUSDT`
- **Timeframe:** candles sequenciais do arquivo de teste
- **Regime predominante:** tendencia descendente persistente com pressao adversa para sinais `long`

---

## 4. Resultados Comparativos

| Metrica                    | Com RiskFilter | Sem RiskFilter | Variacao |
| -------------------------- | -------------- | -------------- | -------- |
| max_drawdown_pct           | 2.2896         | 10.8281        | -78.8550% |
| net_profit                 | -228.9550804   | -1082.8126240  | +78.8555% |
| discipline_ratio           | 0.8000         | 0.0000         | +0.8000 |
| capital_protected_estimate | 781.68359357   | 0.00000000     | +781.68359357 |

---

## 5. Analise

- O filtro reduziu `max_drawdown_pct` em `78.8550%`.
- O impacto no resultado liquido foi positivo neste experimento: a perda liquida caiu de `-1082.8126240` para `-228.9550804`.
- A disciplina operacional passou de `0.0000` para `0.8000`, refletindo intervencao institucional em `8` de `10` sinais.
- A estimativa de capital protegido foi `781.68359357`.
- Sem `RiskFilter`, a estrategia executou `10` trades perdedores consecutivos.
- Com `RiskFilter`, a execucao foi interrompida estruturalmente apos `2` trades perdedores, reduzindo a continuidade da degradacao.

---

## 6. Conclusao Objetiva

- O `RiskFilter` **protege** capital sob pressao neste regime testado.
- A reducao de drawdown **compensa** a variacao de retorno, pois o filtro conteve a degradacao estrutural e reduziu a perda liquida total.
- **Recomendacao:** manter o `RiskFilter` como camada obrigatoria do motor e repetir o experimento em regimes adicionais antes de qualquer generalizacao comercial ampla.

---

## 7. Proximos Passos

1. Repetir o experimento em dois regimes adicionais:
   - mercado fortemente tendencial favoravel
   - mercado lateral de baixa volatilidade
2. Consolidar baseline historico dos stress tests.
3. So entao propor o `Structural Protection Index`.
