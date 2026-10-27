"""Capturas da versão final com uma conta demonstrativa numa base isolada."""

import os
from pathlib import Path

from playwright.sync_api import expect, sync_playwright

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "docs/screenshots"
OUT.mkdir(parents=True, exist_ok=True)
BASE = os.environ["BASE_URL"]
with sync_playwright() as p:
    browser = p.chromium.launch()
    context = browser.new_context(
        viewport={"width": 1440, "height": 1000}, reduced_motion="reduce"
    )
    page = context.new_page()
    page.goto(BASE)
    expect(page.get_by_label("Nome de utilizador")).to_be_visible()
    page.screenshot(path=str(OUT / "desktop-inicio.png"), full_page=True)
    page.set_viewport_size({"width": 390, "height": 844})
    page.screenshot(path=str(OUT / "mobile-inicio.png"), full_page=True)
    page.set_viewport_size({"width": 1440, "height": 1000})
    page.get_by_role("button", name="Criar conta", exact=True).click()
    page.get_by_label("Nome de utilizador").fill("ana_silva")
    page.get_by_label("Palavra-passe", exact=True).fill("Demonstracao!Segura2026")
    page.get_by_label("Confirmar palavra-passe").fill("Demonstracao!Segura2026")
    page.get_by_role("button", name="Criar conta e começar").click()
    expect(page.locator("#greeting")).to_be_focused()
    for index, answer in [(0, "Vento"), (1, "Newton")]:
        card = page.locator(".challenge").nth(index)
        card.get_by_label(answer, exact=True).check()
        card.get_by_role("button", name="Validar resposta").click()
        expect(card).to_contain_text("Desafio concluído")
    page.get_by_role("button", name="Fechar mensagem").click()
    for label, width, height in [("desktop", 1440, 1000), ("mobile", 390, 844)]:
        page.set_viewport_size({"width": width, "height": height})
        page.get_by_role("button", name="Desafios", exact=True).click()
        page.locator("#panel-title").focus()
        page.screenshot(path=str(OUT / f"{label}-dashboard.png"), full_page=True)
        page.get_by_role("button", name="Loja de brindes", exact=True).click()
        page.locator("#panel-title").focus()
        page.screenshot(path=str(OUT / f"{label}-loja.png"), full_page=True)
    page.locator(".reward").nth(0).get_by_role("button", name="Resgatar brinde").click()
    page.get_by_role("button", name="Confirmar resgate", exact=True).click()
    expect(page.get_by_role("dialog")).to_have_count(0)
    expect(page.locator("#panel-title")).to_be_focused()
    page.get_by_role("button", name="Fechar mensagem").click()
    for label, width, height in [("desktop", 1440, 1000), ("mobile", 390, 844)]:
        page.set_viewport_size({"width": width, "height": height})
        page.screenshot(path=str(OUT / f"{label}-historico.png"), full_page=True)
    browser.close()
print(
    "PASS: capturas finais de início, dashboard, loja e histórico em computador e telemóvel."
)
