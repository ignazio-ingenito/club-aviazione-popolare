"""Atomic manifest writer for controlled run artifacts."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import os
import tempfile

from .jsonl import manifest_jsonl_sha256, render_manifest_jsonl
from .models import InventoryManifest


@dataclass(frozen=True, slots=True)
class ManifestWriteResult:
    manifest_path: Path
    checksum_path: Path
    sha256: str
    byte_count: int


def write_manifest_jsonl(
    manifest: InventoryManifest,
    *,
    output_dir: Path | str,
    filename: str,
    repository_root: Path | str | None = None,
) -> ManifestWriteResult:
    """Write a manifest JSONL and sidecar checksum through temp-file renames."""

    if "/" in filename or "\\" in filename or filename in {"", ".", ".."}:
        raise ValueError("filename must be a plain file name.")
    if not filename.endswith(".jsonl"):
        raise ValueError("filename must end with .jsonl.")

    destination_dir = Path(output_dir)
    if repository_root is not None and _is_relative_to(
        destination_dir.resolve(),
        Path(repository_root).resolve(),
    ):
        raise ValueError("output_dir must be outside the repository.")
    destination_dir.mkdir(mode=0o700, parents=True, exist_ok=True)
    try:
        os.chmod(destination_dir, 0o700)
    except PermissionError:
        pass

    payload = render_manifest_jsonl(manifest)
    sha256 = manifest_jsonl_sha256(manifest)
    manifest_path = destination_dir / filename
    checksum_path = destination_dir / f"{filename}.sha256"
    if manifest_path.exists() or checksum_path.exists():
        raise FileExistsError(
            f"Refusing to overwrite existing run artifact for {filename}."
        )

    _atomic_write(manifest_path, payload)
    _atomic_write(
        checksum_path,
        f"{sha256}  {filename}\n".encode("utf-8"),
    )

    return ManifestWriteResult(
        manifest_path=manifest_path,
        checksum_path=checksum_path,
        sha256=sha256,
        byte_count=len(payload),
    )


def _atomic_write(path: Path, payload: bytes) -> None:
    fd, temp_name = tempfile.mkstemp(
        prefix=f".{path.name}.",
        suffix=".tmp",
        dir=path.parent,
    )
    temp_path = Path(temp_name)
    try:
        with os.fdopen(fd, "wb") as handle:
            handle.write(payload)
            handle.flush()
            os.fsync(handle.fileno())
        os.chmod(temp_path, 0o600)
        os.replace(temp_path, path)
    except Exception:
        try:
            temp_path.unlink()
        except FileNotFoundError:
            pass
        raise


def _is_relative_to(path: Path, parent: Path) -> bool:
    try:
        path.relative_to(parent)
    except ValueError:
        return False
    return True
