import { resolveLocale, termsCopy } from '@/lib/i18n';

type TermsPageProps = {
  searchParams?: Promise<{ lang?: string }>;
};

export default async function TermosPage({ searchParams }: TermsPageProps) {
  const params = searchParams ? await searchParams : undefined;
  const locale = resolveLocale(params?.lang);
  const t = termsCopy[locale];

  return (
    <div className="max-w-4xl mx-auto py-12 px-6 animate-fade-in text-slate-300">
      <h1 className="text-4xl font-bold text-white mb-4">{t.title}</h1>
      <p className="text-slate-400 mb-8">{t.intro}</p>
      
      <div className="space-y-6 text-lg leading-relaxed">
        <section>
          <h2 className="text-2xl font-semibold text-white mb-3">{t.s1Title}</h2>
          <p>{t.s1Body}</p>
        </section>

        <section>
          <h2 className="text-2xl font-semibold text-white mb-3">{t.s2Title}</h2>
          <p>{t.s2Body}</p>
        </section>

        <section>
          <h2 className="text-2xl font-semibold text-white mb-3">{t.s3Title}</h2>
          <p>{t.s3Body}</p>
        </section>

        <section>
          <h2 className="text-2xl font-semibold text-white mb-3">{t.s4Title}</h2>
          <p>{t.s4Body}</p>
        </section>

        <section>
          <h2 className="text-2xl font-semibold text-white mb-3">{t.s5Title}</h2>
          <p>{t.s5Body}</p>
        </section>
      </div>
    </div>
  );
}
