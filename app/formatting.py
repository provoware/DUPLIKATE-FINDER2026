from __future__ import annotations


def format_bytes(size: int) -> str:
    """Formatiert Bytewerte einheitlich und laienlesbar."""
    value = float(max(0, int(size)))
    for unit in ("B", "KB", "MB", "GB", "TB"):
        if value < 1024.0 or unit == "TB":
            return f"{value:.1f} {unit}" if unit != "B" else f"{int(value)} B"
        value /= 1024.0
    return f"{int(size)} B"
