"""De eerste canvasweergave volgt de voorkeur, ook vóór externe bestanden."""
from pathlib import Path
import json
from urllib.parse import urlsplit

import pytest
from playwright.sync_api import sync_playwright

from scripts.build_leespaginas import page as render_page

ROOT = Path(__file__).resolve().parents[1]


@pytest.mark.parametrize("reading_mode", [False, True])
@pytest.mark.parametrize("theme", ["licht", "donker"])
def test_verse_background_matches_page_during_reader_start(browser, reading_mode, theme):
    context = browser.new_context(viewport={"width": 834, "height": 1194}, has_touch=True)
    tab = context.new_page()
    try:
        tab.set_content(f'''<html data-theme="{theme}"><body class="opv-lezerpagina">
            <main id="content" class="{'reading-mode' if reading_mode else ''}">
            <div id="verses-container"><div class="verse-row">
            <span class="verse-cell col-2026">In het begin maakte God de hemel en de aarde.</span>
            </div></div></main></body></html>''')
        for stylesheet in ("style.css", "opv.css", "leespaginas.css"):
            tab.add_style_tag(path=str(ROOT / "css" / stylesheet))
        assert tab.locator('.col-2026').evaluate("el => getComputedStyle(el).backgroundColor") == "rgba(0, 0, 0, 0)"
        assert tab.locator('body').evaluate("el => getComputedStyle(el).backgroundColor") == (
            "rgb(15, 28, 39)" if theme == "donker" else "rgb(251, 248, 242)")
    finally:
        context.close()


@pytest.fixture(scope="module")
def browser():
    with sync_playwright() as playwright:
        instance = playwright.chromium.launch()
        yield instance
        instance.close()


def test_dark_links_and_gold_button_have_readable_colors(browser):
    tab = browser.new_page(viewport={"width": 834, "height": 1194})
    try:
        tab.set_content('''<html data-theme="donker"><body>
            <a class="opv-knop" href="#lezen">Begin bij Johannes</a>
            <main id="content"><div id="verses-container"><span class="col-2026">
            <a class="opw-lemma-link" href="#hemel">hemel</a></span></div></main>
            <section class="opv-pagina"><a href="#bron">Lees verder</a></section>
            </body></html>''')
        for stylesheet in ("style.css", "opv.css", "leespaginas.css"):
            tab.add_style_tag(path=str(ROOT / "css" / stylesheet))
        button = tab.locator('.opv-knop')
        assert button.evaluate("el => getComputedStyle(el).color") == "rgb(20, 46, 66)"
        assert button.evaluate("el => getComputedStyle(el).backgroundColor") == "rgb(203, 164, 73)"
        button.hover()
        assert button.evaluate("el => getComputedStyle(el).color") == "rgb(20, 46, 66)"
        assert tab.locator('.opv-pagina a').evaluate("el => getComputedStyle(el).color") == "rgb(172, 203, 217)"
        assert tab.locator('.opw-lemma-link').evaluate("el => getComputedStyle(el).color") == "rgb(231, 225, 212)"
    finally:
        tab.close()


@pytest.mark.parametrize("source", ["index", "chapter"])
@pytest.mark.parametrize("delayed_theme", [False, True])
@pytest.mark.parametrize("saved,system,expected", [
    ('{"thema":"donker"}', "light", "donker"),
    ('{"thema":"licht"}', "dark", "licht"),
    ('{"thema":"auto"}', "dark", "donker"),
    (None, "dark", "donker"),
    ('invalid-json', "dark", "donker"),
    ('{"thema":"unknown"}', "dark", "donker"),
    ('null', "dark", "donker"),
    ('blocked-storage', "dark", "donker"),
    (None, "light", "licht"),
])
def test_canvas_has_theme_before_external_resources(browser, source, delayed_theme, saved, system, expected):
    document = ((ROOT / "index.html").read_text(encoding="utf-8") if source == "index" else
                render_page("Test", "Test", "/bijbel/genesis/1.html", "<p>Tekst</p>", [("Test", "/")]))
    context = browser.new_context(color_scheme=system, service_workers="block")
    context.add_init_script("localStorage.clear();" + (
        "localStorage.setItem('sv2026_vertaalopties', " + json.dumps(saved) + ");"
        if saved is not None else ""))
    if saved == 'blocked-storage':
        context.add_init_script("Object.defineProperty(window, 'localStorage', {get() {throw new DOMException('Unavailable','SecurityError')}})")
    pending = []
    holding = True

    def resource(route):
        path = urlsplit(route.request.url).path
        route.fulfill(path=str(ROOT / path.lstrip('/')))

    def respond(route):
        if route.request.is_navigation_request():
            route.fulfill(body=document, content_type="text/html")
        elif route.request.url.endswith('/js/theme.js') or '/css/' in route.request.url:
            if holding and (delayed_theme or '/css/' in route.request.url):
                pending.append(route)
            else:
                resource(route)
        else:
            route.abort()

    context.route("**/*", respond)
    tab = context.new_page()
    try:
        tab.goto("http://theme.test/", wait_until="commit")
        tab.wait_for_timeout(150)
        actual = tab.evaluate("({theme:document.documentElement.dataset.theme, background:getComputedStyle(document.documentElement).backgroundColor, scheme:getComputedStyle(document.documentElement).colorScheme})")
        assert actual == {"theme": expected, "background": "rgb(15, 28, 39)" if expected == "donker" else "rgb(251, 248, 242)", "scheme": "dark" if expected == "donker" else "light"}
        assert pending, "De externe stijlaanvragen moeten nog geblokkeerd zijn"
        tab.evaluate("window.observedThemes=[];new MutationObserver(() => observedThemes.push(document.documentElement.dataset.theme)).observe(document.documentElement,{attributes:true,attributeFilter:['data-theme']})")
        holding = False
        for route in pending:
            resource(route)
        tab.wait_for_load_state('domcontentloaded')
        assert tab.evaluate("document.documentElement.dataset.theme") == expected
        assert tab.evaluate("getComputedStyle(document.body).backgroundColor") == actual['background']
        assert tab.evaluate("observedThemes.every(theme => theme === document.documentElement.dataset.theme)")
    finally:
        if holding:
            for route in pending:
                route.abort()
        context.close()
