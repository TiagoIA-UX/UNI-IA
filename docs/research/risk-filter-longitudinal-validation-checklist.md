# Risk Filter - Longitudinal Validation Checklist

## Objetivo

Transformar os acceptance gates da fase longitudinal em checklist operacional executavel, com criterio de bloqueio e decisao final explicitos.

## 1. Preparacao de Dataset

- [ ] Dataset cobre >= `N` anos ou >= `M` ciclos completos de volatilidade
- [ ] Inclusao de periodos de alta tendencia
- [ ] Inclusao de periodos de lateralidade
- [ ] Inclusao de periodos de choque de volatilidade
- [ ] Inclusao de periodos de compressao extrema
- [ ] Dados auditados quanto a integridade e consistencia

Critério de bloqueio:

- dataset incompleto invalida a rodada
- dataset com hash divergente da serie declarada invalida a rodada

## 2. Execucao Rolling (6M)

Para cada janela:

- [ ] Calcular drawdown baseline
- [ ] Calcular drawdown com filtro
- [ ] Registrar delta de drawdown
- [ ] Classificar regime
- [ ] Classificar resultado como `PROTECTIVE`, `NEUTRAL` ou `DETRIMENTAL`

Ao final:

- [ ] Media de reducao de drawdown >= `50%` em regimes degradados
- [ ] >= `70%` das janelas degradadas classificadas como `PROTECTIVE`
- [ ] Nenhuma janela com agravamento de drawdown superior a `10%`

Critério de bloqueio:

- falha em qualquer condicao acima gera flag vermelha para a fase

## 3. Neutralidade em Regime Favoravel

- [ ] Impacto medio no retorno liquido dentro de `[-5%, +5%]`
- [ ] Frequencia `DETRIMENTAL` < `5%`
- [ ] Teste estatistico de diferenca nao significativo quando aplicavel

Critério de bloqueio:

- erosao recorrente de upside invalida a tese de limitador estrutural de dano

## 4. Teste de Friccao

Executar simulacoes com:

- [ ] Slippage incremental
- [ ] Spread variavel
- [ ] Execucao imperfeita
- [ ] Latencia simulada

Resultado esperado:

- [ ] >= `80%` da reducao de drawdown preservada

Critério de bloqueio:

- efeito abaixo de `80%` invalida robustez sob friccao

## 5. Falha Parcial

Simular:

- [ ] Ativacao tardia
- [ ] Desativacao prematura
- [ ] Dados corrompidos
- [ ] Spike falso

Validar:

- [ ] Nenhum cenario amplifica risco estrutural
- [ ] Nenhum drawdown > baseline + `15%`

Critério de bloqueio:

- qualquer cenario amplificador de risco invalida robustez operacional

## 6. Decisao Final

- [ ] Todos os gates passaram
- [ ] Falhas documentadas
- [ ] Iteracoes registradas
- [ ] Versao do filtro congelada

Classificacao final:

- `ROBUSTEZ ACEITA` somente se todos os gates forem aprovados
- caso contrario, `ROBUSTEZ NAO ACEITA`

## 7. Regras de Execucao

- cada rodada deve registrar hash do dataset
- cada rodada deve registrar hash do runner
- cada rodada deve registrar hash da estrategia-base
- qualquer mudanca de hash abre nova serie
- nenhum gate pode ser ajustado retroativamente para salvar conclusao

## 8. Relacao com o Overview

Este checklist operacional implementa o `risk-filter-validation-overview.md` como procedimento executavel.
O overview congela a tese.
O checklist executa a prova.
