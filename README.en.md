# backup-gfs-verificacao-hash

GFS backup (grandfather-father-son) with SHA-256 hashing, restore, and byte-by-byte verification, in Python.

IT Support project. The MVP implements the grandfather-father-son cycle (daily / weekly / monthly, simulated in `tmp_dir`), SHA-256 computation, restore, and byte-by-byte verification of a backup against the original. All state is stored in files on disk; there is no database and no external dependencies.

Acceptance criteria: restore OK, tests passing, complete README in PT-BR and EN.

Author: Kelvin Oliveira — License: MIT

---

## EN

### What the project does

- Creates backups of files and directories in a destination directory.
- Computes SHA-256 of each file and of complete trees, stored in `manifest.sha256` inside each backup.
- Rotates backups according to the GFS retention policy by type (daily, weekly, monthly).
- Restores a backup to a destination, replacing the destination if it already exists.
- Verifies byte-by-byte integrity of a backup against the original by comparing the file set and each file through SHA-256.

### Requirements

- Python 3.10+
- pytest (to run the tests)
- No external dependencies beyond the Python standard library

### How to use

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

### Project structure

```
backup-gfs-verificacao-hash/
├── BRIEF.md
├── README.md
├── README.en.md
├── pyproject.toml
├── src/backup_gfs/__init__.py
├── src/backup_gfs/gfs.py
├── src/backup_gfs/__main__.py
└── tests/test_gfs.py
```

### License

MIT

### Author

Kelvin Oliveira
