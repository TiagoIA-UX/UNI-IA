import Image from 'next/image'
import { redirect } from 'next/navigation'
import { isAllowedPlatformEmail } from '@/lib/auth'
import { createClient } from '@/lib/supabase/server'
import riskFilterAggregation from '@/lib/risk-filter-aggregation.json'
import LiveSignalFeed from './live-signal-feed'
import styles from './plataforma.module.css'

type AggregateEntry = {
  count: number
  raw_signals_per_day: number
  executed_signals_per_day: number
  blocked_rate: number
  execution_rate: number
  drawdown_reduction_pct: number
  net_profit_delta_pct: number
  capital_protected: number
}

type ViewEntry = AggregateEntry & {
  blocked_rate_pct: number
  execution_rate_pct: number
}

type GateSummary = {
  status: 'PASS' | 'FAIL'
  pass_count: number
  fail_count: number
}

type ExecutiveCard = {
  id: string
  label: string
  value: number | string
  unit?: 'per_day' | 'pct' | 'currency'
  tone?: 'pass' | 'fail'
}

type AcceptanceGate = {
  id: string
  version: string
  label: string
  status: 'PASS' | 'FAIL'
  tone: 'pass' | 'fail'
  expected_classification: string
  observed_classification: string
  reason: string | null
}

type DimensionRow = ViewEntry & {
  classification: string
  timeframe: string
  mandate: string
  gate: GateSummary
}

type DayRow = ViewEntry & {
  day: string | null
  gate: GateSummary
}

type RegimeRow = ViewEntry & {
  version: string
  regime: string
  expected_classification: string
  observed_classification: string
  acceptance_status: 'PASS' | 'FAIL'
  gate: GateSummary
}

type AggregationSnapshot = {
  generated_at: string
  run_id: string
  schema_version: number
  integrity: {
    risk_filter_version: string
    runner_sha256: string
    snapshot_checksum: string
  }
  source_reports: string[]
  series: Array<{
    version: string
    regime: string
    dataset: string
    dataset_sha256: string
    strategy: string
    strategy_sha256: string | null
    mandate: string
    day: string | null
    timeframe: string
    classification: string
    criteria: {
      drawdown_reduction_threshold_pct: number
      net_profit_max_decline_pct: number
    }
    report_sha256: string
    runner_sha256: string
  }>
  aggregates: {
    overall: AggregateEntry
    by_day: Record<string, AggregateEntry>
    by_classification: Record<string, AggregateEntry>
    by_timeframe: Record<string, AggregateEntry>
    by_mandate: Record<string, AggregateEntry>
    by_version: Record<string, AggregateEntry>
    by_strategy: Record<string, AggregateEntry>
    by_day_classification: Record<string, AggregateEntry>
    by_timeframe_mandate: Record<string, AggregateEntry>
    by_classification_timeframe: Record<string, AggregateEntry>
    by_classification_timeframe_mandate: Record<string, AggregateEntry>
  }
  views: {
    executive_cards: ExecutiveCard[]
    acceptance_gates: AcceptanceGate[]
    tables: {
      by_dimension: {
        group_by: string[]
        rows: DimensionRow[]
      }
      by_day: {
        group_by: string[]
        rows: DayRow[]
      }
    }
    regimes: RegimeRow[]
    integrity: {
      datasets: Array<{ dataset: string; sha256: string }>
      strategies: Array<{ strategy: string; sha256: string | null }>
    }
  }
}

const aggregation = riskFilterAggregation as AggregationSnapshot

function formatExecutiveValue(card: ExecutiveCard): string {
  if (typeof card.value === 'string') return card.value
  if (card.unit === 'pct') return `${card.value.toFixed(2)}%`
  if (card.unit === 'currency') return card.value.toFixed(2)
  if (card.unit === 'per_day') return card.value.toFixed(2)
  return card.value.toString()
}

export default async function PlataformaPage() {
  const supabase = await createClient()
  const { data } = await supabase.auth.getUser()
  const user = data.user

  if (!user?.email) {
    redirect('/login?error=auth')
  }

  if (!isAllowedPlatformEmail(user.email)) {
    redirect('/login?error=unauthorized')
  }

  const rawPerDayCard = aggregation.views.executive_cards.find((card) => card.id === 'raw_signals_per_day')
  const rawPerDayValue =
    typeof rawPerDayCard?.value === 'number' ? rawPerDayCard.value.toFixed(2) : String(rawPerDayCard?.value ?? '-')

  return (
    <div className={styles.root}>
      <section className={styles.heroSection}>
        <div className={styles.heroCopy}>
          <p className={styles.badge}>Validation panel</p>
          <h1 className={styles.heroTitle}>Painel institucional de validacao do RiskFilter</h1>
          <p className={styles.heroDesc}>
            O painel consolida performance, comportamento estrutural e integridade tecnica a partir de um snapshot
            imutavel e exibe bias em tempo real alinhado a fluxo Bybit (sem agregacao, derivacao ou placeholders no front).
          </p>
          <div className={styles.heroStats}>
            <div className={styles.statCard}>
              <p className={styles.statLabel}>Sessao autenticada</p>
              <p className={styles.statValue}>Conta autorizada conectada</p>
            </div>
            <div className={styles.statCard}>
              <p className={styles.statLabel}>Serie congelada</p>
              <p className={styles.statValue}>{aggregation.series.length} cortes validados</p>
            </div>
            <div className={styles.statCard}>
              <p className={styles.statLabel}>Raw signals / day</p>
              <p className={styles.statValue}>{rawPerDayValue}</p>
            </div>
          </div>
        </div>
        <div className={styles.heroImageBox}>
          <Image
            src='/trading-desk-hero.svg'
            alt='Painel privado da plataforma UNI IA'
            width={1200}
            height={900}
            priority
            className={styles.heroImg}
          />
        </div>
      </section>

      <section className={styles.kpiGrid}>
        {aggregation.views.executive_cards.map((card) => (
          <div key={card.id} className={`${styles.kpiCard} ${card.tone ? styles[card.tone] : ''}`}>
            <p className={styles.kpiLabel}>{card.label}</p>
            <p className={styles.kpiValue}>{formatExecutiveValue(card)}</p>
            <p className={styles.kpiNote}>Valor direto do snapshot (render apenas).</p>
          </div>
        ))}
      </section>

      <section className={styles.liveFeedSection}>
        <LiveSignalFeed />
      </section>

      <section className={styles.gateSection}>
        <div className={styles.sectionHeader}>
          <h2 className={styles.sectionTitle}>Acceptance gates</h2>
          <p className={styles.sectionDesc}>Regras deterministicas por regime, calculadas no agregador.</p>
        </div>
        <div className={styles.gateGrid}>
          {aggregation.views.acceptance_gates.map((gate) => (
            <div key={gate.id} className={`${styles.gateCard} ${styles[gate.tone]}`}>
              <p className={styles.gateLabel}>{gate.label}</p>
              <p className={styles.gateValue}>{gate.status}</p>
            </div>
          ))}
        </div>
      </section>

      <section className={styles.windowSection}>
        <div className={styles.sectionHeader}>
          <h2 className={styles.sectionTitle}>Tabela por dimensao</h2>
          <p className={styles.sectionDesc}>Agrupada por classification, timeframe e mandate (sem agregacao no React).</p>
        </div>
        <div className={styles.tableWrap}>
          <table className={styles.table}>
            <thead>
              <tr>
                <th>classification</th>
                <th>timeframe</th>
                <th>mandate</th>
                <th>raw/day</th>
                <th>executed/day</th>
                <th>blocked %</th>
                <th>ΔDD medio</th>
                <th>gate</th>
              </tr>
            </thead>
            <tbody>
              {aggregation.views.tables.by_dimension.rows.map((row) => (
                <tr key={`${row.classification}|${row.timeframe}|${row.mandate}`}>
                  <td>{row.classification}</td>
                  <td>{row.timeframe}</td>
                  <td>{row.mandate}</td>
                  <td>{row.raw_signals_per_day.toFixed(2)}</td>
                  <td>{row.executed_signals_per_day.toFixed(2)}</td>
                  <td>{row.blocked_rate_pct.toFixed(2)}%</td>
                  <td>{row.drawdown_reduction_pct.toFixed(2)}%</td>
                  <td>
                    <span className={`${styles.tablePill} ${row.gate.status === 'PASS' ? styles.pass : styles.fail}`}>
                      {row.gate.status}
                    </span>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </section>

      <section className={styles.gateSection}>
        <div className={styles.sectionHeader}>
          <h2 className={styles.sectionTitle}>Por dia</h2>
          <p className={styles.sectionDesc}>Dimensao day explicitada diretamente do snapshot.</p>
        </div>
        <div className={styles.tableWrap}>
          <table className={styles.table}>
            <thead>
              <tr>
                <th>day</th>
                <th>raw/day</th>
                <th>executed/day</th>
                <th>blocked %</th>
                <th>ΔDD medio</th>
                <th>gate</th>
              </tr>
            </thead>
            <tbody>
              {aggregation.views.tables.by_day.rows.map((row) => (
                <tr key={row.day ?? 'unknown'}>
                  <td>{row.day ?? 'unknown'}</td>
                  <td>{row.raw_signals_per_day.toFixed(2)}</td>
                  <td>{row.executed_signals_per_day.toFixed(2)}</td>
                  <td>{row.blocked_rate_pct.toFixed(2)}%</td>
                  <td>{row.drawdown_reduction_pct.toFixed(2)}%</td>
                  <td>
                    <span className={`${styles.tablePill} ${row.gate.status === 'PASS' ? styles.pass : styles.fail}`}>
                      {row.gate.status}
                    </span>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </section>

      <section className={styles.windowSection}>
        <div className={styles.sectionHeader}>
          <h2 className={styles.sectionTitle}>Distribuicao por janela</h2>
          <p className={styles.sectionDesc}>Regimes e classificacoes carregados do snapshot.</p>
        </div>
        <div className={styles.windowGrid}>
          {aggregation.views.regimes.map((item) => (
            <article key={item.version} className={styles.windowCard}>
              <div className={styles.windowTop}>
                <div>
                  <p className={styles.windowVersion}>{item.version}</p>
                  <p className={styles.windowRegime}>{item.regime}</p>
                </div>
                <span
                  className={`${styles.classificationPill} ${
                    styles[item.observed_classification === 'NEUTRAL' ? 'neutral' : 'protective']
                  }`}
                >
                  {item.observed_classification}
                </span>
              </div>
              <div className={styles.barTrack}>
                <div className={styles.barFill} style={{ width: `${Math.max(item.drawdown_reduction_pct, 0)}%` }} />
              </div>
              <div className={styles.windowStats}>
                <span>ΔDD {item.drawdown_reduction_pct.toFixed(2)}%</span>
                <span>Blocked {item.blocked_rate_pct.toFixed(2)}%</span>
              </div>
              <p className={styles.windowFootnote}>
                Gate {item.acceptance_status} | Capital protegido: {item.capital_protected.toFixed(2)} | Execucao:{' '}
                {item.execution_rate_pct.toFixed(2)}%
              </p>
            </article>
          ))}
        </div>
      </section>

      <section className={styles.gateSection}>
        <div className={styles.sectionHeader}>
          <h2 className={styles.sectionTitle}>Integridade</h2>
          <p className={styles.sectionDesc}>Run, filtro, datasets e checksum do snapshot (cadeia de custodia).</p>
        </div>
        <div className={styles.gateGrid}>
          <div className={styles.gateCard}>
            <p className={styles.gateLabel}>Run ID</p>
            <p className={styles.gateValue}>{aggregation.run_id}</p>
          </div>
          <div className={styles.gateCard}>
            <p className={styles.gateLabel}>Risk filter version</p>
            <p className={styles.gateValue}>{aggregation.integrity.risk_filter_version}</p>
          </div>
          <div className={styles.gateCard}>
            <p className={styles.gateLabel}>Snapshot checksum</p>
            <p className={styles.gateValue}>{aggregation.integrity.snapshot_checksum.slice(0, 12)}...</p>
          </div>
          <div className={styles.gateCard}>
            <p className={styles.gateLabel}>Runner hash</p>
            <p className={styles.gateValue}>{aggregation.integrity.runner_sha256.slice(0, 12)}...</p>
          </div>
          {aggregation.views.integrity.datasets.map((dataset) => (
            <div key={dataset.dataset} className={styles.gateCard}>
              <p className={styles.gateLabel}>Dataset hash</p>
              <p className={styles.gateValue}>
                {dataset.dataset} {dataset.sha256.slice(0, 12)}...
              </p>
            </div>
          ))}
        </div>
      </section>
    </div>
  )
}
