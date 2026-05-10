import { NextRequest, NextResponse } from 'next/server'
import { createClient } from '@/lib/supabase/server'
import { isAllowedPlatformEmail, normalizeNextPath } from '@/lib/auth'

export async function GET(request: NextRequest) {
  const requestUrl = new URL(request.url)
  const code = requestUrl.searchParams.get('code')
  const next = normalizeNextPath(requestUrl.searchParams.get('next'))
  const providerError = requestUrl.searchParams.get('error')
  const providerErrorDescription = requestUrl.searchParams.get('error_description')

  if (providerError) {
    const loginUrl = new URL('/login', request.url)
    loginUrl.searchParams.set('error', 'provider_failed')
    loginUrl.searchParams.set('message', providerErrorDescription || providerError)
    return NextResponse.redirect(loginUrl)
  }

  if (!code) {
    return NextResponse.redirect(new URL('/login?error=missing_code', request.url))
  }

  const supabase = await createClient()
  const { data, error } = await supabase.auth.exchangeCodeForSession(code)

  if (error) {
    const loginUrl = new URL('/login', request.url)
    loginUrl.searchParams.set('error', 'callback_failed')
    loginUrl.searchParams.set('message', error.message)
    return NextResponse.redirect(loginUrl)
  }

  if (!isAllowedPlatformEmail(data.user?.email)) {
    await supabase.auth.signOut()
    return NextResponse.redirect(new URL('/login?error=unauthorized', request.url))
  }

  return NextResponse.redirect(new URL(next, request.url))
}