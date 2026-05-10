import type { Metadata } from 'next'
import { Suspense } from 'react'
import Image from 'next/image'
import { Playfair_Display, Inter } from 'next/font/google'
import NavLinks from '@/app/components/nav-links'
import { isAllowedPlatformEmail } from '@/lib/auth'
import { createClient } from '@/lib/supabase/server'
import styles from './layout.module.css'
import './globals.css'

const playfair = Playfair_Display({
  subsets: ['latin'],
  variable: '--font-playfair',
  display: 'swap',
})

const inter = Inter({
  subsets: ['latin'],
  variable: '--font-inter',
  display: 'swap',
})

export const metadata: Metadata = {
  title: 'Boitatá IA Finanças Brasil',
  description:
    'Onde o capital se multiplica e protege a vida animal da Amazônia. Inteligência artificial financeira com propósito ambiental.',
  keywords:
    'boitatá ia, finanças brasil, inteligência artificial, mercado bitcoin, proteção amazônia, fintech sustentável',
  openGraph: {
    title: 'Boitatá IA Finanças Brasil',
    description: 'Onde o capital se multiplica e protege a vida animal da Amazônia.',
    type: 'website',
    locale: 'pt_BR',
    siteName: 'Boitatá IA',
  },
  icons: {
    icon: '/fivicon.png',
    shortcut: '/fivicon.png',
    apple: '/fivicon.png',
  },
}

export default async function RootLayout({ children }: { children: React.ReactNode }) {
  const supabase = await createClient()
  const { data } = await supabase.auth.getUser()
  const user = data.user
  const hasPlatformAccess = isAllowedPlatformEmail(user?.email)

  return (
    <html
      lang="pt-BR"
      className={`${playfair.variable} ${inter.variable} scroll-smooth antialiased`}
    >
      <body className={styles.body}>
        <header className={styles.header}>
          <div className={styles.headerInner}>
            <a href="/" className={styles.brandRow}>
              <Image
                src="/logotipo.png"
                alt="Boitatá IA Finanças Brasil"
                width={44}
                height={44}
                priority
              />
              <div>
                <h1 className={styles.brandTitle}>
                  Boitatá IA{' '}
                  <span className={styles.brandTitleSub}>Finanças Brasil</span>
                </h1>
                <p className={styles.brandTagline}>
                  Onde o capital multiplica e protege a Amazônia
                </p>
              </div>
            </a>
            <nav className={styles.nav}>
              <Suspense fallback={null}>
                <NavLinks variant="header" />
              </Suspense>
              {hasPlatformAccess ? (
                <a href="/plataforma" className={styles.navBtnPlatform}>
                  Plataforma
                </a>
              ) : (
                <a href="/login" className={styles.navBtnLogin}>
                  Entrar com Google
                </a>
              )}
              {user?.email ? (
                <a href="/auth/signout" className={styles.navBtnSignout}>
                  Sair
                </a>
              ) : null}
              <a
                href="https://t.me/uni_ia_free_bot"
                target="_blank"
                rel="noopener noreferrer"
                className={styles.navBtnTelegram}
              >
                Telegram Gratuito
              </a>
            </nav>
          </div>
        </header>
        <main className={styles.main}>{children}</main>
        <footer className={styles.footer}>
          <p className={styles.footerBrand}>
            Boitatá IA Finanças Brasil © 2026 — Fintech com propósito
          </p>
          <p className={styles.footerMission}>
            🌿 10% do lucro líquido protege a vida animal da Amazônia
          </p>
          <p className={styles.footerNav}>
            <Suspense fallback={null}>
              <NavLinks variant="footer" />
            </Suspense>
          </p>
          <p className={styles.footerDisclaimer}>
            Sem garantia de lucro. Esta plataforma não fornece recomendação de
            investimento. Toda operação envolve risco e pode resultar em perda
            total do capital. Criptoativos regulados pelo BACEN (Res.
            519/520/521) e CVM Res. 30.
          </p>
        </footer>
      </body>
    </html>
  )
}

