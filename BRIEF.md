# BRIEF — backup-gfs-verificacao-hash

**Projeto:** backup-gfs-verificacao-hash
**Área:** Suporte TI
**Stack:** PowerShell (opcional), Python
**Saída:** `C:\Users\Kelvin\AppData\Local\Temp\opencode\github-staging\projects\backup-gfs-verificacao-hash\`
**Autor:** Kelvin Oliveira — Licença: MIT

## Entregas

| Arquivo | Conteúdo |
|---------|----------|
| `src/backup_gfs/__init__.py` | Exporta a API pública do pacote |
| `src/backup_gfs/gfs.py` | Core: `sha256_file`, `sha256_tree`, `make_backup`, `list_backups`, `rotate`, `restore`, `verify` + dataclasses `BackupInfo`, `RotateReport`, `VerifyResult` |
| `src/backup_gfs/__main__.py` | CLI: `create`, `rotate`, `restore`, `verify` |
| `tests/test_gfs.py` | 26 testes pytest |
| `README.md` | Bilíngue PT-BR + EN (título, descrição, como usar, testes, licença MIT, autor) |
| `BRIEF.md` | Este arquivo |
| `pyproject.toml` | Metadados do projeto, `pythonpath = ["src"]` para pytest |

## O que o código faz

- **Rotação GFS simulada:** backups diário / semanal / mensal em `tmp_dir`. O tipo é inferido da data (dia 1 = mensal, domingo = semanal, demais = diário) ou informado via `--kind`. A retenção mantém os N mais recentes de cada tipo (`daily_keep=7`, `weekly_keep=4`, `monthly_keep=12` por padrão).
- **Hash SHA-256:** de arquivo único (`sha256_file`) e de árvore (`sha256_tree`), armazenado em `manifest.sha256` dentro de cada backup.
- **Restauração:** reconstrói o original a partir do backup (arquivo ou diretório), substituindo o destino se já existir.
- **Verificação byte-a-byte:** compara conjunto de arquivos e cada arquivo byte a byte via SHA-256, além do hash agregado das árvores. Retorna `ok`, `byte_equal`, hashes e mensagem.

## Como verificar

1. Entrar na pasta do projeto:
   ```
   cd C:\Users\Kelvin\AppData\Local\Temp\opencode\github-staging\projects\backup-gfs-verificacao-hash
   ```

2. Lint:
   ```
   python -m ruff check .
   ```
   Resultado esperado: `All checks passed!`

3. Testes:
   ```
   python -m pytest -q
   ```
   Resultado esperado: `26 passed in ~1.2s`

4. CLI (opcional, smoke test):
   ```
   python -m backup_gfs create arquivo.txt ./backups --at 2026-10-16T10:00:00Z
   python -m backup_gfs verify ./backups/daily-20261016-100000 ./arquivo.txt
   python -m backup_gfs rotate ./backups
   ```

## Critérios de aceitação (MVP)

- [x] Restauração OK (`restore` reconstrói o original)
- [x] Testes que passam (26/26)
- [x] README PT-BR + EN completa
- [ ] PowerShell — não implementado (opcional; a CLI Python cobre criar, rotacionar, restaurar e verificar)

## Como rodar sem instalar pacote

O pytest lê `src` via `pythonpath` configurado em `pyproject.toml`. Não há dependências externas além da biblioteca padrão do Python.
