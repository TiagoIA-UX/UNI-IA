import Image from 'next/image'
import { redirect } from 'next/navigation'
import { isAllowedPlatformEmail } from '@/lib/auth'
import { createClient } from '@/lib/supabase/server'

export default async function PlataformaPage() {
  const supabase = await createClient()
  const { data } = await supabase.auth.getUser()
  const user = data.user

  if (!user?.email) {
    redirect('/login?error=auth')
  }

  if (!isAllowedPlatformEmail(user.email)) {
    redirect('/login?error=unauthorized')
  }

  return (
    <div style={{ display: 'grid', gap: '1.5rem' }}>
      <section style={{ display: 'grid', gap: '1.2rem', gridTemplateColumns: 'repeat(auto-fit, minmax(320px, 1fr))', alignItems: 'center', border: '1px solid rgba(34,211,238,0.2)', borderRadius: '1.5rem', padding: '1.5rem', background: 'linear-gradient(180deg, rgba(8,47,73,0.38), rgba(2,6,23,0.92))' }}>
        <div>
          <p style={{ margin: '0 0 0.6rem 0', color: '#67e8f9', fontWeight: 700, textTransform: 'uppercase', letterSpacing: '0.08em', fontSize: '0.8rem' }}>
            Access granted
          </p>
          <h1 style={{ margin: '0 0 0.9rem 0', fontSize: 'clamp(2rem, 5vw, 3.3rem)', lineHeight: 1.05 }}>
            Plataforma liberada so para voce
          </h1>
          <p style={{ margin: '0 0 1rem 0', color: '#cbd5e1', lineHeight: 1.7 }}>
            O login foi travado no Google e a area privada aceita apenas o e-mail autorizado da conta principal.
          </p>
          <div style={{ display: 'grid', gap: '0.5rem' }}>
            <div style={{ border: '1px solid rgba(148,163,184,0.18)', borderRadius: '0.9rem', padding: '0.9rem 1rem', background: 'rgba(15,23,42,0.52)' }}>
              <p style={{ margin: '0 0 0.3rem 0', color: '#94a3b8', fontSize: '0.9rem' }}>Sessao autenticada</p>
              <p style={{ margin: 0, color: '#f8fafc', fontWeight: 800 }}>Conta autorizada conectada</p>
            </div>
            <div style={{ border: '1px solid rgba(148,163,184,0.18)', borderRadius: '0.9rem', padding: '0.9rem 1rem', background: 'rgba(15,23,42,0.52)' }}>
              <p style={{ margin: '0 0 0.3rem 0', color: '#94a3b8', fontSize: '0.9rem' }}>Regra ativa</p>
              <p style={{ margin: 0, color: '#f8fafc', fontWeight: 800 }}>Whitelist privada habilitada</p>
            </div>
          </div>
        </div>
        <div style={{ borderRadius: '1.25rem', overflow: 'hidden', border: '1px solid rgba(103,232,249,0.18)', background: 'rgba(2,6,23,0.8)' }}>
          <Image src='/trading-desk-hero.svg' alt='Painel privado da plataforma UNI IA' width={1200} height={900} priority style={{ width: '100%', height: 'auto', display: 'block' }} />
        </div>
      </section>

      <section style={{ display: 'grid', gap: '1rem', gridTemplateColumns: 'repeat(auto-fit, minmax(220px, 1fr))' }}>
        <div style={{ border: '1px solid rgba(148,163,184,0.18)', borderRadius: '1rem', padding: '1.2rem', background: 'rgba(15,23,42,0.7)' }}>
          <h2 style={{ margin: '0 0 0.6rem 0', color: '#e2e8f0', fontSize: '1.1rem' }}>Google login</h2>
          <p style={{ margin: 0, color: '#94a3b8', lineHeight: 1.6 }}>Autenticacao feita via Supabase OAuth com callback validado no servidor.</p>
        </div>
        <div style={{ border: '1px solid rgba(148,163,184,0.18)', borderRadius: '1rem', padding: '1.2rem', background: 'rgba(15,23,42,0.7)' }}>
          <h2 style={{ margin: '0 0 0.6rem 0', color: '#e2e8f0', fontSize: '1.1rem' }}>Whitelist privada</h2>
          <p style={{ margin: 0, color: '#94a3b8', lineHeight: 1.6 }}>Qualquer e-mail diferente do autorizado e barrado e removido da sessao.</p>
        </div>
        <div style={{ border: '1px solid rgba(148,163,184,0.18)', borderRadius: '1rem', padding: '1.2rem', background: 'rgba(15,23,42,0.7)' }}>
          <h2 style={{ margin: '0 0 0.6rem 0', color: '#e2e8f0', fontSize: '1.1rem' }}>Area privada</h2>
          <p style={{ margin: 0, color: '#94a3b8', lineHeight: 1.6 }}>A rota privada agora fica atras do login e pronta para receber o cockpit integrado depois.</p>
        </div>
      </section>
    </div>
  )
}
