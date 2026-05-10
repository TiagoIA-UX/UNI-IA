import { createBrowserClient } from '@supabase/ssr'
import { getSupabasePublishableKey, getSupabaseUrl } from '@/lib/supabase/env'

/**
 * Zairyx IA | Client Supabase
 * Padrão de Projeto Herdado do Cardápio Digital (Regra Browser)
 * import { createClient } from '@/lib/supabase/client' -> createClient()
 */
export function createClient() {
  return createBrowserClient(
    getSupabaseUrl(),
    getSupabasePublishableKey()
  )
}