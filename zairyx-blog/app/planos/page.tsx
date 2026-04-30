'use client';

import Image from 'next/image';
import { useEffect, useState } from 'react';
import { homeCopy, resolveLocale, riskCopy } from '@/lib/i18n';

type Variant = 'A' | 'B';

export default function PlanosPage() {
  const [locale, setLocale] = useState<'en' | 'es' | 'pt' | 'ar' | 'zh'>('en');
  const [variant, setVariant] = useState<Variant | null>(null);
  const [variantSource, setVariantSource] = useState<'query' | 'winner' | 'storage' | 'random'>('random');
  const [sessionId, setSessionId] = useState('');

  useEffect(() => {
    const params = new URLSearchParams(window.location.search);
    setLocale(resolveLocale(params.get('lang') || 'en'));

    const savedSession = localStorage.getItem('uniia-sales-session-id');
    if (savedSession) {
      setSessionId(savedSession);
    } else {
      const generated = typeof crypto !== 'undefined' && 'randomUUID' in crypto
        ? crypto.randomUUID()
        : `sess_${Date.now()}_${Math.random().toString(16).slice(2)}`;
      localStorage.setItem('uniia-sales-session-id', generated);
      setSessionId(generated);
    }

    const resolveVariant = async () => {
      const queryVariant = (params.get('v') || '').toUpperCase();
      if (queryVariant === 'A' || queryVariant === 'B') {
        localStorage.setItem('uniia-sales-variant', queryVariant);
        setVariant(queryVariant as Variant);
        setVariantSource('query');
        return;
      }

      try {
        const res = await fetch('/api/events/decision?page=planos&days=30&minViews=100&metric=redirect', {
          method: 'GET',
          cache: 'no-store',
        });
        const result = await res.json();
        const winner = result?.data?.winner;

        if (res.ok && (winner === 'A' || winner === 'B')) {
          localStorage.setItem('uniia-sales-variant', winner);
          setVariant(winner);
          setVariantSource('winner');
          return;
        }
      } catch {
        // Se a decisao automatica falhar, segue fallback local sem quebrar UX.
      }

      const saved = localStorage.getItem('uniia-sales-variant');
      if (saved === 'A' || saved === 'B') {
        setVariant(saved);
        setVariantSource('storage');
        return;
      }

      const chosen: Variant = Math.random() < 0.5 ? 'A' : 'B';
      localStorage.setItem('uniia-sales-variant', chosen);
      setVariant(chosen);
      setVariantSource('random');
    };

    void resolveVariant();
  }, []);

  const t = homeCopy[locale];
  const risk = riskCopy[locale];
  const [loading, setLoading] = useState(false);
  const [errorMsg, setErrorMsg] = useState('');
  const isPt = locale === 'pt';

  async function trackEvent(eventName: string, details?: Record<string, unknown>) {
    try {
      await fetch('/api/events', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          event: eventName,
          page: 'planos',
          variant: variant || 'A',
          locale,
          sessionId,
          ts: new Date().toISOString(),
          details: {
            ...(details || {}),
            variantSource,
          },
        }),
      });
    } catch {
      // Tracking nunca deve quebrar fluxo de venda.
    }
  }

  useEffect(() => {
    if (!sessionId || !variant) return;
    trackEvent('sales_page_view');
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [variant, sessionId, variantSource]);

  const salesCopy = isPt
    ? {
        heroKicker: 'Mesa privada para execucao disciplinada',
        heroTitleA: 'Pare de operar no escuro. Entre com contexto, risco e timing.',
        heroTitleB: 'Sem metodo, voce paga caro. Com mesa privada, voce executa com disciplina.',
        heroSub: 'A pagina de vendas foi desenhada para quem quer operar com processo: dados reais, governanca de risco e envio operacional em tempo quase real.',
        trust1: 'Dados reais e auditaveis',
        trust2: 'Sem fallback operacional',
        trust3: 'Gate de risco por camadas',
        forWhoTitle: 'Para quem e o UNI IA Premium',
        forWho1: 'Traders que precisam de contexto antes de clicar em comprar/vender.',
        forWho2: 'Operadores que querem regra de risco e aprovacao manual da mesa.',
        forWho3: 'Times pequenos que buscam operacao profissional sem ruído.',
        stepTitle: 'Como funciona na pratica',
        step1: 'Leitura do mercado com dados reais',
        step2: 'Sinal validado por estrategia + risco + compliance',
        step3: 'Despacho para canal e execucao controlada na mesa',
        faqTitle: 'Perguntas diretas',
        faq1Q: 'Tem garantia de lucro?',
        faq1A: 'Nao. A plataforma nao promete retorno e toda operacao envolve risco.',
        faq2Q: 'Os sinais free e premium sao iguais?',
        faq2A: 'Nao. O premium recebe prioridade operacional e contexto mais profundo.',
        faq3Q: 'Posso ativar copy trade direto?',
        faq3A: 'Sim, mas o recomendado e iniciar em paper mode e liberar gradualmente.',
        freeTitle: 'Canal Free',
        freeSub: 'Entrada para acompanhar a leitura de mercado sem custo.',
        premiumSub: 'Execucao com foco em risco, contexto e disciplina operacional.',
        freeBtn: 'Entrar no canal free',
        ctaFinalA: 'Destravar mesa premium',
        ctaFinalB: 'Assumir controle da execucao',
      }
    : {
        heroKicker: 'Private desk for disciplined execution',
        heroTitleA: 'Stop trading blind. Enter with context, risk and timing.',
        heroTitleB: 'Without process you bleed. With a private desk you execute with control.',
        heroSub: 'This sales page is built for operators who need process: real data, risk governance and near-real-time execution flow.',
        trust1: 'Auditable real data',
        trust2: 'No operational fallback',
        trust3: 'Layered risk gate',
        forWhoTitle: 'Who UNI IA Premium is for',
        forWho1: 'Traders who need context before pressing buy/sell.',
        forWho2: 'Operators who require risk rules and manual desk approval.',
        forWho3: 'Small teams that want institutional discipline without noise.',
        stepTitle: 'How it works in practice',
        step1: 'Real-market data ingestion',
        step2: 'Signal validated by strategy + risk + compliance',
        step3: 'Dispatch and controlled desk execution',
        faqTitle: 'Straight answers',
        faq1Q: 'Is profit guaranteed?',
        faq1A: 'No. This platform does not guarantee returns and every operation has risk.',
        faq2Q: 'Are free and premium signals the same?',
        faq2A: 'No. Premium gets operational priority and deeper context.',
        faq3Q: 'Can I enable copy trade right away?',
        faq3A: 'Yes, but the professional path is paper mode first, then gradual release.',
        freeTitle: 'Free Channel',
        freeSub: 'Entry point to follow market intelligence at no cost.',
        premiumSub: 'Execution driven by risk, context and operational discipline.',
        freeBtn: 'Join free channel',
          ctaFinalA: 'Unlock premium desk',
          ctaFinalB: 'Take control of execution',
      };

        const activeVariant: Variant = variant || 'A';
        const heroTitle = activeVariant === 'A' ? salesCopy.heroTitleA : salesCopy.heroTitleB;
        const ctaFinal = activeVariant === 'A' ? salesCopy.ctaFinalA : salesCopy.ctaFinalB;
  
  const handleCheckout = async (e: React.FormEvent<HTMLFormElement>) => {
    e.preventDefault();
    await trackEvent('premium_checkout_submit', { funnel: 'premium' });
    setLoading(true);
    setErrorMsg('');

    const formData = new FormData(e.currentTarget);
    const email = formData.get('email');
    const fullName = formData.get('fullName');
    const planType = 'PREMIUM'; // Hardcoded para o form atual

    try {
      const res = await fetch('/api/checkout', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email, fullName, planType }),
      });

      const result = await res.json();

      if (!res.ok) {
        throw new Error(result.error || 'Unable to process subscription');
      }

      if (result.success && result.data.checkoutUrl) {
        await trackEvent('premium_checkout_redirect', { funnel: 'premium' });
        // Redirecionamento blindado para o gateway financeiro
        window.location.href = result.data.checkoutUrl;
      }
    } catch (error: any) {
      setErrorMsg(error.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="max-w-6xl mx-auto flex flex-col gap-12 animate-fade-in">
      <section className="relative overflow-hidden rounded-3xl border border-cyan-400/25 bg-gradient-to-br from-slate-900 via-slate-950 to-cyan-950/30 px-6 py-10 md:px-10 md:py-14">
        <div className="absolute -top-20 -right-20 h-56 w-56 rounded-full bg-cyan-500/20 blur-3xl" />
        <div className="absolute -bottom-24 -left-16 h-64 w-64 rounded-full bg-emerald-500/20 blur-3xl" />
        <div className="relative grid items-center gap-8 lg:grid-cols-[1.1fr_0.9fr]">
          <div>
            <p className="inline-flex rounded-full border border-cyan-300/40 bg-cyan-500/10 px-3 py-1 text-xs font-semibold uppercase tracking-widest text-cyan-200">
              {salesCopy.heroKicker}
            </p>
            <h1 className="mt-4 text-4xl font-extrabold tracking-tight leading-tight md:text-6xl">
              {heroTitle}
            </h1>
            <p className="mt-5 max-w-3xl text-lg leading-relaxed text-slate-300">
              {salesCopy.heroSub}
            </p>
            <div className="mt-6 flex flex-wrap gap-3 text-sm">
              <span className="rounded-full bg-slate-800/70 px-3 py-1 text-cyan-200">{salesCopy.trust1}</span>
              <span className="rounded-full bg-slate-800/70 px-3 py-1 text-cyan-200">{salesCopy.trust2}</span>
              <span className="rounded-full bg-slate-800/70 px-3 py-1 text-cyan-200">{salesCopy.trust3}</span>
            </div>
          </div>
          <div className="overflow-hidden rounded-3xl border border-cyan-400/20 bg-slate-950/70 shadow-2xl shadow-cyan-500/10">
            <Image
              src="/trading-desk-hero.svg"
              alt="Visual da mesa premium da UNI IA"
              width={1200}
              height={900}
              priority
              className="block h-auto w-full"
            />
          </div>
        </div>
      </section>

      <section className="grid lg:grid-cols-2 gap-8 w-full">
        <div className="border border-slate-800 bg-slate-900/60 rounded-2xl p-8 flex flex-col items-start gap-6 relative overflow-hidden backdrop-blur-sm">
          <div className="absolute top-0 right-0 p-4 opacity-10">
            <span className="text-8xl font-black">U</span>
          </div>
          <div>
            <h3 className="text-2xl font-bold mb-2">{salesCopy.freeTitle}</h3>
            <p className="text-slate-400 text-sm">{salesCopy.freeSub}</p>
          </div>
          <div className="text-4xl font-bold">$0<span className="text-lg text-slate-500 font-normal">/month</span></div>

          <ul className="space-y-3 text-slate-300 w-full mb-8">
            <li className="flex items-center gap-2">✓ Macro snapshots e contexto diario</li>
            <li className="flex items-center gap-2">✓ Alertas gerais de tendencia</li>
            <li className="flex items-center gap-2 opacity-50 line-through">Entrada premium prioritaria</li>
            <li className="flex items-center gap-2 opacity-50 line-through">Fluxo de mesa com aprovacao</li>
          </ul>

          <a href="https://t.me/uni_ia_free_bot" onClick={() => trackEvent('free_channel_click', { funnel: 'free' })} className="mt-auto w-full py-3 px-4 bg-slate-800 hover:bg-slate-700 text-center rounded-xl font-semibold transition-colors duration-200">
            {salesCopy.freeBtn}
          </a>
        </div>

        <div className="border-2 border-cyan-400 bg-slate-950 rounded-2xl p-8 flex flex-col items-start gap-6 relative shadow-2xl shadow-cyan-500/10 transform lg:-translate-y-3">
          <div className="absolute top-0 right-0 bg-cyan-400 text-slate-950 text-xs font-black px-3 py-1 rounded-bl-lg uppercase tracking-wide">
            Premium Desk
          </div>
          <div>
            <h3 className="text-2xl font-bold mb-2 text-white">UNI IA Premium</h3>
            <p className="text-cyan-200 text-sm">{salesCopy.premiumSub}</p>
          </div>
          <div className="text-4xl font-black text-transparent bg-clip-text bg-gradient-to-r from-cyan-300 to-emerald-300">
            $59<span className="text-lg text-slate-500 font-normal">/month</span>
          </div>

          <ul className="space-y-3 text-slate-100 w-full mb-6 font-medium">
            <li className="flex items-center gap-2 px-2 py-1 bg-slate-800/50 rounded">⚡ Entrega operacional em tempo quase real</li>
            <li className="flex items-center gap-2 px-2 py-1 bg-slate-800/50 rounded">🧠 Contexto explicavel por sinal</li>
            <li className="flex items-center gap-2 px-2 py-1 bg-slate-800/50 rounded">🛡 Gate de risco por camadas</li>
            <li className="flex items-center gap-2 px-2 py-1 bg-slate-800/50 rounded">🎛 Mesa privada com disciplina de execucao</li>
          </ul>

          <form onSubmit={handleCheckout} className="w-full space-y-3 mt-auto">
            {errorMsg && <div className="bg-red-500/10 border border-red-500/50 text-red-400 text-sm p-3 rounded-lg">{errorMsg}</div>}
            <input
              type="text"
              name="fullName"
              required
              placeholder={isPt ? 'Seu nome completo' : 'Your full name'}
              className="w-full bg-slate-900 border border-slate-700 rounded-xl px-4 py-3 outline-none focus:border-cyan-400 focus:ring-1 focus:ring-cyan-400 transition-all"
            />
            <input
              type="email"
              name="email"
              required
              placeholder={isPt ? 'Seu melhor e-mail' : 'Your best email'}
              className="w-full bg-slate-900 border border-slate-700 rounded-xl px-4 py-3 outline-none focus:border-cyan-400 focus:ring-1 focus:ring-cyan-400 transition-all"
            />
            <p className="text-xs text-slate-400 leading-relaxed">
              {risk.body} {risk.freeDelay}
            </p>
            <button
              disabled={loading}
              className="w-full py-4 text-slate-950 bg-gradient-to-r from-cyan-300 to-emerald-300 hover:from-cyan-200 hover:to-emerald-200 text-center rounded-xl font-black text-lg transition-transform transform hover:scale-[1.02] shadow-lg shadow-cyan-500/20 active:scale-95 disabled:opacity-50"
            >
              {loading ? (isPt ? 'Iniciando checkout seguro...' : 'Starting secure checkout...') : ctaFinal}
            </button>
          </form>
        </div>
      </section>

      <section className="grid md:grid-cols-3 gap-4">
        <div className="rounded-xl border border-slate-800 bg-slate-900/50 p-5">
          <p className="text-xs uppercase tracking-wider text-cyan-200">{salesCopy.stepTitle}</p>
          <p className="mt-3 text-sm text-slate-300">1. {salesCopy.step1}</p>
          <p className="mt-2 text-sm text-slate-300">2. {salesCopy.step2}</p>
          <p className="mt-2 text-sm text-slate-300">3. {salesCopy.step3}</p>
        </div>
        <div className="rounded-xl border border-slate-800 bg-slate-900/50 p-5 md:col-span-2">
          <p className="text-xs uppercase tracking-wider text-cyan-200">{salesCopy.forWhoTitle}</p>
          <ul className="mt-3 space-y-2 text-sm text-slate-300">
            <li>• {salesCopy.forWho1}</li>
            <li>• {salesCopy.forWho2}</li>
            <li>• {salesCopy.forWho3}</li>
          </ul>
        </div>
      </section>

      <section className="rounded-2xl border border-rose-400/40 bg-rose-950/25 px-5 py-4">
        <p className="text-rose-200 font-semibold">{risk.title}</p>
        <p className="text-rose-100 text-sm leading-relaxed mt-1">{risk.body}</p>
        <p className="text-rose-100 text-sm leading-relaxed font-bold mt-1">{risk.freeDelay}</p>
      </section>

      <section className="grid md:grid-cols-3 gap-4">
        <div className="rounded-xl border border-slate-800 bg-slate-900/50 p-5">
          <p className="text-sm font-semibold text-white">{salesCopy.faq1Q}</p>
          <p className="text-sm text-slate-300 mt-2">{salesCopy.faq1A}</p>
        </div>
        <div className="rounded-xl border border-slate-800 bg-slate-900/50 p-5">
          <p className="text-sm font-semibold text-white">{salesCopy.faq2Q}</p>
          <p className="text-sm text-slate-300 mt-2">{salesCopy.faq2A}</p>
        </div>
        <div className="rounded-xl border border-slate-800 bg-slate-900/50 p-5">
          <p className="text-sm font-semibold text-white">{salesCopy.faq3Q}</p>
          <p className="text-sm text-slate-300 mt-2">{salesCopy.faq3A}</p>
        </div>
      </section>
    </div>
  );
}
