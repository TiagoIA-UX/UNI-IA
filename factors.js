/**
 * FACTORS.JS — Motor de fatores externos com pesos dinâmicos
 * Macro, Geopolítica, Sentimento, Fluxo Institucional, Algoritmos, Calendário
 */

const ExternalFactors = (() => {

  // ===== CALENDÁRIO ECONÔMICO (próximos eventos de alto impacto) =====
  const HIGH_IMPACT_EVENTS = [
    { name: 'FOMC — Decisão de Juros (Fed)', impact: 'muito_alto', frequency: 'bimestral', category: 'macro' },
    { name: 'CPI EUA — Inflação', impact: 'muito_alto', frequency: 'mensal', category: 'macro' },
    { name: 'NFP — Payroll EUA', impact: 'alto', frequency: 'mensal', category: 'macro' },
    { name: 'COPOM — Decisão SELIC', impact: 'muito_alto', frequency: 'bimestral', category: 'macro_br' },
    { name: 'IPCA — Inflação Brasil', impact: 'alto', frequency: 'mensal', category: 'macro_br' },
    { name: 'PIB EUA', impact: 'alto', frequency: 'trimestral', category: 'macro' },
    { name: 'PMI Industrial', impact: 'medio', frequency: 'mensal', category: 'macro' },
    { name: 'Resultado Bernanke/Powell (discurso)', impact: 'alto', frequency: 'variavel', category: 'macro' },
    { name: 'Resultado Trimestral S&P500', impact: 'alto', frequency: 'trimestral', category: 'fundamental' },
    { name: 'Resultado Trimestral IBOV', impact: 'alto', frequency: 'trimestral', category: 'fundamental_br' },
  ];

  // ===== PESOS PADRÃO POR CATEGORIA =====
  let weights = {
    macro_usa: 25,      // Fed, CPI, Payroll
    macro_br: 20,       // SELIC, IPCA, PIB BR
    geopolitico: 20,    // Guerras, sanções, eleições
    sentimento: 15,     // Fear & Greed, RSI mercado
    institucional: 15,  // Fluxo estrangeiro, COT
    algoritmos: 10,     // HFT, stop hunts
    noticias: 15,       // Eventos de notícias
    fundamentalista: 15 // P/L, ROE, DY
  };

  // Estado atual dos fatores (atualizado externamente)
  let currentFactors = buildDefaultFactors();

  function buildDefaultFactors() {
    return {
      macro_usa: {
        score: 0, // -100 a +100
        label: 'Macro EUA',
        items: [
          { name: 'Política Fed (juros)', value: 'neutro', score: 0, description: 'Fed mantém postura cautelosa' },
          { name: 'CPI (inflação)', value: 'neutro', score: 0, description: 'Inflação em linha com expectativa' },
          { name: 'Emprego (NFP)', value: 'neutro', score: 0, description: 'Mercado de trabalho estável' },
          { name: 'PIB EUA', value: 'neutro', score: 0, description: 'Crescimento moderado' },
        ]
      },
      macro_br: {
        score: 0,
        label: 'Macro Brasil',
        items: [
          { name: 'SELIC', value: 'neutro', score: 0, description: 'Taxa estável ou em revisão' },
          { name: 'IPCA (inflação BR)', value: 'neutro', score: 0, description: 'Inflação dentro da meta' },
          { name: 'Câmbio USD/BRL', value: 'neutro', score: 0, description: 'Dólar estável' },
          { name: 'Risco Fiscal', value: 'neutro', score: 0, description: 'Situação fiscal monitorada' },
        ]
      },
      geopolitico: {
        score: 0,
        label: 'Geopolítica',
        items: [
          { name: 'Conflitos Armados', value: 'neutro', score: 0, description: 'Sem escaladas recentes' },
          { name: 'Sanções Econômicas', value: 'neutro', score: 0, description: 'Sem novas sanções' },
          { name: 'Eleições/Política', value: 'neutro', score: 0, description: 'Ambiente político estável' },
          { name: 'Relações EUA-China', value: 'neutro', score: 0, description: 'Tensão moderada' },
        ]
      },
      sentimento: {
        score: 0,
        label: 'Sentimento',
        items: [
          { name: 'Fear & Greed Index', value: 'neutro', score: 0, description: 'Mercado em equilíbrio' },
          { name: 'Volume Geral', value: 'neutro', score: 0, description: 'Volume próximo da média' },
          { name: 'Posição Varejo (retail)', value: 'neutro', score: 0, description: 'Sem extremos detectados' },
          { name: 'Mídia/Redes Sociais', value: 'neutro', score: 0, description: 'Sentimento neutro' },
        ]
      },
      institucional: {
        score: 0,
        label: 'Fluxo Institucional',
        items: [
          { name: 'Fluxo Estrangeiro B3', value: 'neutro', score: 0, description: 'Fluxo externo equilibrado' },
          { name: 'Posição COT (futuros)', value: 'neutro', score: 0, description: 'Sem posições extremas' },
          { name: 'Holdings Institucionais', value: 'neutro', score: 0, description: 'Sem mudanças significativas' },
          { name: 'ETFs/Fundos entrada', value: 'neutro', score: 0, description: 'Captações normais' },
        ]
      },
      algoritmos: {
        score: 0,
        label: 'Ambiente Algorítmico',
        items: [
          { name: 'Risco de Stop Hunt', value: 'neutro', score: 0, description: 'Sem acúmulo anormal de stops' },
          { name: 'HFT Activity', value: 'neutro', score: 0, description: 'Atividade HFT normal' },
          { name: 'Liquidez do Livro', value: 'neutro', score: 0, description: 'Order book equilibrado' },
          { name: 'Correlação Mercados', value: 'neutro', score: 0, description: 'Correlações normais' },
        ]
      },
      noticias: {
        score: 0,
        label: 'Notícias e Eventos',
        items: []
      },
      fundamentalista: {
        score: 0,
        label: 'Análise Fundamentalista',
        items: [
          { name: 'P/L vs Setor', value: 'neutro', score: 0, description: 'Valuation neutro' },
          { name: 'ROE', value: 'neutro', score: 0, description: 'Retorno sobre patrimônio neutro' },
          { name: 'Dividend Yield', value: 'neutro', score: 0, description: 'Yield neutro' },
          { name: 'Dívida/EBITDA', value: 'neutro', score: 0, description: 'Alavancagem moderada' },
        ]
      }
    };
  }

  // ===== ATUALIZAR PESOS =====
  function setWeights(newWeights) {
    weights = { ...weights, ...newWeights };
  }

  // ===== ATUALIZAR FATOR =====
  function setFactor(category, itemIndex, value, score) {
    if (currentFactors[category] && currentFactors[category].items[itemIndex] !== undefined) {
      currentFactors[category].items[itemIndex].value = value;
      currentFactors[category].items[itemIndex].score = score;
      recalculateCategoryScore(category);
    }
  }

  function recalculateCategoryScore(category) {
    const items = currentFactors[category].items;
    if (items.length === 0) return;
    const avg = items.reduce((sum, item) => sum + item.score, 0) / items.length;
    currentFactors[category].score = avg;
  }

  // ===== INJETAR NOTÍCIAS =====
  function injectNews(newsList) {
    currentFactors.noticias.items = newsList.map(n => ({
      name: n.title.substring(0, 60),
      value: n.sentiment,
      score: n.sentiment === 'positive' ? 30 : n.sentiment === 'negative' ? -30 : 0,
      description: n.source,
    }));
    recalculateCategoryScore('noticias');
  }

  // ===== DETECTAR REGIME DE MERCADO =====
  function detectMarketRegime(candles) {
    if (!candles || candles.length < 20) return { regime: 'desconhecido', confidence: 0 };
    const closes = candles.map(c => c.close);
    const n = closes.length;
    const recent = closes.slice(-20);
    const std = standardDeviation(recent);
    const mean = recent.reduce((a, b) => a + b, 0) / recent.length;
    const cv = std / mean; // Coeficiente de variação

    // Detectar tendência
    const slope = linearSlope(recent);
    const slopeStrength = Math.abs(slope / mean);

    // Volume
    const volumes = candles.slice(-20).map(c => c.volume);
    const avgVol = volumes.reduce((a, b) => a + b, 0) / volumes.length;
    const recentVol = volumes.slice(-5).reduce((a, b) => a + b, 0) / 5;
    const volumeRatio = avgVol > 0 ? recentVol / avgVol : 1;

    let regime = 'lateral';
    let confidence = 50;

    if (slopeStrength > 0.005) {
      regime = slope > 0 ? 'tendencia_alta' : 'tendencia_baixa';
      confidence = Math.min(90, 50 + slopeStrength * 5000);
    } else if (cv > 0.03) {
      regime = 'volatil';
      confidence = Math.min(85, 50 + cv * 1000);
    } else {
      regime = 'lateral';
      confidence = Math.min(80, 50 + (1 - cv) * 100);
    }

    return { regime, confidence: Math.round(confidence), cv, slopeStrength, volumeRatio };
  }

  function standardDeviation(arr) {
    const mean = arr.reduce((a, b) => a + b, 0) / arr.length;
    return Math.sqrt(arr.reduce((sum, v) => sum + Math.pow(v - mean, 2), 0) / arr.length);
  }

  function linearSlope(arr) {
    const n = arr.length;
    const xMean = (n - 1) / 2;
    const yMean = arr.reduce((a, b) => a + b, 0) / n;
    let num = 0, den = 0;
    for (let i = 0; i < n; i++) {
      num += (i - xMean) * (arr[i] - yMean);
      den += Math.pow(i - xMean, 2);
    }
    return den === 0 ? 0 : num / den;
  }

  // ===== CALCULAR SCORE PONDERADO FINAL =====
  function calculateFinalScore() {
    const totalWeight = Object.keys(weights).reduce((sum, k) => sum + (weights[k] || 0), 0);
    if (totalWeight === 0) return { score: 0, direction: 'neutro', confidence: 50, breakdown: {} };

    let weightedScore = 0;
    const breakdown = {};

    for (const [cat, factor] of Object.entries(currentFactors)) {
      const w = (weights[cat] || 0) / totalWeight;
      const contribution = factor.score * w;
      weightedScore += contribution;
      breakdown[cat] = {
        label: factor.label,
        score: factor.score,
        weight: weights[cat] || 0,
        contribution: contribution,
      };
    }

    // Normalizar para 0-100
    const normalizedScore = (weightedScore + 100) / 2; // -100..+100 → 0..100
    const direction = weightedScore > 10 ? 'bullish' : weightedScore < -10 ? 'bearish' : 'neutro';
    const confidence = Math.min(95, 45 + Math.abs(weightedScore) * 0.4);

    return {
      score: weightedScore,
      normalizedScore,
      direction,
      confidence: Math.round(confidence),
      breakdown,
      riskLevel: calculateRiskLevel(weightedScore),
    };
  }

  function calculateRiskLevel(score) {
    const absScore = Math.abs(score);
    if (absScore > 60) return 'extremo';
    if (absScore > 40) return 'alto';
    if (absScore > 20) return 'moderado';
    return 'baixo';
  }

  // ===== GERAÇÃO AUTOMÁTICA DE CONTEXTO (baseado em dados disponíveis) =====
  function autoDetectContext(quote, candles, assetType) {
    const regime = detectMarketRegime(candles);

    // Ajusta baseado em contexto atual real
    if (quote) {
      const change = quote.change || 0;
      // Sentimento baseado em movimento de preço
      currentFactors.sentimento.items[0].score = change > 3 ? 60 : change < -3 ? -60 : change * 15;
      currentFactors.sentimento.items[1].score = regime.volumeRatio > 1.5 ? 40 : regime.volumeRatio < 0.6 ? -20 : 0;
      recalculateCategoryScore('sentimento');
    }

    // Ajusta algorítmicos baseado em regime
    if (regime.regime === 'volatil') {
      currentFactors.algoritmos.items[0].score = -30; // Risco de stop hunt maior
      currentFactors.algoritmos.items[2].score = -20; // Liquidez menor
    } else if (regime.regime === 'tendencia_alta') {
      currentFactors.algoritmos.items[2].score = 30; // Liquidez melhor
    }
    recalculateCategoryScore('algoritmos');

    return regime;
  }

  // ===== CALENDÁRIO DE ALTO RISCO =====
  function getCalendarRisk() {
    // Simula datas de alto risco baseado no dia da semana e hora
    const now = new Date();
    const dayOfWeek = now.getDay(); // 0=Dom, 5=Sex
    const hour = now.getHours();
    const risks = [];

    if (dayOfWeek === 5) risks.push({ event: 'Fechamento semanal', level: 'alto', note: 'Sexta-feira: manipulação de fechamento comum' });
    if (hour >= 9 && hour <= 10) risks.push({ event: 'Abertura de mercado', level: 'alto', note: 'Abertura: volatilidade elevada' });
    if (hour >= 14 && hour <= 15) risks.push({ event: 'Mercado EUA abrindo', level: 'alto', note: 'Abertura NYSE: impacto global' });
    if (dayOfWeek === 1) risks.push({ event: 'Segunda-feira', level: 'medio', note: 'Gap pós-weekend comum' });
    if (dayOfWeek === 0 || dayOfWeek === 6) risks.push({ event: 'Fim de semana', level: 'medio', note: 'Mercado fechado — risco de gap' });

    return risks;
  }

  // ===== CRIAR CONTEXTO COMPLETO PARA IA =====
  function buildAIContext(assetKey, techAnalysis, patternResult, quote) {
    const finalScore = calculateFinalScore();
    const calRisk = getCalendarRisk();

    return {
      asset: assetKey,
      technicalDirection: techAnalysis?.direction,
      technicalConfidence: techAnalysis?.confidence,
      technicalBullScore: techAnalysis?.bullScore,
      technicalBearScore: techAnalysis?.bearScore,
      trend: techAnalysis?.trend,
      indicators: {
        rsi: techAnalysis?.indicators?.rsi,
        macdHist: techAnalysis?.indicators?.macd?.hist,
        bbPosition: techAnalysis?.indicators?.bb?.position,
        adx: techAnalysis?.indicators?.adx,
        stochK: techAnalysis?.indicators?.stoch?.k,
      },
      patterns: patternResult?.patterns?.map(p => p.name + ' (' + p.direction + ')') || [],
      patternDirection: patternResult?.dominant,
      patternConfidence: patternResult?.confidence,
      externalScore: finalScore.score,
      externalDirection: finalScore.direction,
      externalConfidence: finalScore.confidence,
      riskLevel: finalScore.riskLevel,
      breakdown: finalScore.breakdown,
      calendarRisks: calRisk,
      quote,
    };
  }

  function getFactors() { return currentFactors; }
  function getWeights() { return weights; }
  function resetFactors() { currentFactors = buildDefaultFactors(); }

  return {
    setWeights, setFactor, injectNews, calculateFinalScore,
    autoDetectContext, detectMarketRegime, getCalendarRisk,
    buildAIContext, getFactors, getWeights, resetFactors,
    HIGH_IMPACT_EVENTS,
  };
})();
