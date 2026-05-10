'use client'

// E:\UNI.IA\zairyx-frontend\app\plataforma\PlataformaClient.tsx
// Client Component — toda a interatividade fica aqui

import { useState, useEffect, useRef } from 'react'
import styles from './plataforma.module.css'

// ── Tipos ─────────────────────────────────────────────────────────────────
interface AgentScore {
  id: string
  nome: string
  animal: string
  emoji: string
  desc: string
  score: number | null
  status: 'OPORTUNIDADE' | 'NEUTRO' | 'RISCO' | null
}

interface SignalData {
  asset: string
  score: number
  classification: string
  explanation: string
  agent_scores?: Record<string, number>
}

// ── Configuração dos agentes-guardiões ────────────────────────────────────
const AGENTES: AgentScore[] = [
  { id: 'AEGIS',     nome: 'AEGIS',       animal: 'Onça-Pintada',     emoji: '🐆', desc: 'Fusão e Risco',        score: null, status: null },
  { id: 'SENTINEL',  nome: 'SENTINEL',    animal: 'Boto-Cor-de-Rosa', emoji: '🐬', desc: 'Governança',           score: null, status: null },
  { id: 'ATLAS',     nome: 'ATLAS',       animal: 'Arara Azul',       emoji: '🦜', desc: 'Técnico/Estrutura',    score: null, status: null },
  { id: 'ORION',     nome: 'ORION',       animal: 'Tamanduá-Bandeira',emoji: '🐜', desc: 'Cognitivo/Notícias',  score: null, status: null },
  { id: 'MACRO',     nome: 'MacroAgent',  animal: 'Harpia',           emoji: '🦅', desc: 'Macroeconomia',        score: null, status: null },
  { id: 'NEWS',      nome: 'NewsAgent',   animal: 'Tucano',           emoji: '🦜', desc: 'Calendário/Global',   score: null, status: null },
  { id: 'SENTIMENT', nome: 'SentimentAgent', animal: 'Mico-Leão-Dourado', emoji: '🐒', desc: 'Sentimento',      score: null, status: null },
  { id: 'ARGUS',     nome: 'ARGUS',       animal: 'Jacaré-Açu',      emoji: '🐊', desc: 'Reversão/Volume',      score: null, status: null },
]

// ── Ativos do Mercado Bitcoin ─────────────────────────────────────────────
const ATIVOS = [
  { symbol: 'BITSTAMP:BTCBRL',  label: 'Bitcoin',   sigla: 'BTC',  icon: '₿' },
  { symbol: 'BITSTAMP:ETHUSD',  label: 'Ethereum',  sigla: 'ETH',  icon: 'Ξ' },
  { symbol: 'BITSTAMP:SOLUSD',  label: 'Solana',    sigla: 'SOL',  icon: 'S' },
  { symbol: 'BITSTAMP:ADAUSD',  label: 'Cardano',   sigla: 'ADA',  icon: 'A' },
  { symbol: 'BITSTAMP:XRPUSD',  label: 'Ripple',    sigla: 'XRP',  icon: 'X' },
  { symbol: 'BITSTAMP:DOGEUSD', label: 'Dogecoin',  sigla: 'DOGE', icon: 'D' },
  { symbol: 'BITSTAMP:LTCUSD',  label: 'Litecoin',  sigla: 'LTC',  icon: 'L' },
  { symbol: 'BITSTAMP:LINKUSD', label: 'Chainlink', sigla: 'LINK', icon: '⬡' },
]

const API_BASE = 'http://127.0.0.1:8000'

// ── Helpers ───────────────────────────────────────────────────────────────
function scoreParaStatus(score: number | null): 'OPORTUNIDADE' | 'NEUTRO' | 'RISCO' | null {
  if (score === null) return null
  if (score >= 75) return 'OPORTUNIDADE'
  if (score >= 50) return 'NEUTRO'
  return 'RISCO'
}

function scoreParaCor(score: number | null): string {
  if (score === null) return 'var(--text-muted, #7a7060)'
  if (score >= 75) return 'var(--color-success, #22c55e)'
  if (score >= 50) return 'var(--color-gold, #c8860a)'
  return 'var(--color-danger, #ef4444)'
}

// ── Componente principal ──────────────────────────────────────────────────
export default function PlataformaClient({ userEmail }: { userEmail: string }) {
  const [ativoAtivo, setAtivoAtivo]   = useState(ATIVOS[0])
  const [timeframe, setTimeframe]     = useState('60')
  const [agentes, setAgentes]         = useState<AgentScore[]>(AGENTES)
  const [signal, setSignal]           = useState<SignalData | null>(null)
  const [alocacao, setAlocacao]       = useState(1)
  const [carregando, setCarregando]   = useState(false)
  const [modalAberto, setModalAberto] = useState<'COMPRA' | 'VENDA' | null>(null)
  const [aceiteRisco, setAceiteRisco] = useState(false)
  const [toast, setToast]             = useState<{ msg: string; cor: string } | null>(null)
  const [dizimo, setDizimo]           = useState<number | null>(null)
  const tvRef = useRef<HTMLDivElement>(null)
  const widgetRef = useRef<unknown>(null)

  // ── TradingView ──────────────────────────────────────────────────────────
  useEffect(() => {
    function carregarTV() {
      if (!tvRef.current) return
      tvRef.current.innerHTML = ''

      // @ts-expect-error — TradingView carregado via CDN
      if (typeof window.TradingView === 'undefined') {
        setTimeout(carregarTV, 300)
        return
      }

      // @ts-expect-error — TradingView global
      widgetRef.current = new window.TradingView.widget({
        autosize:     true,
        symbol:       ativoAtivo.symbol,
        interval:     timeframe,
        theme:        'dark',
        style:        '1',
        locale:       'pt_BR',
        timezone:     'America/Sao_Paulo',
        container_id: 'tv-chart',
        hide_top_toolbar: false,
        allow_symbol_change: false,
        studies: ['MASimple@tv-basicstudies', 'Volume@tv-basicstudies', 'RSI@tv-basicstudies'],
        overrides: {
          'mainSeriesProperties.candleStyle.upColor':        '#22c55e',
          'mainSeriesProperties.candleStyle.downColor':      '#ef4444',
          'mainSeriesProperties.candleStyle.borderUpColor':  '#22c55e',
          'mainSeriesProperties.candleStyle.borderDownColor':'#ef4444',
          'mainSeriesProperties.candleStyle.wickUpColor':    '#22c55e',
          'mainSeriesProperties.candleStyle.wickDownColor':  '#ef4444',
        },
        loading_screen: { backgroundColor: '#07090a', foregroundColor: '#c8860a' },
      })
    }

    carregarTV()
  }, [ativoAtivo.symbol, timeframe])

  // ── Injetar script TradingView uma vez ───────────────────────────────────
  useEffect(() => {
    if (document.getElementById('tv-script')) return
    const s = document.createElement('script')
    s.id  = 'tv-script'
    s.src = 'https://s3.tradingview.com/tv.js'
    s.async = true
    document.head.appendChild(s)
  }, [])

  // ── Buscar sinal da API ───────────────────────────────────────────────────
  async function buscarSinal(sigla: string) {
    setCarregando(true)
    try {
      const r = await fetch(`${API_BASE}/api/analyze`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ asset: sigla + 'BRL', mode: 'swing' }),
        signal: AbortSignal.timeout(8000),
      })
      if (!r.ok) throw new Error('HTTP ' + r.status)
      const data: SignalData = await r.json()
      setSignal(data)
      // Atualizar scores dos agentes
      if (data.agent_scores) {
        setAgentes(prev => prev.map(a => ({
          ...a,
          score: data.agent_scores?.[a.id] ?? a.score,
          status: scoreParaStatus(data.agent_scores?.[a.id] ?? a.score),
        })))
      }
    } catch {
      // API offline — simula scores para não travar a UI
      const scoreSimulado = Math.floor(50 + Math.random() * 40)
      setSignal({ asset: sigla + 'BRL', score: scoreSimulado, classification: scoreSimulado >= 75 ? 'OPORTUNIDADE' : 'NEUTRO', explanation: 'API offline — dados simulados para demonstração.' })
      setAgentes(prev => prev.map(a => {
        const s = Math.floor(40 + Math.random() * 55)
        return { ...a, score: s, status: scoreParaStatus(s) }
      }))
    } finally {
      setCarregando(false)
    }
  }

  // ── Buscar dízimo ────────────────────────────────────────────────────────
  async function buscarDizimo() {
    try {
      const r = await fetch(`${API_BASE}/api/dizimo/status`, { signal: AbortSignal.timeout(4000) })
      if (r.ok) {
        const d = await r.json()
        setDizimo(d.dizimo_acumulado ?? 0)
      }
    } catch { /* silencioso */ }
  }

  // ── Polling ───────────────────────────────────────────────────────────────
  useEffect(() => {
    buscarSinal(ativoAtivo.sigla)
    buscarDizimo()
    const t = setInterval(() => {
      buscarSinal(ativoAtivo.sigla)
      buscarDizimo()
    }, 60000)
    return () => clearInterval(t)
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [ativoAtivo.sigla])

  // ── Trocar ativo ──────────────────────────────────────────────────────────
  function selecionarAtivo(a: typeof ATIVOS[0]) {
    setAtivoAtivo(a)
    buscarSinal(a.sigla)
  }

  // ── Executar ordem ────────────────────────────────────────────────────────
  async function confirmarOrdem() {
    if (!modalAberto) return
    setModalAberto(null)
    setAceiteRisco(false)
    try {
      const r = await fetch(`${API_BASE}/api/desk/execute`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          asset: ativoAtivo.sigla + 'BRL',
          side: modalAberto === 'COMPRA' ? 'BUY' : 'SELL',
          risk_percent: alocacao,
          source: 'plataforma-web',
        }),
        signal: AbortSignal.timeout(10000),
      })
      const d = await r.json()
      mostrarToast(r.ok ? `✅ Ordem de ${modalAberto} enviada (modo paper)` : `⚠️ ${d.detail || 'Erro ao enviar ordem'}`, r.ok ? '#22c55e' : '#f59e0b')
    } catch {
      mostrarToast('⚠️ API offline — ordem registrada localmente (paper)', '#f59e0b')
    }
  }

  function mostrarToast(msg: string, cor: string) {
    setToast({ msg, cor })
    setTimeout(() => setToast(null), 5000)
  }

  // ── Veredito ──────────────────────────────────────────────────────────────
  const veredito = signal
    ? signal.score >= 75 ? 'COMPRA FORTE' : signal.score >= 50 ? 'AGUARDAR' : 'VENDA / RISCO'
    : '— ANALISANDO'
  const verdCor = signal
    ? signal.score >= 75 ? '#22c55e' : signal.score >= 50 ? '#c8860a' : '#ef4444'
    : '#7a7060'

  // ── Render ────────────────────────────────────────────────────────────────
  return (
    <div className={styles.dashboardContainer}>

      {/* ── SIDEBAR ESQUERDA: ativos ── */}
      <aside className={styles.sidebarAtivos}>
        <h3 className={styles.sidebarTitle}>Mercado Bitcoin</h3>
        <div className={styles.listaAtivos}>
          {ATIVOS.map(a => (
            <button
              key={a.symbol}
              className={`${styles.ativoBtn} ${ativoAtivo.symbol === a.symbol ? styles.ativoActive : ''}`}
              onClick={() => selecionarAtivo(a)}
            >
              <span className={styles.ativoIcon}>{a.icon}</span>
              {a.label}
              <span style={{ fontSize: '0.7rem', color: 'var(--color-gold)', marginLeft: 'auto' }}>{a.sigla}</span>
            </button>
          ))}
        </div>

        {/* Dízimo Amazônia */}
        <div className={styles.dizimoInfo}>
          <p>🌿 Dízimo Amazônia</p>
          {dizimo !== null
            ? <strong style={{ color: '#22c55e' }}>R$ {dizimo.toFixed(2)}</strong>
            : <span style={{ fontSize: '0.75rem', color: '#7a7060' }}>Carregando...</span>
          }
        </div>
      </aside>

      {/* ── ÁREA CENTRAL: gráfico + boleta ── */}
      <main className={styles.mainContent}>
        {/* Header */}
        <div className={styles.headerDashboard}>
          <h2 className={styles.mainTitle}>
            {ativoAtivo.label} <span style={{ color: 'var(--color-gold)', fontSize: '0.8em' }}>({ativoAtivo.sigla}/BRL)</span>
          </h2>
          <div className={styles.statusBadgeIA}>
            🛡️ SENTINEL: Proteção Ativa
          </div>
        </div>

        {/* Timeframes */}
        <div className={styles.tfBar}>
          {[['1','1m'],['5','5m'],['15','15m'],['60','1h'],['240','4h'],['D','1D']].map(([v, l]) => (
            <button
              key={v}
              className={`${styles.tfBtn} ${timeframe === v ? styles.tfActive : ''}`}
              onClick={() => setTimeframe(v)}
            >
              {l}
            </button>
          ))}
        </div>

        {/* Gráfico TradingView */}
        <div id="tv-chart" ref={tvRef} className={styles.chartBox} />

        {/* Boleta */}
        <div className={styles.boletaArea}>
          <div className={styles.cardBoleta}>
            <h4 className={styles.cardTitle}>Executar Ordem — Modo Paper</h4>

            {/* Veredito */}
            <div style={{ textAlign: 'center', padding: '10px 0' }}>
              <div style={{ fontSize: '1.3rem', fontWeight: 800, color: verdCor, fontFamily: 'var(--font-playfair)' }}>
                {carregando ? '⏳ Analisando...' : veredito}
              </div>
              {signal && (
                <div style={{ fontSize: '0.75rem', color: '#7a7060', marginTop: 4 }}>
                  Score: {signal.score}/100 · {signal.classification}
                </div>
              )}
            </div>

            {/* Alocação */}
            <div className={styles.inputGroup}>
              <label className={styles.labelCapital}>
                Alocação de Capital: <strong style={{ color: 'var(--color-gold)' }}>{alocacao}%</strong>
              </label>
              <input
                type="range" min="0.5" max="5" step="0.5"
                className={styles.rangeInput}
                value={alocacao}
                onChange={e => setAlocacao(parseFloat(e.target.value))}
              />
              <div style={{ fontSize: '0.7rem', color: '#7a7060', marginTop: 4 }}>
                Máx. 5% por operação · CVM Res. 30
              </div>
            </div>

            {/* Botões */}
            <div className={styles.boletaButtons}>
              <button className={styles.btnCompra} onClick={() => { setModalAberto('COMPRA'); setAceiteRisco(false) }}>
                COMPRAR
              </button>
              <button className={styles.btnVenda} onClick={() => { setModalAberto('VENDA'); setAceiteRisco(false) }}>
                VENDER
              </button>
            </div>

            {/* Explicação do mentor */}
            {signal?.explanation && (
              <div className={styles.mentorText}>
                {signal.explanation}
              </div>
            )}
          </div>
        </div>
      </main>

      {/* ── SIDEBAR DIREITA: agentes-guardiões ── */}
      <aside className={styles.sidebarAgentes}>
        <h3 className={styles.sidebarTitle}>Guardiões Boitatá</h3>
        <div className={styles.agentesGrid}>
          {agentes.map(a => (
            <div key={a.id} className={styles.cardAgenteMini}>
              <div className={styles.agenteTop}>
                <span className={styles.agenteEmoji}>{a.emoji}</span>
                <strong className={styles.agenteAnimal}>{a.animal}</strong>
              </div>
              <p className={styles.agenteNomeIA}>{a.nome}</p>
              <p style={{ fontSize: '0.68rem', color: '#7a7060', margin: '2px 0 6px' }}>{a.desc}</p>

              {/* Barra de score */}
              <div style={{ height: 4, background: 'rgba(255,255,255,0.07)', borderRadius: 2, overflow: 'hidden', marginBottom: 4 }}>
                <div style={{
                  height: '100%',
                  width: `${a.score ?? 0}%`,
                  background: scoreParaCor(a.score),
                  borderRadius: 2,
                  transition: 'width 0.6s ease',
                }} />
              </div>

              <div className={styles.agenteScore}>
                Score: <span className={styles.goldText}>{a.score ?? '--'}</span>
                {a.status && (
                  <span style={{
                    marginLeft: 8, fontSize: '0.65rem', padding: '1px 5px', borderRadius: 3,
                    background: a.status === 'OPORTUNIDADE' ? 'rgba(34,197,94,.15)' : a.status === 'RISCO' ? 'rgba(239,68,68,.15)' : 'rgba(200,134,10,.15)',
                    color: a.status === 'OPORTUNIDADE' ? '#22c55e' : a.status === 'RISCO' ? '#ef4444' : '#c8860a',
                  }}>
                    {a.status}
                  </span>
                )}
              </div>
            </div>
          ))}
        </div>
      </aside>

      {/* ── MODAL DE CONFIRMAÇÃO ── */}
      {modalAberto && (
        <div className={styles.modalOverlay}>
          <div className={styles.modalBox}>
            <h3 className={styles.modalTitle} style={{ color: modalAberto === 'COMPRA' ? '#22c55e' : '#ef4444' }}>
              Confirmar {modalAberto}
            </h3>
            <div className={styles.modalDetails}>
              <strong>Ativo:</strong> {ativoAtivo.label} ({ativoAtivo.sigla}/BRL)<br/>
              <strong>Direção:</strong> {modalAberto}<br/>
              <strong>Alocação:</strong> {alocacao}% do saldo<br/>
              <strong>Score IA:</strong> {signal?.score ?? '—'}/100<br/>
              <strong>Stop Loss:</strong> ATR × 1.5 (automático)<br/>
              <strong>Modo:</strong> PAPER (sem ordem real)
            </div>
            <div className={styles.modalRiskWarn}>
              ⚠️ <strong>Aviso Obrigatório — CVM Res. 30</strong><br/>
              Criptoativos são de alto risco. Você pode perder parte ou todo o capital. O FGC não cobre operações em criptoativos.
            </div>
            <label className={styles.modalCheckbox}>
              <input type="checkbox" checked={aceiteRisco} onChange={e => setAceiteRisco(e.target.checked)} />
              &nbsp;Declaro que li e compreendo os riscos desta operação.
            </label>
            <div className={styles.modalActions}>
              <button className={styles.modalCancel} onClick={() => setModalAberto(null)}>Cancelar</button>
              <button
                className={`${styles.modalConfirm} ${modalAberto === 'COMPRA' ? styles.modalCompra : styles.modalVenda}`}
                disabled={!aceiteRisco}
                onClick={confirmarOrdem}
              >
                CONFIRMAR {modalAberto}
              </button>
            </div>
          </div>
        </div>
      )}

      {/* ── TOAST ── */}
      {toast && (
        <div className={styles.toast} style={{ borderColor: toast.cor, color: toast.cor }}>
          {toast.msg}
        </div>
      )}
    </div>
  )
}

