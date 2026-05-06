# Clean Room Study Policy - UNI IA

## Objetivo

Garantir que o desenvolvimento do sistema UNI IA seja tecnicamente independente, juridicamente seguro e arquiteturalmente proprio, mesmo quando inspirado por projetos open source.

## Principios

1. Estudo nao e derivacao.
2. Conceitos podem ser reaproveitados.
3. Codigo nao pode ser copiado.
4. Estrutura nao deve ser replicada de forma identificavel.
5. Implementacao deve sempre derivar de especificacao propria.

## Fluxo Obrigatorio

1. **Estudo**
   - Ler documentacao e codigo de projetos externos.
   - Registrar insights em `docs/research/`.
   - Nao copiar trechos de codigo.
2. **Especificacao Propria**
   - Criar documento em `docs/specs/`.
   - Descrever arquitetura com nomenclatura propria.
   - Definir contratos e responsabilidades internas.
3. **Implementacao**
   - Implementar do zero.
   - Referenciar apenas a especificacao interna.
   - Nao consultar codigo externo durante implementacao.
4. **Auditoria Interna**
   - Verificar se nomes sao proprios.
   - Verificar se contratos sao proprios.
   - Verificar se a estrutura nao constitui replica estrutural.

## Projetos Estudados

- Jesse (MIT)
- LEAN (Apache-2.0)
- Outros apenas como referencia arquitetural

## Regra de Ouro

O core da UNI IA e:

- state machine
- governanca
- risco
- auditoria
- execucao simulada
- backtest deterministico

Nenhum desses componentes deve ser baseado diretamente em codigo externo.

## Aplicacao no Repositorio

- Estudos comparativos devem ficar em `docs/research/`.
- Especificacoes internas devem ficar em `docs/specs/`.
- O codigo de `ai-sentinel/core/` e `ai-sentinel/adapters/` deve evoluir a partir das especificacoes internas, nao da leitura direta de projetos externos.
