"""De zijkolom van de lezer toont drie uitleggen tegelijk."""
import json
from pathlib import Path

import pytest
from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]
SITE = "https://lezer.test"
WOORDEN = ["hemel", "aarde", "licht", "water", "zee"]
PAGINA = f"""<!doctype html><html lang="nl"><head><meta charset="utf-8">
<link rel="stylesheet" href="/css/opv.css"></head><body><main id="content"><div id="verses-container">
<section class="opw-leesindeling"><div class="opw-leeskolom">{''.join(
    f'<div style="height:900px"><div class="verse-row" data-book="genesis" data-chapter="1" data-verse="{i + 1}">'
    f'<div class="verse-cell col-2026" lang="nl">Dit gaat over {woord}.</div></div></div>' for i, woord in enumerate(WOORDEN + WOORDEN[:1]))
}</div></section></div></main><script src="/js/reading-details.js"></script></body></html>"""


def bron(woorden):
    return "window.OGWReadingTerms = " + json.dumps({"genesis": [
        {"woord": woord, "eenvoudig": f"Uitleg van {woord}.", "hoofdstukken": [1],
         **({"naslag": {"naam": woord, "url": "materialen.html?item=water"}} if woord == "water" else {})}
        for woord in woorden]}) + ";"


@pytest.fixture
def page():
    with sync_playwright() as p:
        browser = p.chromium.launch()
        context = browser.new_context(viewport={"width": 1440, "height": 900})
        context.route(SITE + "/lezer.html", lambda route: route.fulfill(content_type="text/html", body=PAGINA))
        context.route(SITE + "/css/opv.css", lambda route: route.fulfill(path=str(ROOT / "css/opv.css"), content_type="text/css"))
        context.route(SITE + "/js/reading-details.js", lambda route: route.fulfill(
            path=str(ROOT / "js/reading-details.js"), content_type="application/javascript"))
        yield context.new_page()
        browser.close()


def met_bron(page, woorden):
    page.context.route("https://opengodsword.com/data/opw-begrippen.js*", lambda route: route.fulfill(
        content_type="application/javascript", body=bron(woorden)))
    page.goto(SITE + "/lezer.html", wait_until="networkidle")


def getoond(page):
    return page.locator(".opw-uitleg h2").all_inner_texts()


def test_drie_uitleggen_en_het_huidige_woord_bovenaan(page):
    met_bron(page, WOORDEN)
    assert getoond(page) == ["hemel", "aarde", "licht"]
    assert page.locator(".opw-uitleg.is-huidig h2").inner_text() == "hemel"
    assert "Uitleg van aarde." in page.locator(".opw-word-explanation").inner_text()


def test_verder_lezen_schuift_door_zonder_woorden_over_te_slaan(page):
    met_bron(page, WOORDEN)
    page.evaluate("document.querySelector('[data-verse=\"3\"]').scrollIntoView({block: 'center'})")
    page.wait_for_function("document.querySelector('.opw-uitleg.is-huidig h2').textContent === 'licht'")
    assert getoond(page) == ["licht", "water", "zee"]


def test_aan_het_eind_vullen_eerdere_woorden_aan_en_niets_komt_dubbel(page):
    met_bron(page, WOORDEN)
    page.evaluate("document.querySelector('[data-verse=\"5\"]').scrollIntoView({block: 'center'})")
    page.wait_for_function("document.querySelector('.opw-uitleg.is-huidig h2').textContent === 'zee'")
    assert getoond(page) == ["zee", "hemel", "water"]


def test_klik_zet_het_woord_bovenaan(page):
    met_bron(page, WOORDEN)
    page.locator(".opw-word-link", has_text="water").first.click()
    assert getoond(page) == ["water", "zee", "hemel"]


def test_bron_staat_een_keer_onderaan_en_naslag_op_het_woord(page):
    met_bron(page, WOORDEN)
    page.locator(".opw-word-link", has_text="water").first.click()
    paneel = page.locator(".opw-word-explanation")
    assert paneel.locator(".opw-word-source").count() == 1
    assert paneel.locator(".opw-word-source").inner_text() == "Uitleg uit Open Gods Word · concept"
    assert paneel.locator('.opw-uitleg h2 a[href="https://opengodsword.com/materialen.html?item=water"]').inner_text() == "water"


def test_minder_dan_drie_woorden_kan_ook(page):
    met_bron(page, ["hemel"])
    assert getoond(page) == ["hemel"]


def test_zonder_uitleg_blijft_het_paneel_weg(page):
    met_bron(page, [])
    assert page.locator(".opw-word-explanation").is_hidden()
