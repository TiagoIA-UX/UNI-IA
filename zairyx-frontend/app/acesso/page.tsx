import { resolveLocale } from '@/lib/i18n'

type AccessPageProps = {
  searchParams?: Promise<{ lang?: string }>
}

const copy = {
  pt: {
    kicker: 'Jornada de acesso',
    title: 'Como entrar no ecossistema UNI IA sem ruído nem etapa fake',
    subtitle:
      'O fluxo correto separa comunidade, autenticacao, plano e execucao. Sem barra de progresso artificial, sem “verificando informacoes” fake e sem depender de cadastro opaco em plataforma de terceiro para liberar o produto.',
    step1Title: '1. Entrar no canal Telegram',
    step1Body:
      'O canal free e a porta de entrada para acompanhar leituras gerais, contexto e atualizacoes operacionais. Serve para aquecimento e distribuicao inicial dos alertas.',
    step2Title: '2. Fazer login protegido',
    step2Body:
      'O acesso da plataforma privada acontece por Google login e whitelist de e-mail. Isso reduz fraude operacional e evita liberar area interna para trafego irrelevante.',
    step3Title: '3. Escolher o plano e o nivel de acesso',
    step3Body:
      'O plano define prioridade operacional, profundidade do contexto e se o usuario vai receber apenas sinais ou tambem recursos de execucao e mesa.',
    step4Title: '4. Integracao de execucao e opcional',
    step4Body:
      'Conexao com broker e copy trade devem acontecer depois da ativacao e da homologacao. Nao e uma exigencia para entrar no ecossistema e nao deve ser mascarada como “etapa obrigatoria” de cadastro.',
    flagsTitle: 'O que esse HTML que voce trouxe esta fazendo',
    flag1: 'Usa linguagem de “etapa concluida” para induzir continuidade sem validar nada de verdade.',
    flag2: 'Mistura comunidade, onboarding e corretora num mesmo funil para aumentar conversao.',
    flag3: 'Usa prova social e progresso visual para reduzir friccao e empurrar clique.',
    flag4: 'Cria dependencia de marca terceira no funil, o que aumenta risco juridico e de confianca.',
    rightTitle: 'Fluxo recomendado para o seu produto',
    right1: 'Comunidade Telegram: captacao e warming.',
    right2: 'Login Google: identidade e controle de acesso.',
    right3: 'Plano: monetizacao e segmentacao.',
    right4: 'Plataforma: painel, sinais e auditoria.',
    right5: 'Broker opcional: execucao controlada apos aceite.',
    ctaPrimary: 'Entrar no Telegram Free',
    ctaSecondary: 'Fazer login na plataforma',
    ctaTertiary: 'Ver planos',
    noteTitle: 'Nota operacional',
    noteBody:
      'Se voce quiser um onboarding premium de verdade, o certo e vender clareza: dizer o que e comunidade, o que e plataforma, o que e execucao e quando cada etapa vira obrigatoria.',
  },
  en: {
    kicker: 'Access journey',
    title: 'How to enter the UNI IA ecosystem without fake onboarding steps',
    subtitle:
      'The right flow separates community, authentication, plan and execution. No artificial progress bar, no fake “verifying information”, and no opaque third-party signup required to unlock the product.',
    step1Title: '1. Join the Telegram channel',
    step1Body:
      'The free channel is the entry point for broad market context, desk updates and initial signal distribution.',
    step2Title: '2. Complete protected login',
    step2Body:
      'Private platform access happens through Google login and e-mail whitelist. That reduces operational fraud and keeps irrelevant traffic out.',
    step3Title: '3. Choose the plan and access tier',
    step3Body:
      'The plan defines operational priority, depth of context and whether the user receives just signals or also desk and execution features.',
    step4Title: '4. Execution integration is optional',
    step4Body:
      'Broker connection and copy trade should happen after activation and validation. They are not mandatory to enter the ecosystem.',
    flagsTitle: 'What the HTML you sent is doing',
    flag1: 'Uses “step completed” language to induce continuity without real validation.',
    flag2: 'Blends community, onboarding and broker signup into one funnel to raise conversion.',
    flag3: 'Uses social proof and visual progress to reduce friction and push action.',
    flag4: 'Creates third-party brand dependency inside the funnel, increasing legal and trust risk.',
    rightTitle: 'Recommended product flow',
    right1: 'Telegram community: acquisition and warming.',
    right2: 'Google login: identity and access control.',
    right3: 'Plan: monetization and segmentation.',
    right4: 'Platform: dashboard, signals and audit trail.',
    right5: 'Optional broker: controlled execution after consent.',
    ctaPrimary: 'Join Free Telegram',
    ctaSecondary: 'Login to platform',
    ctaTertiary: 'View pricing',
    noteTitle: 'Operational note',
    noteBody:
      'If you want a premium onboarding, sell clarity: explain what is community, what is platform, what is execution, and when each step actually becomes mandatory.',
  },
} as const

export default async function AccessPage({ searchParams }: AccessPageProps) {
  const params = searchParams ? await searchParams : undefined
  const locale = resolveLocale(params?.lang)
  const t = copy[locale === 'pt' ? 'pt' : 'en']

  return (
    <div className='grid gap-6'>
      <section className='relative overflow-hidden rounded-[1.6rem] border border-cyan-400/25 bg-[linear-gradient(135deg,rgba(3,7,18,0.96),rgba(8,47,73,0.72))] p-8'>
        <div className='pointer-events-none absolute inset-0 bg-[radial-gradient(circle_at_80%_10%,rgba(34,211,238,0.18),transparent_28%)]' />
        <div className='relative grid gap-4'>
          <p className='m-0 text-[0.82rem] font-bold uppercase tracking-[0.08em] text-cyan-300'>{t.kicker}</p>
          <h1 className='m-0 text-[clamp(2.2rem,5vw,4rem)] leading-[1.03]'>{t.title}</h1>
          <p className='m-0 max-w-[900px] text-[1.04rem] leading-7 text-slate-300'>{t.subtitle}</p>
          <div className='mt-2 flex flex-wrap gap-3'>
            <a href='https://t.me/uni_ia_free_bot' target='_blank' rel='noopener noreferrer' className='rounded-full bg-[linear-gradient(120deg,#0ea5e9,#22d3ee)] px-5 py-3 font-extrabold text-cyan-950 no-underline'>{t.ctaPrimary}</a>
            <a href='/login' className='rounded-full bg-slate-50 px-5 py-3 font-extrabold text-slate-900 no-underline'>{t.ctaSecondary}</a>
            <a href='/planos' className='rounded-full border border-slate-400/40 px-5 py-3 font-bold text-slate-200 no-underline'>{t.ctaTertiary}</a>
          </div>
        </div>
      </section>

      <section className='grid gap-4 [grid-template-columns:repeat(auto-fit,minmax(230px,1fr))]'>
        {[
          [t.step1Title, t.step1Body],
          [t.step2Title, t.step2Body],
          [t.step3Title, t.step3Body],
          [t.step4Title, t.step4Body],
        ].map(([title, body]) => (
          <div key={title} className='rounded-[1.1rem] border border-slate-400/20 bg-slate-900/70 p-5'>
            <h2 className='mb-2 text-[1.04rem] text-slate-50'>{title}</h2>
            <p className='m-0 leading-7 text-slate-400'>{body}</p>
          </div>
        ))}
      </section>

      <section className='grid gap-5 [grid-template-columns:repeat(auto-fit,minmax(320px,1fr))]'>
        <div className='rounded-[1.2rem] border border-rose-400/30 bg-rose-950/30 p-6'>
          <h2 className='mb-3 text-[1.12rem] text-rose-300'>{t.flagsTitle}</h2>
          <ul className='m-0 list-disc pl-5 leading-7 text-rose-100'>
            <li>{t.flag1}</li>
            <li>{t.flag2}</li>
            <li>{t.flag3}</li>
            <li>{t.flag4}</li>
          </ul>
        </div>
        <div className='rounded-[1.2rem] border border-cyan-400/25 bg-cyan-950/20 p-6'>
          <h2 className='mb-3 text-[1.12rem] text-cyan-300'>{t.rightTitle}</h2>
          <ul className='m-0 list-disc pl-5 leading-7 text-slate-300'>
            <li>{t.right1}</li>
            <li>{t.right2}</li>
            <li>{t.right3}</li>
            <li>{t.right4}</li>
            <li>{t.right5}</li>
          </ul>
        </div>
      </section>

      <section className='rounded-2xl border border-amber-300/30 bg-amber-900/20 px-5 py-4'>
        <h2 className='mb-2 text-base text-amber-200'>{t.noteTitle}</h2>
        <p className='m-0 leading-7 text-amber-100'>{t.noteBody}</p>
      </section>
    </div>
  )
}