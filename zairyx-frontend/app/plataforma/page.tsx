// E:\BOITATÁ_IA\zairyx-frontend\app\plataforma\page.tsx
import { redirect } from 'next/navigation'
import { isAllowedPlatformEmail } from '@/lib/auth'
import { createClient } from '@/lib/supabase/server'
import PlataformaClient from './PlataformaClient'

export const metadata = {
  title: 'Boitatá IA — Mesa Operacional',
  description: 'Dashboard institucional com agentes IA e gráfico em tempo real.',
  robots: { index: false, follow: false },
}

export default async function PlataformaPage() {
  const supabase = await createClient()
  const { data } = await supabase.auth.getUser()
  const user = data.user

  if (!user?.email) {
    redirect('/login?error=auth')
  }

  if (!isAllowedPlatformEmail(user.email)) {
    redirect('/login?error=unauthorized')
  }

  return <PlataformaClient />
}