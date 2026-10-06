from pathlib import Path


ROOT=Path(__file__).resolve().parents[1]


def test_settings_and_export_do_not_use_forbidden_replace_api():
    for rel in ("app/settings_store.py","app/state_portability.py"):
        text=(ROOT/rel).read_text(encoding="utf-8")
        assert ".replace(" not in text


def test_acceptance_requires_new_operating_controls():
    text=(ROOT/"tools/autonomous_acceptance.py").read_text(encoding="utf-8")
    for object_name in (
        "process_pause","process_cancel","cpu_limiter","dashboard_export",
        "dashboard_import","excluded_types_button","duplicate_filter_info",
    ):
        assert object_name in text
