/**
 * APP.JS — Controller principal do Uni IA
 * Orquestra: DataLayer, TechnicalEngine, CandlePatterns, ExternalFactors, AIEngine
 *
 * PATCHES APLICADOS:
 * [BUG-1] Auto-select BTC/USDT no DOMContentLoaded — gráfico renderiza imediatamente
 * [BUG-2] toSec() universal — normaliza timestamps ms e s, evita candles em 1970
 */

// ===== ESTADO GLOBAL =====
let state = {
  selectedAsset: null,
  selectedTF: '1h',
  candles: [],
  quote: null,
  techAnalysis: null,
  patternResult: null,
  lastSignal: null,
  liveInterval: null,
  chartInstance: null,
  volumeChartInstance: null,
  candleSeries: null,
  volumeSeries: null,
  activeIndicators: new Set(['sma9', 'sma21', 'volume']),
  indicatorSeries: {},
  news: [],
};

 ═══════════════════════════════════════════════════════════════════════════
   BLOCO A — Estado do stream (colar após `let state = { ... }`)
   ═══════════════════════════════════════════════════════════════════════════ */
 
let rtState = {
  pollTimer  : null,   // fallback polling para ativos não-Binance
  POLL_MS    : 5_000,  // intervalo de polling (ms)
  statusEl   : null,   // elemento DOM do badge de status (opcional)
};
 
// Atualiza badge de status no header do gráfico (se existir #rt-status no HTML)
function _setRtBadge(status) {
  if (!rtState.statusEl) {
    rtState.statusEl = document.getElementById('rt-status');
  }
  if (!rtState.statusEl) return;
 
  const MAP = {
    connecting  : { text: '⟳ Conectando',   cls: 'rt-connecting'   },
    live        : { text: '● AO VIVO',       cls: 'rt-live'         },
    reconnecting: { text: '↺ Reconectando',  cls: 'rt-reconnecting' },
    stopped     : { text: '○ Offline',        cls: 'rt-stopped'      },
    polling     : { text: '⏱ Polling 5s',    cls: 'rt-polling'      },
  };
 
  const info = MAP[status] || MAP.stopped;
  rtState.statusEl.textContent  = info.text;
  rtState.statusEl.className    = `rt-badge ${info.cls}`;
}
 
// Para todos os streams ativos (WebSocket + polling)
function _stopAllStreams() {
  if (typeof RealtimeStream !== 'undefined') RealtimeStream.stop();
  clearInterval(rtState.pollTimer);
  rtState.pollTimer = null;
}

const TIMEFRAMES = [
  { key: '5m',  label: '5M',    desc: 'Scalping' },
  { key: '15m', label: '15M',   desc: 'Day Trade curto' },
  { key: '1h',  label: '1H',    desc: 'Day Trade clássico' },
  { key: '4h',  label: '4H',    desc: 'Swing Trade' },
  { key: '1d',  label: '1D',    desc: 'Position' },
  { key: '1w',  label: '1W',    desc: 'Long Term' },
];

const INDICATORS_CONFIG = [
  { key: 'sma9',    label: 'SMA9',     color: '#2962ff' },
  { key: 'sma21',   label: 'SMA21',    color: '#00e5ff' },
  { key: 'sma50',   label: 'SMA50',    color: '#ff9100' },
  { key: 'sma200',  label: 'SMA200',   color: '#ff4081' },
  { key: 'ema9',    label: 'EMA9',     color: '#ae92f5' },
  { key: 'vwap',    label: 'VWAP',     color: '#69f0ae' },
  { key: 'bb',      label: 'BB',       color: '#546e7a' },
  { key: 'sar',     label: 'SAR',      color: '#ffd600' },
  { key: 'volume',  label: 'Volume',   color: '#37474f' },
];

// ===== [BUG-2 FIX] TIMESTAMP UNIVERSAL =====
// Normaliza qualquer timestamp para segundos (formato exigido pelo lightweight-charts).
// Binance retorna ms (13 dígitos), Frankfurt/BRAPI podem retornar ms ou s dependendo
// do fallback. Se > 1e10 assume ms e divide por 1000; caso contrário já está em segundos.

/* ═══════════════════════════════════════════════════════════════════════════
   BLOCO B — updateChart() com suporte a .update() do lightweight-charts
   Substitui a função updateChart() existente integralmente.
   ═══════════════════════════════════════════════════════════════════════════ */

function toSec(t) {
  if (!t || !Number.isFinite(t)) return 0;
  return t > 1e10 ? Math.floor(t / 1000) : Math.floor(t);
}

// ===== INIT =====
window.addEventListener('DOMContentLoaded', () => {
  initChart();
  initTimeframeTabs();
  initIndicatorBar();
  initWeightsPanel();
  renderFactorsPanel();
  renderCalendarRisk();
  populateAssetList();
  updateHeaderTime();
  setInterval(updateHeaderTime, 1000);
  updateLearningStats();
  loadApiKeyFromStorage();
});

// ===== RELÓGIO =====
function updateHeaderTime() {
  const now = new Date();
  document.getElementById('hd-time').textContent = now.toLocaleTimeString('pt-BR');
}

// ===== GRÁFICO =====
function initChart() {
  const chartEl = document.getElementById('chart');
  const volEl = document.getElementById('volume-chart');

  state.chartInstance = LightweightCharts.createChart(chartEl, {
    width: chartEl.clientWidth,
    height: 380,
    layout: { background: { color: '#0a0e1a' }, textColor: '#90a4ae' },
    grid: { vertLines: { color: '#1e2d50' }, horzLines: { color: '#1e2d50' } },
    crosshair: { mode: LightweightCharts.CrosshairMode.Normal },
    rightPriceScale: { borderColor: '#1e2d50', scaleMargins: { top: 0.05, bottom: 0.05 } },
    timeScale: { borderColor: '#1e2d50', timeVisible: true, secondsVisible: false },
  });

  state.candleSeries = state.chartInstance.addCandlestickSeries({
    upColor: '#00c853', downColor: '#ff1744',
    borderUpColor: '#00c853', borderDownColor: '#ff1744',
    wickUpColor: '#69f0ae', wickDownColor: '#ff6e6e',
  });

  state.volumeChartInstance = LightweightCharts.createChart(volEl, {
    width: volEl.clientWidth,
    height: 90,
    layout: { background: { color: '#0a0e1a' }, textColor: '#90a4ae' },
    grid: { vertLines: { color: '#1e2d50' }, horzLines: { color: '#1e2d50' } },
    rightPriceScale: { borderColor: '#1e2d50', scaleMargins: { top: 0.1, bottom: 0 } },
    timeScale: { borderColor: '#1e2d50', timeVisible: false },
  });

  state.volumeSeries = state.volumeChartInstance.addHistogramSeries({
    color: '#264653',
    priceFormat: { type: 'volume' },
    priceScaleId: '',
  });

  // Sincronizar scroll
  state.chartInstance.timeScale().subscribeVisibleLogicalRangeChange(range => {
    if (range) state.volumeChartInstance.timeScale().setVisibleLogicalRange(range);
  });
  state.volumeChartInstance.timeScale().subscribeVisibleLogicalRangeChange(range => {
    if (range) state.chartInstance.timeScale().setVisibleLogicalRange(range);
  });

  // Responsivo
  const ro = new ResizeObserver(() => {
    state.chartInstance.applyOptions({ width: chartEl.clientWidth });
    state.volumeChartInstance.applyOptions({ width: volEl.clientWidth });
  });
  ro.observe(chartEl);
}

// ===== TIMEFRAMES =====
function initTimeframeTabs() {
  const container = document.getElementById('tf-tabs');
  container.innerHTML = TIMEFRAMES.map(tf => `
    <button class="tf-btn ${tf.key === state.selectedTF ? 'active' : ''}" 
            onclick="selectTimeframe('${tf.key}')" 
            title="${tf.desc}">${tf.label}</button>
  `).join('');
}

function selectTimeframe(tf) {
  state.selectedTF = tf;
  initTimeframeTabs();
  if (state.selectedAsset) loadAssetData(state.selectedAsset);
}

// ===== INDICADORES =====
function initIndicatorBar() {
  const bar = document.getElementById('ind-bar');
  bar.innerHTML = INDICATORS_CONFIG.map(ind => `
    <div class="ind-chip ${state.activeIndicators.has(ind.key) ? 'active' : ''}" 
         onclick="toggleIndicator('${ind.key}')">${ind.label}</div>
  `).join('');
}

function toggleIndicator(key) {
  if (state.activeIndicators.has(key)) state.activeIndicators.delete(key);
  else state.activeIndicators.add(key);
  initIndicatorBar();
  if (state.candles.length > 0) renderIndicatorsOnChart();
}

// ===== LISTA DE ATIVOS =====
function populateAssetList() {
  const assets = DataLayer.getAssetList();
  const keys = Object.keys(assets);
  document.getElementById('asset-count').textContent = keys.length;
  renderAssetList(keys);

  // Buscar quotes em background
  keys.slice(0, 10).forEach(key => {
    DataLayer.getQuote(key).then(q => {
      if (q) updateAssetItemPrice(key, q);
    }).catch(() => {});
  });

  // ── [BUG-1 FIX] Auto-selecionar primeiro ativo (BTC/USDT) ──────────────────
  // Sem isso, o gráfico nunca renderiza até o usuário clicar manualmente.
  // Aguarda 1 tick para garantir que o DOM da lista já foi pintado antes do fetch.
  const defaultAsset = keys.find(k => k === 'BTC/USDT') || keys[0];
  if (defaultAsset) {
    setTimeout(() => selectAsset(defaultAsset), 0);
  }
  // ────────────────────────────────────────────────────────────────────────────
}

function renderAssetList(keys) {
  const assets = DataLayer.getAssetList();
  const container = document.getElementById('asset-list');
  container.innerHTML = keys.map(key => {
    const a = assets[key];
    const typeMap = { crypto: '🪙 Cripto', b3: '🇧🇷 B3', forex: '💱 Forex', index: '📊 Índice', commodity: '🛢 Commodity' };
    return `
      <div class="asset-item ${state.selectedAsset === key ? 'active' : ''}" 
           id="ai-${key.replace(/\//g,'_')}" onclick="selectAsset('${key}')">
        <div>
          <div class="asset-name">${key}</div>
          <div class="asset-type">${typeMap[a.type] || a.type}</div>
        </div>
        <div class="asset-change" id="ach-${key.replace(/\//g,'_')}">--</div>
      </div>
    `;
  }).join('');
}

function updateAssetItemPrice(key, q) {
  const el = document.getElementById(`ach-${key.replace(/\//g,'_')}`);
  if (!el) return;
  const ch = q.change || 0;
  el.textContent = `${ch >= 0 ? '+' : ''}${ch.toFixed(2)}%`;
  el.className = `asset-change ${ch >= 0 ? 'up' : 'down'}`;
}

function filterAssets() {
  const q = document.getElementById('asset-search').value.toLowerCase();
  const keys = Object.keys(DataLayer.getAssetList()).filter(k => k.toLowerCase().includes(q));
  renderAssetList(keys);
}

// ===== SELECIONAR ATIVO =====
/* ═══════════════════════════════════════════════════════════════════════════
   BLOCO C — selectAsset() com limpeza de stream anterior
   Substitui a função selectAsset() existente integralmente.
   ═══════════════════════════════════════════════════════════════════════════ */
 
async function selectAsset(assetKey) {
  if (!ASSETS[assetKey]) return;
 
  // Para stream do ativo anterior antes de trocar
  _stopAllStreams();
 
  // Atualiza estado e UI
  state.selectedAsset = assetKey;
 
  // Marca botão ativo na sidebar
  document.querySelectorAll('.asset-btn').forEach(btn => {
    btn.classList.toggle('active', btn.dataset.asset === assetKey);
  });
 
  // Atualiza título do painel
  const titleEl = document.getElementById('asset-title');
  if (titleEl) titleEl.textContent = ASSETS[assetKey].label || assetKey;
 
  // Reseta badge enquanto carrega
  _setRtBadge('connecting');
 
  // Carrega histórico + inicia stream
  await updateChart();
 
  // Dispara análise IA em paralelo (não bloqueia o gráfico)
  if (typeof runAnalysis === 'function') {
    runAnalysis().catch(err => console.warn('[AI] Análise falhou:', err));
  }
}
 

async function loadAssetData(key) {
  showChartLoading(true);
  try {
    const [candles, quote, news] = await Promise.all([
      DataLayer.getCandles(key, state.selectedTF, 150),
      DataLayer.getQuote(key),
      DataLayer.getNews(key),
    ]);

    state.candles = candles;
    state.quote = quote;
    state.news = news;

    if (candles && candles.length > 0) {
      updateChart(candles);
      updateQuoteDisplay(key, quote);
    }

    // Análise técnica e padrões
    state.techAnalysis = TechnicalEngine.analyze(candles);
    state.patternResult = CandlePatterns.detectAll(candles, state.techAnalysis?.trend);

    // Auto-detectar contexto nos fatores externos
    ExternalFactors.autoDetectContext(quote, candles, DataLayer.ASSETS[key]?.type);
    ExternalFactors.injectNews(news);

    // Render resultados
    renderIndicatorsGrid();
    renderPatternsPanel();
    renderFactorsPanel();
    renderSRLevels();
    renderNewsPanel();
    updateConfluenceDisplay();
    updateAssetItemPrice(key, quote || { change: 0 });

  } catch (err) {
    showToast('Erro ao carregar dados: ' + err.message, 'error');
  } finally {
    showChartLoading(false);
  }
}

// ===== CHART RENDER =====
async function updateChart() {
  if (!state.selectedAsset || !state.candleSeries) return;
 
  const { symbol } = ASSETS[state.selectedAsset] || {};
  if (!symbol) return;
 
  try {
    // Busca histórico completo (REST)
    const candles = await DataLayer.getCandles(symbol, state.selectedTF);
    if (!candles || candles.length === 0) return;
 
    // Normaliza timestamps (fix Bug 2 — toSec universal)
    const normalized = candles.map(c => ({
      time  : toSec(c.time),
      open  : c.open,
      high  : c.high,
      low   : c.low,
      close : c.close,
    }));
 
    state.candles = normalized;
    state.candleSeries.setData(normalized);
 
    // Atualiza indicadores (volume, EMA, Bollinger, SAR…)
    if (typeof updateIndicators === 'function') updateIndicators(normalized);
 
    // Posiciona view no candle mais recente
    state.chart.timeScale().scrollToRealTime();
 
    // ── Inicia stream em tempo real ───────────────────────────────────────
    _stopAllStreams();
    _startRealtime(state.selectedAsset, state.selectedTF);
 
  } catch (err) {
    console.error('[CHART] Erro ao carregar candles:', err);
  }
}
 
/**
 * Inicia WebSocket Binance (se suportado) ou polling REST como fallback.
 */
function _startRealtime(assetKey, interval) {
  const asset  = ASSETS[assetKey];
  if (!asset) return;
 
  const { symbol } = asset;
 
  // ── Caminho 1: WebSocket Binance (crypto com USDT/BTC/ETH/BNB) ───────────
  if (typeof RealtimeStream !== 'undefined' && RealtimeStream.isSupported(symbol)) {
    RealtimeStream.start(
      symbol,
      interval,
 
      // onTick — chamado a cada frame Binance (milissegundos)
      (tick) => {
        if (!state.candleSeries) return;
 
        // lightweight-charts.update() é inteligente:
        //   • mesmo timestamp → atualiza a vela existente
        //   • timestamp novo  → acrescenta nova vela
        state.candleSeries.update({
          time : tick.time,
          open : tick.open,
          high : tick.high,
          low  : tick.low,
          close: tick.close,
        });
 
        // Atualiza volume series se existir
        if (state.volumeSeries) {
          state.volumeSeries.update({
            time : tick.time,
            value: tick.volume,
            color: tick.close >= tick.open
              ? 'rgba(38,166,154,0.5)'
              : 'rgba(239,83,80,0.5)',
          });
        }
 
        // Atualiza preço no header a cada tick ao vivo
        _updateLivePrice(tick.close, symbol);
      },
 
      // onStatus — badge visual no painel
      _setRtBadge
    );
 
    return; // WebSocket ativo — não usa polling
  }
 
  // ── Caminho 2: Polling REST para ativos sem WebSocket Binance ─────────────
  _setRtBadge('polling');
  console.log(`[RT] Polling REST ${rtState.POLL_MS}ms para ${symbol}`);
 
  rtState.pollTimer = setInterval(async () => {
    try {
      const candles = await DataLayer.getCandles(symbol, interval, 2); // só últimas 2 velas
      if (!candles || candles.length === 0 || !state.candleSeries) return;
 
      const last = candles[candles.length - 1];
      state.candleSeries.update({
        time : toSec(last.time),
        open : last.open,
        high : last.high,
        low  : last.low,
        close: last.close,
      });
 
      _updateLivePrice(last.close, symbol);
    } catch (_) {}
  }, rtState.POLL_MS);
}
 
/**
 * Atualiza preço ao vivo no elemento #live-price (se existir no HTML).
 */
function _updateLivePrice(price, symbol) {
  const el = document.getElementById('live-price');
  if (!el) return;
 
  const fmt = new Intl.NumberFormat('en-US', {
    style                : 'currency',
    currency             : 'USD',
    minimumFractionDigits: price < 1 ? 6 : 2,
    maximumFractionDigits: price < 1 ? 6 : 2,
  });
 
  el.textContent = fmt.format(price);
  el.classList.add('price-flash'); // adiciona classe CSS de flash (opcional)
  setTimeout(() => el.classList.remove('price-flash'), 300);
}
  // ────────────────────────────────────────────────────────────────────────────

  state.candleSeries.setData(data);
  state.volumeSeries.setData(volData);
  state.chartInstance.timeScale().fitContent();
  renderIndicatorsOnChart();
}

function renderIndicatorsOnChart() {
  // Limpar indicadores antigos
  for (const [key, series] of Object.entries(state.indicatorSeries)) {
    try {
      if (key === 'bb') {
        series.upper?.remove?.(); series.mid?.remove?.(); series.lower?.remove?.();
      } else if (key === 'sar') {
        series.forEach?.(s => s.remove?.());
      } else {
        series.remove?.();
      }
    } catch { /* já removido */ }
  }
  state.indicatorSeries = {};

  if (!state.techAnalysis || !state.candles.length) return;

  const closes = state.candles.map(c => c.close);

  // ── [BUG-2 FIX] toSec() também nos indicadores ────────────────────────────
  const toTimeSeries = (arr) => state.candles
    .map((c, i) => arr[i] != null ? { time: toSec(c.time), value: arr[i] } : null)
    .filter(Boolean)
    .filter(p => p.time > 0);
  // ────────────────────────────────────────────────────────────────────────────

  const addLine = (data, color, lineWidth = 1, lineStyle = 0) => {
    const s = state.chartInstance.addLineSeries({ color, lineWidth, lineStyle, priceLineVisible: false, lastValueVisible: false });
    s.setData(data);
    return s;
  };

  if (state.activeIndicators.has('sma9')) {
    const d = TechnicalEngine.sma(closes, 9);
    state.indicatorSeries['sma9'] = addLine(toTimeSeries(d), '#2962ff');
  }
  if (state.activeIndicators.has('sma21')) {
    const d = TechnicalEngine.sma(closes, 21);
    state.indicatorSeries['sma21'] = addLine(toTimeSeries(d), '#00e5ff');
  }
  if (state.activeIndicators.has('sma50')) {
    const d = TechnicalEngine.sma(closes, 50);
    state.indicatorSeries['sma50'] = addLine(toTimeSeries(d), '#ff9100');
  }
  if (state.activeIndicators.has('sma200')) {
    const d = TechnicalEngine.sma(closes, 200);
    state.indicatorSeries['sma200'] = addLine(toTimeSeries(d), '#ff4081', 1, 2);
  }
  if (state.activeIndicators.has('ema9')) {
    const d = TechnicalEngine.ema(closes, 9);
    state.indicatorSeries['ema9'] = addLine(toTimeSeries(d), '#ae92f5');
  }
  if (state.activeIndicators.has('vwap')) {
    const d = TechnicalEngine.vwap(state.candles);
    state.indicatorSeries['vwap'] = addLine(toTimeSeries(d), '#69f0ae', 1, 1);
  }
  if (state.activeIndicators.has('bb')) {
    const bb = TechnicalEngine.bollingerBands(closes, 20, 2);
    const uSeries = addLine(toTimeSeries(bb.upper), '#546e7a', 1, 2);
    const mSeries = addLine(toTimeSeries(bb.mid), '#546e7a', 1, 1);
    const lSeries = addLine(toTimeSeries(bb.lower), '#546e7a', 1, 2);
    state.indicatorSeries['bb'] = { upper: uSeries, mid: mSeries, lower: lSeries };
  }
  if (state.activeIndicators.has('sar')) {
    const sarData = TechnicalEngine.parabolicSAR(state.candles);
    const bullSAR = state.candles.map((c, i) => sarData[i]?.isLong ? { time: toSec(c.time), value: sarData[i].value } : null).filter(Boolean);
    const bearSAR = state.candles.map((c, i) => sarData[i] && !sarData[i].isLong ? { time: toSec(c.time), value: sarData[i].value } : null).filter(Boolean);
    const s1 = state.chartInstance.addLineSeries({ color: '#69f0ae', lineWidth: 0, pointMarkersVisible: true, lastValueVisible: false });
    const s2 = state.chartInstance.addLineSeries({ color: '#ff4081', lineWidth: 0, pointMarkersVisible: true, lastValueVisible: false });
    s1.setData(bullSAR); s2.setData(bearSAR);
    state.indicatorSeries['sar'] = [s1, s2];
  }

  // Suporte & Resistência como linhas de preço
  if (state.techAnalysis?.srLevels) {
    for (const lv of state.techAnalysis.srLevels.slice(0, 4)) {
      state.candleSeries.createPriceLine({
        price: lv.price,
        color: lv.type === 'support' ? '#00c85355' : '#ff174455',
        lineWidth: 1,
        lineStyle: LightweightCharts.LineStyle.Dashed,
        axisLabelVisible: true,
        title: lv.type === 'support' ? 'S' : 'R',
      });
    }
  }
}

// ===== QUOTE DISPLAY =====
function updateQuoteDisplay(key, quote) {
  if (!quote) return;
  const price = typeof quote.price === 'number' ? quote.price : 0;
  const change = typeof quote.change === 'number' ? quote.change : 0;
  document.getElementById('chart-price').textContent = formatPrice(price, key);
  const chEl = document.getElementById('chart-change');
  chEl.textContent = `${change >= 0 ? '+' : ''}${change.toFixed(2)}%`;
  chEl.className = `badge ${change >= 0 ? 'badge-green' : 'badge-red'}`;
}

function formatPrice(price, key) {
  if (!price) return '--';
  const asset = DataLayer.ASSETS[key];
  if (asset?.type === 'forex') return price.toFixed(4);
  if (price > 1000) return price.toLocaleString('pt-BR', { minimumFractionDigits: 2, maximumFractionDigits: 2 });
  if (price < 1) return price.toFixed(6);
  return price.toFixed(2);
}

// ===== INDICADORES GRID =====
function renderIndicatorsGrid() {
  const ta = state.techAnalysis;
  if (!ta) return;
  const grid = document.getElementById('ind-grid-content');
  const ind = ta.indicators;

  const items = [
    { name: 'RSI(14)', val: ind.rsi?.toFixed(1), cls: ind.rsi < 30 ? 'bull' : ind.rsi > 70 ? 'bear' : 'neutral' },
    { name: 'MACD Hist', val: ind.macd?.hist?.toFixed(4), cls: ind.macd?.hist > 0 ? 'bull' : ind.macd?.hist < 0 ? 'bear' : 'neutral' },
    { name: 'BB Width', val: ind.bb?.width?.toFixed(2) + '%', cls: ind.bb?.width < 2 ? 'strong' : 'neutral' },
    { name: 'VWAP', val: formatPrice(ind.vwap, state.selectedAsset), cls: state.candles.at(-1)?.close > ind.vwap ? 'bull' : 'bear' },
    { name: 'Estoc %K', val: ind.stoch?.k?.toFixed(1), cls: ind.stoch?.k < 20 ? 'bull' : ind.stoch?.k > 80 ? 'bear' : 'neutral' },
    { name: 'ADX', val: ind.adx?.toFixed(1), cls: ind.adx > 25 ? 'strong' : 'neutral' },
    { name: 'Williams %R', val: ind.williams?.toFixed(1), cls: ind.williams < -80 ? 'bull' : ind.williams > -20 ? 'bear' : 'neutral' },
    { name: 'CCI(20)', val: ind.cci?.toFixed(1), cls: ind.cci < -100 ? 'bull' : ind.cci > 100 ? 'bear' : 'neutral' },
    { name: 'SMA9', val: formatPrice(ind.sma9, state.selectedAsset), cls: ind.sma9 > ind.sma21 ? 'bull' : 'bear' },
    { name: 'SMA21', val: formatPrice(ind.sma21, state.selectedAsset), cls: ind.sma9 > ind.sma21 ? 'bull' : 'bear' },
    { name: 'SMA50', val: formatPrice(ind.sma50, state.selectedAsset), cls: state.candles.at(-1)?.close > (ind.sma50 || 0) ? 'bull' : 'bear' },
    { name: 'SAR', val: ind.sar ? (ind.sar.isLong ? '▲ Alta' : '▼ Baixa') : '--', cls: ind.sar?.isLong ? 'bull' : 'bear' },
    { name: 'Tendência', val: ta.trend.toUpperCase(), cls: ta.trend === 'alta' ? 'bull' : ta.trend === 'baixa' ? 'bear' : 'neutral' },
    { name: 'ATR(14)', val: ind.atr?.toFixed(4), cls: 'strong' },
  ];

  grid.innerHTML = items.map(item => `
    <div class="ind-item">
      <span class="ind-name">${item.name}</span>
      <span class="ind-val ${item.cls}">${item.val ?? '--'}</span>
    </div>
  `).join('');
}

// ===== PADRÕES =====
function renderPatternsPanel() {
  const pr = state.patternResult;
  const container = document.getElementById('patterns-content');
  if (!pr || pr.patterns.length === 0) {
    container.innerHTML = '<div class="text-center text-dim text-sm" style="padding:20px">Nenhum padrão significativo detectado nas últimas 5 velas</div>';
    return;
  }
  container.innerHTML = pr.patterns.map(p => `
    <div class="pattern-item">
      <div class="pattern-emoji">${p.emoji}</div>
      <div class="pattern-info">
        <div class="pattern-name">${p.name}</div>
        <div class="pattern-desc">${p.description}</div>
      </div>
      <span class="pattern-rel ${p.reliability >= 80 ? 'high' : p.reliability >= 65 ? 'med' : 'low'}">${p.reliability}%</span>
    </div>
  `).join('');
}

// ===== FATORES EXTERNOS =====
function renderFactorsPanel() {
  const factors = ExternalFactors.getFactors();
  const finalScore = ExternalFactors.calculateFinalScore();
  const container = document.getElementById('factors-panel');
  container.innerHTML = Object.entries(factors).map(([, f]) => {
    const score = f.score;
    const barWidth = Math.min(100, Math.abs(score));
    const barColor = score > 0 ? '#00c853' : score < 0 ? '#ff1744' : '#546e7a';
    return `
      <div class="factor-row">
        <span class="factor-name">${f.label}</span>
        <div class="factor-bar-wrap">
          <div class="factor-bar" style="width:${barWidth}%;background:${barColor}"></div>
        </div>
        <span class="factor-score ${score > 5 ? 'pos' : score < -5 ? 'neg' : 'zero'}">${score.toFixed(0)}</span>
      </div>
    `;
  }).join('') + `
    <div class="divider"></div>
    <div style="display:flex;justify-content:space-between;font-size:12px">
      <span class="text-dim">Score total</span>
      <span class="font-bold ${finalScore.score > 0 ? 'text-green' : finalScore.score < 0 ? 'text-red' : 'text-yellow'}">${finalScore.score.toFixed(1)}</span>
    </div>
  `;
}

// ===== SR LEVELS =====
function renderSRLevels() {
  const ta = state.techAnalysis;
  const container = document.getElementById('sr-panel');
  if (!ta?.srLevels?.length) {
    container.innerHTML = '<div class="text-dim text-sm text-center" style="padding:10px">Dados insuficientes</div>';
    return;
  }
  const price = state.candles.at(-1)?.close || 0;
  container.innerHTML = ta.srLevels.slice(0, 6).map(lv => {
    const dist = Math.abs(lv.price - price) / price * 100;
    return `
      <div class="ind-item" style="margin-bottom:5px">
        <span class="ind-name">${lv.type === 'support' ? '🟢 S' : '🔴 R'} ${formatPrice(lv.price, state.selectedAsset)}</span>
        <span class="ind-val ${lv.type === 'support' ? 'bull' : 'bear'}">${dist.toFixed(2)}%</span>
      </div>
    `;
  }).join('');
}

// ===== CALENDÁRIO =====
function renderCalendarRisk() {
  const risks = ExternalFactors.getCalendarRisk();
  const container = document.getElementById('cal-panel');
  if (!risks.length) {
    container.innerHTML = '<div class="text-dim text-sm" style="padding:10px">Sem eventos de alto risco no momento</div>';
    return;
  }
  container.innerHTML = risks.map(r => `
    <div style="padding:7px 0;border-bottom:1px solid var(--border);font-size:12px">
      <div class="font-bold">${r.event}</div>
      <div class="text-dim text-xs mt-1">${r.note}</div>
      <span class="badge ${r.level === 'alto' ? 'badge-red' : 'badge-yellow'} mt-1">${r.level.toUpperCase()}</span>
    </div>
  `).join('');
}

// ===== CONFLUÊNCIA =====
function updateConfluenceDisplay() {
  const ta = state.techAnalysis;
  const pr = state.patternResult;
  const fs = ExternalFactors.calculateFinalScore();
  const regime = ExternalFactors.detectMarketRegime(state.candles);

  const techNorm = ta ? ((ta.bullScore - ta.bearScore) / (ta.bullScore + ta.bearScore || 1) * 50 + 50) : 50;
  const extNorm = (fs.score + 100) / 2;
  const patNorm = pr ? ((pr.bullScore - pr.bearScore) / (pr.bullScore + pr.bearScore + 0.001) * 50 + 50) : 50;
  const totalNorm = Math.round((techNorm * 0.45 + extNorm * 0.35 + patNorm * 0.20));
  document.getElementById('conf-needle').style.left = `${totalNorm}%`;

  const techDir = ta?.direction || '--';
  const techConf = ta?.confidence || '--';
  document.getElementById('cf-tech').textContent = `${techDir} ${techConf}%`;
  document.getElementById('cf-tech').className = `ind-val ${techDir === 'COMPRA' ? 'bull' : techDir === 'VENDA' ? 'bear' : 'neutral'}`;

  document.getElementById('cf-pat').textContent = pr?.dominant || '--';
  document.getElementById('cf-ext').textContent = `${fs.direction} ${fs.confidence}%`;
  document.getElementById('cf-risk').textContent = fs.riskLevel?.toUpperCase() || '--';
  document.getElementById('cf-risk').className = `ind-val ${fs.riskLevel === 'extremo' ? 'bear' : fs.riskLevel === 'alto' ? 'neutral' : 'bull'}`;

  const regimeMap = { tendencia_alta: '📈 Tendência Alta', tendencia_baixa: '📉 Tendência Baixa', volatil: '⚡ Volátil', lateral: '↔️ Lateral', desconhecido: '❓ Desconhecido' };
  document.getElementById('regime-badge').textContent = regimeMap[regime.regime] || regime.regime;
}

// ===== NOTÍCIAS =====
function renderNewsPanel() {
  const container = document.getElementById('news-content');
  if (!state.news?.length) {
    container.innerHTML = '<div class="text-dim text-sm text-center" style="padding:20px">Nenhuma notícia encontrada</div>';
    return;
  }
  container.innerHTML = state.news.map(n => `
    <div class="news-item">
      <div class="news-title">${n.title}</div>
      <div class="news-meta">
        <span class="news-source">${n.source}</span>
        <span class="news-sent ${n.sentiment}">${n.sentiment === 'positive' ? '🟢 Positivo' : n.sentiment === 'negative' ? '🔴 Negativo' : '⚪ Neutro'}</span>
      </div>
    </div>
  `).join('');
}

function buildExecutionGateReport(context) {
  const quality = DataLayer.getDataQuality(state.selectedAsset, state.selectedTF) || {};
  const hasApiKey = !!AIEngine.getApiKey();

  const checks = {
    data: {
      ok: !!quality.candlesReal && !!quality.quoteReal && !!quality.newsReal && state.candles.length >= 80 && Number.isFinite(state.quote?.price),
      details: `candles=${quality.candlesSource || 'unknown'}, quote=${quality.quoteSource || 'unknown'}, news=${quality.newsSource || 'unknown'}`,
    },
    strategy: {
      ok: !!context.technicalDirection && Number.isFinite(context.technicalConfidence) && Number.isFinite(context.patternConfidence),
      details: `technical=${context.technicalDirection || 'na'}, confidence=${context.technicalConfidence ?? 'na'}, pattern=${context.patternConfidence ?? 'na'}`,
    },
    risk: {
      ok: context.riskLevel !== 'extremo' && (context.externalConfidence ?? 0) >= 55,
      details: `riskLevel=${context.riskLevel || 'na'}, externalConfidence=${context.externalConfidence ?? 'na'}`,
    },
    compliance: {
      ok: hasApiKey,
      details: hasApiKey ? 'IA real habilitada' : 'Groq ausente',
    },
  };

  const failures = Object.entries(checks)
    .filter(([, v]) => !v.ok)
    .map(([layer, v]) => ({ layer, details: v.details }));

  return {
    allowed: failures.length === 0,
    checks,
    failures,
  };
}

function renderGateBlock(report) {
  const html = `
    <div class="signal-box wait">
      <div class="signal-label">Execucao bloqueada por governanca</div>
      <div class="signal-main">BLOQUEADO</div>
      <div class="text-xs text-dim" style="margin-top:8px">Falhas encontradas nas camadas obrigatorias:</div>
      <ul style="margin-top:8px;padding-left:16px;font-size:12px;line-height:1.6;color:var(--text2)">
        ${report.failures.map(f => `<li><strong>${f.layer}</strong>: ${f.details}</li>`).join('')}
      </ul>
    </div>
  `;
  document.getElementById('signal-content').innerHTML = html;
  document.getElementById('signal-content').style.display = 'block';
  document.getElementById('signal-loading').style.display = 'none';
  document.getElementById('ai-reasoning-content').innerHTML = '<div class="text-dim text-sm" style="padding:20px">Analise bloqueada ate regularizar todas as camadas de validacao.</div>';
}

// ===== ANÁLISE COMPLETA =====
async function runFullAnalysis() {
  if (!state.selectedAsset) { showToast('Selecione um ativo primeiro', 'error'); return; }
  if (!state.candles.length) { showToast('Aguarde os dados carregarem', 'error'); return; }

  document.getElementById('signal-loading').style.display = 'flex';
  document.getElementById('signal-content').style.display = 'none';

  try {
    const context = ExternalFactors.buildAIContext(
      state.selectedAsset,
      state.techAnalysis,
      state.patternResult,
      state.quote
    );

    const gate = buildExecutionGateReport(context);
    if (!gate.allowed) {
      renderGateBlock(gate);
      showToast('Execucao bloqueada: validacao por camadas reprovada', 'error');
      return;
    }

    const signal = await AIEngine.analyze(context, true, { requireAI: true, blockFallback: true });
    state.lastSignal = signal;

    renderSignal(signal);
    renderAIReasoning(signal);
    renderHistoryPanel();
    updateLearningStats();
    showToast(`Sinal gerado: ${signal.signal} (${signal.confidence}%)`, signal.signal.includes('COMPRA') ? 'success' : signal.signal.includes('VENDA') ? 'error' : 'info');

    document.getElementById('signal-source').textContent = signal.source === 'groq' ? '🤖 Groq IA' : '🚫 Invalido';

  } catch (err) {
    showToast('Erro na análise: ' + err.message, 'error');
    document.getElementById('signal-content').style.display = 'block';
    document.getElementById('signal-loading').style.display = 'none';
  }
}

function renderSignal(signal) {
  const isCompra = signal.signal?.includes('COMPRA');
  const isVenda = signal.signal?.includes('VENDA');
  const boxClass = isCompra ? 'buy' : isVenda ? 'sell' : 'wait';
  const confColor = isCompra ? 'var(--green)' : isVenda ? 'var(--red)' : 'var(--yellow)';

  const html = `
    <div class="signal-box ${boxClass}">
      <div class="signal-label">Sinal ${state.selectedAsset} · ${state.selectedTF}</div>
      <div class="signal-main">${signal.signal}</div>
      <div class="signal-conf">
        <span class="font-bold">${signal.confidence}%</span>
        <div class="conf-bar">
          <div class="conf-fill" style="width:${signal.confidence}%;background:${confColor}"></div>
        </div>
        <span class="text-dim text-xs">confiança</span>
      </div>
      ${signal.recommendedSize ? `<div class="text-xs text-dim mt-1">📊 Tamanho recomendado: <strong class="text-accent">${signal.recommendedSize} do capital</strong></div>` : ''}
      <div class="signal-levels">
        <div class="level-item">
          <div class="lk">🎯 Entrada</div>
          <div class="lv entry">${signal.entry}</div>
        </div>
        <div class="level-item">
          <div class="lk">🛑 Stop Loss</div>
          <div class="lv stop">${signal.stopLoss}</div>
        </div>
        <div class="level-item">
          <div class="lk">✅ Take Profit 1</div>
          <div class="lv tp">${signal.takeProfit1}</div>
        </div>
        <div class="level-item">
          <div class="lk">🏆 Take Profit 2</div>
          <div class="lv tp">${signal.takeProfit2 || '--'}</div>
        </div>
        <div class="level-item">
          <div class="lk">📐 Risco/Retorno</div>
          <div class="lv">${signal.riskReward}</div>
        </div>
        <div class="level-item">
          <div class="lk">⏱ Validade</div>
          <div class="lv">${signal.timeframeValidity || '--'}</div>
        </div>
      </div>
      ${signal.systemicRisk ? `
        <div style="margin-top:10px">
          <div class="text-xs text-dim">Risco Sistêmico</div>
          <div style="height:5px;background:var(--bg4);border-radius:3px;margin-top:4px;overflow:hidden">
            <div style="height:100%;width:${signal.systemicRisk}%;background:${signal.systemicRisk > 65 ? 'var(--red)' : signal.systemicRisk > 40 ? 'var(--yellow)' : 'var(--green)'};border-radius:3px"></div>
          </div>
          <div class="text-xs text-dim mt-1">${signal.systemicRisk}%</div>
        </div>
      ` : ''}
    </div>
  `;

  document.getElementById('signal-content').innerHTML = html;
  document.getElementById('signal-content').style.display = 'block';
  document.getElementById('signal-loading').style.display = 'none';
}

// ===== RACIOCÍNIO IA =====
function renderAIReasoning(signal) {
  const container = document.getElementById('ai-reasoning-content');
  let html = '';

  if (signal.reasoning) {
    html += `<div class="ai-box">`;
    signal.reasoning.split('\n').filter(Boolean).forEach(p => {
      html += `<p>${p}</p>`;
    });
    html += `</div>`;
  }

  if (signal.keyFactors?.length) {
    html += `<div style="margin-top:10px"><div class="text-xs text-dim" style="margin-bottom:6px">FATORES CHAVE</div>`;
    signal.keyFactors.forEach(f => {
      html += `<div class="key-factor">▶ ${f}</div>`;
    });
    html += `</div>`;
  }

  if (signal.warnings?.length) {
    html += `<div style="margin-top:10px">`;
    signal.warnings.forEach(w => {
      html += `<div class="ai-warning">⚠️ ${w}</div>`;
    });
    html += `</div>`;
  }

  if (signal.alternatives) {
    html += `<div style="margin-top:10px;padding:10px;background:var(--bg3);border-radius:8px;font-size:12px">
      <span class="text-dim">Cenário alternativo:</span> ${signal.alternatives}
    </div>`;
  }

  container.innerHTML = html || '<div class="text-dim text-sm" style="padding:20px">Análise não disponível</div>';
}

// ===== HISTÓRICO =====
function renderHistoryPanel() {
  const history = AIEngine.getHistory();
  const container = document.getElementById('history-content');
  if (!history.length) {
    container.innerHTML = '<div class="text-dim text-sm text-center" style="padding:20px">Nenhum sinal ainda</div>';
    return;
  }
  container.innerHTML = history.slice(0, 30).map(h => {
    const isCompra = h.signal?.includes('COMPRA');
    const isVenda = h.signal?.includes('VENDA');
    const sigClass = isCompra ? 'buy' : isVenda ? 'sell' : 'wait';
    const outcomeMap = { acerto: { cls: 'hit', label: '✅ Acerto' }, erro: { cls: 'miss', label: '❌ Erro' }, null: { cls: 'pend', label: '⏱ Pendente' } };
    const oc = outcomeMap[h.outcome] || outcomeMap[null];
    const time = new Date(h.timestamp).toLocaleString('pt-BR', { day:'2-digit', month:'2-digit', hour:'2-digit', minute:'2-digit' });
    return `
      <div class="history-item" onclick="showHistoryMenu(${h.id})">
        <span class="hist-signal ${sigClass}">${h.signal}</span>
        <div class="hist-info">
          <div class="hist-asset">${h.asset}</div>
          <div class="hist-time">${time} · ${h.confidence}%</div>
        </div>
        <span class="hist-outcome ${oc.cls}">${oc.label}</span>
      </div>
    `;
  }).join('');
}

function showHistoryMenu(id) {
  const h = AIEngine.getHistory().find(e => e.id === id);
  if (!h || h.outcome) return;
  const result = confirm(`Sinal: ${h.signal}\nAtivo: ${h.asset}\n\nEste sinal se concretizou?\nOK = Acerto | Cancelar = Erro`);
  const outcome = result ? 'acerto' : 'erro';
  const exitPrice = prompt('Informe o preço de saída (opcional):', '');
  AIEngine.recordOutcome(id, outcome, exitPrice ? parseFloat(exitPrice) : null);
  renderHistoryPanel();
  updateLearningStats();
  showToast(result ? '✅ Acerto registrado' : '❌ Erro registrado', result ? 'success' : 'error');
}

// ===== LEARNING STATS =====
function updateLearningStats() {
  const stats = AIEngine.getStats();
  document.getElementById('hd-acc').textContent = stats.total > 0 ? `${stats.accuracy}%` : '--';
  document.getElementById('hd-total').textContent = stats.total;
  document.getElementById('hd-hits').textContent = stats.hits;
  document.getElementById('hd-miss').textContent = stats.misses;
  document.getElementById('learn-acc').textContent = stats.total > 0 ? `${stats.accuracy}%` : '--%';
  document.getElementById('learn-total').textContent = stats.total;
  document.getElementById('learn-hits').textContent = stats.hits;
  document.getElementById('learn-miss').textContent = stats.misses;
  const history = AIEngine.getHistory();
  const pending = history.filter(h => h.outcome === null).length;
  document.getElementById('learn-pend').textContent = pending;
}

// ===== PESOS =====
function initWeightsPanel() {
  const weights = ExternalFactors.getWeights();
  const labels = {
    macro_usa: '🇺🇸 Macro EUA',
    macro_br: '🇧🇷 Macro Brasil',
    geopolitico: '🌍 Geopolítica',
    sentimento: '😰 Sentimento',
    institucional: '🏦 Institucional',
    algoritmos: '🤖 Algoritmos',
    noticias: '📰 Notícias',
    fundamentalista: '📘 Fundamentalista',
  };
  const container = document.getElementById('weights-panel');
  container.innerHTML = Object.entries(weights).map(([k, v]) => `
    <div class="weight-item">
      <span class="weight-label">${labels[k] || k}</span>
      <input type="number" class="weight-input" id="w-${k}" value="${v}" min="0" max="100" 
             onchange="applyWeights()">
    </div>
  `).join('') + `
    <div class="text-xs text-dim mt-2">Pesos são proporcionais — soma não precisa ser 100</div>
  `;
}

function applyWeights() {
  const labels = ['macro_usa','macro_br','geopolitico','sentimento','institucional','algoritmos','noticias','fundamentalista'];
  const newWeights = {};
  for (const k of labels) {
    const inp = document.getElementById(`w-${k}`);
    if (inp) newWeights[k] = parseFloat(inp.value) || 0;
  }
  ExternalFactors.setWeights(newWeights);
  renderFactorsPanel();
  updateConfluenceDisplay();
}

function resetWeights() {
  ExternalFactors.resetFactors();
  initWeightsPanel();
  renderFactorsPanel();
  updateConfluenceDisplay();
  showToast('Pesos resetados', 'info');
}

// ===== MODAL FATORES =====
function editFactors() {
  const modal = document.getElementById('factors-modal');
  const content = document.getElementById('factors-modal-content');
  const factors = ExternalFactors.getFactors();
  const scoreMap = { bullish: 60, positivo: 60, crescendo: 40, neutro: 0, caindo: -40, bearish: -60, negativo: -60, alto: -40 };

  content.innerHTML = Object.entries(factors).map(([catKey, cat]) => `
    <div style="margin-bottom:16px">
      <div class="font-bold text-sm" style="margin-bottom:8px">${cat.label}</div>
      ${cat.items.map((item, idx) => `
        <div style="display:flex;align-items:center;gap:8px;margin-bottom:6px;font-size:12px">
          <span style="flex:1;color:var(--text2)">${item.name}</span>
          <select class="api-input" style="width:140px;cursor:pointer" 
                  onchange="updateFactor('${catKey}',${idx},this.value,${JSON.stringify(scoreMap)})">
            ${['bullish','positivo','crescendo','neutro','caindo','negativo','bearish'].map(opt => 
              `<option value="${opt}" ${item.value === opt ? 'selected' : ''}>${opt}</option>`
            ).join('')}
          </select>
          <span class="font-bold" style="width:36px;text-align:right;${item.score > 0 ? 'color:var(--green2)' : item.score < 0 ? 'color:var(--red2)' : 'color:var(--text3)'}">${item.score}</span>
        </div>
      `).join('')}
    </div>
    <div class="divider"></div>
  `).join('');

  modal.style.display = 'block';
}

function updateFactor(catKey, idx, value, scoreMap) {
  const score = scoreMap[value] ?? 0;
  ExternalFactors.setFactor(catKey, idx, value, score);
  renderFactorsPanel();
  updateConfluenceDisplay();
}

function closeFactorsModal() {
  document.getElementById('factors-modal').style.display = 'none';
}

// ===== API KEY =====
function loadApiKeyFromStorage() {
  const saved = localStorage.getItem('uniia_groq_key');
  if (saved) {
    document.getElementById('api-key').value = saved;
    AIEngine.setApiKey(saved);
    updateApiStatus('ok');
  }
}

function toggleApiKey() {
  const inp = document.getElementById('api-key');
  inp.type = inp.type === 'password' ? 'text' : 'password';
}

async function testApiKey() {
  const key = document.getElementById('api-key').value.trim();
  if (!key) { showToast('Insira uma API key', 'error'); return; }
  AIEngine.setApiKey(key);
  try {
    const res = await fetch('https://api.groq.com/openai/v1/models', {
      headers: { 'Authorization': `Bearer ${key}` }
    });
    if (res.ok) {
      localStorage.setItem('uniia_groq_key', key);
      updateApiStatus('ok');
      showToast('✅ Groq conectada com sucesso!', 'success');
    } else {
      updateApiStatus('err');
      showToast('❌ Chave inválida', 'error');
    }
  } catch {
    updateApiStatus('err');
    showToast('Erro de conexão com Groq', 'error');
  }
}

function changeModel() {
  const m = document.getElementById('model-select').value;
  AIEngine.setModel(m);
  document.getElementById('hd-model').textContent = m.split('-').slice(0,2).join('-');
}

function updateApiStatus(status) {
  const badge = document.getElementById('ai-status-badge');
  const msg = document.getElementById('api-status-msg');
  if (status === 'ok') {
    badge.textContent = 'Conectada';
    badge.className = 'badge badge-green';
    msg.className = 'api-status ok';
    msg.textContent = '✅ Groq ativa — análise com IA habilitada';
  } else if (status === 'err') {
    badge.textContent = 'Erro';
    badge.className = 'badge badge-red';
    msg.className = 'api-status err';
    msg.textContent = '❌ Chave inválida ou expirada';
  } else {
    badge.textContent = 'Desconectada';
    badge.className = 'badge badge-gray';
    msg.className = 'api-status none';
    msg.textContent = '⚠ Cole sua chave Groq gratuita acima';
  }
}

// ===== REFRESH =====
async function refreshData() {
  if (state.selectedAsset) {
    await loadAssetData(state.selectedAsset);
    showToast('Dados atualizados', 'info');
  }
}

// ===== TABS =====
function switchTab(tab) {
  document.querySelectorAll('#detail-tabs .tab').forEach((el, i) => {
    const ids = ['indicators','patterns','ai-reasoning','news','history'];
    el.classList.toggle('active', ids[i] === tab);
  });
  document.querySelectorAll('.tab-content').forEach(el => {
    el.classList.toggle('active', el.id === `tab-${tab}`);
  });
}

// ===== LOADING =====
function showChartLoading(show) {
  document.getElementById('chart-loading').style.display = show ? 'flex' : 'none';
}

// ===== TOAST =====
function showToast(msg, type = 'info') {
  const container = document.getElementById('toast');
  const el = document.createElement('div');
  el.className = `toast-item ${type}`;
  el.textContent = msg;
  container.appendChild(el);
  setTimeout(() => { el.style.opacity = '0'; el.style.transition = 'opacity 0.3s'; setTimeout(() => el.remove(), 300); }, 3500);
}

// ===== AUTO-REFRESH A CADA 60s =====
setInterval(() => {
  if (state.selectedAsset) {
    DataLayer.getQuote(state.selectedAsset).then(q => {
      if (q) { state.quote = q; updateQuoteDisplay(state.selectedAsset, q); }
    }).catch(() => {});
    renderCalendarRisk();
  }
}, 60000);
