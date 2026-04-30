import { createClient as createSupabaseClient } from '@supabase/supabase-js'
import { getSupabaseServiceRoleKey, getSupabaseUrl } from '@/lib/supabase/env'

/**
 * Zairyx IA | Admin Supabase
 * Padrão de Projeto Herdado do Cardápio Digital (Operações Privilegiadas / Backend/Webhooks)
 * Bypassa o RLS via SERVICE_ROLE_KEY!
 */
export function createAdminClient() {
  return createSupabaseClient(
    getSupabaseUrl(),
    getSupabaseServiceRoleKey(),
    {
      auth: {
        autoRefreshToken: false,
        persistSession: false,
      }
    }
  )
}