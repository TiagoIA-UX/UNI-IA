export const metadata = {
  title: 'Boitatá IA',
  description: 'Acesso restrito.',
  robots: { index: false, follow: false },
}

export default function HomePage() {
  return (
    <main style={{
      background: '#0a0a0a',
      minHeight: '100vh',
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'center',
    }}>
      <a href="/login" style={{
        fontSize: '0.78rem',
        color: '#5c4a2a',
        textDecoration: 'none',
        letterSpacing: '0.12em',
        textTransform: 'uppercase',
        padding: '0.75rem 1.5rem',
        border: '1px solid #1a1408',
        borderRadius: '4px',
      }}>
        🔥 Acessar
      </a>
    </main>
  )
}
