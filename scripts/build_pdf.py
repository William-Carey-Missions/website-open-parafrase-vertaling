#!/usr/bin/env python3
"""Bouw de volledige OPW-leesuitgave als PDF, zonder kanttekeningen.

Installatie: python -m pip install reportlab 'fonttools[woff]'
Uitvoer is afgeleid van data/ en wordt bij iedere publicatie opnieuw gebouwd.
"""
import argparse
import datetime
import html
import io
import json
import re
from pathlib import Path

from fontTools.ttLib import TTFont as SourceFont
from reportlab.lib import colors
from reportlab.lib.pagesizes import A5
from reportlab.lib.styles import ParagraphStyle
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, PageBreak


ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / 'downloads/open-parafrase-weergave.pdf'


def fonts(root=ROOT):
    """Gebruik dezelfde vrij beschikbare letter als de website, ingebed in de PDF."""
    glyphs = None
    for name, filename in [('OV', 'eb-garamond-400.woff2'), ('OVBold', 'eb-garamond-600.woff2'), ('Hebrew', 'noto-serif-hebrew.woff2')]:
        source = SourceFont(root / 'fonts' / filename)
        glyphs = set(source.getBestCmap()) if glyphs is None else glyphs | set(source.getBestCmap())
        source.flavor = None
        buffer = io.BytesIO()
        source.save(buffer)
        buffer.seek(0)
        pdfmetrics.registerFont(TTFont(name, buffer))
    pdfmetrics.registerFontFamily('OV', normal='OV', bold='OVBold')
    return glyphs


class Heading(Paragraph):
    def __init__(self, text, style, key, level):
        super().__init__(html.escape(text), style)
        self.key, self.level, self.title = key, level, text

    def draw(self):
        self.canv.bookmarkPage(self.key)
        self.canv.addOutlineEntry(self.title, self.key, self.level, False)
        self.canv.current_heading = self.title
        super().draw()


def build_pdf(books, output=OUTPUT, root=ROOT):
    if any(book['testament'] not in ('OT', 'NT', 'AP') for book in books):
        raise ValueError('Alleen openbare boeken mogen worden geëxporteerd')
    glyphs = fonts(root)
    selected = []
    counts = dict(boeken=0, hoofdstukken=0, verzen=0)
    missing = set()
    for book in books:
        chapters = []
        for source in book['chapters']:
            nr = source['hoofdstuk']
            verses = [(v['nummer'], v['tekst']) for v in source['verzen']]
            if any(not text for _, text in verses):
                raise ValueError(f"Leeg vers in {book['id']} {nr}")
            for _, text in verses:
                missing.update(ord(c) for c in text if not c.isspace() and ord(c) not in glyphs)
            chapters.append((nr, verses))
            counts['verzen'] += len(verses)
        if chapters:
            selected.append((book, chapters))
            counts['hoofdstukken'] += len(chapters)
    counts['boeken'] = len(selected)
    if missing:
        raise ValueError('Ontbrekende lettertekens: ' + ', '.join(f'U+{n:04X}' for n in sorted(missing)))
    if counts['boeken'] != 82:
        raise ValueError(f"Verwacht 82 openbare boeken, gevonden {counts['boeken']}")

    ink = colors.HexColor('#143247')
    body = ParagraphStyle('body', fontName='OV', fontSize=11, leading=14.5, spaceAfter=3)
    title = ParagraphStyle('title', parent=body, fontName='OVBold', fontSize=34, leading=39, textColor=ink, spaceAfter=20)
    bookstyle = ParagraphStyle('book', parent=body, fontName='OVBold', fontSize=26, leading=32, textColor=ink, spaceAfter=24, keepWithNext=True)
    chapterstyle = ParagraphStyle('chapter', parent=body, fontName='OVBold', fontSize=16, leading=22, spaceBefore=14, spaceAfter=8, keepWithNext=True)
    small = ParagraphStyle('small', parent=body, fontSize=10, leading=14, spaceAfter=10)
    contents = ParagraphStyle('contents', parent=small, spaceAfter=2, leading=14)
    date = datetime.date.today().isoformat()
    version = 'proef; alle verzen concept'
    story = [Spacer(1, 70), Paragraph('Open Parafrase Weergave', title), Paragraph('Volledige leesuitgave', bookstyle),
             Paragraph('Parafrase in eenvoudig Nederlands. Proefversie: alle verzen concept, nog niet door mensen goedgekeurd.', body), Spacer(1, 24),
             Paragraph(f"{counts['boeken']} boeken · {counts['hoofdstukken']} hoofdstukken · {counts['verzen']} verzen", small),
             Paragraph(f'Uitgave {html.escape(version)} · {date}', small),
             Paragraph('Zonder kanttekeningen en afbeeldingen.', small), PageBreak(),
             Paragraph('Over deze uitgave', bookstyle),
             Paragraph('Deze PDF bevat alle beschikbare hoofdstukken van de 82 openbare boeken van de Open Parafrase Weergave, inclusief de apocriefe boeken. Alle verzen hebben de status concept en zijn nog niet door mensen goedgekeurd. Dit is een parafrase. De plaats van aanvullende boeken in de Bijbelcanon verschilt per traditie.', body),
             Spacer(1, 12), Paragraph('CC0 / publiek domein', chapterstyle),
             Paragraph('De Bijbeltekst mag vrij worden gebruikt, gekopieerd, bewerkt en verspreid, voor elk doel. Bronvermelding is niet verplicht. Deze PDF bevat geen extern beeldmateriaal.', body),
             Paragraph('Voorgestelde bronvermelding: Open Parafrase Weergave (proef), boek hoofdstuk:vers, uitgave '+html.escape(version)+', '+date+', https://open-parafrase-weergave.nl.', small),
             Paragraph('Bron: <link href="https://open-parafrase-weergave.nl" color="#143247">open-parafrase-weergave.nl</link>. Licentie: <link href="https://creativecommons.org/publicdomain/zero/1.0/" color="#143247">CC0 1.0</link>. De inhoudsopgave en de bladwijzers van de PDF openen de boeken en hoofdstukken.', small), PageBreak(),
             Paragraph('Inhoud', bookstyle)]
    for book, chapters in selected:
        key = book['id']
        story.append(Paragraph(f'<link href="#{key}" color="#143247">{html.escape(book["nameDutch"])} <font color="#777777">({len(chapters)} hoofdstukken)</font></link>', contents))
    for book, chapters in selected:
        story.extend([PageBreak(), Heading(book['nameDutch'], bookstyle, book['id'], 0)])
        for nr, verses in chapters:
            story.append(Heading(f"{book['nameDutch']} {nr}", chapterstyle, f"{book['id']}-{nr}", 1))
            for number, text in verses:
                safe = re.sub(r'([\u0590-\u05ff]+)', r'<font name="Hebrew">\1</font>', html.escape(text))
                story.append(Paragraph(f'<super><font size="8">{number}</font></super> {safe}', body))

    def footer(canvas, doc):
        canvas.setTitle('Open Parafrase Weergave - volledige leesuitgave')
        canvas.setAuthor('Open Parafrase Weergave')
        canvas.setSubject(f'CC0 / publiek domein; {date}; {counts["boeken"]} boeken; zonder kanttekeningen')
        canvas.setCreator('Open Parafrase Weergave')
        canvas.setFont('OV', 9)
        canvas.setFillColor(colors.HexColor('#666666'))
        canvas.drawCentredString(A5[0]/2, 25, str(doc.page))
        if doc.page > 2:
            canvas.drawString(38, A5[1]-25, 'Open Parafrase Weergave')

    output = Path(output)
    output.parent.mkdir(parents=True, exist_ok=True)
    temporary = output.with_suffix('.pdf.tmp')
    try:
        doc = SimpleDocTemplate(str(temporary), pagesize=A5, leftMargin=38, rightMargin=38, topMargin=42, bottomMargin=42, pageCompression=1)
        doc.build(story, onFirstPage=footer, onLaterPages=footer)
        temporary.replace(output)
    finally:
        temporary.unlink(missing_ok=True)
    print(json.dumps({'bestand': str(output), **counts}, ensure_ascii=False))
    return counts


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, default=OUTPUT)
    from build_downloads import public_books
    build_pdf(public_books(), parser.parse_args().output)
