"""De uitleg gebruikt de beelden van de bijbehorende levende OGW-bron."""
import json
import os
import http.server
import threading
from pathlib import Path

import pytest
from tests.test_geintegreerde_lezer import browser, page_for

OGW = Path(os.environ.get('OGW_SOURCE_DIR', Path(__file__).resolve().parents[2] / 'website-open-gods-woord'))


@pytest.fixture(scope='module')
def site():
    root = Path(__file__).resolve().parents[1]
    class Quiet(http.server.SimpleHTTPRequestHandler):
        def __init__(self, *args, **kwargs):
            super().__init__(*args, directory=str(root), **kwargs)
        def log_message(self, *_args):
            pass
    server = http.server.ThreadingHTTPServer(('127.0.0.1', 0), Quiet)
    threading.Thread(target=server.serve_forever, daemon=True).start()
    try:
        yield f'http://127.0.0.1:{server.server_port}'
    finally:
        server.shutdown()


@pytest.mark.parametrize('width,stone', [(1440, 'sardonix'), (390, 'sardonix'), (390, 'onyx')])
@pytest.mark.skipif(not (OGW / 'data/opw-begrippen.js').exists(), reason='Stel OGW_SOURCE_DIR in op de gebouwde OGW-broncheckout voor deze integratiecontrole.')
def test_echte_materialenbeelden_in_uitleg_en_dialoog(browser, site, width, stone):
    page = page_for(browser, site, viewport={'width': width, 'height': 1000})
    page.add_init_script(r"""window.RegExp = new Proxy(window.RegExp, {
        construct(target, args, newTarget) {
            if (/\(\?<([=!])/.test(String(args[0]))) throw new SyntaxError('Lookbehind niet ondersteund');
            return Reflect.construct(target, args, newTarget);
        }
    });""")
    source = (OGW / 'data/opw-begrippen.js').read_text(encoding='utf-8')
    page.context.route('https://opengodsword.com/data/opw-begrippen.js*', lambda route: route.fulfill(content_type='application/javascript', body=source))
    page.context.route('https://opengodsword.com/images/wiki/materialen/*', lambda route: route.fulfill(
        content_type='image/webp', body=(OGW / route.request.url.split('opengodsword.com/', 1)[1]).read_bytes()))
    if stone == 'onyx':
        chapter = (Path(__file__).resolve().parents[1] / 'bijbel/genesis/2.html').read_text(encoding='utf-8')
        page.context.route(site + '/bijbel/genesis/2.html', lambda route: route.fulfill(
            content_type='text/html', body=chapter.replace('sardonix', 'onyx')))
        text = (Path(__file__).resolve().parents[1] / 'data/vertalingen/nl-opv/genesis/2.json').read_text(encoding='utf-8')
        page.context.route('**/data/vertalingen/nl-opv/genesis/2.json*', lambda route: route.fulfill(
            content_type='application/json', body=text.replace('sardonix', 'onyx')))
    page.goto(site + '/bijbel/genesis/2.html', wait_until='networkidle')
    for word, item in [('goud', 'goud'), (stone, 'sardonix')]:
        link = page.locator('.opw-word-link').filter(has_text=word).first
        link.click(timeout=3000)
        panel = page.locator('.opw-word-explanation' if width > 800 else '.opw-word-dialog[open]')
        image = panel.locator('.opw-term-media img')
        assert image.get_attribute('src') == f'https://opengodsword.com/images/wiki/materialen/{item}.webp'
        page.wait_for_function('img => img.complete && img.naturalWidth > 0', arg=image.element_handle())
        assert image.get_attribute('alt')
        assert panel.locator(f'a[href="https://opengodsword.com/materialen.html?item={item}"]').count() == 1
        expected = 'Een geel metaal' if word == 'goud' else 'Welke steen het precies was, weten we niet zeker.'
        assert expected in panel.inner_text()
        if word == 'goud':
            panel.get_by_role('button', name='Vergroot afbeelding: Goud').click()
            assert page.locator('.opw-image-dialog[open] img').get_attribute('src') == image.get_attribute('src')
            page.keyboard.press('Escape')
            if width < 800:
                assert page.locator('.opw-word-dialog[open]').count() == 1
                assert page.evaluate('document.body.classList.contains("opw-dialog-open")')
        if width < 800:
            page.keyboard.press('Escape')
    assert page.evaluate('document.documentElement.scrollWidth <= innerWidth')


def test_media_weigert_vreemde_urls_en_toont_tekst_veilig(browser, site):
    page = page_for(browser, site, viewport={'width': 390, 'height': 844})
    entry = {'woord': 'goud', 'hoofdstukken': [2], 'eenvoudig': 'Een geel metaal.',
        'naslag': {'naam': '<img src=x onerror=alert(1)>', 'afbeelding': 'https://example.org/wrong.webp', 'url': 'javascript:alert(1)'}}
    page.context.route('https://opengodsword.com/data/opw-begrippen.js*', lambda route: route.fulfill(
        content_type='application/javascript', body='window.OGWReadingTerms = ' + json.dumps({'genesis': [entry]}) + ';'))
    page.goto(site + '/bijbel/genesis/2.html', wait_until='networkidle')
    page.locator('.opw-word-link').first.click()
    panel = page.locator('.opw-word-dialog[open]')
    assert panel.locator('.opw-term-media img').count() == 0
    assert panel.locator('a[href^="javascript:"]').count() == 0
    assert panel.locator('img[src="x"]').count() == 0
