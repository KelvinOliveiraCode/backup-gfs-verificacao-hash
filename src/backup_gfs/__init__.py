"""Backup GFS (avô-pai-filho) com SHA-256, restauração e verificação byte-a-byte."""

from .gfs import (
    KIND_DAILY,
    KIND_MONTHLY,
    KIND_WEEKLY,
    KINDS,
    BackupInfo,
    RotateReport,
    VerifyResult,
    list_backups,
    make_backup,
    restore,
    rotate,
    sha256_file,
    sha256_tree,
    verify,
)

__all__ = [
    "KINDS",
    "KIND_DAILY",
    "KIND_MONTHLY",
    "KIND_WEEKLY",
    "BackupInfo",
    "RotateReport",
    "VerifyResult",
    "list_backups",
    "make_backup",
    "restore",
    "rotate",
    "sha256_file",
    "sha256_tree",
    "verify",
]
