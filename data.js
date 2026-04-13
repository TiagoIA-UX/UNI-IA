/**
 * DATA.JS — Camada de dados: APIs reais + fallback inteligente
 * Binance (cripto), BRAPI (B3), Yahoo Finance via proxy, Frankfurter (câmbio)
 */

const DataLayer = (() => {
  // Cache de dados buscados
  const cache = new Map();
  const CACHE_TTL = 60_000; // 1 minuto
  const dataQuality = new Map();
  const STRICT_REAL_DATA = true;

  function qualityKey(assetKey, timeframe) {
    return `${assetKey || 'unknown'}::${timeframe || 'na'}`;
  }

  function updateQuality(assetKey, timeframe, patch) {
    const key = qualityKey(assetKey, timeframe);
    const prev = dataQuality.get(key) || {
      assetKey,
      timeframe,
      candlesReal: false,
      quoteReal: false,
      newsReal: false,
      candlesSource: 'unknown',
      quoteSource: 'unknown',
      newsSource: 'unknown',
      updatedAt: Date.now(),
    };
    dataQuality.set(key, { ...prev, ...patch, updatedAt: Date.now() });
  }

  // ===== CONFIG DE ATIVOS =====
  const ASSETS = {
    // Cripto — Binance API pública (sem chave)
    'BTC/USDT': { type: 'crypto', symbol: 'BTCUSDT', base: 'BTC', quote: 'USDT' },
    'ETH/USDT': { type: 'crypto', symbol: 'ETHUSDT', base: 'ETH', quote: 'USDT' },
    'BNB/USDT': { type: 'crypto', symbol: 'BNBUSDT', base: 'BNB', quote: 'USDT' },
    'SOL/USDT': { type: 'crypto', symbol: 'SOLUSDT', base: 'SOL', quote: 'USDT' },
    'XRP/USDT': { type: 'crypto', symbol: 'XRPUSDT', base: 'XRP', quote: 'USDT' },
    // B3 — BRAPI (token público, limite de chamadas)
    'PETR4':   { type: 'b3', symbol: 'PETR4', sector: 'energia' },
    'VALE3':   { type: 'b3', symbol: 'VALE3', sector: 'mineracao' },
    'ITUB4':   { type: 'b3', symbol: 'ITUB4', sector: 'financeiro' },
    'BBDC4':   { type: 'b3', symbol: 'BBDC4', sector: 'financeiro' },
    'WEGE3':   { type: 'b3', symbol: 'WEGE3', sector: 'industria' },
    'MGLU3':   { type: 'b3', symbol: 'MGLU3', sector: 'comercio' },
    'BBAS3':   { type: 'b3', symbol: 'BBAS3', sector: 'financeiro' },
    'EGIE3':   { type: 'b3', symbol: 'EGIE3', sector: 'energia' },
    // Forex — via Frankfurter (gratuito)
    'EUR/USD': { type: 'forex', base: 'EUR', quote: 'USD' },
    'USD/BRL': { type: 'forex', base: 'USD', quote: 'BRL' },
    'GBP/USD': { type: 'forex', base: 'GBP', quote: 'USD' },
    // Índices/Commodities — simulado com base em benchmark
    'IBOV':   { type: 'index', symbol: 'IBOV' },
    'SP500':  { type: 'index', symbol: 'SPX' },
    'OURO':   { type: 'commodity', symbol: 'GOLD' },
    'PETRO':  { type: 'commodity', symbol: 'OIL' },
  };

  // Intervalos Binance para cada timeframe
  const TF_BINANCE = {
    '5m': '5m', '15m': '15m', '1h': '1h', '4h': '4h', '1d': '1d', '1w': '1w'
  };

  // ===== BINANCE KLINES =====
  async function fetchBinanceKlines(symbol, interval, limit = 100) {
    const key = `binance_${symbol}_${interval}`;
    if (cache.has(key)) {
      const entry = cache.get(key);
      if (Date.now() - entry.ts < CACHE_TTL) return entry.data;
    }
    try {
      const url = `https://api.binance.com/api/v3/klines?symbol=${symbol}&interval=${interval}&limit=${limit}`;
      const res = await fetch(url);
      if (!res.ok) throw new Error('Binance error');
      const raw = await res.json();
      const candles = raw.map(k => ({
        time: k[0],
        open: parseFloat(k[1]),
        high: parseFloat(k[2]),
        low: parseFloat(k[3]),
        close: parseFloat(k[4]),
        volume: parseFloat(k[5]),
        closeTime: k[6],
      }));
      cache.set(key, { ts: Date.now(), data: candles });
      return candles;
    } catch (err) {
      if (STRICT_REAL_DATA) {
        throw new Error(`Falha ao obter candles reais da Binance para ${symbol}/${interval}: ${err.message || err}`);
      }
      return generateSimulatedCandles(symbol, limit, interval);
    }
  }

  // ===== BINANCE TICKER =====
  async function fetchBinanceTicker(symbol) {
    try {
      const res = await fetch(`https://api.binance.com/api/v3/ticker/24hr?symbol=${symbol}`);
      if (!res.ok) throw new Error();
      return await res.json();
    } catch {
      return null;
    }
  }

  // ===== BRAPI B3 =====
  async function fetchBRAPI(symbol, interval = '1d', range = '3mo') {
    const key = `brapi_${symbol}_${interval}`;
    if (cache.has(key)) {
      const entry = cache.get(key);
      if (Date.now() - entry.ts < CACHE_TTL) return entry.data;
    }
    try {
      const url = `https://brapi.dev/api/quote/${symbol}?interval=${interval}&range=${range}&fundamental=true`;
      const res = await fetch(url);
      if (!res.ok) throw new Error();
      const json = await res.json();
      const q = json.results?.[0];
      if (!q) throw new Error('sem resultado');
      
      // Montar candles dos históricos
      const prices = q.historicalDataPrice || [];
      const candles = prices.map(p => ({
        time: p.date * 1000,
        open: p.open ?? p.close,
        high: p.high ?? p.close,
        low: p.low ?? p.close,
        close: p.close,
        volume: p.volume ?? 0,
      })).filter(c => c.close);

      const data = {
        candles,
        price: q.regularMarketPrice,
        change: q.regularMarketChangePercent,
        volume: q.regularMarketVolume,
        marketCap: q.marketCap,
        pe: q.priceEarningsRatio,
        pb: q.priceToBook,
        roe: q.returnOnEquity,
        dy: q.dividendYield,
        eps: q.epsCurrentYear,
        symbol: q.symbol,
        shortName: q.shortName,
        sector: q.sector,
      };
      cache.set(key, { ts: Date.now(), data });
      return data;
    } catch (err) {
      if (STRICT_REAL_DATA) {
        throw new Error(`Falha ao obter dados reais da BRAPI para ${symbol}: ${err.message || err}`);
      }
      return generateSimulatedB3(symbol, interval);
    }
  }

  // ===== FRANKFURTER FOREX =====
  async function fetchForex(base, quote, days = 100) {
    const key = `forex_${base}_${quote}`;
    if (cache.has(key)) {
      const entry = cache.get(key);
      if (Date.now() - entry.ts < CACHE_TTL) return entry.data;
    }
    try {
      const endDate = new Date().toISOString().split('T')[0];
      const startDate = new Date(Date.now() - days * 86400000).toISOString().split('T')[0];
      const url = `https://api.frankfurter.app/${startDate}..${endDate}?from=${base}&to=${quote}`;
      const res = await fetch(url);
      if (!res.ok) throw new Error();
      const json = await res.json();
      const dates = Object.keys(json.rates).sort();
      const candles = dates.map((d, i) => {
        const rate = json.rates[d][quote];
        const prev = i > 0 ? json.rates[dates[i - 1]][quote] : rate;
        return {
          time: new Date(d).getTime(),
          open: prev,
          high: rate * (1 + Math.random() * 0.003),
          low: rate * (1 - Math.random() * 0.003),
          close: rate,
          volume: Math.floor(Math.random() * 1e9),
        };
      });
      const current = candles[candles.length - 1]?.close ?? 1;
      const prev = candles[candles.length - 2]?.close ?? current;
      const data = { candles, price: current, change: ((current - prev) / prev) * 100 };
      cache.set(key, { ts: Date.now(), data });
      return data;
    } catch (err) {
      if (STRICT_REAL_DATA) {
        throw new Error(`Falha ao obter dados reais de Forex para ${base}/${quote}: ${err.message || err}`);
      }
      return generateSimulatedForex(base, quote, days);
    }
  }

  // ===== NOTÍCIAS DE MERCADO (RSS-like via allorigins) =====
  async function fetchMarketNews(asset) {
    try {
      const query = encodeURIComponent(asset + ' mercado financeiro bolsa');
      const rss = `https://news.google.com/rss/search?q=${query}&hl=pt-BR&gl=BR&ceid=BR:pt-419`;
      const url = `https://api.allorigins.win/get?url=${encodeURIComponent(rss)}`;
      const res = await fetch(url);
      if (!res.ok) throw new Error();
      const json = await res.json();
      const parser = new DOMParser();
      const xml = parser.parseFromString(json.contents, 'text/xml');
      const items = Array.from(xml.querySelectorAll('item')).slice(0, 6);
      return items.map(item => ({
        title: item.querySelector('title')?.textContent || '',
        date: item.querySelector('pubDate')?.textContent || '',
        source: item.querySelector('source')?.textContent || 'Google News',
        sentiment: classifyNewsSentiment(item.querySelector('title')?.textContent || ''),
      }));
    } catch (err) {
      if (STRICT_REAL_DATA) {
        throw new Error(`Falha ao obter noticias reais para ${asset}: ${err.message || err}`);
      }
      return generateSimulatedNews(asset);
    }
  }

  // ===== CLASSIFICAÇÃO SENTIMENTO DE NOTÍCIA =====
  function classifyNewsSentiment(title) {
    const t = title.toLowerCase();
    const positiveWords = ['sobe', 'alta', 'lucro', 'crescimento', 'recorde', 'aprovado', 'acordo', 'positivo', 'ganho', 'expansão', 'recuperação', 'alta', 'retoma'];
    const negativeWords = ['cai', 'queda', 'perde', 'crise', 'risco', 'sanção', 'inflação', 'recessão', 'incerteza', 'preocupa', 'tensão', 'guerra', 'desaceleração'];
    const pos = positiveWords.filter(w => t.includes(w)).length;
    const neg = negativeWords.filter(w => t.includes(w)).length;
    if (pos > neg) return 'positive';
    if (neg > pos) return 'negative';
    return 'neutral';
  }

  // ===== DADOS ECONÔMICOS SIMULADOS (FALLBACK REALISTA) =====
  function generateSimulatedCandles(symbol, count, interval) {
    const bases = { BTCUSDT: 67000, ETHUSDT: 3200, BNBUSDT: 580, SOLUSDT: 145, XRPUSDT: 0.52 };
    let price = bases[symbol] || 100;
    const candles = [];
    const now = Date.now();
    const msPerCandle = intervalToMs(interval);
    
    for (let i = count; i >= 0; i--) {
      const volatility = price * (0.008 + Math.random() * 0.012);
      const open = price;
      const change = (Math.random() - 0.485) * volatility;
      const close = Math.max(price + change, price * 0.95);
      const high = Math.max(open, close) * (1 + Math.random() * 0.005);
      const low = Math.min(open, close) * (1 - Math.random() * 0.005);
      const volume = price * (1000 + Math.random() * 5000);
      candles.push({ time: now - i * msPerCandle, open, high, low, close, volume });
      price = close;
    }
    return candles.map(c => ({ ...c, __simulated: true, __source: 'simulated' }));
  }

  function generateSimulatedB3(symbol, interval) {
    const bases = { PETR4: 38, VALE3: 64, ITUB4: 32, BBDC4: 15, WEGE3: 47, MGLU3: 9, BBAS3: 54, EGIE3: 42 };
    let price = bases[symbol] || 30;
    const candles = [];
    const count = 100;
    const now = Date.now();
    const msPerCandle = intervalToMs(interval === '1d' ? '1d' : '1d');
    for (let i = count; i >= 0; i--) {
      const vol = price * 0.02;
      const open = price;
      const close = price + (Math.random() - 0.49) * vol;
      candles.push({
        time: now - i * msPerCandle,
        open, close,
        high: Math.max(open, close) * (1 + Math.random() * 0.005),
        low: Math.min(open, close) * (1 - Math.random() * 0.005),
        volume: Math.floor(Math.random() * 5e6),
      });
      price = close;
    }
    return {
      candles: candles.map(c => ({ ...c, __simulated: true, __source: 'simulated' })),
      price,
      change: ((price - bases[symbol]) / bases[symbol]) * 100,
      __simulated: true,
      __source: 'simulated',
    };
  }

  function generateSimulatedForex(base, quote, days) {
    const bases = { 'EUR_USD': 1.085, 'USD_BRL': 5.05, 'GBP_USD': 1.27 };
    let price = bases[`${base}_${quote}`] || 1.0;
    const candles = [];
    const now = Date.now();
    for (let i = days; i >= 0; i--) {
      const vol = price * 0.006;
      const open = price;
      const close = price + (Math.random() - 0.5) * vol;
      candles.push({
        time: now - i * 86400000, open, close,
        high: Math.max(open, close) * 1.002, low: Math.min(open, close) * 0.998,
        volume: Math.floor(Math.random() * 1e9),
      });
      price = close;
    }
    return {
      candles: candles.map(c => ({ ...c, __simulated: true, __source: 'simulated' })),
      price,
      change: ((price - (bases[`${base}_${quote}`] || 1)) / (bases[`${base}_${quote}`] || 1)) * 100,
      __simulated: true,
      __source: 'simulated',
    };
  }

  function generateSimulatedNews(asset) {
    const templates = [
      { title: `${asset}: analistas revisam projeções para o trimestre`, sentiment: 'neutral' },
      { title: `Mercado monitora perspectivas para ${asset} após dados macro`, sentiment: 'neutral' },
      { title: `${asset} atrai atenção de investidores institucionais`, sentiment: 'positive' },
      { title: `Volatilidade em ${asset} reflete incerteza global`, sentiment: 'negative' },
      { title: `Gestores aumentam exposição em ${asset}`, sentiment: 'positive' },
      { title: `Volume em ${asset} supera média histórica recente`, sentiment: 'neutral' },
    ];
    return templates.map(t => ({ ...t, date: new Date().toLocaleString('pt-BR'), source: 'Análise interna', __simulated: true, __source: 'simulated' }));
  }

  function intervalToMs(interval) {
    const map = { '1m': 60000, '5m': 300000, '15m': 900000, '1h': 3600000, '4h': 14400000, '1d': 86400000, '1w': 604800000 };
    return map[interval] || 86400000;
  }

  // ===== API PÚBLICA =====
  async function getCandles(assetKey, timeframe = '1h', limit = 120) {
    const asset = ASSETS[assetKey];
    if (!asset) {
      if (STRICT_REAL_DATA) {
        throw new Error(`Ativo nao suportado para operacao real: ${assetKey}`);
      }
      const simulated = generateSimulatedCandles('BTCUSDT', limit, timeframe);
      updateQuality(assetKey, timeframe, { candlesReal: false, candlesSource: 'simulated' });
      return simulated;
    }

    if (asset.type === 'crypto') {
      const interval = TF_BINANCE[timeframe] || '1h';
      const candles = await fetchBinanceKlines(asset.symbol, interval, limit);
      const simulated = candles.some(c => c.__simulated === true);
      updateQuality(assetKey, timeframe, { candlesReal: !simulated, candlesSource: simulated ? 'simulated' : 'binance' });
      return candles;
    }
    if (asset.type === 'b3') {
      const tf = timeframe === '5m' || timeframe === '15m' ? '5m' : timeframe === '1h' ? '1h' : '1d';
      const range = timeframe === '1w' ? '1y' : '3mo';
      const data = await fetchBRAPI(asset.symbol, tf, range);
      const candles = data.candles || generateSimulatedCandles(asset.symbol, limit, timeframe);
      const simulated = data.__simulated === true || candles.some(c => c.__simulated === true);
      if (STRICT_REAL_DATA && simulated) {
        throw new Error(`Candles simulados detectados para ${asset.symbol}. Operacao bloqueada.`);
      }
      updateQuality(assetKey, timeframe, { candlesReal: !simulated, candlesSource: simulated ? 'simulated' : 'brapi' });
      return candles;
    }
    if (asset.type === 'forex') {
      const data = await fetchForex(asset.base, asset.quote, limit);
      const candles = data.candles || generateSimulatedForex(asset.base, asset.quote, limit).candles;
      const simulated = data.__simulated === true || candles.some(c => c.__simulated === true);
      if (STRICT_REAL_DATA && simulated) {
        throw new Error(`Candles simulados detectados para ${asset.base}/${asset.quote}. Operacao bloqueada.`);
      }
      updateQuality(assetKey, timeframe, { candlesReal: !simulated, candlesSource: simulated ? 'simulated' : 'frankfurter' });
      return candles;
    }
    if (STRICT_REAL_DATA) {
      throw new Error(`Tipo de ativo nao suportado em modo real estrito: ${asset.type}`);
    }
    const fallback = generateSimulatedCandles(assetKey, limit, timeframe);
    updateQuality(assetKey, timeframe, { candlesReal: false, candlesSource: 'simulated' });
    return fallback;
  }

  async function getQuote(assetKey) {
    const asset = ASSETS[assetKey];
    if (!asset) return null;
    if (asset.type === 'crypto') {
      const ticker = await fetchBinanceTicker(asset.symbol);
      if (ticker) {
        updateQuality(assetKey, null, { quoteReal: true, quoteSource: 'binance' });
        return {
          price: parseFloat(ticker.lastPrice),
          change: parseFloat(ticker.priceChangePercent),
          volume: parseFloat(ticker.volume),
          high: parseFloat(ticker.highPrice),
          low: parseFloat(ticker.lowPrice),
        };
      }
      if (STRICT_REAL_DATA) {
        throw new Error(`Quote real indisponivel para ativo cripto ${asset.symbol}`);
      }
      updateQuality(assetKey, null, { quoteReal: false, quoteSource: 'unavailable' });
    }
    if (asset.type === 'b3') {
      const data = await fetchBRAPI(asset.symbol);
      const simulated = data.__simulated === true;
      if (STRICT_REAL_DATA && simulated) {
        throw new Error(`Quote simulado detectado para ${asset.symbol}. Operacao bloqueada.`);
      }
      updateQuality(assetKey, null, { quoteReal: !simulated, quoteSource: simulated ? 'simulated' : 'brapi' });
      return { price: data.price, change: data.change, volume: data.volume, pe: data.pe, dy: data.dy };
    }
    if (asset.type === 'forex') {
      const data = await fetchForex(asset.base, asset.quote);
      const simulated = data.__simulated === true;
      if (STRICT_REAL_DATA && simulated) {
        throw new Error(`Quote simulado detectado para ${asset.base}/${asset.quote}. Operacao bloqueada.`);
      }
      updateQuality(assetKey, null, { quoteReal: !simulated, quoteSource: simulated ? 'simulated' : 'frankfurter' });
      return { price: data.price, change: data.change };
    }
    if (STRICT_REAL_DATA) {
      throw new Error(`Tipo de ativo sem quote real suportado: ${asset.type}`);
    }
    updateQuality(assetKey, null, { quoteReal: false, quoteSource: 'unavailable' });
    return null;
  }

  async function getNews(assetKey) {
    const news = await fetchMarketNews(assetKey);
    const simulated = news.some(n => n.__simulated === true);
    updateQuality(assetKey, null, { newsReal: !simulated, newsSource: simulated ? 'simulated' : 'google-news' });
    return news;
  }

  function getAssetList() { return ASSETS; }
  function getDataQuality(assetKey, timeframe = null) {
    const scoped = dataQuality.get(qualityKey(assetKey, timeframe)) || {};
    const base = dataQuality.get(qualityKey(assetKey, null)) || {};
    const merged = { ...base, ...scoped, assetKey, timeframe };
    if (!base.updatedAt && !scoped.updatedAt) return null;
    return merged;
  }

  return { getCandles, getQuote, getNews, getAssetList, getDataQuality, ASSETS };
})();
