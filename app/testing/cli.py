from __future__ import annotations

import argparse
from pathlib import Path

from app.testing.fault_injection import run_fault_injection_suite
from app.testing.performance import run_performance_profile
from app.testing.performance_report import write_performance_report
from app.testing.profiles import available_profiles
from app.testing.runner import run_profile
from app.testing.disturbances import run_disturbance_suite


def configure_testlab_arguments(parser: argparse.ArgumentParser) -> None:
    parser.add_argument(
        "--testlab",
        choices=available_profiles(),
        help="Automatisches Dateisystem-Testprofil ausführen.",
    )
    parser.add_argument(
        "--testlab-performance",
        type=int,
        metavar="DATEIEN",
        help="Expliziten Leistungstest mit der angegebenen Dateianzahl ausführen.",
    )
    parser.add_argument(
        "--testlab-disturbances",
        action="store_true",
        help="Störungstests für Dateiänderung, Abbruch und Pause/Fortsetzen ausführen.",
    )
    parser.add_argument(
        "--testlab-faults",
        action="store_true",
        help="Fehler-Injektion für SQLite, vollen Datenträger und Schreibrechte ausführen.",
    )
    parser.add_argument(
        "--testlab-performance-report",
        type=int,
        metavar="DATEIEN",
        help="Leistungstest ausführen und JSON-/HTML-Bericht erzeugen.",
    )
    parser.add_argument(
        "--testlab-baseline",
        type=Path,
        metavar="JSON",
        help="Früheren JSON-Leistungsbericht als Vergleichsbasis verwenden.",
    )


def run_requested_testlab(args: argparse.Namespace, base: Path) -> int | None:
    if args.testlab:
        result = run_profile(args.testlab)
        print(
            ("OK" if result.ok else "FEHLER"),
            f"Testlabor {result.profile}",
            result.detail,
        )
        return 0 if result.ok else 1

    if args.testlab_performance is not None:
        result = run_performance_profile(file_count=args.testlab_performance)
        print(
            ("OK" if result.ok else "FEHLER"),
            "Leistungstest",
            result.detail,
        )
        return 0 if result.ok else 1

    if args.testlab_disturbances:
        result = run_disturbance_suite()
        print(
            ("OK" if result.ok else "FEHLER"),
            "Störungstest",
            result.detail,
        )
        return 0 if result.ok else 1

    if args.testlab_faults:
        result = run_fault_injection_suite()
        print(
            ("OK" if result.ok else "FEHLER"),
            "Fehler-Injektion",
            result.detail,
        )
        return 0 if result.ok else 1

    if args.testlab_performance_report is not None:
        result = run_performance_profile(
            file_count=args.testlab_performance_report
        )
        try:
            json_path, html_path, snapshot = write_performance_report(
                result,
                base / "reports",
                baseline_path=args.testlab_baseline,
            )
        except (OSError, ValueError) as exc:
            print("FEHLER", "Leistungsbericht", exc)
            return 1

        print(
            ("OK" if result.ok else "FEHLER"),
            "Leistungsbericht",
            result.detail,
        )
        print("JSON", json_path)
        print("HTML", html_path)
        comparison = snapshot.comparison
        if comparison is not None:
            rate = (
                f"{comparison.rate_change_percent:+.1f} %"
                if comparison.rate_change_percent is not None
                else "–"
            )
            print(
                "Vergleich",
                f"Dateien/s {rate}",
                f"RAM {comparison.peak_rss_change_mib:+.1f} MiB",
            )
        return 0 if result.ok else 1

    return None
