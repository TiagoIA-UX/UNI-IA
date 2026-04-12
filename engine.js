/**
 * ENGINE.JS — Motor de análise técnica completo
 * Indicadores: SMA, EMA, DEMA, TEMA, RSI, MACD, Bollinger, Estocástico,
 *              ATR, OBV, VWAP, Ichimoku, Williams %R, CCI, ADX, Parabolic SAR
 */

const TechnicalEngine = (() => {

  // ===== MÉDIAS MÓVEIS =====
  function sma(data, period) {
    const result = new Array(data.length).fill(null);
    for (let i = period - 1; i < data.length; i++) {
      const sum = data.slice(i - period + 1, i + 1).reduce((a, b) => a + b, 0);
      result[i] = sum / period;
    }
    return result;
  }

  function ema(data, period) {
    const k = 2 / (period + 1);
    const result = new Array(data.length).fill(null);
    let emaVal = null;
    for (let i = 0; i < data.length; i++) {
      if (data[i] === null || data[i] === undefined) continue;
      if (emaVal === null) { emaVal = data[i]; result[i] = emaVal; continue; }
      emaVal = data[i] * k + emaVal * (1 - k);
      result[i] = emaVal;
    }
    return result;
  }

  function dema(data, period) {
    const e1 = ema(data, period);
    const validE1 = e1.map(v => v ?? 0);
    const e2 = ema(validE1, period);
    return e1.map((v, i) => v !== null && e2[i] !== null ? 2 * v - e2[i] : null);
  }

  function tema(data, period) {
    const e1 = ema(data, period);
    const validE1 = e1.map(v => v ?? 0);
    const e2 = ema(validE1, period);
    const validE2 = e2.map(v => v ?? 0);
    const e3 = ema(validE2, period);
    return e1.map((v, i) =>
      v !== null && e2[i] !== null && e3[i] !== null ? 3 * v - 3 * e2[i] + e3[i] : null
    );
  }

  function wma(data, period) {
    const result = new Array(data.length).fill(null);
    const weights = Array.from({ length: period }, (_, i) => i + 1);
    const weightSum = weights.reduce((a, b) => a + b, 0);
    for (let i = period - 1; i < data.length; i++) {
      let sum = 0;
      for (let j = 0; j < period; j++) sum += (data[i - j] ?? 0) * weights[period - 1 - j];
      result[i] = sum / weightSum;
    }
    return result;
  }

  // ===== RSI =====
  function rsi(closes, period = 14) {
    const result = new Array(closes.length).fill(null);
    let gains = 0, losses = 0;
    for (let i = 1; i <= period; i++) {
      const diff = closes[i] - closes[i - 1];
      if (diff >= 0) gains += diff; else losses -= diff;
    }
    let avgGain = gains / period;
    let avgLoss = losses / period;
    result[period] = avgLoss === 0 ? 100 : 100 - 100 / (1 + avgGain / avgLoss);
    for (let i = period + 1; i < closes.length; i++) {
      const diff = closes[i] - closes[i - 1];
      const gain = diff > 0 ? diff : 0;
      const loss = diff < 0 ? -diff : 0;
      avgGain = (avgGain * (period - 1) + gain) / period;
      avgLoss = (avgLoss * (period - 1) + loss) / period;
      result[i] = avgLoss === 0 ? 100 : 100 - 100 / (1 + avgGain / avgLoss);
    }
    return result;
  }

  // ===== MACD =====
  function macd(closes, fast = 12, slow = 26, signal = 9) {
    const emaFast = ema(closes, fast);
    const emaSlow = ema(closes, slow);
    const macdLine = emaFast.map((v, i) =>
      v !== null && emaSlow[i] !== null ? v - emaSlow[i] : null
    );
    const validMacd = macdLine.map(v => v ?? 0);
    const signalLine = ema(validMacd, signal);
    const histogram = macdLine.map((v, i) =>
      v !== null && signalLine[i] !== null ? v - signalLine[i] : null
    );
    return { macdLine, signalLine, histogram };
  }

  // ===== BOLLINGER BANDS =====
  function bollingerBands(closes, period = 20, stdDev = 2) {
    const mid = sma(closes, period);
    const upper = new Array(closes.length).fill(null);
    const lower = new Array(closes.length).fill(null);
    const width = new Array(closes.length).fill(null);
    for (let i = period - 1; i < closes.length; i++) {
      const slice = closes.slice(i - period + 1, i + 1);
      const mean = mid[i];
      const variance = slice.reduce((sum, v) => sum + Math.pow(v - mean, 2), 0) / period;
      const sd = Math.sqrt(variance);
      upper[i] = mean + stdDev * sd;
      lower[i] = mean - stdDev * sd;
      width[i] = mean > 0 ? ((upper[i] - lower[i]) / mean) * 100 : null;
    }
    return { upper, mid, lower, width };
  }

  // ===== ESTOCÁSTICO =====
  function stochastic(candles, kPeriod = 14, dPeriod = 3) {
    const kRaw = new Array(candles.length).fill(null);
    for (let i = kPeriod - 1; i < candles.length; i++) {
      const slice = candles.slice(i - kPeriod + 1, i + 1);
      const highMax = Math.max(...slice.map(c => c.high));
      const lowMin = Math.min(...slice.map(c => c.low));
      const range = highMax - lowMin;
      kRaw[i] = range === 0 ? 50 : ((candles[i].close - lowMin) / range) * 100;
    }
    const kSmooth = sma(kRaw.map(v => v ?? 0), 3);
    const dLine = sma(kSmooth.map(v => v ?? 0), dPeriod);
    return { k: kSmooth, d: dLine };
  }

  // ===== ATR (Average True Range) =====
  function atr(candles, period = 14) {
    const tr = candles.map((c, i) => {
      if (i === 0) return c.high - c.low;
      const prev = candles[i - 1].close;
      return Math.max(c.high - c.low, Math.abs(c.high - prev), Math.abs(c.low - prev));
    });
    return sma(tr, period);
  }

  // ===== OBV (On-Balance Volume) =====
  function obv(candles) {
    const result = new Array(candles.length).fill(0);
    result[0] = candles[0].volume;
    for (let i = 1; i < candles.length; i++) {
      if (candles[i].close > candles[i - 1].close) result[i] = result[i - 1] + candles[i].volume;
      else if (candles[i].close < candles[i - 1].close) result[i] = result[i - 1] - candles[i].volume;
      else result[i] = result[i - 1];
    }
    return result;
  }

  // ===== VWAP =====
  function vwap(candles) {
    const result = new Array(candles.length).fill(null);
    let cumPV = 0, cumV = 0;
    for (let i = 0; i < candles.length; i++) {
      const typicalPrice = (candles[i].high + candles[i].low + candles[i].close) / 3;
      cumPV += typicalPrice * candles[i].volume;
      cumV += candles[i].volume;
      result[i] = cumV > 0 ? cumPV / cumV : typicalPrice;
    }
    return result;
  }

  // ===== ICHIMOKU =====
  function ichimoku(candles) {
    const n = candles.length;
    const tenkan = new Array(n).fill(null);
    const kijun = new Array(n).fill(null);
    const senkouA = new Array(n).fill(null);
    const senkouB = new Array(n).fill(null);
    const chikou = new Array(n).fill(null);

    for (let i = 8; i < n; i++) {
      const s9 = candles.slice(i - 8, i + 1);
      tenkan[i] = (Math.max(...s9.map(c => c.high)) + Math.min(...s9.map(c => c.low))) / 2;
    }
    for (let i = 25; i < n; i++) {
      const s26 = candles.slice(i - 25, i + 1);
      kijun[i] = (Math.max(...s26.map(c => c.high)) + Math.min(...s26.map(c => c.low))) / 2;
    }
    for (let i = 25; i < n; i++) {
      if (tenkan[i] !== null && kijun[i] !== null) senkouA[i] = (tenkan[i] + kijun[i]) / 2;
    }
    for (let i = 51; i < n; i++) {
      const s52 = candles.slice(i - 51, i + 1);
      senkouB[i] = (Math.max(...s52.map(c => c.high)) + Math.min(...s52.map(c => c.low))) / 2;
    }
    for (let i = 0; i < n - 26; i++) chikou[i + 26] = candles[i].close;

    return { tenkan, kijun, senkouA, senkouB, chikou };
  }

  // ===== WILLIAMS %R =====
  function williamsR(candles, period = 14) {
    return candles.map((c, i) => {
      if (i < period - 1) return null;
      const slice = candles.slice(i - period + 1, i + 1);
      const high = Math.max(...slice.map(s => s.high));
      const low = Math.min(...slice.map(s => s.low));
      return high === low ? -50 : ((high - c.close) / (high - low)) * -100;
    });
  }

  // ===== CCI =====
  function cci(candles, period = 20) {
    const result = new Array(candles.length).fill(null);
    for (let i = period - 1; i < candles.length; i++) {
      const slice = candles.slice(i - period + 1, i + 1);
      const tp = slice.map(c => (c.high + c.low + c.close) / 3);
      const mean = tp.reduce((a, b) => a + b, 0) / period;
      const md = tp.reduce((sum, v) => sum + Math.abs(v - mean), 0) / period;
      const currentTp = (candles[i].high + candles[i].low + candles[i].close) / 3;
      result[i] = md === 0 ? 0 : (currentTp - mean) / (0.015 * md);
    }
    return result;
  }

  // ===== ADX (Average Directional Index) =====
  function adx(candles, period = 14) {
    if (candles.length < period + 2) return { adx: [], pdi: [], mdi: [] };
    const trArr = [], pDMArr = [], mDMArr = [];
    for (let i = 1; i < candles.length; i++) {
      const prev = candles[i - 1];
      const curr = candles[i];
      trArr.push(Math.max(curr.high - curr.low, Math.abs(curr.high - prev.close), Math.abs(curr.low - prev.close)));
      const upMove = curr.high - prev.high;
      const downMove = prev.low - curr.low;
      pDMArr.push(upMove > downMove && upMove > 0 ? upMove : 0);
      mDMArr.push(downMove > upMove && downMove > 0 ? downMove : 0);
    }
    const smoothTR = ema(trArr, period);
    const smoothPDM = ema(pDMArr, period);
    const smoothMDM = ema(mDMArr, period);
    const pDI = smoothTR.map((v, i) => v > 0 ? (smoothPDM[i] / v) * 100 : null);
    const mDI = smoothTR.map((v, i) => v > 0 ? (smoothMDM[i] / v) * 100 : null);
    const dx = pDI.map((v, i) => {
      if (v === null || mDI[i] === null) return null;
      const sum = v + mDI[i];
      return sum === 0 ? 0 : (Math.abs(v - mDI[i]) / sum) * 100;
    });
    const adxLine = ema(dx.map(v => v ?? 0), period);
    const result = { adx: [null, ...adxLine], pdi: [null, ...pDI], mdi: [null, ...mDI] };
    return result;
  }

  // ===== PARABOLIC SAR =====
  function parabolicSAR(candles, step = 0.02, max = 0.2) {
    const result = new Array(candles.length).fill(null);
    if (candles.length < 2) return result;
    let isLong = candles[1].close > candles[0].close;
    let sar = isLong ? candles[0].low : candles[0].high;
    let ep = isLong ? candles[0].high : candles[0].low;
    let af = step;
    for (let i = 1; i < candles.length; i++) {
      sar = sar + af * (ep - sar);
      if (isLong) {
        if (candles[i].low < sar) {
          isLong = false; sar = ep; ep = candles[i].low; af = step;
        } else {
          if (candles[i].high > ep) { ep = candles[i].high; af = Math.min(af + step, max); }
          sar = Math.min(sar, candles[i - 1].low, i > 1 ? candles[i - 2].low : candles[i - 1].low);
        }
      } else {
        if (candles[i].high > sar) {
          isLong = true; sar = ep; ep = candles[i].high; af = step;
        } else {
          if (candles[i].low < ep) { ep = candles[i].low; af = Math.min(af + step, max); }
          sar = Math.max(sar, candles[i - 1].high, i > 1 ? candles[i - 2].high : candles[i - 1].high);
        }
      }
      result[i] = { value: sar, isLong };
    }
    return result;
  }

  // ===== SUPORTE E RESISTÊNCIA =====
  function supportResistance(candles, lookback = 20, tolerance = 0.003) {
    const levels = [];
    for (let i = lookback; i < candles.length - lookback; i++) {
      const slice = candles.slice(i - lookback, i + lookback);
      const midHigh = candles[i].high;
      const midLow = candles[i].low;
      const isResistance = slice.every(c => c.high <= midHigh * (1 + tolerance));
      const isSupport = slice.every(c => c.low >= midLow * (1 - tolerance));
      if (isResistance) levels.push({ price: midHigh, type: 'resistance', strength: lookback });
      if (isSupport) levels.push({ price: midLow, type: 'support', strength: lookback });
    }
    // Consolidar níveis próximos
    const consolidated = [];
    for (const level of levels) {
      const similar = consolidated.find(l => Math.abs(l.price - level.price) / level.price < tolerance * 3);
      if (similar) similar.strength += 1;
      else consolidated.push({ ...level });
    }
    return consolidated.sort((a, b) => b.strength - a.strength).slice(0, 8);
  }

  // ===== TENDÊNCIA =====
  function detectTrend(closes, period = 20) {
    const recentSMA = sma(closes, period);
    const lastSMA = recentSMA[recentSMA.length - 1];
    const prevSMA = recentSMA[recentSMA.length - 6];
    if (!lastSMA || !prevSMA) return 'lateral';
    const change = (lastSMA - prevSMA) / prevSMA;
    if (change > 0.01) return 'alta';
    if (change < -0.01) return 'baixa';
    return 'lateral';
  }

  // ===== VOLUME PROFILE =====
  function volumeProfile(candles, bins = 20) {
    const prices = candles.map(c => c.close);
    const min = Math.min(...prices);
    const max = Math.max(...prices);
    const binSize = (max - min) / bins;
    const profile = new Array(bins).fill(0).map((_, i) => ({
      price: min + i * binSize + binSize / 2,
      volume: 0,
    }));
    for (const c of candles) {
      const bin = Math.min(Math.floor((c.close - min) / binSize), bins - 1);
      profile[bin].volume += c.volume;
    }
    const maxVol = Math.max(...profile.map(p => p.volume));
    const poc = profile.find(p => p.volume === maxVol);
    return { profile, poc };
  }

  // ===== ANÁLISE COMPLETA =====
  function analyze(candles) {
    if (!candles || candles.length < 30) return null;
    const closes = candles.map(c => c.close);
    const last = candles.length - 1;

    const sma9 = sma(closes, 9);
    const sma21 = sma(closes, 21);
    const sma50 = sma(closes, 50);
    const sma200 = sma(closes, 200);
    const ema9 = ema(closes, 9);
    const ema21 = ema(closes, 21);
    const rsiLine = rsi(closes, 14);
    const macdData = macd(closes);
    const bb = bollingerBands(closes, 20, 2);
    const stoch = stochastic(candles, 14, 3);
    const atrLine = atr(candles, 14);
    const obvLine = obv(candles);
    const vwapLine = vwap(candles);
    const ich = ichimoku(candles);
    const willR = williamsR(candles, 14);
    const cciLine = cci(candles, 20);
    const adxData = adx(candles, 14);
    const sarData = parabolicSAR(candles);
    const srLevels = supportResistance(candles);
    const trend = detectTrend(closes);
    const volProfile = volumeProfile(candles);

    const current = candles[last];
    const currentRSI = rsiLine[last] ?? 50;
    const currentMACD = macdData.macdLine[last] ?? 0;
    const currentSignal = macdData.signalLine[last] ?? 0;
    const currentHist = macdData.histogram[last] ?? 0;
    const prevHist = macdData.histogram[last - 1] ?? 0;
    const currentBBUpper = bb.upper[last] ?? current.close;
    const currentBBLower = bb.lower[last] ?? current.close;
    const currentBBMid = bb.mid[last] ?? current.close;
    const currentBBWidth = bb.width[last] ?? 0;
    const currentStochK = stoch.k[last] ?? 50;
    const currentStochD = stoch.d[last] ?? 50;
    const currentATR = atrLine[last] ?? 0;
    const currentOBV = obvLine[last] ?? 0;
    const prevOBV = obvLine[last - 3] ?? currentOBV;
    const currentVWAP = vwapLine[last] ?? current.close;
    const currentWillR = willR[last] ?? -50;
    const currentCCI = cciLine[last] ?? 0;
    const currentADX = adxData.adx[last] ?? 0;
    const currentPDI = adxData.pdi[last] ?? 0;
    const currentMDI = adxData.mdi[last] ?? 0;
    const sarLast = sarData[last];

    // ===== PONTUAÇÃO TÉCNICA =====
    let bullScore = 0, bearScore = 0, signals = [];

    // RSI
    if (currentRSI < 30) { bullScore += 12; signals.push({ name: 'RSI', signal: 'compra', reason: `RSI ${currentRSI.toFixed(1)} — sobrevenda extrema` }); }
    else if (currentRSI < 45) { bullScore += 6; signals.push({ name: 'RSI', signal: 'compra fraco', reason: `RSI ${currentRSI.toFixed(1)} — sobrevenda leve` }); }
    else if (currentRSI > 70) { bearScore += 12; signals.push({ name: 'RSI', signal: 'venda', reason: `RSI ${currentRSI.toFixed(1)} — sobrecompra extrema` }); }
    else if (currentRSI > 57) { bearScore += 6; signals.push({ name: 'RSI', signal: 'venda fraco', reason: `RSI ${currentRSI.toFixed(1)} — sobrecompra leve` }); }
    else { signals.push({ name: 'RSI', signal: 'neutro', reason: `RSI ${currentRSI.toFixed(1)} — zona neutra` }); }

    // MACD
    if (currentMACD > currentSignal && currentHist > 0 && prevHist <= 0) { bullScore += 15; signals.push({ name: 'MACD', signal: 'compra', reason: 'Cruzamento altista — MACD acima do sinal' }); }
    else if (currentMACD > currentSignal && currentHist > 0) { bullScore += 7; signals.push({ name: 'MACD', signal: 'compra', reason: 'MACD positivo acima do sinal' }); }
    else if (currentMACD < currentSignal && currentHist < 0 && prevHist >= 0) { bearScore += 15; signals.push({ name: 'MACD', signal: 'venda', reason: 'Cruzamento baixista — MACD abaixo do sinal' }); }
    else if (currentMACD < currentSignal) { bearScore += 7; signals.push({ name: 'MACD', signal: 'venda', reason: 'MACD negativo abaixo do sinal' }); }
    else { signals.push({ name: 'MACD', signal: 'neutro', reason: 'MACD sem direção clara' }); }

    // BOLLINGER
    const bbPosition = (current.close - currentBBLower) / (currentBBUpper - currentBBLower);
    if (bbPosition < 0.1) { bullScore += 10; signals.push({ name: 'Bollinger', signal: 'compra', reason: 'Preço tocou banda inferior — possível reversão' }); }
    else if (bbPosition > 0.9) { bearScore += 10; signals.push({ name: 'Bollinger', signal: 'venda', reason: 'Preço tocou banda superior — possível reversão' }); }
    if (currentBBWidth < 2) { signals.push({ name: 'Bollinger Width', signal: 'alerta', reason: 'Compressão (squeeze) — explosão iminente' }); }

    // MÉDIAS MÓVEIS
    const crossGolden = sma9[last] > sma21[last] && sma9[last - 1] < sma21[last - 1];
    const crossDeath = sma9[last] < sma21[last] && sma9[last - 1] > sma21[last - 1];
    if (crossGolden) { bullScore += 14; signals.push({ name: 'MM Cross', signal: 'compra', reason: 'Golden Cross SMA9 > SMA21' }); }
    else if (crossDeath) { bearScore += 14; signals.push({ name: 'MM Cross', signal: 'venda', reason: 'Death Cross SMA9 < SMA21' }); }
    else if (sma9[last] > sma21[last]) { bullScore += 5; signals.push({ name: 'MM Tendência', signal: 'alta', reason: 'MM curta acima da longa — tendência de alta' }); }
    else if (sma9[last] < sma21[last]) { bearScore += 5; signals.push({ name: 'MM Tendência', signal: 'baixa', reason: 'MM curta abaixo da longa — tendência de baixa' }); }

    // ESTOCÁSTICO
    if (currentStochK < 20 && currentStochD < 20) { bullScore += 9; signals.push({ name: 'Estocástico', signal: 'compra', reason: `Estoc ${currentStochK.toFixed(0)}/${currentStochD.toFixed(0)} — zona de sobrevenda` }); }
    else if (currentStochK > 80 && currentStochD > 80) { bearScore += 9; signals.push({ name: 'Estocástico', signal: 'venda', reason: `Estoc ${currentStochK.toFixed(0)}/${currentStochD.toFixed(0)} — zona de sobrecompra` }); }

    // OBV
    const obvTrend = currentOBV > prevOBV ? 'alta' : 'baixa';
    if (obvTrend === 'alta' && trend === 'alta') { bullScore += 8; signals.push({ name: 'OBV', signal: 'confirmação', reason: 'Volume confirma tendência de alta' }); }
    else if (obvTrend === 'baixa' && trend === 'baixa') { bearScore += 8; signals.push({ name: 'OBV', signal: 'confirmação', reason: 'Volume confirma tendência de baixa' }); }
    else if (obvTrend !== (trend === 'alta' ? 'alta' : 'baixa')) { signals.push({ name: 'OBV', signal: 'divergência', reason: 'Volume diverge da tendência — sinal de atenção' }); }

    // VWAP
    if (current.close > currentVWAP) { bullScore += 5; signals.push({ name: 'VWAP', signal: 'alta', reason: 'Preço acima do VWAP — compradores dominantes' }); }
    else { bearScore += 5; signals.push({ name: 'VWAP', signal: 'baixa', reason: 'Preço abaixo do VWAP — vendedores dominantes' }); }

    // ICHIMOKU
    const inCloud = ich.senkouA[last] && ich.senkouB[last] &&
      current.close >= Math.min(ich.senkouA[last], ich.senkouB[last]) &&
      current.close <= Math.max(ich.senkouA[last], ich.senkouB[last]);
    const aboveCloud = ich.senkouA[last] && ich.senkouB[last] &&
      current.close > Math.max(ich.senkouA[last], ich.senkouB[last]);
    if (aboveCloud) { bullScore += 10; signals.push({ name: 'Ichimoku', signal: 'alta', reason: 'Preço acima da nuvem — tendência de alta forte' }); }
    else if (inCloud) { signals.push({ name: 'Ichimoku', signal: 'neutro', reason: 'Preço dentro da nuvem — indecisão' }); }
    else { bearScore += 10; signals.push({ name: 'Ichimoku', signal: 'baixa', reason: 'Preço abaixo da nuvem — tendência de baixa forte' }); }

    // ADX
    if (currentADX > 25) {
      const adxTrend = currentPDI > currentMDI ? 'alta' : 'baixa';
      if (adxTrend === 'alta') { bullScore += 8; signals.push({ name: 'ADX', signal: 'alta', reason: `ADX ${currentADX?.toFixed(1)} — tendência de alta forte` }); }
      else { bearScore += 8; signals.push({ name: 'ADX', signal: 'baixa', reason: `ADX ${currentADX?.toFixed(1)} — tendência de baixa forte` }); }
    } else {
      signals.push({ name: 'ADX', signal: 'fraco', reason: `ADX ${currentADX?.toFixed(1)} — tendência fraca ou lateral` });
    }

    // PARABOLIC SAR
    if (sarLast) {
      if (sarLast.isLong) { bullScore += 6; signals.push({ name: 'SAR', signal: 'alta', reason: 'Parabolic SAR abaixo do preço — sinal de alta' }); }
      else { bearScore += 6; signals.push({ name: 'SAR', signal: 'baixa', reason: 'Parabolic SAR acima do preço — sinal de baixa' }); }
    }

    // WILLIAMS %R
    if (currentWillR < -80) { bullScore += 7; signals.push({ name: 'Williams %R', signal: 'compra', reason: `W%R ${currentWillR.toFixed(1)} — sobrevenda extrema` }); }
    else if (currentWillR > -20) { bearScore += 7; signals.push({ name: 'Williams %R', signal: 'venda', reason: `W%R ${currentWillR.toFixed(1)} — sobrecompra extrema` }); }

    // CCI
    if (currentCCI < -100) { bullScore += 7; signals.push({ name: 'CCI', signal: 'compra', reason: `CCI ${currentCCI.toFixed(1)} — sobrevenda` }); }
    else if (currentCCI > 100) { bearScore += 7; signals.push({ name: 'CCI', signal: 'venda', reason: `CCI ${currentCCI.toFixed(1)} — sobrecompra` }); }

    // SCORE FINAL
    const totalScore = bullScore + bearScore;
    const rawConfidence = totalScore > 0 ? Math.max(bullScore, bearScore) / totalScore : 0.5;
    const confidence = Math.min(0.95, 0.45 + rawConfidence * 0.5);
    const direction = bullScore > bearScore ? 'COMPRA' : bearScore > bullScore ? 'VENDA' : 'AGUARDAR';

    // ENTRY, STOP, TARGET
    const atrVal = currentATR;
    const entry = current.close;
    const stopLoss = direction === 'COMPRA' ? entry - atrVal * 1.5 : entry + atrVal * 1.5;
    const takeProfit = direction === 'COMPRA' ? entry + atrVal * 3 : entry - atrVal * 3;
    const riskReward = Math.abs(takeProfit - entry) / Math.abs(stopLoss - entry);

    return {
      direction,
      confidence: Math.round(confidence * 100),
      bullScore,
      bearScore,
      trend,
      signals,
      indicators: {
        rsi: currentRSI,
        macd: { line: currentMACD, signal: currentSignal, hist: currentHist },
        bb: { upper: currentBBUpper, mid: currentBBMid, lower: currentBBLower, width: currentBBWidth, position: bbPosition },
        stoch: { k: currentStochK, d: currentStochD },
        atr: currentATR,
        obv: currentOBV,
        vwap: currentVWAP,
        adx: currentADX,
        pdi: currentPDI,
        mdi: currentMDI,
        williams: currentWillR,
        cci: currentCCI,
        sar: sarLast,
        sma9: sma9[last], sma21: sma21[last], sma50: sma50[last], sma200: sma200[last],
      },
      srLevels,
      entry, stopLoss, takeProfit, riskReward,
      volProfile,
      raw: { sma9, sma21, sma50, ema9, ema21, rsiLine, macdData, bb, stoch, obvLine, vwapLine, sarData },
    };
  }

  return { analyze, sma, ema, dema, tema, rsi, macd, bollingerBands, stochastic, atr, obv, vwap, ichimoku, williamsR, cci, adx, parabolicSAR, supportResistance, detectTrend, volumeProfile };
})();
