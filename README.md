# backup-gfs-verificacao-hash

Backup GFS (avô-pai-filho) com hash SHA-256, restauração e verificação byte-a-byte, em Python.

Projeto da área Suporte TI. O MVP implementa o ciclo avô-pai-filho (diário / semanal / mensal, simulado em `tmp_dir`), o cálculo de SHA-256, a restauração e a verificação byte-a-byte de um backup contra o original. Todo o estado fica em arquivos no disco; não há banco de dados nem dependências externas.

Critérios de aceitação: restauração OK, testes passando, README completa em PT-BR e EN.

Autor: Kelvin Oliveira — Licença: MIT

---

## PT-BR

### O que o projeto faz

- Cria backups de arquivos e diretórios em um diretório de destino.
- Calcula SHA-256 de cada arquivo e de árvores completas, armazenado em `manifest.sha256` dentro de cada backup.
- Rotaciona backups segundo a política GFS com retenção por tipo (diário, semanal, mensal).
- Restaura um backup para um destino, substituindo o destino se já existir.
- Verifica integridade byte-a-byte de um backup contra o original comparando o conjunto de arquivos e cada arquivo via SHA-256.

### Requisitos

- Python 3.10+
- pytest (para executar os testes)
- Nenhuma dependência externa além da biblioteca padrão do Python

### Como usar

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

### Estrutura do projeto

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

### Licença

MIT

### Autor

Kelvin Oliveira
