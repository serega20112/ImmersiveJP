"""Fix F821 undefined names: LLM mixin modules and user model relationship."""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent

LLM_MODULES = [
    "src/infrastructures/external/llm/fallbacks.py",
    "src/infrastructures/external/llm/requests.py",
    "src/infrastructures/external/llm/prompts.py",
    "src/infrastructures/external/llm/normalization.py",
]

TYPE_CHECKING_BLOCK = (
    "from __future__ import annotations\n"
    "\n"
    "from typing import TYPE_CHECKING\n"
    "\n"
    "if TYPE_CHECKING:\n"
    "    from src.infrastructures.external.llm.client import HuggingFaceLLMClient\n"
)

USER_MODEL_IMPORT = (
    "from src.infrastructures.database.database import Base\n"
    "from src.infrastructures.database.models.timestamp import TimestampMixin\n"
    "from src.infrastructures.database.models.user_document_model import UserDocument\n"
)


def main() -> int:
    for rel in LLM_MODULES:
        p = ROOT / rel
        text = p.read_text(encoding="utf-8")
        if "TYPE_CHECKING" in text:
            continue
        text = text.replace("from __future__ import annotations\n", TYPE_CHECKING_BLOCK, 1)
        p.write_text(text, encoding="utf-8", newline="\n")
        print(f"patched: {rel}")

    user_model = ROOT / "src/infrastructures/database/models/user_model.py"
    text = user_model.read_text(encoding="utf-8")
    if "user_document_model import UserDocument" not in text:
        text = text.replace(
            "from src.infrastructures.database.models.timestamp import TimestampMixin\n",
            USER_MODEL_IMPORT,
            1,
        )
        user_model.write_text(text, encoding="utf-8", newline="\n")
        print("patched: user_model.py")

    return 0


if __name__ == "__main__":
    sys.exit(main())