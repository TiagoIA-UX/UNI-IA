# Stress Test Institucional - v4

**Projeto:** UNI IA  
**Objetivo:** Validar impacto estrutural do `RiskFilter` em regime de volatilidade extrema

---

## 1. Hipotese

O `RiskFilter` deve atuar como mecanismo de sobrevivencia estrutural em regime de volatilidade extrema, mesmo que sem preservar upside.

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

- **Arquivo:** `ai-sentinel/tests/sample_extreme_backtest.csv`
- **Periodo:** `2026-05-01T00:00:00Z` a `2026-05-01T19:00:00Z`
- **Ativo:** `BTCUSDT`
- **Timeframe:** candles sequenciais do arquivo de teste
- **Regime declarado antes da execucao:** volatilidade extrema

---

## 4. Resultados Comparativos

| Metrica                    | Com RiskFilter | Sem RiskFilter | Variacao |
| -------------------------- | -------------- | -------------- | -------- |
| max_drawdown_pct           | 2.2822         | 10.8846        | -79.0328% |
| net_profit                 | -228.22035509  | -1088.45846257 | +79.0327% |
| discipline_ratio           | 0.8000         | 0.0000         | +0.8000 |
| capital_protected_estimate | 781.74237159   | 0.00000000     | +781.74237159 |

---

## 5. Analise

- O filtro reduziu `max_drawdown_pct` em `79.0328%`.
- O impacto no resultado liquido foi positivo neste experimento: a perda liquida caiu de `-1088.45846257` para `-228.22035509`.
- A disciplina operacional passou de `0.0000` para `0.8000`, refletindo intervencao institucional em `8` de `10` sinais.
- A estimativa de capital protegido foi `781.74237159`.
- Sem `RiskFilter`, a estrategia manteve sequencia de `10` perdas em ambiente de variacao abrupta de range.
- Com `RiskFilter`, a execucao foi interrompida estruturalmente apos `2` trades perdedores.

---

## 6. Conclusao Objetiva

- O `RiskFilter` **protege** capital sob volatilidade extrema neste regime testado.
- A reducao de drawdown **compensa** a variacao de retorno, pois o componente conteve dano estrutural e reduziu a perda liquida total.
- **Recomendacao:** manter o componente como camada obrigatoria de sobrevivencia estrutural em contextos de choque.

---

## 7. Proximos Passos

1. Consolidar os resultados da serie v1-v4.
2. Verificar se o comportamento protetivo se repete de forma transversal, nao apenas em um regime isolado.
3. Somente apos a consolidacao, avaliar se existe base para propor uma metrica proprietaria.
