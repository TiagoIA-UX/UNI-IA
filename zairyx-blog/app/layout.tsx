import type { Metadata } from 'next'
import { Suspense } from 'react'
import Image from 'next/image'
import LanguageSwitcher from '@/app/components/language-switcher'
import NavLinks from '@/app/components/nav-links'
import { isAllowedPlatformEmail } from '@/lib/auth'
import { createClient } from '@/lib/supabase/server'

export const metadata: Metadata = {
  title: 'UNI IA - Institutional AI Signals',
  description: 'Institutional-grade AI orchestration for premium trading signals, macro intelligence and risk-controlled execution.',
  keywords: 'uni ia, ai trading signals, forex ai, premium telegram signals, market intelligence',
}

export default async function RootLayout({ children }: { children: React.ReactNode }) {
  const supabase = await createClient()
  const { data } = await supabase.auth.getUser()
  const user = data.user
  const hasPlatformAccess = isAllowedPlatformEmail(user?.email)

  return (
    <html lang='en' className='scroll-smooth antialiased'>
      <body style={{ margin: 0, fontFamily: 'ui-sans-serif, system-ui, -apple-system, Segoe UI, Helvetica Neue, sans-serif', background: 'radial-gradient(circle at 10% 10%, #1f2937 0%, #020617 35%, #030712 100%)', color: '#f8fafc', display: 'flex', flexDirection: 'column', minHeight: '100vh' }}>
        <header style={{ borderBottom: '1px solid rgba(255,255,255,0.12)', background: 'rgba(2,6,23,0.82)', backdropFilter: 'blur(14px)', position: 'sticky', top: 0, zIndex: 50 }}>
          <div style={{ maxWidth: 1120, margin: '0 auto', padding: '1rem 1.25rem', display: 'flex', justifyContent: 'space-between', alignItems: 'center', gap: '1rem', flexWrap: 'wrap' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
              <Image src='/uni-ia-logo.svg' alt='UNI IA Logo' width={42} height={42} priority />
              <div>
                <h1 style={{ fontSize: '1.1rem', fontWeight: 700, margin: 0 }}>UNI IA <span style={{ fontWeight: 400, color: '#94a3b8' }}>| Global Desk</span></h1>
                <p style={{ margin: '0.1rem 0 0 0', fontSize: '0.72rem', letterSpacing: '0.04em', textTransform: 'uppercase', color: '#67e8f9' }}>
                  Neuro Agressivo: leitura fria, execucao cirurgica
                </p>
              </div>
            </div>
            <nav style={{ display: 'flex', gap: '0.8rem', fontSize: '0.85rem', fontWeight: 600, alignItems: 'center', flexWrap: 'wrap' }}>
              <Suspense fallback={null}>
                <NavLinks variant='header' />
              </Suspense>
              {hasPlatformAccess ? (
                <a href='/plataforma' style={{ background: 'linear-gradient(120deg, #f59e0b, #22d3ee)', color: '#0f172a', padding: '0.45rem 1rem', borderRadius: '9999px', textDecoration: 'none', boxShadow: '0 6px 18px rgba(34,211,238,0.24)' }}>
                  Plataforma
                </a>
              ) : (
                <a href='/login' style={{ background: '#f8fafc', color: '#0f172a', padding: '0.45rem 1rem', borderRadius: '9999px', textDecoration: 'none', boxShadow: '0 6px 18px rgba(248,250,252,0.18)' }}>
                  Login Google
                </a>
              )}
              {user?.email ? (
                <a href='/auth/signout' style={{ border: '1px solid rgba(148,163,184,0.4)', color: '#e2e8f0', padding: '0.45rem 1rem', borderRadius: '9999px', textDecoration: 'none' }}>
                  Sair
                </a>
              ) : null}
              <a href='https://t.me/uni_ia_free_bot' target='_blank' rel='noreferrer' style={{ background: '#0ea5e9', color: '#fff', padding: '0.45rem 1rem', borderRadius: '9999px', textDecoration: 'none', boxShadow: '0 6px 18px rgba(14,165,233,0.35)' }}>Free Telegram</a>
              <Suspense fallback={null}>
                <LanguageSwitcher />
              </Suspense>
            </nav>
          </div>
        </header>
        <main style={{ flex: 1, width: '100%', maxWidth: 1120, margin: '0 auto', padding: '2.5rem 1.25rem' }}>
          {children}
        </main>
        <footer style={{ padding: '2rem', textAlign: 'center', fontSize: '0.78rem', color: '#94a3b8', borderTop: '1px solid rgba(255,255,255,0.08)', background: 'rgba(2,6,23,0.42)' }}>
          <p>UNI IA © 2026. Institutional AI Infrastructure for global paid subscribers.</p>
          <p style={{ marginTop: '0.5rem' }}>
            <Suspense fallback={null}>
              <NavLinks variant='footer' />
            </Suspense>
          </p>
          <p style={{ marginTop: '0.6rem', maxWidth: 820, marginLeft: 'auto', marginRight: 'auto', lineHeight: 1.6 }}>
            No profit guarantee. This platform does not provide investment advice. All operations involve risk and may result in total capital loss.
          </p>
        </footer>
      </body>
    </html>
  )
}
