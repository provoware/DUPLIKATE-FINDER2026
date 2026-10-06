from __future__ import annotations

import json
import logging
import sys
from logging.handlers import RotatingFileHandler
from pathlib import Path
from types import TracebackType


def configure_logging(base_dir: Path) -> Path:
    log_dir = base_dir / "logs"
    log_dir.mkdir(parents=True, exist_ok=True)
    log_file = log_dir / "provoware.log"
    root = logging.getLogger()
    root.setLevel(logging.INFO)
    if not any(isinstance(handler, RotatingFileHandler) for handler in root.handlers):
        handler = RotatingFileHandler(log_file, maxBytes=2_000_000, backupCount=5, encoding="utf-8")
        handler.setFormatter(logging.Formatter("%(asctime)s | %(levelname)s | %(name)s | %(message)s"))
        root.addHandler(handler)
    logging.getLogger(__name__).info("Logging gestartet")
    return log_file


def install_exception_hook(log_file: Path) -> None:
    old_hook = sys.excepthook

    def hook(exc_type: type[BaseException], exc: BaseException, tb: TracebackType | None) -> None:
        logging.getLogger("provoware.unhandled").critical("Unbehandelter Fehler", exc_info=(exc_type, exc, tb))
        try:
            (log_file.parent / "letzter_fehler.json").write_text(
                json.dumps({"typ": exc_type.__name__, "meldung": str(exc), "protokoll": str(log_file)}, ensure_ascii=False, indent=2),
                encoding="utf-8",
            )
        except OSError:
            pass
        old_hook(exc_type, exc, tb)

    sys.excepthook = hook
