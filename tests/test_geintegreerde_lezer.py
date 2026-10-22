"""Eén hoofdstukadres biedt tekst, citaten en leesinstellingen."""
import http.server
from pathlib import Path
import threading

import pytest
from playwright.sync_api import sync_playwright

from scripts.build_leespaginas import build_site

ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture(scope="module")
def site():
    build_site(ROOT)

    class Quiet(http.server.SimpleHTTPRequestHandler):
        def __init__(self, *args, **kwargs):
            super().__init__(*args, directory=str(ROOT), **kwargs)

        def log_message(self, *_args):
            pass

    server = http.server.ThreadingHTTPServer(("127.0.0.1", 0), Quiet)
    threading.Thread(target=server.serve_forever, daemon=True).start()
    try:
        yield f"http://127.0.0.1:{server.server_port}"
    finally:
        server.shutdown()


@pytest.fixture
def browser():
    with sync_playwright() as p:
        instance = p.chromium.launch()
        yield instance
        instance.close()


def page_for(browser, site, **kwargs):
    context = browser.new_context(**kwargs)
    context.route("**/*", lambda route: route.continue_() if route.request.url.startswith(site) else route.abort())
    return context.new_page()


def test_de_volledige_lezer_is_standaard_met_rode_cursieve_citaten(browser, site):
    page = page_for(browser, site, viewport={"width": 1440, "height": 1000})
    page.add_init_script("localStorage.setItem('sv2026_vertaalopties', JSON.stringify({versnummers:'aan'}))")
    page.goto(site + "/index.html#genesis/1", wait_until="domcontentloaded")
    page.wait_for_url("**/bijbel/genesis/1.html")
    quote = page.locator('.verse-row[data-verse="3"] .god-speaks').first
    quote.wait_for(timeout=20000)
    assert page.locator("#verses-container h1").inner_text() == "Genesis 1"
    assert "Gods Woord in begrijpelijke taal" in page.locator(".opv-meta").first.inner_text()
    assert page.locator(".verse-num").first.evaluate("el => getComputedStyle(el).display") == "none"
    assert quote.evaluate("el => getComputedStyle(el).color") == "rgb(163, 32, 32)"
    assert quote.evaluate("el => getComputedStyle(el).fontStyle") == "italic"
    assert page.locator(".opw-hoofdstukbeeld img").count() == 3
    assert page.locator(".opw-hoofdstukbeeld img").first.get_attribute("src") == "/images/boekseries/genesis/1.webp"
    for picture in page.locator(".opw-hoofdstukbeeld img").all():
        page.wait_for_function("img => img.complete && img.naturalWidth > 0", arg=picture.element_handle())
    page.locator("#topnav-weergave").click()
    assert page.locator("#sidebar-right").is_visible()
    assert page.locator("#sidebar-right #toggle-versnummers").count() == 0
    page.locator("#toggle-citaten").uncheck()
    page.wait_for_function("document.body.classList.contains('citaten-uit')")
    assert quote.evaluate("el => getComputedStyle(el).fontStyle") == "normal"
    page.locator("#sidebar-right-toggle").click()
    page.locator(".opv-verder-vol").click()
    page.wait_for_url("**/bijbel/genesis/2.html")
    page.locator('.verse-row[data-verse="1"]').wait_for(timeout=20000)
    assert page.locator("#verses-container h1").inner_text() == "Genesis 2"


def test_tekst_en_citaten_zijn_ook_zonder_javascript_aanwezig(browser, site):
    page = page_for(browser, site, java_script_enabled=False)
    page.goto(site + "/bijbel/genesis/1.html", wait_until="domcontentloaded")
    assert page.locator("h1").inner_text() == "Genesis 1"
    quote = page.locator("#vers-3 .god-speaks").first
    assert "Laat er licht zijn!" in quote.inner_text()
    assert quote.evaluate("el => getComputedStyle(el).fontStyle") == "italic"
    assert page.locator("#opv-start").count() == 0


def test_versankers_zoeken_en_boekenmenu_gebruiken_hetzelfde_adres(browser, site):
    page = page_for(browser, site, viewport={"width": 390, "height": 844})
    page.goto(site + "/bijbel/johannes/1.html#vers-40", wait_until="domcontentloaded")
    page.locator('.verse-row[data-verse="40"]').wait_for(timeout=20000)
    page.wait_for_function("document.querySelector('#opv-hfst .mp-label').textContent === 'Johannes 1'")
    page.evaluate("Search._goTo('genesis', 2, 3)")
    page.wait_for_url("**/bijbel/genesis/2.html#vers-3")
    page.locator('.verse-row[data-verse="3"]').wait_for(timeout=20000)
    page.wait_for_function("document.querySelector('#opv-hfst .mp-label').textContent === 'Genesis 2'")
    page.goto(site + "/bijbel/", wait_until="domcontentloaded")
    assert page.locator(".opw-boeken img").count() == 88
    assert page.evaluate("document.documentElement.scrollWidth <= innerWidth")
    page.locator("#topnav-weergave").click()
    page.locator("#sidebar-right[open]").wait_for(timeout=15000)


def test_startbeelden_en_laatste_genesishoofdstuk_laden_op_mobiel(browser, site):
    page = page_for(browser, site, viewport={"width": 390, "height": 844})
    page.goto(site + "/", wait_until="domcontentloaded")
    pictures = page.locator(".opv-verhaalbeeld")
    assert pictures.count() == 6
    for picture in pictures.all():
        picture.scroll_into_view_if_needed()
        page.wait_for_function("img => img.complete && img.naturalWidth > 0", arg=picture.element_handle())
    assert page.evaluate("document.documentElement.scrollWidth <= innerWidth")
    page.goto(site + "/bijbel/genesis/50.html", wait_until="domcontentloaded")
    page.locator('.verse-row[data-verse="1"]').wait_for(timeout=20000)
    page.wait_for_function("document.querySelector('.opw-hoofdstukbeeld img')?.naturalWidth > 0")
    assert page.locator(".opw-hoofdstukbeeld img").count() == 3
    assert page.locator(".opw-hoofdstukbeeld img").first.get_attribute("src") == "/images/boekseries/genesis/50-1.webp"


@pytest.mark.parametrize("chapter,width", [(1, 1440), (40, 390)])
def test_exodusbeelden_in_dezelfde_lezer(browser, site, chapter, width):
    page = page_for(browser, site, viewport={"width": width, "height": 900})
    page.goto(site + f"/index.html#exodus/{chapter}", wait_until="domcontentloaded")
    page.wait_for_url(f"**/bijbel/exodus/{chapter}.html")
    page.locator(".verse-num").first.wait_for(state="attached", timeout=20000)
    assert page.locator("#verses-container h1").inner_text() == f"Exodus {chapter}"
    assert page.locator(".opw-hoofdstukbeeld img").count() == 3
    assert page.locator(".opw-hoofdstukbeeld img").first.get_attribute("src").startswith("/images/boekseries/exodus/")
    page.wait_for_function("document.querySelector('.opw-hoofdstukbeeld img')?.naturalWidth > 0")
    assert page.locator(".verse-num").first.evaluate("el => getComputedStyle(el).display") == "none"
    assert page.evaluate("document.documentElement.scrollWidth <= innerWidth")
    page.locator("#topnav-weergave" if width > 640 else "#opv-duim-aa").click()
    assert page.locator("#sidebar-right").is_visible()
