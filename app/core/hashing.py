from __future__ import annotations

import hashlib
from pathlib import Path

from app.core.control import ProcessControl


def sha256_file(
    path: Path,
    chunk_size: int = 1024 * 1024,
    *,
    control: ProcessControl | None = None,
) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        while True:
            if control is not None:
                control.checkpoint()
            chunk = handle.read(chunk_size)
            if not chunk:
                break
            digest.update(chunk)
    return digest.hexdigest()
