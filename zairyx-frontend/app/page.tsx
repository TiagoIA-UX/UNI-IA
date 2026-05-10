import React from 'react';

export default function DashboardPage() {
  return (
    <main style={{ width: '100vw', height: '100vh', margin: 0, padding: 0, overflow: 'hidden', backgroundColor: '#0a0e1a' }}>
      <iframe 
        src="/index.html" 
        style={{ width: '100%', height: '100%', border: 'none', display: 'block' }}
        title="UNI IA - Dashboard de Operações"
      />
    </main>
  );
}