import { redirect } from 'next/navigation'
import GoogleLoginButton from '@/app/components/google-login-button'
import { isAllowedPlatformEmail } from '@/lib/auth'
import { createClient } from '@/lib/supabase/server'

type LoginPageProps = {
  searchParams?: Promise<{ error?: string; signed_out?: string; message?: string }>
}

const errorMessages: Record<string, string> = {
  missing_code: 'O Google nao retornou o codigo de autenticacao.',
  callback_failed: 'Falha ao concluir o login com Google.',
  provider_failed: 'O provedor Google retornou uma falha antes de concluir a autenticacao.',
  unauthorized: 'Este acesso esta liberado apenas para o e-mail autorizado da plataforma.',
  auth: 'Faca login para entrar na plataforma privada.',
}

export default async function LoginPage({ searchParams }: LoginPageProps) {
  const params = searchParams ? await searchParams : undefined
  const supabase = await createClient()
  const { data } = await supabase.auth.getUser()

  if (isAllowedPlatformEmail(data.user?.email)) {
    redirect('/plataforma')
  }

  const errorCode = params?.error || ''
  const errorMessage = errorCode
    ? params?.message
      ? `${errorMessages[errorCode] || 'Nao foi possivel autenticar seu acesso.'} Detalhe: ${params.message}`
      : errorMessages[errorCode] || 'Nao foi possivel autenticar seu acesso.'
    : ''
  const signedOut = params?.signed_out === '1'

  return (
    <div style={{ display: 'grid', gap: '1.5rem', maxWidth: 760, margin: '0 auto', padding: '2rem 0' }}>
      <section style={{ border: '1px solid rgba(34,211,238,0.22)', borderRadius: '1.5rem', overflow: 'hidden', background: 'linear-gradient(180deg, rgba(8,47,73,0.4), rgba(2,6,23,0.92))' }}>
        <div style={{ padding: '2rem' }}>
          <p style={{ margin: '0 0 0.75rem 0', color: '#67e8f9', fontWeight: 700, textTransform: 'uppercase', letterSpacing: '0.08em', fontSize: '0.8rem' }}>
            Plataforma privada
          </p>
          <h1 style={{ margin: '0 0 1rem 0', fontSize: 'clamp(2rem, 5vw, 3.4rem)', lineHeight: 1.05 }}>
            Login protegido por Google
          </h1>
          <p style={{ margin: '0 0 1.25rem 0', color: '#cbd5e1', fontSize: '1.05rem', lineHeight: 1.7 }}>
            O acesso da plataforma foi travado para um unico e-mail autorizado. Apenas a conta Google correta entra na area privada.
          </p>
          <div style={{ marginBottom: '1.5rem', border: '1px solid rgba(148,163,184,0.18)', borderRadius: '1rem', padding: '1rem 1.1rem', background: 'rgba(15,23,42,0.6)' }}>
            <p style={{ margin: '0 0 0.35rem 0', color: '#94a3b8', fontSize: '0.92rem' }}>Acesso liberado</p>
            <p style={{ margin: 0, color: '#f8fafc', fontWeight: 800 }}>Somente para a conta Google autorizada</p>
          </div>
          {errorMessage ? (
            <div style={{ marginBottom: '1rem', border: '1px solid rgba(248,113,113,0.45)', borderRadius: '1rem', padding: '0.9rem 1rem', background: 'rgba(69,10,10,0.3)', color: '#fecdd3' }}>
              {errorMessage}
            </div>
          ) : null}
          {signedOut ? (
            <div style={{ marginBottom: '1rem', border: '1px solid rgba(45,212,191,0.4)', borderRadius: '1rem', padding: '0.9rem 1rem', background: 'rgba(6,78,59,0.28)', color: '#ccfbf1' }}>
              Sessao encerrada com sucesso.
            </div>
          ) : null}
          <GoogleLoginButton />
        </div>
      </section>
    </div>
  )
}
