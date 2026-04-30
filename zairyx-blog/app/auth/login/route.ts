import { NextRequest, NextResponse } from 'next/server'
import { normalizeNextPath } from '@/lib/auth'
import { createClient } from '@/lib/supabase/server'

export async function GET(request: NextRequest) {
  const requestUrl = new URL(request.url)
  const next = normalizeNextPath(requestUrl.searchParams.get('next'))
  const redirectTo = new URL('/auth/callback', request.url)
  redirectTo.searchParams.set('next', next)

  const supabase = await createClient()
  const { data, error } = await supabase.auth.signInWithOAuth({
    provider: 'google',
    options: {
      redirectTo: redirectTo.toString(),
      queryParams: {
        access_type: 'offline',
        prompt: 'select_account',
      },
    },
  })

  if (error || !data.url) {
    const loginUrl = new URL('/login', request.url)
    loginUrl.searchParams.set('error', 'provider_failed')
    loginUrl.searchParams.set('message', error?.message || 'Nao foi possivel iniciar o login com Google.')
    return NextResponse.redirect(loginUrl)
  }

  return NextResponse.redirect(data.url)
}