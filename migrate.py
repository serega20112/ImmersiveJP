"""One-shot migration: move DDD layout to Clean Architecture layout.

Moves directories with `git mv` and rewrites `src.backend...` imports
according to a mapping table. Run from the repository root:

    python migrate.py --apply      # perform moves + rewrite imports
    python migrate.py --check      # dry run: print planned actions
"""

from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent

# Directory trees to move: (old relative dir, new relative dir)
TREE_MOVES: list[tuple[str, str]] = [
    ("src/backend/domain", "src/domain"),
    ("src/backend/dto", "src/application/dto"),
    ("src/backend/use_case", "src/application/use_cases"),
    ("src/backend/services", "src/application/services"),
    ("src/backend/repository", "src/infrastructures/repositories/implementations"),
    ("src/backend/infrastructure/repositories", "src/application/interfaces/repositories"),
    ("src/backend/infrastructure", "src/infrastructures"),
    ("src/backend/dependencies", "src/infrastructures/di_containers"),
    ("src/backend/delivery", "src/presentation/http"),
    ("src/backend/tests", "src/tests"),
]

# Single files to move: (old path, new path)
FILE_MOVES: list[tuple[str, str]] = [
    ("src/backend/create_app.py", "src/presentation/http/app.py"),
    ("src/backend/dependencies/settings_model.py", "src/config/settings.py"),
]

# Import rewrite rules: ordered, first match wins.
IMPORT_RULES: list[tuple[str, str]] = [
    ("src.config.settings", "src.config.settings"),
    ("src.infrastructures.di_containers", "src.infrastructures.di_containers"),
    ("src.application.interfaces.repositories", "src.application.interfaces.repositories"),
    ("src.infrastructures", "src.infrastructures"),
    ("src.infrastructures.repositories.implementations", "src.infrastructures.repositories.implementations"),
    ("src.application.interfaces.services", "src.application.interfaces.services"),
    ("src.application.services", "src.application.services"),
    ("src.application.use_cases", "src.application.use_cases"),
    ("src.application.dto", "src.application.dto"),
    ("src.domain", "src.domain"),
    ("src.presentation.http", "src.presentation.http"),
    ("src.presentation.http.app", "src.presentation.http.app"),
    ("src.tests", "src.tests"),
]


def git(*args: str) -> None:
    subprocess.run(["git", *args], check=True, cwd=ROOT, capture_output=True, text=True)


def move_tree(old: str, new: str, apply: bool) -> None:
    src = ROOT / old
    if not src.exists():
        print(f"skip (missing): {old}")
        return
    dst = ROOT / new
    if apply:
        dst.parent.mkdir(parents=True, exist_ok=True)
        git("mv", old, new)
        print(f"moved: {old} -> {new}")


def move_file(old: str, new: str, apply: bool) -> None:
    src = ROOT / old
    if not src.exists():
        print(f"skip (missing): {old}")
        return
    if apply:
        dst = ROOT / new
        dst.parent.mkdir(parents=True, exist_ok=True)
        git("mv", old, new)
        print(f"moved: {old} -> {new}")


def rewrite_imports(apply: bool) -> None:
    py_files = [
        p
        for p in ROOT.rglob("*.py")
        if ".venv" not in p.parts
        and "__pycache__" not in p.parts
        and ".git" not in p.parts
    ]
    changed = 0
    for path in py_files:
        text = path.read_text(encoding="utf-8")
        new_text = text
        for old, new in IMPORT_RULES:
            new_text = new_text.replace(old, new)
        if new_text != text:
            changed += 1
            print(f"rewritten: {path.relative_to(ROOT)}")
            if apply:
                path.write_text(new_text, encoding="utf-8", newline="\n")
    print(f"files changed: {changed}")


def remaining_backend_refs() -> list[str]:
    refs = []
    for p in ROOT.rglob("*.py"):
        if ".venv" in p.parts or "__pycache__" in p.parts or ".git" in p.parts:
            continue
        for i, line in enumerate(p.read_text(encoding="utf-8").splitlines(), 1):
            if "src.backend" in line:
                refs.append(f"{p.relative_to(ROOT)}:{i}: {line.strip()}")
    return refs


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--apply", action="store_true", help="perform the migration")
    parser.add_argument("--check", action="store_true", help="dry run")
    args = parser.parse_args()
    apply = args.apply

    for old, new in TREE_MOVES:
        move_tree(old, new, apply)
    for old, new in FILE_MOVES:
        move_file(old, new, apply)

    rewrite_imports(apply)

    leftovers = remaining_backend_refs()
    if leftovers:
        print("\nRemaining src.backend references:")
        for ref in leftovers:
            print(" ", ref)

    # Remove now-empty backend dir
    backend = ROOT / "src" / "backend"
    if backend.exists() and not any(backend.iterdir()):
        if apply:
            subprocess.run(["cmd", "/c", "rmdir", str(backend)], check=True, cwd=ROOT)
            print("removed empty: src/backend")
        else:
            print("would remove empty: src/backend")
    elif backend.exists():
        leftovers = [str(p.relative_to(ROOT)) for p in backend.rglob("*")]
        print("\nsrc/backend still contains:")
        for item in leftovers:
            print(" ", item)

    return 0


if __name__ == "__main__":
    sys.exit(main())