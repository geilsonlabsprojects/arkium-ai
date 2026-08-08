"""Restaura o banco a partir de um arquivo de backup.

Uso: python scripts/restore.py backups/arkium-20260101-120000.db
"""

import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DB = ROOT / "backend" / "data" / "arkium.db"


def main() -> None:
    if len(sys.argv) < 2:
        raise SystemExit("Uso: python scripts/restore.py <arquivo-de-backup.db>")
    source = Path(sys.argv[1])
    if not source.exists():
        raise SystemExit(f"Arquivo nao encontrado: {source}")
    DB.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(source, DB)
    print(f"Banco restaurado de {source}")


if __name__ == "__main__":
    main()
