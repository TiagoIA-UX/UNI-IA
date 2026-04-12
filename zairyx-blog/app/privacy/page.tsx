import { privacyCopy, resolveLocale } from '@/lib/i18n';

type PrivacyPageProps = {
  searchParams?: Promise<{ lang?: string }>;
};

export default async function PrivacyPage({ searchParams }: PrivacyPageProps) {
  const params = searchParams ? await searchParams : undefined;
  const locale = resolveLocale(params?.lang);
  const t = privacyCopy[locale];

  return (
    <div className="max-w-4xl mx-auto py-12 px-6 text-slate-300">
      <h1 className="text-4xl font-bold text-white mb-4">{t.title}</h1>
      <p className="text-slate-400 mb-8">{t.intro}</p>
      <div className="space-y-4 leading-relaxed text-lg">
        <p>{t.p1}</p>
        <p>{t.p2}</p>
        <p>{t.p3}</p>
        <p>{t.p4}</p>
      </div>
    </div>
  );
}
