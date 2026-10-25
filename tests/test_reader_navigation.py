"""Hoofdstukken wisselen zonder een nieuw document of een lege leestekst."""
import time

import pytest

from tests.test_geintegreerde_lezer import browser, site, page_for


def ready(page, book, chapter):
    page.wait_for_function("([b,c]) => typeof Navigation !== 'undefined' && Navigation._renderedChapter === `${b}/${c}` && document.querySelector('.verse-num') && document.querySelector('.opv-verder-vol')", arg=[book, chapter])
    assert page.locator('#verses-container h1').inner_text() == f'{book.capitalize()} {chapter}'


@pytest.mark.parametrize('width,touch', [(1440, False), (1024, True), (390, True)])
def test_volgende_vorige_boekkeuze_en_browsergeschiedenis_behouden_de_lezer(browser, site, width, touch):
    page = page_for(browser, site, viewport={'width': width, 'height': 1000}, has_touch=touch)
    page.add_init_script("localStorage.setItem('sv2026_vertaalopties',JSON.stringify({thema:'donker',godsnaam:'JAHWEH'}))")
    page.goto(site + '/bijbel/genesis/1.html', wait_until='networkidle')
    ready(page, 'genesis', 1)
    page.evaluate("window.__readerDocument = 'blijft-bewaard'")
    documents = []
    page.on('request', lambda request: documents.append(request.url) if request.is_navigation_request() and request.frame == page.main_frame else None)
    page.locator('.opv-verder-vol').click()
    page.wait_for_url('**/bijbel/genesis/2.html')
    ready(page, 'genesis', 2)
    assert page.locator('#opv-hfst .mp-label').inner_text() == 'Genesis 2'
    assert page.evaluate('window.__readerDocument') == 'blijft-bewaard'
    assert documents == []
    assert page.locator('html').get_attribute('data-theme') == 'donker'
    page.evaluate('Navigation.navigateRelative(1)')
    page.wait_for_url('**/bijbel/genesis/3.html')
    ready(page, 'genesis', 3)
    page.evaluate("Navigation.navigateChapter('johannes',1)")
    page.wait_for_url('**/bijbel/johannes/1.html')
    ready(page, 'johannes', 1)
    assert page.locator('link[rel="canonical"]').get_attribute('href') == site + '/bijbel/johannes/1.html'
    page.go_back()
    ready(page, 'genesis', 3)
    page.go_forward()
    ready(page, 'johannes', 1)
    assert page.evaluate('window.__readerDocument') == 'blijft-bewaard'
    assert documents == []


def test_trage_beeldindex_maakt_de_voorgeladen_tekst_niet_leeg(browser, site):
    page = page_for(browser, site)
    page.add_init_script("""window.__blankReads=0; let hadText=false;
        new MutationObserver(() => {
            const holder=document.getElementById('verses-container');
            const hasText=!!holder?.querySelector('.verse-row');
            if(hadText && holder && !hasText) window.__blankReads++;
            if(hasText) hadText=true;
        }).observe(document,{childList:true,subtree:true});""")
    def delayed(route):
        time.sleep(.8)
        route.continue_()
    page.context.route('**/data/book-images.json', delayed)
    page.goto(site + '/bijbel/genesis/1.html', wait_until='networkidle')
    ready(page, 'genesis', 1)
    assert page.evaluate('window.__blankReads') == 0


def test_startlink_versanker_en_boekgrens_blijven_werken(browser, site):
    page = page_for(browser, site)
    page.goto(site + '/index.html#genesis/1/3', wait_until='networkidle')
    ready(page, 'genesis', 1)
    assert page.url.endswith('/bijbel/genesis/1.html#vers-3')
    assert page.evaluate('document.baseURI') == site + '/'
    page.evaluate("Navigation.navigateChapter('genesis',50)")
    ready(page, 'genesis', 50)
    page.evaluate('Navigation.navigateRelative(1)')
    ready(page, 'exodus', 1)


def test_trage_oude_navigatie_overschrijft_het_laatste_hoofdstuk_niet(browser, site):
    page = page_for(browser, site)
    page.goto(site + '/bijbel/genesis/1.html', wait_until='networkidle')
    ready(page, 'genesis', 1)
    page.evaluate("""() => {
        const original=App.renderChapter.bind(App);
        App.renderChapter=async (b,c,opts) => {
            if (c===4) await new Promise(resolve=>setTimeout(resolve,500));
            return original(b,c,opts);
        };
        Navigation.navigateChapter('genesis',4);
        setTimeout(()=>Navigation.navigateChapter('genesis',5),20);
    }""")
    ready(page, 'genesis', 5)
    page.wait_for_timeout(650)
    assert page.locator('#verses-container h1').inner_text() == 'Genesis 5'
    assert page.url.endswith('/bijbel/genesis/5.html')


def test_sneller_hoofdstuk_in_nieuw_boek_krijgt_de_juiste_knoppen(browser, site):
    page = page_for(browser, site)
    page.goto(site + '/bijbel/genesis/1.html', wait_until='networkidle')
    ready(page, 'genesis', 1)
    page.evaluate("""() => {
        const original=DataLoader.loadBook.bind(DataLoader); let delayed=false;
        DataLoader.loadBook=async b => {
            if (b==='johannes' && !delayed) {delayed=true; await new Promise(r=>setTimeout(r,400));}
            return original(b);
        };
        Navigation.navigateChapter('johannes',1);
        setTimeout(()=>Navigation.navigateChapter('johannes',2),20);
    }""")
    ready(page, 'johannes', 2)
    page.wait_for_timeout(550)
    assert page.locator('#chapter-nav button').count() == 21
    assert page.locator('#chapter-nav button.active').inner_text() == '2'
    assert page.locator('#opv-hfst .mp-label').inner_text() == 'Johannes 2'


def test_mislukt_laden_behoudt_tekst_en_biedt_opnieuw_proberen(browser, site):
    page = page_for(browser, site)
    page.goto(site + '/bijbel/genesis/1.html', wait_until='networkidle')
    ready(page, 'genesis', 1)
    page.evaluate("""async () => {
        const original=DataLoader.loadChapter.bind(DataLoader); let failed=false;
        DataLoader.loadChapter=async (b,c) => {
            if(c===4 && !failed) {failed=true; throw new Error('Niet bereikbaar');}
            return original(b,c);
        };
        await Navigation.navigateChapter('genesis',4);
    }""")
    assert page.locator('#verses-container h1').inner_text() == 'Genesis 1'
    assert page.url.endswith('/bijbel/genesis/1.html')
    page.locator('#chapter-load-error button').click()
    ready(page, 'genesis', 4)


def test_doorlopend_laden_van_vorig_boek_verandert_nieuwe_lezer_niet(browser, site):
    page = page_for(browser, site)
    page.goto(site + '/bijbel/genesis/1.html', wait_until='networkidle')
    ready(page, 'genesis', 1)
    page.evaluate("""async () => {
        localStorage.setItem('doorlopend','true');
        App._afterRenderContinuous=(append,prepend) => {
            if(!append && !prepend) {
                App._contLast=App._contFirst={bookId:Navigation.currentBook,chapterNum:Navigation.currentChapter};
                App._contLoading=false;
            }
        };
        App._afterRenderContinuous(false,false);
        const original=DataLoader.loadChapter.bind(DataLoader);
        DataLoader.loadChapter=async(b,c) => {
            if(b==='genesis' && c===2) await new Promise(r=>setTimeout(r,500));
            return original(b,c);
        };
        const pending=App._loadNextContinuous();
        await Navigation.navigateChapter('johannes',1);
        await pending;
    }""")
    ready(page, 'johannes', 1)
    assert page.evaluate('App._contLast') == {'bookId':'johannes','chapterNum':1}
    assert page.locator('.verse-row[data-book="genesis"]').count() == 0
