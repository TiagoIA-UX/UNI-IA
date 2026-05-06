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
      <section className={styles.heroSection}>
        <div className={styles.heroBg} />
        <div className={styles.heroGrid}>
          <div className={styles.heroText}>
            <h2 className={styles.heroTitle}>
              {t.heroTitle}
            </h2>
            <p className={styles.heroDesc}>
              {t.heroSubtitle}
            </p>
            <p className={styles.heroStatement}>{t.heroStatement}</p>
            <div className={styles.authorityPanel}>
              <p className={styles.authorityTitle}>{t.authorityTitle}</p>
              <ul className={styles.authorityList}>
                {t.authorityItems.map((item) => (
                  <li key={item} className={styles.authorityItem}>{item}</li>
                ))}
              </ul>
            </div>
            <div className={styles.heroCtas}>
              <a href={`/acesso?lang=${locale}`} className={styles.ctaPrimary}>{t.primaryCta}</a>
              <a href='https://t.me/uni_ia_free_bot' target='_blank' rel='noopener noreferrer' className={styles.ctaSecondary}>{t.secondaryCta}</a>
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

      <section className={styles.twoColSection}>
        <div className={styles.twoColCard}>
          <h3 className={styles.twoColTitle}>Operational governance flow</h3>
          <p className={styles.twoColBody}>
            Market data, signal generation, risk validation and controlled dispatch are structured as an operational chain instead of a loose collection of alerts.
          </p>
          <p className={styles.twoColBodyAlt}>
            The platform is presented as governed infrastructure: strategy, discipline and execution under explicit control.
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

      <section className={styles.edgeSection}>
        <h3 className={styles.edgeTitle}>{t.edgeTitle}</h3>
        <p className={styles.edgeBody}>{t.edgeBody}</p>
      </section>

      <section className={styles.riskSection}>
        <h3 className={styles.riskTitle}>{risk.title}</h3>
        <p className={styles.riskBody}>{risk.body}</p>
        <p className={styles.riskFreeDelay}>{risk.freeDelay}</p>
      </section>
    </div>
  )
}
