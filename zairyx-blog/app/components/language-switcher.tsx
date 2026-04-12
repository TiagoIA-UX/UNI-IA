'use client';

import { useEffect, useState } from 'react';
import { usePathname, useRouter } from 'next/navigation';
import { localeLabels, SUPPORTED_LOCALES } from '@/lib/i18n';

export default function LanguageSwitcher() {
  const pathname = usePathname();
  const router = useRouter();
  const [currentLang, setCurrentLang] = useState('en');

  useEffect(() => {
    const params = new URLSearchParams(window.location.search);
    setCurrentLang(params.get('lang') || 'en');
  }, []);

  function onChange(nextLang: string) {
    const params = new URLSearchParams(window.location.search);
    params.set('lang', nextLang);
    setCurrentLang(nextLang);
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
