import { createClient as createSupabaseClient } from '@supabase/supabase-js'

/**
 * Zairyx IA | Admin Supabase
 * Padrão de Projeto Herdado do Cardápio Digital (Operações Privilegiadas / Backend/Webhooks)
 * Bypassa o RLS via SERVICE_ROLE_KEY!
 */
export function createAdminClient() {
  return createSupabaseClient(
    process.env.NEXT_PUBLIC_SUPABASE_URL!,
    process.env.SUPABASE_SERVICE_ROLE_KEY!,
    {
      auth: {
        autoRefreshToken: false,
        persistSession: false,
      }
    }
  )
}