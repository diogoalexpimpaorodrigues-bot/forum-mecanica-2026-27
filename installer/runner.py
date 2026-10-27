"""Conclui a instalação e abre o site com o Python preparado pelo executável.
Auxílio de IA identificado em AI_USAGE.md. A base pessoal fica fora de .forum/.
"""

import argparse
import datetime
import hashlib
import importlib.metadata
import json
import os
import re
import signal
import socket
import sqlite3
import subprocess
import sys
import time
import uuid
import webbrowser
from pathlib import Path
from urllib.error import URLError
from urllib.request import urlopen


def atomic_json(path, value):
    temporary = path.with_name(path.name + ".new")
    with temporary.open("w", encoding="utf-8") as file:
        json.dump(value, file, ensure_ascii=False, indent=2)
        file.write("\n")
    temporary.replace(path)
    try:
        path.chmod(0o600)
    except OSError:
        pass


def requirements_match(path):
    """Confirmamos versões instaladas, mesmo que alguém tenha alterado o ambiente."""
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.split("#", 1)[0].strip()
        if not line:
            continue
        match = re.fullmatch(r"([A-Za-z0-9_.-]+)==([A-Za-z0-9.+!-]+)", line)
        if not match:
            return False
        try:
            if importlib.metadata.version(match[1]) != match[2]:
                return False
        except importlib.metadata.PackageNotFoundError:
            return False
    return True


def install_requirements(uv, project, offline):
    requirements = project / "backend/requirements.txt"
    if requirements_match(requirements):
        print(
            "[3/4] As dependências já estão instaladas nas versões previstas.",
            flush=True,
        )
        return
    print("[3/4] A instalar as dependências do site…", flush=True)
    command = [
        str(uv),
        "pip",
        "install",
        "--python",
        sys.executable,
        "--index-url",
        "https://pypi.org/simple",
        "--only-binary",
        ":all:",
        "-r",
        str(requirements),
    ]
    if offline:
        command.append("--offline")
    subprocess.run(command, cwd=project, check=True)
    if not requirements_match(requirements):
        raise RuntimeError(
            "As versões instaladas não correspondem aos requisitos do projeto."
        )


def migration_plan(project):
    # Consultamos a configuração real do Django para respeitar também uma
    # localização personalizada da base, sem procurar ficheiros por adivinhação.
    script = """
import json, os
from pathlib import Path
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
import django
django.setup()
from django.db import connections
from django.db.migrations.executor import MigrationExecutor
connection = connections['default']
name = str(connection.settings_dict['NAME'])
path = Path(name).resolve()
existed = path.exists() and path.stat().st_size > 0
executor = MigrationExecutor(connection)
plan = executor.migration_plan(executor.loader.graph.leaf_nodes())
print(json.dumps({'database':str(path), 'existed':existed, 'pending':len(plan)}))
"""
    result = subprocess.run(
        [sys.executable, "-c", script],
        cwd=project / "backend",
        check=True,
        text=True,
        encoding="utf-8",
        stdout=subprocess.PIPE,
    )
    return json.loads(result.stdout)


def backup_database(source, directory):
    """A API SQLite inclui os dados confirmados, mesmo quando existe um WAL ativo."""
    directory.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.datetime.now(datetime.timezone.utc).strftime("%Y%m%dT%H%M%S")
    target = directory / f"db-{timestamp}-{uuid.uuid4().hex[:8]}.sqlite3"
    with sqlite3.connect(
        source.as_uri() + "?mode=ro", uri=True, timeout=20
    ) as original:
        with sqlite3.connect(target) as backup:
            original.backup(backup)
    return target


def prepare_database(project, runtime):
    print("[4/4] A verificar a base de dados…", flush=True)
    plan = migration_plan(project)
    backup = None
    if plan["pending"]:
        if plan["existed"]:
            backup = backup_database(Path(plan["database"]), runtime / "backups")
            print(f"Cópia de segurança criada: {backup}", flush=True)
        subprocess.run(
            [sys.executable, "manage.py", "migrate", "--noinput"],
            cwd=project / "backend",
            check=True,
        )
    subprocess.run(
        [sys.executable, "manage.py", "check"],
        cwd=project / "backend",
        check=True,
    )
    return plan["database"], str(backup) if backup else None


def available_port(preferred):
    for port in range(preferred, min(preferred + 20, 65536)):
        with socket.socket() as probe:
            try:
                probe.bind(("127.0.0.1", port))
                return port
            except OSError:
                continue
    with socket.socket() as probe:
        probe.bind(("127.0.0.1", 0))
        return probe.getsockname()[1]


def server_ready(url):
    try:
        with urlopen(url + "/api/session/", timeout=1) as response:
            state = json.load(response)
        with urlopen(url, timeout=1) as response:
            html = response.read().decode("utf-8")
        return "user" in state and "Passaporte Fórum" in html
    except (URLError, OSError, ValueError):
        return False


def stop_server(server):
    if server.poll() is not None:
        return
    if os.name == "nt":
        try:
            server.send_signal(signal.CTRL_BREAK_EVENT)
        except OSError:
            server.terminate()
    else:
        os.killpg(server.pid, signal.SIGTERM)
    try:
        server.wait(timeout=5)
    except subprocess.TimeoutExpired:
        server.kill()
        server.wait()


def serve(project, runtime, preferred, no_browser):
    port = available_port(preferred)
    url = f"http://127.0.0.1:{port}"
    options = (
        {"creationflags": subprocess.CREATE_NEW_PROCESS_GROUP}
        if os.name == "nt"
        else {"start_new_session": True}
    )
    server = subprocess.Popen(
        [
            sys.executable,
            "-u",
            "manage.py",
            "runserver",
            f"127.0.0.1:{port}",
            "--noreload",
        ],
        cwd=project / "backend",
        **options,
    )
    try:
        deadline = time.monotonic() + 30
        while time.monotonic() < deadline:
            if server.poll() is not None:
                raise RuntimeError("O servidor terminou antes de abrir o site.")
            if server_ready(url):
                break
            time.sleep(0.2)
        else:
            raise RuntimeError("O servidor não respondeu dentro de 30 segundos.")
        atomic_json(runtime / "server.json", {"url": url, "pid": server.pid})
        print(f"\nFórum Mecânica pronto: {url}", flush=True)
        print(
            "Mantém esta janela aberta. Para terminar, carrega em Ctrl+C.\n", flush=True
        )
        if not no_browser:
            try:
                if not webbrowser.open(url, new=2):
                    print("Abre manualmente o endereço acima no navegador.", flush=True)
            except OSError:
                print("Abre manualmente o endereço acima no navegador.", flush=True)
        result = server.wait()
        if result:
            raise RuntimeError(f"O servidor terminou com o código {result}.")
    finally:
        stop_server(server)
        (runtime / "server.json").unlink(missing_ok=True)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--project", required=True, type=Path)
    parser.add_argument("--uv", required=True, type=Path)
    parser.add_argument("--port", type=int, default=8000)
    parser.add_argument("--offline", action="store_true")
    parser.add_argument("--install-only", action="store_true")
    parser.add_argument("--no-browser", action="store_true")
    args = parser.parse_args()
    if not 1 <= args.port <= 65535:
        parser.error("A porta deve estar entre 1 e 65535.")
    project = args.project.resolve()
    runtime = project / ".forum"
    install_requirements(args.uv, project, args.offline)
    database, backup = prepare_database(project, runtime)
    atomic_json(
        runtime / "installed.json",
        {
            "installed_at": datetime.datetime.now(datetime.timezone.utc).isoformat(),
            "python": sys.version.split()[0],
            "django": importlib.metadata.version("Django"),
            "requirements_sha256": hashlib.sha256(
                (project / "backend/requirements.txt").read_bytes()
            ).hexdigest(),
            "database": database,
            "migration_backup": backup,
        },
    )
    print(f"Base de dados: {database}", flush=True)
    if not args.install_only:
        serve(project, runtime, args.port, args.no_browser)
    else:
        print(
            "Instalação concluída. Volta a abrir o mesmo instalador para iniciar o site.",
            flush=True,
        )


def interrupted(_signum, _frame):
    raise KeyboardInterrupt


if __name__ == "__main__":
    signal.signal(signal.SIGTERM, interrupted)
    if hasattr(signal, "SIGHUP"):
        signal.signal(signal.SIGHUP, interrupted)
    try:
        main()
    except KeyboardInterrupt:
        print("\nFórum terminado.", flush=True)
    except (OSError, ValueError, RuntimeError, subprocess.CalledProcessError) as error:
        print(f"\nNão foi possível concluir: {error}", file=sys.stderr)
        print(
            "Consulta .forum/installation.log. Na primeira instalação, confirma a ligação à Internet.",
            file=sys.stderr,
        )
        raise SystemExit(1) from None
