"""Percurso real em Chromium. Executar com o servidor local já ligado.
Usa contas descartáveis com nomes únicos; não executar numa instalação com dados reais.
"""

import json
import os
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from urllib.request import Request, urlopen

from playwright.sync_api import expect, sync_playwright

BASE = os.getenv("BASE_URL", "http://127.0.0.1:8000")
OUT = Path(__file__).resolve().parents[1] / "docs" / "screenshots"
OUT.mkdir(parents=True, exist_ok=True)

with sync_playwright() as p:
    engine = os.getenv("TEST_BROWSER", "chromium")
    browser = getattr(p, engine).launch()
    for label, viewport in [
        ("desktop", {"width": 1440, "height": 1000}),
        ("mobile", {"width": 390, "height": 844}),
    ]:
        context = browser.new_context(viewport=viewport)
        page = context.new_page()
        errors = []
        page.on("pageerror", lambda error: errors.append(str(error)))
        page.goto(BASE)
        expect(page.get_by_label("Nome de utilizador")).to_be_visible()
        page.screenshot(path=str(OUT / f"{label}-inicio.png"), full_page=True)
        page.get_by_role("button", name="Criar conta", exact=True).click()
        username = f"e2e_{label}_{time.time_ns()}"[:30]
        page.get_by_label("Nome de utilizador").fill(username)
        page.get_by_label("Palavra-passe", exact=True).fill("Teste!Engenharia2026")
        page.get_by_label("Confirmar palavra-passe").fill("Teste!Engenharia2026")
        page.get_by_role("button", name="Criar conta e começar").click()
        expect(page.get_by_role("heading", name=f"Olá, {username}")).to_be_visible()
        first = page.locator(".challenge").nth(0)
        first.get_by_label("Carvão").check()
        first.get_by_role("button", name="Validar resposta").click()
        expect(page.get_by_role("alert")).to_contain_text("Ainda não é essa")
        first.get_by_label("Vento").check()
        first.get_by_role("button", name="Validar resposta").click()
        expect(first).to_contain_text("Desafio concluído")
        second = page.locator(".challenge").nth(1)
        second.get_by_label("Newton").check()
        second.get_by_role("button", name="Validar resposta").click()
        expect(second).to_contain_text("Desafio concluído")
        expect(page.locator(".balance strong")).to_have_text("180 pts")
        page.get_by_role("button", name="Loja de brindes").click()
        page.locator(".reward").nth(0).get_by_role(
            "button", name="Resgatar brinde"
        ).click()
        expect(page.get_by_role("dialog")).to_be_visible()
        page.get_by_role("button", name="Cancelar", exact=True).click()
        expect(page.get_by_role("dialog")).to_have_count(0)
        page.locator(".reward").nth(0).get_by_role(
            "button", name="Resgatar brinde"
        ).click()
        page.get_by_role("button", name="Confirmar resgate", exact=True).click()
        expect(page.get_by_role("dialog")).to_have_count(0)
        expect(page.locator(".balance strong")).to_have_text("100 pts")
        expect(page.locator("#panel-title")).to_be_focused()
        page.get_by_role("button", name="Loja de brindes", exact=True).click()
        expect(
            page.locator(".reward").nth(0).get_by_role("button", name="Já resgatado")
        ).to_be_disabled()
        page.get_by_role("button", name="Histórico", exact=True).click()
        expect(page.locator(".movement")).to_have_count(3)
        expect(page.get_by_text("Código de resgate", exact=False)).to_be_visible()
        page.screenshot(path=str(OUT / f"{label}-historico.png"), full_page=True)
        page.get_by_role("button", name="Desafios", exact=True).click()
        page.screenshot(path=str(OUT / f"{label}-dashboard.png"), full_page=True)
        assert page.evaluate(
            "document.documentElement.scrollWidth <= window.innerWidth"
        ), "Overflow horizontal"
        page.reload()
        expect(page.locator(".balance strong")).to_have_text("100 pts")

        # Dois pedidos simultâneos para o mesmo crédito: no máximo um pode ser aceite.
        cookies = context.cookies()
        cookie_header = "; ".join(f"{c['name']}={c['value']}" for c in cookies)
        csrf = next(c["value"] for c in cookies if c["name"] == "csrftoken")

        def claim_concurrent(_):
            from urllib.error import HTTPError

            request = Request(
                BASE + "/api/claim/",
                data=json.dumps({"id": "circular", "answer": 0}).encode(),
                headers={
                    "Content-Type": "application/json",
                    "Cookie": cookie_header,
                    "X-CSRFToken": csrf,
                },
                method="POST",
            )
            try:
                with urlopen(request) as response:
                    return response.status
            except HTTPError as error:
                return error.code

        with ThreadPoolExecutor(max_workers=2) as pool:
            statuses = list(pool.map(claim_concurrent, range(2)))
        assert statuses.count(200) == 1 and all(
            s in [200, 409, 503] for s in statuses
        ), statuses
        page.reload()
        expect(page.locator(".balance strong")).to_have_text("220 pts")
        page.get_by_role("button", name="Sair").click()
        expect(page.get_by_label("Nome de utilizador")).to_be_visible()
        page.get_by_label("Nome de utilizador").fill(username)
        page.get_by_label("Palavra-passe", exact=True).fill("Teste!Engenharia2026")
        page.get_by_role("button", name="Entrar no meu passaporte").click()
        expect(page.locator(".balance strong")).to_have_text("220 pts")
        assert not errors, errors
        print(
            f"PASS {engine}/{label}: registo, resposta errada/correta, crédito, cancelamento, resgate, histórico, persistência, concorrência, logout/login, sem overflow e sem erros JS"
        )
        context.close()
    browser.close()
