import { disclosureCopy, resolveLocale } from '@/lib/i18n';

type RiskDisclosurePageProps = {
  searchParams?: Promise<{ lang?: string }>;
};

export default async function RiskDisclosurePage({ searchParams }: RiskDisclosurePageProps) {
  const params = searchParams ? await searchParams : undefined;
  const locale = resolveLocale(params?.lang);
  const t = disclosureCopy[locale];

  return (
    <div className="max-w-4xl mx-auto py-12 px-6 text-slate-300">
      <h1 className="text-4xl font-bold text-white mb-4">{t.title}</h1>
      <p className="text-slate-400 mb-8">{t.intro}</p>
      <div className="space-y-4 leading-relaxed text-lg">
        <p>{t.d1}</p>
        <p>{t.d2}</p>
        <p>{t.d3}</p>
      </div>
    </div>
  );
}
