#!/usr/bin/env python3
"""Maak compacte leesdata uit bestaande OPV- en OGW-bronnen.

De OGW-bron blijft eigendom van de zustersite. De uitvoer is een snapshot zodat
de OPV-site zelfstandig gebouwd kan worden zonder zusterrepo in CI.
"""

from __future__ import annotations

import json
import re
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OGW_GEO = ROOT.parent / "website-open-gods-woord/data/geografie-runtime.geojson"
DATA = ROOT / "data"

# Redactionele selectie, geen automatische vertaling van een heel vers.
GROUND_ROOTS = (
    "verbond", "genad", "verzoen", "rechtvaard", "heilig", "opstand",
    "wedergeboort", "opnieuw", "geboort", "gelov", "geloof", "vertrouw", "zond",
    "vergev", "verloss", "red", "messias", "gezalf", "christus", "geest",
    "koninkrijk", "zegen", "aanbid", "offer", "profet", "profeet",
    "wijsheid", "waarheid", "leven", "liefde", "liefheb", "vrede",
    "schepp", "schep", "woord", "licht", "wereld", "god", "yhvh",
)

CORE_TERMS = (
    "aanbidding", "altaar", "apostel", "bekering", "besnijdenis", "bidden",
    "brood des levens", "christus", "doop", "engel", "evangelie", "genade",
    "gebed", "gerechtigheid", "geloof", "gemeente", "heilig", "heiligheid",
    "heiligmaking", "heilige geest", "hoop", "koninkrijk van god", "kruis",
    "liefde", "messias", "offer", "opstanding", "oordeel", "priester",
    "profetie", "profeet", "rechtvaardiging", "redding", "sabbat",
    "schrift", "tempel", "vergeving", "verlossing", "verzoening", "verbond",
    "wijsheid", "zegen", "zonde", "zoon van god",
)


def write_json(name: str, value: object) -> None:
    (DATA / name).write_text(json.dumps(value, ensure_ascii=False, separators=(",", ":")) + "\n", encoding="utf-8")


def dictionary() -> None:
    entries: dict[str, dict] = {}
    files = json.loads((DATA / "begrippenlijst-INDEX.json").read_text(encoding="utf-8"))
    for book in files:
        path = DATA / book["file"]
        if not path.is_file():
            continue
        for item in json.loads(path.read_text(encoding="utf-8")):
            word = str(item.get("woord", "")).strip()
            definition = str(item.get("uitleg", "")).strip()
            if not word or not definition:
                continue
            key = word.casefold()
            entry = entries.setdefault(key, {"woord": word, "categorie": item.get("categorie", "begrip"), "betekenissen": []})
            meaning = {"uitleg": definition, "boek": book["slug"], "ref": item.get("ref", "")}
            if not any(existing["uitleg"] == definition for existing in entry["betekenissen"]):
                entry["betekenissen"].append(meaning)
    output = {"status": "concept", "humanReviewed": False,
              "note": "Bestaande OPV-begrippenlijsten; geen bronnenonderzoek naar de vroege kerk.",
              "terms": sorted(entries.values(), key=lambda item: item["woord"].casefold())}
    write_json("reading-dictionary.json", output)
    write_json("reading-term-index.json", [entries[word] ["woord"] for word in CORE_TERMS if word in entries])
    print(f"Woordenboek: {len(entries)} lemma's; {len(json.loads((DATA / 'reading-term-index.json').read_text()))} leeslinks")


def locations(source: Path = OGW_GEO) -> None:
    if not source.is_file():
        raise SystemExit(f"Geografische bron ontbreekt: {source}")
    geo = json.loads(source.read_text(encoding="utf-8"))
    refs: dict[tuple[str, int, int], list[dict]] = defaultdict(list)
    for feature in geo["features"]:
        props = feature["properties"]
        coords = feature.get("geometry", {}).get("coordinates", [])
        if len(coords) != 2 or not all(isinstance(value, (float, int)) for value in coords):
            continue
        for ref in props.get("refs", []):
            if ref.get("status") != "agent-reviewed":
                continue
            name = ref.get("label") or props.get("naam")
            if not name:
                continue
            refs[(ref.get("boek"), ref.get("hoofdstuk"), ref.get("vers"))].append({
                "id": props["id"], "naam": name, "aliases": props.get("aliases", []),
                "lat": round(coords[1], 5), "lon": round(coords[0], 5),
                "zekerheid": props.get("zekerheid", "onzeker"),
                "precisie": props.get("kaartPrecisie", {}).get("label", "Benaderde locatie"),
            })
    books: dict[str, dict[str, list[dict]]] = {}
    chapters = DATA / "edities/opv/chapters"
    for path in sorted(chapters.glob("*/*.json")):
        chapter = json.loads(path.read_text(encoding="utf-8"))
        book_id, chapter_num = chapter["boek"], chapter["hoofdstuk"]
        verse_text = {verse["nummer"]: verse["tekst"].casefold() for verse in chapter["verzen"]}
        blocks = chapter.get("blokken") or [{"vanaf": 1, "tot": max(verse_text), "kop": "Locaties in dit hoofdstuk"}]
        cards = []
        for block in blocks:
            places = []
            seen = set()
            for number in range(int(block["vanaf"]), int(block["tot"]) + 1):
                text = verse_text.get(number, "")
                for place in refs.get((book_id, chapter_num, number), []):
                    names = [place["naam"], *place["aliases"]]
                    if place["id"] in seen or not any(name and name.casefold() in text for name in names):
                        continue
                    seen.add(place["id"])
                    places.append({key: value for key, value in place.items() if key != "aliases"})
            if places:
                cards.append({"verse": int(block["vanaf"]), "heading": block.get("kop", "Locaties"),
                              "places": places[:4], "more": max(0, len(places) - 4)})
        if cards:
            books.setdefault(book_id, {})[str(chapter_num)] = cards
    write_json("reading-locations.json", {
        "source": "Open Gods Woord / OpenBible.info Bible Geocoding Data",
        "status": "agent-reviewed", "humanReviewed": False,
        "note": "Schematische positie; coördinaten kunnen onzeker of representatief zijn.",
        "books": books,
    })
    print(f"Kaartjes: {sum(len(book) for book in books.values())} hoofdstukken in {len(books)} boeken")


def ground_words() -> None:
    lexicons = {
        "H": json.loads((DATA / "lexicon-nl/bdb-nl.json").read_text(encoding="utf-8")),
        "G": json.loads((DATA / "lexicon-nl/tbesg-nl.json").read_text(encoding="utf-8")),
    }
    books = {}
    for path in sorted((DATA / "woordnummers-inline").glob("*.json")):
        book_id = path.stem
        chapter_dir = DATA / "edities/opv/chapters" / book_id
        if not chapter_dir.is_dir():
            continue
        source = json.loads(path.read_text(encoding="utf-8"))
        for chapter_key, verse_mappings in source.get("chapters", {}).items():
            chapter_path = chapter_dir / f"{chapter_key}.json"
            if not chapter_path.is_file():
                continue
            chapter = json.loads(chapter_path.read_text(encoding="utf-8"))
            cards = []
            used = set()
            for block in chapter.get("blokken", []):
                candidates = []
                for verse in range(int(block["vanaf"]), int(block["tot"]) + 1):
                    for mapping in verse_mappings.get(str(verse), []):
                        if mapping.get("reviewstatus") != "handmatig_gecontroleerd":
                            continue
                        numbers = mapping.get("strongs", [])
                        words = mapping.get("bronwoorden", [])
                        for index, number in enumerate(numbers):
                            if not re.fullmatch(r"[HG]\d+", number) or index >= len(words):
                                continue
                            definition = lexicons[number[0]].get(number, {})
                            gloss = str(definition.get("glossNl", "")).strip()
                            if not gloss or len(gloss) > 90:
                                continue
                            tokens = re.findall(r"[a-z]+", gloss.casefold())
                            rank = next((i for i, root in enumerate(GROUND_ROOTS)
                                         if any(token.startswith(root) for token in tokens)), None)
                            if rank is None or number in used:
                                continue
                            candidates.append((rank, verse, index, number, words[index], gloss, mapping))
                # Eén kernwoord per tekstblok houdt ruimte voor beeld en kaart.
                for rank, verse, index, number, word, gloss, mapping in sorted(candidates, key=lambda item: item[:4])[:1]:
                    if number in used:
                        continue
                    used.add(number)
                    cards.append({
                        "verse": verse, "woord": word, "strongs": number,
                        "betekenis": gloss, "taal": "Hebreeuws" if number[0] == "H" else "Grieks",
                        "bron": mapping.get("herkomst", {}).get("dataset", "lokale grondtekstlaag"),
                        "reviewstatus": mapping["reviewstatus"],
                    })
            if cards:
                books.setdefault(book_id, {})[chapter_key] = sorted(cards, key=lambda card: card["verse"])
    write_json("reading-groundwords.json", {
        "source": "OPV woordnummers-inline + Nederlandse lexiconprojectie",
        "note": "Korte selectie uit per vers gekoppelde grondtekstwoorden; de OPV is een parafrase. Lexiconbetekenissen vragen contextuele beoordeling.",
        "books": books,
    })
    print(f"Grondtekstkaarten: {sum(len(chapters) for chapters in books.values())} hoofdstukken in {len(books)} boeken")


if __name__ == "__main__":
    dictionary()
    locations()
    ground_words()
