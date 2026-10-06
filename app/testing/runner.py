from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from app.core.duplicates import scan_duplicate_groups_to_database
from app.core.search_pipeline import run_search_to_database
from app.models.entities import SearchJob
from app.storage.database import Database
from app.testing.profiles import PROFILES, QUERY, Expected, materialize_profile
from app.testing.sandbox import TestSandbox


@dataclass(frozen=True)
class TestLabResult:
    profile: str
    ok: bool
    expected: Expected
    files: int
    search_hits: int
    duplicate_groups: int
    duplicate_files: int
    errors: int
    detail: str


def run_profile(
    profile_name: str,
    *,
    sandbox_parent: Path | None = None,
) -> TestLabResult:
    if profile_name not in PROFILES:
        raise ValueError(
            f"Unbekanntes Testprofil: {profile_name}. "
            f"Verfügbar: {', '.join(PROFILES)}"
        )
    profile = PROFILES[profile_name]

    with TestSandbox.create(sandbox_parent) as sandbox:
        materialize_profile(profile, sandbox.files_dir)
        database = Database(sandbox.state_dir / "testlab.sqlite3")
        database.initialize()

        search = run_search_to_database(
            SearchJob(
                root=sandbox.files_dir,
                query=QUERY,
                search_names=False,
                search_contents=True,
            ),
            database,
            run_kind=f"testlab-{profile.name}",
        )
        scanned, group_count, duplicate_errors = scan_duplicate_groups_to_database(
            sandbox.files_dir,
            database,
        )
        summaries = database.duplicate_group_summaries()
        duplicate_files = sum(members for _gid, _digest, _size, members in summaries)
        errors = search.error_count + duplicate_errors

        expected = profile.expected
        ok = (
            scanned == expected.files
            and search.hit_count == expected.search_hits
            and group_count == expected.duplicate_groups
            and duplicate_files == expected.duplicate_files
            and errors == expected.errors
        )
        detail = (
            f"Dateien {scanned}/{expected.files} · "
            f"Treffer {search.hit_count}/{expected.search_hits} · "
            f"Gruppen {group_count}/{expected.duplicate_groups} · "
            f"Duplikatdateien {duplicate_files}/{expected.duplicate_files} · "
            f"Fehler {errors}/{expected.errors}"
        )
        return TestLabResult(
            profile=profile.name,
            ok=ok,
            expected=expected,
            files=scanned,
            search_hits=search.hit_count,
            duplicate_groups=group_count,
            duplicate_files=duplicate_files,
            errors=errors,
            detail=detail,
        )
