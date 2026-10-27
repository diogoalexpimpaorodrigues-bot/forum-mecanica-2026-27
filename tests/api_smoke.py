"""Verificação HTTP e concorrência com SQLite real. Apenas biblioteca padrão.
Cria uma conta descartável em cada execução; usar exclusivamente na demonstração local.
"""

import json
import os
import time
from concurrent.futures import ThreadPoolExecutor
from http.cookiejar import CookieJar
from urllib.error import HTTPError
from urllib.request import HTTPCookieProcessor, Request, build_opener

base = os.getenv("BASE_URL", "http://127.0.0.1:8000")
jar = CookieJar()
opener = build_opener(HTTPCookieProcessor(jar))
opener.open(base + "/api/session/").close()


def post(path, data):
    csrf = next(cookie.value for cookie in jar if cookie.name == "csrftoken")
    # Cada thread usa o mesmo cookie de sessão, sem alterar o CookieJar partilhado.
    cookie = "; ".join(f"{item.name}={item.value}" for item in jar)
    request = Request(
        base + "/api/" + path + "/",
        data=json.dumps(data).encode(),
        headers={
            "Content-Type": "application/json",
            "X-CSRFToken": csrf,
            "Cookie": cookie,
        },
        method="POST",
    )
    try:
        response = build_opener().open(request)
    except HTTPError as error:
        response = error
    with response:
        return response.status, json.load(response)


username = "smoke_" + str(time.time_ns())
csrf = next(cookie.value for cookie in jar if cookie.name == "csrftoken")
request = Request(
    base + "/api/register/",
    data=json.dumps(
        {
            "username": username,
            "password": "Motor!Seguro2026",
            "confirmation": "Motor!Seguro2026",
        }
    ).encode(),
    headers={"Content-Type": "application/json", "X-CSRFToken": csrf},
    method="POST",
)
with opener.open(request) as response:
    assert response.status == 201
with ThreadPoolExecutor(max_workers=4) as pool:
    statuses = list(
        pool.map(lambda _: post("claim", {"id": "energia", "answer": 1})[0], range(4))
    )
assert statuses.count(200) == 1 and all(s in (200, 409, 503) for s in statuses), (
    statuses
)
for identifier, answer in [("mecanica", 2), ("circular", 0)]:
    assert post("claim", {"id": identifier, "answer": answer})[0] == 200
with ThreadPoolExecutor(max_workers=2) as pool:
    redemptions = list(
        pool.map(lambda id: post("redeem", {"id": id})[0], ["caderno", "garrafa"])
    )
assert redemptions.count(200) == 1 and all(s in (200, 409, 503) for s in redemptions), (
    redemptions
)
with opener.open(base + "/api/session/") as response:
    data = json.load(response)
assert data["balance"] in (50, 120), data
assert data["balance"] == sum(m["amount"] for m in data["movements"])
assert len(data["movements"]) == 4
print(
    "PASS: quatro créditos simultâneos resultam num único crédito; dois resgates incompatíveis resultam num único débito; saldo e histórico reconciliados."
)
print("Estados HTTP crédito:", statuses, "resgates:", redemptions)
