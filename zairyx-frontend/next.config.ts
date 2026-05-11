import type { NextConfig } from 'next'
import fs from 'node:fs'
import path from 'node:path'

/**
 * Chaves permitidas ao ler `../.env.local` (raiz do monorepo).
 * Objetivo: o Next não importar para o processo Node tokens só do backend
 * (Groq, Telegram, etc.) — esses ficam para o Python ler o mesmo ficheiro.
 * Amplie esta lista se adicionar novas variáveis usadas pelo zairyx-frontend.
 */
const PARENT_ENV_ALLOWLIST = new Set([
  'NEXT_PUBLIC_AI_API_URL',
  'NEXT_PUBLIC_API_BASE',
  'NEXT_PUBLIC_SUPABASE_URL',
  'NEXT_PUBLIC_SUPABASE_PUBLISHABLE_KEY',
  'NEXT_PUBLIC_SUPABASE_ANON_KEY',
  'NEXT_PUBLIC_MB_SIGNAL_ASSETS',
  'NEXT_PUBLIC_SITE_URL',
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

    if (!key || !PARENT_ENV_ALLOWLIST.has(key) || process.env[key]) {
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