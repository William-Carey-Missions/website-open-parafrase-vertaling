#!/usr/bin/env python3
"""Toon hoeveel hoofdstukbeelden nog ontbreken voor drie per hoofdstuk."""

import argparse
import json
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--missing", action="store_true", help="Toon ook ieder onvolledig hoofdstuk")
    args = parser.parse_args()

    editions = json.loads((ROOT / "data/vertalingen/manifest.json").read_text(encoding="utf-8"))["edities"]
    published = set(next(edition["boeken"] for edition in editions if edition["code"] == "nl-opv"))
    images = json.loads((ROOT / "data/book-images.json").read_text(encoding="utf-8"))["books"]
    counts = Counter((book, scene["chapter"]) for book, scenes in images.items() for scene in scenes)
    chapters = [
        (book, int(path.stem))
        for book in sorted(published)
        for path in (ROOT / "data/vertalingen/nl-opv" / book).glob("*.json")
        if path.stem.isdigit()
    ]
    missing = [(book, chapter, 3 - counts[book, chapter]) for book, chapter in chapters if counts[book, chapter] < 3]
    report = {
        "books": len(published),
        "chapters": len(chapters),
        "chapters_with_three_images": len(chapters) - len(missing),
        "images": sum(counts.values()),
        "images_still_needed": sum(item[2] for item in missing),
    }
    if args.missing:
        report["missing"] = [{"book": book, "chapter": chapter, "needed": needed} for book, chapter, needed in missing]
    print(json.dumps(report, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
