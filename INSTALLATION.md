# 📚 Guia Completo de Instalação — UNI IA

> **Para iniciantes**: Este guia é escrito como se você fosse um aluno aprendendo do zero. Sem jargão desnecessário. Passo a passo.

---

## 🎯 O que é UNI IA?

UNI IA é um **laboratório de inteligência artificial financeira** que:
- Analisa mercados usando múltiplos agentes especializados
- Toma decisões com **governança rigorosa**
- Executa operações com **controle de risco obsessivo**
- Mantém **auditoria completa** de cada passo

**Garantia de segurança**: Antes de executar qualquer operação real de trading, o sistema exige aprovação manual humana.

---

## 📋 Pré-Requisitos (Antes de começar)

Você precisa ter instalado no seu computador:

| Ferramenta | O que é | Como instalar |
|-----------|--------|--------------|
| **Git** | Ferramenta para baixar código | [git-scm.com](https://git-scm.com/) |
| **Node.js** (v18+) | Ambiente JavaScript | [nodejs.org](https://nodejs.org/) |
| **Python** (3.9+) | Linguagem para IA | [python.org](https://www.python.org/) |
| **npm** ou **yarn** | Gerenciador de pacotes Node | Vem com Node.js |

**Como verificar se estão instalados:**
```bash
git --version
node --version
python --version
npm --version
```

Se aparecer a versão, está instalado. ✅

---

## 🚀 Passo 1: Clonar o Repositório

Clonar significa fazer uma **cópia completa do código** do GitHub para seu computador.

### No Windows (PowerShell ou CMD):

```bash
# Escolha uma pasta onde quer guardar o projeto
cd Desktop

# Copie o código do GitHub
git clone https://github.com/TiagoIA-UX/UNI-IA.git

# Entre na pasta do projeto
cd UNI-IA
```

### No Mac/Linux:

```bash
cd ~/Desktop
git clone https://github.com/TiagoIA-UX/UNI-IA.git
cd UNI-IA
```

**O que aconteceu?**
- Uma pasta `UNI-IA` foi criada com todo o código
- Você está dentro dessa pasta agora

---

## ⚙️ Passo 2: Configurar Variáveis de Ambiente

Variáveis de ambiente são **senhas e chaves secretas** que o sistema precisa para funcionar.

### 2.1 Copiar o arquivo de exemplo

```bash
# Windows
copy .env.example .env.local

# Mac/Linux
cp .env.example .env.local
```

### 2.2 Proteção obrigatória — leia antes de continuar

> ⛔ **ATENÇÃO CRÍTICA**: O arquivo `.env.local` contém suas senhas reais. Ele **NUNCA** deve ir para o GitHub.
>
> O projeto já possui um `.gitignore` configurado que bloqueia este arquivo automaticamente. Para confirmar que está protegido, verifique:
>
> ```bash
> # Windows
> type .gitignore | findstr ".env"
>
> # Mac/Linux
> grep ".env" .gitignore
> ```
>
> Se aparecer `.env.local` ou `.env*.local` na saída, você está protegido. ✅
> Se não aparecer, adicione manualmente:
>
> ```bash
> echo ".env.local" >> .gitignore
> ```

### 2.3 Como preencher o `.env.local` corretamente

Abra o arquivo `.env.local` em um editor de texto (VS Code, Notepad++, etc).

**Regras de preenchimento:**

| Regra | Correto ✅ | Errado ❌ |
|-------|-----------|----------|
| Sem espaços ao redor do `=` | `CHAVE=valor` | `CHAVE = valor` |
| Sem aspas (na maioria dos casos) | `URL=https://exemplo.com` | `URL="https://exemplo.com"` |
| Sem comentários na mesma linha | `CHAVE=valor` | `CHAVE=valor # meu comentário` |
| Sem espaços no início da linha | `CHAVE=valor` | `  CHAVE=valor` |

**Onde conseguir cada chave:**

#### 🗄️ Supabase (banco de dados)
1. Acesse [supabase.com](https://supabase.com) → crie uma conta grátis
2. Clique em **"New Project"** → dê um nome → crie
3. Aguarde ~2 minutos enquanto o banco é provisionado
4. Vá em **Settings → API**
5. Copie os três valores:

```dotenv
NEXT_PUBLIC_SUPABASE_URL=https://XXXXXXXXXXXXXXXX.supabase.co
NEXT_PUBLIC_SUPABASE_PUBLISHABLE_KEY=eyJhbGci...  ← campo "anon / public"
SUPABASE_SERVICE_ROLE_KEY=eyJhbGci...             ← campo "service_role" (⚠️ nunca exponha)
```

#### 🤖 Groq API (motor de IA)
1. Acesse [console.groq.com](https://console.groq.com) → crie uma conta grátis
2. Vá em **API Keys → Create API Key**
3. Dê um nome (ex: `uni-ia-local`) e clique em Create
4. **Copie imediatamente** — a chave só é exibida uma vez

```dotenv
GROQ_API_KEY=gsk_XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX
```

> ⚠️ **Se o Groq estiver fora do ar**: O sistema interrompe o ciclo automaticamente (sem gerar sinais inválidos) e envia um alerta via Telegram para o canal administrativo. Configure `LLM_FAILURE_ALERT_ENABLED=true` e `TELEGRAM_ADMIN_CHAT_IDS` no `.env.local`.

#### 🔐 CRON_SECRET (segurança do agendador)
Gere uma senha aleatória segura diretamente no terminal:

```bash
node -e "console.log(require('crypto').randomBytes(32).toString('hex'))"
```

Copie o resultado e cole:

```dotenv
CRON_SECRET=resultado_aqui
```

#### 📱 Telegram (notificações — essencial para alertas operacionais)
1. No Telegram, busque por **@BotFather**
2. Envie `/newbot` e siga as instruções
3. Copie o token fornecido

```dotenv
TELEGRAM_BOT_TOKEN=1234567890:AAxxxxxxxxxxxxxx
TELEGRAM_FREE_CHANNEL=@nome_do_seu_canal
LLM_FAILURE_ALERT_ENABLED=true
TELEGRAM_ADMIN_CHAT_IDS=seu_chat_id_aqui
```

> 💡 Para descobrir seu `TELEGRAM_ADMIN_CHAT_IDS`, envie uma mensagem para o seu bot e acesse `/api/telegram/status` — o campo `last_seen_chat_id` mostrará o valor correto.

---

## 📦 Passo 3: Instalar Dependências

### 3.1 Backend (Python — Agentes de IA)

```bash
# Entrar na pasta do backend
cd ai-sentinel

# Criar ambiente isolado
python -m venv venv

# Ativar o ambiente:
# Windows:
venv\Scripts\activate
# Mac/Linux:
source venv/bin/activate

# Instalar bibliotecas
pip install -r requirements.txt

# Voltar para pasta raiz
cd ..
```

> **O que é `venv`?** Uma "caixa isolada" com suas próprias bibliotecas, que evita conflitos entre projetos diferentes.

### 3.2 Frontend (JavaScript — Interface web)

```bash
cd zairyx-blog
npm install
cd ..
```

---

## 🗄️ Passo 4: Configurar o Banco de Dados

1. No painel do Supabase, clique no seu projeto
2. No menu lateral, clique em **"SQL Editor"** → **"New query"**
3. Abra o arquivo `schema.sql` da raiz do projeto
4. Copie todo o conteúdo (`Ctrl+A` → `Ctrl+C`) e cole no editor
5. Clique em **"Run"** (`Ctrl + Enter`)

Resultado esperado: `Success. No rows returned` ✅

---

## ▶️ Passo 5: Rodar o Projeto Localmente

O projeto precisa de **dois terminais abertos ao mesmo tempo**.

### Terminal 1 — Backend (IA)

```bash
cd ai-sentinel

# Windows:
venv\Scripts\activate
# Mac/Linux:
source venv/bin/activate

python run_local_api.py
```

Aguarde:
```
INFO:     Uvicorn running on http://127.0.0.1:8000
```
✅ Backend rodando. **Não feche este terminal.**

### Terminal 2 — Frontend (interface)

```bash
cd zairyx-blog
npm run dev
```

Aguarde:
```
▲ Next.js
- Local: http://localhost:3000
- Ready in 2.1s
```
✅ Frontend rodando. **Não feche este terminal.**

### Para encerrar

Quando quiser parar, pressione `Ctrl + C` em cada terminal.

---

## 🌐 Passo 6: Acessar a Aplicação

Abra seu navegador e acesse: **[http://localhost:3000](http://localhost:3000)**

Você verá a interface do UNI IA carregando. ✅

---

## 🎮 Passo 7: Fluxo de Uso

```
1. Acesse http://localhost:3000/plataforma
2. Faça login com suas credenciais
3. Selecione um ativo (ex: BTCUSD)
4. Clique em "Analisar"
5. Veja o score e classificação da IA
6. Aprove ou rejeite a operação
```

### Modos de operação

| Modo | O que faz | Quando usar |
|------|----------|------------|
| **`paper`** (padrão) | Simula operações, sem dinheiro real | ✅ Sempre no início |
| **`approval`** | Pede aprovação antes de cada operação | Após 7+ dias em paper |
| **`live`** | Executa operações **reais** | Só após homologação completa |

Configure no `.env.local`:
```dotenv
DESK_MODE=paper
DESK_REQUIRE_MANUAL_APPROVAL=true
```

---

## 🧪 Passo 8: Roteiro Progressivo de Testes (Recomendado)

**Não pule etapas. Sua segurança financeira depende disso.**

### Etapa 1 — Modo paper (mínimo 7 dias)
- `DESK_MODE=paper`
- `DESK_REQUIRE_MANUAL_APPROVAL=true`
- Faça 100+ análises de teste
- Anote e valide os sinais

### Etapa 2 — Aprovação manual (7–14 dias)
- Continue em `paper`
- Analise e decida manualmente cada operação proposta
- Registre acertos e erros

### Etapa 3 — Modo live (somente após as etapas anteriores)
- Comece com no máximo 1–2% do seu capital
- Aumente gradualmente apenas com resultados consistentes

---

## 🐛 Solução de Problemas

### ❌ "Module not found: @/lib/supabase/admin"
Certifique-se de rodar de dentro da pasta correta:
```bash
cd zairyx-blog
npm run dev
```

### ❌ "CRON_SECRET não configurado"
```bash
# Verifique se o arquivo .env.local existe (não .env.example):
ls -la | grep .env      # Mac/Linux
dir | findstr ".env"    # Windows
```
Adicione ao `.env.local`: `CRON_SECRET=seu_valor_aqui`

### ❌ Conexão com Supabase negada
1. Confirme que `NEXT_PUBLIC_SUPABASE_URL` começa com `https://` e termina com `.supabase.co`
2. Verifique se não há espaços extras nas chaves
3. Confirme que o projeto no Supabase não está pausado

### ❌ Telegram não recebe mensagens
1. Verifique se o bot foi adicionado como **admin** no canal
2. Teste: `curl http://localhost:8000/api/telegram/status`

### ❌ Groq retorna erro 429 ou 5xx
O sistema interrompe o ciclo e dispara alerta Telegram automaticamente (quando `LLM_FAILURE_ALERT_ENABLED=true`). Verifique o status em [console.groq.com](https://console.groq.com) e retome via comando `/cycle` no canal administrativo.

### ❌ Porta 3000 já em uso
```bash
# Mac/Linux:
lsof -ti:3000 | xargs kill -9

# Windows:
netstat -ano | findstr :3000
taskkill /PID <numero> /F
```

### ❌ "python: command not found" no Windows
1. Abra "Adicionar ou remover programas" → Python → Modify
2. Marque **"Add Python to PATH"**
3. Reinicie o terminal

### ❌ "npm: command not found"
1. Reinstale o Node.js em [nodejs.org](https://nodejs.org)
2. Feche **todos** os terminais e abra um novo

### ❌ Erro ao reinstalar dependências do Node
```bash
rm -rf node_modules package-lock.json
npm install
```

### ❌ `pip install` falha com erro de permissão
```bash
pip install -r requirements.txt --user
```

### ❌ `.env.local` foi para o GitHub por engano
**Ação imediata — não ignore isso:**
1. Revogue **todas** as chaves comprometidas (Supabase, Groq, Telegram) nos respectivos painéis
2. Gere novas chaves
3. Remova o arquivo do histórico Git:
```bash
git rm --cached .env.local
echo ".env.local" >> .gitignore
git commit -m "fix: remove .env.local and add to gitignore"
git push
```

---

## 🎓 Arquitetura do Sistema

UNI IA usa **múltiplos agentes especializados** que votam em conjunto:

```
┌─────────────────────────────────────────────┐
│         ORQUESTRA DE DECISÃO (AEGIS)         │
├─────────────────────────────────────────────┤
│                                             │
│  MacroAgent     → Cenário geral (risk-on/off)│
│  ATLAS          → Estrutura técnica          │
│  NewsAgent      → Notícias e contexto        │
│  SentimentAgent → Sentimento do mercado      │
│  TrendsAgent    → Anomalias de volume        │
│  Fundamentalist → Fundamentos do ativo       │
│                                             │
│         ↓↓↓ (Todos votam) ↓↓↓              │
│                                             │
│  SENTINEL (Gate de Risco) → Aprova/Rejeita  │
│                                             │
└─────────────────────────────────────────────┘
```

Nenhuma decisão passa sem consenso. Cada voto é registrado e auditável.

---

## 📚 Próximos Passos

1. **Leia a documentação**:
   - [README.md](../README.md) — visão geral técnica e estratégica
   - [schema.sql](../schema.sql) — estrutura do banco de dados
   - [.env.example](../.env.example) — todas as variáveis disponíveis

2. **Explore a API**: `curl http://localhost:8000/api/desk/status`

3. **Customize para seus ativos** no `.env.local`:
   ```dotenv
   SIGNAL_SCAN_ASSETS=BTCUSD,ETHUSD
   SIGNAL_MIN_SCORE=75
   SIGNAL_SCAN_INTERVAL_SECONDS=60
   ```

---

## ✅ Checklist de Instalação Completa

- [ ] Git, Node.js e Python instalados e verificados
- [ ] Repositório clonado com `git clone`
- [ ] `.env.local` criado (não `.env.example`)
- [ ] `.env.local` protegido no `.gitignore`
- [ ] Supabase: URL e chaves preenchidas corretamente
- [ ] Groq: API Key preenchida
- [ ] CRON_SECRET gerado e preenchido
- [ ] Telegram: bot criado e `LLM_FAILURE_ALERT_ENABLED=true` configurado
- [ ] Schema SQL executado no Supabase (5 tabelas criadas)
- [ ] Backend rodando (`python run_local_api.py` → porta 8000)
- [ ] Frontend rodando (`npm run dev` → porta 3000)
- [ ] Aplicação acessível em `http://localhost:3000`
- [ ] Pelo menos 1 análise feita em modo `paper`
- [ ] README.md lido

**Se tudo está marcado: parabéns, você está pronto para usar o UNI IA!** 🎉

---

## 📞 Suporte

Se algo não funcionar após seguir este guia:

1. **Verifique os logs**:
   - Backend: mensagens no terminal onde rodou `python run_local_api.py`
   - Frontend: abra DevTools no navegador (`F12` → aba Console)

2. **Abra uma issue no GitHub**:
   [github.com/TiagoIA-UX/UNI-IA/issues](https://github.com/TiagoIA-UX/UNI-IA/issues)
   Inclua: sistema operacional, versões instaladas e o erro completo.

---

> **Última atualização**: 07 de Maio de 2026
> **Versão**: 1.2 (revisada)
> **Compatibilidade**: Windows, Mac, Linux
