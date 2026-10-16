"""Suíte de testes do backup-gfs-verificacao-hash.

Cada teste valida um comportamento real do pacote, sem mocks.
"""

from __future__ import annotations

import hashlib
from datetime import datetime, timezone
from pathlib import Path

import pytest

from backup_gfs import (
    KIND_DAILY,
    KIND_MONTHLY,
    KIND_WEEKLY,
    list_backups,
    make_backup,
    restore,
    rotate,
    sha256_file,
    sha256_tree,
    verify,
)

UTC = timezone.utc

DIARIO_2026 = datetime(2026, 10, 16, 10, 0, 0, tzinfo=UTC)  # sexta-feira
MENSAL_2026 = datetime(2026, 10, 1, 10, 0, 0, tzinfo=UTC)   # dia 1 do mês
SEMANAL_2026 = datetime(2026, 1, 4, 10, 0, 0, tzinfo=UTC)   # domingo


@pytest.fixture
def arquivo_origem(tmp_path: Path) -> Path:
    origem = tmp_path / "origem.txt"
    origem.write_text("conteúdo original para teste de hash\n", encoding="utf-8")
    return origem


@pytest.fixture
def diretorio_origem(tmp_path: Path) -> Path:
    raiz = tmp_path / "origem_dir"
    raiz.mkdir()
    (raiz / "a.txt").write_text("arquivo A\n", encoding="utf-8")
    sub = raiz / "sub"
    sub.mkdir()
    (sub / "b.txt").write_text("arquivo B\n", encoding="utf-8")
    return raiz


def test_sha256_file_corresponde_ao_padrao(arquivo_origem: Path) -> None:
    esperado = hashlib.sha256(arquivo_origem.read_bytes()).hexdigest()
    assert sha256_file(arquivo_origem) == esperado


def test_sha256_file_deterministico(arquivo_origem: Path) -> None:
    primeira = sha256_file(arquivo_origem)
    segunda = sha256_file(arquivo_origem)
    assert primeira == segunda
    assert len(primeira) == 64


def test_sha256_file_conteudo_diferente_produz_hash_diferente(
    arquivo_origem: Path, tmp_path: Path
) -> None:
    outro = tmp_path / "outro.txt"
    outro.write_text("conteúdo diferente\n", encoding="utf-8")
    assert sha256_file(arquivo_origem) != sha256_file(outro)


def test_sha256_file_arquivo_inexistente_levanta_erro(tmp_path: Path) -> None:
    ausente = tmp_path / "nao_existe.txt"
    with pytest.raises(FileNotFoundError):
        sha256_file(ausente)


def test_make_backup_arquivo_cria_diretorio_e_manifesto(
    arquivo_origem: Path, tmp_path: Path
) -> None:
    backup_root = tmp_path / "backups"
    info = make_backup(arquivo_origem, backup_root, created_at=DIARIO_2026)

    assert info.kind == KIND_DAILY
    assert info.path.is_dir()
    assert info.created_at == DIARIO_2026
    assert (info.path / "origem.txt").is_file()
    manifest = info.path / "manifest.sha256"
    assert manifest.is_file()
    linhas = manifest.read_text(encoding="utf-8").splitlines()
    assert linhas[0] == KIND_DAILY
    assert len(info.sha256) == 64


def test_make_backup_diretorio_copia_arvore_completa(
    diretorio_origem: Path, tmp_path: Path
) -> None:
    backup_root = tmp_path / "backups"
    info = make_backup(diretorio_origem, backup_root, created_at=DIARIO_2026)

    assert (info.path / "a.txt").is_file()
    assert (info.path / "sub" / "b.txt").is_file()
    assert (info.path / "manifest.sha256").is_file()
    assert info.size > 0


def test_make_backup_infere_tipo_mensal_no_dia_um(tmp_path: Path) -> None:
    origem = tmp_path / "x.txt"
    origem.write_text("x\n", encoding="utf-8")
    backup_root = tmp_path / "backups"
    info = make_backup(origem, backup_root, created_at=MENSAL_2026)
    assert info.kind == KIND_MONTHLY


def test_make_backup_infere_tipo_semanal_no_domingo(tmp_path: Path) -> None:
    origem = tmp_path / "x.txt"
    origem.write_text("x\n", encoding="utf-8")
    backup_root = tmp_path / "backups"
    info = make_backup(origem, backup_root, created_at=SEMANAL_2026)
    assert info.kind == KIND_WEEKLY


def test_make_backup_infere_tipo_diario_por_padrao(tmp_path: Path) -> None:
    origem = tmp_path / "x.txt"
    origem.write_text("x\n", encoding="utf-8")
    backup_root = tmp_path / "backups"
    info = make_backup(origem, backup_root, created_at=DIARIO_2026)
    assert info.kind == KIND_DAILY


def test_make_backup_created_at_gera_nome_deterministico(
    arquivo_origem: Path, tmp_path: Path
) -> None:
    backup_root = tmp_path / "backups"
    info = make_backup(arquivo_origem, backup_root, created_at=DIARIO_2026)
    assert info.label == f"{KIND_DAILY}-20261016-100000"
    assert info.path == backup_root / info.label


def test_make_backup_tipo_invalido_levanta_erro(arquivo_origem: Path, tmp_path: Path) -> None:
    backup_root = tmp_path / "backups"
    with pytest.raises(ValueError):
        make_backup(arquivo_origem, backup_root, kind="anual")  # type: ignore[arg-type]


def test_make_backup_origem_inexistente_levanta_erro(tmp_path: Path) -> None:
    backup_root = tmp_path / "backups"
    ausente = tmp_path / "nao_existe.txt"
    with pytest.raises(FileNotFoundError):
        make_backup(ausente, backup_root)


def test_list_backups_diretorio_vazio_retorna_lista_vazia(tmp_path: Path) -> None:
    assert list(rotate(tmp_path / "backups").kept) == []
    from backup_gfs import list_backups
    assert list_backups(tmp_path / "backups") == []


def test_list_backups_lista_backups_criados(
    arquivo_origem: Path, tmp_path: Path
) -> None:
    from backup_gfs import BackupInfo

    backup_root = tmp_path / "backups"
    primeiro = make_backup(arquivo_origem, backup_root, created_at=DIARIO_2026)
    segundo = make_backup(arquivo_origem, backup_root, created_at=MENSAL_2026)

    listados = list_backups(backup_root)
    rotulos = {item.label for item in listados}
    assert primeiro.label in rotulos
    assert segundo.label in rotulos
    assert all(isinstance(item, BackupInfo) for item in listados)


def test_rotate_mantem_n_mais_recentes_de_cada_tipo(tmp_path: Path) -> None:
    from backup_gfs import list_backups

    backup_root = tmp_path / "backups"
    # 5 diários, 2 semanais, 3 mensais com datas crescentes
    bases = [
        (KIND_DAILY, datetime(2026, 10, 10, 10, 0, 0, tzinfo=UTC)),
        (KIND_DAILY, datetime(2026, 10, 11, 10, 0, 0, tzinfo=UTC)),
        (KIND_DAILY, datetime(2026, 10, 12, 10, 0, 0, tzinfo=UTC)),
        (KIND_DAILY, datetime(2026, 10, 13, 10, 0, 0, tzinfo=UTC)),
        (KIND_DAILY, datetime(2026, 10, 14, 10, 0, 0, tzinfo=UTC)),
        (KIND_WEEKLY, datetime(2026, 1, 4, 10, 0, 0, tzinfo=UTC)),
        (KIND_WEEKLY, datetime(2026, 1, 11, 10, 0, 0, tzinfo=UTC)),
        (KIND_MONTHLY, datetime(2026, 9, 1, 10, 0, 0, tzinfo=UTC)),
        (KIND_MONTHLY, datetime(2026, 10, 1, 10, 0, 0, tzinfo=UTC)),
        (KIND_MONTHLY, datetime(2026, 11, 1, 10, 0, 0, tzinfo=UTC)),
    ]
    origem = tmp_path / "origem.txt"
    origem.write_text("dados\n", encoding="utf-8")
    for kind, quando in bases:
        make_backup(origem, backup_root, kind=kind, created_at=quando)

    # manter 2 diários, 1 semanal, 2 mensais
    relatorio = rotate(backup_root, daily_keep=2, weekly_keep=1, monthly_keep=2)

    mantidos_por_tipo: dict[str, int] = {}
    for item in relatorio.kept:
        mantidos_por_tipo[item.kind] = mantidos_por_tipo.get(item.kind, 0) + 1
    assert mantidos_por_tipo == {KIND_DAILY: 2, KIND_WEEKLY: 1, KIND_MONTHLY: 2}
    assert len(relatorio.removed) == 10 - 5
    # os mais recentes de cada tipo devem estar entre os mantidos
    ultimos_diarios = {item.label for item in list_backups(backup_root) if item.kind == KIND_DAILY}
    assert len(ultimos_diarios) == 2


def test_rotate_limite_negativo_levanta_erro(tmp_path: Path) -> None:
    backup_root = tmp_path / "backups"
    backup_root.mkdir()
    with pytest.raises(ValueError):
        rotate(backup_root, daily_keep=-1)


def test_restore_restaura_arquivo_identico(
    arquivo_origem: Path, tmp_path: Path
) -> None:
    backup_root = tmp_path / "backups"
    info = make_backup(arquivo_origem, backup_root, created_at=DIARIO_2026)
    destino = tmp_path / "restaurado.txt"
    restaurado = restore(info.path, destino)

    assert restaurado == destino
    assert destino.read_text(encoding="utf-8") == arquivo_origem.read_text(encoding="utf-8")
    assert sha256_file(destino) == sha256_file(arquivo_origem)


def test_restore_restaura_diretorio_identico(
    diretorio_origem: Path, tmp_path: Path
) -> None:
    backup_root = tmp_path / "backups"
    info = make_backup(diretorio_origem, backup_root, created_at=DIARIO_2026)
    destino = tmp_path / "restaurado_dir"
    restaurado = restore(info.path, destino)

    assert (restaurado / "a.txt").is_file()
    assert (restaurado / "sub" / "b.txt").is_file()
    assert (restaurado / "a.txt").read_text(encoding="utf-8") == (
        diretorio_origem / "a.txt"
    ).read_text(encoding="utf-8")


def test_restore_substituir_destino_existente(
    arquivo_origem: Path, tmp_path: Path
) -> None:
    backup_root = tmp_path / "backups"
    info = make_backup(arquivo_origem, backup_root, created_at=DIARIO_2026)
    destino = tmp_path / "restaurado.txt"
    destino.write_text("conteúdo antigo que será sobrescrito\n", encoding="utf-8")

    restore(info.path, destino)
    assert destino.read_text(encoding="utf-8") == arquivo_origem.read_text(encoding="utf-8")


def test_verify_backup_idêntico_ao_original_retorna_ok(
    arquivo_origem: Path, tmp_path: Path
) -> None:
    backup_root = tmp_path / "backups"
    info = make_backup(arquivo_origem, backup_root, created_at=DIARIO_2026)
    resultado = verify(info.path, arquivo_origem)

    assert resultado.ok is True
    assert resultado.byte_equal is True
    assert resultado.backup_sha256 == resultado.original_sha256
    assert "confirmada" in resultado.message


def test_verify_conteudo_alterado_falha_byte_a_byte(
    arquivo_origem: Path, tmp_path: Path
) -> None:
    backup_root = tmp_path / "backups"
    info = make_backup(arquivo_origem, backup_root, created_at=DIARIO_2026)
    # altera o backup depois de criado
    (info.path / "origem.txt").write_text("conteúdo alterado\n", encoding="utf-8")

    resultado = verify(info.path, arquivo_origem)
    assert resultado.ok is False
    assert resultado.byte_equal is False
    assert resultado.backup_sha256 != resultado.original_sha256


def test_verify_conjunto_de_arquivos_diferente_falha(
    diretorio_origem: Path, tmp_path: Path
) -> None:
    backup_root = tmp_path / "backups"
    info = make_backup(diretorio_origem, backup_root, created_at=DIARIO_2026)
    # remove um arquivo do backup
    (info.path / "a.txt").unlink()

    resultado = verify(info.path, diretorio_origem)
    assert resultado.ok is False
    assert resultado.byte_equal is False


def test_verify_backup_inexistente_levanta_erro(
    arquivo_origem: Path, tmp_path: Path
) -> None:
    with pytest.raises(FileNotFoundError):
        verify(tmp_path / "nao_existe", arquivo_origem)


def test_verify_original_inexistente_levanta_erro(
    arquivo_origem: Path, tmp_path: Path
) -> None:
    backup_root = tmp_path / "backups"
    info = make_backup(arquivo_origem, backup_root, created_at=DIARIO_2026)
    with pytest.raises(FileNotFoundError):
        verify(info.path, tmp_path / "nao_existe")


def test_sha256_tree_exclui_manifesto(
    diretorio_origem: Path, tmp_path: Path
) -> None:
    backup_root = tmp_path / "backups"
    info = make_backup(diretorio_origem, backup_root, created_at=DIARIO_2026)
    hashes = sha256_tree(info.path, exclude={"manifest.sha256"})
    assert "a.txt" in hashes
    assert "sub/b.txt" in hashes
    assert "manifest.sha256" not in hashes


def test_fluxo_completo_restauracao_e_verificacao_passam(
    diretorio_origem: Path, tmp_path: Path
) -> None:
    """Aceitação: criar, rotacionar, restaurar e verificar byte-a-byte."""
    backup_root = tmp_path / "backups"
    info = make_backup(diretorio_origem, backup_root, created_at=DIARIO_2026)

    rotacao = rotate(backup_root, daily_keep=1, weekly_keep=1, monthly_keep=1)
    assert len(rotacao.kept) >= 1

    destino = tmp_path / "restaurado"
    restaurado = restore(info.path, destino)

    resultado = verify(restaurado, diretorio_origem)
    assert resultado.ok is True
    assert resultado.byte_equal is True
