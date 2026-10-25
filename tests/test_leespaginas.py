"""Publieke hoofdstukken blijven leesbaar en vindbaar zonder JavaScript."""
import importlib.util
import json
import re
from pathlib import Path
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[1]


def builder():
    spec = importlib.util.spec_from_file_location("leespaginas", ROOT / "scripts/build_leespaginas.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def fixture_site(tmp_path):
    (tmp_path / "index.html").write_text((ROOT / "index.html").read_text(encoding="utf-8"), encoding="utf-8")
    books = [
        {"id": "genesis", "nameDutch": "Genesis", "testament": "OT"},
        {"id": "johannes", "nameDutch": "Johannes", "testament": "NT"},
    ]
    (tmp_path / "data").mkdir()
    (tmp_path / "data/books.json").write_text(json.dumps({"books": books}), encoding="utf-8")
    edition = tmp_path / "data/vertalingen/nl-opv"
    edition.mkdir(parents=True)
    (edition.parent / "manifest.json").write_text(json.dumps({"edities": [
        {"code": "nl-opv", "boeken": ["genesis", "johannes"]}
    ]}), encoding="utf-8")
    for book, chapter, text in [
        ("genesis", 1, "In het begin. Daarna was er licht!"),
        ("genesis", 2, 'Een tuin met <bomen> & water. Hij rustte.'),
        ("johannes", 1, "In het begin was het Woord er al."),
    ]:
        folder = edition / book
        folder.mkdir(exist_ok=True)
        (folder / f"{chapter}.json").write_text(json.dumps({
            "boek": book, "hoofdstuk": chapter, "kop": "Het begin",
            "blokken": [{"vers": 1, "tekst": "Een nieuw begin"}],
            "verzen": [{"nummer": 1, "tekst": text}],
        }), encoding="utf-8")
    scenes = {book: [{"chapter": 1, "file": "1.webp", "alt": "Een begin", "scene": "Begin"}]
              for book in ("genesis", "johannes")}
    (tmp_path / "data/book-images.json").write_text(json.dumps({"books": scenes}), encoding="utf-8")
    for book in scenes:
        folder = tmp_path / "images/boekseries" / book
        folder.mkdir(parents=True)
        (folder / "1.webp").write_bytes(b"fixture")
    return tmp_path


def test_volledige_tekst_metadata_en_navigatie(tmp_path):
    root = fixture_site(tmp_path)
    result = builder().build_site(root)
    assert result == {"boeken": 2, "hoofdstukken": 3}
    first = (root / "bijbel/genesis/1.html").read_text(encoding="utf-8")
    assert "In het begin.<br>Daarna was er licht!" in first
    assert '<link rel="canonical" href="https://open-parafrase-weergave.nl/bijbel/genesis/1.html">' in first
    assert 'href="/bijbel/genesis/2.html" rel="next"' in first
    assert 'id="vers-1"' in first
    assert '<h1 class="opv-titel" id="hoofdstuk-titel">Genesis 1</h1>' in first
    assert '<p class="opv-hoofdstuktitel opw-hoofdstuktitel">Het begin</p>' in first
    assert "Proeftekst" in first
    assert '<base href="/">' in first
    assert 'id="sidebar-right"' in first
    assert 'js/app.js' in first
    assert '/js/reading-support.js?v=5' in first
    assert '/js/reading-details.js?v=8' in first
    assert 'Lees met instellingen' not in first
    assert 'Lezer met instellingen' not in first
    assert 'type="application/ld+json"' in first
    second = (root / "bijbel/genesis/2.html").read_text(encoding="utf-8")
    assert '&lt;bomen&gt; &amp; water' in second
    assert 'href="/bijbel/johannes/1.html" rel="next"' in second
    assert 'href="/bijbel/genesis/1.html" rel="prev"' in second
    plain = (root / "bijbel/genesis/2.txt").read_text(encoding="utf-8")
    assert 'Een tuin met <bomen> & water. Hij rustte.' in plain
    assert 'href="/bijbel/genesis/"' in (root / "bijbel/index.html").read_text(encoding="utf-8")


def test_sitemap_en_ai_ingangen_volgen_de_beschikbare_tekst(tmp_path):
    root = fixture_site(tmp_path)
    module = builder()
    module.build_site(root)
    sitemap = ET.parse(root / "sitemap.xml")
    urls = [el.text for el in sitemap.findall(".//{*}loc")]
    assert len(urls) == len(set(urls)) == 10
    assert "https://open-parafrase-weergave.nl/woordenboek.html" in urls
    assert all("#" not in url for url in urls)
    assert "https://open-parafrase-weergave.nl/bijbel/johannes/1.html" in urls
    guide = (root / "llms.txt").read_text(encoding="utf-8")
    assert "2 boeken" in guide and "3 hoofdstukken" in guide
    assert "concept" in guide and "publiek domein" in guide
    assert "vergelijkingskolom" not in guide
    assert (root / "LLM.txt").read_text(encoding="utf-8") == guide
    assert "In het begin was het Woord er al." in (root / "llms-full.txt").read_text(encoding="utf-8")
    before = (root / "sitemap.xml").read_bytes()
    module.build_site(root)
    assert (root / "sitemap.xml").read_bytes() == before


def test_boekvolgorde_is_niet_de_importvolgorde(tmp_path):
    root = fixture_site(tmp_path)
    path = root / "data/books.json"
    data = json.loads(path.read_text(encoding="utf-8"))
    data["books"].reverse()
    path.write_text(json.dumps(data), encoding="utf-8")
    assert [book["id"] for book in builder().catalog(root)] == ["genesis", "johannes"]


def test_hoofdstukkaartjes_tonen_hun_eigen_beelden_en_behouden_de_leesserie(tmp_path):
    root = fixture_site(tmp_path)
    path = root / "data/book-images.json"
    images = json.loads(path.read_text(encoding="utf-8"))
    for suffix in ("land", "dieren"):
        images["books"]["genesis"].append({"chapter": 1, "file": f"1-{suffix}.webp",
            "alt": suffix, "scene": suffix})
        (root / f"images/boekseries/genesis/1-{suffix}.webp").write_bytes(b"fixture")
    path.write_text(json.dumps(images), encoding="utf-8")
    legacy = root / "images/hoofdstukken/genesis"
    legacy.mkdir(parents=True)
    (legacy / "2.webp").write_bytes(b"fixture")
    builder().build_site(root)
    overview = (root / "bijbel/genesis/index.html").read_text(encoding="utf-8")
    cards = overview.split('<ol class="opw-hoofdstukken">', 1)[1].split("</ol>", 1)[0]
    for chapter, image in ((1, "/images/boekseries/genesis/1.webp"),
                           (2, "/images/hoofdstukken/genesis/2.webp")):
        card = re.search(f'<a href="/bijbel/genesis/{chapter}.html">(.*?)</a>', cards).group(1)
        assert f'src="{image}"' in card
        assert 'class="opw-hoofdstukpreview"' in card
        assert 'loading="lazy"' in card
    reading = (root / "bijbel/genesis/1.html").read_text(encoding="utf-8")
    for image in ("1.webp", "1-land.webp", "1-dieren.webp"):
        assert f'src="/images/boekseries/genesis/{image}"' in reading


def test_hoofdstuk_zonder_eigen_beeld_krijgt_geen_onjuiste_afbeelding(tmp_path):
    root = fixture_site(tmp_path)
    builder().build_site(root)
    overview = (root / "bijbel/genesis/index.html").read_text(encoding="utf-8")
    cards = overview.split('<ol class="opw-hoofdstukken">', 1)[1].split("</ol>", 1)[0]
    second = re.search('<a href="/bijbel/genesis/2.html">(.*?)</a>', cards).group(1)
    assert "<img" not in second
    assert "Hoofdstuk 2" in second


def test_boekbeeld_vult_hoofdstukken_zonder_eigen_scenebeeld_aan(tmp_path):
    root = fixture_site(tmp_path)
    cover = root / "images/boeken/genesis.webp"
    cover.parent.mkdir(parents=True)
    cover.write_bytes(b"fixture")
    builder().build_site(root)
    overview = (root / "bijbel/genesis/index.html").read_text(encoding="utf-8")
    cards = overview.split('<ol class="opw-hoofdstukken">', 1)[1].split("</ol>", 1)[0]
    first = re.search('<a href="/bijbel/genesis/1.html">(.*?)</a>', cards).group(1)
    second = re.search('<a href="/bijbel/genesis/2.html">(.*?)</a>', cards).group(1)
    assert 'src="/images/boekseries/genesis/1.webp"' in first
    assert 'src="/images/boeken/genesis.webp"' in second
    reading = (root / "bijbel/genesis/2.html").read_text(encoding="utf-8")
    assert 'src="/images/boeken/genesis.webp"' in reading
    assert "Boekbeeld bij Genesis" in reading


def test_citaatopmaak_en_zinsregels_blijven_behouden():
    rendered = builder().verse_html({
        "tekst": "God zei: Licht! Het werd licht. Toen begon de dag.",
        "html": 'God zei: <span class="god-speaks" onclick="onveilig()"><i>Licht!</i></span> Het werd licht. Toen begon de dag.',
    })
    assert '<span class="god-speaks"><i>Licht!</i></span><br>Het werd licht.<br>Toen begon de dag.<br>' in rendered
    assert 'onclick' not in rendered


def test_exodus_heeft_hoofdstukbeeld_in_tekst_en_deelvoorbeeld(tmp_path):
    root = fixture_site(tmp_path)
    books_path = root / 'data/books.json'
    books = json.loads(books_path.read_text(encoding='utf-8'))
    books['books'].append({'id': 'exodus', 'nameDutch': 'Exodus', 'testament': 'OT'})
    books_path.write_text(json.dumps(books), encoding='utf-8')
    manifest_path = root / 'data/vertalingen/manifest.json'
    manifest = json.loads(manifest_path.read_text(encoding='utf-8'))
    manifest['edities'][0]['boeken'].append('exodus')
    manifest_path.write_text(json.dumps(manifest), encoding='utf-8')
    folder = root / 'data/vertalingen/nl-opv/exodus'
    folder.mkdir()
    for number in (1, 40):
        (folder / f'{number}.json').write_text(json.dumps({
            'boek': 'exodus', 'hoofdstuk': number, 'kop': 'Het volk en de tabernakel',
            'verzen': [{'nummer': 1, 'tekst': 'De HEERE sprak tot Mozes.'}],
        }), encoding='utf-8')
    image_manifest = root / "data/book-images.json"
    images = json.loads(image_manifest.read_text(encoding="utf-8"))
    images["books"]["exodus"] = [{"chapter": 1, "file": "1.webp", "alt": "Het volk", "scene": "Het volk"}]
    image_manifest.write_text(json.dumps(images), encoding="utf-8")
    series = root / "images/boekseries/exodus"
    series.mkdir(parents=True)
    (series / "1.webp").write_bytes(b"fixture")
    legacy = root / "images/hoofdstukken/exodus"
    legacy.mkdir(parents=True)
    (legacy / "40.webp").write_bytes(b"fixture")
    builder().build_site(root)
    for number in (1, 40):
        html = (root / f'bijbel/exodus/{number}.html').read_text(encoding='utf-8')
        image_path = f"/images/{'boekseries' if number == 1 else 'hoofdstukken'}/exodus/{number}.webp"
        assert f'<figure class="opw-hoofdstukbeeld opw-sidecar-item is-active"><img src="{image_path}"' in html
        assert f'<meta property="og:image" content="https://open-parafrase-weergave.nl{image_path}">' in html
        assert ('alt="Het volk"' if number == 1 else f'alt="Illustratie bij Exodus {number}:') in html


def test_markdown_en_achtergrondpagina(tmp_path):
    site = fixture_site(tmp_path)
    (site / "achtergrond.md").write_text("# Achtergrond\n\n> Kort.\n\n## Kop\n\nTekst met [link](https://openvertaling.nl/).\n\n- **Bron**: punt\n", encoding="utf-8")
    (site / "data/reading-dictionary.json").write_text(json.dumps({"status": "concept", "note": "", "terms": [
        {"woord": "Verbond", "categorie": "begrip", "betekenissen": [{"uitleg": "Een plechtige afspraak.", "ref": "Gen 9:9"}]},
    ]}), encoding="utf-8")
    builder().build_site(site)
    genesis = (site / "markdown/opv/genesis.md").read_text(encoding="utf-8")
    assert "## Genesis 1: Het begin" in genesis and "### Een nieuw begin" in genesis
    assert "**1** In het begin. Daarna was er licht!" in genesis
    assert r"**1** Een tuin met \<bomen\> & water. Hij rustte." in genesis
    volledig = (site / "markdown/opv-volledig.md").read_text(encoding="utf-8")
    assert "## Genesis" in volledig and "### Genesis 1: Het begin" in volledig and "#### Een nieuw begin" in volledig
    assert "https://open-parafrase-weergave.nl/markdown/opv/johannes.md" in (site / "markdown/index.md").read_text(encoding="utf-8")
    assert "- Een plechtige afspraak. (Gen 9:9)" in (site / "markdown/woordenboek.md").read_text(encoding="utf-8")
    pagina = (site / "achtergrond.html").read_text(encoding="utf-8")
    assert '<link rel="canonical" href="https://open-parafrase-weergave.nl/achtergrond.html">' in pagina
    assert '<a href="https://openvertaling.nl/">link</a>' in pagina and "<li><strong>Bron</strong>: punt</li>" in pagina
    guide = (site / "llms.txt").read_text(encoding="utf-8")
    assert "https://open-parafrase-weergave.nl/markdown/index.md" in guide and "/achtergrond.md" in guide
    assert "https://open-parafrase-weergave.nl/achtergrond.html" in (site / "sitemap.xml").read_text(encoding="utf-8")
