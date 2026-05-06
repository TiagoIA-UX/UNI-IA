'use client';

import { useMemo } from 'react';
import { usePathname, useSearchParams } from 'next/navigation';
import { resolveLocale } from '@/lib/i18n';
import styles from './nav-links.module.css';

type NavLinksProps = {
  variant: 'header' | 'footer';
};

export default function NavLinks({ variant }: NavLinksProps) {
  const pathname = usePathname();
  const searchParams = useSearchParams();

  const lang = resolveLocale(searchParams.get('lang') || 'en');

  const linkFor = useMemo(() => {
    return (targetPath: string) => {
      const params = new URLSearchParams(searchParams.toString());
      params.set('lang', lang);
      const qs = params.toString();
      return qs ? `${targetPath}?${qs}` : targetPath;
    };
  }, [searchParams, lang]);

  if (variant === 'footer') {
    return (
      <>
        <a href={linkFor('/privacy')} className={`${styles.link} ${styles.footerLink}`}>
          Privacy Policy
        </a>
        <a href={linkFor('/risk-disclosure')} className={`${styles.link} ${styles.footerLink}`}>
          Risk Disclosure
        </a>
        <a href={linkFor('/termos')} className={`${styles.link} ${styles.footerLinkLast}`}>
          Terms
        </a>
      </>
    );
  }

  return (
    <>
      <a href={linkFor('/')} className={`${styles.link} ${pathname === '/' ? styles.navLinkActive : styles.navLink}`}>
        Home
      </a>
      <a href={linkFor('/acesso')} className={`${styles.link} ${pathname === '/acesso' ? styles.navLinkActive : styles.navLink}`}>
        Access
      </a>
      <a href={linkFor('/plataforma')} className={`${styles.link} ${pathname === '/plataforma' ? styles.navLinkActive : styles.navLink}`}>
        Platform
      </a>
      <a href={linkFor('/planos')} className={`${styles.link} ${pathname === '/planos' ? styles.navLinkActive : styles.navLink}`}>
        Pricing
      </a>
      <a href={linkFor('/termos')} className={`${styles.link} ${pathname === '/termos' ? styles.navLinkActive : styles.navLink}`}>
        Terms
      </a>
      <a href={linkFor('/privacy')} className={`${styles.link} ${pathname === '/privacy' ? styles.navLinkActive : styles.navLink}`}>
        Privacy
      </a>
      <a href={linkFor('/risk-disclosure')} className={`${styles.link} ${pathname === '/risk-disclosure' ? styles.navLinkActive : styles.navLink}`}>
        Risk
      </a>
    </>
  );
}
