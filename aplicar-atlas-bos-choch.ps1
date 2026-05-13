# ════════════════════════════════════════════════════════════════════════════
# BOITATÁ IA — ATLAS: Corrigir BOS + Adicionar CHoCH
# Arquivo: E:\01Boitata\ai-sentinel\agents\atlas_agent.py
#
# Codificação: UTF-8 com BOM (compatível com Windows PowerShell 5.1). Também pode usar:
#   pwsh -NoProfile -ExecutionPolicy Bypass -File .\aplicar-atlas-bos-choch.ps1
#
# O que este script corrige:
#   1. BOS usava highs[-1] como preco atual (errado) → usa close[-1]
#   2. CHoCH completamente ausente → adicionado com lógica correta
#   3. Estrutura só era calculada em M1-M30 → agora em TODOS os timeframes
#   4. System prompt não mencionava BOS/CHoCH → atualizado
#
# Execução:
#   Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
#   .\aplicar-atlas-bos-choch.ps1                    # commit local (sem push)
#   .\aplicar-atlas-bos-choch.ps1 -Push             # commit + git push
#   $env:BOITATA_ATLAS_PUSH = '1'; .\aplicar-atlas-bos-choch.ps1
#   .\aplicar-atlas-bos-choch.ps1 -NoGit            # só altera o .py, sem git
# ════════════════════════════════════════════════════════════════════════════

[CmdletBinding()]
param(
    [switch] $Push,
    [switch] $NoGit
)

$doPush = $Push -or ($env:BOITATA_ATLAS_PUSH -eq '1')

$atlasFile = "E:\01Boitata\ai-sentinel\agents\atlas_agent.py"

Write-Host ""
Write-Host "════════════════════════════════════════" -ForegroundColor DarkGreen
Write-Host "  BOITATÁ IA — ATLAS: BOS + CHoCH" -ForegroundColor Yellow
Write-Host "════════════════════════════════════════" -ForegroundColor DarkGreen
Write-Host ""

if (-not (Test-Path $atlasFile)) {
    Write-Host "❌ atlas_agent.py não encontrado em $atlasFile" -ForegroundColor Red
    exit 1
}

$conteudo = Get-Content $atlasFile -Raw -Encoding UTF8

# ── PASSO 1: Estender estrutura para TODOS os timeframes ─────────────────────
Write-Host "[ 1/4 ] Estendendo detecção de estrutura para todos os timeframes..." -ForegroundColor Cyan

$de1 = '_USER_CHART_SWING_STRUCTURE_TFS = frozenset({"1m", "2m", "5m", "15m", "30m"})'
$para1 = '_USER_CHART_SWING_STRUCTURE_TFS = frozenset({"1m", "2m", "5m", "15m", "30m", "1h", "90m", "4h", "1d", "1wk", "1mo", "3mo"})'

if ($conteudo -like "*$de1*") {
    $conteudo = $conteudo.Replace($de1, $para1)
    Write-Host "   ✅ _USER_CHART_SWING_STRUCTURE_TFS expandido para todos os TFs" -ForegroundColor Green
} else {
    Write-Host "   ⚠️  Linha _USER_CHART_SWING_STRUCTURE_TFS não encontrada — verifique manualmente" -ForegroundColor Yellow
}

# ── PASSO 2: Corrigir system prompt para mencionar BOS/CHoCH ─────────────────
Write-Host ""
Write-Host "[ 2/4 ] Atualizando system prompt do ATLAS..." -ForegroundColor Cyan

$de2 = @'
        Regras:
1. NUNCA invente numeros. Use APENAS os fornecidos.
2. Analise a confluencia entre timeframes.
3. Identifique se a estrutura permite risco (entrada) ou nao.

Sua saida DEVE ser UNICA E EXCLUSIVAMENTE um JSON estrito:
{
    "signal_type": "STRONG BUY" ou "BUY" ou "NEUTRAL" ou "SELL" ou "STRONG SELL",
    "confidence": 85.5,
    "summary": "Interpretacao estrutural objetiva baseada nas features."
}
'@

$para2 = @'
        Regras:
1. NUNCA invente numeros. Use APENAS os fornecidos.
2. Analise a confluencia entre timeframes.
3. Identifique se a estrutura permite risco (entrada) ou nao.
4. Priorize features de estrutura: structure_bos, structure_choch, structure_pattern, structure_trend.
5. BOS (Break of Structure) confirmado = continuidade da tendencia vigente.
6. CHoCH (Change of Character) confirmado = possivel reversao — aumente peso se presente.
7. Para scalping (M1-M15): user_chart_tf_structure_bos e user_chart_tf_structure_choch sao o gatilho principal.

Sua saida DEVE ser UNICA E EXCLUSIVAMENTE um JSON estrito:
{
    "signal_type": "STRONG BUY" ou "BUY" ou "NEUTRAL" ou "SELL" ou "STRONG SELL",
    "confidence": 85.5,
    "summary": "Interpretacao estrutural objetiva: mencione BOS/CHoCH se presentes."
}
'@

if ($conteudo -like "*Priorize features de estrutura*") {
    Write-Host "   ℹ️  System prompt já inclui BOS/CHoCH" -ForegroundColor Gray
} elseif ($conteudo -like "*NUNCA invente numeros*") {
    $conteudo = $conteudo.Replace($de2, $para2)
    Write-Host "   ✅ System prompt atualizado com regras BOS/CHoCH" -ForegroundColor Green
} else {
    Write-Host "   ⚠️  System prompt não encontrado no formato esperado" -ForegroundColor Yellow
}

# ── PASSO 3: Corrigir _detect_market_structure (BOS + CHoCH) ─────────────────
Write-Host ""
Write-Host "[ 3/4 ] Substituindo _detect_market_structure com CHoCH + BOS corrigido..." -ForegroundColor Cyan

$deMetodo = @'
    def _detect_market_structure(self, highs: np.ndarray, lows: np.ndarray) -> Dict[str, Any]:
        """Detecta HH/HL/LH/LL e Break of Structure."""
        result: Dict[str, Any] = {
            "pattern": "undefined",
            "trend": "undefined",
            "bos": False,
            "swing_high": None,
            "swing_low": None,
        }

        if len(highs) < 10:
            return result

        # Find swing points (simplified: local extremes over 5-bar window)
        swing_highs = []
        swing_lows = []
        for i in range(2, len(highs) - 2):
            if highs[i] >= max(highs[i - 2], highs[i - 1], highs[i + 1], highs[i + 2]):     
                swing_highs.append((i, float(highs[i])))
            if lows[i] <= min(lows[i - 2], lows[i - 1], lows[i + 1], lows[i + 2]):
                swing_lows.append((i, float(lows[i])))

        if len(swing_highs) < 2 or len(swing_lows) < 2:
            return result

        last_sh = swing_highs[-1][1]
        prev_sh = swing_highs[-2][1]
        last_sl = swing_lows[-1][1]
        prev_sl = swing_lows[-2][1]

        result["swing_high"] = last_sh
        result["swing_low"] = last_sl

        hh = last_sh > prev_sh
        hl = last_sl > prev_sl
        lh = last_sh < prev_sh
        ll = last_sl < prev_sl

        if hh and hl:
            result["pattern"] = "HH+HL"
            result["trend"] = "bullish"
        elif lh and ll:
            result["pattern"] = "LH+LL"
            result["trend"] = "bearish"
        elif hh and ll:
            result["pattern"] = "HH+LL"
            result["trend"] = "expansion"
        elif lh and hl:
            result["pattern"] = "LH+HL"
            result["trend"] = "compression"
        else:
            result["pattern"] = "mixed"
            result["trend"] = "neutral"

        # BOS: preco atual rompeu ultimo swing high ou low
        current_close = float(highs[-1])  # approximate with last high
        if current_close > last_sh:
            result["bos"] = True
        elif float(lows[-1]) < last_sl:
            result["bos"] = True

        return result
'@

$paraMetodo = @'
    def _detect_market_structure(
        self,
        highs: np.ndarray,
        lows: np.ndarray,
        closes: Optional[np.ndarray] = None,
    ) -> Dict[str, Any]:
        """Detecta HH/HL/LH/LL, BOS e CHoCH.

        Usa o ultimo close do array closes quando tem o mesmo comprimento que highs/lows;
        caso contrario usa a media (high+low)/2 do ultimo candle como fallback.
        """
        result: Dict[str, Any] = {
            "pattern": "undefined",
            "trend": "undefined",
            "bos": False,
            "choch": False,
            "choch_direction": None,
            "swing_high": None,
            "swing_low": None,
        }

        if len(highs) < 10:
            return result

        swing_highs = []
        swing_lows = []
        for i in range(2, len(highs) - 2):
            if highs[i] >= max(highs[i - 2], highs[i - 1], highs[i + 1], highs[i + 2]):
                swing_highs.append((i, float(highs[i])))
            if lows[i] <= min(lows[i - 2], lows[i - 1], lows[i + 1], lows[i + 2]):
                swing_lows.append((i, float(lows[i])))

        if len(swing_highs) < 2 or len(swing_lows) < 2:
            return result

        last_sh = swing_highs[-1][1]
        prev_sh = swing_highs[-2][1]
        last_sl = swing_lows[-1][1]
        prev_sl = swing_lows[-2][1]

        result["swing_high"] = last_sh
        result["swing_low"] = last_sl

        hh = last_sh > prev_sh
        hl = last_sl > prev_sl
        lh = last_sh < prev_sh
        ll = last_sl < prev_sl

        if hh and hl:
            result["pattern"] = "HH+HL"
            result["trend"] = "bullish"
        elif lh and ll:
            result["pattern"] = "LH+LL"
            result["trend"] = "bearish"
        elif hh and ll:
            result["pattern"] = "HH+LL"
            result["trend"] = "expansion"
        elif lh and hl:
            result["pattern"] = "LH+HL"
            result["trend"] = "compression"
        else:
            result["pattern"] = "mixed"
            result["trend"] = "neutral"

        if closes is not None and len(closes) == len(highs) and len(closes) > 0:
            current_close = float(closes[-1])
        else:
            current_close = float((highs[-1] + lows[-1]) / 2.0)

        trend = result["trend"]
        if trend == "bullish":
            if current_close > last_sh:
                result["bos"] = True
            if current_close < last_sl:
                result["choch"] = True
                result["choch_direction"] = "bearish"
        elif trend == "bearish":
            if current_close < last_sl:
                result["bos"] = True
            if current_close > last_sh:
                result["choch"] = True
                result["choch_direction"] = "bullish"
        else:
            if current_close > last_sh or current_close < last_sl:
                result["bos"] = True

        return result
'@

if ($conteudo -match 'closes:\s*Optional\[np\.ndarray\]\s*=\s*None') {
    Write-Host "   ℹ️  _detect_market_structure já inclui CHoCH + closes (nada a fazer)" -ForegroundColor Gray
} elseif ($conteudo.Contains($deMetodo)) {
    $conteudo = $conteudo.Replace($deMetodo, $paraMetodo)
    Write-Host "   ✅ _detect_market_structure reescrito com CHoCH + BOS corrigido" -ForegroundColor Green
} else {
    Write-Host "   ⚠️  Bloco legado de _detect_market_structure não encontrado — verifique atlas_agent.py" -ForegroundColor Yellow
}

# Chamada 1D: passar série de fechamento para BOS/CHoCH precisos
$deCall1d = "self._detect_market_structure(high_1d, low_1d)"
$paraCall1d = "self._detect_market_structure(high_1d, low_1d, close_1d)"
if ($conteudo.Contains($paraCall1d)) {
    Write-Host "   ℹ️  Chamada 1D já passa close_1d" -ForegroundColor Gray
} elseif ($conteudo.Contains($deCall1d)) {
    $conteudo = $conteudo.Replace($deCall1d, $paraCall1d)
    Write-Host "   ✅ compute_features: estrutura 1D usa close_1d" -ForegroundColor Green
}

# ── PASSO 4: Expor CHoCH nas features do gráfico (user_chart_tf_*) ───────────
Write-Host ""
Write-Host "[ 4/4 ] Expondo choch nas features user_chart_tf_..." -ForegroundColor Cyan

$deExposicao = @'
            if len(hi) >= 10:
                st = self._detect_market_structure(hi, lo)
                features["user_chart_tf_structure_pattern"] = st.get("pattern")
                features["user_chart_tf_structure_trend"] = st.get("trend")
                features["user_chart_tf_structure_bos"] = bool(st.get("bos"))
'@

$paraExposicao = @'
            if len(hi) >= 10:
                st = self._detect_market_structure(hi, lo, close)
                features["user_chart_tf_structure_pattern"] = st.get("pattern")
                features["user_chart_tf_structure_trend"] = st.get("trend")
                features["user_chart_tf_structure_bos"] = bool(st.get("bos"))
                features["user_chart_tf_structure_choch"] = bool(st.get("choch"))
                features["user_chart_tf_structure_choch_direction"] = st.get("choch_direction")
                features["user_chart_tf_swing_high"] = _safe(st.get("swing_high"))
                features["user_chart_tf_swing_low"] = _safe(st.get("swing_low"))
'@

if ($conteudo -match 'user_chart_tf_structure_choch') {
    Write-Host "   ℹ️  Features user_chart_tf já expõem CHoCH / swings" -ForegroundColor Gray
} elseif ($conteudo -like '*features["user_chart_tf_structure_bos"] = bool(st.get("bos"))*') {
    $conteudo = $conteudo.Replace($deExposicao, $paraExposicao)
    Write-Host "   ✅ CHoCH e swing levels expostos nas features user_chart_tf_" -ForegroundColor Green
} else {
    Write-Host "   ⚠️  Bloco de exposição não encontrado no formato esperado" -ForegroundColor Yellow
}

# Expor também nas features base (1D)
$deBase = @'
        features["structure_pattern"] = structure["pattern"]
        features["structure_trend"] = structure["trend"]
        features["structure_bos"] = structure["bos"]
        features["structure_swing_high"] = _safe(structure["swing_high"])
        features["structure_swing_low"] = _safe(structure["swing_low"])
'@

$paraBase = @'
        features["structure_pattern"] = structure["pattern"]
        features["structure_trend"] = structure["trend"]
        features["structure_bos"] = structure["bos"]
        features["structure_choch"] = bool(structure.get("choch"))
        features["structure_choch_direction"] = structure.get("choch_direction")
        features["structure_swing_high"] = _safe(structure["swing_high"])
        features["structure_swing_low"] = _safe(structure["swing_low"])
'@

if ($conteudo -match 'features\["structure_choch"\]') {
    Write-Host "   ℹ️  Features base já expõem CHoCH" -ForegroundColor Gray
} elseif ($conteudo -like '*features["structure_bos"] = structure["bos"]*') {
    $conteudo = $conteudo.Replace($deBase, $paraBase)
    Write-Host "   ✅ CHoCH exposto nas features base (1D)" -ForegroundColor Green
} else {
    Write-Host "   ⚠️  Bloco de features base não encontrado" -ForegroundColor Yellow
}

# ── Salvar ────────────────────────────────────────────────────────────────────
$utf8NoBom = New-Object System.Text.UTF8Encoding $false
[System.IO.File]::WriteAllText(
    $atlasFile,
    ($conteudo.TrimEnd() + [Environment]::NewLine),
    $utf8NoBom
)
Write-Host ""
Write-Host "   💾 atlas_agent.py salvo." -ForegroundColor Cyan

# ── Git commit (opcional) ─────────────────────────────────────────────────────
if (-not $NoGit) {
    Write-Host ""
    Write-Host "Git (ai-sentinel)..." -ForegroundColor Cyan
    Set-Location "E:\01Boitata\ai-sentinel"
    git add agents/atlas_agent.py
    $gitStatus = git status --porcelain
    if ($gitStatus) {
        git commit -m "fix(atlas): BOS usa close real; adiciona CHoCH; estrutura em todos os TFs"
        if ($doPush) {
            git push
            Write-Host "   ✅ Commit e push enviados" -ForegroundColor Green
        } else {
            Write-Host "   ✅ Commit local feito (sem push). Use -Push ou BOITATA_ATLAS_PUSH=1 para enviar." -ForegroundColor Green
        }
    } else {
        Write-Host "   ℹ️  Nada a commitar — arquivo já está atualizado" -ForegroundColor Gray
    }
} else {
    Write-Host ""
    Write-Host "   ℹ️  -NoGit: ignorando git add/commit" -ForegroundColor Gray
}

# ── Resultado ─────────────────────────────────────────────────────────────────
Write-Host ""
Write-Host "════════════════════════════════════════" -ForegroundColor DarkGreen
Write-Host "  ✅ ATLAS CORRIGIDO" -ForegroundColor Green
Write-Host "════════════════════════════════════════" -ForegroundColor DarkGreen
Write-Host ""
Write-Host "  O que mudou:" -ForegroundColor White
Write-Host "  · BOS: corrigido para usar close real (era highs[-1])" -ForegroundColor Gray
Write-Host "  · CHoCH: adicionado — detecta reversão de tendência" -ForegroundColor Gray
Write-Host "  · Estrutura: calculada em TODOS os timeframes (antes só M1-M30)" -ForegroundColor Gray
Write-Host "  · Features novas: structure_choch, structure_choch_direction," -ForegroundColor Gray
Write-Host "                    user_chart_tf_structure_choch, user_chart_tf_swing_high/low" -ForegroundColor Gray
Write-Host "  · System prompt: ATLAS agora instrui o LLM a priorizar BOS/CHoCH" -ForegroundColor Gray
Write-Host ""
Write-Host "  O que NÃO mudou (intocado):" -ForegroundColor White
Write-Host "  · Toda a lógica de RSI, MACD, ATR, VWAP, Volume" -ForegroundColor Gray
Write-Host "  · Interface AgentSignal / FeatureStore" -ForegroundColor Gray
Write-Host "  · Chamada ao LLM Groq" -ForegroundColor Gray
Write-Host '  · Todos os outros agentes (AEGIS, ORION, MACRO)' -ForegroundColor Gray
Write-Host ""
Write-Host "  Próximo passo:" -ForegroundColor Yellow
Write-Host "  Reinicie o uvicorn e faça uma análise no M1 ou M5." -ForegroundColor Cyan
Write-Host "  As features structure_bos e structure_choch aparecem no log do backend." -ForegroundColor Cyan
Write-Host "  O AEGIS passa a receber dados coerentes com o timeframe." -ForegroundColor Cyan
Write-Host ""
Write-Host "  Validar no terminal Python:" -ForegroundColor Yellow
Write-Host '  from agents.atlas_agent import AtlasAgent' -ForegroundColor Cyan
Write-Host '  a = AtlasAgent()' -ForegroundColor Cyan
Write-Host '  f = a.compute_features(''BTC-BRL'', chart_timeframe=''5m'')' -ForegroundColor Cyan
Write-Host '  print(f[''user_chart_tf_structure_choch''], f[''user_chart_tf_structure_bos''])' -ForegroundColor Cyan
Write-Host ""
