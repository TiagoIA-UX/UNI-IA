export default function TermosPage() {
  return (
    <div className="max-w-4xl mx-auto py-12 px-6 animate-fade-in text-slate-300">
      <h1 className="text-4xl font-bold text-white mb-8">Termos de Uso - Uni IA (Zairyx)</h1>
      
      <div className="space-y-6 text-lg leading-relaxed">
        <section>
          <h2 className="text-2xl font-semibold text-white mb-3">1. Aceitação dos Termos</h2>
          <p>
            Ao acessar e utilizar os serviços de inteligência artificial da Uni IA (Zairyx), você concorda integralmente com estes termos. O serviço é destinado exclusivamente para ferramentas analíticas e não constitui recomendação financeira direta.
          </p>
        </section>

        <section>
          <h2 className="text-2xl font-semibold text-white mb-3">2. Isenção de Responsabilidade</h2>
          <p>
            As análises fornecidas pelo robô (multi-agentes) são baseadas em dados históricos e em tempo real. O mercado financeiro é de alto risco. A Uni IA não se responsabiliza por lucros cessantes, perdas de capital ou falhas de execução em corretoras terceiras.
          </p>
        </section>

        <section>
          <h2 className="text-2xl font-semibold text-white mb-3">3. Conformidade Legal (KYC/AML)</h2>
          <p>
            Em conformidade com as regulamentações financeiras aplicáveis, nós nos reservamos o direito de auditar assinaturas e suspender contas que apresentem indícios de lavagem de dinheiro ou uso indevido das nossas APIs de automação.
          </p>
        </section>

        <section>
          <h2 className="text-2xl font-semibold text-white mb-3">4. Transparência Algorítmica</h2>
          <p>
            Nossos modelos utilizam arquitetura LLM (Large Language Models) e indicadores técnicos clássicos. Nenhuma IA tem 100% de acerto. Promovemos auditorias regulares para atestar a estabilidade dos nossos agentes ("fallback" zero ativado).
          </p>
        </section>
      </div>
    </div>
  );
}
