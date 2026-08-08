"""Atualiza todas as dependencias Python do ambiente virtual."""

import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REQ = ROOT / "backend" / "requirements.txt"


def main() -> None:
    subprocess.check_call([sys.executable, "-m", "pip", "install", "--upgrade", "pip"])
    subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", str(REQ), "--upgrade"])
    print("Dependencias atualizadas.")


if __name__ == "__main__":
    main()
