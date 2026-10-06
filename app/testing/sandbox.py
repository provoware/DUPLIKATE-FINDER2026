from __future__ import annotations

import shutil
import tempfile
from dataclasses import dataclass
from pathlib import Path


MARKER = ".PROVOWARE_TEST_SANDBOX"


@dataclass
class TestSandbox:
    root: Path

    @classmethod
    def create(cls, parent: Path | None = None) -> "TestSandbox":
        if parent is None:
            root = Path(tempfile.mkdtemp(prefix="provoware-testlab-"))
        else:
            parent.mkdir(parents=True, exist_ok=True)
            root = Path(tempfile.mkdtemp(prefix="provoware-testlab-", dir=parent))
        (root / MARKER).write_text("PROVOWARE test sandbox\n", encoding="utf-8")
        (root / "files").mkdir()
        (root / "state").mkdir()
        return cls(root)

    @property
    def files_dir(self) -> Path:
        return self.root / "files"

    @property
    def state_dir(self) -> Path:
        return self.root / "state"

    def cleanup(self) -> None:
        marker = self.root / MARKER
        if not marker.is_file():
            raise RuntimeError(
                f"Sicherheitsabbruch: Test-Markierung fehlt in {self.root}"
            )
        shutil.rmtree(self.root)

    def __enter__(self) -> "TestSandbox":
        return self

    def __exit__(self, exc_type, exc, tb) -> None:
        self.cleanup()
