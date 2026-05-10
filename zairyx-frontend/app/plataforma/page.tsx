// E:\UNI.IA\zairyx-frontend\app\plataforma\page.tsx
// Server Component puro — NÃO tem "use client"
// O dashboard interativo fica em PlataformaClient.tsx

import { redirect } from 'next/navigation'
import { createClient } from '@/lib/supabase/server'
import { isAllowedPlatformEmail } from '@/lib/auth'
import PlataformaClient from './PlataformaClient'

export const metadata = {
  title: 'Plataforma — Boitatá IA Finanças Brasil',
  description: 'Painel de operações com inteligência artificial multi-agente.',
}

export default async function PlataformaPage() {
  // Verificação de autenticação no servidor
  const supabase = await createClient()
  const { data } = await supabase.auth.getUser()
  const user = data.user

  if (!user || !isAllowedPlatformEmail(user.email)) {
    redirect('/login')
  }

  return <PlataformaClient userEmail={user.email ?? ''} />
}
