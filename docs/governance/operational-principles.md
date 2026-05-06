# Operational Principles Policy - UNI IA

## Objetivo

Definir os principios operacionais obrigatorios da UNI IA para garantir que o sistema evolua com governanca, auditabilidade e controle institucional.

Esta policy existe para impedir:

- comportamento silencioso
- fallback operacional implicito
- placeholder em ambiente produtivo
- execucao sem validacao formal
- ambiguidade de estado

## Tese Operacional

Na UNI IA, confianca nao nasce de conveniencia.
Confianca nasce de estado explicito, validacao formal e falha observavel.

Regra central:

> Se o sistema nao consegue explicar o proprio estado, ele nao esta pronto para operar.

## Principios Obrigatorios

### 1. Zero Comportamento Silencioso

Nenhum fluxo relevante pode falhar, degradar ou alterar comportamento sem gerar evidencia observavel.

Aplicacoes praticas:

- toda decisao relevante deve produzir log, estado ou artefato auditavel
- falhas de validacao devem ser explicitadas
- bloqueios de execucao devem deixar rastreabilidade
- alteracoes de modo, status e risco devem ser verificaveis

Violacoes desta regra incluem:

- `except` que suprime erro sem registrar impacto
- retorno neutro quando o sistema deveria falhar explicitamente
- degradacao silenciosa de integracao, risco ou auditoria

### 2. Zero Fallback Operacional

Em ambiente operacional, fallback invisivel e proibido.

Aplicacoes praticas:

- se uma dependencia critica nao estiver pronta, o sistema deve bloquear ou falhar de forma declarada
- integracoes criticas nao podem trocar para comportamento alternativo sem politica explicita
- ausencia de configuracao obrigatoria invalida execucao segura

Violacoes desta regra incluem:

- usar valor alternativo nao homologado sem sinalizacao
- executar fluxo parcial como se fosse fluxo valido
- substituir dependencia critica por mock, placeholder ou comportamento default em producao

### 3. Zero Placeholder em Producao

Qualquer valor ficticio invalida a confianca do sistema.

Aplicacoes praticas:

- exemplos, seeds, IDs fake e credenciais de exemplo nao podem participar de fluxo operacional
- dataset de teste e estrategia de amostra devem permanecer segregados de producao
- configuracoes obrigatorias devem ser reais, verificadas e consistentes com o ambiente

Violacoes desta regra incluem:

- uso de valores dummy em execucao live ou homologacao declarada
- resposta institucional baseada em dado sintetico sem marcacao explicita
- sinal, score ou estado fabricado para “manter o fluxo funcionando”

### 4. Zero Execucao sem Validacao

Nenhuma execucao pode atravessar o sistema sem gate formal.

Aplicacoes praticas:

- todo fluxo operacional deve respeitar validacao de modo e status
- backtest exige contratos formais de entrada, risco e exportacao
- runtime live exige validacao de ambiente, auditoria e governanca antes da execucao
- experimentos comparativos exigem protocolo congelado antes da rodada

Violacoes desta regra incluem:

- bypass de `RiskFilter`
- criacao de pendencia ou execucao live sem validacao institucional
- alteracao de criterio experimental apos ver resultado

### 5. Zero Ambiguidade de Estado

Estado institucional precisa ser determinavel em qualquer momento relevante.

Aplicacoes praticas:

- `mode`, `status`, bloqueios e razoes devem ser explicitos
- toda decisao precisa indicar origem, regra aplicada e consequencia operacional
- series de experimento exigem hashes, runner e estrategia congelados
- artefatos devem permitir reconstituir o contexto minimo da execucao

Violacoes desta regra incluem:

- estado implicito sem campo formal correspondente
- decisao sem motivo rastreavel
- ambiente homologado sem baseline declarado
- serie experimental sem integridade verificavel

## Regras de Implementacao

### Regras para Codigo

- falhas criticas devem falhar de forma explicita
- dependencias criticas devem ser verificadas antes do uso
- logs e artefatos devem refletir a verdade operacional, nao uma narrativa conveniente
- novos componentes devem declarar contrato, limites e criterio de bloqueio

### Regras para Backtest

- mesma serie exige mesmo runner, mesma estrategia, mesmo dataset e mesmo criterio
- qualquer mudanca de hash abre nova serie
- governanca deve ser mensuravel e exportavel
- resultado sem protocolo congelado nao conta como evidencia institucional

### Regras para Runtime

- baseline de runtime deve permanecer documentado
- checklist de ambiente deve ser executavel
- warning critico nao pode ser tratado como detalhe cosmetico
- ambiente quebrado invalida homologacao

### Regras para Documentacao

- spec antecede evolucao estrutural
- research registra evidencia e comparacao, nao entusiasmo
- governance define restricao operacional real, nao principio decorativo
- README e landing nao podem prometer o que o sistema nao consegue sustentar por codigo e artefatos

## Criterio de Aceitacao de Mudanca

Uma mudanca so e institucionalmente aceitavel se:

1. nao introduzir comportamento silencioso
2. nao depender de fallback operacional implicito
3. nao inserir placeholder em fluxo real
4. respeitar gates de validacao existentes
5. manter estado auditavel e nao ambiguo

Se qualquer item acima falhar, a mudanca deve ser bloqueada ou reclassificada como nao pronta para operacao.

## Criterio de Escalacao

Mudancas devem ser escaladas para revisao documental quando:

- alterarem contratos de risco, execucao ou estado
- criarem nova dependencia critica
- modificarem criterio experimental congelado
- ampliarem superficie live sem evidencia previa
- reduzirem observabilidade operacional

## Aplicacao no Repositorio

Esta policy se aplica especialmente a:

- `ai-sentinel/core/`
- `ai-sentinel/api/`
- `ai-sentinel/tests/`
- `docs/specs/`
- `docs/research/`
- `docs/governance/`
- `zairyx-blog/` quando houver afirmacao institucional de produto

## Relacao com Outras Policies

Esta policy complementa:

- `docs/governance/clean-room-study.md`
- `docs/governance/runtime-baseline.md`
- `docs/governance/environment-checklist.md`

## Regra Final

Na UNI IA, conveniencia nunca tem precedencia sobre clareza operacional.

Se houver conflito entre “continuar rodando” e “continuar confiavel”, a prioridade institucional e continuar confiavel.
