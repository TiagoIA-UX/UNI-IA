import Image from 'next/image';
import { homeCopy, resolveLocale, riskCopy } from '@/lib/i18n';

type HomeProps = {
  searchParams?: Promise<{ lang?: string }>;
};

export default async function Home({ searchParams }: HomeProps) {
  const params = searchParams ? await searchParams : undefined;
  const locale = resolveLocale(params?.lang);
  const t = homeCopy[locale];
  const risk = riskCopy[locale];

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '3rem' }}>
      <section style={{ padding: '3.2rem 0 2rem', position: 'relative' }}>
        <div style={{ position: 'absolute', inset: 0, background: 'radial-gradient(circle at 50% 20%, rgba(34,211,238,0.22), transparent 45%)', pointerEvents: 'none' }} />
        <div style={{ position: 'relative', display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(320px, 1fr))', gap: '1.5rem', alignItems: 'center' }}>
          <div style={{ textAlign: 'left' }}>
            <h2 style={{ fontSize: 'clamp(2rem, 6vw, 3.8rem)', fontWeight: 900, margin: '0 0 1rem 0', lineHeight: 1.05, letterSpacing: '-0.02em' }}>
              {t.heroTitle}
            </h2>
            <p style={{ fontSize: '1.1rem', color: '#cbd5e1', maxWidth: 760, margin: '0 0 2rem 0', lineHeight: 1.7 }}>
              {t.heroSubtitle}
            </p>
            <div style={{ display: 'flex', gap: '0.8rem', flexWrap: 'wrap' }}>
              <a href={`/acesso?lang=${locale}`} style={{ background: 'linear-gradient(120deg, #f59e0b, #22d3ee)', color: '#0f172a', padding: '0.95rem 1.5rem', borderRadius: '0.65rem', fontWeight: 800, textDecoration: 'none', transition: 'all 0.2s', boxShadow: '0 10px 30px rgba(245,158,11,0.25)' }}>{t.primaryCta}</a>
              <a href='https://t.me/uni_ia_free_bot' target='_blank' rel='noopener noreferrer' style={{ background: 'transparent', color: '#e2e8f0', padding: '0.95rem 1.5rem', borderRadius: '0.65rem', fontWeight: 700, textDecoration: 'none', border: '1px solid #475569' }}>{t.secondaryCta}</a>
            </div>
          </div>
          <div style={{ borderRadius: '1.4rem', overflow: 'hidden', border: '1px solid rgba(103,232,249,0.25)', background: 'linear-gradient(180deg, rgba(8,47,73,0.35), rgba(2,6,23,0.9))', boxShadow: '0 24px 80px rgba(8,145,178,0.22)' }}>
            <Image
              src='/trading-desk-hero.svg'
              alt='Painel visual da mesa de trading da UNI IA'
              width={1200}
              height={900}
              priority
              style={{ width: '100%', height: 'auto', display: 'block' }}
            />
          </div>
        </div>
      </section>

      <section style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(260px, 1fr))', gap: '1.2rem' }}>
        <div style={{ background: 'rgba(15,23,42,0.88)', padding: '1.7rem', borderRadius: '1rem', border: '1px solid rgba(148,163,184,0.2)' }}>
          <h3 style={{ margin: '0 0 0.8rem 0', color: '#e2e8f0', fontSize: '1.25rem' }}>01. {t.feature1Title}</h3>
          <p style={{ margin: 0, color: '#94a3b8', lineHeight: 1.65 }}>{t.feature1Body}</p>
        </div>
        <div style={{ background: 'rgba(15,23,42,0.88)', padding: '1.7rem', borderRadius: '1rem', border: '1px solid rgba(148,163,184,0.2)' }}>
          <h3 style={{ margin: '0 0 0.8rem 0', color: '#e2e8f0', fontSize: '1.25rem' }}>02. {t.feature2Title}</h3>
          <p style={{ margin: 0, color: '#94a3b8', lineHeight: 1.65 }}>{t.feature2Body}</p>
        </div>
        <div style={{ background: 'rgba(15,23,42,0.88)', padding: '1.7rem', borderRadius: '1rem', border: '1px solid rgba(148,163,184,0.2)' }}>
          <h3 style={{ margin: '0 0 0.8rem 0', color: '#e2e8f0', fontSize: '1.25rem' }}>03. {t.feature3Title}</h3>
          <p style={{ margin: 0, color: '#94a3b8', lineHeight: 1.65 }}>{t.feature3Body}</p>
        </div>
      </section>

      <section style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(320px, 1fr))', gap: '1.4rem', alignItems: 'center' }}>
        <div style={{ background: 'rgba(15,23,42,0.88)', padding: '1.8rem', borderRadius: '1rem', border: '1px solid rgba(148,163,184,0.2)' }}>
          <h3 style={{ margin: '0 0 0.8rem 0', color: '#67e8f9', fontSize: '1.25rem' }}>Operational signal flow</h3>
          <p style={{ margin: '0 0 1rem 0', color: '#cbd5e1', lineHeight: 1.7 }}>
            Market data, model orchestration, risk validation and controlled dispatch now have a visual layer on the platform.
          </p>
          <p style={{ margin: 0, color: '#94a3b8', lineHeight: 1.7 }}>
            This makes the commercial experience look closer to an actual institutional desk instead of a plain text-only landing page.
          </p>
        </div>
        <div style={{ borderRadius: '1.4rem', overflow: 'hidden', border: '1px solid rgba(148,163,184,0.2)', background: 'rgba(2,6,23,0.75)' }}>
          <Image
            src='/signal-flow.svg'
            alt='Fluxo operacional dos sinais da UNI IA'
            width={1200}
            height={700}
            style={{ width: '100%', height: 'auto', display: 'block' }}
          />
        </div>
      </section>

      <section style={{ padding: '1.2rem 1.4rem', border: '1px solid rgba(34,211,238,0.35)', borderRadius: '1rem', background: 'linear-gradient(120deg, rgba(8,47,73,0.45), rgba(15,23,42,0.8))' }}>
        <h3 style={{ margin: '0 0 0.7rem 0', color: '#67e8f9', fontSize: '1.15rem' }}>{t.edgeTitle}</h3>
        <p style={{ margin: 0, color: '#cbd5e1', lineHeight: 1.7 }}>{t.edgeBody}</p>
      </section>

      <section style={{ padding: '1rem 1.2rem', border: '1px solid rgba(248,113,113,0.45)', borderRadius: '0.9rem', background: 'rgba(69,10,10,0.3)' }}>
        <h3 style={{ margin: '0 0 0.4rem 0', color: '#fda4af', fontSize: '1rem' }}>{risk.title}</h3>
        <p style={{ margin: '0 0 0.4rem 0', color: '#fecdd3', lineHeight: 1.6, fontSize: '0.95rem' }}>{risk.body}</p>
        <p style={{ margin: 0, color: '#fbcfe8', lineHeight: 1.6, fontSize: '0.95rem', fontWeight: 700 }}>{risk.freeDelay}</p>
      </section>
    </div>
  )
}
