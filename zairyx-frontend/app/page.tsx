import { createClient } from '@/lib/supabase/server'
import { isAllowedPlatformEmail } from '@/lib/auth'
import Image from 'next/image'

export const metadata = {
  title: 'Boitatá IA Finanças Brasil',
  description: 'Onde o capital se multiplica e protege a vida animal da Amazônia.',
}

export default async function HomePage() {
  const supabase = await createClient()
  const { data } = await supabase.auth.getUser()
  const user = data.user
  const temAcesso = isAllowedPlatformEmail(user?.email)

  return (
    <main style={{ background: '#0a0a0a', minHeight: '80vh', display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', padding: '2rem', textAlign: 'center' }}>
      <Image src="/logotipo.png" alt="Boitatá IA" width={120} height={120} priority style={{ marginBottom: '1.5rem' }} />
      <h1 style={{ fontFamily: 'var(--font-playfair)', fontSize: 'clamp(1.8rem,4vw,2.8rem)', color: '#f0ede6', margin: '0 0 1rem' }}>
        Boitatá IA <span style={{ color: '#c8860a' }}>Finanças Brasil</span>
      </h1>
      <p style={{ fontSize: '1.1rem', color: '#b8b0a0', maxWidth: '600px', lineHeight: 1.7, margin: '0 0 0.75rem' }}>
        Onde o capital se multiplica e protege a vida animal da Amazônia.
      </p>
      <p style={{ fontSize: '0.85rem', color: '#22c55e', marginBottom: '2rem' }}>
        🌿 10% do lucro líquido destinado à proteção animal na Amazônia
      </p>
      <div style={{ display: 'flex', gap: '1rem', flexWrap: 'wrap', justifyContent: 'center' }}>
        {temAcesso ? (
          <a href="/plataforma" style={{ background: 'linear-gradient(120deg,#c8860a,#ff6b00)', color: '#0a0a0a', padding: '0.75rem 2rem', borderRadius: '999px', fontWeight: 800, textDecoration: 'none', fontSize: '1rem' }}>
            Acessar Plataforma
          </a>
        ) : (
          <a href="/login" style={{ background: 'linear-gradient(120deg,#c8860a,#ff6b00)', color: '#0a0a0a', padding: '0.75rem 2rem', borderRadius: '999px', fontWeight: 800, textDecoration: 'none', fontSize: '1rem' }}>
            Entrar com Google
          </a>
        )}
        <a href="https://t.me/uni_ia_free_bot" target="_blank" rel="noopener noreferrer" style={{ background: 'transparent', color: '#c8860a', padding: '0.75rem 2rem', borderRadius: '999px', fontWeight: 700, textDecoration: 'none', fontSize: '1rem', border: '1px solid #c8860a' }}>
          Telegram Gratuito
        </a>
      </div>
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit,minmax(160px,1fr))', gap: '1rem', marginTop: '3rem', maxWidth: '700px', width: '100%' }}>
        {[
          { emoji: '🐆', nome: 'AEGIS', animal: 'Onça-Pintada', desc: 'Fusão e Risco' },
          { emoji: '🐬', nome: 'SENTINEL', animal: 'Boto-Cor-de-Rosa', desc: 'Governança' },
          { emoji: '🦜', nome: 'ATLAS', animal: 'Arara Azul', desc: 'Técnico' },
          { emoji: '🦅', nome: 'MacroAgent', animal: 'Harpia', desc: 'Macroeconomia' },
        ].map(a => (
          <div key={a.nome} style={{ background: 'rgba(26,58,26,.2)', border: '1px solid rgba(200,134,10,.2)', borderRadius: '10px', padding: '1rem', borderLeft: '3px solid #c8860a' }}>
            <div style={{ fontSize: '1.5rem', marginBottom: '6px' }}>{a.emoji}</div>
            <div style={{ fontSize: '0.7rem', fontWeight: 700, letterSpacing: '0.05em', color: '#c8860a', textTransform: 'uppercase' }}>{a.nome}</div>
            <div style={{ fontSize: '0.72rem', color: '#b8b0a0' }}>{a.animal}</div>
            <div style={{ fontSize: '0.68rem', color: '#7a7060', marginTop: '2px' }}>{a.desc}</div>
          </div>
        ))}
      </div>
    </main>
  )
}
