// E:\BOITATÁ_IA\zairyx-frontend\app\page.tsx
// Página pública — "Em breve"
// Sem funcionalidade comercial — compatível com Vercel Hobby

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

      <div style={{
        fontSize: '2.8rem',
        marginBottom: '1.25rem',
        filter: 'drop-shadow(0 0 24px rgba(200,134,10,0.35))',
      }}>
        🔥
      </div>

      <h1 style={{
        fontSize: 'clamp(1.6rem, 4vw, 2.2rem)',
        color: '#f0ede6',
        margin: '0 0 0.6rem',
        fontWeight: 800,
        letterSpacing: '-0.02em',
      }}>
        Boitatá IA
      </h1>

      <p style={{
        fontSize: '0.95rem',
        color: '#5c4a2a',
        maxWidth: '380px',
        lineHeight: 1.7,
        margin: '0 0 2.5rem',
        letterSpacing: '0.01em',
      }}>
        Plataforma em desenvolvimento.
        <br />
        Em breve.
      </p>

      <div style={{
        width: '36px',
        height: '1px',
        background: 'rgba(200,134,10,0.3)',
        marginBottom: '2.5rem',
      }} />

      {/* Link de acesso interno — discreto, sem destaque visual */}
      <a
        href="/login"
        style={{
          fontSize: '0.72rem',
          color: '#3a2e1a',
          textDecoration: 'none',
          letterSpacing: '0.1em',
          textTransform: 'uppercase',
        }}
      >
        acesso restrito
      </a>

    </main>
  )
}
