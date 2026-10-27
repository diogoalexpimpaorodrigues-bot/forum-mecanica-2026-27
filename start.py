#!/usr/bin/env python3
"""Arranque portátil da demonstração local, com verificação de pré-requisitos.
Desenvolvido com auxílio de IA; ver AI_USAGE.md.
"""

import argparse
import importlib.util
import socket
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent


def main():
    parser = argparse.ArgumentParser(
        description="Inicia o Passaporte Fórum no teu computador."
    )
    parser.add_argument(
        "--port", type=int, default=8000, help="Porta local (por defeito: 8000)."
    )
    args = parser.parse_args()
    if not 1 <= args.port <= 65535:
        parser.error("A porta deve estar entre 1 e 65535.")
    if sys.version_info < (3, 10):
        parser.exit(1, "É necessário Python 3.10 ou superior.\n")
    if importlib.util.find_spec("django") is None:
        parser.exit(
            1,
            "Instala as dependências: python -m pip install -r backend/requirements.txt\n",
        )
    if not (ROOT / "frontend/dist/index.html").exists():
        parser.exit(
            1, "Falta o React compilado. Executa npm ci e npm run build em frontend/.\n"
        )
    with socket.socket() as probe:
        if probe.connect_ex(("127.0.0.1", args.port)) == 0:
            parser.exit(
                1,
                f"A porta {args.port} está ocupada. Experimenta python start.py --port {args.port + 1 if args.port < 65535 else 8000}\n",
            )
    try:
        subprocess.run(
            [sys.executable, "manage.py", "migrate"], cwd=ROOT / "backend", check=True
        )
        print(
            f"\nAbre http://127.0.0.1:{args.port} — termina com Ctrl+C.\n", flush=True
        )
        subprocess.run(
            [
                sys.executable,
                "-u",
                "manage.py",
                "runserver",
                f"127.0.0.1:{args.port}",
                "--noreload",
            ],
            cwd=ROOT / "backend",
            check=True,
        )
    except KeyboardInterrupt:
        print("\nServidor terminado.")
    except subprocess.CalledProcessError:
        parser.exit(
            1,
            "Não foi possível iniciar. Consulta a mensagem acima para corrigir a configuração.\n",
        )


if __name__ == "__main__":
    main()
