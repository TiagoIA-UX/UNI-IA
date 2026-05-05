# 📚 Guia Completo de Instalação - UNI IA

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
# Exemplo: C:\Users\SeuNome\Desktop\

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

### 2.2 Editar o arquivo `.env.local`

Abra o arquivo `.env.local` em um editor de texto (VS Code, Notepad++, etc):

```dotenv
# ⚠️ PREENCHER COM SEUS VALORES REAIS:

# 1. Supabase (Banco de dados)
NEXT_PUBLIC_SUPABASE_URL=https://seu-projeto.supabase.co
NEXT_PUBLIC_SUPABASE_PUBLISHABLE_KEY=seu_key_aqui
SUPABASE_SERVICE_ROLE_KEY=sua_chave_secreta_aqui

# 2. Groq API (Motor de IA)
GROQ_API_KEY=sua_chave_groq_aqui

# 3. Telegram (Notificações)
TELEGRAM_BOT_TOKEN=seu_token_bot
TELEGRAM_FREE_CHANNEL=@seu_canal

# ... (e outras variáveis)
```

**Onde conseguir essas chaves?**

| Serviço | Como conseguir | Tutorial |
|---------|---------------|----------|
| **Supabase** | [supabase.com](https://supabase.com) - criar conta grátis | Crie um projeto, vá em Settings > API |
| **Groq API** | [console.groq.com](https://console.groq.com) - grátis | Crie conta, vá em API Keys |
| **Telegram** | Fale com [@BotFather](https://t.me/botfather) no Telegram | `/newbot` e siga as instruções |

**⚠️ IMPORTANTE**: Nunca compartilhe seu `.env.local`! É como deixar sua senha na internet.

---

## 📦 Passo 3: Instalar Dependências

Dependências são **bibliotecas de código** que o projeto precisa para funcionar.

### 3.1 Backend (Python - Agentes de IA)

```bash
# Entrar na pasta do backend
cd ai-sentinel

# Criar ambiente isolado (virtual environment)
python -m venv venv

# Ativar o ambiente
# Windows:
venv\Scripts\activate

# Mac/Linux:
source venv/bin/activate

# Instalar bibliotecas
pip install -r requirements.txt

# Voltar para pasta raiz
cd ..
```

**O que significa `venv`?**
- É uma "caixa isolada" com suas próprias bibliotecas
- Evita conflitos entre projetos diferentes

### 3.2 Frontend (JavaScript - Interface web)

```bash
# Entrar na pasta do frontend
cd zairyx-blog

# Instalar dependências
npm install

# Voltar para pasta raiz
cd ..
```

---

## 🔧 Passo 4: Testar a Instalação

Agora vamos testar se tudo está funcionando.

### 4.1 Testar Backend

```bash
cd ai-sentinel

# Ativar venv novamente se não estiver ativado
# Windows:
venv\Scripts\activate

# Rodar o servidor
python run_local_api.py

# Você deve ver algo como:
# [INFO] Uvicorn running on http://127.0.0.1:8000
```

**Deixe este terminal rodando!** Abra um novo terminal para o próximo passo.

### 4.2 Testar Frontend

```bash
# Novo terminal
cd zairyx-blog
npm run dev

# Você deve ver algo como:
# ready - started server on 0.0.0.0:3000
```

### 4.3 Acessar a aplicação

Abra seu navegador e vá para:

```
http://localhost:3000
```

**Você deve ver a página inicial do UNI IA!** ✅

---

## 🎮 Passo 5: Usar a Aplicação

### 5.1 Fluxo básico de operação

```
1. Ir para http://localhost:3000/plataforma
2. Fazer login com suas credenciais
3. Selecionar um ativo (ex: BTCUSD)
4. Clicar em "Analisar"
5. Ver o score e classificação da IA
6. Aprovar ou rejeitar a operação
```

### 5.2 Modo de operação

A aplicação tem **3 modos**:

| Modo | O que faz | Quando usar |
|------|----------|------------|
| **`paper`** (padrão) | Simula operações, não gasta dinheiro real | Aprendizado e testes |
| **`approval`** | Pede sua aprovação antes de cada operação | Treinamento |
| **`live`** | Executa operações REAIS de verdade | Só após homologação completa |

**Configurar modo:**

No arquivo `.env.local`:
```dotenv
DESK_MODE=paper          # Seguro - simula
DESK_REQUIRE_MANUAL_APPROVAL=true  # Pede aprovação
```

---

## 🧪 Passo 6: Testar sem Risco (Recomendado)

Antes de usar dinheiro real, siga este roteiro:

### 6.1 Testar em `paper` (sem risco)
```
- Deixe DESK_MODE=paper
- Deixe DESK_REQUIRE_MANUAL_APPROVAL=true
- Faça 100+ análises de teste
- Valide os sinais durante 7 dias
```

### 6.2 Testar com aprovação manual
```
- Quando confiar, deixe DESK_MODE=paper mas monitore
- Analise cada operação proposta
- Aprove/rejeite manualmente
```

### 6.3 Só depois: modo live
```
- Comece com quantia MUITO pequena
- 1-2 semanas de operação real
- Aumente gradualmente se tudo der certo
```

---

## 🐛 Solução de Problemas

### Problema: "Module not found: @/lib/supabase/admin"

**Solução**: Certifique-se que está dentro da pasta `zairyx-blog`:
```bash
cd zairyx-blog
npm run dev
```

### Problema: "CRON_SECRET não configurado"

**Solução**: Adicione ao `.env.local`:
```dotenv
CRON_SECRET=seu_cron_secret_aqui
```

### Problema: Conexão com Supabase negada

**Solução**: Verifique se:
1. A URL do Supabase está correta
2. As chaves estão certas
3. Seu projeto no Supabase está ativo

### Problema: Telegram não está recebendo mensagens

**Solução**:
1. Verifique se `TELEGRAM_BOT_TOKEN` está correto
2. Verifique se `TELEGRAM_FREE_CHANNEL` existe
3. Rodar: `curl http://localhost:8000/api/telegram/status`

---

## 📚 Próximos Passos

Após instalação bem-sucedida:

### 1. Ler a documentação
- [README.md](../README.md) - Visão geral técnica
- [schema.sql](../schema.sql) - Estrutura do banco de dados
- [.env.example](../.env.example) - Todas as variáveis disponíveis

### 2. Explorar a aplicação
```bash
# Terminal 1: Backend rodando
cd ai-sentinel && python run_local_api.py

# Terminal 2: Frontend rodando
cd zairyx-blog && npm run dev

# Terminal 3: Você pode testar a API
curl http://localhost:8000/api/desk/status
```

### 3. Customizar para seus ativos
No `.env.local`, mude:
```dotenv
SIGNAL_SCAN_ASSETS=BTCUSD,ETHUSD    # Seus ativos
SIGNAL_MIN_SCORE=75                  # Sua tolerância a risco
SIGNAL_SCAN_INTERVAL_SECONDS=60     # Frequência de análise
```

---

## 🎓 Entender a Arquitetura

UNI IA usa **múltiplos agentes especializados**:

```
┌─────────────────────────────────────────────┐
│         ORQUESTRA DE DECISÃO (AEGIS)         │
├─────────────────────────────────────────────┤
│                                             │
│  MacroAgent     → Cenário geral (risk-on/off)
│  ATLAS          → Estrutura técnica (gráficos)
│  NewsAgent      → Notícias e contexto
│  SentimentAgent → Sentimento do mercado
│  TrendsAgent    → Anomalias de volume
│  Fundamentalist → Fundamentos da empresa
│                                             │
│         ↓↓↓ (Todos votam) ↓↓↓              │
│                                             │
│  SENTINEL (Gate de Risco) → Aprova/Rejeita │
│                                             │
└─────────────────────────────────────────────┘
```

Cada agente é um **especialista** em sua área. O sistema **funde as opiniões** com governança.

---

## 📞 Suporte

Se algo não funcionar:

1. **Verifique os logs**:
   ```bash
   # Backend: veja as mensagens no terminal onde rodou python
   # Frontend: abra DevTools (F12) no navegador
   ```

2. **Consulte a documentação**:
   - [Variáveis de ambiente](../.env.example)
   - [Schema do banco](../schema.sql)
   - [README técnico](../README.md)

3. **Contato**:
   - Issues no GitHub: https://github.com/TiagoIA-UX/UNI-IA/issues
   - Email: (a ser preenchido)

---

## ✅ Checklist de Instalação Completa

- [ ] Git, Node.js, Python instalados
- [ ] Repositório clonado (`git clone`)
- [ ] `.env.local` criado e preenchido
- [ ] Dependências instaladas (`pip install`, `npm install`)
- [ ] Backend testado (`python run_local_api.py`)
- [ ] Frontend testado (`npm run dev`)
- [ ] Aplicação acessível em `http://localhost:3000`
- [ ] Modo testado em `paper`
- [ ] Documentação lida

**Se tudo está verde, parabéns! Você está pronto para usar UNI IA!** 🎉

---

> **Última atualização**: Maio 5, 2026
> **Versão**: 1.0
> **Compatibilidade**: Windows, Mac, Linux
