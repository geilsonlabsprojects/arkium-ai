"""Remove arquivos de log e limpa a tabela de logs de requisicao."""

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
LOG_DIR = ROOT / "backend" / "logs"


def main() -> None:
    removed = 0
    for file in LOG_DIR.glob("*.log*"):
        file.unlink()
        removed += 1
    print(f"{removed} arquivo(s) de log removido(s).")
    print("Para limpar a tabela request_logs use o painel (Logs > Limpar) ou DELETE /api/admin/logs.")


if __name__ == "__main__":
    main()
