'use client';

import { useMemo } from 'react';
import { usePathname, useSearchParams } from 'next/navigation';
import { resolveLocale } from '@/lib/i18n';

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
        <a href={linkFor('/privacy')} style={{ color: '#cbd5e1', textDecoration: 'none', marginRight: '0.7rem' }}>
          Privacy Policy
        </a>
        <a href={linkFor('/risk-disclosure')} style={{ color: '#cbd5e1', textDecoration: 'none', marginRight: '0.7rem' }}>
          Risk Disclosure
        </a>
        <a href={linkFor('/termos')} style={{ color: '#cbd5e1', textDecoration: 'none' }}>
          Terms
        </a>
      </>
    );
  }

  return (
    <>
      <a href={linkFor('/')} style={{ color: pathname === '/' ? '#22d3ee' : '#e2e8f0', textDecoration: 'none' }}>
        Home
      </a>
      <a href={linkFor('/acesso')} style={{ color: pathname === '/acesso' ? '#22d3ee' : '#e2e8f0', textDecoration: 'none' }}>
        Access
      </a>
      <a href={linkFor('/plataforma')} style={{ color: pathname === '/plataforma' ? '#22d3ee' : '#e2e8f0', textDecoration: 'none' }}>
        Platform
      </a>
      <a href={linkFor('/planos')} style={{ color: pathname === '/planos' ? '#22d3ee' : '#e2e8f0', textDecoration: 'none' }}>
        Pricing
      </a>
      <a href={linkFor('/termos')} style={{ color: pathname === '/termos' ? '#22d3ee' : '#e2e8f0', textDecoration: 'none' }}>
        Terms
      </a>
      <a href={linkFor('/privacy')} style={{ color: pathname === '/privacy' ? '#22d3ee' : '#e2e8f0', textDecoration: 'none' }}>
        Privacy
      </a>
      <a href={linkFor('/risk-disclosure')} style={{ color: pathname === '/risk-disclosure' ? '#22d3ee' : '#e2e8f0', textDecoration: 'none' }}>
        Risk
      </a>
    </>
  );
}
