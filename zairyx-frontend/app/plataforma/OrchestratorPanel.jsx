import { useState, useEffect, useRef } from "react";

// ─── Dados simulados com estrutura real do sistema ───────────────────────────
const MOCK_OPERATIONS = [
  {
    id: "OP-2026-0509-001",
    ativo: "BTCUSDT",
    nomeAtivo: "Bitcoin",
    direcao: "COMPRA",
    status: "monitorando",
    inicio: new Date(Date.now() - 1000 * 60 * 14),
    fim: null,
    precoEntrada: 80252.2,
    precoAtual: 80891.5,
    stopLoss: 79450.0,
    alvo: 82100.0,
    score: 87,
    agentes: [
      { nome: "Análise Técnica", voto: "COMPRA", confianca: 91 },
      { nome: "Contexto de Mercado", voto: "COMPRA", confianca: 85 },
      { nome: "Notícias Recentes", voto: "NEUTRO", confianca: 62 },
      { nome: "Sentimento", voto: "COMPRA", confianca: 88 },
      { nome: "Proteção de Capital", voto: "APROVADO", confianca: 95 },
    ],
    motivo:
      "O preço rompeu uma resistência importante e o volume confirma a força do movimento. O mercado global está favorável.",
    resultado: null,
  },
  {
    id: "OP-2026-0509-002",
    ativo: "ETHUSDT",
    nomeAtivo: "Ethereum",
    direcao: "VENDA",
    status: "encerrada",
    inicio: new Date(Date.now() - 1000 * 60 * 98),
    fim: new Date(Date.now() - 1000 * 60 * 41),
    precoEntrada: 2318.5,
    precoAtual: 2302.35,
    stopLoss: 2380.0,
    alvo: 2210.0,
    score: 81,
    agentes: [
      { nome: "Análise Técnica", voto: "VENDA", confianca: 83 },
      { nome: "Contexto de Mercado", voto: "VENDA", confianca: 79 },
      { nome: "Notícias Recentes", voto: "VENDA", confianca: 74 },
      { nome: "Sentimento", voto: "NEUTRO", confianca: 58 },
      { nome: "Proteção de Capital", voto: "APROVADO", confianca: 92 },
    ],
    motivo:
      "Formação de topo duplo identificada na estrutura de preços. Pressão vendedora crescente nas últimas 3 horas.",
    resultado: { tipo: "GANHO", variacao: -0.70, valorPts: 16.15 },
  },
  {
    id: "OP-2026-0509-003",
    ativo: "SOLUSDT",
    nomeAtivo: "Solana",
    direcao: "COMPRA",
    status: "rejeitada",
    inicio: new Date(Date.now() - 1000 * 60 * 210),
    fim: new Date(Date.now() - 1000 * 60 * 210),
    precoEntrada: null,
    precoAtual: 92.5,
    stopLoss: null,
    alvo: null,
    score: 68,
    agentes: [
      { nome: "Análise Técnica", voto: "COMPRA", confianca: 71 },
      { nome: "Contexto de Mercado", voto: "NEUTRO", confianca: 55 },
      { nome: "Notícias Recentes", voto: "VENDA", confianca: 61 },
      { nome: "Sentimento", voto: "NEUTRO", confianca: 49 },
      { nome: "Proteção de Capital", voto: "REJEITADO", confianca: 88 },
    ],
    motivo:
      "Pontuação abaixo do mínimo exigido (68 de 75). O sistema de proteção de capital bloqueou a operação por precaução.",
    resultado: null,
  },
];

// ─── Helpers ─────────────────────────────────────────────────────────────────
function formatTime(date) {
  return date.toLocaleTimeString("pt-BR", { hour: "2-digit", minute: "2-digit", second: "2-digit" });
}
function formatDate(date) {
  return date.toLocaleDateString("pt-BR", { day: "2-digit", month: "2-digit", year: "numeric" });
}
function duracao(inicio, fim) {
  const ms = (fim || new Date()) - inicio;
  const min = Math.floor(ms / 60000);
  const sec = Math.floor((ms % 60000) / 1000);
  if (min >= 60) return `${Math.floor(min / 60)}h ${min % 60}min`;
  return `${min}min ${sec}s`;
}
function useLiveTime() {
  const [now, setNow] = useState(new Date());
  useEffect(() => {
    const id = setInterval(() => setNow(new Date()), 1000);
    return () => clearInterval(id);
  }, []);
  return now;
}

// ─── Componente principal ─────────────────────────────────────────────────────
export default function OrchestratorPanel() {
  const now = useLiveTime();
  const [selected, setSelected] = useState(MOCK_OPERATIONS[0].id);
  const [livePrice, setLivePrice] = useState({ BTCUSDT: 80252.2, ETHUSDT: 2302.35, SOLUSDT: 92.5 });
  const [apiStatus, setApiStatus] = useState("conectando");
  const tickRef = useRef(null);

  // Simular feed de preços em tempo real
  useEffect(() => {
    setApiStatus("conectado");
    tickRef.current = setInterval(() => {
      setLivePrice((prev) => ({
        BTCUSDT: +(prev.BTCUSDT + (Math.random() - 0.5) * 40).toFixed(2),
        ETHUSDT: +(prev.ETHUSDT + (Math.random() - 0.5) * 4).toFixed(2),
        SOLUSDT: +(prev.SOLUSDT + (Math.random() - 0.5) * 0.3).toFixed(3),
      }));
    }, 1800);
    return () => clearInterval(tickRef.current);
  }, []);

  const op = MOCK_OPERATIONS.find((o) => o.id === selected);
  const currentPrice = livePrice[op.ativo] || op.precoAtual;

  const variacao = op.precoEntrada
    ? (((currentPrice - op.precoEntrada) / op.precoEntrada) * 100 * (op.direcao === "VENDA" ? -1 : 1)).toFixed(2)
    : null;

  const statusColor = {
    monitorando: "#22C55E",
    encerrada: "#94A3B8",
    rejeitada: "#EF4444",
    aguardando: "#F59E0B",
  };

  const statusLabel = {
    monitorando: "Monitorando agora",
    encerrada: "Encerrada",
    rejeitada: "Não executada",
    aguardando: "Aguardando aprovação",
  };

  const direcaoColor = { COMPRA: "#22C55E", VENDA: "#EF4444" };
  const votoColor = { COMPRA: "#22C55E", VENDA: "#EF4444", NEUTRO: "#94A3B8", APROVADO: "#22C55E", REJEITADO: "#EF4444" };

  return (
    <div style={{ fontFamily: "'DM Sans', 'Segoe UI', sans-serif", background: "#0A0F1E", minHeight: "100vh", color: "#E2E8F0", padding: "0" }}>
      {/* Google Font */}
      <style>{`
        @import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@300;400;500;600;700&family=DM+Mono:wght@400;500&display=swap');
        * { box-sizing: border-box; margin: 0; padding: 0; }
        ::-webkit-scrollbar { width: 4px; }
        ::-webkit-scrollbar-track { background: #0F172A; }
        ::-webkit-scrollbar-thumb { background: #334155; border-radius: 2px; }
        .op-card { cursor: pointer; transition: all 0.2s; border: 1px solid #1E293B; }
        .op-card:hover { border-color: #334155 !important; background: #111827 !important; }
        .op-card.active { border-color: #3B82F6 !important; background: #0F1C2E !important; }
        .pulse { animation: pulse 2s infinite; }
        @keyframes pulse { 0%, 100% { opacity: 1; } 50% { opacity: 0.4; } }
        .slide-in { animation: slideIn 0.3s ease; }
        @keyframes slideIn { from { opacity: 0; transform: translateY(8px); } to { opacity: 1; transform: translateY(0); } }
        .price-tick { animation: priceTick 0.4s ease; }
        @keyframes priceTick { 0% { background: #1E3A2F; } 100% { background: transparent; } }
      `}</style>

      {/* Header */}
      <div style={{ background: "#060C18", borderBottom: "1px solid #1E293B", padding: "16px 24px", display: "flex", alignItems: "center", justifyContent: "space-between" }}>
        <div style={{ display: "flex", alignItems: "center", gap: "12px" }}>
          <div style={{ width: "32px", height: "32px", background: "linear-gradient(135deg, #3B82F6, #8B5CF6)", borderRadius: "8px", display: "flex", alignItems: "center", justifyContent: "center", fontWeight: "700", fontSize: "14px" }}>U</div>
          <div>
            <div style={{ fontWeight: "600", fontSize: "15px", letterSpacing: "-0.3px" }}>UNI IA — Mesa Operacional</div>
            <div style={{ fontSize: "11px", color: "#64748B", fontFamily: "'DM Mono', monospace" }}>{formatDate(now)} · {formatTime(now)}</div>
          </div>
        </div>
        <div style={{ display: "flex", alignItems: "center", gap: "8px" }}>
          <div className={apiStatus === "conectado" ? "pulse" : ""} style={{ width: "7px", height: "7px", borderRadius: "50%", background: apiStatus === "conectado" ? "#22C55E" : "#EF4444" }} />
          <span style={{ fontSize: "12px", color: "#64748B" }}>{apiStatus === "conectado" ? "Feed ao vivo" : "Conectando..."}</span>
        </div>
      </div>

      {/* Preços ao vivo */}
      <div style={{ background: "#060C18", borderBottom: "1px solid #1E293B", padding: "8px 24px", display: "flex", gap: "32px" }}>
        {Object.entries(livePrice).map(([sym, price]) => (
          <div key={sym} className="price-tick" style={{ display: "flex", alignItems: "center", gap: "8px" }}>
            <span style={{ fontSize: "11px", color: "#64748B", fontFamily: "'DM Mono', monospace" }}>{sym}</span>
            <span style={{ fontSize: "13px", fontFamily: "'DM Mono', monospace", fontWeight: "500", color: "#E2E8F0" }}>${price.toLocaleString("en-US", { minimumFractionDigits: 2 })}</span>
          </div>
        ))}
      </div>

      <div style={{ display: "grid", gridTemplateColumns: "300px 1fr", height: "calc(100vh - 97px)" }}>

        {/* Sidebar — lista de operações */}
        <div style={{ borderRight: "1px solid #1E293B", overflowY: "auto", padding: "16px" }}>
          <div style={{ fontSize: "10px", fontWeight: "600", color: "#475569", letterSpacing: "0.1em", textTransform: "uppercase", marginBottom: "12px", padding: "0 4px" }}>
            Operações de Hoje
          </div>
          {MOCK_OPERATIONS.map((o) => (
            <div key={o.id} className={`op-card ${selected === o.id ? "active" : ""}`}
              style={{ borderRadius: "10px", padding: "12px", marginBottom: "8px", background: "#0A0F1E" }}
              onClick={() => setSelected(o.id)}>
              <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", marginBottom: "6px" }}>
                <div>
                  <span style={{ fontSize: "13px", fontWeight: "600" }}>{o.nomeAtivo}</span>
                  <span style={{ fontSize: "11px", color: "#475569", marginLeft: "6px", fontFamily: "'DM Mono', monospace" }}>{o.ativo}</span>
                </div>
                <span style={{ fontSize: "10px", padding: "2px 8px", borderRadius: "20px", background: statusColor[o.status] + "20", color: statusColor[o.status], fontWeight: "500" }}>
                  {o.status === "monitorando" && <span className="pulse" style={{ display: "inline-block", width: "5px", height: "5px", borderRadius: "50%", background: statusColor[o.status], marginRight: "4px", verticalAlign: "middle" }} />}
                  {statusLabel[o.status]}
                </span>
              </div>
              <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
                <span style={{ fontSize: "12px", padding: "2px 10px", borderRadius: "4px", background: direcaoColor[o.direcao] + "20", color: direcaoColor[o.direcao], fontWeight: "600" }}>{o.direcao}</span>
                <span style={{ fontSize: "11px", color: "#475569", fontFamily: "'DM Mono', monospace" }}>{formatTime(o.inicio)}</span>
              </div>
              {o.resultado && (
                <div style={{ marginTop: "6px", fontSize: "12px", color: o.resultado.tipo === "GANHO" ? "#22C55E" : "#EF4444", fontWeight: "600" }}>
                  {o.resultado.tipo === "GANHO" ? "▲" : "▼"} {Math.abs(o.resultado.variacao).toFixed(2)}% · {o.resultado.tipo}
                </div>
              )}
            </div>
          ))}
        </div>

        {/* Painel principal */}
        <div className="slide-in" key={selected} style={{ overflowY: "auto", padding: "24px" }}>

          {/* Cabeçalho da operação */}
          <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", marginBottom: "24px" }}>
            <div>
              <div style={{ display: "flex", alignItems: "center", gap: "10px", marginBottom: "4px" }}>
                <h1 style={{ fontSize: "22px", fontWeight: "700", letterSpacing: "-0.5px" }}>{op.nomeAtivo}</h1>
                <span style={{ fontSize: "13px", padding: "3px 12px", borderRadius: "6px", background: direcaoColor[op.direcao] + "25", color: direcaoColor[op.direcao], fontWeight: "700" }}>{op.direcao}</span>
                <span style={{ fontSize: "12px", padding: "3px 10px", borderRadius: "20px", background: statusColor[op.status] + "20", color: statusColor[op.status], fontWeight: "500" }}>
                  {op.status === "monitorando" && <span className="pulse" style={{ display: "inline-block", width: "6px", height: "6px", borderRadius: "50%", background: statusColor[op.status], marginRight: "5px", verticalAlign: "middle" }} />}
                  {statusLabel[op.status]}
                </span>
              </div>
              <div style={{ fontSize: "12px", color: "#475569", fontFamily: "'DM Mono', monospace" }}>{op.id}</div>
            </div>
            <div style={{ textAlign: "right" }}>
              <div style={{ fontSize: "28px", fontWeight: "700", fontFamily: "'DM Mono', monospace", letterSpacing: "-1px" }}>
                ${currentPrice.toLocaleString("en-US", { minimumFractionDigits: 2 })}
              </div>
              {variacao !== null && (
                <div style={{ fontSize: "13px", color: parseFloat(variacao) >= 0 ? "#22C55E" : "#EF4444", fontWeight: "600" }}>
                  {parseFloat(variacao) >= 0 ? "▲" : "▼"} {Math.abs(variacao)}% desde a entrada
                </div>
              )}
            </div>
          </div>

          {/* Linha do tempo */}
          <div style={{ background: "#0D1526", border: "1px solid #1E293B", borderRadius: "12px", padding: "20px", marginBottom: "16px" }}>
            <div style={{ fontSize: "11px", fontWeight: "600", color: "#475569", letterSpacing: "0.08em", textTransform: "uppercase", marginBottom: "16px" }}>Linha do Tempo</div>
            <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr 1fr", gap: "16px" }}>
              <div>
                <div style={{ fontSize: "11px", color: "#475569", marginBottom: "4px" }}>Detecção da oportunidade</div>
                <div style={{ fontSize: "15px", fontWeight: "600", fontFamily: "'DM Mono', monospace" }}>{formatTime(op.inicio)}</div>
                <div style={{ fontSize: "11px", color: "#64748B" }}>{formatDate(op.inicio)}</div>
              </div>
              <div>
                <div style={{ fontSize: "11px", color: "#475569", marginBottom: "4px" }}>
                  {op.status === "monitorando" ? "Duração até agora" : "Duração total"}
                </div>
                <div style={{ fontSize: "15px", fontWeight: "600", fontFamily: "'DM Mono', monospace" }}>
                  {duracao(op.inicio, op.fim)}
                </div>
                <div style={{ fontSize: "11px", color: "#64748B" }}>
                  {op.status === "monitorando" ? "em andamento" : "operação encerrada"}
                </div>
              </div>
              <div>
                <div style={{ fontSize: "11px", color: "#475569", marginBottom: "4px" }}>
                  {op.fim ? "Encerramento" : "Previsão de encerramento"}
                </div>
                <div style={{ fontSize: "15px", fontWeight: "600", fontFamily: "'DM Mono', monospace" }}>
                  {op.fim ? formatTime(op.fim) : "— em aberto —"}
                </div>
                <div style={{ fontSize: "11px", color: "#64748B" }}>
                  {op.fim ? formatDate(op.fim) : "monitoramento contínuo"}
                </div>
              </div>
            </div>

            {/* Barra de progresso visual */}
            {op.precoEntrada && op.status === "monitorando" && (
              <div style={{ marginTop: "16px" }}>
                <div style={{ display: "flex", justifyContent: "space-between", fontSize: "10px", color: "#475569", marginBottom: "4px" }}>
                  <span>Stop: ${op.stopLoss?.toLocaleString()}</span>
                  <span>Entrada: ${op.precoEntrada?.toLocaleString()}</span>
                  <span>Alvo: ${op.alvo?.toLocaleString()}</span>
                </div>
                <div style={{ height: "6px", background: "#1E293B", borderRadius: "3px", position: "relative" }}>
                  {(() => {
                    const range = op.alvo - op.stopLoss;
                    const pos = Math.max(0, Math.min(100, ((currentPrice - op.stopLoss) / range) * 100));
                    return (
                      <>
                        <div style={{ position: "absolute", left: `${((op.precoEntrada - op.stopLoss) / range) * 100}%`, width: "2px", height: "100%", background: "#475569" }} />
                        <div style={{ position: "absolute", left: `${pos}%`, transform: "translateX(-50%)", width: "12px", height: "12px", top: "-3px", borderRadius: "50%", background: parseFloat(variacao) >= 0 ? "#22C55E" : "#EF4444", border: "2px solid #0D1526" }} />
                      </>
                    );
                  })()}
                </div>
              </div>
            )}
          </div>

          {/* O que o sistema detectou */}
          <div style={{ background: "#0D1526", border: "1px solid #1E293B", borderRadius: "12px", padding: "20px", marginBottom: "16px" }}>
            <div style={{ fontSize: "11px", fontWeight: "600", color: "#475569", letterSpacing: "0.08em", textTransform: "uppercase", marginBottom: "12px" }}>O que o sistema detectou</div>
            <p style={{ fontSize: "14px", lineHeight: "1.7", color: "#CBD5E1" }}>{op.motivo}</p>
            {op.status === "rejeitada" && (
              <div style={{ marginTop: "12px", padding: "10px 14px", background: "#EF444415", border: "1px solid #EF444430", borderRadius: "8px", fontSize: "13px", color: "#FCA5A5" }}>
                Esta operação não foi executada. O capital permanece protegido.
              </div>
            )}
            {op.resultado && (
              <div style={{ marginTop: "12px", padding: "10px 14px", background: op.resultado.tipo === "GANHO" ? "#22C55E15" : "#EF444415", border: `1px solid ${op.resultado.tipo === "GANHO" ? "#22C55E30" : "#EF444430"}`, borderRadius: "8px", fontSize: "13px", color: op.resultado.tipo === "GANHO" ? "#86EFAC" : "#FCA5A5" }}>
                Resultado: {op.resultado.tipo} de {Math.abs(op.resultado.variacao).toFixed(2)}% · {op.resultado.valorPts > 0 ? "+" : ""}{op.resultado.valorPts} pontos
              </div>
            )}
          </div>

          {/* Votação dos agentes */}
          <div style={{ background: "#0D1526", border: "1px solid #1E293B", borderRadius: "12px", padding: "20px", marginBottom: "16px" }}>
            <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "16px" }}>
              <div style={{ fontSize: "11px", fontWeight: "600", color: "#475569", letterSpacing: "0.08em", textTransform: "uppercase" }}>Avaliação dos Especialistas</div>
              <div style={{ display: "flex", alignItems: "center", gap: "8px" }}>
                <span style={{ fontSize: "11px", color: "#475569" }}>Pontuação geral</span>
                <span style={{ fontSize: "16px", fontWeight: "700", fontFamily: "'DM Mono', monospace", color: op.score >= 75 ? "#22C55E" : "#EF4444" }}>{op.score}/100</span>
              </div>
            </div>
            <div style={{ display: "flex", flexDirection: "column", gap: "10px" }}>
              {op.agentes.map((a) => (
                <div key={a.nome} style={{ display: "flex", alignItems: "center", gap: "12px" }}>
                  <div style={{ width: "28px", height: "28px", borderRadius: "6px", background: votoColor[a.voto] + "20", display: "flex", alignItems: "center", justifyContent: "center" }}>
                    <span style={{ fontSize: "11px", color: votoColor[a.voto] }}>
                      {a.voto === "COMPRA" || a.voto === "APROVADO" ? "▲" : a.voto === "VENDA" || a.voto === "REJEITADO" ? "▼" : "—"}
                    </span>
                  </div>
                  <div style={{ flex: 1 }}>
                    <div style={{ display: "flex", justifyContent: "space-between", marginBottom: "3px" }}>
                      <span style={{ fontSize: "13px", color: "#CBD5E1" }}>{a.nome}</span>
                      <span style={{ fontSize: "11px", color: votoColor[a.voto], fontWeight: "600" }}>{a.voto}</span>
                    </div>
                    <div style={{ height: "3px", background: "#1E293B", borderRadius: "2px" }}>
                      <div style={{ height: "100%", width: `${a.confianca}%`, background: votoColor[a.voto], borderRadius: "2px", transition: "width 1s ease" }} />
                    </div>
                  </div>
                  <span style={{ fontSize: "11px", color: "#475569", fontFamily: "'DM Mono', monospace", width: "32px", textAlign: "right" }}>{a.confianca}%</span>
                </div>
              ))}
            </div>
          </div>

          {/* Limites de risco */}
          {op.precoEntrada && (
            <div style={{ background: "#0D1526", border: "1px solid #1E293B", borderRadius: "12px", padding: "20px" }}>
              <div style={{ fontSize: "11px", fontWeight: "600", color: "#475569", letterSpacing: "0.08em", textTransform: "uppercase", marginBottom: "16px" }}>Limites de Controle de Risco</div>
              <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr 1fr", gap: "16px" }}>
                {[
                  { label: "Preço de Entrada", value: `$${op.precoEntrada?.toLocaleString("en-US", { minimumFractionDigits: 2 })}`, desc: "onde a operação começou", color: "#3B82F6" },
                  { label: "Limite de Perda", value: `$${op.stopLoss?.toLocaleString("en-US", { minimumFractionDigits: 2 })}`, desc: "encerra automaticamente se atingir", color: "#EF4444" },
                  { label: "Alvo de Ganho", value: `$${op.alvo?.toLocaleString("en-US", { minimumFractionDigits: 2 })}`, desc: "objetivo de encerramento", color: "#22C55E" },
                ].map((item) => (
                  <div key={item.label} style={{ padding: "14px", background: "#0A0F1E", borderRadius: "8px", border: `1px solid ${item.color}25` }}>
                    <div style={{ fontSize: "10px", color: "#475569", marginBottom: "6px", textTransform: "uppercase", letterSpacing: "0.05em" }}>{item.label}</div>
                    <div style={{ fontSize: "18px", fontWeight: "700", fontFamily: "'DM Mono', monospace", color: item.color, marginBottom: "4px" }}>{item.value}</div>
                    <div style={{ fontSize: "11px", color: "#475569" }}>{item.desc}</div>
                  </div>
                ))}
              </div>
              <div style={{ marginTop: "12px", padding: "10px 14px", background: "#1E293B40", borderRadius: "8px", fontSize: "12px", color: "#64748B", lineHeight: "1.6" }}>
                Aviso regulatório: Toda operação envolve risco e pode resultar em perda total do capital alocado. As informações acima são geradas automaticamente pelo sistema e não constituem recomendação de investimento.
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
