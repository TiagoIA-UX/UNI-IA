import type { Metadata } from 'next'
import LanguageSwitcher from '@/app/components/language-switcher'

export const metadata: Metadata = {
  title: 'Zairyx Uni IA - Institutional AI Signals',
  description: 'Institutional-grade AI orchestration for premium trading signals, macro intelligence and risk-controlled execution.',
  keywords: 'zairyx, uni ia, ai trading signals, forex ai, premium telegram signals, market intelligence',
}

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang='en' className='scroll-smooth antialiased'>
      <body style={{ margin: 0, fontFamily: 'ui-sans-serif, system-ui, -apple-system, Segoe UI, Helvetica Neue, sans-serif', background: 'radial-gradient(circle at 10% 10%, #1f2937 0%, #020617 35%, #030712 100%)', color: '#f8fafc', display: 'flex', flexDirection: 'column', minHeight: '100vh' }}>
        <header style={{ borderBottom: '1px solid rgba(255,255,255,0.12)', background: 'rgba(2,6,23,0.82)', backdropFilter: 'blur(14px)', position: 'sticky', top: 0, zIndex: 50 }}>
          <div style={{ maxWidth: 1120, margin: '0 auto', padding: '1rem 1.25rem', display: 'flex', justifyContent: 'space-between', alignItems: 'center', gap: '1rem', flexWrap: 'wrap' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
              <span style={{ fontSize: '2rem', fontWeight: 900, background: 'linear-gradient(120deg, #f59e0b, #22d3ee)', WebkitBackgroundClip: 'text', WebkitTextFillColor: 'transparent' }}>Z</span>
              <h1 style={{ fontSize: '1.1rem', fontWeight: 700, margin: 0 }}>Zairyx Uni IA <span style={{ fontWeight: 400, color: '#94a3b8' }}>| Global Desk</span></h1>
            </div>
            <nav style={{ display: 'flex', gap: '0.8rem', fontSize: '0.85rem', fontWeight: 600, alignItems: 'center', flexWrap: 'wrap' }}>
              <a href='/?lang=en' style={{ color: '#e2e8f0', textDecoration: 'none' }}>Home</a>
              <a href='/planos?lang=en' style={{ color: '#22d3ee', textDecoration: 'none' }}>Pricing</a>
              <a href='/termos?lang=en' style={{ color: '#e2e8f0', textDecoration: 'none' }}>Terms</a>
              <a href='/privacy?lang=en' style={{ color: '#e2e8f0', textDecoration: 'none' }}>Privacy</a>
              <a href='/risk-disclosure?lang=en' style={{ color: '#e2e8f0', textDecoration: 'none' }}>Risk</a>
              <a href='https://t.me/zairyx_free' target='_blank' rel='noreferrer' style={{ background: '#0ea5e9', color: '#fff', padding: '0.45rem 1rem', borderRadius: '9999px', textDecoration: 'none', boxShadow: '0 6px 18px rgba(14,165,233,0.35)' }}>Free Telegram</a>
              <LanguageSwitcher />
            </nav>
          </div>
        </header>
        <main style={{ flex: 1, width: '100%', maxWidth: 1120, margin: '0 auto', padding: '2.5rem 1.25rem' }}>
          {children}
        </main>
        <footer style={{ padding: '2rem', textAlign: 'center', fontSize: '0.78rem', color: '#94a3b8', borderTop: '1px solid rgba(255,255,255,0.08)', background: 'rgba(2,6,23,0.42)' }}>
          <p>Zairyx Uni IA © 2026. Institutional AI Infrastructure for global paid subscribers.</p>
          <p style={{ marginTop: '0.5rem' }}>
            <a href='/privacy?lang=en' style={{ color: '#cbd5e1', textDecoration: 'none', marginRight: '0.7rem' }}>Privacy Policy</a>
            <a href='/risk-disclosure?lang=en' style={{ color: '#cbd5e1', textDecoration: 'none', marginRight: '0.7rem' }}>Risk Disclosure</a>
            <a href='/termos?lang=en' style={{ color: '#cbd5e1', textDecoration: 'none' }}>Terms</a>
          </p>
          <p style={{ marginTop: '0.6rem', maxWidth: 820, marginLeft: 'auto', marginRight: 'auto', lineHeight: 1.6 }}>
            No profit guarantee. This platform does not provide investment advice. All operations involve risk and may result in total capital loss.
          </p>
        </footer>
      </body>
    </html>
  )
}
