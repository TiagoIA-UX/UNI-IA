/**
 * AI.JS — Motor de IA com Groq + Sistema de Aprendizado Progressivo
 * Modelos: llama-3.3-70b-versatile, mixtral-8x7b, gemma2-9b
 */

const AIEngine = (() => {
  let apiKey = '';
  let model = 'llama-3.3-70b-versatile';
  let signalHistory = [];
  let learningStats = { total: 0, hits: 0, misses: 0, accuracy: 0 };

  // ===== CONFIGURAÇÃO =====
  function setApiKey(key) { apiKey = key.trim(); }
  function setModel(m) { model = m; }
  function getApiKey() { return apiKey; }

  // ===== PROMPT SISTEMA =====
  function buildSystemPrompt() {
    return `Você é um sistema especialista em análise de mercados financeiros chamado Uni IA — desenvolvido para identificar sinais de compra e venda de alta confiabilidade.

Seu papel é analisar dados técnicos, padrões de candlestick e fatores externos simultaneamente, ponderando cada componente com inteligência contextual.

PRINCÍPIOS FUNDAMENTAIS:
1. Nunca confie em um único indicador isoladamente
2. O contexto externo pode invalidar padrões técnicos perfeitos
3. Nunca recomende operar em contexto de risco extremo sem stop loss
4. Seja preciso: dê zonas de entrada, stop e alvo com base no ATR
5. Priorize a preservação de capital antes do lucro
6. Identifique se o padrão é a favor ou contra a tendência dominante
7. Considere os algoritmos: identifique zonas de possível stop hunt
8. O timeframe determina a força e durabilidade do sinal

TIPOS DE SINAL PERMITIDOS:
- COMPRA FORTE: Confluência técnica + fundamentos + fatores externos positivos > 75%
- COMPRA: Confluência técnica + ao menos 1 fator externo positivo > 60%
- VENDA FORTE: Confluência técnica + fundamentos + fatores externos negativos > 75%
- VENDA: Confluência técnica + ao menos 1 fator externo negativo > 60%
- AGUARDAR: Confluência insuficiente, contexto adverso ou risco extremo

FORMATO DA RESPOSTA (JSON estrito):
{
  "signal": "COMPRA|COMPRA_FORTE|VENDA|VENDA_FORTE|AGUARDAR",
  "confidence": 0-100,
  "entry": "zona de preço de entrada",
  "stopLoss": "nível de stop loss",
  "takeProfit1": "primeiro alvo",
  "takeProfit2": "segundo alvo (opcional)",
  "riskReward": "relação risco/retorno ex: 1:2.5",
  "timeframeValidity": "ex: 2-4 horas",
  "reasoning": "raciocínio completo em 4-6 parágrafos",
  "keyFactors": ["fator 1", "fator 2", "fator 3"],
  "warnings": ["aviso 1", "aviso 2"],
  "alternatives": "cenário alternativo se o sinal falhar",
  "systemicRisk": 0-100,
  "recommendedSize": "% do capital recomendado para a operação"
}`;
  }

  // ===== PROMPT USER =====
  function buildUserPrompt(context) {
    const {
      asset, technicalDirection, technicalConfidence, trend,
      indicators, patterns, patternDirection, patternConfidence,
      externalScore, externalDirection, externalConfidence, riskLevel,
      breakdown, calendarRisks, quote
    } = context;

    let prompt = `## ANÁLISE SOLICITADA: ${asset}\n\n`;

    prompt += `### DADOS DE MERCADO\n`;
    if (quote) {
      prompt += `- Preço atual: ${quote.price?.toFixed ? quote.price.toFixed(4) : quote.price}\n`;
      prompt += `- Variação 24h: ${quote.change?.toFixed ? quote.change.toFixed(2) : quote.change}%\n`;
      if (quote.volume) prompt += `- Volume 24h: ${(quote.volume / 1e6).toFixed(2)}M\n`;
    }

    prompt += `\n### ANÁLISE TÉCNICA QUANTITATIVA\n`;
    prompt += `- Direção técnica: **${technicalDirection}** (Confiança: ${technicalConfidence}%)\n`;
    prompt += `- Tendência dominante: ${trend}\n`;
    if (indicators) {
      prompt += `- RSI(14): ${indicators.rsi?.toFixed(1)}\n`;
      prompt += `- MACD Histograma: ${indicators.macdHist?.toFixed(4)}\n`;
      prompt += `- Posição nas Bandas Bollinger: ${(indicators.bbPosition * 100)?.toFixed(1)}%\n`;
      prompt += `- ADX: ${indicators.adx?.toFixed(1)} (tendência ${indicators.adx > 25 ? 'FORTE' : 'FRACA/LATERAL'})\n`;
      prompt += `- Estocástico %K: ${indicators.stochK?.toFixed(1)}\n`;
    }

    prompt += `\n### PADRÕES DE CANDLESTICK DETECTADOS\n`;
    if (patterns && patterns.length > 0) {
      patterns.forEach(p => prompt += `- ${p}\n`);
      prompt += `- Direção dominante dos padrões: ${patternDirection} (${patternConfidence}%)\n`;
    } else {
      prompt += `- Nenhum padrão significativo nas últimas 5 velas\n`;
    }

    prompt += `\n### FATORES EXTERNOS (Score: ${externalScore?.toFixed(1)} | Direção: ${externalDirection})\n`;
    if (breakdown) {
      for (const [, v] of Object.entries(breakdown)) {
        prompt += `- ${v.label} [peso: ${v.weight}%]: ${v.score?.toFixed(1)} pts\n`;
      }
    }

    if (calendarRisks && calendarRisks.length > 0) {
      prompt += `\n### RISCOS DE CALENDÁRIO ATIVOS\n`;
      calendarRisks.forEach(r => prompt += `- ⚠️ ${r.event}: ${r.note}\n`);
    }

    prompt += `\n### NÍVEL DE RISCO SISTÊMICO: ${riskLevel?.toUpperCase()}\n`;

    prompt += `\n---\nCom base em TODOS os dados acima, gere o sinal de análise completo em JSON estrito conforme o formato do sistema. Seja preciso, objetivo e contextualizado. Leve em conta os fatores externos como modificadores de peso dos sinais técnicos.`;

    return prompt;
  }

  // ===== CHAMAR GROQ API =====
  async function callGroq(context) {
    if (!apiKey) throw new Error('API Key da Groq não configurada');

    const payload = {
      model,
      messages: [
        { role: 'system', content: buildSystemPrompt() },
        { role: 'user', content: buildUserPrompt(context) }
      ],
      temperature: 0.2,
      max_tokens: 1500,
      response_format: { type: 'json_object' },
    };

    const response = await fetch('https://api.groq.com/openai/v1/chat/completions', {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${apiKey}`,
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(payload),
    });

    if (!response.ok) {
      const err = await response.json().catch(() => ({}));
      throw new Error(err.error?.message || `Groq API error ${response.status}`);
    }

    const data = await response.json();
    const content = data.choices?.[0]?.message?.content;
    if (!content) throw new Error('Resposta vazia da Groq');

    try {
      return JSON.parse(content);
    } catch {
      // Tentar extrair JSON inline
      const match = content.match(/\{[\s\S]*\}/);
      if (match) return JSON.parse(match[0]);
      throw new Error('Falha ao parsear JSON da IA');
    }
  }

  // ===== ANÁLISE SEM IA (regras determinísticas) =====
  function analyzeWithRules(context) {
    const {
      technicalDirection, technicalConfidence,
      externalScore, externalDirection,
      patternDirection, patternConfidence,
      riskLevel, indicators, quote
    } = context;

    // Pesos compostos
    let techWeight = 0.45;
    let extWeight = 0.35;
    let patWeight = 0.20;

    let bullScore = 0;
    let bearScore = 0;

    // Técnico
    if (technicalDirection === 'COMPRA') bullScore += techWeight * (technicalConfidence / 100);
    else if (technicalDirection === 'VENDA') bearScore += techWeight * (technicalConfidence / 100);

    // Externo
    if (externalDirection === 'bullish') bullScore += extWeight * (externalConfidence / 100);
    else if (externalDirection === 'bearish') bearScore += extWeight * (externalConfidence / 100);

    // Padrões
    if (patternDirection === 'compra') bullScore += patWeight * (patternConfidence / 100);
    else if (patternDirection === 'venda') bearScore += patWeight * (patternConfidence / 100);

    const total = bullScore + bearScore;
    const confidence = total > 0 ? Math.max(bullScore, bearScore) / total : 0.5;
    const dir = bullScore > bearScore ? 'COMPRA' : bearScore > bullScore ? 'VENDA' : 'AGUARDAR';

    // Reduzir confiança em risco extremo
    let adjustedConf = Math.round(confidence * 100);
    if (riskLevel === 'extremo') adjustedConf = Math.round(adjustedConf * 0.7);
    if (riskLevel === 'alto') adjustedConf = Math.round(adjustedConf * 0.85);

    const price = quote?.price || 0;
    const atr = indicators?.atr || price * 0.02;

    return {
      signal: adjustedConf >= 70 ? `${dir}_FORTE` : adjustedConf >= 55 ? dir : 'AGUARDAR',
      confidence: adjustedConf,
      entry: `${(price).toFixed(4)}`,
      stopLoss: dir === 'COMPRA' ? `${(price - atr * 1.5).toFixed(4)}` : `${(price + atr * 1.5).toFixed(4)}`,
      takeProfit1: dir === 'COMPRA' ? `${(price + atr * 2.5).toFixed(4)}` : `${(price - atr * 2.5).toFixed(4)}`,
      takeProfit2: dir === 'COMPRA' ? `${(price + atr * 4).toFixed(4)}` : `${(price - atr * 4).toFixed(4)}`,
      riskReward: '1:2.5',
      timeframeValidity: '2-6 horas',
      reasoning: `Análise gerada por regras determinísticas. Técnico: ${technicalDirection} (${technicalConfidence}%). Externo: ${externalDirection} (score ${externalScore?.toFixed(1)}). Padrões: ${patternDirection} (${patternConfidence}%).`,
      keyFactors: [
        `Direção técnica: ${technicalDirection}`,
        `Fatores externos: ${externalDirection}`,
        `Padrões detectados: ${patternDirection}`,
      ],
      warnings: riskLevel !== 'baixo' ? [`Nível de risco sistêmico: ${riskLevel}`] : [],
      alternatives: 'Se o sinal falhar, aguarde nova confluência em timeframe maior',
      systemicRisk: riskLevel === 'extremo' ? 85 : riskLevel === 'alto' ? 65 : riskLevel === 'moderado' ? 40 : 20,
      recommendedSize: adjustedConf >= 75 ? '2%' : adjustedConf >= 65 ? '1.5%' : '1%',
      source: 'regras',
    };
  }

  // ===== ANÁLISE COMPLETA =====
  async function analyze(context, useAI = true) {
    let result;
    let source = 'regras';

    if (useAI && apiKey) {
      try {
        result = await callGroq(context);
        result.source = 'groq';
        source = 'groq';
      } catch (err) {
        console.warn('Groq falhou, usando regras:', err.message);
        result = analyzeWithRules(context);
      }
    } else {
      result = analyzeWithRules(context);
    }

    // Registrar no histórico
    const entry = {
      id: Date.now(),
      timestamp: new Date().toISOString(),
      asset: context.asset,
      signal: result.signal,
      confidence: result.confidence,
      entry: result.entry,
      stopLoss: result.stopLoss,
      takeProfit1: result.takeProfit1,
      source,
      outcome: null, // Será preenchido depois
    };
    signalHistory.unshift(entry);
    if (signalHistory.length > 200) signalHistory.pop();
    saveHistory();

    return { ...result, historyId: entry.id };
  }

  // ===== REGISTRAR RESULTADO =====
  function recordOutcome(historyId, outcome, exitPrice) {
    const entry = signalHistory.find(e => e.id === historyId);
    if (!entry) return;
    entry.outcome = outcome;
    entry.exitPrice = exitPrice;

    // Recalcular stats
    const resolved = signalHistory.filter(e => e.outcome !== null);
    learningStats.total = resolved.length;
    learningStats.hits = resolved.filter(e => e.outcome === 'acerto').length;
    learningStats.misses = resolved.filter(e => e.outcome === 'erro').length;
    learningStats.accuracy = learningStats.total > 0
      ? Math.round((learningStats.hits / learningStats.total) * 100)
      : 0;

    saveHistory();
    return learningStats;
  }

  // ===== PERSISTÊNCIA =====
  function saveHistory() {
    try {
      localStorage.setItem('uniia_history', JSON.stringify(signalHistory));
      localStorage.setItem('uniia_stats', JSON.stringify(learningStats));
    } catch { /* storage cheio */ }
  }

  function loadHistory() {
    try {
      const h = localStorage.getItem('uniia_history');
      const s = localStorage.getItem('uniia_stats');
      if (h) signalHistory = JSON.parse(h);
      if (s) learningStats = JSON.parse(s);
    } catch { /* sem storage */ }
  }

  function getHistory() { return signalHistory; }
  function getStats() { return learningStats; }

  // Inicializar
  loadHistory();

  return { setApiKey, setModel, getApiKey, analyze, recordOutcome, getHistory, getStats };
})();
