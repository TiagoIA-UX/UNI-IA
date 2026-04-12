import type { Metadata } from 'next'

export const metadata: Metadata = {
  title: 'Zairyx IA Blog - Sinais e Insights do Mercado Financeiro',
  description: 'Descubra análises profundas sobre Dólar, Euro e Cripto geradas pelos nossos 7 Agentes de Inteligência Artificial. Transforme ruído em lucro. Assine o Uni IA e lidere.',
  keywords: 'zairyx ia, uni ia, mercado financeiro, sinais premium telegram, robô de dólar, inteligência artificial forex',
}

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang='pt-BR' className='scroll-smooth antialiased'>
      <body style={{ margin: 0, fontFamily: 'system-ui, sans-serif', background: '#020617', color: '#f8fafc', display: 'flex', flexDirection: 'column', minHeight: '100vh' }}>
        <header style={{ borderBottom: '1px solid rgba(255,255,255,0.1)', background: 'rgba(2,6,23,0.9)', backdropFilter: 'blur(10px)', position: 'sticky', top: 0, zIndex: 50 }}>
          <div style={{ maxWidth: 1024, margin: '0 auto', padding: '1.5rem', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
              <span style={{ fontSize: '2rem', fontWeight: 900, background: 'linear-gradient(to right, #3b82f6, #34d399)', WebkitBackgroundClip: 'text', WebkitTextFillColor: 'transparent' }}>Z</span>
              <h1 style={{ fontSize: '1.25rem', fontWeight: 700, margin: 0 }}>Zairyx IA <span style={{ fontWeight: 400, color: '#94a3b8' }}>| Uni IA</span></h1>
            </div>
            <nav style={{ display: 'flex', gap: '1.5rem', fontSize: '0.875rem', fontWeight: 500, alignItems: 'center' }}>
              <a href='/planos' style={{ color: '#60a5fa', textDecoration: 'none' }}>Seja Premium / Assine</a>
              <a href='#telegram' style={{ background: '#2563eb', color: '#fff', padding: '0.5rem 1.25rem', borderRadius: '9999px', textDecoration: 'none', boxShadow: '0 4px 14px 0 rgba(37,99,235,0.39)' }}>Telegram (Grátis)</a>
            </nav>
          </div>
        </header>
        <main style={{ flex: 1, width: '100%', maxWidth: 1024, margin: '0 auto', padding: '3rem 1.5rem' }}>
          {children}
        </main>
        <footer style={{ padding: '2rem', textAlign: 'center', fontSize: '0.75rem', color: '#64748b', borderTop: '1px solid rgba(255,255,255,0.05)', background: 'rgba(2,6,23,0.5)' }}>
          <p>Zairyx IA © 2026. Liderança em Orquestração de Agentes IA para o Mercado. Este blog é uma interface de atração de negócios.</p>
        </footer>
      </body>
    </html>
  )
}
