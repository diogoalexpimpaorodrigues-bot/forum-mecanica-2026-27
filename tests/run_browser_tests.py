"""Executa os testes num servidor e numa base descartáveis, sem tocar nas contas locais."""

import argparse
import json
import os
import secrets
import socket
import subprocess
import sys
import tempfile
import time
from pathlib import Path
from urllib.error import URLError
from urllib.request import urlopen

ROOT = Path(__file__).resolve().parents[1]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--suite", choices=["all", "e2e", "ui", "api", "soak", "preview"], default="all"
    )
    parser.add_argument(
        "--minutes",
        type=float,
        default=1,
        help="Duração do ensaio prolongado, quando --suite soak.",
    )
    parser.add_argument(
        "--browser", choices=["chromium", "firefox", "webkit"], default="chromium"
    )
    args = parser.parse_args()
    if args.browser != "chromium" and args.suite != "e2e":
        parser.error("Para Firefox ou WebKit usa --suite e2e.")
    if args.minutes <= 0:
        parser.error("A duração tem de ser positiva.")
    scripts = {
        "all": ["e2e.py", "ui_audit.py", "api_smoke.py"],
        "preview": ["capture_preview.py"],
        "e2e": ["e2e.py"],
        "ui": ["ui_audit.py"],
        "api": ["api_smoke.py"],
        "soak": ["soak.py"],
    }
    with tempfile.TemporaryDirectory(prefix="forum-tests-") as directory:
        with socket.socket() as sock:
            sock.bind(("127.0.0.1", 0))
            port = sock.getsockname()[1]
        env = os.environ | {
            "FORUM_DB_PATH": str(Path(directory) / "test.sqlite3"),
            "FORUM_ISOLATED_TESTS": "1",
            "DJANGO_SECRET_KEY": secrets.token_urlsafe(64),
            "DJANGO_DEBUG": "1",
            "BASE_URL": f"http://127.0.0.1:{port}",
            "SOAK_MINUTES": str(args.minutes),
            "TEST_BROWSER": args.browser,
        }
        subprocess.run(
            [sys.executable, "manage.py", "migrate", "--noinput"],
            cwd=ROOT / "backend",
            env=env,
            check=True,
            stdout=subprocess.DEVNULL,
        )
        with (Path(directory) / "server.log").open("w+") as log:
            server = subprocess.Popen(
                [
                    sys.executable,
                    "manage.py",
                    "runserver",
                    f"127.0.0.1:{port}",
                    "--noreload",
                ],
                cwd=ROOT / "backend",
                env=env,
                stdout=log,
                stderr=log,
            )
            results = []
            try:
                ready = False
                for _ in range(100):
                    if server.poll() is not None:
                        break
                    try:
                        with urlopen(
                            env["BASE_URL"] + "/api/session/", timeout=1
                        ) as response:
                            ready = response.status == 200
                    except (URLError, TimeoutError):
                        pass
                    if ready:
                        break
                    time.sleep(0.1)
                if not ready:
                    raise RuntimeError("O servidor isolado não arrancou.")
                for script in scripts[args.suite]:
                    started = time.monotonic()
                    result = subprocess.run(
                        [sys.executable, str(ROOT / "tests" / script)],
                        cwd=ROOT,
                        env=env,
                    )
                    results.append(
                        {
                            "script": script,
                            "passed": result.returncode == 0,
                            "seconds": round(time.monotonic() - started, 2),
                        }
                    )
                    if result.returncode:
                        raise RuntimeError(f"O teste {script} falhou.")
            except Exception:
                log.flush()
                log.seek(0)
                print(
                    "\nÚltimas mensagens do servidor:\n"
                    + "\n".join(log.read().splitlines()[-25:]),
                    file=sys.stderr,
                )
                raise
            finally:
                server.terminate()
                try:
                    server.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    server.kill()
                    server.wait()
                report = ROOT / "docs/qa"
                report.mkdir(parents=True, exist_ok=True)
                (report / f"{args.suite}-{args.browser}-run.json").write_text(
                    json.dumps(
                        {"isolated_database": True, "results": results}, indent=2
                    )
                )
            print(
                "PASS: servidor e base isolados; dados de teste removidos automaticamente."
            )


if __name__ == "__main__":
    main()
