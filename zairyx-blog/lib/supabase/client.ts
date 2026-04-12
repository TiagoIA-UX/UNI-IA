import { createBrowserClient } from '@supabase/ssr'

/**
 * Zairyx IA | Client Supabase
 * Padrão de Projeto Herdado do Cardápio Digital (Regra Browser)
 * import { createClient } from '@/lib/supabase/client' -> createClient()
 */
export function createClient() {
  return createBrowserClient(
    process.env.NEXT_PUBLIC_SUPABASE_URL!,
    process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY!
  )
}