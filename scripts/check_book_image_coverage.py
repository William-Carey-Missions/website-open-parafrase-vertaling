#!/usr/bin/env python3
"""Inventariseer hoofdstukbeelden zonder een vast gewenst aantal."""

import argparse
import json
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--missing", action="store_true", help="Toon ook ieder hoofdstuk zonder eigen beeld")
    args = parser.parse_args()

    editions = json.loads((ROOT / "data/vertalingen/manifest.json").read_text(encoding="utf-8"))["edities"]
    from build_leespaginas import BOOK_ORDER
    published = set(next(edition["boeken"] for edition in editions if edition["code"] == "nl-opv")) & set(BOOK_ORDER[:82])
    images = json.loads((ROOT / "data/book-images.json").read_text(encoding="utf-8"))["books"]
    counts = Counter((book, scene["chapter"]) for book, scenes in images.items() for scene in scenes)
    chapters = [
        (book, int(path.stem))
        for book in sorted(published)
        for path in (ROOT / "data/vertalingen/nl-opv" / book).glob("*.json")
        if path.stem.isdigit()
    ]
    missing = [(book, chapter) for book, chapter in chapters if not counts[book, chapter]]
    distribution = Counter(counts[book, chapter] for book, chapter in chapters)
    report = {
        "books": len(published),
        "chapters": len(chapters),
        "chapters_with_images": len(chapters) - len(missing),
        "chapters_without_images": len(missing),
        "images_per_chapter": dict(sorted(distribution.items())),
        "images": sum(counts[book, chapter] for book, chapter in chapters),
    }
    if args.missing:
        report["missing"] = [{"book": book, "chapter": chapter} for book, chapter in missing]
    print(json.dumps(report, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
