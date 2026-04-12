export default function Home() {
  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '3rem' }}>
      <section style={{ textAlign: 'center', padding: '4rem 0' }}>
        <h2 style={{ fontSize: '3rem', fontWeight: 800, margin: '0 0 1rem 0', lineHeight: 1.1 }}>Domine o Mercado com os<br/> Sinais do <span style={{ color: '#3b82f6' }}>Uni IA</span></h2>
        <p style={{ fontSize: '1.25rem', color: '#cbd5e1', maxWidth: 600, margin: '0 auto 2rem auto' }}>
          Deixamos os analistas humanos para trás. 7 Agentes de IA orquestrados analisando o Dólar, o Euro e o Bovespa 24/7. Pare de perder dinheiro tentando adivinhar as tendências de Big Players.
        </p>
        <div style={{ display: 'flex', gap: '1rem', justifyContent: 'center' }}>
          <a href='/planos' style={{ background: '#10b981', color: '#fff', padding: '1rem 2rem', borderRadius: '0.5rem', fontWeight: 700, textDecoration: 'none', transition: 'all 0.2s', boxShadow: '0 10px 15px -3px rgba(16, 185, 129, 0.3)' }}>Assine Zairyx Premium (Dólar/Euro)</a>
          <a href='#telegram' style={{ background: 'transparent', color: '#f8fafc', padding: '1rem 2rem', borderRadius: '0.5rem', fontWeight: 600, textDecoration: 'none', border: '1px solid #334155' }}>Ver Sinais Grátis</a>
        </div>
      </section>

      <section style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(300px, 1fr))', gap: '2rem' }}>
        <div style={{ background: '#0f172a', padding: '2rem', borderRadius: '1rem', border: '1px solid #1e293b' }}>
          <h3 style={{ margin: '0 0 1rem 0', color: '#e2e8f0', fontSize: '1.5rem' }}>🤖 Guarda-Costas de Operações</h3>
          <p style={{ margin: 0, color: '#94a3b8', lineHeight: 1.6 }}>O Zairyx IA possui o PositionMonitorAgent, um agente dedicado exclusivamente a proteger contas. Se houver divergência no mercado após você realizar uma operação (Tape Reading revertendo), você recebe alerta de FECHAMENTO em tempo real.</p>
        </div>
        <div style={{ background: '#0f172a', padding: '2rem', borderRadius: '1rem', border: '1px solid #1e293b' }}>
          <h3 style={{ margin: '0 0 1rem 0', color: '#e2e8f0', fontSize: '1.5rem' }}>📊 Multi-Timeframe Crossover</h3>
          <p style={{ margin: 0, color: '#94a3b8', lineHeight: 1.6 }}>Nada de operar 'achismos' em gráfico de 5 minutos. O Uni IA obrigatoriamente concilia as tendências primárias do gráfico Semanal e Diário antes de liberar um sinal Scalper / Day-Trade.</p>
        </div>
        <div style={{ background: '#0f172a', padding: '2rem', borderRadius: '1rem', border: '1px solid #1e293b' }}>
          <h3 style={{ margin: '0 0 1rem 0', color: '#e2e8f0', fontSize: '1.5rem' }}>🧠 Radar Psicológico e VIX</h3>
          <p style={{ margin: 0, color: '#94a3b8', lineHeight: 1.6 }}>O sentimento das massas manipula os preços. O SentimentAgent drena milhares de manchetes econômicas por milissegundo e mede o nível de pânico ou FOMO no índice VIX comportamental.</p>
        </div>
      </section>
    </div>
  )
}
