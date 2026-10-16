# backup-gfs-verificacao-hash

Backup GFS (avô-pai-filho) com hash SHA-256, restauração e verificação byte-a-byte, em Python.

Projeto da área Suporte TI. O MVP implementa o ciclo avô-pai-filho (diário / semanal / mensal, simulado em `tmp_dir`), o cálculo de SHA-256, a restauração e a verificação byte-a-byte de um backup contra o original.

Critérios de aceitação: restauração OK, testes passando, README completa em PT-BR e EN.

Autor: Kelvin Oliveira — Licença: MIT

---

# backup-gfs-verificacao-hash

GFS backup (grandfather-father-son) with SHA-256 hashing, restore, and byte-by-byte verification, in Python.

IT Support project. The MVP implements the grandfather-father-son cycle (daily / weekly / monthly, simulated in `tmp_dir`), SHA-256 computation, restore, and byte-by-byte verification of a backup against the original.

Acceptance criteria: restore OK, tests passing, complete README in PT-BR and EN.

Author: Kelvin Oliveira — License: MIT

---

## PT-BR

### Como usar

Pré-requisitos: Python 3.10+ e pytest.

Criar um backup de um arquivo:

```
python -m backup_gfs create documento.pdf ./backups --at 2026-10-16T10:00:00Z
```

Criar um backup de um diretório:

```
python -m backup_gfs create ./pasta ./backups --kind monthly --at 2026-10-01T08:00:00Z
```

Rotacionar conforme a retenção GFS:

```
python -m backup_gfs rotate ./backups --daily-keep 7 --weekly-keep 4 --monthly-keep 12
```

Restaurar um backup:

```
python -m backup_gfs restore ./backups/daily-20261016-100000 ./restaurado
```

Verificar integridade byte-a-byte contra o original:

```
python -m backup_gfs verify ./backups/daily-20261016-100000 ./documento.pdf
```

Quando não informado, o tipo (diário / semanal / mensal) é inferido da data: dia 1 = mensal, domingo = semanal, demais dias = diário.

### Testes

```
python -m pytest -q
```

Resultado: 26 testes passando. A suíte cobre SHA-256 de arquivo e árvore, criação de backup, inferência de tipo GFS, rotação por retenção, restauração de arquivo e diretório, verificação byte-a-byte e casos de erro (arquivo ausente, tipo inválido, retenção negativa).

### Licença

MIT

---

## EN

### How to use

Requirements: Python 3.10+ and pytest.

Create a backup of a file:

```
python -m backup_gfs create documento.pdf ./backups --at 2026-10-16T10:00:00Z
```

Create a backup of a directory:

```
python -m backup_gfs create ./pasta ./backups --kind monthly --at 2026-10-01T08:00:00Z
```

Rotate according to GFS retention:

```
python -m backup_gfs rotate ./backups --daily-keep 7 --weekly-keep 4 --monthly-keep 12
```

Restore a backup:

```
python -m backup_gfs restore ./backups/daily-20261016-100000 ./restaurado
```

Verify byte-by-byte integrity against the original:

```
python -m backup_gfs verify ./backups/daily-20261016-100000 ./documento.pdf
```

When not informed, the type (daily / weekly / monthly) is inferred from the date: day 1 = monthly, Sunday = weekly, other days = daily.

### Tests

```
python -m pytest -q
```

Result: 26 tests passing. The suite covers SHA-256 of file and tree, backup creation, GFS type inference, retention-based rotation, file and directory restore, byte-by-byte verification, and error cases (missing file, invalid type, negative retention).

### License

MIT

---

## Estrutura do projeto

```
backup-gfs-verificacao-hash/
├── BRIEF.md
├── README.md
├── pyproject.toml
├── src/backup_gfs/__init__.py
├── src/backup_gfs/gfs.py
├── src/backup_gfs/__main__.py
└── tests/test_gfs.py
```

O PowerShell está disponível no host, mas não foi necessário para o MVP: a CLI em Python cobre criar, rotacionar, restaurar e verificar. A parte PowerShell permanece opcional, conforme o brief.
