'use client';

import { useEffect, useRef, useState, useCallback } from 'react';
import styles from './plataforma.module.css';

// ── Tipos ────────────────────────────────────────────────────────────────────
interface TickerData {
  symbol:    string;
  last:      number;
  prevLast:  number;
  high:      number;
  low:       number;
  vol:       number;
  open:      number;
  buy:       number;
  sell:      number;
  change24h: number;
  bias:      'ALTA' | 'BAIXA' | 'NEUTRO';
  updatedAt: number;
}

type StatusConexao = 'conectando' | 'conectado' | 'atualizando' | 'erro';

// ── Configuração ──────────────────────────────────────────────────────────────
const SIMBOLOS = (process.env.NEXT_PUBLIC_MB_SIGNAL_ASSETS ?? 'BTC-BRL,ETH-BRL,SOL-BRL,XRP-BRL,ADA-BRL')
  .split(',')
  .map(s => s.trim().toUpperCase())
  .filter(Boolean);

const MB_API         = 'https://api.mercadobitcoin.net/api/v4';
const INTERVALO_MS   = 5000; // Polling a cada 5 segundos

// ── Helpers ───────────────────────────────────────────────────────────────────
function calcBias(last: number, open: number): 'ALTA' | 'BAIXA' | 'NEUTRO' {
  if (open <= 0) return 'NEUTRO';
  const delta = ((last - open) / open) * 100;
  if (delta >  0.15) return 'ALTA';
  if (delta < -0.15) return 'BAIXA';
  return 'NEUTRO';
}

function fmtBRL(n: number): string {
  return n.toLocaleString('pt-BR', { minimumFractionDigits: 2, maximumFractionDigits: 2 });
}

function fmtIdade(ms: number): string {
  const s = Math.floor((Date.now() - ms) / 1000);
  if (s < 60) return `${s}s atrás`;
  return `${Math.floor(s / 60)}m atrás`;
}

async function buscarTicker(simbolo: string): Promise<TickerData | null> {
  try {
    const r = await fetch(`${MB_API}/${encodeURIComponent(simbolo)}/ticker`, {
      cache: 'no-store',
      signal: AbortSignal.timeout(4000),
    });
    if (!r.ok) return null;
    const data = await r.json();
    const t = data.ticker;
    if (!t?.last) return null;

    const last = parseFloat(t.last);
    const open = parseFloat(t.open ?? t.last);

    return {
      symbol:    simbolo,
      last,
      prevLast:  last,
      high:      parseFloat(t.high  ?? t.last),
      low:       parseFloat(t.low   ?? t.last),
      vol:       parseFloat(t.vol   ?? '0'),
      open,
      buy:       parseFloat(t.buy   ?? t.last),
      sell:      parseFloat(t.sell  ?? t.last),
      change24h: open > 0 ? ((last - open) / open) * 100 : 0,
      bias:      calcBias(last, open),
      updatedAt: Date.now(),
    };
  } catch {
    return null;
  }
}

// ── Componente principal ──────────────────────────────────────────────────────
export default function LiveSignalFeed() {
  const [tickers, setTickers]     = useState<Record<string, TickerData>>({});
  const [status, setStatus]       = useState<StatusConexao>('conectando');
  const [numAtualizacoes, setNumAtualizacoes] = useState(0);
  const mountedRef = useRef(true);
  const timerRef   = useRef<ReturnType<typeof setInterval> | null>(null);

  const poll = useCallback(async () => {
    setStatus('atualizando');
    const resultados = await Promise.all(SIMBOLOS.map(buscarTicker));
    if (!mountedRef.current) return;

    let algumSucesso = false;

    setTickers(prev => {
      const next = { ...prev };
      resultados.forEach((t, i) => {
        if (t) {
          const sym = SIMBOLOS[i];
          // Preservar prevLast para animação de preço
          t.prevLast = prev[sym]?.last ?? t.last;
          next[sym]  = t;
          algumSucesso = true;
        }
      });
      return next;
    });

    setStatus(algumSucesso ? 'conectado' : 'erro');
    if (algumSucesso) setNumAtualizacoes(c => c + 1);
  }, []);

  useEffect(() => {
    mountedRef.current = true;
    poll();
    timerRef.current = setInterval(poll, INTERVALO_MS);
    return () => {
      mountedRef.current = false;
      if (timerRef.current) clearInterval(timerRef.current);
    };
  }, [poll]);

  const simbolosComDados = SIMBOLOS.filter(s => tickers[s]);

  return (
    <div className={styles.liveFeedContainer}>

      {/* Cabeçalho */}
      <div className={styles.liveFeedHeader}>
        <div className={styles.liveFeedTitle}>
          <span className={styles.liveFeedIcon}>📡</span>
          <span>Feed em Tempo Real — Mercado Bitcoin</span>
        </div>
        <div className={styles.liveFeedMeta}>
          <BadgeStatus status={status} />
          {status === 'conectado' && (
            <span className={styles.liveFeedTick}>
              {numAtualizacoes} atualizações · a cada {INTERVALO_MS / 1000}s
            </span>
          )}
        </div>
      </div>

      {/* Tabela ou estado vazio */}
      {simbolosComDados.length === 0 ? (
        <div className={styles.liveFeedLoading}>
          {status === 'conectando' || status === 'atualizando'
            ? '⏳ Conectando à API do Mercado Bitcoin...'
            : '⚠️ Sem dados disponíveis. Verifique a conexão.'}
        </div>
      ) : (
        <div className={styles.liveFeedWrapper}>
          <table className={styles.liveFeedTable}>
            <thead>
              <tr>
                <th>Ativo</th>
                <th>Último (R$)</th>
                <th>Variação 24h</th>
                <th>Sinal</th>
                <th>Máxima</th>
                <th>Mínima</th>
                <th>Volume</th>
                <th>Atualizado</th>
              </tr>
            </thead>
            <tbody>
              {simbolosComDados.map(sym => {
                const t   = tickers[sym];
                const subiu = t.last >= t.prevLast;
                return (
                  <tr key={sym} className={styles.liveFeedRow}>
                    <td className={styles.liveFeedSymbol}>
                      {sym.replace('-BRL', '')}/BRL
                    </td>
                    <td className={[
                      styles.liveFeedPrice,
                      subiu ? styles.priceUp : styles.priceDown,
                    ].join(' ')}>
                      R$ {fmtBRL(t.last)}
                    </td>
                    <td className={t.change24h >= 0 ? styles.changePositive : styles.changeNegative}>
                      {t.change24h >= 0 ? '+' : ''}{t.change24h.toFixed(2)}%
                    </td>
                    <td>
                      <span className={`${styles.biasBadge} ${
                        t.bias === 'ALTA'  ? styles.biasLONG    :
                        t.bias === 'BAIXA' ? styles.biasSHORT   :
                                             styles.biasNEUTRAL
                      }`}>
                        {t.bias === 'ALTA'  ? '▲ ALTA'  :
                         t.bias === 'BAIXA' ? '▼ BAIXA' :
                                              '◆ NEUTRO'}
                      </span>
                    </td>
                    <td style={{ color: '#22c55e', fontFamily: 'monospace' }}>
                      R$ {fmtBRL(t.high)}
                    </td>
                    <td style={{ color: '#ef4444', fontFamily: 'monospace' }}>
                      R$ {fmtBRL(t.low)}
                    </td>
                    <td className={styles.liveFeedVol}>
                      {t.vol.toFixed(4)}
                    </td>
                    <td className={styles.liveFeedAge}>
                      {fmtIdade(t.updatedAt)}
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      )}

      <p className={styles.liveFeedDisclaimer}>
        Dados via API pública do Mercado Bitcoin · atualização a cada {INTERVALO_MS / 1000}s ·
        Não constitui recomendação de investimento · BACEN Res. 519/520/521 · CVM Res. 30
      </p>
    </div>
  );
}

// ── Sub-componente: badge de status ───────────────────────────────────────────
function BadgeStatus({ status }: { status: StatusConexao }) {
  const mapa: Record<StatusConexao, { label: string; cls: string }> = {
    conectando:   { label: '⏳ Conectando',   cls: 'statusConnecting'   },
    conectado:    { label: '🟢 Ao vivo',      cls: 'statusConnected'    },
    atualizando:  { label: '🔄 Atualizando',  cls: 'statusReconnecting' },
    erro:         { label: '🔴 Sem dados',    cls: 'statusError'        },
  };
  const { label, cls } = mapa[status];
  return <span className={`${styles.statusBadge} ${styles[cls]}`}>{label}</span>;
}
