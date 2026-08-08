"""Backup do banco de dados SQLite para a pasta backups/."""

import shutil
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DB = ROOT / "backend" / "data" / "arkium.db"
DEST = ROOT / "backups"


def main() -> None:
    if not DB.exists():
        raise SystemExit(f"Banco nao encontrado em {DB}")
    DEST.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    target = DEST / f"arkium-{stamp}.db"
    shutil.copy2(DB, target)
    print(f"Backup criado: {target}")


if __name__ == "__main__":
    main()
