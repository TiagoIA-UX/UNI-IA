import type { NextConfig } from 'next'
import fs from 'node:fs'
import path from 'node:path'

/**
 * Chaves não públicas permitidas ao ler `../.env.local` (raiz do monorepo).
 * Tudo o que começa por `NEXT_PUBLIC_` também é aceite (wildcard), para não
 * quebrar novas variáveis públicas nem URLs alternativas da API.
 * Tokens só de backend (Groq, Telegram, etc.) não entram aqui.
 */
const PARENT_ENV_SERVER_ALLOWLIST = new Set([
  'SUPABASE_URL',
  'SUPABASE_SERVICE_ROLE_KEY',
  'SUPABASE_SECRET_KEY',
  'ALLOWED_PLATFORM_EMAILS',
  'BROKER_API_BASE_URL',
  'BYBIT_SIGNAL_ASSETS',
  'BYBIT_SIGNAL_INTERVAL',
  'CRON_SECRET',
  'RESEND_API_KEY',
  'RESEND_FROM_EMAIL',
])

function isParentEnvKeyAllowed(key: string): boolean {
  return key.startsWith('NEXT_PUBLIC_') || PARENT_ENV_SERVER_ALLOWLIST.has(key)
}

function loadParentEnvFile() {
  const envPath = path.join(__dirname, '..', '.env.local')

  if (!fs.existsSync(envPath)) {
    return
  }

  const envContent = fs.readFileSync(envPath, 'utf8')
  const lines = envContent.split(/\r?\n/)

  for (const rawLine of lines) {
    const line = rawLine.trim()

    if (!line || line.startsWith('#')) {
      continue
    }

    const separatorIndex = line.indexOf('=')
    if (separatorIndex <= 0) {
      continue
    }

    const key = line.slice(0, separatorIndex).trim()
    let value = line.slice(separatorIndex + 1).trim()

    if (!key || !isParentEnvKeyAllowed(key) || process.env[key]) {
      continue
    }

    if (
      (value.startsWith('"') && value.endsWith('"')) ||
      (value.startsWith("'") && value.endsWith("'"))
    ) {
      value = value.slice(1, -1)
    }

    process.env[key] = value
  }
}

loadParentEnvFile()

const nextConfig: NextConfig = {}

export default nextConfig