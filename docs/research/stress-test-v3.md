# Stress Test Institucional - v3

**Projeto:** UNI IA  
**Objetivo:** Validar impacto estrutural do `RiskFilter` em regime lateral com ruido

---

## 1. Hipotese

O `RiskFilter` deve aumentar disciplina e reduzir desgaste progressivo de capital em ambiente lateral com ruido.

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

- **Arquivo:** `ai-sentinel/tests/sample_lateral_backtest.csv`
- **Periodo:** `2026-04-01T00:00:00Z` a `2026-04-01T19:00:00Z`
- **Ativo:** `BTCUSDT`
- **Timeframe:** candles sequenciais do arquivo de teste
- **Regime declarado antes da execucao:** lateral com ruido

---

## 4. Resultados Comparativos

| Metrica                    | Com RiskFilter | Sem RiskFilter | Variacao |
| -------------------------- | -------------- | -------------- | -------- |
| max_drawdown_pct           | 2.2938         | 10.9536        | -79.0589% |
| net_profit                 | -229.37943415  | -1095.35541575 | +79.0589% |
| discipline_ratio           | 0.8000         | 0.0000         | +0.8000 |
| capital_protected_estimate | 781.64964527   | 0.00000000     | +781.64964527 |

---

## 5. Analise

- O filtro reduziu `max_drawdown_pct` em `79.0589%`.
- O impacto no resultado liquido foi positivo neste experimento: a perda liquida caiu de `-1095.35541575` para `-229.37943415`.
- A disciplina operacional passou de `0.0000` para `0.8000`, refletindo intervencao institucional em `8` de `10` sinais.
- A estimativa de capital protegido foi `781.64964527`.
- Sem `RiskFilter`, a estrategia executou `10` trades perdedores consecutivos em ambiente de churn elevado.
- Com `RiskFilter`, a execucao foi interrompida estruturalmente apos `2` trades perdedores.

---

## 6. Conclusao Objetiva

- O `RiskFilter` **protege** capital sob ruido lateral neste regime testado.
- A reducao de drawdown **compensa** a variacao de retorno, pois o componente conteve a degradacao estrutural e reduziu a perda liquida total.
- **Recomendacao:** manter o `RiskFilter` como camada obrigatoria em cenarios de churn e seguir para consolidacao da serie.

---

## 7. Proximos Passos

1. Executar o regime de volatilidade extrema sob o mesmo protocolo.
2. Consolidar a leitura da serie v1-v4 sem alterar criterio.
3. Avaliar consistencia transversal antes de qualquer nova tese proprietaria.
