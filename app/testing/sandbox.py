from __future__ import annotations

import tempfile
from dataclasses import dataclass, field
from pathlib import Path


MARKER = ".PROVOWARE_TEST_SANDBOX"


@dataclass
class TestSandbox:
    __test__ = False

    root: Path
    _temporary: tempfile.TemporaryDirectory = field(repr=False)

    @classmethod
    def create(cls, parent: Path | None = None) -> "TestSandbox":
        if parent is not None:
            parent.mkdir(parents=True, exist_ok=True)
        temporary = tempfile.TemporaryDirectory(
            prefix="provoware-testlab-",
            dir=str(parent) if parent is not None else None,
        )
        root = Path(temporary.name)
        (root / MARKER).write_text("PROVOWARE test sandbox\n", encoding="utf-8")
        (root / "files").mkdir()
        (root / "state").mkdir()
        return cls(root, temporary)

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
        self._temporary.cleanup()

    def __enter__(self) -> "TestSandbox":
        return self

    def __exit__(self, exc_type, exc, tb) -> None:
        self.cleanup()
