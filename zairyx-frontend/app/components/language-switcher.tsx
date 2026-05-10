'use client';

import { useMemo } from 'react';
import { usePathname, useRouter, useSearchParams } from 'next/navigation';
import { localeLabels, resolveLocale, SUPPORTED_LOCALES } from '@/lib/i18n';

export default function LanguageSwitcher() {
  const pathname = usePathname();
  const router = useRouter();
  const searchParams = useSearchParams();

  const currentLang = useMemo(() => {
    return resolveLocale(searchParams.get('lang') || 'en');
  }, [searchParams]);

  function onChange(nextLang: string) {
    const params = new URLSearchParams(searchParams.toString());
    params.set('lang', nextLang);
    router.push(`${pathname}?${params.toString()}`);
  }

  return (
    <label style={{ display: 'inline-flex', alignItems: 'center', gap: '0.5rem', color: '#cbd5e1' }}>
      <span style={{ fontSize: '0.75rem', letterSpacing: '0.03em', textTransform: 'uppercase', opacity: 0.8 }}>Language</span>
      <select
        value={currentLang}
        onChange={(e) => onChange(e.target.value)}
        style={{
          borderRadius: '999px',
          background: 'rgba(15,23,42,0.9)',
          border: '1px solid rgba(148,163,184,0.4)',
          color: '#f8fafc',
          padding: '0.35rem 0.8rem',
          fontSize: '0.85rem',
          cursor: 'pointer',
        }}
      >
        {SUPPORTED_LOCALES.map((locale) => (
          <option key={locale} value={locale}>
            {localeLabels[locale]}
          </option>
        ))}
      </select>
    </label>
  );
}
