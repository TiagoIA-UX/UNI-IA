import Image from 'next/image';
import { homeCopy, resolveLocale, riskCopy } from '@/lib/i18n';
import styles from './page.module.css';

type HomeProps = {
  searchParams?: Promise<{ lang?: string }>;
};

export default async function Home({ searchParams }: HomeProps) {
  const params = searchParams ? await searchParams : undefined;
  const locale = resolveLocale(params?.lang);
  const t = homeCopy[locale];
  const risk = riskCopy[locale];

  return (
    <div className={styles.root}>

      {/* ── HERO ──────────────────────────────────────────────────────────── */}
      <section className={styles.heroSection}>
        <div className={styles.heroBg} />
        <div className={styles.heroGrid}>
          <div className={styles.heroText}>
            <h2 className={styles.heroTitle}>
              🦄 {t.heroTitle}
            </h2>
            <p className={styles.heroDesc}>{t.heroSubtitle}</p>
            <p className={styles.heroStatement}>{t.heroStatement}</p>

            {/*
              NEUROCOMPORTAMENTAL — âncora cognitiva numérica (P0):
              Números concretos ativam o Sistema 2 (pensamento analítico) e
              aumentam credibilidade percebida antes da decisão de compra.
              Referência: Kahneman, 2011 — "Thinking, Fast and Slow"
            */}
            <div className={styles.anchorStrip}>
              {t.heroAnchor}
            </div>

            <div className={styles.authorityPanel}>
              <p className={styles.authorityTitle}>{t.authorityTitle}</p>
              <ul className={styles.authorityList}>
                {t.authorityItems.map((item) => (
                  <li key={item} className={styles.authorityItem}>{item}</li>
                ))}
              </ul>
            </div>

            {/*
              NEUROCOMPORTAMENTAL — prova social (P1):
              Validação social reduz incerteza e atua como atalho heurístico.
              Referência: Cialdini, 2001 — "Influence: The Psychology of Persuasion"
            */}
            <div className={styles.socialProofPanel}>
              <p className={styles.socialProofLabel}>{t.socialProofLabel}</p>
              <ul className={styles.socialProofList}>
                {t.socialProofItems.map((item) => (
                  <li key={item} className={styles.socialProofItem}>{item}</li>
                ))}
              </ul>
            </div>

            <div className={styles.heroCtas}>
              <a href={`/acesso?lang=${locale}`} className={styles.ctaPrimary}>{t.primaryCta}</a>
              <a
                href='https://t.me/uni_ia_free_bot'
                target='_blank'
                rel='noopener noreferrer'
                className={styles.ctaSecondary}
              >
                {t.secondaryCta}
              </a>
            </div>

            {/*
              JURÍDICO — P0 CRÍTICO:
              Disclaimer visível no hero é exigência implícita da CVM para
              plataformas que distribuem sinais analíticos sem credenciamento
              como assessora de investimentos (CVM IN 621/20, Art. 2º).
              O atraso de 15 min no plano gratuito deve ser destacado para
              evitar reclamações no PROCON (CDC Art. 6º, III — informação clara).
            */}
            <div className={styles.legalBadge}>
              {t.legalBadge}
            </div>
          </div>

          <div className={styles.heroImageContainer}>
            <Image
              src='/trading-desk-hero.svg'
              alt='Painel visual da mesa de trading da UNI IA'
              width={1200}
              height={900}
              priority
              className={styles.heroImg}
            />
          </div>
        </div>
      </section>

      {/* ── FEATURES ──────────────────────────────────────────────────────── */}
      {/*
        NEUROCOMPORTAMENTAL — benefício emocional explícito:
        O copy de cada feature foi atualizado no i18n para incluir a
        consequência emocional positiva ("disciplina aplicada por código,
        não por força de vontade"), ativando motivação intrínseca.
        Referência: Deci & Ryan, 2000 — Self-Determination Theory
      */}
      <section className={styles.featuresGrid}>
        <div className={styles.featureCard}>
          <h3 className={styles.featureTitle}>01. {t.feature1Title}</h3>
          <p className={styles.featureBody}>{t.feature1Body}</p>
        </div>
        <div className={styles.featureCard}>
          <h3 className={styles.featureTitle}>02. {t.feature2Title}</h3>
          <p className={styles.featureBody}>{t.feature2Body}</p>
        </div>
        <div className={styles.featureCard}>
          <h3 className={styles.featureTitle}>03. {t.feature3Title}</h3>
          <p className={styles.featureBody}>{t.feature3Body}</p>
        </div>
      </section>

      {/* ── REALTIME ──────────────────────────────────────────────────────── */}
      <section className={styles.realtimeSection}>
        <div className={styles.realtimeCard}>
          <h3 className={styles.realtimeTitle}>Bybit real-time signal alignment</h3>
          <p className={styles.realtimeBody}>
            The platform calibrates structural alerts against live Bybit market flow and applies a
            neurobehavioral discipline layer before execution.
          </p>
        </div>
      </section>

      {/* ── TWO-COL ───────────────────────────────────────────────────────── */}
      <section className={styles.twoColSection}>
        <div className={styles.twoColCard}>
          <h3 className={styles.twoColTitle}>Operational governance flow</h3>
          <p className={styles.twoColBody}>
            Market data, signal generation, risk validation and controlled dispatch are structured as
            an operational chain instead of a loose collection of alerts.
          </p>
          <p className={styles.twoColBodyAlt}>
            The platform is presented as governed infrastructure: strategy, discipline and execution
            under explicit control.
          </p>
        </div>
        <div className={styles.twoColImageBox}>
          <Image
            src='/signal-flow.svg'
            alt='Fluxo operacional dos sinais da UNI IA'
            width={1200}
            height={700}
            className={styles.twoColImg}
          />
        </div>
      </section>

      {/* ── EDGE ──────────────────────────────────────────────────────────── */}
      <section className={styles.edgeSection}>
        <h3 className={styles.edgeTitle}>{t.edgeTitle}</h3>
        <p className={styles.edgeBody}>{t.edgeBody}</p>
      </section>

      {/* ── RISK DISCLOSURE ───────────────────────────────────────────────── */}
      {/*
        JURÍDICO + NEUROCOMPORTAMENTAL:
        Risk disclosure redesenhada para gerar confiança (não apenas ansiedade).
        A cor foi mantida mas o texto agora é mais específico e inclui
        jurisdição — aumentando credibilidade institucional percebida.
        Referência comportamental: transparência radical aumenta confiança
        (Ariely, 2008 — "Predictably Irrational")
      */}
      <section id="risco" className={styles.riskSection}>
        <h3 className={styles.riskTitle}>{risk.title}</h3>
        <p className={styles.riskBody}>{risk.body}</p>
        <p className={styles.riskFreeDelay}>{risk.freeDelay}</p>
        <p className={styles.riskJurisdiction}>{risk.jurisdiction}</p>
      </section>

    </div>
  );
}
