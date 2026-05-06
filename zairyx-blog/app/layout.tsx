import type { Metadata } from 'next'
import { Suspense } from 'react'
import Image from 'next/image'
import LanguageSwitcher from '@/app/components/language-switcher'
import NavLinks from '@/app/components/nav-links'
import { isAllowedPlatformEmail } from '@/lib/auth'
import { createClient } from '@/lib/supabase/server'
import styles from './layout.module.css'

export const metadata: Metadata = {
  title: 'UNI IA - Because uncontrolled risk is elimination',
  description: 'Institutional architecture for risk, discipline and execution. Strategy without governance is speculation.',
  keywords: 'uni ia, risk governance, institutional trading infrastructure, risk-controlled execution, deterministic backtest',
}

export default async function RootLayout({ children }: { children: React.ReactNode }) {
  const supabase = await createClient()
  const { data } = await supabase.auth.getUser()
  const user = data.user
  const hasPlatformAccess = isAllowedPlatformEmail(user?.email)

  return (
    <html lang='en' className='scroll-smooth antialiased'>
      <body className={styles.body}>
        <header className={styles.header}>
          <div className={styles.headerInner}>
            <div className={styles.brandRow}>
              <Image src='/uni-ia-logo.svg' alt='UNI IA Logo' width={42} height={42} priority />
              <div>
                <h1 className={styles.brandTitle}>UNI IA <span className={styles.brandTitleSub}>| Global Desk</span></h1>
                <p className={styles.brandTagline}>
                  Porque risco sem controle e eliminacao
                </p>
              </div>
            </div>
            <nav className={styles.nav}>
              <Suspense fallback={null}>
                <NavLinks variant='header' />
              </Suspense>
              {hasPlatformAccess ? (
                <a href='/plataforma' className={styles.navBtnPlatform}>
                  Plataforma
                </a>
              ) : (
                <a href='/login' className={styles.navBtnLogin}>
                  Login Google
                </a>
              )}
              {user?.email ? (
                <a href='/auth/signout' className={styles.navBtnSignout}>
                  Sair
                </a>
              ) : null}
              <a href='https://t.me/uni_ia_free_bot' target='_blank' rel='noopener noreferrer' className={styles.navBtnTelegram}>Free Telegram</a>
              <Suspense fallback={null}>
                <LanguageSwitcher />
              </Suspense>
            </nav>
          </div>
        </header>
        <main className={styles.main}>
          {children}
        </main>
        <footer className={styles.footer}>
          <p>UNI IA © 2026. Institutional AI Infrastructure for global paid subscribers.</p>
          <p className={styles.footerNav}>
            <Suspense fallback={null}>
              <NavLinks variant='footer' />
            </Suspense>
          </p>
          <p className={styles.footerDisclaimer}>
            No profit guarantee. This platform does not provide investment advice. All operations involve risk and may result in total capital loss.
          </p>
        </footer>
      </body>
    </html>
  )
}
