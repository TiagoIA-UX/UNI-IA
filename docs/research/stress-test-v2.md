# Stress Test Institucional - v2

**Projeto:** UNI IA  
**Objetivo:** Validar impacto estrutural do `RiskFilter` em regime tendencial favoravel

---

## 1. Hipotese

O `RiskFilter` nao deve destruir upside de forma desproporcional em regime tendencial favoravel. Se nao houver degradacao estrutural de drawdown ou retorno, o componente deve ser classificado como neutro neste regime.

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

- **Arquivo:** `ai-sentinel/tests/sample_trend_backtest.csv`
- **Periodo:** `2026-03-01T00:00:00Z` a `2026-03-01T19:00:00Z`
- **Ativo:** `BTCUSDT`
- **Timeframe:** candles sequenciais do arquivo de teste
- **Regime declarado antes da execucao:** tendencial favoravel

---

## 4. Resultados Comparativos

| Metrica                    | Com RiskFilter | Sem RiskFilter | Variacao |
| -------------------------- | -------------- | -------------- | -------- |
| max_drawdown_pct           | 0.0000         | 0.0000         | 0.0000% |
| net_profit                 | 2970.74628952  | 2970.74628952  | 0.0000% |
| discipline_ratio           | 0.0000         | 0.0000         | 0.0000 |
| capital_protected_estimate | 0.00000000     | 0.00000000     | 0.00000000 |

---

## 5. Analise

- O filtro nao alterou `max_drawdown_pct`, que permaneceu em `0.0000`.
- O resultado liquido permaneceu identico em `2970.74628952`.
- A disciplina operacional permaneceu em `0.0000`, sem intervencao do componente.
- A estimativa de capital protegido permaneceu em `0.00000000`.
- Neste regime, a estrategia nao entrou em processo de degradacao que exigisse intervencao de risco.

---

## 6. Conclusao Objetiva

- O `RiskFilter` **nao prejudicou** o comportamento do sistema neste regime.
- Como nao houve reducao de drawdown nem custo de retorno, a classificacao resultante e **NEUTRAL**.
- **Recomendacao:** manter o componente inalterado e avaliar sua contribuicao nos regimes em que ha pressao real sobre o capital.

---

## 7. Proximos Passos

1. Executar o regime lateral com ruido sob o mesmo protocolo.
2. Executar o regime de volatilidade extrema sob o mesmo protocolo.
3. Consolidar a serie historica sem reclassificacao de criterio.
