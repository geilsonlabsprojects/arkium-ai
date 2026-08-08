"""Remove caches do Python (__pycache__, .pytest_cache) do projeto."""

import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def main() -> None:
    removed = 0
    for path in ROOT.rglob("__pycache__"):
        shutil.rmtree(path, ignore_errors=True)
        removed += 1
    for path in ROOT.rglob(".pytest_cache"):
        shutil.rmtree(path, ignore_errors=True)
        removed += 1
    print(f"{removed} pasta(s) de cache removida(s).")


if __name__ == "__main__":
    main()
