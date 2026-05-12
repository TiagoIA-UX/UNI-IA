# Boitatá DOC — Diário de Operações com Criptoativos (módulo filho)

**Estado:** fase experimental / testes — **não substitui** o motor `ai-sentinel` nem o frontend.

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

O monólito **01Boitata** pode evoluir com **integrações opcionais** (hooks que chamam este módulo após uma ordem). Até lá, os registos podem ser alimentados **manualmente**, por CSV ou por script de ingestão próprio — sem tocar nos serviços em execução.

## Espelho no disco do sistema

Ver `docs/PROCEDIMENTOS-TESTE-AUDITORIA.md` — clone recomendado: `C:\BoitataDOC` (cópia apenas de `boitata-doc/`, não do venv do `ai-sentinel`).
