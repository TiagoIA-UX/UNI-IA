import { redirect } from 'next/navigation'
import GoogleLoginButton from '@/app/components/google-login-button'
import { isAllowedPlatformEmail } from '@/lib/auth'
import { createClient } from '@/lib/supabase/server'

type LoginPageProps = {
  searchParams?: Promise<{ error?: string; signed_out?: string; message?: string }>
}

const unauthorizedMessages: Record<string, { en: string; pt: string; es: string; ar: string; zh: string }> = {
  title: {
    en: 'Restricted Access',
    pt: 'Acesso Restrito',
    es: 'Acceso Restringido',
    ar: 'وصول مقيد',
    zh: '访问受限',
  },
  body: {
    en: 'This platform is currently in private development. Access is limited to authorized administrators only. If you believe you should have access, please contact the team.',
    pt: 'Esta plataforma está em fase de desenvolvimento privado. O acesso é restrito a administradores autorizados. Se acredita que deveria ter acesso, entre em contato com a equipe.',
    es: 'Esta plataforma se encuentra en fase de desarrollo privado. El acceso está restringido a administradores autorizados. Si cree que debería tener acceso, comuníquese con el equipo.',
    ar: 'هذه المنصة في مرحلة التطوير الخاص حاليًا. الوصول مقتصر على المسؤولين المعتمدين فقط. إذا كنت تعتقد أنه يجب أن يكون لديك وصول، يرجى التواصل مع الفريق.',
    zh: '该平台目前处于私有开发阶段，仅限授权管理员访问。如果您认为您应该拥有访问权限，请联系团队。',
  },
  contact: {
    en: 'Contact: zairyx.ai@gmail.com',
    pt: 'Contato: zairyx.ai@gmail.com',
    es: 'Contacto: zairyx.ai@gmail.com',
    ar: 'التواصل: zairyx.ai@gmail.com',
    zh: '联系方式：zairyx.ai@gmail.com',
  },
  back: {
    en: 'Try another account',
    pt: 'Tentar outra conta',
    es: 'Intentar con otra cuenta',
    ar: 'المحاولة بحساب آخر',
    zh: '尝试其他账户',
  },
}

const errorMessages: Record<string, string> = {
  missing_code: 'O Google não retornou o código de autenticação.',
  callback_failed: 'Falha ao concluir o login com Google.',
  provider_failed: 'O provedor Google retornou uma falha antes de concluir a autenticação.',
  auth: 'Faça login para entrar na plataforma privada.',
}

export default async function LoginPage({ searchParams }: LoginPageProps) {
  const params = searchParams ? await searchParams : undefined
  const supabase = await createClient()
  const { data } = await supabase.auth.getUser()

  if (isAllowedPlatformEmail(data.user?.email)) {
    redirect('/plataforma')
  }

  const errorCode = params?.error || ''
  const isUnauthorized = errorCode === 'unauthorized'

  // Página de acesso restrito — exibida quando o email não é autorizado
  if (isUnauthorized) {
    return (
      <div style={{ display: 'grid', placeItems: 'center', minHeight: '60vh', padding: '2rem' }}>
        <div style={{
          maxWidth: 560,
          width: '100%',
          border: '1px solid rgba(251,191,36,0.3)',
          borderRadius: '1.5rem',
          background: 'linear-gradient(180deg, rgba(120,53,15,0.25), rgba(2,6,23,0.92))',
          padding: '2.5rem 2rem',
          textAlign: 'center',
        }}>
          <div style={{ fontSize: '3rem', marginBottom: '1rem' }}>🔒</div>
          <p style={{ color: '#fbbf24', fontWeight: 700, textTransform: 'uppercase', letterSpacing: '0.1em', fontSize: '0.78rem', margin: '0 0 0.5rem' }}>
            UNI IA — Private Beta
          </p>

          {/* Mensagens em todos os idiomas */}
          {(['pt', 'en', 'es', 'ar', 'zh'] as const).map((lang) => (
            <div key={lang} style={{ marginBottom: '1.25rem', borderBottom: '1px solid rgba(255,255,255,0.07)', paddingBottom: '1.25rem' }}>
              <h2 style={{ margin: '0 0 0.5rem', fontSize: '1.1rem', color: '#f8fafc' }}>
                {unauthorizedMessages.title[lang]}
              </h2>
              <p style={{ margin: '0 0 0.35rem', color: '#cbd5e1', fontSize: '0.92rem', lineHeight: 1.65 }}>
                {unauthorizedMessages.body[lang]}
              </p>
              <p style={{ margin: 0, color: '#94a3b8', fontSize: '0.82rem' }}>
                {unauthorizedMessages.contact[lang]}
              </p>
            </div>
          ))}

          <a
            href='/login'
            style={{
              display: 'inline-block',
              marginTop: '0.5rem',
              padding: '0.65rem 1.5rem',
              borderRadius: '0.75rem',
              border: '1px solid rgba(148,163,184,0.3)',
              color: '#94a3b8',
              fontSize: '0.9rem',
              textDecoration: 'none',
              background: 'rgba(15,23,42,0.5)',
            }}
          >
            ← {unauthorizedMessages.back.pt} / {unauthorizedMessages.back.en}
          </a>
        </div>
      </div>
    )
  }

  // Página de login normal
  const errorMessage = errorCode
    ? params?.message
      ? `${errorMessages[errorCode] || 'Não foi possível autenticar seu acesso.'} Detalhe: ${params.message}`
      : errorMessages[errorCode] || 'Não foi possível autenticar seu acesso.'
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
            O acesso da plataforma está restrito a contas Google autorizadas.
          </p>
          {errorMessage ? (
            <div style={{ marginBottom: '1rem', border: '1px solid rgba(248,113,113,0.45)', borderRadius: '1rem', padding: '0.9rem 1rem', background: 'rgba(69,10,10,0.3)', color: '#fecdd3' }}>
              {errorMessage}
            </div>
          ) : null}
          {signedOut ? (
            <div style={{ marginBottom: '1rem', border: '1px solid rgba(45,212,191,0.4)', borderRadius: '1rem', padding: '0.9rem 1rem', background: 'rgba(6,78,59,0.28)', color: '#ccfbf1' }}>
              Sessão encerrada com sucesso.
            </div>
          ) : null}
          <GoogleLoginButton />
        </div>
      </section>
    </div>
  )
}