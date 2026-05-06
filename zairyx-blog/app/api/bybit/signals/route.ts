import { NextResponse } from 'next/server'

const BYBIT_BASE_URL = 'https://api.bybit.com'
const SYMBOLS = ['BTCUSDT', 'ETHUSDT', 'SOLUSDT']
const INTERVAL = '15m'

type BybitKline = {
  id: string
  open: string
  high: string
  low: string
  close: string
  volume: string
  turnover: string
  start: string
  end: string
}

type BybitResponse = {
  retCode: number
  retMsg: string
  result: {
    list: BybitKline[]
  }
}

type BybitSignal = {
  symbol: string
  timeframe: string
  price: number
  signal: 'LONG' | 'SHORT' | 'NEUTRAL'
  confidence: number
  momentum: number
  volatility: number
}

function safeNumber(value: string | number) {
  const parsed = typeof value === 'string' ? Number(value) : value
  return Number.isFinite(parsed) ? parsed : 0
}

function average(values: number[]) {
  if (values.length === 0) return 0
  return values.reduce((sum, value) => sum + value, 0) / values.length
}

function standardDeviation(values: number[]) {
  if (values.length === 0) return 0
  const mean = average(values)
  const variance = average(values.map((value) => Math.pow(value - mean, 2)))
  return Math.sqrt(variance)
}

function buildSignal(symbol: string, list: BybitKline[]): BybitSignal {
  const closes = list.map((item) => safeNumber(item.close)).filter((value) => value > 0)
  const last = closes[closes.length - 1] ?? 0
  const previous = closes[closes.length - 2] ?? last
  const sma10 = average(closes.slice(-10))
  const sma20 = average(closes.slice(-20))
  const momentum = previous > 0 ? ((last - previous) / previous) * 100 : 0
  const returns = closes.slice(1).map((value, index) => {
    const prior = closes[index]
    return prior > 0 ? (value - prior) / prior : 0
  })
  const volatility = standardDeviation(returns) * 100

  const isBullish = last >= sma10 && last >= sma20
  const isBearish = last <= sma10 && last <= sma20
  const signal: BybitSignal['signal'] = isBullish ? 'LONG' : isBearish ? 'SHORT' : 'NEUTRAL'
  const confidence = Math.min(100, Math.max(10, Math.abs((last - sma20) / Math.max(sma20, 1)) * 200))

  return {
    symbol,
    timeframe: INTERVAL,
    price: Number(last.toFixed(2)),
    signal,
    confidence: Number(confidence.toFixed(0)),
    momentum: Number(momentum.toFixed(2)),
    volatility: Number(volatility.toFixed(2)),
  }
}

async function fetchKlines(symbol: string) {
  const url = `${BYBIT_BASE_URL}/v5/market/kline?symbol=${encodeURIComponent(symbol)}&interval=${INTERVAL}&limit=20`
  const response = await fetch(url, { cache: 'no-store' })
  const payload = (await response.json()) as BybitResponse
  if (payload.retCode !== 0 || !payload.result?.list) {
    throw new Error(`Bybit response error for ${symbol}: ${payload.retMsg || 'unexpected payload'}`)
  }
  return payload.result.list
}

export async function GET() {
  try {
    const signals = await Promise.all(
      SYMBOLS.map(async (symbol) => {
        const list = await fetchKlines(symbol)
        return buildSignal(symbol, list)
      })
    )

    return NextResponse.json({
      success: true,
      updatedAt: new Date().toISOString(),
      data: signals,
    })
  } catch (error) {
    return NextResponse.json(
      {
        success: false,
        error: error instanceof Error ? error.message : 'Unknown error while fetching Bybit feed.',
      },
      { status: 500 }
    )
  }
}
