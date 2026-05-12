# Boitatá DOC — Diário de Operações com Criptoativos (módulo filho)

**Estado:** fase de **desenvolvimento e testes** — **não substitui** o motor `ai-sentinel` nem o frontend.

### Política de releases (transparência)

- O projeto-pai (**01Boitata**) e este módulo estão **em construção**; comportamento e integrações podem mudar entre commits.
- **Antes** de iniciar operações sistemáticas **em conta real**, a equipa deve publicar no GitHub um **release semântico** com notas claras de risco, dependências e limites regulatórios. As tags `doc` / pré-release servem apenas para **marcar marcos de código**, não aval de investimento nem de compliance fiscal automatizado.

### Ledger no software pai (opcional)

Com `DOC_LEDGER_ENABLED=true` no `.env.local` da API (`ai-sentinel`), cada execução bem-sucedida via `CopyTradeService` grava evidência técnica (símbolo, lado, preço/ref MB, timeframe, **hint** day/swing preliminar). O ficheiro por defeito no Windows é `C:\BoitataDOC\data\doc_ledger.jsonl` (sobrescrevível com `DOC_LEDGER_PATH`). **Não** dispensa extratos da corretora nem GCAP/DIRPF.

Este diretório é um **pacote independente**: não altera importações nem ficheiros do software operacional já em produção local. Serve como base para **transparência, rastreio e auditoria** de registos fiscais (processuais/documentais), segundo o desenho funcional DOCM v1 descrito nos documentos incluídos.

## Avisos legais

- Este software **não é assessoria jurídica nem tributária**.
- Regras de IR, isenção, DARF e GCAP **variam com a legislação e interpretação administrativa/jurisprudência**; valide sempre com **contador** e fontes oficiais da RFB.
- A lista `EXCHANGES_AUTORIZADAS` é referência de documentação; **a autorização regulatória deve ser verificada na data da operação** nas fontes BACEN/institucionais.

## Estrutura

```
boitata-doc/
├── doc_module/           # Núcleo Python (registo, apuração, export, NAO)
├── docs/                  # Procedimentos auditáveis (GitHub)
├── scripts/               # Backup / clones (referência operacional)
└── tests/                 # Testes unitários determinísticos
```

## Execução rápida dos testes

```powershell
cd E:\01Boitata\boitata-doc
py -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements-dev.txt -q
python -m pytest tests -q
```

## Ligação ao repositório principal

- **Ledger JSONL** (opcional): implementado em `ai-sentinel/core/doc_ledger.py`, invocado após `place_order` no copy trade.
- **Pacote `doc_module/`**: continua utilizável em standalone (exportadores, NAO simbólica, testes) para processar ou cruzar com o ledger.

## Espelho no disco do sistema (`C:`)

| Passo | Ação |
|-------|------|
| 1 | `robocopy E:\01Boitata\boitata-doc C:\BoitataDOC /MIR /XD .venv __pycache__ .pytest_cache` |
| 2 | PowerShell **como administrador**: `boitata-doc/scripts/win/ensure-boitatadoc-admin-c-drive.ps1` (cria `C:\BoitataDOC\data` e ajusta ACLs ao seu utilizador) |
| 3 | No `.env.local`, `DOC_LEDGER_PATH=C:\BoitataDOC\data\doc_ledger.jsonl` se não quiser o default |

Se a política da máquina **bloquear escrita na raiz de `C:\`**, defina `DOC_LEDGER_PATH` para uma pasta no seu perfil (ex.: `%USERPROFILE%\BoitataDOC\data\doc_ledger.jsonl`) — o software **não** impõe `C:`; apenas sugere para alinhar ao “clone” administrativo.

Documentação adicional: `docs/PROCEDIMENTOS-TESTE-AUDITORIA.md`.
