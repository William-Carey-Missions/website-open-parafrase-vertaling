#!/usr/bin/env python3
"""Bouw publieke leespagina's, tekstbestanden, AI-ingangen en sitemap uit nl-opv."""
from __future__ import annotations

import argparse
from html import escape
from html.parser import HTMLParser
import json
from pathlib import Path
import re
from xml.sax.saxutils import escape as xml_escape

ROOT = Path(__file__).resolve().parents[1]
BASE = "https://open-parafrase-weergave.nl"
NAME = "Open Parafrase Weergave"
GROUPS = {"OT": "Oude Testament", "NT": "Nieuwe Testament",
          "AP": "Apocriefe boeken", "ET": "Ethiopische boeken"}
IMAGE = "/images/psalm-23-herder.webp"
BOOK_ORDER = """genesis exodus leviticus numeri deuteronomium jozua richteren ruth
1samuel 2samuel 1koningen 2koningen 1kronieken 2kronieken ezra nehemia esther
job psalmen spreuken prediker hooglied jesaja jeremia klaagliederen ezechiel daniel
hosea joel amos obadja jona micha nahum habakuk zefanja haggai zacharia maleachi
mattheus markus lukas johannes handelingen romeinen 1korinthiers 2korinthiers
galaten efeziers filippenzen kolossenzen 1tessalonicensen 2tessalonicensen
1timotheus 2timotheus titus filemon hebreeen jakobus 1petrus 2petrus 1johannes
2johannes 3johannes judas openbaring
3ezra 4ezra tobit judith boekderwijsheid jezussirach baruch estherapocrief
gebedvanazaria gezangindevuuroven susanna belenddedraak gebedvanmanasse
1makkabeeen 2makkabeeen 3makkabeeen henoch jubileeen 1meqabyan 2meqabyan 3meqabyan 4baruch""".split()


def write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="\n") as output:
        output.write(text)


def catalog(root: Path) -> list[dict]:
    manifest = json.loads((root / "data/vertalingen/manifest.json").read_text(encoding="utf-8"))
    published = set(next(e["boeken"] for e in manifest["edities"] if e["code"] == "nl-opv"))
    books = json.loads((root / "data/books.json").read_text(encoding="utf-8"))["books"]
    result = []
    for book in books:
        if book["id"] not in published:
            continue
        folder = root / "data/vertalingen/nl-opv" / book["id"]
        files = sorted((p for p in folder.glob("*.json") if p.stem.isdigit()), key=lambda p: int(p.stem))
        if not files:
            raise ValueError(f"Geen leeseditie voor {book['id']}")
        chapters = [json.loads(path.read_text(encoding="utf-8")) for path in files]
        if any(not chapter.get("verzen") for chapter in chapters):
            raise ValueError(f"Leeg hoofdstuk in {book['id']}")
        result.append({**book, "chapters": chapters})
    if len(result) != len(published):
        raise ValueError("Niet alle gepubliceerde boeken staan in de boekencatalogus")
    order = {book_id: index for index, book_id in enumerate(BOOK_ORDER)}
    return sorted(result, key=lambda book: (order.get(book["id"], len(order)), book["id"]))


def chapter_path(book: dict, chapter: dict) -> str:
    return f"/bijbel/{book['id']}/{chapter['hoofdstuk']}.html"


def book_cover(book_id: str, book_images: dict) -> str:
    scenes = book_images.get(book_id)
    return (f"/images/boekseries/{book_id}/{scenes[0]['file']}" if scenes
            else f"/images/boeken/{book_id}.webp")


def schema_json(value: dict) -> str:
    return json.dumps(value, ensure_ascii=False, separators=(",", ":")).replace("<", "\\u003c")


def page(title: str, description: str, path: str, body: str, crumbs: list[tuple[str, str]],
         creative_work: dict | None = None, text_path: str | None = None,
         reader_path: str = "/bijbel/johannes/1.html", image: str = IMAGE,
         image_alt: str = "Een herder met schapen bij stil water, illustratie bij Psalm 23") -> str:
    graph = [{"@type": "WebPage", "@id": BASE + path, "url": BASE + path,
              "name": title, "description": description, "inLanguage": "nl-NL",
              "isPartOf": {"@id": BASE + "/#website"}},
             {"@type": "BreadcrumbList", "itemListElement": [
                 {"@type": "ListItem", "position": i, "name": name, "item": BASE + url}
                 for i, (name, url) in enumerate(crumbs, 1)]}]
    if creative_work:
        graph.append(creative_work)
    alternate = (f'<link rel="alternate" type="text/plain" href="{escape(text_path)}" title="Platte tekst">'
                 if text_path else "")
    breadcrumb = " <span aria-hidden=\"true\">/</span> ".join(
        f'<a href="{escape(url)}">{escape(name)}</a>' for name, url in crumbs[:-1])
    breadcrumb += f' <span aria-hidden="true">/</span> <span aria-current="page">{escape(crumbs[-1][0])}</span>'
    return f'''<!DOCTYPE html>
<html lang="nl">
<head>
<base href="/">
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{escape(title)} | {NAME}</title>
<meta name="description" content="{escape(description, quote=True)}">
<meta name="robots" content="index, follow, max-image-preview:large">
<link rel="canonical" href="{BASE}{escape(path)}">
<link rel="icon" type="image/svg+xml" href="/favicon.svg">
<link rel="manifest" href="/manifest.json">
<link rel="alternate" type="text/plain" href="/llms.txt" title="Informatie voor AI en hergebruik">
{alternate}
<meta name="theme-color" content="#142e42">
<meta property="og:type" content="{'article' if creative_work else 'website'}">
<meta property="og:site_name" content="{NAME}">
<meta property="og:locale" content="nl_NL">
<meta property="og:title" content="{escape(title, quote=True)}">
<meta property="og:description" content="{escape(description, quote=True)}">
<meta property="og:url" content="{BASE}{escape(path)}">
<meta property="og:image" content="{BASE}{escape(image, quote=True)}">
<meta property="og:image:alt" content="{escape(image_alt, quote=True)}">
<meta name="twitter:card" content="summary_large_image">
<meta name="twitter:title" content="{escape(title, quote=True)}">
<meta name="twitter:description" content="{escape(description, quote=True)}">
<meta name="twitter:image" content="{BASE}{escape(image, quote=True)}">
<meta name="twitter:image:alt" content="{escape(image_alt, quote=True)}">
<script type="application/ld+json">{schema_json({'@context': 'https://schema.org', '@graph': graph})}</script>
<script src="/js/theme.js"></script>
<script src="/js/sites.js" defer></script>
<link rel="stylesheet" href="/css/fonts.css">
<link rel="stylesheet" href="/css/style.css">
<link rel="stylesheet" href="/css/opv.css?v=1.0.5">
<link rel="stylesheet" href="/css/leespaginas.css?v=1.0.2">
</head>
<body class="opw-statisch">
<a class="opw-skip" href="{escape(path)}#inhoud">Direct naar de inhoud</a>
<header class="opw-sitekop" id="topnav">
<a class="opv-merk" href="/"><span class="opv-merk-naam">{NAME}<small>Gods Woord in begrijpelijke taal</small></span></a>
<nav aria-label="Hoofdmenu"><a href="/bijbel/">Alle boeken</a><a href="{escape(reader_path)}">Lezen</a><a href="/over-opv.html">Over OPW</a></nav>
</header>
<script src="/js/topnav.js?v=0.38.7"></script>
<main class="opv-pagina" id="inhoud" tabindex="-1">
<nav class="opw-kruimels" aria-label="Broodkruimelpad">{breadcrumb}</nav>
{body}
</main>
<footer class="opv-voet"><span class="opv-ark">de kleine ark</span>
<nav aria-label="Meer informatie"><a href="/bijbel/">Alle Bijbelboeken</a><a href="/over-opv.html#status">Over de proeftekst</a><a href="/llms.txt">AI en hergebruik</a><a href="https://openvertaling.nl/" data-ov-href="">Open Vertaling</a><a href="https://opengodsword.com/wiki.html" data-ogw-href="wiki.html">Achtergrond</a></nav>
<span>Bijbeltekst: publiek domein · proefversie</span></footer>
</body>
</html>
'''


def sentence_lines(text: str) -> str:
    return re.sub(r'([.!?…][”’"\')\]]*)\s+(?=\S)', r'\1<br>', escape(text, quote=False))


class CitationHTML(HTMLParser):
    """Bewaar uitsluitend de bekende inline citaatopmaak van de leeseditie."""
    def __init__(self):
        super().__init__()
        self.parts = []
        self.stack = []

    def handle_starttag(self, tag, attrs):
        if tag not in ("span", "i", "em", "strong"):
            self.stack.append((tag, False))
            return
        classes = dict(attrs).get("class", "").split()
        allowed = [name for name in classes if name in (
            "god-speaks", "direct-speech", "angel-speaks", "devil-speaks", "nested-quote")]
        attribute = f' class="{" ".join(allowed)}"' if allowed else ""
        self.parts.append(f"<{tag}{attribute}>")
        self.stack.append((tag, True))

    def handle_endtag(self, tag):
        if self.stack and self.stack[-1][0] == tag:
            _, allowed = self.stack.pop()
            if allowed:
                self.parts.append(f"</{tag}>")

    def handle_data(self, text):
        self.parts.append(escape(text, quote=False))


def verse_html(verse: dict) -> str:
    if not verse.get("html"):
        html = sentence_lines(verse["tekst"])
    else:
        parser = CitationHTML()
        parser.feed(verse["html"])
        html = "".join(parser.parts)
        html = re.sub(r'([.!?…](?:[”’"\')\]]|</(?:span|i|em|strong)>)*\s*)\s+(?=\S)',
                      lambda match: match[1].rstrip() + "<br>", html)
    if re.search(r'[.!?…][”’"\')\]]*\s*$', verse["tekst"]):
        html += "<br>"
    return html


def reading_image(book_id: str, scene: dict) -> str:
    anchor = f' data-verse="{int(scene["verse"])}"' if scene.get("verse") else ""
    return (f'<figure class="opw-hoofdstukbeeld"{anchor}>'
            f'<img src="/images/boekseries/{book_id}/{escape(scene["file"], quote=True)}" '
            f'width="1536" height="1024" alt="{escape(scene["alt"], quote=True)}" loading="lazy">'
            f'<figcaption>{escape(scene["scene"])}</figcaption></figure>')


def integrated_reader(template: str, document: str, path: str) -> str:
    """Gebruik dezelfde lezer, met vooraf gerenderde tekst als eerste weergave."""
    head = document.split("</head>", 1)[0]
    content = re.search(r'<main class="opv-pagina"[^>]*>(.*?)</main>', document, re.S).group(1)
    content = re.sub(r'<nav class="opw-kruimels"[^>]*>.*?</nav>', '', content, flags=re.S)
    body = re.search(r'<body[^>]*>(.*?)</body>', template, re.S).group(1)
    body = re.sub(r'<section id="opv-start"[^>]*>.*?</section>', '', body, flags=re.S)
    placeholder = '<div id="verses-container"></div>'
    if placeholder not in body:
        raise ValueError("De gedeelde lezer mist zijn teksthouder")
    body = body.replace(placeholder, f'<div id="verses-container">{content}</div>', 1)
    body = body.replace('<main id="content">', '<main id="content" tabindex="-1">', 1)
    skip = f'<a class="opw-skip" href="{path}#content" onclick="event.preventDefault();document.getElementById(\'content\').focus();document.getElementById(\'content\').scrollIntoView()">Direct naar de inhoud</a>'
    return head + '''<link rel="stylesheet" href="/css/verification.css">
<link rel="stylesheet" href="/css/verwijzing-popup.css">
<link rel="stylesheet" href="/css/print.css" media="print">
<script src="/js/reading-support.js?v=1" defer></script>
<noscript><style>#mobile-footer-nav,#chapter-footer,.chapter-swipe-nav {display:none!important}</style></noscript>
</head><body class="opv-lezerpagina opw-hoofdstukpagina">''' + skip + body + '</body></html>\n'


def build_site(root: Path = ROOT) -> dict:
    books = catalog(root)
    book_images = json.loads((root / "data/book-images.json").read_text(encoding="utf-8"))["books"]
    catalog_by_id = {book["id"]: book for book in books}
    if set(book_images) != set(catalog_by_id):
        missing = sorted(set(catalog_by_id) - set(book_images))
        unexpected = sorted(set(book_images) - set(catalog_by_id))
        raise ValueError(f"Boekbeelden ontbreken of horen niet bij een gepubliceerd boek: {missing=}, {unexpected=}")
    for book_id, scenes in book_images.items():
        if not scenes or len({scene["file"] for scene in scenes}) != len(scenes):
            raise ValueError(f"Boekbeelden ontbreken of bestandsnamen zijn dubbel voor {book_id}")
        chapters = {chapter["hoofdstuk"] for chapter in catalog_by_id[book_id]["chapters"]}
        chapter_counts = {chapter: sum(scene["chapter"] == chapter for scene in scenes) for chapter in chapters}
        if any(count > 3 for count in chapter_counts.values()):
            raise ValueError(f"Meer dan drie beelden in een hoofdstuk van {book_id}")
        for scene in scenes:
            if scene["chapter"] not in chapters:
                raise ValueError(f"Geen gepubliceerd hoofdstuk voor boekbeeld: {book_id} {scene['chapter']}")
            if not (root / f"images/boekseries/{book_id}/{scene['file']}").is_file():
                raise ValueError(f"Ontbrekend boekbeeld: {book_id} {scene['file']}")
    reader_template = (root / "index.html").read_text(encoding="utf-8")
    sequence = [(book, chapter) for book in books for chapter in book["chapters"]]
    # De bron heeft geen publicatiedatum: checkouttijd is geen inhoudswijziging.
    # Daarom geen verzonnen lastmod-datums in de sitemap.
    urls = [("/", None), ("/over-opv.html", None), ("/bijbel/", None), ("/woordenboek.html", None)]
    guide = f'''# {NAME} — de Bijbel in eenvoudig Nederlands

> Gods Woord in begrijpelijke taal. Nederlandse parafrase van de Bijbel. Proefversie: alle verzen hebben de status concept. De Bijbeltekst is publiek domein.

Er zijn {len(books)} boeken en {len(sequence)} hoofdstukken beschikbaar. De collectie omvat het Oude en Nieuwe Testament en daarnaast apocriefe en Ethiopische boeken. Die aanvullende boeken behoren niet in alle tradities tot de Bijbelcanon.

## Lezen en vinden
- [Alle Bijbelboeken]({BASE}/bijbel/): boekenoverzicht met links naar ieder hoofdstuk; volledig leesbaar zonder JavaScript.
- [Woordenboek]({BASE}/woordenboek.html): bestaande begrippenverklaringen, met conceptstatus.
- [Over de weergave]({BASE}/over-opv.html): doelgroep, bronbeleid, proefstatus en hergebruik.
- [Volledige tekst]({BASE}/llms-full.txt): alle beschikbare hoofdstukken als UTF-8-tekst; groot bestand.
- [Sitemap]({BASE}/sitemap.xml): canonieke HTML-adressen van boeken en hoofdstukken.

## Bronvermelding en gebruik
Noem de tekst "Open Parafrase Weergave (proef)". Vermeld boek, hoofdstuk en waar nodig vers. Dit is een parafrase en geen woordelijke vertaling uit de grondtekst. Presenteer de proeftekst niet als onafhankelijk door mensen goedgekeurd. De tekst is vrij te gebruiken, te kopiëren en te verspreiden.

Hoofdstukken staan op `/bijbel/BOEK/NUMMER.html`, met dezelfde tekst als platte tekst op `/bijbel/BOEK/NUMMER.txt`. Een specifiek vers heeft een anker `#vers-NUMMER`. Ieder hoofdstuk bevat direct de tekst en dezelfde leesinstellingen. Oude links op `/index.html#BOEK/NUMMER` verwijzen naar het bijbehorende hoofdstuk. Interne editiecode: `nl-opv`.

## Boeken en tekstbestanden
'''
    full = [f"# {NAME} (proef)\n\nBijbeltekst: publiek domein. Alle verzen: concept.\n"]
    for book in books:
        book_path = f"/bijbel/{book['id']}/"
        urls.append((book_path, None))
        title = book["nameDutch"]
        links = "".join(f'<li><a href="{chapter_path(book, chapter)}">Hoofdstuk {chapter["hoofdstuk"]}<span>{escape(chapter.get("kop", ""))}</span></a></li>' for chapter in book["chapters"])
        scenes = book_images.get(book['id'], [])[:3]
        gallery = ('<section class="opw-boekserie" aria-labelledby="boekserie-titel"><h2 id="boekserie-titel">Beelden bij dit boek</h2><div class="opw-boekserie-grid">' +
                   ''.join(f'<figure><a href="/bijbel/{book["id"]}/{scene["chapter"]}.html"><img src="/images/boekseries/{book["id"]}/{scene["file"]}" width="1536" height="1024" loading="lazy" alt="{escape(scene["alt"], quote=True)}"><span>{escape(title)} {scene["chapter"]}: {escape(scene["scene"])}</span></a></figure>' for scene in scenes) +
                   '</div></section>') if scenes else ''
        cover = book_cover(book['id'], book_images)
        body = f'<div class="opw-boekintro"><div><h1>{escape(title)} in eenvoudig Nederlands</h1><p class="opv-lead">Lees {escape(title)} in de {NAME}. Kies een hoofdstuk om te beginnen.</p><p class="opv-pil">Proeftekst · alle verzen concept</p></div><img class="opw-boekillustratie" src="{cover}" width="1536" height="1024" alt=""></div>{gallery}<ol class="opw-hoofdstukken">{links}</ol>'
        write(root / book_path.strip("/") / "index.html", page(
            f"{title} in eenvoudig Nederlands", f"Lees alle {len(book['chapters'])} hoofdstukken van {title} in de Open Parafrase Weergave. Gratis Bijbeltekst in eenvoudig Nederlands; proefversie.",
            book_path, body, [("Start", "/"), ("Bijbel", "/bijbel/"), (title, book_path)],
            reader_path=chapter_path(book, book['chapters'][0]),
            image=cover, image_alt=f"Beeld bij {title}"))
        guide += f'- [{title}]({BASE}{book_path}): {len(book["chapters"])} hoofdstukken; [platte tekst]({BASE}{book_path}tekst.txt).\n'
        book_text = [f"# {title} — {NAME} (proef)\n\nBijbeltekst: publiek domein.\n"]
        for chapter in book["chapters"]:
            text = f"## {title} {chapter['hoofdstuk']} — {chapter.get('kop', '')}\n\n"
            text += "\n".join(f"{verse['nummer']}. {verse['tekst']}" for verse in chapter["verzen"]) + "\n"
            book_text.append(text)
            full.append(text)
            write(root / book_path.strip("/") / f"{chapter['hoofdstuk']}.txt", f"{NAME} (proef). Bijbeltekst: publiek domein.\n\n{text}")
        write(root / book_path.strip("/") / "tekst.txt", "\n".join(book_text))

    for index, (book, chapter) in enumerate(sequence):
        path = chapter_path(book, chapter)
        number = chapter["hoofdstuk"]
        ref = f"{book['nameDutch']} {number}"
        heading = chapter.get("kop") or ref
        description = f"{ref} in eenvoudig Nederlands. " + " ".join(chapter["verzen"][0]["tekst"].split())
        if len(description) > 170:
            description = description[:166].rsplit(" ", 1)[0] + "…"
        headings = {int(item["vers"]): item["tekst"] for item in chapter.get("blokken", []) if item.get("vers") and item.get("tekst")}
        verses = []
        for verse in chapter["verzen"]:
            if int(verse["nummer"]) in headings:
                verses.append(f'<div class="pericope-heading" role="heading" aria-level="2">{escape(headings[int(verse["nummer"])])}</div>')
            verses.append(f'<div class="verse-row" id="vers-{int(verse["nummer"])}" data-book="{book["id"]}" data-chapter="{number}" data-verse="{int(verse["nummer"])}"><div class="verse-cell col-2026" lang="nl">{verse_html(verse)}</div></div>')
        navigation = []
        for neighbor, relation, label in [(index - 1, "prev", "Vorige"), (index + 1, "next", "Volgende")]:
            if 0 <= neighbor < len(sequence):
                nb, nc = sequence[neighbor]
                navigation.append(f'<a href="{chapter_path(nb, nc)}" rel="{relation}">{label}: {escape(nb["nameDutch"])} {nc["hoofdstuk"]}</a>')
        subtitle = f'<p class="opv-hoofdstuktitel opw-hoofdstuktitel">{escape(heading)}</p>' if heading != ref else ''
        minutes = max(1, int(sum(len(v['tekst'].split()) for v in chapter['verzen']) / 150 + .5))
        read_time = '1 minuut' if minutes == 1 else f'ongeveer {minutes} minuten'
        chapter_images = [scene for scene in book_images.get(book['id'], []) if scene['chapter'] == number]
        legacy_image = f"/images/hoofdstukken/{book['id']}/{number}.webp"
        has_legacy = (root / legacy_image.lstrip('/')).is_file()
        chapter_cover = (f"/images/boekseries/{book['id']}/{chapter_images[0]['file']}" if chapter_images
                         else legacy_image if has_legacy else f"/images/boeken/{book['id']}.webp")
        illustration = ('<aside class="opw-hoofdstukbeelden" aria-label="Beelden en locaties bij dit hoofdstuk">' +
                        ''.join(reading_image(book['id'], scene) for scene in chapter_images) +
                        '</aside>') if chapter_images else ''
        if not chapter_images and has_legacy:
            illustration = (f'<aside class="opw-hoofdstukbeelden" aria-label="Beeld bij dit hoofdstuk">'
                            f'<figure class="opw-hoofdstukbeeld"><img src="{legacy_image}" width="1536" height="1024" '
                            f'alt="Illustratie bij {escape(ref)}: {escape(heading, quote=True)}" loading="lazy"></figure></aside>')
        body = f'''<section class="opw-leesindeling{' heeft-beelden' if illustration else ''}">
<div class="opw-leeskolom"><header class="opv-hoofdstukkop" aria-labelledby="hoofdstuk-titel">
<p class="opv-boven">{escape(GROUPS.get(book['testament'], 'Bijbel'))}</p>
<h1 class="opv-titel" id="hoofdstuk-titel">{escape(ref)}</h1>
{subtitle}
<div class="opv-meta"><span class="opv-pil" title="Alle verzen hebben nog de status concept">Proeftekst</span><span>Gods Woord in begrijpelijke taal · {read_time}</span></div>
</header>
<div class="opw-bijbeltekst">{''.join(verses)}</div></div>
{illustration}
</section>
<nav class="opw-hoofdstuknav" aria-label="Hoofdstukken">{''.join(navigation)}</nav>
<p class="opw-tekstdownload"><a href="{path.removesuffix('.html')}.txt" download>Download hoofdstuk als tekstbestand</a></p>'''
        work = {"@type": "Chapter", "@id": BASE + path + "#hoofdstuk", "name": f"{ref}: {heading}",
                "position": number, "inLanguage": "nl-NL", "isAccessibleForFree": True,
                "creativeWorkStatus": "Concept", "copyrightNotice": "Bijbeltekst: publiek domein",
                "isPartOf": {"@type": "Book", "name": f"{book['nameDutch']} — {NAME}",
                             "url": f"{BASE}/bijbel/{book['id']}/"}}
        document = page(f"{ref} — {heading}", description, path, body,
              [("Start", "/"), ("Bijbel", "/bijbel/"), (book["nameDutch"], f"/bijbel/{book['id']}/"), (ref, path)], work, path.removesuffix(".html") + ".txt",
              reader_path=path,
              image=chapter_cover,
              image_alt=f"Illustratie bij {ref}: {heading}")
        write(root / path.lstrip("/"), integrated_reader(reader_template, document, path))
        urls.append((path, None))

    sections = []
    for group, label in GROUPS.items():
        links = "".join(f'<li><a href="/bijbel/{book["id"]}/"><img class="opw-boekbeeld" src="{book_cover(book["id"], book_images)}" width="1024" height="1024" loading="lazy" decoding="async" alt=""><span class="opw-boeknaam">{escape(book["nameDutch"])}</span><span>{len(book["chapters"])} hoofdstukken</span></a></li>' for book in books if book["testament"] == group)
        if links:
            sections.append(f'<section aria-labelledby="groep-{group}"><h2 id="groep-{group}">{label}</h2><ul class="opw-boeken">{links}</ul></section>')
    body = f'<h1>De Bijbel in eenvoudig Nederlands</h1><p class="opv-lead">Alle {len(books)} boeken en {len(sequence)} hoofdstukken van de {NAME}. Kies een boek en daarna een hoofdstuk.</p><p class="opv-pil">Proeftekst · alle verzen concept</p><p>De apocriefe en Ethiopische boeken staan apart; hun plaats in de Bijbelcanon verschilt per traditie.</p>{"".join(sections)}'
    write(root / "bijbel/index.html", page("Alle Bijbelboeken in eenvoudig Nederlands", f"Lees de Bijbel gratis in eenvoudig Nederlands: {len(books)} boeken en {len(sequence)} hoofdstukken. Open Parafrase Weergave, proefversie.", "/bijbel/", body, [("Start", "/"), ("Bijbel", "/bijbel/")]))
    guide += f'''\n## Verwante bronnen
- [Open Vertaling](https://openvertaling.nl/): voor wie een meer woordelijke weergave wil lezen.
- [Open Gods Woord](https://opengodsword.com/wiki.html): Bijbelachtergrond en broninformatie.
'''
    write(root / "llms.txt", guide)
    write(root / "LLM.txt", guide)
    write(root / "llms-full.txt", "\n".join(full))
    sitemap = ['<?xml version="1.0" encoding="UTF-8"?>', '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">']
    for path, date in urls:
        modified = f"<lastmod>{date}</lastmod>" if date else ""
        sitemap.append(f"  <url><loc>{xml_escape(BASE + path)}</loc>{modified}</url>")
    write(root / "sitemap.xml", "\n".join(sitemap) + "\n</urlset>\n")
    return {"boeken": len(books), "hoofdstukken": len(sequence)}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=ROOT)
    print(json.dumps(build_site(parser.parse_args().root), ensure_ascii=False))
