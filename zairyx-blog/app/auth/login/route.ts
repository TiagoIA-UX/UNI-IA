import { NextRequest, NextResponse } from 'next/server'
import { normalizeNextPath } from '@/lib/auth'
import { createClient } from '@/lib/supabase/server'

async function getOAuthProviderError(authUrl: string) {
  try {
    const response = await fetch(authUrl, {
      method: 'GET',
      redirect: 'manual',
      headers: {
        accept: 'application/json',
      },
    })

    if (response.status >= 300 && response.status < 400) {
      return ''
    }

    if (!response.ok) {
      const contentType = response.headers.get('content-type') || ''
      if (contentType.includes('application/json')) {
        const payload = await response.json().catch(() => null)
        return payload?.msg || payload?.message || payload?.error_description || payload?.error || ''
      }

      return (await response.text()).slice(0, 200)
    }
  } catch {
    return ''
  }

  return ''
}

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

  const providerError = await getOAuthProviderError(data.url)
  if (providerError) {
    const loginUrl = new URL('/login', request.url)
    loginUrl.searchParams.set('error', 'provider_failed')
    loginUrl.searchParams.set('message', providerError)
    return NextResponse.redirect(loginUrl)
  }

  return NextResponse.redirect(data.url)
}