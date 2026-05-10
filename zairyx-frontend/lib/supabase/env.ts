function requireEnv(value: string | undefined, message: string) {
  if (!value) {
    throw new Error(message)
  }

  return value
}

export function getSupabaseUrl() {
  return requireEnv(
    process.env.NEXT_PUBLIC_SUPABASE_URL || process.env.SUPABASE_URL,
    'Missing Supabase URL. Set NEXT_PUBLIC_SUPABASE_URL.'
  )
}

export function getSupabasePublishableKey() {
  return requireEnv(
    process.env.NEXT_PUBLIC_SUPABASE_PUBLISHABLE_KEY ||
      process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY,
    'Missing Supabase publishable key. Set NEXT_PUBLIC_SUPABASE_PUBLISHABLE_KEY or NEXT_PUBLIC_SUPABASE_ANON_KEY.'
  )
}

export function getSupabaseServiceRoleKey() {
  return requireEnv(
    process.env.SUPABASE_SERVICE_ROLE_KEY || process.env.SUPABASE_SECRET_KEY,
    'Missing Supabase service role key. Set SUPABASE_SERVICE_ROLE_KEY.'
  )
}
