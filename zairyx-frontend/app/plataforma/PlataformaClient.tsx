'use client'
// E:\BOITATÁ_IA\zairyx-frontend\app\plataforma\PlataformaClient.tsx
// Boitatá IA Financas Brasil - Mesa Operacional
// BACEN Res. 519/520/521 | CVM Res. 30 | LGPD 13.709/2018

import { useState, useEffect, useRef, useCallback } from 'react'
import styles from './plataforma.module.css'

// ─── Tipos ───────────────────────────────────────────────────────────────────
interface Agente {
  id: string; animal: string; emoji: string; papel: string
  score: number | null; voto: 'COMPRA' | 'VENDA' | 'NEUTRO' | 'APROVADO' | 'REJEITADO' | null
}
interface Ativo {
  simbolo: string; nome: string; categoria: string; tv: string; score?: number
}
interface Operacao {
  id: string; ativo: string; nomeAtivo: string
  direcao: 'COMPRA' | 'VENDA'
  status: 'monitorando' | 'encerrada' | 'rejeitada' | 'aguardando'
  inicio: Date; fim: Date | null
  precoEntrada: number | null; precoAtual: number
  stopLoss: number | null; alvo: number | null
  score: number; motivo: string
  resultado: { tipo: 'GANHO' | 'PERDA'; variacao: number } | null
}
/** Trecho de `data` em POST /api/analyze/{asset} (alerta consolidado). */
interface AnalyzeAlertPayload {
  asset?: string
  score?: number
  classification?: string
  explanation?: string
  strategy?: {
    mode?: string
    direction?: string
    reasons?: string[]
    operational_status?: string
  } | null
  governance?: { approved?: boolean } | null
}

/** Corpo JSON de POST /api/analyze/{asset} (campos usados na plataforma). */
interface AnalyzeApiBody {
  success?: boolean
  data?: unknown
  agent_scores?: Record<string, number | null>
  agent_failures?: { agent_name: string; error_type: string; error_message: string }[]
  integrity_score?: number
}
interface Oportunidade {
  simbolo: string
  nome: string
  score: number | null
  direcao: 'COMPRA' | 'VENDA' | 'NEUTRO'
  /** Taxa de acerto historica (wins / decisivos) neste timeframe — exige outcomes gravados. */
  taxaAcerto: number | null
  tradesHistorico: number | null
  amostraTier: string | null
  classificacao: string | null
}

type TfMeta = {
  label: string
  canonical: string
  tv: string
  strategy_hint: string
  agent_alignment?: string
  /** Alinhado a GET /api/meta/chart-timeframes (motor). */
  strategy_family?: string
  strategy_family_note?: string
}

/** Igual a `core/chart_timeframes.py` — usado se GET /api/meta/chart-timeframes falhar. */
const FALLBACK_TF_CATALOG: TfMeta[] = [
  { label: 'M1', canonical: '1m', tv: '1', strategy_hint: 'Micro scalping — VWAP, volume, micro-estrutura', agent_alignment: 'ATLAS + ARGUS lideram; MACRO/NEWS so pano de fundo.', strategy_family: 'intraday_swings' },
  { label: 'M2', canonical: '2m', tv: '2', strategy_hint: 'Scalping rapido — ritmo curto', agent_alignment: 'Tecnico + volume dominam; sentimento macro peso baixo.', strategy_family: 'intraday_swings' },
  { label: 'M5', canonical: '5m', tv: '5', strategy_hint: 'Scalping classico — medias curtas + BB', agent_alignment: 'ATLAS central; ORION/NEWS se catalisar volatilidade.', strategy_family: 'intraday_swings' },
  { label: 'M15', canonical: '15m', tv: '15', strategy_hint: 'Intraday — MACD, RSI 14, VWAP', agent_alignment: 'ATLAS + Trends; MACRO ainda filtro.', strategy_family: 'intraday_swings' },
  { label: 'M30', canonical: '30m', tv: '30', strategy_hint: 'Intraday swing — medias 20/50', agent_alignment: 'Tecnico + regime; NEWS/SENTIMENT moderados.', strategy_family: 'intraday_swings' },
  { label: 'H1', canonical: '1h', tv: '60', strategy_hint: 'Swing curto — tendencia intradia', agent_alignment: 'ATLAS + AEGIS; MACRO/ORION mais relevantes.', strategy_family: 'swing_intraday_htf' },
  { label: 'M90', canonical: '90m', tv: '90', strategy_hint: 'Sessao estendida — ponte para HTF', agent_alignment: 'Similar ao H1 com menos ruido.', strategy_family: 'swing_intraday_htf' },
  { label: 'H4', canonical: '4h', tv: '240', strategy_hint: 'Swing — estrutura HTF + momentum', agent_alignment: 'MACRO + ATLAS; noticias para eventos.', strategy_family: 'swing_htf' },
  { label: 'D1', canonical: '1d', tv: 'D', strategy_hint: 'Posicao — regime, gap abertura vs dia anterior', agent_alignment: 'MACRO, Trends, Fundamentalista; ATLAS refino.', strategy_family: 'position_gap_session' },
  { label: 'W1', canonical: '1wk', tv: 'W', strategy_hint: 'Macro semanal — tendencia dominante', agent_alignment: 'MACRO dominante; tecnico confirmacao.', strategy_family: 'macro_position' },
  { label: 'MN1', canonical: '1mo', tv: 'M', strategy_hint: 'Ciclo mensal — posicao longa', agent_alignment: 'Fundamental + macro longo; execucao em TF menor.', strategy_family: 'macro_position' },
  { label: 'Q1', canonical: '3mo', tv: '3M', strategy_hint: 'Contexto trimestral', agent_alignment: 'Visao institucional; operacao sempre em TF menor.', strategy_family: 'macro_position' },
]

function compactAssetKey(simboloMb: string) {
  return simboloMb.replace(/-/g, '').toUpperCase()
}

function resolveTfRow(catalog: TfMeta[] | null, label: string): TfMeta {
  const rows = catalog ?? FALLBACK_TF_CATALOG
  return rows.find(r => r.label === label) ?? rows.find(r => r.label === 'H1')!
}

function timeframeMs(canonical: string): number | null {
  const map: Record<string, number> = {
    '1m': 60_000,
    '2m': 120_000,
    '5m': 300_000,
    '15m': 900_000,
    '30m': 1_800_000,
    '1h': 3_600_000,
    '90m': 5_400_000,
    '4h': 14_400_000,
    '1d': 86_400_000,
    '1wk': 604_800_000,
  }
  return map[canonical] ?? null
}

function delayAteFechamentoConfirmado(canonical: string): number {
  const ms = timeframeMs(canonical)
  if (!ms) return 60_000
  const now = Date.now()
  const closeIn = ms - (now % ms)
  return Math.max(5_000, closeIn + 5_000)
}

// ─── Agentes ──────────────────────────────────────────────────────────────────
// IDs alinhados ao backend (api/main.py _FRONTEND_AGENT_FEATURE_MAP):
//   ATLAS, MACRO, ORION, NEWS, TRENDS, FUND, SENTIMENT, SENTINEL, ARGUS, AEGIS
const AGENTES_BASE: Agente[] = [
  { id: 'ATLAS',     animal: 'Onca-Pintada',    emoji: '🐆', papel: 'Analise Tecnica',       score: null, voto: null },
  { id: 'MACRO',     animal: 'Harpia',           emoji: '🦅', papel: 'Contexto de Mercado',   score: null, voto: null },
  { id: 'ORION',     animal: 'Coruja',           emoji: '🦉', papel: 'Cognicao de Noticias',  score: null, voto: null },
  { id: 'NEWS',      animal: 'Arara Azul',       emoji: '🦜', papel: 'Noticias',              score: null, voto: null },
  { id: 'TRENDS',    animal: 'Capivara',         emoji: '🦫', papel: 'Volume e Fluxo',        score: null, voto: null },
  { id: 'FUND',      animal: 'Cutia',            emoji: '🐀', papel: 'Fundamentos',           score: null, voto: null },
  { id: 'SENTIMENT', animal: 'Boto-Cor-de-Rosa', emoji: '🐬', papel: 'Sentimento',            score: null, voto: null },
  { id: 'SENTINEL',  animal: 'Jabuti',           emoji: '🐢', papel: 'Protecao de Capital',   score: null, voto: null },
  { id: 'ARGUS',     animal: 'Puma',             emoji: '🐆', papel: 'Monitoramento Posicao', score: null, voto: null },
  { id: 'AEGIS',     animal: 'Tucano',           emoji: '🐦', papel: 'Fusao de Decisao',      score: null, voto: null },
]

// ─── Ativos seed ──────────────────────────────────────────────────────────────
// TradingView usa pares BRL quando existem; preço operacional e execução vêm do Mercado Bitcoin via API.
const MB_ATIVOS_SEED: Ativo[] = [
  { simbolo: 'BTC-BRL',   nome: 'Bitcoin',       categoria: 'L1',         tv: 'BINANCE:BTCBRL' },
  { simbolo: 'ETH-BRL',   nome: 'Ethereum',      categoria: 'L1',         tv: 'BINANCE:ETHBRL' },
  { simbolo: 'SOL-BRL',   nome: 'Solana',        categoria: 'L1',         tv: 'BINANCE:SOLBRL' },
  { simbolo: 'BNB-BRL',   nome: 'BNB',           categoria: 'L1',         tv: 'BINANCE:BNBBRL' },
  { simbolo: 'XRP-BRL',   nome: 'Ripple',        categoria: 'Altcoin',    tv: 'BINANCE:XRPBRL' },
  { simbolo: 'ADA-BRL',   nome: 'Cardano',       categoria: 'L1',         tv: 'BINANCE:ADABRL' },
  { simbolo: 'DOT-BRL',   nome: 'Polkadot',      categoria: 'L1',         tv: 'BINANCE:DOTBRL' },
  { simbolo: 'AVAX-BRL',  nome: 'Avalanche',     categoria: 'L1',         tv: 'BINANCE:AVAXBRL' },
  { simbolo: 'LINK-BRL',  nome: 'Chainlink',     categoria: 'Altcoin',    tv: 'BINANCE:LINKBRL' },
  { simbolo: 'DOGE-BRL',  nome: 'Dogecoin',      categoria: 'Altcoin',    tv: 'BINANCE:DOGEBRL' },
  { simbolo: 'LTC-BRL',   nome: 'Litecoin',      categoria: 'Altcoin',    tv: 'BINANCE:LTCBRL' },
  { simbolo: 'MATIC-BRL', nome: 'Polygon',       categoria: 'L2',         tv: 'BINANCE:MATICBRL' },
  { simbolo: 'UNI-BRL',   nome: 'Uniswap',       categoria: 'DeFi',       tv: 'BINANCE:UNIBRL' },
  { simbolo: 'ATOM-BRL',  nome: 'Cosmos',        categoria: 'L1',         tv: 'BINANCE:ATOMBRL' },
  { simbolo: 'NEAR-BRL',  nome: 'NEAR Protocol', categoria: 'L1',         tv: 'BINANCE:NEARBRL' },
  { simbolo: 'ALGO-BRL',  nome: 'Algorand',      categoria: 'L1',         tv: 'BINANCE:ALGOBRL' },
  { simbolo: 'SAND-BRL',  nome: 'The Sandbox',   categoria: 'Metaverso',  tv: 'BINANCE:SANDBRL' },
  { simbolo: 'MANA-BRL',  nome: 'Decentraland',  categoria: 'Metaverso',  tv: 'BINANCE:MANABRL' },
  { simbolo: 'FTM-BRL',   nome: 'Fantom',        categoria: 'L1',         tv: 'BINANCE:FTMBRL' },
  { simbolo: 'USDT-BRL',  nome: 'Tether',        categoria: 'Stablecoin', tv: 'BINANCE:USDTBRL' },
  { simbolo: 'USDC-BRL',  nome: 'USD Coin',      categoria: 'Stablecoin', tv: 'BINANCE:USDCUSDT' },
]

/** Caminho interno: Next reescreve para BOITATA_AI_SENTINEL_ORIGIN (ver next.config.ts). */
const BOITATA_API_PROXY_BASE = '/boitata-api'

/**
 * Base URL das chamadas à API ai-sentinel no browser.
 * 1) NEXT_PUBLIC_AI_API_URL / NEXT_PUBLIC_API_BASE se definidos (override explícito).
 * 2) Em localhost: http://127.0.0.1:8010 (dev local via start-local).
 * 3) Noutro host (ex.: Vercel): mesmo site + /boitata-api (proxy server-side, sem CORS).
 */
const API_BASE = ((): string => {
  const strip = (u: string) => u.replace(/\/$/, '')
  const fromEnv = strip(
    (typeof process !== 'undefined'
      ? (process.env.NEXT_PUBLIC_AI_API_URL || process.env.NEXT_PUBLIC_API_BASE || '').trim()
      : '') || ''
  )
  if (fromEnv) return fromEnv
  if (typeof window !== 'undefined') {
    const h = window.location.hostname
    if (h === 'localhost' || h === '127.0.0.1') return 'http://127.0.0.1:8010'
    return strip(window.location.origin) + BOITATA_API_PROXY_BASE
  }
  return 'http://127.0.0.1:8010'
})()

/** Timeout POST /api/analyze (ms). Groq multi-agente pode exceder 60s sob TPM ou rede lenta. */
const ANALYZE_TIMEOUT_MS = ((): number => {
  const raw =
    typeof process !== 'undefined' ? (process.env.NEXT_PUBLIC_ANALYZE_TIMEOUT_MS || '').trim() : ''
  const n = parseInt(raw, 10)
  if (Number.isFinite(n) && n >= 45000) return n
  return 120000
})()
const ANALYZE_TIMEOUT_SEC = Math.max(45, Math.round(ANALYZE_TIMEOUT_MS / 1000))

/** Par MB (`BTC-BRL`) -> segmento `POST /api/analyze/{asset}` como `BTCBRL` (broker MB). */
function mbSimboloParaAssetAnalyzePath(simboloMb: string): string {
  const s = simboloMb.trim().toUpperCase()
  const m1 = s.match(/^([A-Z0-9]+)-BRL$/)
  if (m1) return `${m1[1]}BRL`
  const compact = s.replace(/-/g, '')
  if (compact.endsWith('BRL') && compact.length > 4) return compact
  return compact
}

function simboloMbParaMarketPath(simboloMb: string): string {
  const s = simboloMb.trim().toUpperCase().replace(/\//g, '-')
  if (s.includes('-')) return s
  if (s.endsWith('BRL') && s.length > 3) return `${s.slice(0, -3)}-BRL`
  return `${s}-BRL`
}

/** URL completa POST /api/analyze/{asset} (asset sempre no path; encodeURIComponent). */
function urlPostAnalyze(simboloMb: string): string {
  const asset = mbSimboloParaAssetAnalyzePath(simboloMb)
  return `${API_BASE}/api/analyze/${encodeURIComponent(asset)}`
}

/** Qualquer valor atirado ao catch → texto útil (evita "falha desconhecida"). */
function erroToMensagem(err: unknown): string {
  if (err instanceof Error) return (err.message || err.name || 'Error').trim() || 'Error'
  if (typeof err === 'string') return err
  if (err != null && typeof err === 'object') {
    const m = (err as { message?: unknown }).message
    if (typeof m === 'string' && m.trim()) return m.trim()
    try {
      return JSON.stringify(err)
    } catch {
      /* vazio */
    }
  }
  return String(err)
}

function parseCorpoAnalyzeJson(text: string, urlPedido: string, httpStatus: number): AnalyzeApiBody {
  const trimmed = text.trim()
  if (!trimmed) {
    throw new Error(`Resposta vazia (${urlPedido}, HTTP ${httpStatus}).`)
  }
  if (trimmed.startsWith('<')) {
    throw new Error(
      `Resposta HTML em vez de JSON (${urlPedido}, HTTP ${httpStatus}). ` +
        'Verifique rota POST /api/analyze/{asset} e proxy (evita Unexpected token < no cliente).'
    )
  }
  try {
    return JSON.parse(text) as AnalyzeApiBody
  } catch {
    const head = trimmed.slice(0, 160).replace(/\s+/g, ' ')
    throw new Error(`JSON invalido (${urlPedido}, HTTP ${httpStatus}): ${head}`)
  }
}

// ─── Helpers de tempo ─────────────────────────────────────────────────────────
function pad(n: number) { return String(n).padStart(2, '0') }
function formatHora(d: Date) { return `${pad(d.getHours())}:${pad(d.getMinutes())}:${pad(d.getSeconds())}` }
function formatData(d: Date) { return `${pad(d.getDate())}/${pad(d.getMonth() + 1)}/${d.getFullYear()}` }
function duracaoTexto(inicio: Date, fim?: Date | null) {
  const ms = (fim ?? new Date()).getTime() - inicio.getTime()
  const min = Math.floor(ms / 60000)
  const sec = Math.floor((ms % 60000) / 1000)
  if (min >= 60) return `${Math.floor(min / 60)}h ${min % 60}min`
  return `${min}min ${sec}s`
}
function minutosPassados(inicio: Date) {
  return Math.floor((Date.now() - inicio.getTime()) / 60000)
}

// ─── Lógica do Orquestrador ───────────────────────────────────────────────────
function avaliarEntradaAtrasada(
  op: Operacao,
  precoAtual: number,
  minutosDecorridos: number,
  /** Ex.: "M1 (motor: 1m)" — obrigatório para texto coerente com o TF do gráfico. */
  tfLinha: string
): {
  podeEntrar: boolean
  mensagem: string
  urgencia: 'ok' | 'atencao' | 'perigo'
  movimentoConsumidoPorc: number
  /** Quando AEGIS ainda não fundiu — UI não deve dizer "atenção antes de entrar". */
  dialogoVariant?: 'consolidacao'
} {
  if (op.status === 'aguardando') {
    return {
      podeEntrar: false,
      mensagem:
        `Aguardando o motor (AEGIS) consolidar a analise para o timeframe ${tfLinha}. ` +
        'O primeiro relogio da linha do tempo marca desde que escolheu este ativo neste TF — ainda nao e o horario do sinal consolidado.',
      urgencia: 'atencao',
      movimentoConsumidoPorc: 0,
      dialogoVariant: 'consolidacao',
    }
  }
  if (op.status === 'encerrada' || op.status === 'rejeitada') {
    return {
      podeEntrar: false,
      mensagem: `Esta operacao ja foi ${op.status === 'encerrada' ? 'encerrada' : 'rejeitada'}. Aguarde o proximo sinal.`,
      urgencia: 'perigo',
      movimentoConsumidoPorc: 100,
    }
  }
  if (!op.stopLoss || !op.alvo) {
    return {
      podeEntrar: false,
      mensagem: op.precoEntrada
        ? 'Preco de referencia registado; stop e alvo nao constam na resposta do motor. Defina na mesa antes de dimensionar posicao.'
        : 'Aguardando dados completos da operacao (entrada, stop e alvo).',
      urgencia: 'atencao',
      movimentoConsumidoPorc: 0,
    }
  }
  if (!op.precoEntrada) {
    return { podeEntrar: false, mensagem: 'Aguardando preco de referencia da operacao.', urgencia: 'atencao', movimentoConsumidoPorc: 0 }
  }
  const movimentoTotal = Math.abs(op.alvo - op.precoEntrada)
  const movimentoAtual = op.direcao === 'COMPRA' ? precoAtual - op.precoEntrada : op.precoEntrada - precoAtual
  const movimentoConsumidoPorc = movimentoTotal > 0 ? Math.max(0, (movimentoAtual / movimentoTotal) * 100) : 0
  const variacaoPorcEntrada = op.direcao === 'COMPRA'
    ? ((precoAtual - op.precoEntrada) / op.precoEntrada) * 100
    : ((op.precoEntrada - precoAtual) / op.precoEntrada) * 100

  if (variacaoPorcEntrada < -0.3) {
    return {
      podeEntrar: true,
      mensagem: `Otimo momento para entrar: o preco recuou ${Math.abs(variacaoPorcEntrada).toFixed(2)}% desde o sinal (${minutosDecorridos} minutos atras), oferecendo uma entrada MELHOR do que a original. Stop em R$ ${op.stopLoss.toLocaleString('pt-BR')}, alvo em R$ ${op.alvo.toLocaleString('pt-BR')}.`,
      urgencia: 'ok',
      movimentoConsumidoPorc,
    }
  }
  if (movimentoConsumidoPorc <= 20) {
    return {
      podeEntrar: true,
      mensagem: `O sinal tem ${minutosDecorridos} minutos e o preco se moveu pouco (${movimentoConsumidoPorc.toFixed(0)}% do esperado). Entrada ainda valida. Stop em R$ ${op.stopLoss.toLocaleString('pt-BR')}, alvo em R$ ${op.alvo.toLocaleString('pt-BR')}.`,
      urgencia: 'ok',
      movimentoConsumidoPorc,
    }
  }
  if (movimentoConsumidoPorc <= 55) {
    return {
      podeEntrar: true,
      mensagem: `Sinal gerado ha ${minutosDecorridos} minutos — ${movimentoConsumidoPorc.toFixed(0)}% do caminho percorrido. Ainda ha espaco, mas use metade do tamanho de posicao. Stop em R$ ${op.stopLoss.toLocaleString('pt-BR')}. Alvo: R$ ${op.alvo.toLocaleString('pt-BR')}.`,
      urgencia: 'atencao',
      movimentoConsumidoPorc,
    }
  }
  if (movimentoConsumidoPorc <= 80) {
    return {
      podeEntrar: false,
      mensagem: `Nao recomendado. ${movimentoConsumidoPorc.toFixed(0)}% do movimento ja aconteceu (${minutosDecorridos} min atras). Risco de reversao alto. Aguarde o proximo sinal.`,
      urgencia: 'perigo',
      movimentoConsumidoPorc,
    }
  }
  return {
    podeEntrar: false,
    mensagem: `Oportunidade encerrada. ${movimentoConsumidoPorc.toFixed(0)}% do movimento percorrido desde o sinal. Acompanhe o proximo sinal.`,
    urgencia: 'perigo',
    movimentoConsumidoPorc,
  }
}

// ─── TradingView via iframe (único método confiável no Next.js 2025/2026) ──────
// Gráfico 100% limpo: ZERO indicadores. Apenas candles e volume integrado do TV.
// O usuário pode adicionar via "Indicators" do próprio widget se quiser. Os
// indicadores que o motor consome são computados no backend (ATLAS) e não
// poluem a visualização aqui.
function TradingViewChart({ simboloTV, interval }: { simboloTV: string; interval: string }) {
  const src =
    `https://www.tradingview.com/widgetembed/` +
    `?symbol=${encodeURIComponent(simboloTV)}` +
    `&interval=${interval}` +
    `&theme=dark` +
    `&style=1` +
    `&locale=pt` +
    `&timezone=America%2FSao_Paulo` +
    `&hide_top_toolbar=1` +
    `&hide_legend=1` +
    `&hide_side_toolbar=1` +
    `&withdateranges=0` +
    `&details=0` +
    `&hotlist=0` +
    `&calendar=0` +
    `&studies=[]` +
    `&backgroundColor=rgba(7%2C9%2C10%2C1)`

  return (
    <iframe
      key={`${simboloTV}-${interval}`}
      src={src}
      style={{ width: '100%', height: '100%', border: 'none', display: 'block' }}
      allowFullScreen
    />
  )
}

// ─── Banner de sinal consolidado (mesa) ──────────────────────────────────────
interface SignalBannerProps {
  decisao: 'COMPRA' | 'VENDA' | 'NEUTRO' | 'BLOQUEADO' | null
  confianca: number | null
  taxaAcerto: number | null
  taxaTrades: number | null
  atualizado: Date | null
  bloqueioMotivo: string | null
  newsGateSuppressed: boolean
  carregando: boolean
}

function SignalBanner({
  decisao,
  confianca,
  taxaAcerto,
  taxaTrades,
  atualizado,
  bloqueioMotivo,
  newsGateSuppressed,
  carregando,
}: SignalBannerProps) {
  const CONFIG = {
    COMPRA: { bg: 'rgba(34,197,94,0.12)', border: '#22c55e', texto: '#22c55e', label: 'COMPRA' },
    VENDA: { bg: 'rgba(239,68,68,0.12)', border: '#ef4444', texto: '#ef4444', label: 'VENDA' },
    NEUTRO: { bg: 'rgba(245,158,11,0.10)', border: '#f59e0b', texto: '#f59e0b', label: 'NEUTRO' },
    BLOQUEADO: { bg: 'rgba(100,116,139,0.10)', border: '#64748b', texto: '#94a3b8', label: 'BLOQUEADO' },
  } as const

  const cfg = decisao ? CONFIG[decisao] : null

  const [segsAtras, setSegsAtras] = useState(0)
  useEffect(() => {
    const id = setInterval(() => {
      setSegsAtras(atualizado ? Math.floor((Date.now() - atualizado.getTime()) / 1000) : 0)
    }, 1000)
    return () => clearInterval(id)
  }, [atualizado])

  const tempoLabel = segsAtras < 60
    ? `${segsAtras}s atras`
    : `${Math.floor(segsAtras / 60)}min atras`

  return (
    <div
      style={{
        background: cfg?.bg ?? 'rgba(100,116,139,0.06)',
        border: `1px solid ${cfg?.border ?? '#334155'}`,
        borderRadius: 12,
        padding: '14px 16px',
        marginBottom: 12,
      }}
    >
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 10 }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
          {carregando ? (
            <span style={{ fontSize: '1.4rem', fontWeight: 800, color: '#475569', letterSpacing: '-0.5px' }}>
              Analisando...
            </span>
          ) : (
            <span
              style={{
                fontSize: '1.6rem',
                fontWeight: 900,
                color: cfg?.texto ?? '#475569',
                letterSpacing: '-0.5px',
                lineHeight: 1,
              }}
            >
              {cfg?.label ?? '—'}
            </span>
          )}
        </div>
        {confianca !== null && !carregando && (
          <div style={{ textAlign: 'right' }}>
            <div style={{ fontSize: '1.3rem', fontWeight: 700, color: cfg?.texto ?? '#475569', lineHeight: 1 }}>
              {confianca.toFixed(0)}
              <span style={{ fontSize: '0.75rem', fontWeight: 400, color: '#64748b', marginLeft: 2 }}>/100</span>
            </div>
            <div style={{ fontSize: '0.65rem', color: '#475569', marginTop: 2 }}>forca do sinal</div>
          </div>
        )}
      </div>

      {confianca !== null && (
        <div style={{ height: 5, background: 'rgba(255,255,255,0.07)', borderRadius: 3, marginBottom: 10, overflow: 'hidden' }}>
          <div
            style={{
              height: '100%',
              width: `${Math.min(100, confianca)}%`,
              background: cfg?.border ?? '#334155',
              borderRadius: 3,
              transition: 'width 0.8s cubic-bezier(0.4,0,0.2,1)',
            }}
          />
        </div>
      )}

      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
        <div>
          <div
            style={{
              fontSize: '0.65rem',
              color: '#475569',
              textTransform: 'uppercase',
              letterSpacing: '0.08em',
              marginBottom: 2,
            }}
          >
            Taxa de acerto · 90 dias
          </div>
          {taxaAcerto !== null ? (
            <div style={{ display: 'flex', alignItems: 'baseline', gap: 5 }}>
              <span
                style={{
                  fontSize: '1.1rem',
                  fontWeight: 700,
                  color: taxaAcerto >= 60 ? '#22c55e' : taxaAcerto >= 45 ? '#f59e0b' : '#ef4444',
                }}
              >
                {taxaAcerto.toFixed(1)}%
              </span>
              {taxaTrades !== null && (
                <span style={{ fontSize: '0.7rem', color: '#475569' }}>({taxaTrades} trades)</span>
              )}
            </div>
          ) : (
            <span style={{ fontSize: '0.75rem', color: '#334155' }}>Sem dados suficientes (&lt;5 trades)</span>
          )}
        </div>
        <div style={{ textAlign: 'right' }}>
          <div style={{ fontSize: '0.65rem', color: '#334155' }}>
            {carregando ? 'atualizando...' : tempoLabel}
          </div>
        </div>
      </div>

      {decisao === 'BLOQUEADO' && bloqueioMotivo && (
        <div
          style={{
            marginTop: 8,
            padding: '6px 10px',
            background: 'rgba(100,116,139,0.12)',
            borderRadius: 6,
            fontSize: '0.72rem',
            color: '#94a3b8',
            lineHeight: 1.5,
          }}
        >
          {bloqueioMotivo}
        </div>
      )}

      {newsGateSuppressed && (
        <div
          style={{
            marginTop: 6,
            padding: '5px 10px',
            background: 'rgba(239,68,68,0.08)',
            borderRadius: 6,
            fontSize: '0.72rem',
            color: '#f87171',
          }}
        >
          Arara Azul bloqueou: noticia quente detectada — janela de risco ativa. Operacao suspensa ate a janela
          encerrar.
        </div>
      )}
    </div>
  )
}

// ─── Componente Principal ─────────────────────────────────────────────────────
export default function PlataformaClient({ userEmail = '' }: { userEmail?: string }) {
  const [agentes, setAgentes] = useState<Agente[]>(AGENTES_BASE)
  const [ativos, setAtivos] = useState<Ativo[]>(MB_ATIVOS_SEED)
  const [ativoSelecionado, setAtivoSelecionado] = useState(MB_ATIVOS_SEED[0])
  const [tfCatalog, setTfCatalog] = useState<TfMeta[] | null>(null)
  const [operacaoAtiva, setOperacaoAtiva] = useState<Operacao | null>(null)
  const [precoAtual, setPrecoAtual] = useState(412850)
  const [busca, setBusca] = useState('')
  const [categoriaFiltro, setCategoriaFiltro] = useState('Todos')
  const [modoAutomatico, setModoAutomatico] = useState(false)
  const [capitalTotal] = useState(10000)
  const [riscoPorc, setRiscoPorc] = useState(2)
  const [modalOrdem, setModalOrdem] = useState<'COMPRA' | 'VENDA' | null>(null)
  const [aceiteRisco, setAceiteRisco] = useState(false)
  const [toast, setToast] = useState<{ msg: string; cor: string } | null>(null)
  const [now, setNow] = useState(new Date())
  const [carregandoAnalise, setCarregandoAnalise] = useState(false)
  /** Timestamp em ms quando a análise atual começou (para contador "analisando há Xs"). */
  const [analiseIniciadaEm, setAnaliseIniciadaEm] = useState<number | null>(null)
  /** Erro real da última análise (rede, pipeline bloqueado, etc.). Mostrado na UI. */
  const [analiseErro, setAnaliseErro] = useState<string | null>(null)
  /** Score de integridade real (0-100) — quantos agentes retornaram dados. */
  const [integrityScore, setIntegrityScore] = useState<number | null>(null)
  /** Falhas reais do pipeline (agente -> tipo de erro). */
  const [agentFailures, setAgentFailures] = useState<{ agent_name: string; error_type: string; error_message: string }[]>([])
  /** Modo real retornado pelo motor (ex.: fast_scalp em M1-M15). */
  const [analiseModo, setAnaliseModo] = useState<string | null>(null)
  /** AbortController da análise atual (cancela quando muda ativo/TF ou desmonta). */
  const analiseAbortRef = useRef<AbortController | null>(null)
  const [abaEsquerda, setAbaEsquerda] = useState<'operacao' | 'ativos'>('operacao')
  /** Drawer dos Guardiões (direita) colapsável para maximizar o gráfico. Default ABERTO. */
  const [guardioesAbertos, setGuardioesAbertos] = useState(true)
  const [timeframe, setTimeframe] = useState<string>('H1')
  const [oportunidades, setOportunidades] = useState<Oportunidade[]>([])
  const [carregandoOport, setCarregandoOport] = useState(false)
  const [sinalDecisao, setSinalDecisao] = useState<'COMPRA' | 'VENDA' | 'NEUTRO' | 'BLOQUEADO' | null>(null)
  const [sinalConfianca, setSinalConfianca] = useState<number | null>(null)
  const [taxaAcerto, setTaxaAcerto] = useState<number | null>(null)
  const [taxaTrades, setTaxaTrades] = useState<number | null>(null)
  const [sinalAtualizado, setSinalAtualizado] = useState<Date | null>(null)
  const [sinalBloqueioMotivo, setSinalBloqueioMotivo] = useState<string | null>(null)
  const [newsGateSuppressed, setNewsGateSuppressed] = useState(false)
  /** Estado da mesa na API (paper/live, broker, copy trade automático). */
  const [mesaExecContext, setMesaExecContext] = useState<{
    mode: string
    brokerReady: boolean
    copyTradeEnabled: boolean
  } | null>(null)
  const operacaoInicioRef = useRef<Date>(new Date())
  const precoAtualRef = useRef(precoAtual)
  precoAtualRef.current = precoAtual

  // Relógio
  useEffect(() => {
    const id = setInterval(() => setNow(new Date()), 1000)
    return () => clearInterval(id)
  }, [])

  // Operação ativa simulada — reseta sempre que mudar o ATIVO ou o TIMEFRAME.
  // Sem essa reset o "tempo decorrido" e o "motivo" não condiziam com o TF escolhido.
  useEffect(() => {
    operacaoInicioRef.current = new Date()
    setOperacaoAtiva({
      id: `OP-${ativoSelecionado.simbolo}-${timeframe}-${Date.now()}`,
      ativo: ativoSelecionado.simbolo,
      nomeAtivo: ativoSelecionado.nome,
      direcao: 'COMPRA',
      status: 'aguardando',
      inicio: operacaoInicioRef.current,
      fim: null,
      precoEntrada: null,
      precoAtual: precoAtual,
      stopLoss: null,
      alvo: null,
      score: 0,
      motivo: `Aguardando analise do motor para ${ativoSelecionado.nome} no timeframe ${timeframe}. A operacao so e considerada apos AEGIS fundir os sinais reais dos agentes.`,
      resultado: null,
    })
    // Limpa os agentes ao mudar TF para não exibir scores antigos.
    setAgentes(AGENTES_BASE.map(a => ({ ...a, score: null, voto: null })))
    setAgentFailures([])
    setIntegrityScore(null)
    setAnaliseErro(null)
    setAnaliseModo(null)
    setSinalDecisao(null)
    setSinalConfianca(null)
    setTaxaAcerto(null)
    setTaxaTrades(null)
    setSinalAtualizado(null)
    setSinalBloqueioMotivo(null)
    setNewsGateSuppressed(false)
    // 'precoAtual' propositalmente fora das deps: senão recriaria a operação a cada tick.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [ativoSelecionado, timeframe])

  // Preço real do Mercado Bitcoin: a tela operacional deve refletir o mesmo mercado da execução.
  useEffect(() => {
    let cancelled = false
    const carregarPreco = async () => {
      try {
        const market = simboloMbParaMarketPath(ativoSelecionado.simbolo)
        const r = await fetch(`${API_BASE}/api/market/mb/ticker?asset=${encodeURIComponent(market)}`, {
          signal: AbortSignal.timeout(8000),
        })
        if (!r.ok || cancelled) return
        const j = await r.json()
        const last = Number(j.data?.last)
        if (Number.isFinite(last) && last > 0) {
          setPrecoAtual(+last.toFixed(2))
        }
      } catch {
        /* Mantem ultimo preco valido. */
      }
    }
    carregarPreco()
    const id = setInterval(carregarPreco, 5000)
    return () => clearInterval(id)
  }, [ativoSelecionado.simbolo])

  // Carregar lista completa de ativos MB
  useEffect(() => {
    fetch('https://api.mercadobitcoin.net/api/v4/symbols')
      .then(r => r.json())
      .then((data: string[]) => {
        if (!Array.isArray(data)) return
        const extras: Ativo[] = data
          .filter((s: string) => s.endsWith('-BRL'))
          .filter((s: string) => !MB_ATIVOS_SEED.find(a => a.simbolo === s))
          .slice(0, 580)
          .map((s: string) => {
            const base = s.replace('-BRL', '')
            return {
              simbolo: s,
              nome: base,
              categoria: 'Outro',
              // Default visual: par BRL no TradingView quando existir; operacional vem do MB.
              tv: `BINANCE:${base}BRL`,
            }
          })
        setAtivos([...MB_ATIVOS_SEED, ...extras])
      })
      .catch(() => { /* mantém seed */ })
  }, [])

  // Catálogo de timeframes (motor + TV) — espelha GET /api/meta/chart-timeframes
  useEffect(() => {
    fetch(`${API_BASE}/api/meta/chart-timeframes`, { signal: AbortSignal.timeout(5000) })
      .then(r => (r.ok ? r.json() : null))
      .then((j: { success?: boolean; items?: TfMeta[] } | null) => {
        if (j?.success && Array.isArray(j.items) && j.items.length > 0) {
          setTfCatalog(j.items as TfMeta[])
        }
      })
      .catch(() => { /* mantém fallback local */ })
  }, [])

  // Estado da mesa / broker (consistência com ordens manuais e automáticas)
  useEffect(() => {
    let cancelled = false
    ;(async () => {
      try {
        const r = await fetch(`${API_BASE}/api/desk/status`, { signal: AbortSignal.timeout(8000) })
        if (!r.ok || cancelled) return
        const j = await r.json()
        const root = j.data ?? j
        const desk = root.desk ?? {}
        const ct = root.copy_trade ?? {}
        setMesaExecContext({
          mode: String(desk.mode ?? 'paper'),
          brokerReady: Boolean(ct.broker_ready),
          copyTradeEnabled: Boolean(ct.enabled),
        })
      } catch {
        if (!cancelled) setMesaExecContext(null)
      }
    })()
    return () => { cancelled = true }
  }, [])

  // Análise do ativo selecionado (lê agent_scores REAIS do FeatureStore via backend).
  // Usa AbortController para cancelar chamadas anteriores quando muda ativo/TF.
  const buscarAnalise = useCallback(async (simbolo: string, tfLabel: string) => {
    // Cancela chamada anterior em curso (sem deixar pendurada).
    if (analiseAbortRef.current) {
      try { analiseAbortRef.current.abort('superseded') } catch { /* ignora */ }
    }
    const ctrl = new AbortController()
    analiseAbortRef.current = ctrl

    const row = resolveTfRow(tfCatalog, tfLabel)
    const assetPath = mbSimboloParaAssetAnalyzePath(simbolo)
    const urlPost = urlPostAnalyze(simbolo)
    const startedAt = Date.now()

    setCarregandoAnalise(true)
    setAnaliseIniciadaEm(startedAt)
    setAnaliseErro(null)
    setAnaliseModo(null)

    // Timeout do pedido — alinhado ao tempo real do pipeline (varias chamadas Groq).
    const timeoutId = setTimeout(() => {
      try { ctrl.abort('timeout') } catch { /* ignora */ }
    }, ANALYZE_TIMEOUT_MS)

    console.info('[Boitata] analyze REQUEST', { assetPath, tf: row.canonical, url: urlPost })

    try {
      const r = await fetch(urlPost, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ timeframe: row.canonical, tf_label: tfLabel }),
        signal: ctrl.signal,
      })
      const bodyText = await r.text()
      if (!r.ok) {
        let detail = `HTTP ${r.status}`
        try {
          const j = JSON.parse(bodyText) as { detail?: unknown }
          if (j?.detail != null) detail = typeof j.detail === 'string' ? j.detail : JSON.stringify(j.detail)
        } catch {
          detail = bodyText.trimStart().startsWith('<')
            ? `HTTP ${r.status} — corpo HTML (rota ou proxy errado). Pedido: ${urlPost}`
            : `${detail}: ${bodyText.slice(0, 220)}`
        }
        throw new Error(detail)
      }
      const data = parseCorpoAnalyzeJson(bodyText, urlPost, r.status)
      console.info('[Boitata] analyze RESPONSE', {
        ms: Date.now() - startedAt,
        agent_scores: data.agent_scores,
        integrity_score: data.integrity_score,
        agent_failures: data.agent_failures,
      })

      const scores: Record<string, number | null> = data.agent_scores ?? {}
      const failures: { agent_name: string; error_type: string; error_message: string }[] =
        Array.isArray(data.agent_failures) ? data.agent_failures : []
      const integ = typeof data.integrity_score === 'number' ? data.integrity_score : null

      if (data.success === false) {
        const degraded = data.data as { explanation?: unknown } | undefined
        setAnaliseErro(
          typeof degraded?.explanation === 'string'
            ? degraded.explanation
            : 'Analise degradada: o backend retornou success=false.'
        )
      } else if (data.agent_scores) setAnaliseErro(null)
      else {
        setAnaliseErro(
          'Backend desatualizado: nao retornou agent_scores. Reinicie o ai-sentinel (uvicorn) para pegar o commit mais recente.'
        )
      }

      const failureSet = new Set(failures.map(f => String(f.agent_name)))
      const idToBackendName: Record<string, string> = {
        ATLAS: 'ATLAS',
        MACRO: 'MacroAgent',
        ORION: 'ORION',
        NEWS: 'NewsAgent',
        TRENDS: 'TrendsAgent',
        FUND: 'FundamentalistAgent',
        SENTIMENT: 'SentimentAgent',
        SENTINEL: 'SENTINEL',
        ARGUS: 'ARGUS',
        AEGIS: 'AEGIS',
      }

      let decisaoParaVoto: 'COMPRA' | 'VENDA' | 'NEUTRO' | 'BLOQUEADO' | null = null
      try {
        const sr = await fetch(
          `${API_BASE}/api/signal/summary/${encodeURIComponent(assetPath)}?timeframe=${encodeURIComponent(row.canonical)}`,
          { signal: ctrl.signal }
        )
        if (sr.ok) {
          const sd = await sr.json() as {
            decision?: string | null
            confidence?: number | null
            hit_rate_pct?: number | null
            hit_rate_trades?: number | null
            last_updated?: string | null
            blocking_reason?: string | null
            news_gate_suppressed?: boolean
          }
          const d = sd.decision
          if (d === 'COMPRA' || d === 'VENDA' || d === 'NEUTRO' || d === 'BLOQUEADO') {
            decisaoParaVoto = d
          } else {
            decisaoParaVoto = null
          }
          setSinalDecisao(decisaoParaVoto)
          setSinalConfianca(typeof sd.confidence === 'number' ? sd.confidence : null)
          setTaxaAcerto(typeof sd.hit_rate_pct === 'number' ? sd.hit_rate_pct : null)
          setTaxaTrades(typeof sd.hit_rate_trades === 'number' ? sd.hit_rate_trades : null)
          setSinalBloqueioMotivo(typeof sd.blocking_reason === 'string' ? sd.blocking_reason : null)
          setNewsGateSuppressed(Boolean(sd.news_gate_suppressed))
          if (sd.last_updated) {
            const parsed = new Date(sd.last_updated)
            setSinalAtualizado(Number.isFinite(parsed.getTime()) ? parsed : new Date())
          } else {
            setSinalAtualizado(new Date())
          }
        }
      } catch {
        /* nao bloqueia a analise de agentes */
      }

      setAgentes(prev => prev.map(a => {
        const raw = scores[a.id]
        const failed = failureSet.has(idToBackendName[a.id] ?? a.id)
        const score: number | null = typeof raw === 'number' && Number.isFinite(raw) ? raw : null
        let voto: Agente['voto'] = null
        if (score != null) {
          if (decisaoParaVoto === 'COMPRA') {
            voto = score >= 70 ? 'COMPRA' : score >= 45 ? 'NEUTRO' : 'VENDA'
          } else if (decisaoParaVoto === 'VENDA') {
            voto = score <= 35 ? 'VENDA' : score <= 55 ? 'NEUTRO' : 'COMPRA'
          } else {
            voto = score >= 75 ? 'COMPRA' : score >= 50 ? 'NEUTRO' : 'VENDA'
          }
        } else if (failed) {
          voto = 'REJEITADO'
        }
        return { ...a, score, voto }
      }))
      setAgentFailures(failures)
      setIntegrityScore(integ)

      const alert = data.data as AnalyzeAlertPayload | undefined
      if (alert && typeof alert === 'object') {
        const strat = alert.strategy
        setAnaliseModo(typeof strat?.mode === 'string' ? strat.mode : null)
        const dirRaw = String(strat?.direction ?? '').toLowerCase()
        const direcao: 'COMPRA' | 'VENDA' = dirRaw === 'short' ? 'VENDA' : 'COMPRA'
        const cls = String(alert.classification ?? '')
          .normalize('NFD')
          .replace(/[\u0300-\u036f]/g, '')
          .toUpperCase()
        const gov = alert.governance
        const blockedByGov = gov != null && gov.approved === false
        let status: Operacao['status'] = 'monitorando'
        if (blockedByGov || cls.includes('RISCO')) status = 'rejeitada'

        const scoreNum =
          typeof alert.score === 'number' && Number.isFinite(alert.score) ? alert.score : 0
        const motivoParts: string[] = []
        if (alert.explanation) motivoParts.push(String(alert.explanation))
        if (strat?.reasons && strat.reasons.length > 0) {
          motivoParts.push(strat.reasons.slice(0, 6).join(' · '))
        }
        if (dirRaw === 'flat' || !strat) {
          motivoParts.push('Direcao da estrategia neutra (flat) ou indefinida.')
        }
        motivoParts.push('Stop e alvo nao constam na resposta da API; defina na mesa se for operar.')

        const sinalEm = new Date()
        setOperacaoAtiva(prev => {
          if (!prev || prev.ativo !== simbolo) return prev
          const px = precoAtualRef.current
          const directional = dirRaw === 'long' || dirRaw === 'short'
          return {
            ...prev,
            direcao,
            status,
            score: scoreNum,
            motivo: motivoParts.filter(Boolean).join('\n\n'),
            inicio: sinalEm,
            precoEntrada: status === 'monitorando' && directional ? px : prev.precoEntrada,
            precoAtual: px,
          }
        })
      }
    } catch (err) {
      const msg = erroToMensagem(err)
      const abortReason = String(ctrl.signal.reason ?? '').toLowerCase()
      const aborted =
        ctrl.signal.aborted ||
        (err instanceof Error && /abort/i.test(String(err.message ?? err.name ?? ''))) ||
        /^(aborterror|superseded|unmount)$/i.test(msg)
      const silentAbort = aborted && (abortReason === 'superseded' || abortReason === 'unmount' || /^(superseded|unmount)$/i.test(msg))
      if (silentAbort) {
        console.info('[Boitata] analyze ABORTED', { reason: abortReason || msg })
        return
      }
      const isNet = /Failed to fetch|network|TypeError|NetworkError|Load failed/i.test(msg)
      const friendly = aborted
        ? `Tempo esgotado (>${ANALYZE_TIMEOUT_SEC}s). Pedido: POST /api/analyze/{asset} em ${API_BASE}.`
        : isNet
          ? (() => {
              const host =
                typeof window !== 'undefined' ? window.location.hostname : ''
              const apiIsLoopback = /127\.0\.0\.1|localhost/i.test(API_BASE)
              const uiIsRemote = host && host !== 'localhost' && host !== '127.0.0.1'
              if (apiIsLoopback && uiIsRemote) {
                return (
                  `A plataforma abriu em "${host}" mas a API esta em ${API_BASE} (só o seu PC). ` +
                  'Defina NEXT_PUBLIC_AI_API_URL com o URL publico do ai-sentinel e faça novo build, ' +
                  'ou use zairyx-frontend/.env.local com essa variável em dev.'
                )
              }
              return (
                `Sem ligacao a API em ${API_BASE}. Confirme que o uvicorn esta a correr na mesma porta ` +
                `(ex.: start-local.cmd usa 8010). Detalhe: ${msg}`
              )
            })()
          : `${msg} | ${urlPost}`
      console.warn('[Boitata] analyze ERROR', { ms: Date.now() - startedAt, msg, friendly })
      setAnaliseErro(friendly)
      setAgentes(AGENTES_BASE.map(a => ({ ...a, score: null, voto: null })))
      setAgentFailures([])
      setIntegrityScore(null)
      setAnaliseModo(null)
      setSinalDecisao(null)
      setSinalConfianca(null)
      setTaxaAcerto(null)
      setTaxaTrades(null)
      setSinalAtualizado(null)
      setSinalBloqueioMotivo(null)
      setNewsGateSuppressed(false)
    } finally {
      clearTimeout(timeoutId)
      // Só desliga o "carregando" se essa chamada ainda for a atual (não foi superseded).
      if (analiseAbortRef.current === ctrl) {
        analiseAbortRef.current = null
        setCarregandoAnalise(false)
        setAnaliseIniciadaEm(null)
      }
    }
  }, [tfCatalog])

  useEffect(() => {
    let cancelled = false
    let nextTimer: ReturnType<typeof setTimeout> | null = null
    const tfRowLoop = resolveTfRow(tfCatalog, timeframe)

    const executarEAgendar = () => {
      if (cancelled) return
      void buscarAnalise(ativoSelecionado.simbolo, timeframe).finally(() => {
        if (cancelled) return
        nextTimer = setTimeout(executarEAgendar, delayAteFechamentoConfirmado(tfRowLoop.canonical))
      })
    }

    executarEAgendar()

    return () => {
      cancelled = true
      if (nextTimer) clearTimeout(nextTimer)
      if (analiseAbortRef.current) {
        try { analiseAbortRef.current.abort('unmount') } catch { /* ignora */ }
      }
    }
  }, [ativoSelecionado.simbolo, timeframe, buscarAnalise])

  // ── Ranking: taxa de acerto histórica (quando existir) + score ao vivo; prioridade = acerto depois score
  const buscarOportunidades = useCallback(async (tfLabel: string) => {
    const row = resolveTfRow(tfCatalog, tfLabel)
    setCarregandoOport(true)
    const candidatos = MB_ATIVOS_SEED.slice(0, 10)
    const hitMap = new Map<string, { hit: number; trades: number; tier: string }>()
    try {
      const hr = await fetch(
        `${API_BASE}/api/performance/asset-hit-ranking?timeframe=${encodeURIComponent(row.canonical)}&window_days=90&min_trades=1`,
        { signal: AbortSignal.timeout(6000) }
      )
      if (hr.ok) {
        const hj = await hr.json()
        const items = hj.data?.items ?? []
        for (const it of items as { asset?: string; hit_rate_pct?: number; trades?: number; sample_tier?: string }[]) {
          if (!it.asset) continue
          hitMap.set(compactAssetKey(`${it.asset}`), {
            hit: Number(it.hit_rate_pct) || 0,
            trades: Number(it.trades) || 0,
            tier: String(it.sample_tier ?? ''),
          })
        }
      }
    } catch { /* ranking opcional */ }

    try {
      // O ranking nao deve chamar /api/analyze em lote: isso satura o LLM e derruba a leitura principal.
      const ranking: Oportunidade[] = candidatos
        .map((ativo) => {
          const base = {
            simbolo: ativo.simbolo,
            nome: ativo.nome,
            score: null as number | null,
            direcao: 'NEUTRO' as const,
            taxaAcerto: null as number | null,
            tradesHistorico: null as number | null,
            amostraTier: null as string | null,
            classificacao: null as string | null,
          }
          const hk = hitMap.get(compactAssetKey(ativo.simbolo))
          if (hk && hk.trades > 0) {
            base.taxaAcerto = hk.hit
            base.tradesHistorico = hk.trades
            base.amostraTier = hk.tier || null
          }
          return base
        })
        .sort((a, b) => {
          const decisive = (t: number | null) => (t != null && t >= 3 ? 1 : 0)
          const pa = decisive(a.tradesHistorico) ? (a.taxaAcerto ?? -1) : -1
          const pb = decisive(b.tradesHistorico) ? (b.taxaAcerto ?? -1) : -1
          if (pb !== pa) return pb - pa
          const sa = a.score ?? -1
          const sb = b.score ?? -1
          return sb - sa
        })

      setOportunidades(ranking)

      const melhor = ranking[0]
      if (melhor && melhor.score != null && melhor.score >= 82 && melhor.direcao === 'COMPRA') {
        const ac =
          melhor.taxaAcerto != null && (melhor.tradesHistorico ?? 0) >= 3
            ? ` · Acerto ${melhor.taxaAcerto}% (${melhor.tradesHistorico} ops)`
            : ''
        mostrarToast(
          `⚡ Oportunidade: ${melhor.nome} · COMPRA · Score ${melhor.score} · ${tfLabel}${ac}`,
          '#f59e0b'
        )
      }
    } catch { /* silencioso */ }
    finally { setCarregandoOport(false) }
  }, [tfCatalog])

  useEffect(() => {
    buscarOportunidades(timeframe)
    const id = setInterval(() => buscarOportunidades(timeframe), 5 * 60 * 1000)
    return () => clearInterval(id)
  }, [timeframe, buscarOportunidades])

  // Confirmação de ordem
  async function confirmarOrdem() {
    if (!modalOrdem) return
    const tipo = modalOrdem
    setModalOrdem(null)
    setAceiteRisco(false)
    const tfRowOrdem = resolveTfRow(tfCatalog, timeframe)
    try {
      const r = await fetch(`${API_BASE}/api/desk/execute`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          asset: compactAssetKey(ativoSelecionado.simbolo),
          side: tipo === 'COMPRA' ? 'BUY' : 'SELL',
          risk_percent: riscoPorc,
          source: 'plataforma-web',
          chart_timeframe: tfRowOrdem.canonical,
          auto_mode_context: modoAutomatico,
        }),
        signal: AbortSignal.timeout(20000),
      })
      let j: Record<string, unknown> = {}
      try {
        j = (await r.json()) as Record<string, unknown>
      } catch { /* corpo vazio */ }
      if (!r.ok) {
        const det = j.detail
        const msg =
          typeof det === 'string'
            ? det
            : Array.isArray(det)
              ? (det as { msg?: string }[]).map(x => x.msg).filter(Boolean).join('; ')
              : `HTTP ${r.status}`
        mostrarToast(`Ordem recusada: ${msg}`, '#ef4444')
        return
      }
      const data = (j.data ?? j) as {
        message?: string
        action?: string
        mode?: string
      }
      const msg =
        typeof data.message === 'string'
          ? data.message
          : data.action === 'paper_simulated'
            ? 'Paper: ordem simulada na mesa (sem broker).'
            : 'Ordem processada.'
      const okReal = data.action === 'executed'
      mostrarToast(msg, okReal ? '#22c55e' : '#38bdf8')
      try {
        const st = await fetch(`${API_BASE}/api/desk/status`, { signal: AbortSignal.timeout(6000) })
        if (st.ok) {
          const sj = await st.json()
          const root = sj.data ?? sj
          const desk = root.desk ?? {}
          const ct = root.copy_trade ?? {}
          setMesaExecContext({
            mode: String(desk.mode ?? 'paper'),
            brokerReady: Boolean(ct.broker_ready),
            copyTradeEnabled: Boolean(ct.enabled),
          })
        }
      } catch { /* opcional */ }
    } catch {
      mostrarToast('API offline ou timeout — confirme se o ai-sentinel está em ' + API_BASE, '#f59e0b')
    }
  }

  function mostrarToast(msg: string, cor: string) {
    setToast({ msg, cor })
    setTimeout(() => setToast(null), 7000)
  }

  // Derivados
  const minutosDecorridos = operacaoAtiva ? minutosPassados(operacaoAtiva.inicio) : 0
  const tfRow = resolveTfRow(tfCatalog, timeframe)
  const tfLinhaMotor = `${timeframe} (motor ${tfRow.canonical})`
  const avaliacaoEntrada = operacaoAtiva
    ? avaliarEntradaAtrasada(operacaoAtiva, precoAtual, minutosDecorridos, tfLinhaMotor)
    : null

  const ativosFiltrados = ativos.filter(a => {
    const m = a.nome.toLowerCase().includes(busca.toLowerCase()) || a.simbolo.toLowerCase().includes(busca.toLowerCase())
    const c = categoriaFiltro === 'Todos' || a.categoria === categoriaFiltro
    return m && c
  })
  const categorias = ['Todos', ...Array.from(new Set(ativos.map(a => a.categoria)))]

  const variacaoPorc = operacaoAtiva?.precoEntrada
    ? (((precoAtual - operacaoAtiva.precoEntrada) / operacaoAtiva.precoEntrada) * 100
       * (operacaoAtiva.direcao === 'VENDA' ? -1 : 1)).toFixed(2)
    : '0.00'
  const podeAutoReal =
    Boolean(mesaExecContext?.copyTradeEnabled && mesaExecContext?.brokerReady && mesaExecContext?.mode === 'live')

  // AEGIS real (sem cair em mock da operação simulada para não enganar o utilizador).
  const scoreFinal = agentes.find(a => a.id === 'AEGIS')?.score ?? null
  const fastScalpAtivo = analiseModo === 'fast_scalp'
  const fastScalpCoreIds = new Set(['ATLAS', 'TRENDS', 'SENTINEL', 'AEGIS'])
  const agentesVisiveis = fastScalpAtivo ? agentes.filter(a => fastScalpCoreIds.has(a.id)) : agentes

  const corScore = (s: number | null) =>
    s === null ? '#7a7060' : s >= 75 ? '#22c55e' : s >= 50 ? '#f59e0b' : '#ef4444'

  const corVoto: Record<string, string> = {
    COMPRA: '#22c55e', VENDA: '#ef4444', NEUTRO: '#f59e0b', APROVADO: '#22c55e', REJEITADO: '#ef4444',
  }

  const corDirecao = (d: string) =>
    d === 'COMPRA' ? '#22c55e' : d === 'VENDA' ? '#ef4444' : '#f59e0b'

  const tfRowsUi = tfCatalog ?? FALLBACK_TF_CATALOG
  return (
    <div className={styles.plataforma} data-platform-root>

      {/* ── BARRA SUPERIOR ─────────────────────────────────────────────────── */}
      <header className={styles.topBar}>
        <div className={styles.topBarLeft}>
          <a href="/" className={styles.topBarBrand} title="Voltar ao site">Boitata IA</a>
          <span className={styles.topBarSep}>|</span>
          <span className={styles.statusDot} />
          <span className={styles.topBarTitle}>Mesa Operacional</span>
          <span className={styles.topBarSep}>|</span>
          <span className={styles.topBarUser}>{userEmail}</span>
          {mesaExecContext && (
            <>
              <span className={styles.topBarSep}>|</span>
              <span className={styles.topBarMeta} title="UNI_IA_MODE na API; ordem real só em live com broker pronto. Automático exige COPY_TRADE_ENABLED e scanner.">
                Mesa {mesaExecContext.mode.toUpperCase()}
                {' · '}
                Broker {mesaExecContext.brokerReady ? 'pronto' : 'incompleto'}
                {' · '}
                Auto {mesaExecContext.copyTradeEnabled ? 'on' : 'off'}
              </span>
            </>
          )}
        </div>
        <div className={styles.topBarCenter}>
          {operacaoAtiva && (
            <span className={styles.topBarAtivo}>
              {operacaoAtiva.nomeAtivo} &middot; R${' '}
              {precoAtual.toLocaleString('pt-BR', { minimumFractionDigits: 2 })}
              <span style={{ color: parseFloat(variacaoPorc) >= 0 ? '#22c55e' : '#ef4444', marginLeft: 8 }}>
                {parseFloat(variacaoPorc) >= 0 ? '▲' : '▼'} {Math.abs(parseFloat(variacaoPorc))}%
              </span>
            </span>
          )}
        </div>
        <div className={styles.topBarRight}>
          <span className={styles.relogio}>{formatData(now)} {formatHora(now)}</span>
          <a href="/auth/signout" className={styles.topBarSignout} title="Sair">Sair</a>
        </div>
      </header>

      {analiseErro && (
        <div className={styles.erroApiBanner} role="alert">
          <strong>Analise API</strong>
          {' — '}
          {analiseErro}
        </div>
      )}

      {/* ── LAYOUT PRINCIPAL ────────────────────────────────────────────────── */}
      <div className={styles.layout}>

        {/* ── COLUNA ESQUERDA ─────────────────────────────────────────────── */}
        <aside className={styles.colunaEsquerda}>
          <div className={styles.abas}>
            <button className={`${styles.aba} ${abaEsquerda === 'operacao' ? styles.abaAtiva : ''}`}
              onClick={() => setAbaEsquerda('operacao')}>Operacao</button>
            <button className={`${styles.aba} ${abaEsquerda === 'ativos' ? styles.abaAtiva : ''}`}
              onClick={() => setAbaEsquerda('ativos')}>Ativos ({ativos.length})</button>
          </div>

          {/* ABA OPERACAO */}
          {abaEsquerda === 'operacao' && operacaoAtiva && (
            <div className={styles.painelOperacao}>

              <div className={styles.opHeader}>
                <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                  <span className={styles.opNome}>{operacaoAtiva.nomeAtivo}</span>
                  <span className={styles.badge}
                    style={{
                      background: operacaoAtiva.direcao === 'COMPRA' ? '#22c55e20' : '#ef444420',
                      color: operacaoAtiva.direcao === 'COMPRA' ? '#22c55e' : '#ef4444',
                    }}>
                    {operacaoAtiva.direcao}
                  </span>
                </div>
                <span className={styles.badgePulso}>
                  <span className={styles.pontoPulso} />
                  {operacaoAtiva.status === 'rejeitada'
                    ? 'Rejeitada'
                    : operacaoAtiva.status === 'aguardando'
                      ? 'Aguardando'
                      : 'Monitorando'}
                </span>
              </div>

              <div className={styles.precoBloco}>
                <div className={styles.precoAtual}>
                  R$ {precoAtual.toLocaleString('pt-BR', { minimumFractionDigits: 2 })}
                </div>
                {operacaoAtiva.precoEntrada ? (
                  <div style={{ color: parseFloat(variacaoPorc) >= 0 ? '#22c55e' : '#ef4444', fontSize: '0.82rem', fontWeight: 600, marginTop: 2 }}>
                    {parseFloat(variacaoPorc) >= 0 ? '▲' : '▼'} {Math.abs(parseFloat(variacaoPorc))}% desde a entrada
                  </div>
                ) : (
                  <div style={{ color: '#7a7060', fontSize: '0.78rem', fontWeight: 500, marginTop: 2 }}>
                    Sem preco de referencia de entrada (aguardando motor ou niveis).
                  </div>
                )}
              </div>

              {/* LINHA DO TEMPO */}
              <div className={styles.linhaDoTempo}>
                <div className={styles.ldtTitulo}>Linha do Tempo</div>
                <div className={styles.ldtTfEscopo} title="Mesmo timeframe que o botao ativo no grafico e o enviado ao motor na analise.">
                  Valido para <strong>{timeframe}</strong>
                  <span style={{ opacity: 0.85 }}> · motor {tfRow.canonical}</span>
                </div>
                <div className={styles.ldtGrid}>
                  <div className={styles.ldtItem}>
                    <div className={styles.ldtLabel}>
                      {operacaoAtiva.status === 'aguardando' ? 'Janela aberta' : 'Sinal consolidado'}
                    </div>
                    <div className={styles.ldtValor}>{formatHora(operacaoAtiva.inicio)}</div>
                    <div className={styles.ldtSub}>
                      {formatData(operacaoAtiva.inicio)}
                      {operacaoAtiva.status === 'aguardando' ? ' · aguardando AEGIS' : ''}
                    </div>
                  </div>
                  <div className={styles.ldtItem}>
                    <div className={styles.ldtLabel}>Tempo decorrido</div>
                    <div className={styles.ldtValor}
                      style={{ color: minutosDecorridos > 45 ? '#f59e0b' : '#22c55e' }}>
                      {duracaoTexto(operacaoAtiva.inicio)}
                    </div>
                    <div className={styles.ldtSub}>
                      {operacaoAtiva.status === 'aguardando' ? 'desde selecao TF' : 'em andamento'}
                    </div>
                  </div>
                  <div className={styles.ldtItem}>
                    <div className={styles.ldtLabel}>Encerramento</div>
                    <div className={styles.ldtValor}>
                      {operacaoAtiva.fim ? formatHora(operacaoAtiva.fim) : 'em aberto'}
                    </div>
                    <div className={styles.ldtSub}>
                      {operacaoAtiva.fim ? formatData(operacaoAtiva.fim) : 'monitoramento continuo'}
                    </div>
                  </div>
                </div>
              </div>

              {/* CAIXA DO ORQUESTRADOR */}
              {avaliacaoEntrada && (() => {
                const consolidando = avaliacaoEntrada.dialogoVariant === 'consolidacao'
                const borda = consolidando
                  ? '#38bdf8'
                  : avaliacaoEntrada.urgencia === 'ok'
                    ? '#22c55e'
                    : avaliacaoEntrada.urgencia === 'atencao'
                      ? '#f59e0b'
                      : '#ef4444'
                const fundo = consolidando
                  ? 'rgba(56,189,248,0.08)'
                  : avaliacaoEntrada.urgencia === 'ok'
                    ? 'rgba(34,197,94,0.06)'
                    : avaliacaoEntrada.urgencia === 'atencao'
                      ? 'rgba(245,158,11,0.06)'
                      : 'rgba(239,68,68,0.06)'
                const titulo = consolidando
                  ? 'Tucano: consolidando leitura do TF'
                  : avaliacaoEntrada.urgencia === 'ok'
                    ? 'Tucano diz: entrada ainda valida'
                    : avaliacaoEntrada.urgencia === 'atencao'
                      ? 'Tucano diz: atencao antes de entrar'
                      : 'Tucano diz: nao recomendado entrar agora'
                const emoji = consolidando ? '🦉' : avaliacaoEntrada.urgencia === 'ok' ? '🦉' : avaliacaoEntrada.urgencia === 'atencao' ? '⚠️' : '🛑'
                return (
                <div className={styles.dialogoOrquestrador}
                  style={{
                    borderLeftColor: borda,
                    background: fundo,
                  }}>
                  <div className={styles.dialogoEmoji}>{emoji}</div>
                  <div>
                    <div className={styles.dialogoTitulo}
                      style={{
                        color: consolidando
                          ? '#38bdf8'
                          : avaliacaoEntrada.urgencia === 'ok'
                            ? '#22c55e'
                            : avaliacaoEntrada.urgencia === 'atencao'
                              ? '#f59e0b'
                              : '#ef4444',
                      }}>
                      {titulo}
                    </div>
                    <p className={styles.dialogoMensagem}>{avaliacaoEntrada.mensagem}</p>
                    {avaliacaoEntrada.movimentoConsumidoPorc > 0 && (
                      <div className={styles.barraMovimento}>
                        <div className={styles.barraMovimentoFundo}>
                          <div className={styles.barraMovimentoPreench}
                            style={{
                              width: `${Math.min(100, avaliacaoEntrada.movimentoConsumidoPorc)}%`,
                              background: avaliacaoEntrada.urgencia === 'ok' ? '#22c55e' :
                                          avaliacaoEntrada.urgencia === 'atencao' ? '#f59e0b' : '#ef4444',
                            }} />
                        </div>
                        <span className={styles.barraMovimentoTexto}>
                          {avaliacaoEntrada.movimentoConsumidoPorc.toFixed(0)}% do movimento percorrido
                        </span>
                      </div>
                    )}
                  </div>
                </div>
                )
              })()}

              {/* Motivo */}
              <div className={styles.motivoBloco}>
                <div className={styles.motivoTitulo}>O que o sistema identificou</div>
                <p className={styles.motivoTexto}>{operacaoAtiva.motivo}</p>
              </div>

              {/* Níveis */}
              <div className={styles.niveisGrid}>
                {[
                  { label: 'Entrada', valor: operacaoAtiva.precoEntrada, cor: '#3b82f6' },
                  { label: 'Limite de perda', valor: operacaoAtiva.stopLoss, cor: '#ef4444' },
                  { label: 'Alvo', valor: operacaoAtiva.alvo, cor: '#22c55e' },
                ].map(item => (
                  <div key={item.label} className={styles.nivelItem} style={{ borderTopColor: item.cor }}>
                    <div className={styles.nivelLabel}>{item.label}</div>
                    <div className={styles.nivelValor} style={{ color: item.cor }}>
                      {item.valor ? `R$ ${item.valor.toLocaleString('pt-BR')}` : '—'}
                    </div>
                  </div>
                ))}
              </div>

              {/* Modo automático */}
              <div className={styles.modoAutoBloco}>
                <div>
                  <div className={styles.modoAutoLabel}>Modo automatico</div>
                  <div className={styles.modoAutoSub}>
                    {modoAutomatico
                      ? (podeAutoReal ? 'Sistema pode executar no Mercado Bitcoin' : 'Auto visual ligado; execucao real bloqueada pela mesa')
                      : 'Voce aprova cada operacao'}
                  </div>
                </div>
                <button className={`${styles.toggle} ${modoAutomatico ? styles.toggleOn : ''}`}
                  title={
                    podeAutoReal
                      ? 'Automático real habilitado: live + broker pronto + copy trade on.'
                      : 'Protecao: automatico real exige UNI_IA_MODE=live, broker pronto e COPY_TRADE_ENABLED=true.'
                  }
                  onClick={() => setModoAutomatico(m => !m)}>
                  <span className={styles.toggleThumb} />
                </button>
              </div>

              {/* Risco */}
              <div className={styles.riscoBloco}>
                <div className={styles.riscoHeader}>
                  <span>Risco por operacao</span>
                  <span style={{ color: '#ef4444', fontWeight: 600 }}>
                    {riscoPorc}% &middot; R$ {((capitalTotal * riscoPorc) / 100).toLocaleString('pt-BR', { minimumFractionDigits: 2 })}
                  </span>
                </div>
                <input type="range" min="0.5" max="5" step="0.5"
                  value={riscoPorc}
                  onChange={e => setRiscoPorc(parseFloat(e.target.value))}
                  className={styles.slider}
                />
                <div className={styles.riscoEscala}>
                  <span>Conservador 0.5%</span><span>Agressivo 5%</span>
                </div>
                <div className={styles.riscoCVM}>CVM Res. 30 - maximo recomendado: 3% por operacao</div>
              </div>

              {/* Botões — bloqueados enquanto não houver análise consolidada,
                  para evitar ordem manual sem direcao real do motor. */}
              <div className={styles.botoesOrdem}>
                <button
                  className={styles.btnComprar}
                  disabled={
                    operacaoAtiva.status === 'aguardando' ||
                    operacaoAtiva.status === 'rejeitada' ||
                    scoreFinal === null
                  }
                  title={
                    operacaoAtiva.status === 'rejeitada'
                      ? 'Sinal rejeitado pelo motor (Sentinel/governanca ou classificacao de risco).'
                      : scoreFinal === null
                        ? 'Aguardando analise (AEGIS) para liberar ordem.'
                        : 'Comprar agora'
                  }
                  onClick={() => { setModalOrdem('COMPRA'); setAceiteRisco(false) }}>
                  ▲ COMPRAR
                </button>
                <button
                  className={styles.btnVender}
                  disabled={
                    operacaoAtiva.status === 'aguardando' ||
                    operacaoAtiva.status === 'rejeitada' ||
                    scoreFinal === null
                  }
                  title={
                    operacaoAtiva.status === 'rejeitada'
                      ? 'Sinal rejeitado pelo motor (Sentinel/governanca ou classificacao de risco).'
                      : scoreFinal === null
                        ? 'Aguardando analise (AEGIS) para liberar ordem.'
                        : 'Vender agora'
                  }
                  onClick={() => { setModalOrdem('VENDA'); setAceiteRisco(false) }}>
                  ▼ VENDER
                </button>
              </div>

              <div className={styles.avisoRisco}>
                Toda operacao envolve risco de perda total do capital. BACEN Res. 519/2025 e CVM Res. 30.
              </div>
            </div>
          )}

          {/* ABA ATIVOS */}
          {abaEsquerda === 'ativos' && (
            <div className={styles.painelAtivos}>
              <input className={styles.buscaInput} placeholder="Buscar ativo..."
                value={busca} onChange={e => setBusca(e.target.value)} />
              <div className={styles.categoriasFiltro}>
                {categorias.slice(0, 7).map(cat => (
                  <button key={cat}
                    className={`${styles.catBtn} ${categoriaFiltro === cat ? styles.catBtnAtivo : ''}`}
                    onClick={() => setCategoriaFiltro(cat)}>
                    {cat}
                  </button>
                ))}
              </div>
              <div className={styles.listaAtivos}>
                {ativosFiltrados.slice(0, 100).map(a => (
                  <button key={a.simbolo}
                    className={`${styles.ativoItem} ${ativoSelecionado.simbolo === a.simbolo ? styles.ativoItemAtivo : ''}`}
                    onClick={() => { setAtivoSelecionado(a); setAbaEsquerda('operacao') }}>
                    <span className={styles.ativoItemNome}>{a.nome}</span>
                    <span className={styles.ativoItemSigla}>{a.simbolo.replace('-BRL', '')}</span>
                  </button>
                ))}
                {ativosFiltrados.length > 100 && (
                  <div className={styles.maisAtivos}>+{ativosFiltrados.length - 100} ativos - refine a busca</div>
                )}
              </div>
            </div>
          )}
        </aside>

        {/* ── COLUNA CENTRAL: GRÁFICO ─────────────────────────────────────── */}
        <main className={styles.colunaCentral}>

          {/* Cabeçalho do gráfico com seletor de timeframe */}
          <div className={styles.graficoHeader}>
            <span className={styles.graficoTitulo} title={ativoSelecionado.simbolo}>
              {ativoSelecionado.nome}
              <span className={styles.graficoTituloSym}> {ativoSelecionado.simbolo}</span>
            </span>

            <div className={styles.tfRail} role="tablist" aria-label="Timeframe do grafico">
              {tfRowsUi.map(tf => (
                <button
                  key={tf.label}
                  type="button"
                  role="tab"
                  aria-selected={timeframe === tf.label}
                  className={`${styles.tfBtn} ${timeframe === tf.label ? styles.tfBtnActive : ''}`}
                  onClick={() => setTimeframe(tf.label)}
                >
                  {tf.label}
                </button>
              ))}
            </div>

            <div
              className={styles.tfHintBlock}
              title={[
                tfRow.strategy_hint,
                tfRow.strategy_family ? `Motor: ${tfRow.strategy_family}` : '',
                tfRow.strategy_family_note ?? '',
                tfRow.agent_alignment ?? '',
              ]
                .filter(Boolean)
                .join('\n')}
            >
              <span className={styles.graficoSub}>
                {[
                  tfRow.strategy_hint,
                  tfRow.strategy_family ? `Motor: ${tfRow.strategy_family}` : '',
                  tfRow.agent_alignment ?? '',
                ]
                  .filter(Boolean)
                  .join(' · ')}
              </span>
            </div>
          </div>

          {oportunidades.length > 0 && (
            <div className={styles.oppStrip}>
              <span className={styles.oppStripLabel}>
                {carregandoOport ? 'Atualizando' : 'Prioridade'}
              </span>
              <span className={styles.graficoAgentAlign} style={{ flexShrink: 0, marginRight: 6 }}>
                acerto → score
              </span>
              {oportunidades.slice(0, 10).map(op => (
                <button
                  key={op.simbolo}
                  type="button"
                  className={`${styles.oppChip} ${op.classificacao === 'OPORTUNIDADE' ? styles.oppChipOpp : ''}`}
                  style={{
                    borderColor: `${corDirecao(op.direcao)}44`,
                    color: corDirecao(op.direcao),
                    background: `${corDirecao(op.direcao)}14`,
                  }}
                  onClick={() => {
                    const a = ativos.find(x => x.simbolo === op.simbolo)
                    if (a) { setAtivoSelecionado(a); setAbaEsquerda('operacao') }
                  }}
                >
                  <span style={{ opacity: 0.96 }}>
                    {op.nome.split(' ')[0]}
                    {op.classificacao === 'OPORTUNIDADE' ? ' ★' : ''}
                    {' · '}
                    {op.score == null ? '—' : op.score}
                    {op.taxaAcerto != null && (op.tradesHistorico ?? 0) >= 1
                      ? ` · ${op.taxaAcerto}%/${op.tradesHistorico}`
                      : ''}
                  </span>
                </button>
              ))}
            </div>
          )}

          <div className={styles.graficoBox}>
            <div className={styles.chartFrame}>
              <TradingViewChart
                key={`${ativoSelecionado.simbolo}-${timeframe}`}
                simboloTV={ativoSelecionado.tv}
                interval={tfRow.tv}
              />
            </div>
          </div>
        </main>

        {/* ── COLUNA DIREITA: AGENTES (drawer colapsavel) ────────────────── */}
        <aside className={`${styles.colunaDireita} ${guardioesAbertos ? '' : styles.colunaDireitaFechada}`}>
          <SignalBanner
            decisao={sinalDecisao}
            confianca={sinalConfianca}
            taxaAcerto={taxaAcerto}
            taxaTrades={taxaTrades}
            atualizado={sinalAtualizado}
            bloqueioMotivo={sinalBloqueioMotivo}
            newsGateSuppressed={newsGateSuppressed}
            carregando={carregandoAnalise}
          />
          <div className={styles.agentesHeader}>
            {guardioesAbertos ? (
              <>
                <span className={styles.agentesTitulo}>Guardioes Boitata</span>
                <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                  {carregandoAnalise && (
                    <span className={styles.analisandoChip}>
                      {analiseIniciadaEm
                        ? `analisando ${Math.max(0, Math.floor((now.getTime() - analiseIniciadaEm) / 1000))}s / ${ANALYZE_TIMEOUT_SEC}s`
                        : 'analisando...'}
                    </span>
                  )}
                  {scoreFinal !== null ? (
                    <span style={{ fontSize: '1rem', fontWeight: 700, color: corScore(scoreFinal) }}>
                      {scoreFinal}/100
                    </span>
                  ) : (
                    <span style={{ fontSize: '0.7rem', color: '#7a7060', fontFamily: 'var(--mono)' }}>—/100</span>
                  )}
                  <button
                    type="button"
                    className={styles.drawerToggle}
                    onClick={() => setGuardioesAbertos(false)}
                    aria-label="Esconder painel dos guardioes"
                    title="Esconder painel — mais espaço para o gráfico"
                  >
                    ›
                  </button>
                </div>
              </>
            ) : (
              <button
                type="button"
                className={styles.drawerToggleOpen}
                onClick={() => setGuardioesAbertos(true)}
                aria-label="Abrir painel dos guardioes"
                title={`Abrir guardiões${scoreFinal !== null ? ` · AEGIS ${scoreFinal}/100` : ''}`}
              >
                <span className={styles.drawerToggleArrow}>‹</span>
                <span className={styles.drawerToggleScore} style={{ color: scoreFinal !== null ? corScore(scoreFinal) : '#7a7060' }}>
                  {scoreFinal !== null ? `${scoreFinal}` : '—'}
                </span>
                <span className={styles.drawerToggleLabel}>AEGIS</span>
              </button>
            )}
          </div>

          {guardioesAbertos && (analiseErro || agentFailures.length > 0 || integrityScore != null) && (
            <div
              style={{
                margin: '8px 8px 0',
                padding: '8px 10px',
                borderRadius: 6,
                background: analiseErro ? 'rgba(239,68,68,0.08)' : 'rgba(245,158,11,0.06)',
                border: analiseErro ? '1px solid rgba(239,68,68,0.25)' : '1px solid rgba(245,158,11,0.18)',
                fontSize: 10.5,
                lineHeight: 1.4,
                color: analiseErro ? '#ef4444' : '#f59e0b',
              }}
            >
              {analiseErro ? (
                <div><strong>Analise indisponivel:</strong> {analiseErro}</div>
              ) : (
                <>
                  {fastScalpAtivo && (
                    <div style={{ color: '#d1d5db', marginBottom: 4 }}>
                      FAST_SCALP: apenas ATLAS, TRENDS, SENTINEL e AEGIS entram no gatilho. Noticias/macro ficam fora do caminho critico.
                    </div>
                  )}
                  {integrityScore != null && (
                    <div style={{ color: '#d1d5db', marginBottom: agentFailures.length > 0 ? 4 : 0 }}>
                      Integridade: {integrityScore.toFixed(0)}% dos agentes responderam
                    </div>
                  )}
                  {agentFailures.length > 0 && (
                    <div>
                      <strong>Falhas reais:</strong>{' '}
                      {agentFailures.map(f => `${f.agent_name} (${f.error_type})`).join(', ')}
                    </div>
                  )}
                </>
              )}
            </div>
          )}

          {guardioesAbertos && <div className={styles.agentesLista}>
            {agentesVisiveis.map(a => (
              <div key={a.id} className={styles.agenteCard}>
                <div className={styles.agenteTop}>
                  <span className={styles.agenteEmoji}>{a.emoji}</span>
                  <div style={{ flex: 1 }}>
                    <div className={styles.agenteAnimal}>{a.animal}</div>
                    <div className={styles.agentePapel}>{a.papel}</div>
                  </div>
                  {a.voto && (
                    <span style={{ fontSize: '0.65rem', fontWeight: 700, color: corVoto[a.voto] }}>
                      {a.voto}
                    </span>
                  )}
                </div>
                <div className={styles.agenteBarraFundo}>
                  <div className={styles.agenteBarraPreench}
                    style={{ width: `${a.score ?? 0}%`, background: corScore(a.score) }} />
                </div>
                <div className={styles.agenteScoreTexto}>
                  {a.score !== null
                    ? `${a.score}/100`
                    : a.voto === 'REJEITADO'
                      ? 'agente falhou'
                      : carregandoAnalise
                        ? 'analisando...'
                        : analiseErro
                          ? 'sem leitura'
                          : 'aguardando'}
                </div>
              </div>
            ))}
          </div>}
        </aside>
      </div>

      {/* ── MODAL DE CONFIRMAÇÃO ────────────────────────────────────────────── */}
      {modalOrdem && (
        <div className={styles.modalOverlay}>
          <div className={styles.modalBox}>
            <h3 className={styles.modalTitulo}
              style={{ color: modalOrdem === 'COMPRA' ? '#22c55e' : '#ef4444' }}>
              Confirmar {modalOrdem}
            </h3>
            <div className={styles.modalDetalhes}>
              {[
                ['Ativo', `${ativoSelecionado.nome} (${ativoSelecionado.simbolo})`],
                ['Direcao', modalOrdem],
                ['Timeframe', timeframe],
                ['Estrategia (TF)', tfRow.strategy_hint.slice(0, 52) + (tfRow.strategy_hint.length > 52 ? '…' : '')],
                ['Agentes (alinhamento)', (tfRow.agent_alignment ?? '—').slice(0, 72) + ((tfRow.agent_alignment?.length ?? 0) > 72 ? '…' : '')],
                ['Alocacao de risco', `${riscoPorc}%`],
                ['Valor em risco', `R$ ${((capitalTotal * riscoPorc) / 100).toLocaleString('pt-BR', { minimumFractionDigits: 2 })}`],
                ['Score do sistema', `${scoreFinal ?? 'N/A'}/100`],
                ['Limite de perda', `R$ ${operacaoAtiva?.stopLoss?.toLocaleString('pt-BR') ?? '—'}`],
                ['Alvo de ganho', `R$ ${operacaoAtiva?.alvo?.toLocaleString('pt-BR') ?? '—'}`],
                ['Modo', 'PAPER - sem ordem real'],
              ].map(([label, valor]) => (
                <div key={label} className={styles.modalLinha}>
                  <span>{label}</span>
                  <strong>{valor}</strong>
                </div>
              ))}
            </div>

            <div className={styles.modalAvisoRisco}>
              <strong>Aviso obrigatorio - CVM Res. 30 / BACEN Res. 519</strong><br />
              Criptoativos sao de alto risco. Voce pode perder parte ou todo o capital. O FGC nao cobre operacoes em criptoativos.
            </div>

            <label className={styles.modalCheckLabel}>
              <input type="checkbox" checked={aceiteRisco}
                onChange={e => setAceiteRisco(e.target.checked)} />
              <span>Li e compreendo os riscos desta operacao.</span>
            </label>

            <div className={styles.modalBotoes}>
              <button className={styles.modalCancelar} onClick={() => setModalOrdem(null)}>Cancelar</button>
              <button
                className={styles.modalConfirmar}
                style={{
                  background: !aceiteRisco ? '#334155' :
                    modalOrdem === 'COMPRA' ? '#16a34a' : '#dc2626',
                  cursor: aceiteRisco ? 'pointer' : 'not-allowed',
                }}
                disabled={!aceiteRisco}
                onClick={confirmarOrdem}>
                Confirmar {modalOrdem}
              </button>
            </div>
          </div>
        </div>
      )}

      {/* ── TOAST ───────────────────────────────────────────────────────────── */}
      {toast && (
        <div className={styles.toast} style={{ borderLeftColor: toast.cor, color: toast.cor }}>
          {toast.msg}
        </div>
      )}
    </div>
  )
}
