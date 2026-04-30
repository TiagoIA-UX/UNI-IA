# Relatório Funcional do Coptrader UNI IA

## Visão geral

O coptrader da UNI IA funciona como uma mesa privada assistida por IA.
Ele não toma decisão apenas por um indicador isolado. Ele cruza múltiplas fontes de contexto e transforma isso em um alerta operacional.

Hoje, o fluxo validado é:

1. receber o ativo para análise;
2. analisar contexto macro, volume, gráfico, fundamentos, notícias e sentimento;
3. consolidar tudo em um score e uma classificação final;
4. gerar um alerta operacional;
5. colocar a operação em fila de aprovação manual quando estiver em live;
6. só enviar ordem real após aprovação da mesa.

## O que ele analisa

O sistema usa os seguintes blocos de análise:

1. Macro: ambiente de risco e contexto geral do mercado.
2. Tendência e volume: aumento ou queda de interesse no ativo.
3. Técnico: leitura de preço e múltiplos tempos gráficos.
4. Fundamentalista: leitura de fundamentos quando aplicável.
5. Notícias: manchetes e fatos recentes do mercado.
6. Sentimento: tom emocional e viés das notícias coletadas.

Essas leituras são consolidadas em um único alerta final.

## O que o sistema entrega

Ao final da análise, o sistema entrega:

1. ativo analisado;
2. score de confiança operacional;
3. classificação do cenário;
4. explicação humana do racional;
5. lista das fontes que sustentaram a decisão;
6. eventual alerta de reversão de posição.

As classificações hoje seguem esta lógica:

1. OPORTUNIDADE: cenário elegível para mesa.
2. ATENÇÃO: cenário intermediário, sem execução.
3. RISCO: cenário adverso ou não elegível.

## Como a execução funciona

O coptrader não dispara ordem automaticamente só porque existe um sinal.

Fluxo operacional atual:

1. o sistema gera o alerta;
2. a mesa valida as regras mínimas;
3. se o modo estiver em live com aprovação manual, a operação vira `pending_approval`;
4. somente depois de uma aprovação explícita a ordem segue para a Bybit.

Isso reduz risco operacional e mantém governança humana antes da execução.

## O que já foi validado no ambiente atual

Foi validado que:

1. a Bybit responde autenticada com sucesso;
2. o broker está pronto para execução;
3. a mesa está em `live` com `manual_approval=true`;
4. o endpoint de análise gerou um alerta real para PETR4;
5. esse alerta caiu corretamente em `pending_approval`.

Resumo da situação atual:

1. o sistema já analisa e gera sinal real;
2. o sistema já prepara a execução;
3. a ordem ainda depende de aprovação manual;
4. o Telegram ainda precisa de validação operacional completa de envio.

## O que ele não faz ainda, do jeito atual

Hoje o coptrader ainda não está modelado como:

1. um alarme visual desenhado dentro do gráfico;
2. um sistema nativo de gatilho por preço exato do tipo "se bater em X, comprar";
3. um painel de performance estatística consolidada com win rate auditado.

Hoje ele é mais correto de descrever como:

1. análise multiagente;
2. geração de alerta operacional;
3. fila de execução controlada;
4. integração com broker para envio após aprovação.

## Sobre o score

O score atual não deve ser interpretado como garantia matemática de acerto.

O score representa a confiança operacional do sistema com base na convergência dos agentes.

Na prática:

1. score alto = maior convergência dos sinais analisados;
2. score baixo = menor convicção operacional;
3. isso não substitui estatística auditada de performance histórica.

## Onde o alerta aparece hoje

Hoje o alerta aparece principalmente em:

1. resposta da API;
2. fila da mesa privada;
3. integração de notificação, quando o Telegram estiver totalmente operacional.

Portanto, o comportamento atual é mais próximo de uma central de decisão e execução do que de um simples aviso visual dentro do gráfico.

## Modelo de operação atual

Em termos simples, o funcionamento hoje é:

1. pedir a análise do ativo;
2. receber um score e um parecer consolidado;
3. se houver oportunidade real, a mesa registra a operação como pendente;
4. um operador humano aprova;
5. a ordem é enviada ao broker.

## Próxima evolução natural do produto

Os próximos avanços mais naturais seriam:

1. alerta visual no gráfico;
2. gatilhos por faixa de preço;
3. stop, alvo e invalidação estruturados;
4. painel de histórico de sinais e taxa real de acerto;
5. distribuição automática por Telegram e painel interno.