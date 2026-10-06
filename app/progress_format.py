from __future__ import annotations


def format_eta(seconds: float | None) -> str:
    if seconds is None:
        return "wird ermittelt"
    value=max(0,int(round(seconds)))
    if value < 60:
        return f"ca. {value} s"
    minutes,sec=divmod(value,60)
    if minutes < 60:
        return f"ca. {minutes} min {sec:02d} s"
    hours,minutes=divmod(minutes,60)
    return f"ca. {hours} h {minutes:02d} min"
