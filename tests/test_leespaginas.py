"""Publieke hoofdstukken blijven leesbaar en vindbaar zonder JavaScript."""
import importlib.util
import json
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
    assert len(urls) == len(set(urls)) == 9
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
        assert f'<figure class="opw-hoofdstukbeeld"><img src="{image_path}"' in html
        assert f'<meta property="og:image" content="https://open-parafrase-weergave.nl{image_path}">' in html
        assert ('alt="Het volk"' if number == 1 else f'alt="Illustratie bij Exodus {number}:') in html
