"""Interface de linha de comando do backup-gfs-verificacao-hash."""

from __future__ import annotations

import argparse
from datetime import datetime, timezone
from pathlib import Path

from .gfs import (
    DEFAULT_DAILY_KEEP,
    DEFAULT_MONTHLY_KEEP,
    DEFAULT_WEEKLY_KEEP,
    make_backup,
    restore,
    rotate,
    verify,
)


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="backup-gfs",
        description="Backup GFS (avô-pai-filho) com SHA-256 e verificação byte-a-byte.",
    )
    sub = parser.add_subparsers(dest="command", required=True)

    p_create = sub.add_parser("create", help="criar um backup")
    p_create.add_argument("source")
    p_create.add_argument("backup_root")
    p_create.add_argument("--kind", choices=["daily", "weekly", "monthly"], default=None)
    p_create.add_argument("--at", help="data de criação ISO 8601 (UTC)")

    p_rotate = sub.add_parser("rotate", help="rotacionar (retenção GFS)")
    p_rotate.add_argument("backup_root")
    p_rotate.add_argument("--daily-keep", type=int, default=DEFAULT_DAILY_KEEP)
    p_rotate.add_argument("--weekly-keep", type=int, default=DEFAULT_WEEKLY_KEEP)
    p_rotate.add_argument("--monthly-keep", type=int, default=DEFAULT_MONTHLY_KEEP)

    p_restore = sub.add_parser("restore", help="restaurar um backup")
    p_restore.add_argument("backup")
    p_restore.add_argument("destination")

    p_verify = sub.add_parser("verify", help="verificar integridade byte-a-byte")
    p_verify.add_argument("backup")
    p_verify.add_argument("original")

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = _build_parser()
    args = parser.parse_args(argv)

    if args.command == "create":
        created_at: datetime | None = None
        if args.at:
            created_at = datetime.fromisoformat(args.at)
            if created_at.tzinfo is None:
                created_at = created_at.replace(tzinfo=timezone.utc)
        info = make_backup(Path(args.source), Path(args.backup_root), kind=args.kind, created_at=created_at)
        print(f"backup criado: {info.label} ({info.kind}) sha256={info.sha256[:12]}...")
        return 0

    if args.command == "rotate":
        report = rotate(
            Path(args.backup_root),
            daily_keep=args.daily_keep,
            weekly_keep=args.weekly_keep,
            monthly_keep=args.monthly_keep,
        )
        print(f"rotação concluída: {len(report.kept)} mantidos, {len(report.removed)} removidos")
        for path in report.removed:
            print(f"  removido: {path}")
        return 0

    if args.command == "restore":
        restore(Path(args.backup), Path(args.destination))
        print(f"restauração concluída: {args.destination}")
        return 0

    if args.command == "verify":
        result = verify(Path(args.backup), Path(args.original))
        print(result.message)
        print(f"  backup_sha256={result.backup_sha256}")
        print(f"  original_sha256={result.original_sha256}")
        print(f"  byte_equal={result.byte_equal}")
        return 0 if result.ok else 1

    parser.error("comando desconhecido")
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
