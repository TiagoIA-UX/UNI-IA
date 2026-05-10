import { createServerClient, type CookieOptions } from '@supabase/ssr'
import { cookies } from 'next/headers'
import { getSupabasePublishableKey, getSupabaseUrl } from '@/lib/supabase/env'

/**
 * Zairyx IA | Server Supabase
 * Padrão de Projeto Herdado do Cardápio Digital (Regra Server Components/Actions)
 * import { createClient } from '@/lib/supabase/server' -> await createClient()
 */
export async function createClient() {
  const cookieStore = await cookies()

  return createServerClient(
    getSupabaseUrl(),
    getSupabasePublishableKey(),
    {
      cookies: {
        getAll() {
          return cookieStore.getAll()
        },
        setAll(cookiesToSet) {
          try {
            cookiesToSet.forEach(({ name, value, options }: { name: string; value: string; options: CookieOptions }) => {
              cookieStore.set({ name, value, ...options })
            })
          } catch {
            // Pode ser chamado de Server Components on render
          }
        },
      },
    }
  )
}