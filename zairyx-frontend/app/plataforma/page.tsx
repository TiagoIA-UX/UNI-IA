'use client'

import React, { useEffect, useRef, useState } from 'react'
import Image from 'next/image'
import styles from './plataforma.module.css'

// Mapeamento dos Guardiões conforme SI
const GUARDIÕES = [
  { id: 'AEGIS', nome: 'AEGIS', animal: 'Onça-Pintada', emoji: '🐆', desc: 'Fusão e Risco' },
  { id: 'SENTINEL', nome: 'SENTINEL', animal: 'Boto-Cor-de-Rosa', emoji: '🐬', desc: 'Governança' },
  { id: 'ATLAS', nome: 'ATLAS', animal: 'Arara Azul', emoji: '🦜', desc: 'Técnico/Estrutura' },
  { id: 'ORION', nome: 'ORION', animal: 'Tamanduá-Bandeira', emoji: '🐜', desc: 'Cognitivo/Notícias' },
  { id: 'MACRO', nome: 'MacroAgent', animal: 'Harpia', emoji: '🦅', desc: 'Macroeconomia' },
  { id: 'NEWS', nome: 'NewsAgent', animal: 'Tucano', emoji: '🦜', desc: 'Calendário/Global' },
  { id: 'SENTIMENT', nome: 'SentimentAgent', animal: 'Mico-Leão-Dourado', emoji: '🐒', desc: 'Sentimento' },
  { id: 'ARGUS', nome: 'ARGUS', animal: 'Jacaré-Açu', emoji: '🐊', desc: 'Reversão/Volume' },
]

const ATIVOS_MB = [
  { symbol: 'MERCADOBITCOIN:BTCBRL', label: 'Bitcoin', icon: '₿' },
  { symbol: 'MERCADOBITCOIN:ETHBRL', label: 'Ethereum', icon: 'Ξ' },
  { symbol: 'MERCADOBITCOIN:SOLBRL', label: 'Solana', icon: 'S' },
  { symbol: 'MERCADOBITCOIN:ADABRL', label: 'Cardano', icon: 'A' },
]

export default function PlataformaPage() {
  const [ativo, setAtivo] = useState('MERCADOBITCOIN:BTCBRL')
  const [statusIA, setStatusIA] = useState<any>(null)
  const [capitalPct, setCapitalPct] = useState(1)
  const containerRef = useRef<HTMLDivElement>(null)

  // Polling para os Agentes (30s)
  useEffect(() => {
    const fetchData = async () => {
      try {
        const res = await fetch('/api/signals/status')
        const data = await res.json()
        setStatusIA(data)
      } catch (e) { console.error("Erro ao buscar sinais", e) }
    }
    fetchData()
    const interval = setInterval(fetchData, 30000)
    return () => clearInterval(interval)
  }, [])

  // Injeção do TradingView
  useEffect(() => {
    const script = document.createElement('script')
    script.src = 'https://s3.tradingview.com/tv.js'
    script.async = true
    script.onload = () => {
      if (typeof window.TradingView !== 'undefined' && containerRef.current) {
        new window.TradingView.widget({
          autosize: true,
          symbol: ativo,
          interval: '60',
          timezone: 'America/Sao_Paulo',
          theme: 'dark',
          style: '1',
          locale: 'br',
          toolbar_bg: '#0a0a0a',
          enable_publishing: false,
          hide_side_toolbar: false,
          allow_symbol_change: true,
          container_id: containerRef.current.id,
          studies: [
            'MASimple@tv-basicstudies', // ATLAS (EMA)
            'BB@tv-basicstudies',       // ATLAS (Bollinger)
            'StochasticRSI@tv-basicstudies', // SENTINEL
            'VWAP@tv-basicstudies'      // ARGUS
          ],
        })
      }
    }
    document.head.appendChild(script)
    return () => { script.remove() }
  }, [ativo])

  return (
    <div className={styles.dashboardContainer}>
      {/* Sidebar de Ativos */}
      <aside className={styles.sidebarAtivos}>
        <h3 className={styles.sidebarTitle}>Mercado Bitcoin</h3>
        <div className={styles.listaAtivos}>
          {ATIVOS_MB.map((item) => (
            <button 
              key={item.symbol} 
              className={`${styles.ativoBtn} ${ativo === item.symbol ? styles.ativoActive : ''}`}
              onClick={() => setAtivo(item.symbol)}
            >
              <span className={styles.ativoIcon}>{item.icon}</span>
              {item.label}
            </button>
          ))}
        </div>
        
        <div className={styles.dizimoInfo}>
          <p>🌳 10% de dízimo para a Amazônia</p>
        </div>
      </aside>

      {/* Área Central: Gráfico + Boletas */}
      <main className={styles.mainContent}>
        <div className={styles.headerDashboard}>
          <h2>Operação em Modo Paper (Simulação)</h2>
          <div className={styles.statusBadgeIA}>SENTINEL: Proteção Ativa 🛡️</div>
        </div>

        <div id="tradingview_widget" ref={containerRef} className={styles.chartBox} />

        <div className={styles.boletaArea}>
          <div className={styles.cardBoleta}>
            <h4>Execução de Ordem</h4>
            <div className={styles.inputGroup}>
              <label>Capital: {capitalPct}%</label>
              <input 
                type="range" min="1" max="5" step="0.5" 
                value={capitalPct} onChange={(e) => setCapitalPct(parseFloat(e.target.value))} 
              />
            </div>
            <div className={styles.boletaButtons}>
              <button className={styles.btnCompra}>COMPRAR</button>
              <button className={styles.btnVenda}>VENDER</button>
            </div>
          </div>
        </div>
      </main>

      {/* Painel Lateral dos Agentes */}
      <aside className={styles.sidebarAgentes}>
        <h3 className={styles.sidebarTitle}>Guardiões Boitatá</h3>
        <div className={styles.agentesGrid}>
          {GUARDIÕES.map((ag) => (
            <div key={ag.id} className={`${styles.cardAgenteMini} agente-${ag.id.toLowerCase()}`}>
              <div className={styles.agenteTop}>
                <span>{ag.emoji}</span>
                <strong>{ag.animal}</strong>
              </div>
              <p className={styles.agenteNomeIA}>{ag.nome}</p>
              <div className={styles.agenteScore}>
                Score: <span className={styles.goldText}>{statusIA?.scores?.[ag.id] || '--'}</span>
              </div>
            </div>
          ))}
        </div>
      </aside>
    </div>
  )
}