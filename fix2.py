"""Follow-up fixes for the migration: flatten double-nested dirs, move settings,
remove dead placeholder, rewrite remaining import prefixes."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent

MOVES = [
    ("src/infrastructures/infrastructure/external", "src/infrastructures/external"),
    ("src/infrastructures/infrastructure/files", "src/infrastructures/database"),
    ("src/infrastructures/infrastructure/models", "src/infrastructures/database/models"),
    ("src/infrastructures/infrastructure/observability", "src/infrastructures/observability"),
    ("src/infrastructures/infrastructure/security", "src/infrastructures/security"),
    ("src/infrastructures/infrastructure/web", "src/presentation/http/web"),
    ("src/infrastructures/infrastructure/__init__.py", "src/infrastructures/__init__.py"),
    ("src/infrastructures/di_containers/settings_model.py", "src/config/settings.py"),
]

DELETES = [
    "src/backend/__init__.py",
    "src/presentation/http/mentor_routes.py",  # dead placeholder endpoint
]

IMPORT_RULES = [
    ("src.infrastructures", "src.infrastructures"),
    ("src.infrastructures.database", "src.infrastructures.database"),
    ("src.infrastructures.database.models", "src.infrastructures.database.models"),
    ("src.presentation.http.web", "src.presentation.http.web"),
]

NEW_INITS = [
    "src/application/__init__.py",
    "src/application/interfaces/__init__.py",
    "src/config/__init__.py",
    "src/presentation/__init__.py",
]


def git(*args: str) -> None:
    subprocess.run(["git", *args], check=True, cwd=ROOT, capture_output=True, text=True)


def main() -> int:
    for old, new in MOVES:
        src = ROOT / old
        if not src.exists():
            print(f"skip missing: {old}")
            continue
        (ROOT / new).parent.mkdir(parents=True, exist_ok=True)
        git("mv", old, new)
        print(f"moved: {old} -> {new}")

    for path in DELETES:
        p = ROOT / path
        if p.exists():
            git("rm", "-q", path)
            print(f"deleted: {path}")

    for rel in NEW_INITS:
        p = ROOT / rel
        if not p.exists():
            p.write_text("", encoding="utf-8", newline="\n")
            print(f"created: {rel}")

    for py in ROOT.rglob("*.py"):
        parts = py.parts
        if ".venv" in parts or "__pycache__" in parts or ".git" in parts:
            continue
        text = py.read_text(encoding="utf-8")
        new_text = text
        for old, new in IMPORT_RULES:
            new_text = new_text.replace(old, new)
        if new_text != text:
            py.write_text(new_text, encoding="utf-8", newline="\n")
            print(f"rewritten: {py.relative_to(ROOT)}")

    leftover = ROOT / "src" / "backend"
    if leftover.exists() and not any(leftover.iterdir()):
        leftover.rmdir()
        print("removed empty: src/backend")
    elif leftover.exists():
        print("src/backend still has:", [str(p) for p in leftover.rglob("*")])

    return 0


if __name__ == "__main__":
    sys.exit(main())