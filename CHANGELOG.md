# Changelog

Todas as alterações notáveis ao repositório serão documentadas neste ficheiro.

O formato inspira-se em [Keep a Changelog](https://keepachangelog.com/pt-BR/1.0.0/).
A versionagem segue [Semantic Versioning](https://semver.org/lang/pt-BR/) onde aplicável
(*major* quando há *breaking*, *minor* para funcionalidades, *patch* para correções e docs relevantes para compliance).

---

## [Não lançado]

---

## [1.3.2] — 2026-05-12

### Corrigido

- Mesa (`PrivateDesk`): quando **`DESK_REQUIRE_MANUAL_APPROVAL`** está definida no ambiente, **prevalece** sobre **`UNI_IA_REQUIRE_APPROVAL`**, alinhando código a `.env.example` / `INSTALLATION.md`; valores não reconhecidos fazem fallback seguro para `UNI_IA_REQUIRE_APPROVAL`.

### Alterado

- **`.gitignore`:** entrada `ai-sentinel/backtest-export-*/` para evitar falhas de permissão em `git status`; mantidas regras de SO e scripts temporários na raiz.

### Testes

- Novos casos em `tests/test_desk_and_scanner.py` e isolamento em `base_env` (`DESK_REQUIRE_MANUAL_APPROVAL=""`) para evitar vazamento do ambiente do SO nas suites.

---

## [1.3.1] — 2026-05-12

### Documentação e governança (README)

- Reestruturação do **README** em formato orientado a **auditoria / due diligence**.
- Clarificação do **Conselho Guardião** como **metáfora analítica** (papéis técnicos), sem implicar obrigações de repasse automático por nomenclatura.
- Remoção da linguagem comercial/antiga centrada em «dízimo» e percentagens vinculantes sem enquadramento legal.
- Inclusão de **política institucional de destinação** (meta até **6%**) condicionada a lei vigente, *due diligence* de entidades e orientação técnico-contábil, com referência à tramitação do **PL 3.726/2023** ([Senado — matéria 158929](https://www25.senado.leg.br/web/atividade/materias/-/materia/158929)).
- Declaração explícita: **ausência de integração de runtime** com **Forge Ops AI** no código atual do monólito.
- Mantidas secções operacionais (*quick start*, rastreabilidade, risco, licença BUSL).

### Relação com `v1.3.0-doc-beta`

- A pré-release **`v1.3.0-doc-beta`** permanece como marco do *ledger* DOC opcional; **`v1.3.1`** consolida documentação institucional e transparência perante auditoria, **sem** alteração funcional obrigatória do motor de trading.
