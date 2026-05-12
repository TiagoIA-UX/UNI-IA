# Procedimentos em fase de testes — transparência auditável (DOC / Boitatá)

**Versão:** 0.1 (rascunho para GitHub)  
**Objetivo:** documentar, de forma **reproduzível**, como **proteger** o código-fonte versionado, **espelhar** o módulo DOC noutra localização e **executar** verificações mínimas **sem alterar** o software operacional já funcional (`ai-sentinel`, `zairyx-frontend`).

**Âmbito:** processo operacional da equipa desenvolvimento; não constitui orientação fiscal.

---

## 1. Princípio de segregação (“não tocar no que opera”)

| Caminho versionado sob teste | Motivo |
|------------------------------|--------|
| `boitata-doc/` | novo “software filho” — apenas este ramo deve ser configurado/evoluído para DOC |
| `ai-sentinel/`, `zairyx-frontend/` | mantidos **íntegros**; integração DOC futura = opt-in |

---

## 2. Backup de proteção (somente estado Git oficial)

Um snapshot **auditável** do que está **commitado** no repositório:

```powershell
Set-Location E:\01Boitata
New-Item -ItemType Directory -Force -Path E:\Boitata-backups | Out-Null
$zip = "E:\Boitata-backups\01Boitata_git_archive_$(Get-Date -Format yyyy-MM-dd).zip"
git archive --format=zip -o $zip HEAD
```

- **Vantagem:** prova de **conteúdo exato** referenciado por commit (hash Git no log + ficheiro zip datado).
- **Limite:** ficheiros **não** versionados (`*.env.local`, `venv`, `node_modules`) **não** entram — por desenho (segredos não devem estar no zip público).

**Registar no relatório mensal:** data, caminho `E:\Boitata-backups\...zip`, comando, e **`git rev-parse HEAD`**.

---

## 3. Espelho local no disco `C:` (clone do módulo filho)

Espelhar **apenas** o pacote DOC (rápido, sem cópias de `node_modules`/`venv` do monólito):

```powershell
robocopy E:\01Boitata\boitata-doc C:\BoitataDOC /MIR /R:2 /W:2 /XD .venv __pycache__ .pytest_cache
```

Opcionalmente, após cópia, criar um repositório Git **só** em `C:\BoitataDOC` para trabalho paralelo isolado (`git init`); ou continuar versionando só a cópia em `E:\01Boitata\boitata-doc` dentro do mesmo remoto principal (recomendado para uma única “fonte de verdade” no GitHub).

---

## 4. Trilho de evidência (“audit trail”) mínimo

1. **Commit** com mensagem descritiva em `boitata-doc/` (código + este documento).
2. **CI** (quando existir): `pytest` sobre `boitata-doc/tests`.
3. **Registo de exportações** do DOC: guardar ficheiros JSON/CSV/PDF gerados em pasta **fora** do Git (ex.: `C:\BoitataDOC\exports_local\`) com naming `YYYY-MM-DD_lote_...`.
4. **Integridade:** cada registo `EntradaDOC` mantém `hash_integridade`; documentos NAO gerados incluem `hash_documento` (ver `doc_module/nao_generator.py`).

---

## 5. Testes automáticos executáveis

```powershell
cd E:\01Boitata\boitata-doc
python -m pytest tests -q
```

Casos mínimos cobertos (ver `tests/`):

- classificação day vs swing (mesmo dia vs dias diferentes);
- isenção swing com volume mensal no limiar;
- recusa de exchange não listada com log de aviso legal;
- hash determinístico do registo.

---

## 6. Transparência no GitHub

- Abrir **Pull Request** com título do tipo: `docs: procedimentos auditáveis DOC (fase testes)`.
- No corpo do PR: indicar `git rev-parse HEAD`, lista de ficheiros novos em `boitata-doc/`, e confirmação de que **não** foram editados `ai-sentinel/api/main.py` nem rotas do frontend salvo acordo explícito.

---

## 7. Próximos passos (fora do escopo deste documento)

- Integração read-only do DOC com eventos de ordem (fila assíncrona);
- Validação de layout JSON com o **GCAP** oficial na versão vigente;
- Revisão jurídica/contábil de textos de NAO e de alíquotas.

---

*Documento operacional interno — Boitatá / Zairyx — DOC-Module.*
