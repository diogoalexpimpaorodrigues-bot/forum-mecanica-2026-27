#!/usr/bin/env python3
"""Repete as verificações principais com um único comando, a partir da raiz do projeto."""

import argparse
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--browser",
        action="store_true",
        help="Inclui navegador, acessibilidade e concorrência numa base descartável.",
    )
    args = parser.parse_args()
    npm = shutil.which("npm")
    if not npm:
        parser.exit(1, "Instala Node.js 24 e npm para verificar o frontend.\n")
    commands = [
        ([sys.executable, "backend/manage.py", "check"], ROOT),
        (
            [
                sys.executable,
                "backend/manage.py",
                "makemigrations",
                "--check",
                "--dry-run",
            ],
            ROOT,
        ),
        ([sys.executable, "backend/manage.py", "test", "core"], ROOT),
        ([npm, "run", "lint"], ROOT / "frontend"),
        ([npm, "run", "format:check"], ROOT / "frontend"),
        ([npm, "test"], ROOT / "frontend"),
        ([npm, "run", "build"], ROOT / "frontend"),
    ]
    if args.browser:
        commands.append(
            ([sys.executable, "tests/run_browser_tests.py", "--suite", "all"], ROOT)
        )
    for command, cwd in commands:
        print("\nA verificar: " + " ".join(command[1:]), flush=True)
        result = subprocess.run(command, cwd=cwd)
        if result.returncode:
            parser.exit(
                1,
                "\nA verificação falhou. Corrige a mensagem acima e volta a executar.\n",
            )
    print("\nTodas as verificações selecionadas passaram.")


if __name__ == "__main__":
    main()
