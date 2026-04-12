'use client';

import { useEffect, useState } from 'react';
import { homeCopy, resolveLocale, riskCopy } from '@/lib/i18n';

export default function PlanosPage() {
  const [locale, setLocale] = useState<'en' | 'es' | 'pt' | 'ar' | 'zh'>('en');

  useEffect(() => {
    const params = new URLSearchParams(window.location.search);
    setLocale(resolveLocale(params.get('lang') || 'en'));
  }, []);

  const t = homeCopy[locale];
  const risk = riskCopy[locale];
  const [loading, setLoading] = useState(false);
  const [errorMsg, setErrorMsg] = useState('');
  
  const handleCheckout = async (e: React.FormEvent<HTMLFormElement>) => {
    e.preventDefault();
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
    <div className="max-w-6xl mx-auto flex flex-col items-center gap-12 animate-fade-in">
      <div className="text-center space-y-4">
        <h1 className="text-4xl md:text-5xl font-extrabold tracking-tight">
          Global Execution with <span className="bg-gradient-to-r from-blue-400 to-emerald-400 bg-clip-text text-transparent">Uni IA</span>
        </h1>
        <p className="text-slate-400 max-w-2xl mx-auto text-lg leading-relaxed">
          {t.heroSubtitle}
        </p>
        <div className="max-w-3xl mx-auto rounded-xl border border-rose-400/40 bg-rose-950/30 px-4 py-3 text-left">
          <p className="text-rose-200 font-semibold">{risk.title}</p>
          <p className="text-rose-100 text-sm leading-relaxed">{risk.body}</p>
          <p className="text-rose-100 text-sm leading-relaxed font-bold">{risk.freeDelay}</p>
        </div>
      </div>

      <div className="grid md:grid-cols-2 gap-8 w-full max-w-4xl">
        {/* FREE TIER */}
        <div className="border border-slate-800 bg-slate-900/50 rounded-2xl p-8 flex flex-col items-start gap-6 relative overflow-hidden backdrop-blur-sm">
          <div className="absolute top-0 right-0 p-4 opacity-10">
            <span className="text-8xl font-black">Z</span>
          </div>
          <div>
            <h3 className="text-2xl font-bold mb-2">Free Telegram Access</h3>
            <p className="text-slate-400 text-sm">Daily macro snapshots and trend monitoring.</p>
          </div>
          <div className="text-4xl font-bold">$0<span className="text-lg text-slate-500 font-normal">/month</span></div>
          
          <ul className="space-y-3 text-slate-300 w-full mb-8">
            <li className="flex items-center gap-2">✓ Generic trend alerts</li>
            <li className="flex items-center gap-2">✓ End-of-day market report</li>
            <li className="flex items-center gap-2 opacity-50 line-through">USD/EUR premium entries</li>
            <li className="flex items-center gap-2 opacity-50 line-through">Position guardian exit alerts</li>
          </ul>

          <a href="https://t.me/zairyx_free" className="mt-auto w-full py-3 px-4 bg-slate-800 hover:bg-slate-700 text-center rounded-xl font-semibold transition-colors duration-200">
            Join Free Channel
          </a>
        </div>

        {/* PREMIUM TIER */}
        <div className="border-2 border-blue-500 bg-slate-900 rounded-2xl p-8 flex flex-col items-start gap-6 relative shadow-2xl shadow-blue-500/10 transform md:-translate-y-4">
          <div className="absolute top-0 right-0 bg-blue-500 text-white text-xs font-bold px-3 py-1 rounded-bl-lg">
            MOST CHOSEN
          </div>
          <div>
            <h3 className="text-2xl font-bold mb-2 text-white">Zairyx Premium</h3>
            <p className="text-blue-300 text-sm">Real-time orchestration for paid traders and global desks.</p>
          </div>
          <div className="text-4xl font-black text-transparent bg-clip-text bg-gradient-to-r from-blue-400 to-emerald-400">
            $59<span className="text-lg text-slate-500 font-normal">/month</span>
          </div>
          
          <ul className="space-y-3 text-slate-200 w-full mb-6 font-medium">
            <li className="flex items-center gap-2 px-2 py-1 bg-slate-800/50 rounded">🔥 High-volatility USD/EUR setups</li>
            <li className="flex items-center gap-2 px-2 py-1 bg-slate-800/50 rounded">🚨 Loss-protection reversal alerts</li>
            <li className="flex items-center gap-2 px-2 py-1 bg-slate-800/50 rounded">🧠 Explainable confidence score</li>
            <li className="flex items-center gap-2 px-2 py-1 bg-slate-800/50 rounded">⚡ Multi-timeframe execution model</li>
          </ul>

          <form onSubmit={handleCheckout} className="w-full space-y-3 mt-auto">
            {errorMsg && <div className="bg-red-500/10 border border-red-500/50 text-red-400 text-sm p-3 rounded-lg">{errorMsg}</div>}
            <input 
              type="text" 
              name="fullName"
              required 
              placeholder="Your full name" 
              className="w-full bg-slate-800 border border-slate-700 rounded-xl px-4 py-3 outline-none focus:border-blue-500 focus:ring-1 focus:ring-blue-500 transition-all"
            />
            <input 
              type="email" 
              name="email"
              required 
              placeholder="Your best email" 
              className="w-full bg-slate-800 border border-slate-700 rounded-xl px-4 py-3 outline-none focus:border-blue-500 focus:ring-1 focus:ring-blue-500 transition-all"
            />
            <p className="text-xs text-slate-400 leading-relaxed">
              By subscribing, you acknowledge that trading involves risk, results are not guaranteed, and this platform does not provide investment advice.
            </p>
            <button 
              disabled={loading}
              className="w-full py-4 text-slate-950 bg-gradient-to-r from-blue-400 to-emerald-400 hover:from-blue-300 hover:to-emerald-300 text-center rounded-xl font-black text-lg transition-transform transform hover:scale-[1.02] shadow-lg shadow-emerald-500/20 active:scale-95 disabled:opacity-50"
            >
              {loading ? 'Starting secure checkout...' : 'Subscribe to Premium'}
            </button>
          </form>
        </div>
      </div>
    </div>
  );
}
