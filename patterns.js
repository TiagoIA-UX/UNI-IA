/**
 * PATTERNS.JS — Reconhecimento de 30+ padrões de candlestick
 * Com contexto de tendência e pontuação de confiabilidade
 */

const CandlePatterns = (() => {

  // ===== HELPERS =====
  const body = c => Math.abs(c.close - c.open);
  const upperShadow = c => c.high - Math.max(c.open, c.close);
  const lowerShadow = c => Math.min(c.open, c.close) - c.low;
  const range = c => c.high - c.low;
  const isBull = c => c.close > c.open;
  const isBear = c => c.close < c.open;
  const midpoint = c => (c.open + c.close) / 2;

  // ===== PADRÕES DE 1 VELA =====
  function doji(c) {
    const b = body(c);
    const r = range(c);
    return r > 0 && b / r < 0.1;
  }

  function dragonfly(c) {
    const b = body(c);
    const r = range(c);
    const ls = lowerShadow(c);
    const us = upperShadow(c);
    return b / r < 0.1 && ls > r * 0.6 && us < r * 0.1;
  }

  function gravestone(c) {
    const b = body(c);
    const r = range(c);
    const ls = lowerShadow(c);
    const us = upperShadow(c);
    return b / r < 0.1 && us > r * 0.6 && ls < r * 0.1;
  }

  function hammer(c, trend) {
    const b = body(c);
    const r = range(c);
    const ls = lowerShadow(c);
    const us = upperShadow(c);
    return trend === 'baixa' && b > 0 && ls >= b * 2 && us <= b * 0.5 && b / r > 0.1;
  }

  function hangingMan(c, trend) {
    const b = body(c);
    const r = range(c);
    const ls = lowerShadow(c);
    const us = upperShadow(c);
    return trend === 'alta' && b > 0 && ls >= b * 2 && us <= b * 0.5 && b / r > 0.1;
  }

  function invertedHammer(c, trend) {
    const b = body(c);
    const r = range(c);
    const ls = lowerShadow(c);
    const us = upperShadow(c);
    return trend === 'baixa' && b > 0 && us >= b * 2 && ls <= b * 0.5;
  }

  function shootingStar(c, trend) {
    const b = body(c);
    const r = range(c);
    const us = upperShadow(c);
    const ls = lowerShadow(c);
    return trend === 'alta' && b > 0 && us >= b * 2 && ls <= b * 0.5 && isBear(c);
  }

  function marubozu(c) {
    const b = body(c);
    const r = range(c);
    return b / r > 0.92;
  }

  function spinningTop(c) {
    const b = body(c);
    const r = range(c);
    const us = upperShadow(c);
    const ls = lowerShadow(c);
    return b / r < 0.35 && us > b * 0.5 && ls > b * 0.5;
  }

  // ===== PADRÕES DE 2 VELAS =====
  function engulfing(prev, curr) {
    const bullEngulf = isBear(prev) && isBull(curr) &&
      curr.open <= prev.close && curr.close >= prev.open &&
      body(curr) > body(prev) * 1.1;
    const bearEngulf = isBull(prev) && isBear(curr) &&
      curr.open >= prev.close && curr.close <= prev.open &&
      body(curr) > body(prev) * 1.1;
    return { bullEngulf, bearEngulf };
  }

  function harami(prev, curr) {
    const bullHarami = isBear(prev) && isBull(curr) &&
      curr.open > prev.close && curr.close < prev.open &&
      body(curr) < body(prev) * 0.5;
    const bearHarami = isBull(prev) && isBear(curr) &&
      curr.open < prev.close && curr.close > prev.open &&
      body(curr) < body(prev) * 0.5;
    return { bullHarami, bearHarami };
  }

  function harami_cross(prev, curr) {
    return (isBear(prev) || isBull(prev)) &&
      doji(curr) &&
      curr.high < Math.max(prev.open, prev.close) &&
      curr.low > Math.min(prev.open, prev.close);
  }

  function piercing(prev, curr) {
    return isBear(prev) && isBull(curr) &&
      curr.open < prev.low &&
      curr.close > midpoint(prev) &&
      curr.close < prev.open;
  }

  function darkCloudCover(prev, curr) {
    return isBull(prev) && isBear(curr) &&
      curr.open > prev.high &&
      curr.close < midpoint(prev) &&
      curr.close > prev.open;
  }

  function tweezerTop(prev, curr) {
    return isBull(prev) && isBear(curr) &&
      Math.abs(prev.high - curr.high) / prev.high < 0.002;
  }

  function tweezerBottom(prev, curr) {
    return isBear(prev) && isBull(curr) &&
      Math.abs(prev.low - curr.low) / prev.low < 0.002;
  }

  // ===== PADRÕES DE 3 VELAS =====
  function morningstar(c1, c2, c3) {
    return isBear(c1) &&
      body(c2) < body(c1) * 0.35 &&
      c2.high < c1.close &&
      isBull(c3) &&
      c3.close > midpoint(c1) &&
      body(c3) > body(c1) * 0.5;
  }

  function eveningstar(c1, c2, c3) {
    return isBull(c1) &&
      body(c2) < body(c1) * 0.35 &&
      c2.low > c1.close &&
      isBear(c3) &&
      c3.close < midpoint(c1) &&
      body(c3) > body(c1) * 0.5;
  }

  function threeWhiteSoldiers(c1, c2, c3) {
    return isBull(c1) && isBull(c2) && isBull(c3) &&
      c2.open > c1.open && c2.close > c1.close &&
      c3.open > c2.open && c3.close > c2.close &&
      lowerShadow(c1) < body(c1) * 0.3 &&
      lowerShadow(c2) < body(c2) * 0.3 &&
      lowerShadow(c3) < body(c3) * 0.3;
  }

  function threeBlackCrows(c1, c2, c3) {
    return isBear(c1) && isBear(c2) && isBear(c3) &&
      c2.open < c1.open && c2.close < c1.close &&
      c3.open < c2.open && c3.close < c2.close &&
      upperShadow(c1) < body(c1) * 0.3 &&
      upperShadow(c2) < body(c2) * 0.3 &&
      upperShadow(c3) < body(c3) * 0.3;
  }

  function threeInsideUp(c1, c2, c3) {
    return isBear(c1) &&
      isBull(c2) && c2.open > c1.close && c2.close < c1.open &&
      isBull(c3) && c3.close > c1.open;
  }

  function threeInsideDown(c1, c2, c3) {
    return isBull(c1) &&
      isBear(c2) && c2.open < c1.close && c2.close > c1.open &&
      isBear(c3) && c3.close < c1.open;
  }

  function abandonedBaby(c1, c2, c3, bullish) {
    if (bullish) {
      return isBear(c1) && doji(c2) && isBull(c3) &&
        c2.high < c1.low && c3.low > c2.high;
    }
    return isBull(c1) && doji(c2) && isBear(c3) &&
      c2.low > c1.high && c3.high < c2.low;
  }

  function risingThreeMethods(c1, c2, c3, c4, c5) {
    if (!c5) return false;
    return isBull(c1) && isBear(c2) && isBear(c3) && isBear(c4) && isBull(c5) &&
      c2.close > c1.open && c4.close > c1.open &&
      c5.close > c1.close &&
      body(c1) > body(c2) * 2;
  }

  function fallingThreeMethods(c1, c2, c3, c4, c5) {
    if (!c5) return false;
    return isBear(c1) && isBull(c2) && isBull(c3) && isBull(c4) && isBear(c5) &&
      c2.close < c1.open && c4.close < c1.open &&
      c5.close < c1.close &&
      body(c1) > body(c2) * 2;
  }

  // ===== ANÁLISE COMPLETA DE PADRÕES =====
  function detectAll(candles, trend = 'lateral') {
    const n = candles.length;
    if (n < 5) return [];
    const found = [];
    const last = candles[n - 1];
    const prev = candles[n - 2];
    const prev2 = candles[n - 3];
    const prev3 = candles[n - 4];
    const prev4 = candles[n - 5];

    // === 1 VELA ===
    if (doji(last)) {
      found.push({ name: 'Doji', type: 'reversão', direction: 'neutro', reliability: 65, emoji: '🔄', candles: 1, description: 'Indecisão total do mercado — possível reversão' });
    }
    if (dragonfly(last)) {
      found.push({ name: 'Doji Libélula', type: 'reversão alta', direction: 'compra', reliability: 72, emoji: '🐉', candles: 1, description: 'Forte rejeição de baixas — compradores assumiram' });
    }
    if (gravestone(last)) {
      found.push({ name: 'Doji Lápide', type: 'reversão baixa', direction: 'venda', reliability: 72, emoji: '🪦', candles: 1, description: 'Forte rejeição de altas — vendedores assumiram' });
    }
    if (hammer(last, trend)) {
      found.push({ name: 'Martelo', type: 'reversão alta', direction: 'compra', reliability: 78, emoji: '🔨', candles: 1, description: 'Padrão de reversão após tendência de baixa' });
    }
    if (hangingMan(last, trend)) {
      found.push({ name: 'Enforcado', type: 'reversão baixa', direction: 'venda', reliability: 74, emoji: '🧟', candles: 1, description: 'Padrão de reversão após tendência de alta' });
    }
    if (invertedHammer(last, trend)) {
      found.push({ name: 'Martelo Invertido', type: 'reversão alta', direction: 'compra', reliability: 68, emoji: '⬆️', candles: 1, description: 'Possível reversão de alta após baixa' });
    }
    if (shootingStar(last, trend)) {
      found.push({ name: 'Estrela Cadente', type: 'reversão baixa', direction: 'venda', reliability: 76, emoji: '⭐', candles: 1, description: 'Rejeição de alta após tendência de alta' });
    }
    if (marubozu(last)) {
      const dir = isBull(last) ? 'compra' : 'venda';
      found.push({ name: `Marubozu ${isBull(last) ? 'Alta' : 'Baixa'}`, type: 'continuação', direction: dir, reliability: 82, emoji: isBull(last) ? '🟩' : '🟥', candles: 1, description: 'Corpo cheio sem sombras — força máxima de tendência' });
    }
    if (spinningTop(last)) {
      found.push({ name: 'Pião', type: 'indecisão', direction: 'neutro', reliability: 55, emoji: '🌀', candles: 1, description: 'Indecisão com sombras longas dos dois lados' });
    }

    // === 2 VELAS ===
    const engulf = engulfing(prev, last);
    if (engulf.bullEngulf) {
      found.push({ name: 'Engolfo de Alta', type: 'reversão alta', direction: 'compra', reliability: 85, emoji: '💚', candles: 2, description: 'Vela de alta engole completamente a anterior — sinal forte' });
    }
    if (engulf.bearEngulf) {
      found.push({ name: 'Engolfo de Baixa', type: 'reversão baixa', direction: 'venda', reliability: 85, emoji: '❤️', candles: 2, description: 'Vela de baixa engole completamente a anterior — sinal forte' });
    }
    const har = harami(prev, last);
    if (har.bullHarami) {
      found.push({ name: 'Harami de Alta', type: 'reversão alta', direction: 'compra', reliability: 65, emoji: '🤰', candles: 2, description: 'Vela pequena dentro da vela grande anterior — indecisão' });
    }
    if (har.bearHarami) {
      found.push({ name: 'Harami de Baixa', type: 'reversão baixa', direction: 'venda', reliability: 65, emoji: '🤰', candles: 2, description: 'Sinal de possível reversão após tendência de alta' });
    }
    if (harami_cross(prev, last)) {
      found.push({ name: 'Harami Cross', type: 'reversão', direction: 'neutro', reliability: 68, emoji: '✝️', candles: 2, description: 'Doji dentro de vela grande — reversão muito provável' });
    }
    if (piercing(prev, last)) {
      found.push({ name: 'Linha de Penetração', type: 'reversão alta', direction: 'compra', reliability: 76, emoji: '🗡️', candles: 2, description: 'Vela alta fecha acima do meio da vela baixa anterior' });
    }
    if (darkCloudCover(prev, last)) {
      found.push({ name: 'Cobertura de Nuvem Negra', type: 'reversão baixa', direction: 'venda', reliability: 76, emoji: '⛈️', candles: 2, description: 'Vela baixa fecha abaixo do meio da vela alta anterior' });
    }
    if (tweezerTop(prev, last)) {
      found.push({ name: 'Pinça no Topo', type: 'reversão baixa', direction: 'venda', reliability: 70, emoji: '📌', candles: 2, description: 'Duas velas com topos iguais — resistência confirmada' });
    }
    if (tweezerBottom(prev, last)) {
      found.push({ name: 'Pinça no Fundo', type: 'reversão alta', direction: 'compra', reliability: 70, emoji: '📌', candles: 2, description: 'Duas velas com fundos iguais — suporte confirmado' });
    }

    // === 3 VELAS ===
    if (morningstar(prev2, prev, last)) {
      found.push({ name: 'Estrela da Manhã', type: 'reversão alta', direction: 'compra', reliability: 88, emoji: '🌅', candles: 3, description: 'Padrão de 3 velas forte — reversão de baixa para alta' });
    }
    if (eveningstar(prev2, prev, last)) {
      found.push({ name: 'Estrela da Tarde', type: 'reversão baixa', direction: 'venda', reliability: 88, emoji: '🌆', candles: 3, description: 'Padrão de 3 velas forte — reversão de alta para baixa' });
    }
    if (threeWhiteSoldiers(prev2, prev, last)) {
      found.push({ name: 'Três Soldados Brancos', type: 'continuação alta', direction: 'compra', reliability: 84, emoji: '⚔️', candles: 3, description: 'Três velas de alta consecutivas — tendência forte' });
    }
    if (threeBlackCrows(prev2, prev, last)) {
      found.push({ name: 'Três Corvos Negros', type: 'continuação baixa', direction: 'venda', reliability: 84, emoji: '🦅', candles: 3, description: 'Três velas de baixa consecutivas — tendência forte de queda' });
    }
    if (threeInsideUp(prev2, prev, last)) {
      found.push({ name: 'Três Dentro para Cima', type: 'reversão alta', direction: 'compra', reliability: 78, emoji: '📈', candles: 3, description: 'Confirmação de reversão altista após harami' });
    }
    if (threeInsideDown(prev2, prev, last)) {
      found.push({ name: 'Três Dentro para Baixo', type: 'reversão baixa', direction: 'venda', reliability: 78, emoji: '📉', candles: 3, description: 'Confirmação de reversão baixista após harami' });
    }
    if (abandonedBaby(prev2, prev, last, true)) {
      found.push({ name: 'Bebê Abandonado Alta', type: 'reversão alta', direction: 'compra', reliability: 90, emoji: '👶', candles: 3, description: 'Padrão raro e muito confiável de reversão altista' });
    }
    if (abandonedBaby(prev2, prev, last, false)) {
      found.push({ name: 'Bebê Abandonado Baixa', type: 'reversão baixa', direction: 'venda', reliability: 90, emoji: '👶', candles: 3, description: 'Padrão raro e muito confiável de reversão baixista' });
    }

    // === 5 VELAS ===
    if (risingThreeMethods(prev4, prev3, prev2, prev, last)) {
      found.push({ name: 'Três Métodos Ascendentes', type: 'continuação alta', direction: 'compra', reliability: 80, emoji: '📊', candles: 5, description: 'Pausa na tendência de alta antes de continuar subindo' });
    }
    if (fallingThreeMethods(prev4, prev3, prev2, prev, last)) {
      found.push({ name: 'Três Métodos Descendentes', type: 'continuação baixa', direction: 'venda', reliability: 80, emoji: '📊', candles: 5, description: 'Pausa na tendência de baixa antes de continuar caindo' });
    }

    // Pontuação ponderada
    let bs = 0, ss = 0;
    for (const p of found) {
      const weight = p.reliability / 100;
      if (p.direction === 'compra') bs += weight * 10;
      else if (p.direction === 'venda') ss += weight * 10;
    }

    return {
      patterns: found,
      bullScore: bs,
      bearScore: ss,
      dominant: bs > ss ? 'compra' : ss > bs ? 'venda' : 'neutro',
      confidence: found.length > 0 ? Math.round(Math.max(bs, ss) / (bs + ss || 1) * 100) : 50,
    };
  }

  // Scan de padrões nos últimos N candles (busca histórica)
  function scanHistory(candles, lookback = 10) {
    const results = [];
    for (let i = 5; i <= Math.min(candles.length - 1, lookback + 5); i++) {
      const slice = candles.slice(0, i + 1);
      const detected = detectAll(slice);
      if (detected.patterns.length > 0) {
        results.push({
          index: i,
          time: candles[i].time,
          candle: candles[i],
          patterns: detected.patterns,
          outcome: i < candles.length - 3 ? measureOutcome(candles, i) : 'pendente',
        });
      }
    }
    return results;
  }

  function measureOutcome(candles, signalIdx) {
    const refPrice = candles[signalIdx].close;
    const future = candles.slice(signalIdx + 1, signalIdx + 5);
    if (future.length === 0) return 'pendente';
    const maxHigh = Math.max(...future.map(c => c.high));
    const minLow = Math.min(...future.map(c => c.low));
    const upMove = (maxHigh - refPrice) / refPrice * 100;
    const downMove = (refPrice - minLow) / refPrice * 100;
    if (upMove > 1 && upMove > downMove) return 'acertou_alta';
    if (downMove > 1 && downMove > upMove) return 'acertou_baixa';
    return 'lateral';
  }

  return { detectAll, scanHistory };
})();
