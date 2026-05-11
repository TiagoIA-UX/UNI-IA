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
// Símbolos TradingView usam BINANCE:<BASE>USDT — referência global líquida.
// MERCADOBITCOIN:* não existe no TradingView; o preço em BRL vem do MB via API.
const MB_ATIVOS_SEED: Ativo[] = [
  { simbolo: 'BTC-BRL',   nome: 'Bitcoin',       categoria: 'L1',         tv: 'BINANCE:BTCUSDT' },
  { simbolo: 'ETH-BRL',   nome: 'Ethereum',      categoria: 'L1',         tv: 'BINANCE:ETHUSDT' },
  { simbolo: 'SOL-BRL',   nome: 'Solana',        categoria: 'L1',         tv: 'BINANCE:SOLUSDT' },
  { simbolo: 'BNB-BRL',   nome: 'BNB',           categoria: 'L1',         tv: 'BINANCE:BNBUSDT' },
  { simbolo: 'XRP-BRL',   nome: 'Ripple',        categoria: 'Altcoin',    tv: 'BINANCE:XRPUSDT' },
  { simbolo: 'ADA-BRL',   nome: 'Cardano',       categoria: 'L1',         tv: 'BINANCE:ADAUSDT' },
  { simbolo: 'DOT-BRL',   nome: 'Polkadot',      categoria: 'L1',         tv: 'BINANCE:DOTUSDT' },
  { simbolo: 'AVAX-BRL',  nome: 'Avalanche',     categoria: 'L1',         tv: 'BINANCE:AVAXUSDT' },
  { simbolo: 'LINK-BRL',  nome: 'Chainlink',     categoria: 'Altcoin',    tv: 'BINANCE:LINKUSDT' },
  { simbolo: 'DOGE-BRL',  nome: 'Dogecoin',      categoria: 'Altcoin',    tv: 'BINANCE:DOGEUSDT' },
  { simbolo: 'LTC-BRL',   nome: 'Litecoin',      categoria: 'Altcoin',    tv: 'BINANCE:LTCUSDT' },
  { simbolo: 'MATIC-BRL', nome: 'Polygon',       categoria: 'L2',         tv: 'BINANCE:MATICUSDT' },
  { simbolo: 'UNI-BRL',   nome: 'Uniswap',       categoria: 'DeFi',       tv: 'BINANCE:UNIUSDT' },
  { simbolo: 'ATOM-BRL',  nome: 'Cosmos',        categoria: 'L1',         tv: 'BINANCE:ATOMUSDT' },
  { simbolo: 'NEAR-BRL',  nome: 'NEAR Protocol', categoria: 'L1',         tv: 'BINANCE:NEARUSDT' },
  { simbolo: 'ALGO-BRL',  nome: 'Algorand',      categoria: 'L1',         tv: 'BINANCE:ALGOUSDT' },
  { simbolo: 'SAND-BRL',  nome: 'The Sandbox',   categoria: 'Metaverso',  tv: 'BINANCE:SANDUSDT' },
  { simbolo: 'MANA-BRL',  nome: 'Decentraland',  categoria: 'Metaverso',  tv: 'BINANCE:MANAUSDT' },
  { simbolo: 'FTM-BRL',   nome: 'Fantom',        categoria: 'L1',         tv: 'BINANCE:FTMUSDT' },
  { simbolo: 'USDT-BRL',  nome: 'Tether',        categoria: 'Stablecoin', tv: 'BINANCE:USDTBRL' },
  { simbolo: 'USDC-BRL',  nome: 'USD Coin',      categoria: 'Stablecoin', tv: 'BINANCE:USDCUSDT' },
]

const API_BASE =
  (typeof process !== 'undefined' &&
    (process.env.NEXT_PUBLIC_AI_API_URL || process.env.NEXT_PUBLIC_API_BASE || '').trim()) ||
  'http://127.0.0.1:8000'

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
  minutosDecorridos: number
): {
  podeEntrar: boolean
  mensagem: string
  urgencia: 'ok' | 'atencao' | 'perigo'
  movimentoConsumidoPorc: number
} {
  if (!op.precoEntrada || !op.stopLoss || !op.alvo) {
    return { podeEntrar: false, mensagem: 'Aguardando dados completos da operacao.', urgencia: 'atencao', movimentoConsumidoPorc: 0 }
  }
  if (op.status === 'encerrada' || op.status === 'rejeitada') {
    return {
      podeEntrar: false,
      mensagem: `Esta operacao ja foi ${op.status === 'encerrada' ? 'encerrada' : 'rejeitada'}. Aguarde o proximo sinal.`,
      urgencia: 'perigo',
      movimentoConsumidoPorc: 100,
    }
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
function TradingViewChart({ simboloTV, interval }: { simboloTV: string; interval: string }) {
  const estudos = [
    'RSI%40tv-basicstudies',
    'Volume%40tv-basicstudies',
    'MACD%40tv-basicstudies',
    'BB%40tv-basicstudies',
  ].join('%1F')
  const src =
    `https://www.tradingview.com/widgetembed/` +
    `?symbol=${encodeURIComponent(simboloTV)}` +
    `&interval=${interval}` +
    `&theme=dark` +
    `&style=1` +
    `&locale=pt` +
    `&timezone=America%2FSao_Paulo` +
    `&hide_top_toolbar=0` +
    `&hide_legend=0` +
    `&studies=${estudos}` +
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
  const [abaEsquerda, setAbaEsquerda] = useState<'operacao' | 'ativos'>('operacao')
  const [timeframe, setTimeframe] = useState<string>('H1')
  const [oportunidades, setOportunidades] = useState<Oportunidade[]>([])
  const [carregandoOport, setCarregandoOport] = useState(false)
  /** Estado da mesa na API (paper/live, broker, copy trade automático). */
  const [mesaExecContext, setMesaExecContext] = useState<{
    mode: string
    brokerReady: boolean
    copyTradeEnabled: boolean
  } | null>(null)
  const operacaoInicioRef = useRef<Date>(new Date())

  // Relógio
  useEffect(() => {
    const id = setInterval(() => setNow(new Date()), 1000)
    return () => clearInterval(id)
  }, [])

  // Operação ativa simulada
  useEffect(() => {
    operacaoInicioRef.current = new Date()
    setOperacaoAtiva({
      id: 'OP-2026-0509-001',
      ativo: ativoSelecionado.simbolo,
      nomeAtivo: ativoSelecionado.nome,
      direcao: 'COMPRA',
      status: 'monitorando',
      inicio: operacaoInicioRef.current,
      fim: null,
      precoEntrada: 412850,
      precoAtual: precoAtual,
      stopLoss: 404000,
      alvo: 428000,
      score: 87,
      motivo: 'Rompimento de resistencia em R$ 410.000 com volume 2,3x acima da media. RSI em 58 com espaco para subida. Medias de 20 e 50 periodos alinhadas para cima. Harpia confirma mercado global favoravel.',
      resultado: null,
    })
  }, [ativoSelecionado])

  // Preço simulado em tempo real
  useEffect(() => {
    const id = setInterval(() => {
      setPrecoAtual(p => +(p + (Math.random() - 0.48) * 180).toFixed(2))
    }, 2000)
    return () => clearInterval(id)
  }, [])

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
              // Default: BINANCE:<BASE>USDT (símbolo TradingView validado).
              tv: `BINANCE:${base}USDT`,
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

  // Análise do ativo selecionado (lê agent_scores REAIS do FeatureStore via backend)
  const buscarAnalise = useCallback(async (simbolo: string, tfLabel: string) => {
    const row = resolveTfRow(tfCatalog, tfLabel)
    setCarregandoAnalise(true)
    try {
      const assetParam = simbolo.replace('-BRL', '') + 'BRL'
      const r = await fetch(`${API_BASE}/api/analyze/${assetParam}`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ timeframe: row.canonical, tf_label: tfLabel }),
        signal: AbortSignal.timeout(60000), // pipeline LLM real (Macro/ATLAS/ORION/News) pode levar 20-50s
      })
      if (!r.ok) throw new Error()
      const data = await r.json()
      const scores: Record<string, number | null> = data.agent_scores ?? {}
      const failures: { agent_name: string }[] = Array.isArray(data.agent_failures) ? data.agent_failures : []
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
      setAgentes(prev => prev.map(a => {
        const raw = scores[a.id]
        const failed = failureSet.has(idToBackendName[a.id] ?? a.id)
        const score: number | null = typeof raw === 'number' && Number.isFinite(raw) ? raw : null
        let voto: Agente['voto'] = null
        if (score != null) {
          voto = score >= 75 ? 'COMPRA' : score >= 50 ? 'NEUTRO' : 'VENDA'
        } else if (failed) {
          voto = 'REJEITADO'
        }
        return { ...a, score, voto }
      }))
    } catch {
      // Sem inflar dados: marca tudo como sem score e voto nulo.
      setAgentes(AGENTES_BASE.map(a => ({ ...a, score: null, voto: null })))
    } finally {
      setCarregandoAnalise(false)
    }
  }, [tfCatalog])

  useEffect(() => {
    buscarAnalise(ativoSelecionado.simbolo, timeframe)
    const id = setInterval(() => buscarAnalise(ativoSelecionado.simbolo, timeframe), 60000)
    return () => clearInterval(id)
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
      const resultados = await Promise.allSettled(
        candidatos.map(a =>
          fetch(`${API_BASE}/api/analyze/${a.simbolo.replace('-BRL', '') + 'BRL'}`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ timeframe: row.canonical, tf_label: tfLabel }),
            signal: AbortSignal.timeout(8000),
          }).then(r => r.ok ? r.json() : null)
        )
      )
      const ranking: Oportunidade[] = resultados
        .map((r, i) => {
          const base = {
            simbolo: candidatos[i].simbolo,
            nome: candidatos[i].nome,
            score: null as number | null,
            direcao: 'NEUTRO' as const,
            taxaAcerto: null as number | null,
            tradesHistorico: null as number | null,
            amostraTier: null as string | null,
            classificacao: null as string | null,
          }
          const hk = hitMap.get(compactAssetKey(candidatos[i].simbolo))
          if (hk && hk.trades > 0) {
            base.taxaAcerto = hk.hit
            base.tradesHistorico = hk.trades
            base.amostraTier = hk.tier || null
          }
          if (r.status !== 'fulfilled' || !r.value) {
            return base
          }
          const d = r.value.data ?? r.value
          const rawScore = d.score
          const s: number | null = typeof rawScore === 'number' && Number.isFinite(rawScore) ? rawScore : null
          const cls = typeof d.classification === 'string' ? d.classification : null
          return {
            ...base,
            score: s,
            direcao: (s != null && s >= 70 ? 'COMPRA' : s != null && s >= 50 ? 'NEUTRO' : 'VENDA') as Oportunidade['direcao'],
            classificacao: cls,
          }
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
  const avaliacaoEntrada = operacaoAtiva
    ? avaliarEntradaAtrasada(operacaoAtiva, precoAtual, minutosDecorridos)
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

  const scoreFinal = agentes.find(a => a.id === 'AEGIS')?.score ?? operacaoAtiva?.score ?? null

  const corScore = (s: number | null) =>
    s === null ? '#7a7060' : s >= 75 ? '#22c55e' : s >= 50 ? '#f59e0b' : '#ef4444'

  const corVoto: Record<string, string> = {
    COMPRA: '#22c55e', VENDA: '#ef4444', NEUTRO: '#f59e0b', APROVADO: '#22c55e', REJEITADO: '#ef4444',
  }

  const corDirecao = (d: string) =>
    d === 'COMPRA' ? '#22c55e' : d === 'VENDA' ? '#ef4444' : '#f59e0b'

  const tfRow = resolveTfRow(tfCatalog, timeframe)
  const tfRowsUi = tfCatalog ?? FALLBACK_TF_CATALOG
  return (
    <div className={styles.plataforma}>

      {/* ── BARRA SUPERIOR ─────────────────────────────────────────────────── */}
      <header className={styles.topBar}>
        <div className={styles.topBarLeft}>
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
        </div>
      </header>

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
                  <span className={styles.pontoPulso} /> Monitorando
                </span>
              </div>

              <div className={styles.precoBloco}>
                <div className={styles.precoAtual}>
                  R$ {precoAtual.toLocaleString('pt-BR', { minimumFractionDigits: 2 })}
                </div>
                <div style={{ color: parseFloat(variacaoPorc) >= 0 ? '#22c55e' : '#ef4444', fontSize: '0.82rem', fontWeight: 600, marginTop: 2 }}>
                  {parseFloat(variacaoPorc) >= 0 ? '▲' : '▼'} {Math.abs(parseFloat(variacaoPorc))}% desde a entrada
                </div>
              </div>

              {/* LINHA DO TEMPO */}
              <div className={styles.linhaDoTempo}>
                <div className={styles.ldtTitulo}>Linha do Tempo</div>
                <div className={styles.ldtGrid}>
                  <div className={styles.ldtItem}>
                    <div className={styles.ldtLabel}>Sinal detectado</div>
                    <div className={styles.ldtValor}>{formatHora(operacaoAtiva.inicio)}</div>
                    <div className={styles.ldtSub}>{formatData(operacaoAtiva.inicio)}</div>
                  </div>
                  <div className={styles.ldtItem}>
                    <div className={styles.ldtLabel}>Tempo decorrido</div>
                    <div className={styles.ldtValor}
                      style={{ color: minutosDecorridos > 45 ? '#f59e0b' : '#22c55e' }}>
                      {duracaoTexto(operacaoAtiva.inicio)}
                    </div>
                    <div className={styles.ldtSub}>em andamento</div>
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
              {avaliacaoEntrada && (
                <div className={styles.dialogoOrquestrador}
                  style={{
                    borderLeftColor:
                      avaliacaoEntrada.urgencia === 'ok' ? '#22c55e' :
                      avaliacaoEntrada.urgencia === 'atencao' ? '#f59e0b' : '#ef4444',
                    background:
                      avaliacaoEntrada.urgencia === 'ok' ? 'rgba(34,197,94,0.06)' :
                      avaliacaoEntrada.urgencia === 'atencao' ? 'rgba(245,158,11,0.06)' :
                      'rgba(239,68,68,0.06)',
                  }}>
                  <div className={styles.dialogoEmoji}>
                    {avaliacaoEntrada.urgencia === 'ok' ? '🦉' :
                     avaliacaoEntrada.urgencia === 'atencao' ? '⚠️' : '🛑'}
                  </div>
                  <div>
                    <div className={styles.dialogoTitulo}
                      style={{
                        color: avaliacaoEntrada.urgencia === 'ok' ? '#22c55e' :
                               avaliacaoEntrada.urgencia === 'atencao' ? '#f59e0b' : '#ef4444',
                      }}>
                      {avaliacaoEntrada.urgencia === 'ok' ? 'Tucano diz: entrada ainda valida' :
                       avaliacaoEntrada.urgencia === 'atencao' ? 'Tucano diz: atencao antes de entrar' :
                       'Tucano diz: nao recomendado entrar agora'}
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
              )}

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
                    {modoAutomatico ? 'Sistema executa sem aprovacao manual' : 'Voce aprova cada operacao'}
                  </div>
                </div>
                <button className={`${styles.toggle} ${modoAutomatico ? styles.toggleOn : ''}`}
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

              {/* Botões */}
              <div className={styles.botoesOrdem}>
                <button className={styles.btnComprar}
                  onClick={() => { setModalOrdem('COMPRA'); setAceiteRisco(false) }}>
                  ▲ COMPRAR
                </button>
                <button className={styles.btnVender}
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
            <span className={styles.graficoTitulo}>{ativoSelecionado.nome} / BRL</span>

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

            <div className={styles.tfHintBlock}>
              <span className={styles.graficoSub}>{tfRow.strategy_hint}</span>
              {tfRow.strategy_family ? (
                <span className={styles.graficoFamilia} title={tfRow.strategy_family_note ?? undefined}>
                  Motor: {tfRow.strategy_family}
                </span>
              ) : null}
              {tfRow.agent_alignment ? (
                <span className={styles.graficoAgentAlign}>{tfRow.agent_alignment}</span>
              ) : null}
            </div>
          </div>

          {oportunidades.length > 0 && (
            <div className={styles.oppStrip}>
              <span className={styles.oppStripLabel}>
                {carregandoOport ? 'Atualizando' : 'Prioridade'}
              </span>
              <span className={styles.graficoAgentAlign} style={{ flexShrink: 0, marginRight: 6 }}>
                {timeframe} · acerto→score
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
                simboloTV={ativoSelecionado.tv}
                interval={tfRow.tv}
              />
            </div>
          </div>
        </main>

        {/* ── COLUNA DIREITA: AGENTES ─────────────────────────────────────── */}
        <aside className={styles.colunaDireita}>
          <div className={styles.agentesHeader}>
            <span className={styles.agentesTitulo}>Guardioes Boitata</span>
            <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
              {carregandoAnalise && <span className={styles.analisandoChip}>Analisando...</span>}
              {scoreFinal !== null && (
                <span style={{ fontSize: '1rem', fontWeight: 700, color: corScore(scoreFinal) }}>
                  {scoreFinal}/100
                </span>
              )}
            </div>
          </div>

          <div className={styles.agentesLista}>
            {agentes.map(a => (
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
                  {a.score !== null ? `${a.score}/100` : 'aguardando'}
                </div>
              </div>
            ))}
          </div>
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
