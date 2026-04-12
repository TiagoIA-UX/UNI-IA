'use client';

import { useState } from 'react';
import { useRouter } from 'next/navigation';

export default function PlanosPage() {
  const router = useRouter();
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
        throw new Error(result.error || 'Falha ao processar assinatura');
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
          Acelere seus Lucros com <span className="bg-gradient-to-r from-blue-400 to-emerald-400 bg-clip-text text-transparent">Uni IA</span>
        </h1>
        <p className="text-slate-400 max-w-2xl mx-auto text-lg leading-relaxed">
          Exclusividade para Traders Profissionais e CFOs Corporativos. 
          O robô Zairyx processa bilhões de dados via Groq LLaMA3 e dita o ritmo de Wall Street no seu Telegram.
        </p>
      </div>

      <div className="grid md:grid-cols-2 gap-8 w-full max-w-4xl">
        {/* FREE TIER */}
        <div className="border border-slate-800 bg-slate-900/50 rounded-2xl p-8 flex flex-col items-start gap-6 relative overflow-hidden backdrop-blur-sm">
          <div className="absolute top-0 right-0 p-4 opacity-10">
            <span className="text-8xl font-black">Z</span>
          </div>
          <div>
            <h3 className="text-2xl font-bold mb-2">Acesso Básico (Telegram)</h3>
            <p className="text-slate-400 text-sm">Visão macroeconômica diária gratuita.</p>
          </div>
          <div className="text-4xl font-bold">R$ 0<span className="text-lg text-slate-500 font-normal">/mês</span></div>
          
          <ul className="space-y-3 text-slate-300 w-full mb-8">
            <li className="flex items-center gap-2">✓ Alertas de tendência genérica</li>
            <li className="flex items-center gap-2">✓ Relatórios fim-de-dia (B3)</li>
            <li className="flex items-center gap-2 opacity-50 line-through">Alerta de Oportunidades Dólar/Euro</li>
            <li className="flex items-center gap-2 opacity-50 line-through">Guardião de Posição Aberta</li>
          </ul>

          <a href="https://t.me/zairyx_free" className="mt-auto w-full py-3 px-4 bg-slate-800 hover:bg-slate-700 text-center rounded-xl font-semibold transition-colors duration-200">
            Entrar no Canal Free
          </a>
        </div>

        {/* PREMIUM TIER */}
        <div className="border-2 border-blue-500 bg-slate-900 rounded-2xl p-8 flex flex-col items-start gap-6 relative shadow-2xl shadow-blue-500/10 transform md:-translate-y-4">
          <div className="absolute top-0 right-0 bg-blue-500 text-white text-xs font-bold px-3 py-1 rounded-bl-lg">
            MAIS ESCOLHIDO
          </div>
          <div>
            <h3 className="text-2xl font-bold mb-2 text-white">Zairyx Premium</h3>
            <p className="text-blue-300 text-sm">Integração profunda Real-Time + Multi-Agentes.</p>
          </div>
          <div className="text-4xl font-black text-transparent bg-clip-text bg-gradient-to-r from-blue-400 to-emerald-400">
            R$ 297<span className="text-lg text-slate-500 font-normal">/mês</span>
          </div>
          
          <ul className="space-y-3 text-slate-200 w-full mb-6 font-medium">
            <li className="flex items-center gap-2 px-2 py-1 bg-slate-800/50 rounded">🔥 Sinais de Alta Volatilidade (USD/EUR)</li>
            <li className="flex items-center gap-2 px-2 py-1 bg-slate-800/50 rounded">🚨 Alerta Anti-Quebra (Reversão de Posição)</li>
            <li className="flex items-center gap-2 px-2 py-1 bg-slate-800/50 rounded">🧠 Score Explicável (Por que operar agora?)</li>
            <li className="flex items-center gap-2 px-2 py-1 bg-slate-800/50 rounded">⚡ Múltiplos Tempos Gráficos (5m a 1wk)</li>
          </ul>

          <form onSubmit={handleCheckout} className="w-full space-y-3 mt-auto">
            {errorMsg && <div className="bg-red-500/10 border border-red-500/50 text-red-400 text-sm p-3 rounded-lg">{errorMsg}</div>}
            <input 
              type="text" 
              name="fullName"
              required 
              placeholder="Seu nome completo" 
              className="w-full bg-slate-800 border border-slate-700 rounded-xl px-4 py-3 outline-none focus:border-blue-500 focus:ring-1 focus:ring-blue-500 transition-all"
            />
            <input 
              type="email" 
              name="email"
              required 
              placeholder="Seu melhor e-mail (Telegram ID)" 
              className="w-full bg-slate-800 border border-slate-700 rounded-xl px-4 py-3 outline-none focus:border-blue-500 focus:ring-1 focus:ring-blue-500 transition-all"
            />
            <button 
              disabled={loading}
              className="w-full py-4 text-slate-950 bg-gradient-to-r from-blue-400 to-emerald-400 hover:from-blue-300 hover:to-emerald-300 text-center rounded-xl font-black text-lg transition-transform transform hover:scale-[1.02] shadow-lg shadow-emerald-500/20 active:scale-95 disabled:opacity-50"
            >
              {loading ? 'Inicializando Escolta...' : 'Assinar Acesso Exclusivo'}
            </button>
          </form>
        </div>
      </div>
    </div>
  );
}
