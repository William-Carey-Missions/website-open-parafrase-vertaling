#!/usr/bin/env python3
"""Bouw de openbare leesuitgave als PDF en Markdown uit dezelfde nl-opv-bron."""
from pathlib import Path
import json

from build_leespaginas import catalog, book_markdown, write
from build_pdf import build_pdf

ROOT = Path(__file__).resolve().parents[1]


def public_books(root=ROOT):
    books = [book for book in catalog(root) if book['testament'] in ('OT', 'NT', 'AP')]
    if len(books) != 82:
        raise ValueError(f'Verwacht 82 openbare boeken, gevonden: {len(books)}')
    return books


def main():
    books = public_books()
    destination = ROOT / 'downloads'
    destination.mkdir(exist_ok=True)
    introduction = ('# Open Parafrase Weergave (proef)\n\n'
                    'Volledige openbare leesuitgave: 82 boeken. Parafrase in eenvoudig Nederlands.\n\n'
                    'Proefversie: alle verzen hebben de status concept; niet door mensen goedgekeurd.\n\n'
                    'Bijbeltekst: publiek domein (CC0). Vrij te gebruiken, te kopiëren en te verspreiden.\n'
                    'https://creativecommons.org/publicdomain/zero/1.0/deed.nl\n\n'
                    'Bron: https://open-parafrase-weergave.nl/\n\n'
                    'Citeerwijze: Open Parafrase Weergave (proef), boek hoofdstuk:vers.\n\n')
    markdown = introduction + '\n'.join(book_markdown(book) for book in books)
    write(destination / 'open-parafrase-weergave.md', markdown)
    build_pdf(books, destination / 'open-parafrase-weergave.pdf', ROOT)
    counts = {'boeken': len(books), 'hoofdstukken': sum(len(b['chapters']) for b in books),
              'verzen': sum(len(c['verzen']) for b in books for c in b['chapters'])}
    write(destination / 'index.json', json.dumps(counts, ensure_ascii=False) + '\n')
    print(json.dumps(counts))


if __name__ == '__main__':
    main()
