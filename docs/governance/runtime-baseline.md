# Runtime Baseline - UNI IA

## Objetivo

Congelar o baseline minimo de runtime da UNI IA para reduzir variacao de ambiente, evitar falhas por dependencia implicita e manter execucao auditavel.

## Baseline Suportado

### Backend

- Python minimo suportado: `3.11.x`
- Python recomendado para homologacao local: `3.11.x`
- Gerenciador de pacotes: `pip`
- Dependencias instaladas a partir de `ai-sentinel/requirements.txt`

Observacao:

- ambientes Python `3.12+` podem exigir validacao adicional de compatibilidade antes de uso institucional
- o backend depende de `pydantic` com `pydantic_core` corretamente instalado no ambiente

### Frontend

- Node.js minimo suportado: `20.x`
- Node.js recomendado: `20.x LTS`
- Next.js baseline: `16.1.7`
- React baseline: `19.2.0`
- TypeScript baseline: `5.9.3`

## Sistema Operacional Testado

- Windows com PowerShell

Observacao:

- outros ambientes podem ser usados, mas so devem ser promovidos a baseline apos validacao formal de build, testes e CLI

## Estrategia de Versionamento

- o baseline institucional privilegia previsibilidade sobre atualizacao automatica agressiva
- upgrades de runtime devem ocorrer por revisao deliberada, nao por drift do ambiente
- alteracoes de major version exigem revalidacao de:
  - suite de testes
  - backtest CLI
  - build do frontend
  - warnings e deprecations criticos

## Politica de Dependencias

- ranges existentes podem permanecer durante fase de estabilizacao, desde que o ambiente homologado seja registrado
- qualquer dependencia critica quebrada em ambiente local invalida o baseline ate correção ou ajuste documental
- dependencias transientes obrigatorias, como `pydantic_core`, devem ser verificadas explicitamente em ambientes novos

## Politica de Update

1. validar necessidade operacional ou de seguranca
2. atualizar em branch dedicada de hardening
3. executar testes e build completos
4. registrar novo baseline documental se a mudanca alterar o chao suportado

## Regras Institucionais

- sem warning critico ignorado no baseline ativo
- sem dependencia faltante em ambiente considerado homologado
- sem divergencia entre runtime documentado e runtime efetivamente usado em validacao
