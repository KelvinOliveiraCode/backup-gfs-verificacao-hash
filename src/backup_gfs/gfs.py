"""Backup GFS (avô-pai-filho) com SHA-256, restauração e verificação byte-a-byte.

Rotaciona backups simulados (diário / semanal / mensal) num diretório de
destino, calcula SHA-256 de cada árvore de arquivos, restaura um backup e
verifica integridade byte-a-byte contra o original. Todo o estado fica em
arquivos no disco; não há banco de dados nem dependências externas.
"""

from __future__ import annotations

import hashlib
import shutil
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Final

KIND_DAILY: Final = "daily"
KIND_WEEKLY: Final = "weekly"
KIND_MONTHLY: Final = "monthly"

KINDS: Final[tuple[str, ...]] = (KIND_DAILY, KIND_WEEKLY, KIND_MONTHLY)

DEFAULT_DAILY_KEEP: Final = 7
DEFAULT_WEEKLY_KEEP: Final = 4
DEFAULT_MONTHLY_KEEP: Final = 12

CHUNK_SIZE: Final = 1024 * 1024  # 1 MiB

MANIFEST_NAME: Final = "manifest.sha256"


@dataclass(frozen=True)
class BackupInfo:
    """Metadados de um backup já existente no disco."""

    path: Path
    label: str
    kind: str
    created_at: datetime
    sha256: str
    size: int


@dataclass(frozen=True)
class RotateReport:
    """Resultado de uma rotação GFS."""

    removed: list[Path]
    kept: list[BackupInfo]


@dataclass(frozen=True)
class VerifyResult:
    """Resultado da verificação de integridade de um backup."""

    ok: bool
    backup_sha256: str
    original_sha256: str
    byte_equal: bool
    message: str


def sha256_file(path: Path) -> str:
    """Retorna o hash SHA-256 de um arquivo."""
    if not path.is_file():
        raise FileNotFoundError(f"arquivo não encontrado: {path}")
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(CHUNK_SIZE), b""):
            digest.update(block)
    return digest.hexdigest()


def _relative_files(root: Path) -> list[str]:
    """Caminhos relativos (POSIX) dos arquivos de ``root``, em ordem estável."""
    return sorted(
        file.relative_to(root).as_posix()
        for file in root.rglob("*")
        if file.is_file()
    )


def sha256_tree(root: Path, *, exclude: set[str] | None = None) -> dict[str, str]:
    """SHA-256 de cada arquivo de uma árvore, chaveado pelo caminho relativo.

    Quando ``root`` é um único arquivo, retorna uma entrada com seu próprio nome.
    """
    if not root.exists():
        raise FileNotFoundError(f"caminho não encontrado: {root}")
    skipped = exclude or set()
    hashes: dict[str, str] = {}
    if root.is_file():
        chave = root.name
        if chave not in skipped:
            hashes[chave] = sha256_file(root)
        return hashes
    for relative in _relative_files(root):
        if relative in skipped:
            continue
        hashes[relative] = sha256_file(root / relative)
    return hashes


def _classify_kind(created_at: datetime) -> str:
    """Inferir o tipo GFS de uma data: dia 1 = mensal, domingo = semanal."""
    if created_at.day == 1:
        return KIND_MONTHLY
    if created_at.weekday() == 6:  # domingo
        return KIND_WEEKLY
    return KIND_DAILY


def _label(created_at: datetime, kind: str) -> str:
    return f"{kind}-{created_at.strftime('%Y%m%d-%H%M%S')}"


def _parse_timestamp(text: str) -> datetime:
    return datetime.fromisoformat(text)


def _sort_newest_first(items: list[BackupInfo]) -> list[BackupInfo]:
    return sorted(items, key=lambda item: item.created_at, reverse=True)


def list_backups(backup_root: Path) -> list[BackupInfo]:
    """Listar os backups válidos presentes em ``backup_root``."""
    if not backup_root.exists():
        return []
    infos: list[BackupInfo] = []
    for child in sorted(backup_root.iterdir()):
        if not child.is_dir():
            continue
        manifest = child / MANIFEST_NAME
        if not manifest.is_file():
            continue
        lines = manifest.read_text(encoding="utf-8").splitlines()
        kind = lines[0].strip() if len(lines) > 0 else KIND_DAILY
        created_at = (
            _parse_timestamp(lines[1].strip())
            if len(lines) > 1
            else datetime.min.replace(tzinfo=timezone.utc)
        )
        sha256 = lines[2].strip() if len(lines) > 2 else ""
        size = sum(f.stat().st_size for f in child.rglob("*") if f.is_file())
        infos.append(
            BackupInfo(
                path=child,
                label=child.name,
                kind=kind,
                created_at=created_at,
                sha256=sha256,
                size=size,
            )
        )
    return infos


def make_backup(
    source: Path,
    backup_root: Path,
    *,
    kind: str | None = None,
    created_at: datetime | None = None,
) -> BackupInfo:
    """Criar um backup de ``source`` em ``backup_root``.

    Parâmetros
    ----------
    source:
        Arquivo ou diretório a copiar.
    backup_root:
        Diretório raiz onde os backups são armazenados.
    kind:
        ``daily``, ``weekly`` ou ``monthly``. Quando omitido, infere da data
        de criação (regra GFS: dia 1 = mensal, domingo = semanal).
    created_at:
        Data de criação (UTC). Padrão: ``datetime.now(timezone.utc)``.
        Expor esse parâmetro torna a rotação determinística em testes.
    """
    if not source.exists():
        raise FileNotFoundError(f"origem não encontrada: {source}")
    now = created_at or datetime.now(timezone.utc)
    resolved_kind = kind or _classify_kind(now)
    if resolved_kind not in KINDS:
        raise ValueError(
            f"tipo inválido: {resolved_kind!r}. Esperado um de {KINDS}."
        )

    backup_root.mkdir(parents=True, exist_ok=True)
    label = _label(now, resolved_kind)
    backup_path = backup_root / label
    if backup_path.exists():
        shutil.rmtree(backup_path)

    if source.is_dir():
        shutil.copytree(source, backup_path, symlinks=True)
    else:
        backup_path.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, backup_path / source.name)

    tree_hashes = sha256_tree(backup_path, exclude={MANIFEST_NAME})
    combined = "".join(f"{relative} {hash_}\n" for relative, hash_ in sorted(tree_hashes.items()))
    backup_sha256 = hashlib.sha256(combined.encode("utf-8")).hexdigest()

    manifest = backup_path / MANIFEST_NAME
    manifest.write_text(
        f"{resolved_kind}\n{now.isoformat()}\n{backup_sha256}\n",
        encoding="utf-8",
    )

    size = sum(f.stat().st_size for f in backup_path.rglob("*") if f.is_file())
    return BackupInfo(
        path=backup_path,
        label=label,
        kind=resolved_kind,
        created_at=now,
        sha256=backup_sha256,
        size=size,
    )


def rotate(
    backup_root: Path,
    *,
    daily_keep: int = DEFAULT_DAILY_KEEP,
    weekly_keep: int = DEFAULT_WEEKLY_KEEP,
    monthly_keep: int = DEFAULT_MONTHLY_KEEP,
    now: datetime | None = None,
) -> RotateReport:
    """Aplicar a política de retenção GFS e remover os backups excedentes.

    Mantém os ``daily_keep`` mais recentes de cada tipo, os
    ``weekly_keep`` semanais e os ``monthly_keep`` mensais, avaliados
    independentemente por tipo (política simulada por tipo).
    """
    if daily_keep < 0 or weekly_keep < 0 or monthly_keep < 0:
        raise ValueError("os limites de retenção devem ser não negativos")
    if not backup_root.exists():
        return RotateReport(removed=[], kept=[])

    by_kind: dict[str, list[BackupInfo]] = {kind: [] for kind in KINDS}
    for info in list_backups(backup_root):
        by_kind.setdefault(info.kind, []).append(info)

    removed: list[Path] = []
    kept: list[BackupInfo] = []
    limits = {
        KIND_DAILY: daily_keep,
        KIND_WEEKLY: weekly_keep,
        KIND_MONTHLY: monthly_keep,
    }
    for kind in KINDS:
        ordered = _sort_newest_first(by_kind.get(kind, []))
        limit = limits[kind]
        for index, info in enumerate(ordered):
            if index < limit:
                kept.append(info)
            else:
                removed.append(info.path)
                shutil.rmtree(info.path)
    return RotateReport(removed=removed, kept=kept)


def restore(backup: Path, destination: Path) -> Path:
    """Restaurar o conteúdo de ``backup`` em ``destination``.

    Se ``destination`` já existir, é substituído. Retorna o caminho restaurado.
    """
    if not backup.exists():
        raise FileNotFoundError(f"backup não encontrado: {backup}")
    if destination.exists():
        if destination.is_dir():
            shutil.rmtree(destination)
        else:
            destination.unlink()
    destination.parent.mkdir(parents=True, exist_ok=True)

    conteudo = [
        relativo
        for relativo in _relative_files(backup)
        if relativo != MANIFEST_NAME
    ]
    if backup.is_file():
        shutil.copy2(backup, destination)
    elif len(conteudo) == 1 and "/" not in conteudo[0]:
        # backup de um único arquivo: restaura esse arquivo no destino
        shutil.copy2(backup / conteudo[0], destination)
    else:
        shutil.copytree(
            backup,
            destination,
            symlinks=True,
            ignore=shutil.ignore_patterns(MANIFEST_NAME),
        )
    return destination


def _tree_combined_sha256(root: Path) -> str:
    tree_hashes = sha256_tree(root, exclude={MANIFEST_NAME})
    combined = "".join(f"{relative} {hash_}\n" for relative, hash_ in sorted(tree_hashes.items()))
    return hashlib.sha256(combined.encode("utf-8")).hexdigest()


def verify(backup: Path, original: Path) -> VerifyResult:
    """Verificar integridade byte-a-byte de ``backup`` contra ``original``.

    Compara primeiro o conjunto de arquivos e depois cada arquivo byte a byte
    (através dos hashes SHA-256), além do hash agregado das árvores.
    """
    if not backup.exists():
        raise FileNotFoundError(f"backup não encontrado: {backup}")
    if not original.exists():
        raise FileNotFoundError(f"original não encontrado: {original}")

    backup_hashes = sha256_tree(backup, exclude={MANIFEST_NAME})
    original_hashes = sha256_tree(original, exclude={MANIFEST_NAME})

    backup_sha256 = _tree_combined_sha256(backup)
    original_sha256 = _tree_combined_sha256(original)

    same_files = set(backup_hashes) == set(original_hashes)
    byte_equal = same_files and all(
        backup_hashes[relative] == original_hashes[relative] for relative in backup_hashes
    )
    ok = byte_equal and backup_sha256 == original_sha256

    if ok:
        message = "integridade confirmada: backup idêntico ao original"
    elif not same_files:
        message = "falha: conjunto de arquivos difere entre backup e original"
    elif not byte_equal:
        message = "falha: conteúdo byte-a-byte difere entre backup e original"
    else:
        message = "falha: hashes SHA-256 divergem"

    return VerifyResult(
        ok=ok,
        backup_sha256=backup_sha256,
        original_sha256=original_sha256,
        byte_equal=byte_equal,
        message=message,
    )
