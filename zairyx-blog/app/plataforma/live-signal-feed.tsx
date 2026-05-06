'use client'

import { useEffect, useState } from 'react'
import styles from './plataforma.module.css'

type BybitSignal = {
  symbol: string
  timeframe: string
  price: number
  signal: 'LONG' | 'SHORT' | 'NEUTRAL'
  confidence: number
  momentum: number
  volatility: number
}

type FeedResponse = {
  success: boolean
  updatedAt?: string
  data?: BybitSignal[]
  error?: string
}

function formatPrice(value: number) {
  return value.toLocaleString(undefined, {
    minimumFractionDigits: value >= 1000 ? 2 : 2,
    maximumFractionDigits: 2,
  })
}

function formatPercent(value: number) {
  return `${value.toFixed(1)}%`
}

export default function LiveSignalFeed() {
  const [feed, setFeed] = useState<BybitSignal[] | null>(null)
  const [updatedAt, setUpdatedAt] = useState<string | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [loading, setLoading] = useState(true)

  const fetchFeed = async () => {
    setLoading(true)
    setError(null)

    try {
      const response = await fetch('/api/bybit/signals', { cache: 'no-store' })
      const payload = (await response.json()) as FeedResponse

      if (!response.ok || !payload.success) {
        setError(payload.error || 'Failed to load live feed.')
        setFeed(null)
        return
      }

      setFeed(payload.data ?? null)
      setUpdatedAt(payload.updatedAt ?? null)
    } catch (err) {
      setError('Live feed unavailable. Check network or API connectivity.')
      setFeed(null)
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    fetchFeed()
    const interval = window.setInterval(fetchFeed, 15000)
    return () => window.clearInterval(interval)
  }, [])

  return (
    <div className={styles.liveFeedContainer}>
      <div className={styles.sectionHeader}>
        <h2 className={styles.sectionTitle}>Real-time Bybit signal feed</h2>
        <p className={styles.sectionDesc}>
          Live Bybit market structure, momentum and volatility are sampled every 15 seconds and translated into an institutional signal bias.
        </p>
      </div>

      <div className={styles.liveFeedMeta}>
        <span>Fonte: Bybit Public API</span>
        <span>{loading ? 'Atualizando...' : updatedAt ? `Última atualização: ${new Date(updatedAt).toLocaleTimeString()}` : 'Atualização pendente'}</span>
      </div>

      <div className={styles.liveFeedWrapper}>
        <table className={styles.liveFeedTable}>
          <thead>
            <tr>
              <th>Symbol</th>
              <th>Bias</th>
              <th>Preço</th>
              <th>Confiança</th>
              <th>Momento</th>
              <th>Volatilidade</th>
            </tr>
          </thead>
          <tbody>
            {feed?.map((signal) => (
              <tr key={signal.symbol}>
                <td>{signal.symbol}</td>
                <td>
                  <span
                    className={
                      signal.signal === 'LONG'
                        ? styles.pass
                        : signal.signal === 'SHORT'
                        ? styles.fail
                        : styles.pending
                    }
                  >
                    {signal.signal}
                  </span>
                </td>
                <td>{formatPrice(signal.price)}</td>
                <td>{formatPercent(signal.confidence)}</td>
                <td>{formatPercent(signal.momentum)}</td>
                <td>{formatPercent(signal.volatility)}</td>
              </tr>
            ))}
          </tbody>
        </table>

        {error ? (
          <p className={styles.errorMessage}>{error}</p>
        ) : null}

        {!feed?.length && !loading && !error ? (
          <p className={styles.errorMessage}>No live signal data available.</p>
        ) : null}
      </div>
    </div>
  )
}
