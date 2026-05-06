'use client';

import { useEffect, useRef, useState, useCallback } from 'react';
import styles from './plataforma.module.css';

// ── Tipos ────────────────────────────────────────────────────────────────────
interface SignalData {
  symbol: string;
  price: number;
  prevPrice: number;
  bias: 'LONG' | 'SHORT' | 'NEUTRAL';
  confidence: number;
  momentum: number;
  volatility: number;
  volume24h: number;
  change24h: number;
  updatedAt: number;
}

type ConnectionStatus = 'connecting' | 'connected' | 'reconnecting' | 'error';

// ── Constantes ───────────────────────────────────────────────────────────────
const SYMBOLS = (process.env.NEXT_PUBLIC_BYBIT_SIGNAL_ASSETS ?? 'BTCUSDT,ETHUSDT,SOLUSDT')
  .split(',')
  .map((s) => s.trim().toUpperCase());

const WS_URL = 'wss://stream.bybit.com/v5/public/linear';
const RECONNECT_DELAY_MS = 2000;
const MAX_RECONNECT_ATTEMPTS = 10;
const CANDLE_WINDOW = 20; // velas para calcular métricas

// ── Helpers ───────────────────────────────────────────────────────────────────
function calcBias(closes: number[]): { bias: 'LONG' | 'SHORT' | 'NEUTRAL'; confidence: number } {
  if (closes.length < 3) return { bias: 'NEUTRAL', confidence: 50 };
  const recent = closes.slice(-5);
  const older = closes.slice(-10, -5);
  const recentAvg = recent.reduce((a, b) => a + b, 0) / recent.length;
  const olderAvg = older.reduce((a, b) => a + b, 0) / (older.length || 1);
  const delta = (recentAvg - olderAvg) / olderAvg;
  const absD = Math.abs(delta);
  const confidence = Math.min(50 + absD * 2000, 99);
  if (delta > 0.0005) return { bias: 'LONG', confidence };
  if (delta < -0.0005) return { bias: 'SHORT', confidence };
  return { bias: 'NEUTRAL', confidence: 50 };
}

function calcMomentum(closes: number[]): number {
  if (closes.length < 2) return 0;
  const prev = closes[closes.length - 2];
  const curr = closes[closes.length - 1];
  return prev !== 0 ? ((curr - prev) / prev) * 100 : 0;
}

function calcVolatility(closes: number[]): number {
  if (closes.length < 2) return 0;
  const returns = closes.slice(1).map((c, i) => Math.log(c / closes[i]));
  const mean = returns.reduce((a, b) => a + b, 0) / returns.length;
  const variance = returns.reduce((a, b) => a + (b - mean) ** 2, 0) / returns.length;
  return Math.sqrt(variance) * 100;
}

function fmtPrice(n: number): string {
  return n >= 1000
    ? n.toLocaleString('pt-BR', { minimumFractionDigits: 2, maximumFractionDigits: 2 })
    : n.toFixed(4);
}

function fmtAge(ms: number): string {
  const s = Math.floor((Date.now() - ms) / 1000);
  if (s < 60) return `${s}s atrás`;
  return `${Math.floor(s / 60)}m atrás`;
}

// ── Componente principal ─────────────────────────────────────────────────────
export default function LiveSignalFeed() {
  const [signals, setSignals] = useState<Record<string, SignalData>>({});
  const [status, setStatus] = useState<ConnectionStatus>('connecting');
  const [lastTick, setLastTick] = useState<number>(0);
  const [tickCount, setTickCount] = useState<number>(0);

  const wsRef = useRef<WebSocket | null>(null);
  const closesRef = useRef<Record<string, number[]>>({});
  const prevPricesRef = useRef<Record<string, number>>({});
  const reconnectAttempts = useRef(0);
  const reconnectTimer = useRef<ReturnType<typeof setTimeout> | null>(null);
  const mountedRef = useRef(true);

  // ── Processa ticks de trade (preço em tempo real) ─────────────────────────
  const processTrade = useCallback((symbol: string, price: number, volume: number) => {
    if (!closesRef.current[symbol]) closesRef.current[symbol] = [];
    const closes = closesRef.current[symbol];

    // Adiciona preço atual como "close" corrente
    closes.push(price);
    if (closes.length > CANDLE_WINDOW * 10) closes.shift();

    const { bias, confidence } = calcBias(closes);
    const momentum = calcMomentum(closes);
    const volatility = calcVolatility(closes.slice(-CANDLE_WINDOW));
    const prevPrice = prevPricesRef.current[symbol] ?? price;

    setSignals((prev) => {
      const existing = prev[symbol];
      const change24h = existing?.change24h ?? 0;
      const volume24h = existing ? existing.volume24h + volume * price : volume * price;
      return {
        ...prev,
        [symbol]: {
          symbol,
          price,
          prevPrice,
          bias,
          confidence,
          momentum,
          volatility,
          volume24h,
          change24h,
          updatedAt: Date.now(),
        },
      };
    });

    prevPricesRef.current[symbol] = price;
    setLastTick(Date.now());
    setTickCount((c) => c + 1);
  }, []);

  // ── Processar ticker 24h ──────────────────────────────────────────────────
  const processTicker = useCallback((symbol: string, lastPrice: number, change24h: number) => {
    setSignals((prev) => {
      if (!prev[symbol]) return prev;
      return {
        ...prev,
        [symbol]: { ...prev[symbol], price: lastPrice, change24h },
      };
    });
  }, []);

  // ── Conectar WebSocket ────────────────────────────────────────────────────
  const connect = useCallback(() => {
    if (!mountedRef.current) return;

    setStatus('connecting');
    const ws = new WebSocket(WS_URL);
    wsRef.current = ws;

    ws.onopen = () => {
      if (!mountedRef.current) return;
      reconnectAttempts.current = 0;
      setStatus('connected');

      // Inscrever em trades públicos (tick-by-tick) e ticker 24h
      const tradeTopics = SYMBOLS.map((s) => `publicTrade.${s}`);
      const tickerTopics = SYMBOLS.map((s) => `tickers.${s}`);
      ws.send(JSON.stringify({ op: 'subscribe', args: [...tradeTopics, ...tickerTopics] }));
    };

    ws.onmessage = (evt) => {
      if (!mountedRef.current) return;
      try {
        const msg = JSON.parse(evt.data as string);

        // Trade tick — mais frequente (~10-50ms entre updates)
        if (msg.topic?.startsWith('publicTrade.') && Array.isArray(msg.data)) {
          const symbol = msg.topic.replace('publicTrade.', '');
          for (const trade of msg.data) {
            processTrade(symbol, parseFloat(trade.p), parseFloat(trade.v ?? '0'));
          }
        }

        // Ticker 24h
        if (msg.topic?.startsWith('tickers.') && msg.data) {
          const symbol = msg.topic.replace('tickers.', '');
          const d = msg.data;
          if (d.lastPrice) {
            processTicker(
              symbol,
              parseFloat(d.lastPrice),
              parseFloat(d.price24hPcnt ?? '0') * 100,
            );
          }
        }
      } catch {
        // ignora frames malformados
      }
    };

    ws.onerror = () => {
      if (!mountedRef.current) return;
      setStatus('error');
    };

    ws.onclose = () => {
      if (!mountedRef.current) return;
      if (reconnectAttempts.current < MAX_RECONNECT_ATTEMPTS) {
        reconnectAttempts.current += 1;
        setStatus('reconnecting');
        reconnectTimer.current = setTimeout(connect, RECONNECT_DELAY_MS);
      } else {
        setStatus('error');
      }
    };
  }, [processTrade, processTicker]);

  // ── Ciclo de vida ─────────────────────────────────────────────────────────
  useEffect(() => {
    mountedRef.current = true;
    connect();
    return () => {
      mountedRef.current = false;
      if (reconnectTimer.current) clearTimeout(reconnectTimer.current);
      wsRef.current?.close();
    };
  }, [connect]);

  // ── Render ────────────────────────────────────────────────────────────────
  const sortedSymbols = SYMBOLS.filter((s) => signals[s]);

  return (
    <div className={styles.liveFeedContainer}>
      {/* Header */}
      <div className={styles.liveFeedHeader}>
        <div className={styles.liveFeedTitle}>
          <span className={styles.liveFeedIcon}>📡</span>
          <span>Feed em Tempo Real — Bybit WebSocket</span>
        </div>
        <div className={styles.liveFeedMeta}>
          <StatusBadge status={status} />
          {status === 'connected' && lastTick > 0 && (
            <span className={styles.liveFeedTick}>
              {tickCount.toLocaleString()} ticks · {fmtAge(lastTick)}
            </span>
          )}
        </div>
      </div>

      {/* Tabela */}
      {sortedSymbols.length === 0 ? (
        <div className={styles.liveFeedLoading}>
          {status === 'connecting' || status === 'reconnecting'
            ? '⏳ Conectando ao WebSocket da Bybit...'
            : '⚠️ Sem dados disponíveis'}
        </div>
      ) : (
        <div className={styles.liveFeedWrapper}>
          <table className={styles.liveFeedTable}>
            <thead>
              <tr>
                <th>Ativo</th>
                <th>Preço</th>
                <th>24h %</th>
                <th>Sinal</th>
                <th>Confiança</th>
                <th>Momentum</th>
                <th>Volatilidade</th>
                <th>Atualizado</th>
              </tr>
            </thead>
            <tbody>
              {sortedSymbols.map((sym) => {
                const s = signals[sym];
                const priceUp = s.price >= s.prevPrice;
                const priceDown = s.price < s.prevPrice;
                return (
                  <tr key={sym} className={styles.liveFeedRow}>
                    <td className={styles.liveFeedSymbol}>{sym}</td>
                    <td
                      className={[
                        styles.liveFeedPrice,
                        priceUp ? styles.priceUp : '',
                        priceDown ? styles.priceDown : '',
                      ].join(' ')}
                    >
                      ${fmtPrice(s.price)}
                    </td>
                    <td
                      className={
                        s.change24h >= 0 ? styles.changePositive : styles.changeNegative
                      }
                    >
                      {s.change24h >= 0 ? '+' : ''}
                      {s.change24h.toFixed(2)}%
                    </td>
                    <td>
                      <span className={`${styles.biasBadge} ${styles[`bias${s.bias}`]}`}>
                        {s.bias === 'LONG' ? '▲ LONG' : s.bias === 'SHORT' ? '▼ SHORT' : '◆ NEUTRO'}
                      </span>
                    </td>
                    <td>
                      <ConfidenceBar value={s.confidence} bias={s.bias} />
                    </td>
                    <td
                      className={
                        s.momentum >= 0 ? styles.changePositive : styles.changeNegative
                      }
                    >
                      {s.momentum >= 0 ? '+' : ''}
                      {s.momentum.toFixed(4)}%
                    </td>
                    <td className={styles.liveFeedVol}>{s.volatility.toFixed(4)}%</td>
                    <td className={styles.liveFeedAge}>{fmtAge(s.updatedAt)}</td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      )}

      <p className={styles.liveFeedDisclaimer}>
        Dados públicos via Bybit WebSocket. Uso educacional — não constitui recomendação de investimento.
      </p>
    </div>
  );
}

// ── Sub-componentes ───────────────────────────────────────────────────────────
function StatusBadge({ status }: { status: ConnectionStatus }) {
  const map: Record<ConnectionStatus, { label: string; cls: string }> = {
    connecting:   { label: '⏳ Conectando',    cls: 'statusConnecting' },
    connected:    { label: '🟢 Ao vivo',       cls: 'statusConnected' },
    reconnecting: { label: '🔄 Reconectando',  cls: 'statusReconnecting' },
    error:        { label: '🔴 Erro',          cls: 'statusError' },
  };
  const { label, cls } = map[status];
  return <span className={`${styles.statusBadge} ${styles[cls]}`}>{label}</span>;
}

function ConfidenceBar({ value, bias }: { value: number; bias: string }) {
  return (
    <div className={styles.confBarWrap}>
      <div
        className={`${styles.confBarFill} ${
          bias === 'LONG' ? styles.confLong : bias === 'SHORT' ? styles.confShort : styles.confNeutral
        }`}
        style={{ width: `${value}%` }}
      />
      <span className={styles.confLabel}>{value.toFixed(0)}%</span>
    </div>
  );
}

// ── CSS a adicionar em plataforma.module.css ──────────────────────────────────
// Cole o bloco abaixo no final do seu plataforma.module.css existente
/*
.liveFeedContainer { width: 100%; margin-top: 2rem; }

.liveFeedHeader {
  display: flex; justify-content: space-between; align-items: center;
  margin-bottom: 0.75rem; flex-wrap: wrap; gap: 0.5rem;
}
.liveFeedTitle { display: flex; align-items: center; gap: 0.5rem;
  font-size: 1rem; font-weight: 600; color: #1a5276; }
.liveFeedIcon { font-size: 1.1rem; }
.liveFeedMeta { display: flex; align-items: center; gap: 0.75rem; flex-wrap: wrap; }
.liveFeedTick { font-size: 0.75rem; color: #666; }

.statusBadge { font-size: 0.75rem; font-weight: 600; padding: 2px 10px;
  border-radius: 12px; white-space: nowrap; }
.statusConnecting  { background: #fef9e7; color: #7d6608; border: 1px solid #f0c040; }
.statusConnected   { background: #d5f5e3; color: #1e8449; border: 1px solid #58d68d; }
.statusReconnecting{ background: #d6eaf8; color: #1a5276; border: 1px solid #5dade2; }
.statusError       { background: #fadbd8; color: #922b21; border: 1px solid #e74c3c; }

.liveFeedLoading { padding: 2rem; text-align: center; color: #666; font-size: 0.9rem; }

.liveFeedWrapper { width: 100%; overflow-x: auto; border-radius: 8px;
  border: 1px solid #d0d7de; }

.liveFeedTable { width: 100%; border-collapse: collapse; font-size: 0.875rem; }
.liveFeedTable thead { background: #0d2b4e; }
.liveFeedTable thead th { color: #fff; font-weight: 600; padding: 10px 14px;
  text-align: left; white-space: nowrap; font-size: 0.8rem; letter-spacing: 0.03em; }
.liveFeedTable thead th:first-child { border-radius: 8px 0 0 0; }
.liveFeedTable thead th:last-child  { border-radius: 0 8px 0 0; }

.liveFeedRow { border-bottom: 1px solid #eaecef; transition: background 0.15s; }
.liveFeedRow:nth-child(odd)  { background: #f8f9fa; }
.liveFeedRow:nth-child(even) { background: #ffffff; }
.liveFeedRow:hover { background: #eaf4fb; }
.liveFeedTable td { padding: 9px 14px; color: #0a0a0a; vertical-align: middle; }

.liveFeedSymbol { font-weight: 700; font-family: monospace; color: #0d2b4e; }

.liveFeedPrice { font-family: monospace; font-weight: 600; font-size: 0.9rem;
  transition: color 0.2s; }
.priceUp   { color: #1e8449 !important; }
.priceDown { color: #922b21 !important; }

.changePositive { color: #1e8449; font-weight: 600; }
.changeNegative { color: #922b21; font-weight: 600; }

.biasBadge { display: inline-block; padding: 3px 10px; border-radius: 4px;
  font-size: 0.78rem; font-weight: 700; white-space: nowrap; }
.biasLONG    { background: #d5f5e3; color: #1e8449; border: 1px solid #58d68d; }
.biasSHORT   { background: #fadbd8; color: #922b21; border: 1px solid #e74c3c; }
.biasNEUTRAL { background: #f4f4f4; color: #555;    border: 1px solid #ccc; }

.confBarWrap { position: relative; width: 80px; height: 8px;
  background: #e9ecef; border-radius: 4px; overflow: visible; display: flex; align-items: center; }
.confBarFill { height: 100%; border-radius: 4px; transition: width 0.3s ease; }
.confLong    { background: #27ae60; }
.confShort   { background: #e74c3c; }
.confNeutral { background: #aaa; }
.confLabel   { position: absolute; left: 88px; font-size: 0.72rem; color: #444;
  white-space: nowrap; }

.liveFeedVol { font-family: monospace; color: #555; }
.liveFeedAge { font-size: 0.75rem; color: #888; white-space: nowrap; }

.liveFeedDisclaimer { font-size: 0.72rem; color: #999; margin-top: 0.5rem;
  text-align: right; }
*/
