"""Filesystem indexing and previews for CSV/TXT/MD files."""

from __future__ import annotations

from datetime import datetime
from pathlib import Path
from typing import Any

import pandas as pd

SUPPORTED_EXTENSIONS = {".csv", ".txt", ".md"}


def _matches_size(size_bytes: int, size_range: tuple[int | None, int | None] | None) -> bool:
    if not size_range:
        return True
    min_size, max_size = size_range
    if min_size is not None and size_bytes < min_size:
        return False
    if max_size is not None and size_bytes > max_size:
        return False
    return True


def _matches_modified(
    modified_at: datetime,
    modified_range: tuple[datetime | None, datetime | None] | None,
) -> bool:
    if not modified_range:
        return True
    min_modified, max_modified = modified_range
    if min_modified is not None and modified_at < min_modified:
        return False
    if max_modified is not None and modified_at > max_modified:
        return False
    return True


def list_supported_files(
    root_path: str,
    recursive: bool = True,
    search: str | None = None,
    file_types: list[str] | None = None,
    size_range: tuple[int | None, int | None] | None = None,
    modified_range: tuple[datetime | None, datetime | None] | None = None,
) -> list[dict[str, Any]]:
    """Return filtered metadata for supported files."""
    if not str(root_path or "").strip():
        return []

    root = Path(root_path).expanduser()
    if not root.exists() or not root.is_dir():
        return []

    requested_types = {ext.lower() for ext in (file_types or list(SUPPORTED_EXTENSIONS))}
    normalized_search = (search or "").strip().lower()
    iterator = root.rglob("*") if recursive else root.glob("*")

    result: list[dict[str, Any]] = []
    for path in iterator:
        if not path.is_file():
            continue
        ext = path.suffix.lower()
        if ext not in SUPPORTED_EXTENSIONS or ext not in requested_types:
            continue

        stat = path.stat()
        modified_at = datetime.fromtimestamp(stat.st_mtime)
        if normalized_search and normalized_search not in path.name.lower():
            continue
        if not _matches_size(stat.st_size, size_range):
            continue
        if not _matches_modified(modified_at, modified_range):
            continue

        result.append(
            {
                "path": str(path),
                "name": path.name,
                "extension": ext,
                "size_bytes": stat.st_size,
                "modified_at": modified_at,
            }
        )

    result.sort(key=lambda item: item["modified_at"], reverse=True)
    return result


def _read_csv_preview(file_path: str, max_rows: int) -> pd.DataFrame:
    try:
        return pd.read_csv(file_path, nrows=max_rows)
    except Exception:
        return pd.read_csv(file_path, nrows=max_rows, sep=None, engine="python")


def read_preview(file_path: str, max_rows: int = 20, max_chars: int = 5000) -> dict[str, Any]:
    """Read safe preview for UI."""
    path = Path(file_path)
    ext = path.suffix.lower()
    if ext == ".csv":
        preview_df = _read_csv_preview(file_path, max_rows=max_rows)
        return {"kind": "csv", "preview": preview_df}

    text = path.read_text(encoding="utf-8", errors="ignore")
    return {"kind": "text", "preview": text[:max_chars]}
