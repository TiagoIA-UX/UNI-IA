'use client';

import { usePathname } from 'next/navigation';
import styles from './nav-links.module.css';

type NavLinksProps = {
  variant: 'header' | 'footer';
};

export default function NavLinks({ variant }: NavLinksProps) {
  const pathname = usePathname();

  if (variant === 'footer') {
    return (
      <>
        <a href="/privacy" className={`${styles.link} ${styles.footerLink}`}>Privacidade</a>
        <a href="/risk-disclosure" className={`${styles.link} ${styles.footerLink}`}>Divulgação de Risco</a>
        <a href="/termos" className={`${styles.link} ${styles.footerLinkLast}`}>Termos de Uso</a>
      </>
    );
  }

  return (
    <>
      <a href="/" className={`${styles.link} ${pathname === '/' ? styles.navLinkActive : styles.navLink}`}>Início</a>
      <a href="/acesso" className={`${styles.link} ${pathname === '/acesso' ? styles.navLinkActive : styles.navLink}`}>Acesso</a>
      <a href="/plataforma" className={`${styles.link} ${pathname === '/plataforma' ? styles.navLinkActive : styles.navLink}`}>Plataforma</a>
      <a href="/planos" className={`${styles.link} ${pathname === '/planos' ? styles.navLinkActive : styles.navLink}`}>Planos</a>
      <a href="/termos" className={`${styles.link} ${pathname === '/termos' ? styles.navLinkActive : styles.navLink}`}>Termos</a>
    </>
  );
}
