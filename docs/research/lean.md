# Estudo Tecnico - LEAN

Licenca: Apache-2.0  
Objetivo do estudo: arquitetura orientada a evento e separacao de responsabilidades

## Pontos Observados

### Event-Driven Engine

- Separacao entre dados, execucao e portfolio

### Portfolio State

- Ledger consistente
- Metricas integradas

### Execution Model

- Simulacao com slippage e fee

## O que Aproveitar Conceitualmente

- Separacao broker / portfolio / execution
- Metricas calculadas ao final

## O que Nao Reproduzir

- Modelo exato de eventos
- Estrutura de namespaces
- Organizacao interna de engine

## Decisao Arquitetural UNI IA

- Manter engine sequencial deterministica
- Separar `execution_simulator`
- Manter `portfolio_state` proprio
