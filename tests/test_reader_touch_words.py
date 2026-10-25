"""Woorduitleg op tablets, ook zonder ingebouwde dialoogondersteuning."""
import json
import pytest
from tests.test_geintegreerde_lezer import browser, site, page_for


@pytest.mark.parametrize('width', [1024,1366])
@pytest.mark.parametrize('native_dialog', [True,False])
def test_tikken_op_moeilijk_woord_op_tablet(browser, site, width, native_dialog):
    page=page_for(browser,site,viewport={'width':width,'height':1024},has_touch=True)
    if not native_dialog:
        page.add_init_script('delete HTMLDialogElement.prototype.showModal;delete HTMLDialogElement.prototype.close;')
    terms={'genesis':[{'woord':'Geest van God','hoofdstukken':[1],'eenvoudig':'God is hier en werkt.'}]}
    page.context.route('https://opengodsword.com/data/opw-begrippen.js*',lambda route:route.fulfill(content_type='application/javascript',body='window.OGWReadingTerms='+json.dumps(terms)+';'))
    page.goto(site+'/bijbel/genesis/1.html',wait_until='networkidle')
    word=page.locator('.opw-word-link').filter(has_text='Geest van God').first
    word.tap()
    dialog=page.locator('.opw-word-dialog[open]')
    assert dialog.is_visible()
    assert 'God is hier en werkt.' in dialog.inner_text()
    dialog.get_by_role('button',name='Sluiten',exact=True).tap()
    assert not page.locator('.opw-word-dialog[open]').count()
    assert not page.locator('.opw-dialog-backdrop').count()
    assert not page.evaluate('document.body.classList.contains("opw-dialog-open")')
