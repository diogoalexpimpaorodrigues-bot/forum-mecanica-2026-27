"""Auditoria real de acessibilidade, teclado, rede e sincronização entre separadores.
Requer npm ci no frontend (axe-core) e o servidor de demonstração ligado.
"""

import json
import os
import time
from pathlib import Path
from urllib.parse import urljoin

from playwright.sync_api import expect, sync_playwright

ROOT = Path(__file__).resolve().parents[1]
BASE = os.getenv("BASE_URL", "http://127.0.0.1:8000")
OUT = ROOT / "docs" / "qa"
OUT.mkdir(parents=True, exist_ok=True)
AXE = (ROOT / "frontend/node_modules/axe-core/axe.min.js").read_text()
report = []


def audit(page, name):
    page.evaluate(AXE)
    result = page.evaluate(
        "async () => { const r = await axe.run(document, {runOnly:{type:'tag',values:['wcag2a','wcag2aa','wcag21aa']}}); return {violations:r.violations.map(v=>({id:v.id,impact:v.impact,description:v.description,nodes:v.nodes.map(n=>({target:n.target,summary:n.failureSummary}))})),passes:r.passes.length}; }"
    )
    report.append({"screen": name, **result})
    (OUT / "accessibility.json").write_text(
        json.dumps(report, indent=2, ensure_ascii=False)
    )
    assert not result["violations"], json.dumps(
        result["violations"], ensure_ascii=False
    )


with sync_playwright() as p:
    browser = p.chromium.launch()
    context = browser.new_context(
        viewport={"width": 1440, "height": 1000},
        permissions=["clipboard-read", "clipboard-write"],
    )
    page = context.new_page()
    page.goto(BASE)
    expect(page.get_by_label("Nome de utilizador")).to_be_visible()
    # O ficheiro recebido deve chegar intacto ao navegador, incluindo no favicon.
    logo = page.locator(".brand-icon")
    expect(logo).to_have_js_property("naturalWidth", 200)
    original = (ROOT / "frontend/src/assets/forum-logo.png").read_bytes()
    assert page.request.get(urljoin(BASE, logo.get_attribute("src"))).body() == original
    favicon = page.locator('link[rel="icon"]').get_attribute("href")
    assert page.request.get(urljoin(BASE, favicon)).body() == original
    # A apresentação é mais longa do que a área pessoal; verificamos também
    # as colunas, a ilustração e o formulário em quatro larguras reais.
    for width in [320, 390, 768, 1440]:
        page.set_viewport_size({"width": width, "height": 900})
        assert page.evaluate("document.documentElement.scrollWidth <= innerWidth"), (
            f"Overflow na página inicial a {width}px"
        )
        audit(page, f"entrada-{width}")
    page.keyboard.press("Tab")
    expect(page.get_by_role("link", name="Saltar para o conteúdo")).to_be_focused()
    page.keyboard.press("Enter")
    expect(page.locator("#main-content")).to_be_focused()
    page.get_by_role("button", name="Criar conta", exact=True).click()
    page.get_by_role("button", name="Criar conta e começar").click()
    expect(page.get_by_label("Nome de utilizador")).to_be_focused()
    audit(page, "registo-com-erros")
    username = "qa_" + str(time.time_ns())
    page.get_by_label("Nome de utilizador").fill(username)
    page.get_by_label("Palavra-passe", exact=True).fill("Revisao!Segura2026")
    page.get_by_label("Confirmar palavra-passe").fill("Revisao!Segura2026")
    page.get_by_role("button", name="Criar conta e começar").click()
    expect(page.locator(".balance strong")).to_have_text("0 pts")
    for width in [320, 390, 768, 1440]:
        page.set_viewport_size({"width": width, "height": 900})
        assert page.evaluate("document.documentElement.scrollWidth <= innerWidth"), (
            f"Overflow a {width}px"
        )
        audit(page, f"desafios-{width}")
    for i, answer in enumerate(["Vento", "Newton", "Manutenção preventiva"]):
        card = page.locator(".challenge").nth(i)
        card.get_by_label(answer, exact=True).check()
        card.get_by_role("button", name="Validar resposta").click()
        expect(card).to_contain_text("Desafio concluído")
    expect(page.locator(".balance strong")).to_have_text("300 pts")
    page.get_by_role("button", name="Loja de brindes", exact=True).click()
    audit(page, "loja")
    page.locator(".reward").nth(0).get_by_role("button", name="Resgatar brinde").click()
    modal = page.get_by_role("dialog")
    expect(modal).to_be_visible()
    audit(page, "confirmacao")
    for _ in range(5):
        page.keyboard.press("Tab")
        assert page.evaluate(
            'document.querySelector("dialog").contains(document.activeElement) || document.activeElement === document.body'
        )
    page.keyboard.press("Escape")
    expect(modal).to_have_count(0)
    expect(
        page.locator(".reward").nth(0).get_by_role("button", name="Resgatar brinde")
    ).to_be_focused()

    # O servidor conclui o débito; a resposta é descartada para simular uma ligação perdida.
    def lose_response(route):
        response = route.fetch()
        assert response.status == 200
        route.abort("failed")

    page.route("**/api/redeem/", lose_response, times=1)
    page.locator(".reward").nth(0).get_by_role("button", name="Resgatar brinde").click()
    page.get_by_role("button", name="Confirmar resgate", exact=True).click()
    expect(modal).to_have_count(0)
    expect(page.locator(".balance strong")).to_have_text("220 pts")
    expect(page.locator(".movement")).to_have_count(4)
    expect(page.get_by_role("status")).to_contain_text("confirmado no servidor")
    page.get_by_role("button", name="Copiar código de Pack de autocolantes").click()
    code = page.locator(".redemption-code code").inner_text()
    assert page.evaluate("navigator.clipboard.readText()") == code
    with page.expect_download() as download:
        page.get_by_role("button", name="Descarregar histórico").click()
    downloaded = download.value.path()
    assert "Pack de autocolantes" in Path(downloaded).read_text(encoding="utf-8-sig")
    page.get_by_role("button", name="Resgates", exact=True).click()
    expect(page.locator(".movement")).to_have_count(1)
    audit(page, "historico-filtrado")
    page.reload()
    expect(
        page.get_by_role("heading", name="O teu percurso, em movimentos.")
    ).to_be_visible()

    page.get_by_role("button", name="Loja de brindes", exact=True).click()
    page.locator(".reward").nth(1).get_by_role("button", name="Resgatar brinde").click()
    context.set_offline(True)
    page.get_by_role("button", name="Confirmar resgate", exact=True).click()
    expect(modal.get_by_role("alert")).to_contain_text("ligação")
    expect(modal).to_be_visible()
    page.keyboard.press("Escape")
    context.set_offline(False)
    expect(page.locator(".balance strong")).to_have_text("220 pts")

    # Um segundo separador partilha a sessão; terminar sessão limpa o primeiro.
    other = context.new_page()
    other.goto(BASE + "/dashboard")
    expect(other.locator(".balance strong")).to_have_text("220 pts")
    other.get_by_role("button", name="Sair", exact=True).click()
    expect(page.get_by_label("Nome de utilizador")).to_be_visible()
    expect(other.get_by_label("Nome de utilizador")).to_be_visible()
    browser.close()
print(
    f"PASS: {len(report)} auditorias axe sem violações; teclado, foco, resposta perdida, offline, CSV, clipboard e sessão entre separadores."
)
