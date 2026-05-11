export const metadata = {
  title: 'Boitatá IA — Em breve',
  description: 'Plataforma em desenvolvimento. Em breve disponível.',
  robots: { index: false, follow: false },
}

export default function HomePage() {
  return (
    <main style={{
      background: '#0a0a0a',
      minHeight: '80vh',
      display: 'flex',
      flexDirection: 'column',
      alignItems: 'center',
      justifyContent: 'center',
      padding: '2rem',
      textAlign: 'center',
    }}>
      <div style={{ fontSize: '2.8rem', marginBottom: '1.25rem' }}>
        🔥
      </div>
      <h1 style={{ fontSize: 'clamp(1.6rem,4vw,2.2rem)', color: '#f0ede6', margin: '0 0 0.6rem', fontWeight: 800 }}>
        Boitatá IA
      </h1>
      <p style={{ fontSize: '0.95rem', color: '#5c4a2a', maxWidth: '380px', lineHeight: 1.7, margin: '0 0 2.5rem' }}>
        Plataforma em desenvolvimento.<br />Em breve.
      </p>
      <div style={{ width: '36px', height: '1px', background: 'rgba(200,134,10,0.3)', marginBottom: '2.5rem' }} />
      <a href="/login" style={{ fontSize: '0.72rem', color: '#3a2e1a', textDecoration: 'none', letterSpacing: '0.1em', textTransform: 'uppercase' }}>
        acesso restrito
      </a>
    </main>
  )
}