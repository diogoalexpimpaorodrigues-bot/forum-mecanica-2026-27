"""Ensaio prolongado de pontos: concorrência, repetição e reconciliação contínua.
Só pode correr na base descartável criada por run_browser_tests.py.
"""

import json
import os
import random
import sys
import time
from collections import Counter
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from urllib.error import HTTPError
from urllib.request import Request, urlopen

ROOT = Path(__file__).resolve().parents[1]
if os.getenv("FORUM_ISOLATED_TESTS") != "1" or not os.getenv("FORUM_DB_PATH"):
    sys.exit("Usa: python tests/run_browser_tests.py --suite soak --minutes 1")
sys.path.insert(0, str(ROOT / "backend"))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
import django

django.setup()
from core.models import Wallet
from django.contrib.auth.models import User
from django.db import connections
from django.test import Client

BASE = os.environ["BASE_URL"]
DURATION = float(os.environ.get("SOAK_MINUTES", "1")) * 60
START = time.monotonic()
accounts = []
for index in range(16):
    user = User.objects.create_user(f"soak_{index}")
    Wallet.objects.create(user=user)
    client = Client(HTTP_HOST="127.0.0.1")
    client.force_login(user)
    client.get("/api/session/")
    accounts.append(
        {
            "cookie": "; ".join(
                f"{key}={value.value}" for key, value in client.cookies.items()
            ),
            "csrf": client.cookies["csrftoken"].value,
            "username": user.username,
        }
    )
connections.close_all()


def request(account, path, data=None):
    headers = {
        "Cookie": account["cookie"],
        "X-CSRFToken": account["csrf"],
        "Content-Type": "application/json",
    }
    req = Request(
        BASE + "/api/" + path + "/",
        data=json.dumps(data).encode() if data is not None else None,
        headers=headers,
        method="POST" if data is not None else "GET",
    )
    try:
        response = urlopen(req, timeout=30)
    except HTTPError as error:
        response = error
    with response:
        return response.status, json.load(response)


def worker(seed):
    rng = random.Random(seed)
    counts = Counter()
    latencies = []
    rounds = 0
    while time.monotonic() - START < DURATION:
        account = rng.choice(accounts)
        path = rng.choice(["session", "claim", "claim", "redeem"])
        if path == "claim":
            identifier, answer = rng.choice(
                [("energia", 1), ("mecanica", 2), ("circular", 0)]
            )
            data = {
                "id": identifier,
                "answer": answer,
                "expected_user": account["username"],
            }
        elif path == "redeem":
            data = {
                "id": rng.choice(["autocolantes", "caderno", "garrafa"]),
                "expected_user": account["username"],
            }
        else:
            data = None
        before = time.monotonic()
        status, payload = request(account, path, data)
        latencies.append(time.monotonic() - before)
        assert status in [200, 409, 503], (status, payload)
        counts[str(status)] += 1
        if status == 200:
            assert payload["user"]["username"] == account["username"]
            assert payload["balance"] >= 0
            assert payload["balance"] == sum(m["amount"] for m in payload["movements"])
            keys = [(m["kind"], m["reference"]) for m in payload["movements"]]
            assert len(keys) == len(set(keys)), keys
            assert payload["revision"] == len(payload["movements"])
        rounds += 1
        # Tráfego controlado: o objetivo é verificar estabilidade, sem saturar a máquina.
        time.sleep(rng.uniform(0.05, 0.2))
    return counts, latencies, rounds


with ThreadPoolExecutor(max_workers=4) as pool:
    futures = [pool.submit(worker, seed) for seed in range(4)]
    while not all(f.done() for f in futures):
        completed = sum(f.done() for f in futures)
        print(
            f"Ensaio em curso: {int(time.monotonic() - START)} s; {completed}/4 trabalhadores terminados.",
            flush=True,
        )
        time.sleep(min(20, max(1, DURATION - (time.monotonic() - START))))
    results = [f.result() for f in futures]
counts = Counter()
times = []
for tally, latencies, _ in results:
    counts.update(tally)
    times.extend(latencies)
for account in accounts:
    status, data = request(account, "session")
    assert status == 200
    assert data["balance"] == sum(m["amount"] for m in data["movements"])
times.sort()
report = {
    "seconds": round(time.monotonic() - START, 2),
    "workers": 4,
    "accounts": len(accounts),
    "requests": len(times),
    "http_statuses": dict(counts),
    "latency_p50_ms": round(times[len(times) // 2] * 1000, 2),
    "latency_p95_ms": round(times[int(len(times) * 0.95)] * 1000, 2),
    "invariants": "saldo não negativo; saldo igual à soma do histórico; operações únicas; isolamento por conta; revisão igual ao número de movimentos",
    "passed": True,
}
(ROOT / "docs/qa").mkdir(parents=True, exist_ok=True)
(ROOT / "docs/qa/soak.json").write_text(
    json.dumps(report, indent=2, ensure_ascii=False)
)
print(json.dumps(report, indent=2, ensure_ascii=False), flush=True)
