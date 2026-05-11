'use client'
// E:\UNI.IA\zairyx-frontend\app\plataforma\PlataformaClient.tsx
// Boitatá IA Financas Brasil - Mesa Operacional
// BACEN Res. 519/520/521 | CVM Res. 30 | LGPD 13.709/2018

import { useState, useEffect, useRef, useCallback } from 'react'
import styles from './plataforma.module.css'

// Tipos
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

// Agentes - Guardioes da Amazonia
const AGENTES_BASE: Agente[] = [
  { id: 'ATLAS',     animal: 'Onca-Pintada',    emoji: '🐆', papel: 'Analise Tecnica',     score: null, voto: null },
  { id: 'MACRO',     animal: 'Harpia',           emoji: '🦅', papel: 'Contexto de Mercado', score: null, voto: null },
  { id: 'SENTIMENT', animal: 'Boto-Cor-de-Rosa', emoji: '🐬', papel: 'Sentimento',          score: null, voto: null },
  { id: 'NEWS',      animal: 'Arara Azul',       emoji: '🦜', papel: 'Noticias',            score: null, voto: null },
  { id: 'ARGUS',     animal: 'Capivara',         emoji: '🦫', papel: 'Volume e Fluxo',      score: null, voto: null },
  { id: 'SENTINEL',  animal: 'Jabuti',           emoji: '🐢', papel: 'Protecao de Capital', score: null, voto: null },
  { id: 'PUMA',      animal: 'Puma',             emoji: '🐱', papel: 'Monitoramento',       score: null, voto: null },
  { id: 'AEGIS',     animal: 'Tucano',           emoji: '🦉', papel: 'Fusao de Decisao',    score: null, voto: null },
]

// Ativos Mercado Bitcoin - seed inicial, resto carregado via API
const MB_ATIVOS_SEED: Ativo[] = [
  { simbolo: 'BTC-BRL',   nome: 'Bitcoin',       categoria: 'L1',         tv: 'MERCADOBITCOIN:BTCBRL' },
  { simbolo: 'ETH-BRL',   nome: 'Ethereum',      categoria: 'L1',         tv: 'MERCADOBITCOIN:ETHBRL' },
  { simbolo: 'SOL-BRL',   nome: 'Solana',        categoria: 'L1',         tv: 'MERCADOBITCOIN:SOLBRL' },
  { simbolo: 'BNB-BRL',   nome: 'BNB',           categoria: 'L1',         tv: 'MERCADOBITCOIN:BNBBRL' },
  { simbolo: 'XRP-BRL',   nome: 'Ripple',        categoria: 'Altcoin',    tv: 'MERCADOBITCOIN:XRPBRL' },
  { simbolo: 'ADA-BRL',   nome: 'Cardano',       categoria: 'L1',         tv: 'MERCADOBITCOIN:ADABRL' },
  { simbolo: 'DOT-BRL',   nome: 'Polkadot',      categoria: 'L1',         tv: 'MERCADOBITCOIN:DOTBRL' },
  { simbolo: 'AVAX-BRL',  nome: 'Avalanche',     categoria: 'L1',         tv: 'MERCADOBITCOIN:AVAXBRL' },
  { simbolo: 'LINK-BRL',  nome: 'Chainlink',     categoria: 'Altcoin',    tv: 'MERCADOBITCOIN:LINKBRL' },
  { simbolo: 'DOGE-BRL',  nome: 'Dogecoin',      categoria: 'Altcoin',    tv: 'MERCADOBITCOIN:DOGEBRL' },
  { simbolo: 'LTC-BRL',   nome: 'Litecoin',      categoria: 'Altcoin',    tv: 'MERCADOBITCOIN:LTCBRL' },
  { simbolo: 'MATIC-BRL', nome: 'Polygon',       categoria: 'L2',         tv: 'MERCADOBITCOIN:MATICBRL' },
  { simbolo: 'UNI-BRL',   nome: 'Uniswap',       categoria: 'DeFi',       tv: 'MERCADOBITCOIN:UNIBRL' },
  { simbolo: 'ATOM-BRL',  nome: 'Cosmos',        categoria: 'L1',         tv: 'MERCADOBITCOIN:ATOMBRL' },
  { simbolo: 'NEAR-BRL',  nome: 'NEAR Protocol', categoria: 'L1',         tv: 'MERCADOBITCOIN:NEARBRL' },
  { simbolo: 'ALGO-BRL',  nome: 'Algorand',      categoria: 'L1',         tv: 'MERCADOBITCOIN:ALGOBRL' },
  { simbolo: 'SAND-BRL',  nome: 'The Sandbox',   categoria: 'Metaverso',  tv: 'MERCADOBITCOIN:SANDBRL' },
  { simbolo: 'MANA-BRL',  nome: 'Decentraland',  categoria: 'Metaverso',  tv: 'MERCADOBITCOIN:MANABRL' },
  { simbolo: 'FTM-BRL',   nome: 'Fantom',        categoria: 'L1',         tv: 'MERCADOBITCOIN:FTMBRL' },
  { simbolo: 'USDT-BRL',  nome: 'Tether',        categoria: 'Stablecoin', tv: 'MERCADOBITCOIN:USDTBRL' },
  { simbolo: 'USDC-BRL',  nome: 'USD Coin',      categoria: 'Stablecoin', tv: 'MERCADOBITCOIN:USDCBRL' },
]

const API_BASE = 'http://127.0.0.1:8000'

// Helpers de tempo
function pad(n: number) { return String(n).padStart(2, '0') }
function formatHora(d: Date) { return `${pad(d.getHours())}:${pad(d.getMinutes())}:${pad(d.getSeconds())}` }
function formatData(d: Date) { return `${pad(d.getDate())}/${pad(d.getMonth()+1)}/${d.getFullYear()}` }
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

// ============================================================
// LOGICA CENTRAL: O que dizer ao investidor sobre entrada atrasada
//
// Principio da literatura de price action (TradingPedia, LiteFinance, ACY):
// "Se voce acredita que ainda estaria segurando porcao da posicao
//  apos escalar, entre com essa porcao e o mesmo stop-loss."
//
// O Orquestrador avalia:
// 1. Quanto do movimento ja ocorreu vs o esperado
// 2. Se o risco/retorno ainda justifica entrada
// 3. Se o preco atual esta melhor, igual ou pior que a entrada original
// 4. Emite orientacao em linguagem natural, clara e sem jargoes
// ============================================================
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
    return {
      podeEntrar: false,
      mensagem: 'Aguardando dados completos da operacao.',
      urgencia: 'atencao',
      movimentoConsumidoPorc: 0,
    }
  }

  // Operacao ja encerrada
  if (op.status === 'encerrada' || op.status === 'rejeitada') {
    return {
      podeEntrar: false,
      mensagem: `Esta operacao ja foi ${op.status === 'encerrada' ? 'encerrada' : 'rejeitada'}. Nao ha mais nada a fazer aqui. Aguarde o proximo sinal do Orquestrador.`,
      urgencia: 'perigo',
      movimentoConsumidoPorc: 100,
    }
  }

  const movimentoTotal = Math.abs(op.alvo - op.precoEntrada)
  const movimentoAtual = op.direcao === 'COMPRA'
    ? precoAtual - op.precoEntrada
    : op.precoEntrada - precoAtual

  const movimentoConsumidoPorc = movimentoTotal > 0
    ? Math.max(0, (movimentoAtual / movimentoTotal) * 100)
    : 0

  const variacaoPorcEntrada = op.direcao === 'COMPRA'
    ? ((precoAtual - op.precoEntrada) / op.precoEntrada) * 100
    : ((op.precoEntrada - precoAtual) / op.precoEntrada) * 100

  // --- PRECO MELHOROU (pullback) - oportunidade melhor que a original ---
  if (variacaoPorcEntrada < -0.3) {
    const melhoria = Math.abs(variacaoPorcEntrada).toFixed(2)
    return {
      podeEntrar: true,
      mensagem: `Otimo momento para entrar: o preco recuou ${melhoria}% desde o sinal (${minutosDecorridos} minutos atras), oferecendo uma entrada MELHOR do que a original. O movimento esperado continua valido. Stop em R$ ${op.stopLoss.toLocaleString('pt-BR')}, alvo em R$ ${op.alvo.toLocaleString('pt-BR')}.`,
      urgencia: 'ok',
      movimentoConsumidoPorc,
    }
  }

  // --- PRECO QUASE NO MESMO LUGAR - entrada normal ---
  if (movimentoConsumidoPorc <= 20) {
    return {
      podeEntrar: true,
      mensagem: `O sinal tem ${minutosDecorridos} minutos e o preco se moveu pouco desde entao (${movimentoConsumidoPorc.toFixed(0)}% do movimento esperado). A entrada ainda e valida com o mesmo risco da analise original. Stop em R$ ${op.stopLoss.toLocaleString('pt-BR')}, alvo em R$ ${op.alvo.toLocaleString('pt-BR')}.`,
      urgencia: 'ok',
      movimentoConsumidoPorc,
    }
  }

  // --- MOVIMENTO PARCIAL - entrada com tamanho reduzido ---
  if (movimentoConsumidoPorc <= 55) {
    return {
      podeEntrar: true,
      mensagem: `O sinal foi gerado ha ${minutosDecorridos} minutos e o preco ja percorreu ${movimentoConsumidoPorc.toFixed(0)}% do caminho esperado. Ainda ha espaco para lucro, mas o risco/retorno piorou. Se decidir entrar, use metade do tamanho normal de posicao com o mesmo stop em R$ ${op.stopLoss.toLocaleString('pt-BR')}. Alvo: R$ ${op.alvo.toLocaleString('pt-BR')}.`,
      urgencia: 'atencao',
      movimentoConsumidoPorc,
    }
  }

  // --- MOVIMENTO AVANCADO - nao recomendado ---
  if (movimentoConsumidoPorc <= 80) {
    return {
      podeEntrar: false,
      mensagem: `Nao recomendado entrar agora. O sinal ocorreu ha ${minutosDecorridos} minutos e ${movimentoConsumidoPorc.toFixed(0)}% do movimento ja aconteceu. Entrar neste momento seria perseguir o preco com risco de ser pego numa reversao. Aguarde a proxima oportunidade.`,
      urgencia: 'perigo',
      movimentoConsumidoPorc,
    }
  }

  // --- QUASE NO ALVO - perdida ---
  return {
    podeEntrar: false,
    mensagem: `Oportunidade encerrada. O preco ja percorreu ${movimentoConsumidoPorc.toFixed(0)}% do movimento esperado desde o sinal (${minutosDecorridos} minutos atras). Nao ha mais relacao risco/retorno favoravel. Acompanhe o proximo sinal.`,
    urgencia: 'perigo',
    movimentoConsumidoPorc,
  }
}

// Componente TradingView - embed correto 2025/2026 via script tag
function TradingViewChart({ simboloTV, agentesAtivos }: { simboloTV: string; agentesAtivos: string[] }) {
  const containerRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    if (!containerRef.current) return
    containerRef.current.innerHTML = ''

    // Mapear agentes para indicadores do grafico
    const estudos: string[] = []
    if (agentesAtivos.includes('ATLAS'))     { estudos.push('RSI@tv-basicstudies', 'BB@tv-basicstudies', 'MASimple@tv-basicstudies') }
    if (agentesAtivos.includes('ARGUS'))     { estudos.push('Volume@tv-basicstudies', 'VWAP@tv-basicstudies') }
    if (agentesAtivos.includes('MACRO'))     { estudos.push('MACD@tv-basicstudies') }
    if (agentesAtivos.includes('SENTIMENT')) { estudos.push('StochasticRSI@tv-basicstudies') }
    // Garantir indicadores basicos sempre presentes
    ['RSI@tv-basicstudies', 'Volume@tv-basicstudies', 'MACD@tv-basicstudies'].forEach(e => {
      if (!estudos.includes(e)) estudos.push(e)
    })

    const wrapper = document.createElement('div')
    wrapper.className = 'tradingview-widget-container'
    wrapper.style.cssText = 'height:100%;width:100%;'

    const inner = document.createElement('div')
    inner.className = 'tradingview-widget-container__widget'
    inner.style.cssText = 'height:100%;width:100%;'
    wrapper.appendChild(inner)

    // Embed via script tag - metodo correto TradingView 2025/2026
    const script = document.createElement('script')
    script.src = 'https://s3.tradingview.com/external-embedding/embed-widget-advanced-chart.js'
    script.async = true
    script.innerHTML = JSON.stringify({
      autosize: true,
      symbol: simboloTV,
      interval: '60',
      timezone: 'America/Sao_Paulo',
      theme: 'dark',
      style: '1',
      locale: 'pt',
      backgroundColor: 'rgba(7, 9, 10, 1)',
      gridColor: 'rgba(30, 41, 59, 0.4)',
      allow_symbol_change: false,
      calendar: false,
      studies: [...new Set(estudos)],
      hide_top_toolbar: false,
      hide_legend: false,
      support_host: 'https://www.tradingview.com',
    })
    wrapper.appendChild(script)
    containerRef.current.appendChild(wrapper)

    return () => {
      if (containerRef.current) containerRef.current.innerHTML = ''
    }
  }, [simboloTV, agentesAtivos.join(',')])

  return <div ref={containerRef} style={{ height: '100%', width: '100%' }} />
}

// Componente Principal
export default function PlataformaClient({ userEmail }: { userEmail: string }) {
  const [agentes, setAgentes] = useState<Agente[]>(AGENTES_BASE)
  const [ativos, setAtivos] = useState<Ativo[]>(MB_ATIVOS_SEED)
  const [ativoSelecionado, setAtivoSelecionado] = useState(MB_ATIVOS_SEED[0])
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
  const [dizimo, setDizimo] = useState<number | null>(null)
  const [now, setNow] = useState(new Date())
  const [carregandoAnalise, setCarregandoAnalise] = useState(false)
  const [abaEsquerda, setAbaEsquerda] = useState<'operacao' | 'ativos'>('operacao')

  // Relogio
  useEffect(() => {
    const id = setInterval(() => setNow(new Date()), 1000)
    return () => clearInterval(id)
  }, [])

  // Operacao ativa simulada (substituir por dados reais da API)
  useEffect(() => {
    setOperacaoAtiva({
      id: 'OP-2026-0509-001',
      ativo: ativoSelecionado.simbolo,
      nomeAtivo: ativoSelecionado.nome,
      direcao: 'COMPRA',
      status: 'monitorando',
      inicio: new Date(Date.now() - 1000 * 60 * 23),
      fim: null,
      precoEntrada: 412850,
      precoAtual: precoAtual,
      stopLoss: 404000,
      alvo: 428000,
      score: 87,
      motivo: 'Rompimento de resistencia em R$ 410.000 com volume 2,3x acima da media. RSI em 58 com espaco para subida. Medias de 20 e 50 periodos alinhadas para cima. Harpia confirma mercado global favoravel.',
      resultado: null,
    })
  }, [ativoSelecionado, precoAtual])

  // Preco oscilando em tempo real (simulado - substituir por WebSocket MB)
  useEffect(() => {
    const id = setInterval(() => {
      setPrecoAtual(p => +(p + (Math.random() - 0.48) * 180).toFixed(2))
    }, 2000)
    return () => clearInterval(id)
  }, [])

  // Carregar lista completa de ativos MB via API publica
  useEffect(() => {
    fetch('https://api.mercadobitcoin.net/api/v4/symbols')
      .then(r => r.json())
      .then((data: string[]) => {
        if (!Array.isArray(data)) return
        const extras: Ativo[] = data
          .filter((s: string) => s.endsWith('-BRL'))
          .filter((s: string) => !MB_ATIVOS_SEED.find(a => a.simbolo === s))
          .slice(0, 580)
          .map((s: string) => ({
            simbolo: s,
            nome: s.replace('-BRL', ''),
            categoria: 'Outro',
            tv: `MERCADOBITCOIN:${s.replace('-', '')}`,
          }))
        setAtivos([...MB_ATIVOS_SEED, ...extras])
      })
      .catch(() => { /* mantém seed */ })
  }, [])

  // Dizimo
  useEffect(() => {
    fetch(`${API_BASE}/api/dizimo/status`, { signal: AbortSignal.timeout(4000) })
      .then(r => r.ok ? r.json() : null)
      .then(d => d && setDizimo(d.dizimo_acumulado ?? 0))
      .catch(() => setDizimo(847.32))
  }, [])

  // Analise via API
  const buscarAnalise = useCallback(async (simbolo: string) => {
    setCarregandoAnalise(true)
    try {
      const r = await fetch(`${API_BASE}/api/analyze`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ asset: simbolo.replace('-BRL', '') + 'BRL', mode: 'swing' }),
        signal: AbortSignal.timeout(10000),
      })
      if (!r.ok) throw new Error()
      const data = await r.json()
      if (data.agent_scores) {
        setAgentes(prev => prev.map(a => ({
          ...a,
          score: data.agent_scores[a.id] ?? a.score,
          voto: (data.agent_scores[a.id] ?? 0) >= 75 ? 'COMPRA'
              : (data.agent_scores[a.id] ?? 0) >= 50 ? 'NEUTRO' : 'VENDA',
        })))
      }
    } catch {
      // Simular scores quando API offline
      setAgentes(AGENTES_BASE.map(a => {
        const s = Math.floor(50 + Math.random() * 40)
        return { ...a, score: s, voto: s >= 75 ? 'COMPRA' : s >= 50 ? 'NEUTRO' : 'VENDA' }
      }))
    } finally {
      setCarregandoAnalise(false)
    }
  }, [])

  useEffect(() => {
    buscarAnalise(ativoSelecionado.simbolo)
    const id = setInterval(() => buscarAnalise(ativoSelecionado.simbolo), 60000)
    return () => clearInterval(id)
  }, [ativoSelecionado.simbolo, buscarAnalise])

  // Confirmacao de ordem
  async function confirmarOrdem() {
    if (!modalOrdem) return
    const tipo = modalOrdem
    setModalOrdem(null)
    setAceiteRisco(false)
    try {
      await fetch(`${API_BASE}/api/desk/execute`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          asset: ativoSelecionado.simbolo.replace('-', ''),
          side: tipo === 'COMPRA' ? 'BUY' : 'SELL',
          risk_percent: riscoPorc,
          source: 'plataforma-web',
        }),
        signal: AbortSignal.timeout(10000),
      })
      mostrarToast(`Ordem de ${tipo} registrada - modo paper`, '#22c55e')
    } catch {
      mostrarToast('API offline - ordem registrada localmente (paper)', '#f59e0b')
    }
  }

  function mostrarToast(msg: string, cor: string) {
    setToast({ msg, cor })
    setTimeout(() => setToast(null), 6000)
  }

  // Avaliacao de entrada atrasada - O CORACAO DO ORCHESTRADOR
  const minutosDecorridos = operacaoAtiva ? minutosPassados(operacaoAtiva.inicio) : 0
  const avaliacaoEntrada = operacaoAtiva
    ? avaliarEntradaAtrasada(operacaoAtiva, precoAtual, minutosDecorridos)
    : null

  // Agentes que votaram compra (para indicadores do grafico)
  const agentesCompra = agentes.filter(a => a.voto === 'COMPRA').map(a => a.id)

  // Filtro de ativos
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
    COMPRA: '#22c55e', VENDA: '#ef4444', NEUTRO: '#f59e0b', APROVADO: '#22c55e', REJEITADO: '#ef4444'
  }

  return (
    <div className={styles.plataforma}>

      {/* BARRA SUPERIOR */}
      <header className={styles.topBar}>
        <div className={styles.topBarLeft}>
          <span className={styles.statusDot} />
          <span className={styles.topBarTitle}>Mesa Operacional</span>
          <span className={styles.topBarSep}>|</span>
          <span className={styles.topBarUser}>{userEmail}</span>
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
          {dizimo !== null && (
            <span className={styles.dizimoChip}>🌿 R$ {dizimo.toFixed(2)}</span>
          )}
          <span className={styles.relogio}>{formatData(now)} {formatHora(now)}</span>
        </div>
      </header>

      {/* LAYOUT PRINCIPAL */}
      <div className={styles.layout}>

        {/* COLUNA ESQUERDA */}
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

              {/* Header operacao */}
              <div className={styles.opHeader}>
                <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                  <span className={styles.opNome}>{operacaoAtiva.nomeAtivo}</span>
                  <span className={styles.badge}
                    style={{ background: operacaoAtiva.direcao === 'COMPRA' ? '#22c55e20' : '#ef444420',
                             color: operacaoAtiva.direcao === 'COMPRA' ? '#22c55e' : '#ef4444' }}>
                    {operacaoAtiva.direcao}
                  </span>
                </div>
                <span className={styles.badgePulso}>
                  <span className={styles.pontoPulso} /> Monitorando
                </span>
              </div>

              {/* Preco */}
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

              {/* CAIXA DE DIALOGO DO ORQUESTRADOR - peca central */}
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
                               avaliacaoEntrada.urgencia === 'atencao' ? '#f59e0b' : '#ef4444'
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
                                          avaliacaoEntrada.urgencia === 'atencao' ? '#f59e0b' : '#ef4444'
                            }}
                          />
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

              {/* Niveis */}
              <div className={styles.niveisGrid}>
                {[
                  { label: 'Entrada', valor: operacaoAtiva.precoEntrada, cor: '#3b82f6' },
                  { label: 'Limite de perda', valor: operacaoAtiva.stopLoss, cor: '#ef4444' },
                  { label: 'Alvo', valor: operacaoAtiva.alvo, cor: '#22c55e' },
                ].map(item => (
                  <div key={item.label} className={styles.nivelItem}
                    style={{ borderTopColor: item.cor }}>
                    <div className={styles.nivelLabel}>{item.label}</div>
                    <div className={styles.nivelValor} style={{ color: item.cor }}>
                      {item.valor ? `R$ ${item.valor.toLocaleString('pt-BR')}` : '—'}
                    </div>
                  </div>
                ))}
              </div>

              {/* Modo automatico */}
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

              {/* Botoes */}
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
                Toda operacao envolve risco de perda total do capital. Esta plataforma nao garante resultados.
                BACEN Res. 519/2025 e CVM Res. 30.
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

        {/* COLUNA CENTRAL: GRAFICO */}
        <main className={styles.colunaCentral}>
          <div className={styles.graficoHeader}>
            <span className={styles.graficoTitulo}>{ativoSelecionado.nome} / BRL</span>
            <div style={{ display: 'flex', gap: 6, flexWrap: 'wrap' }}>
              {['RSI', 'MACD', 'Bollinger', 'Volume', 'VWAP'].map(ind => (
                <span key={ind} className={styles.indChip}>{ind}</span>
              ))}
            </div>
            <span className={styles.graficoSub}>TradingView &middot; tempo real</span>
          </div>
          <div className={styles.graficoBox}>
            <TradingViewChart
              simboloTV={ativoSelecionado.tv}
              agentesAtivos={agentesCompra.length > 0 ? agentesCompra : ['ATLAS', 'ARGUS', 'MACRO']}
            />
          </div>
        </main>

        {/* COLUNA DIREITA: AGENTES */}
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
                    style={{
                      width: `${a.score ?? 0}%`,
                      background: corScore(a.score),
                    }}
                  />
                </div>
                <div className={styles.agenteScoreTexto}>
                  {a.score !== null ? `${a.score}/100` : 'aguardando'}
                </div>
              </div>
            ))}
          </div>

          {/* Dizimo */}
          <div className={styles.dizimoCard}>
            <div className={styles.dizimoTitulo}>🌿 Dizimo Amazonia</div>
            <div className={styles.dizimoValor}>R$ {(dizimo ?? 0).toFixed(2)}</div>
            <div className={styles.dizimoSub}>
              10% do lucro liquido protege animais da Amazonia
            </div>
          </div>
        </aside>
      </div>

      {/* MODAL DE CONFIRMACAO */}
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
              Criptoativos sao de alto risco. Voce pode perder parte ou todo o capital. O FGC nao cobre operacoes em criptoativos. Resultados passados nao garantem resultados futuros.
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

      {/* TOAST */}
      {toast && (
        <div className={styles.toast} style={{ borderLeftColor: toast.cor, color: toast.cor }}>
          {toast.msg}
        </div>
      )}
    </div>
  )
}