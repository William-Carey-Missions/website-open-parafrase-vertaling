"""Het vooraf gerenderde hoofdstuk gebruikt meteen de uiteindelijke beeldmaat."""
from tests.test_geintegreerde_lezer import browser, site, page_for


def test_genesis_vier_beeld_krimpt_niet_na_opstarten(browser, site):
    initial = page_for(browser, site, java_script_enabled=False, viewport={'width':1440,'height':1000})
    initial.goto(site+'/bijbel/genesis/4.html', wait_until='domcontentloaded')
    before = initial.locator('.opw-hoofdstukbeeld img').first.bounding_box()
    page = page_for(browser, site, viewport={'width':1440,'height':1000})
    page.goto(site+'/bijbel/genesis/4.html', wait_until='networkidle')
    page.locator('.opw-leesindeling[data-reading-ready="true"]').wait_for()
    after = page.locator('.opw-hoofdstukbeeld.is-active img').first.bounding_box()
    assert abs(before['width']-after['width']) < 3
    assert abs(before['height']-after['height']) < 3
