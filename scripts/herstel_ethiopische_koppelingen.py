#!/usr/bin/env python3
"""Controleer de zes Ge'ez-boeken; schrijf alleen met --write.

Geen nieuwe woordnummers of geraden lemma's. Projectie gebruikt een aanwezige
glosse, eventueel elders bij exact dezelfde Ge'ez-vorm EN hetzelfde nummer.
Alleen unieke Nederlandse inhoudswoorden/woordgroepen krijgen automatisch
een link. Herhaalde/overlappende ankers en concurrerende bronwoorden vallen af.
De rapportage onderscheidt technische controle van inhoudelijke beoordeling.
"""
from __future__ import annotations

import argparse
from collections import Counter, defaultdict
from copy import deepcopy
import hashlib
from html.parser import HTMLParser
import json
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[1]
BOOKS = ('henoch', 'jubileeen', '1meqabyan', '2meqabyan', '3meqabyan', '4baruch')
VERSION = 'geez-koppelingen-2026-11-07-v1'
VISIBLE = {'handmatig_gecontroleerd', 'automatisch_hoog_vertrouwen'}
MARKER = re.compile(r'\d+(?::\d+)?\Z')
WORD = re.compile(r'[^\W_]+', re.UNICODE)
# Deze woorden mogen nooit zelfstandig de aanleiding zijn voor een nieuwe link.
FUNCTION = set('''en of maar want omdat opdat zoals als dan nog ook niet geen wel
 al alles allen alle elk elke ieder iedere deze dit dat die wie wat welke welk
 het de een der des den te ten ter om voor van in op uit bij naar tot door met
 over onder aan achter boven zonder tegen tussen binnen buiten rondom terwijl
 toen wanneer waar daar hier daarom dus is was waren zijn zij hij ik gij jij je
 u wij we jullie men er het hem hen hun haar mijn mij uw ons onze onze eigen zich
 zelf zichzelf hemzelf mijzelf uwer haarzelf heeft heb hebt hebben had hadden
 zal zult zullen zou zouden moet moeten mogen kan kunnen wordt worden werd
 werden zijt zijne zijner haren hunner hemzelf gijzelf elkaar meer minder zeer
 veel vele weinig weinige zo even zozeer heen af toe weg reeds nu eerst laatst
 degene hetgeen datgene wiens diens welker diens welke vanwege sinds totdat
 voordat nadat alvorens indien eer aldaar hierna daarna tevoren daarheen daaruit
 hieruit daarin hierin daarover hierover waartoe waarom slechts alleen beide
 beiden tegelijk telkens altijd nooit ooit weder wederom wederom heen zodra
'''.split())
PREFIX = set('''en de het een van voor in op uit bij naar tot door met over onder
 aan om te zijn haar hun mijn uw onze ons hij zij ik gij jij u wij je die dat
'''.split())
SUFFIX = {'van'}


class ReaderText(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.parts = []
        self.skipped = 0

    def handle_starttag(self, tag, attrs):
        if tag in {'sup', 'button', 'script', 'style'}:
            self.skipped += 1

    def handle_endtag(self, tag):
        if tag in {'sup', 'button', 'script', 'style'} and self.skipped:
            self.skipped -= 1

    def handle_data(self, value):
        if not self.skipped:
            self.parts.append(value)


def plain(verse):
    parser = ReaderText()
    parser.feed(verse.get('text2026_html') or verse.get('text2026', ''))
    return ''.join(parser.parts)


def spans(text, anchor):
    # Dezelfde letter/cijfer-grenzen als renderInline; underscore is een grens.
    return [m.span() for m in re.finditer(
        r'(?<![^\W_])' + re.escape(anchor) + r'(?![^\W_])', text, re.I
    )] if anchor else []


def digest(value):
    return hashlib.sha256(json.dumps(value, ensure_ascii=False, sort_keys=True).encode()).hexdigest()


def indices(mapping):
    return mapping.get('herkomst', {}).get('grondindices', [])


def visible(mapping):
    return mapping.get('reviewstatus', 'handmatig_gecontroleerd') in VISIBLE


def anchor_span(verse, mapping):
    matches = spans(plain(verse), mapping.get('tekst') or mapping.get('anker', ''))
    occurrence = mapping.get('voorkomen', 1)
    return matches[occurrence - 1] if 0 < occurrence <= len(matches) else None


def overlap(a, b):
    return a[0] < b[1] and b[0] < a[1]


def alternatives(gloss):
    # Geen fuzzy matching, stemming, negatieve omschrijvingen of woorden uit
    # vrije woordenboekdefinities. Alleen complete glosse of grammaticaal frame.
    if any(c in gloss for c in '[]();:') or re.search(r'\b(niet|geen|zonder)\b', gloss, re.I):
        return set()
    result = set()
    for part in re.split(r'[/,]', gloss):
        part = part.strip().lower()
        tokens = part.split()
        if not tokens or not all(WORD.fullmatch(t) for t in tokens):
            continue
        if any(t not in FUNCTION and len(t) >= 3 for t in tokens):
            result.add(part)
        while len(tokens) > 1 and tokens[0] in PREFIX:
            tokens.pop(0)
        while len(tokens) > 1 and tokens[-1] in SUFFIX:
            tokens.pop()
        if any(t not in FUNCTION and len(t) >= 3 for t in tokens):
            result.add(' '.join(tokens))
    return result


def source_key(word):
    return word.get('woord', ''), word.get('strongs', '')


def glossary(chapters):
    known = defaultdict(dict)
    for (book, chapter), data in chapters.items():
        for verse in data['verses']:
            for i, word in enumerate(verse.get('grondtekst', [])):
                gloss = word.get('betekenis', '').strip()
                if gloss:
                    known[source_key(word)].setdefault(gloss, [book, chapter, verse['number'], i])
    return known


def gloss_for(word, known):
    if word.get('betekenis'):
        return word['betekenis'], None
    values = known.get(source_key(word), {})
    if len(values) == 1:
        gloss, reference = next(iter(values.items()))
        return gloss, reference
    return '', None


def mapping_for(verse, book, chapter, index, anchor, gloss, evidence=None, manual=False, occurrence=1):
    word = verse['grondtekst'][index]
    provenance = {
        'dataset': 'lokale-grondtekst', 'versie': VERSION,
        'sha256': digest(verse['grondtekst']),
        'referentie': f'{book} {chapter}:{verse["number"]}',
        'bronindices': [index], 'grondindices': [index],
        'methode': 'inhoudelijk-beoordeeld' if manual else 'unieke-inhoudswoordmatch-met-glosse',
    }
    if evidence:
        provenance['glosse_bron'] = evidence
    return {
        'tekst': anchor, 'voorkomen': occurrence, 'strongs': [word['strongs']],
        'bronwoorden': [word['woord']], 'transliteraties': [word.get('transliteratie', '')],
        'glossen': [gloss], 'confidence': 1.0 if manual else 0.9,
        'reviewstatus': 'handmatig_gecontroleerd' if manual else 'automatisch_hoog_vertrouwen',
        'herkomst': provenance,
    }


def split_jubilees(chapters, changes):
    """Splits alleen expliciete, oplopende versmarkeringen naar lege verzen.

    De 43 grenzen in hoofdstukken 11–20 zijn beoordeeld naast de Nederlandse
    tekst. 31:19–20 valt hier bewust buiten: beide verzen bevatten al grondtekst.
    De marker verhuist mee, zodat elk bronobject exact behouden blijft.
    """
    for (book, chapter), data in chapters.items():
        if book != 'jubileeen' or not 11 <= chapter <= 20:
            continue
        verses = {v['number']: v for v in data['verses']}
        for verse in data['verses']:
            ground = verse.get('grondtekst', [])
            cuts = [(i, int(w['woord'])) for i, w in enumerate(ground)
                    if i and w['woord'].isdigit() and int(w['woord']) > verse['number']]
            if not cuts:
                continue
            numbers = [n for _, n in cuts]
            assert numbers == list(range(verse['number'] + 1, verse['number'] + 1 + len(cuts)))
            assert all(n in verses and not verses[n].get('grondtekst') and not verses[n].get('woordnummers') for n in numbers)
            segments = [(0, verse['number']), *cuts, (len(ground), None)]
            old_mappings = deepcopy(verse.get('woordnummers', []))
            for j, (start, number) in enumerate(segments[:-1]):
                end = segments[j + 1][0]
                target = verses[number]
                target['grondtekst'] = deepcopy(ground[start:end])
                target['woordnummers'] = []
                for original in old_mappings:
                    ix = indices(original)
                    assert ix and (all(start <= i < end for i in ix) or all(i < start or i >= end for i in ix))
                    if all(start <= i < end for i in ix):
                        mapping = deepcopy(original)
                        mapping['herkomst'].update({
                            'grondindices': [i - start for i in ix],
                            'bronindices': [i - start for i in ix],
                            'referentie': f'{book} {chapter}:{number}',
                            'sha256': digest(target['grondtekst']), 'versie': VERSION,
                            'versgrens_herstel': {'van': verse['number'], 'oude_grondindices': ix},
                        })
                        target['woordnummers'].append(mapping)
                changes.append({'type': 'versgrens', 'boek': book, 'hoofdstuk': chapter,
                                'van_vers': verse['number'], 'naar_vers': number,
                                'bronbereik': [start, end], 'verplaatste_woorden': end - start})


def suspect_boundary(book, chapter, verse):
    ground = verse.get('grondtekst', [])
    if ground and re.fullmatch(r'\d+:\d+', ground[0]['woord']):
        if ground[0]['woord'] != f'{chapter}:{verse["number"]}':
            return True
    return any(i and MARKER.fullmatch(w['woord']) and int(w['woord'].split(':')[-1]) != verse['number']
               for i, w in enumerate(verse.get('grondtekst', [])))


def repair_jubilees31(chapters, changes):
    """31:20 stond achter 19; 21–30 waren daardoor één vers verschoven."""
    verses = {v['number']: v for v in chapters['jubileeen', 31]['verses']}
    if verses[20].get('grondtekst', [{}])[0].get('woord') == '31:20':
        return
    original = deepcopy(verses)
    assert original[19]['grondtekst'][9]['woord'] == '31:20'
    assert all(original[n]['grondtekst'][0]['woord'] == f'31:{n+1}' for n in range(20, 30))
    assert original[30]['grondtekst'][0]['woord'] == 'ወሖረት'
    segments = [(19, 0, 9, 19), (19, 9, len(original[19]['grondtekst']), 20)]
    segments += [(n, 0, len(original[n]['grondtekst']), n + 1) for n in range(20, 30)]
    segments += [(30, 0, len(original[30]['grondtekst']), 30)]
    for n in range(19, 31):
        verses[n]['grondtekst'] = []
        verses[n]['woordnummers'] = []
    for old, start, end, new in segments:
        target = verses[new]
        offset = len(target['grondtekst'])
        target['grondtekst'].extend(deepcopy(original[old]['grondtekst'][start:end]))
        for mapping in original[old].get('woordnummers', []):
            ix = indices(mapping)
            assert ix and (all(start <= i < end for i in ix) or all(i < start or i >= end for i in ix))
            if all(start <= i < end for i in ix):
                m = deepcopy(mapping)
                m['herkomst'].update({'grondindices': [i-start+offset for i in ix],
                    'bronindices': [i-start+offset for i in ix],
                    'referentie': f'jubileeen 31:{new}', 'versie': VERSION,
                    'versgrens_herstel': {'van': old, 'oude_grondindices': ix}})
                target['woordnummers'].append(m)
        changes.append({'type': 'versgrens', 'boek': 'jubileeen', 'hoofdstuk': 31,
                        'van_vers': old, 'naar_vers': new, 'bronbereik': [start, end],
                        'verplaatste_woorden': end-start})
    for n in range(19, 31):
        for mapping in verses[n]['woordnummers']:
            mapping['herkomst']['sha256'] = digest(verses[n]['grondtekst'])


def apply_review_plan(chapters, root, changes):
    path = root / 'reviews' / 'geez' / 'inhoudelijke-correcties-2026-11-07.json'
    if not path.exists():
        return
    for item in json.loads(path.read_text())['correcties']:
        book, chapter, number = item['referentie']
        verse = next(v for v in chapters[book, chapter]['verses'] if v['number'] == number)
        assert digest(verse['grondtekst']) == item['grondtekst_sha256'], item['referentie']
        assert digest({k: v for k, v in verse.items() if k.startswith('text2026')}) == item['tekst_sha256']
        i = item['grondindex']
        current = [m for m in verse.get('woordnummers', []) if indices(m) == [i]]
        if not item.get('uitschakelen') and any(m.get('tekst') == item['tekst'] and m.get('voorkomen', 1) == item.get('voorkomen', 1) for m in current):
            continue
        matching = [m for m in verse.get('woordnummers', [])
                    if indices(m) == [item.get('oude_grondindex', i)]
                    and ('oud_anker' not in item or m.get('tekst') == item['oud_anker'])]
        if item.get('uitschakelen'):
            assert len(matching) == 1
            if matching[0].get('reviewstatus') == 'controle_nodig':
                continue
            old = deepcopy(matching[0])
            matching[0]['reviewstatus'] = 'controle_nodig'
            matching[0]['reviewopmerking'] = item['reden']
            changes.append({'type': 'inhoudelijk_uitgeschakeld', 'referentie': item['referentie'],
                            'voor': old, 'na': deepcopy(matching[0]), 'reden': item['reden']})
            continue
        anchor, occurrence = item['tekst'], item.get('voorkomen', 1)
        word = verse['grondtekst'][i]
        mapping = mapping_for(verse, book, chapter, i, anchor, word.get('betekenis', ''), manual=True, occurrence=occurrence)
        mapping['herkomst']['beoordeling'] = item['reden']
        assert anchor_span(verse, mapping), item
        assert len(matching) <= 1, item
        previous = deepcopy(matching[0]) if matching else None
        if matching:
            verse['woordnummers'].remove(matching[0])
        verse.setdefault('woordnummers', []).append(mapping)
        changes.append({'type': 'inhoudelijke_correctie' if previous else 'inhoudelijke_aanvulling',
                        'referentie': item['referentie'], 'voor': previous, 'na': mapping, 'reden': item['reden']})


def repartition(chapters, book, chapter, segments, changes):
    verses = {v['number']: v for v in chapters[book, chapter]['verses']}
    old = deepcopy(verses)
    for number in {new for _, _, _, new in segments}:
        verses[number]['grondtekst'] = []
        verses[number]['woordnummers'] = []
    for number, start, end, target_number in segments:
        source = old[number]
        end = len(source['grondtekst']) if end is None else end
        target = verses[target_number]
        offset = len(target['grondtekst'])
        target['grondtekst'].extend(deepcopy(source['grondtekst'][start:end]))
        for previous in source.get('woordnummers', []):
            ix = indices(previous)
            assert ix and (all(start <= i < end for i in ix) or all(i < start or i >= end for i in ix))
            if all(start <= i < end for i in ix):
                mapping = deepcopy(previous)
                mapping['herkomst'].update({
                    'grondindices': [i-start+offset for i in ix], 'bronindices': [i-start+offset for i in ix],
                    'referentie': f'{book} {chapter}:{target_number}', 'versie': VERSION,
                    'versgrens_herstel': {'van': number, 'oude_grondindices': ix},
                })
                target['woordnummers'].append(mapping)
        changes.append({'type': 'versgrens', 'boek': book, 'hoofdstuk': chapter,
                        'van_vers': number, 'naar_vers': target_number,
                        'bronbereik': [start, end], 'verplaatste_woorden': end-start})
    for number in {new for _, _, _, new in segments}:
        for mapping in verses[number]['woordnummers']:
            mapping['herkomst']['sha256'] = digest(verses[number]['grondtekst'])


def repair_meqabyan(chapters, changes):
    verses = {v['number']: v for v in chapters['1meqabyan', 8]['verses']}
    if verses[10]['grondtekst'][0]['woord'] == '8:9':
        assert verses[9]['grondtekst'][0]['woord'] == 'ወኮነት'
        assert verses[25]['grondtekst'][6]['woord'] == '8:25'
        assert all(verses[n]['grondtekst'][0]['woord'] == f'8:{n-1}' for n in range(10, 26))
        segments = [(8, 0, None, 8), (9, 0, None, 8)]
        segments += [(n, 0, None, n-1) for n in range(10, 25)]
        segments += [(25, 0, 6, 24), (25, 6, None, 25)]
        repartition(chapters, '1meqabyan', 8, segments, changes)
    verses = {v['number']: v for v in chapters['1meqabyan', 14]['verses']}
    if verses[3]['grondtekst'][0]['woord'] == '14:4':
        assert verses[2]['grondtekst'][26]['woord'] == '14:3'
        repartition(chapters, '1meqabyan', 14, [(2,0,26,2),(2,26,None,3),(3,0,None,4),(4,0,None,4)], changes)
    verses = {v['number']: v for v in chapters['3meqabyan', 4]['verses']}
    if verses[7]['grondtekst'][0]['woord'] == '4:6':
        assert all(verses[n]['grondtekst'][0]['woord'] == f'4:{n-1}' for n in range(7, 28))
        assert verses[27]['grondtekst'][13]['woord'] == '4:27'
        duplicate = deepcopy(verses[7]['grondtekst'])
        canonical = verses[6]['grondtekst']
        assert len(duplicate) == len(canonical)+1
        # Hetzelfde fragment, met één enkelvoud/meervoudvariant in het werkwoord.
        assert [w for i,w in enumerate(duplicate[1:]) if i != 3] == [w for i,w in enumerate(canonical) if i != 3]
        assert (canonical[3]['woord'], duplicate[4]['woord']) == ('ይከውኑ', 'ይከውን')
        old_mappings = deepcopy(verses[7].get('woordnummers', []))
        archived_mappings = deepcopy(old_mappings)
        segments = [(n,0,None,n-1) for n in range(8,28)]
        segments[-1:] = [(27,0,13,26),(27,13,None,27)]
        repartition(chapters, '3meqabyan', 4, segments, changes)
        for mapping in old_mappings:
            ix = indices(mapping)
            assert all(i > 0 and canonical[i-1]['woord'] == duplicate[i]['woord'] for i in ix)
            mapping['herkomst'].update({'grondindices': [i-1 for i in ix], 'bronindices': [i-1 for i in ix],
                'referentie': '3meqabyan 4:6', 'sha256': digest(canonical), 'versie': VERSION,
                'versgrens_herstel': {'van':7, 'oude_grondindices': ix}})
            verses[6].setdefault('woordnummers', []).append(mapping)
        changes.append({'type':'dubbel_bronfragment_gearchiveerd', 'referentie':['3meqabyan',4,7],
                        'reden':'Dubbele opname van 4:6, met werkwoordvariant. De eerdere volledige bronlaag bij 4:6 blijft canoniek; de variant blijft hier bewaard.',
                        'grondtekst':duplicate, 'woordnummers':archived_mappings})


def project(verse, book, chapter, known, *, reviewed_boundary=False):
    if suspect_boundary(book, chapter, verse) and not reviewed_boundary:
        return []
    text = plain(verse)
    mappings = verse.get('woordnummers', [])
    covered = {i for m in mappings if visible(m) and anchor_span(verse, m) for i in indices(m)}
    occupied = [anchor_span(verse, m) for m in mappings if visible(m) and anchor_span(verse, m)]
    candidates = defaultdict(list)
    owners = defaultdict(set)
    locations = defaultdict(set)
    # Ook al gekoppelde en ongenummerde bronwoorden tellen als concurrent.
    for i, word in enumerate(verse.get('grondtekst', [])):
        gloss, evidence = gloss_for(word, known)
        for anchor in alternatives(gloss):
            matches = spans(text, anchor)
            for span in matches:
                owners[span].add(i)
                locations[i].add(span)
            if len(matches) == 1:
                span = matches[0]
                candidates[i].append((span, gloss, evidence))
    result = []
    for i, options in candidates.items():
        word = verse['grondtekst'][i]
        if i in covered or not re.fullmatch(r'OVG\d+', word.get('strongs', '')):
            continue
        good = [(s, g, e) for s, g, e in options
                if not any(overlap(s, o) for o in occupied)
                and not any(overlap(s, other) and owner != {i} for other, owner in owners.items())]
        if not good:
            continue
        # Alternatieven op verschillende plaatsen zijn inhoudelijk dubbelzinnig.
        best = max(good, key=lambda item: item[0][1] - item[0][0])
        if not all(overlap(best[0], s) for s in locations[i]):
            continue
        span, gloss, evidence = best
        mapping = mapping_for(verse, book, chapter, i, text[slice(*span)], gloss, evidence)
        result.append(mapping)
        occupied.append(span)
    return result


def audit(chapters):
    counts = {book: Counter() for book in BOOKS}
    issues, missing = [], []
    for (book, chapter), data in chapters.items():
        count = counts[book]
        for verse in data['verses']:
            ref = [book, chapter, verse['number']]
            ground = verse.get('grondtekst', [])
            count['verzen'] += 1
            count['verzen_zonder_grondtekst'] += not bool(ground)
            count['genummerde_grondwoorden'] += sum(bool(w.get('strongs')) for w in ground)
            count['grondwoorden_zonder_nummer'] += sum(not w.get('strongs') and not MARKER.fullmatch(w['woord']) for w in ground)
            covered = set()
            source_uses = Counter()
            occupied = []
            if suspect_boundary(book, chapter, verse):
                issues.append({'referentie': ref, 'probleem': 'versgrens_controleren'})
            for mapping in verse.get('woordnummers', []):
                count['koppelingen'] += 1
                if not visible(mapping):
                    count['koppelingen_in_afwachting'] += 1
                    continue
                span = anchor_span(verse, mapping)
                ix = indices(mapping)
                valid_source = bool(ix) and all(isinstance(i, int) and 0 <= i < len(ground) for i in ix)
                valid_source = valid_source and [ground[i].get('strongs') for i in ix] == mapping.get('strongs')
                valid_source = valid_source and [ground[i].get('woord') for i in ix] == mapping.get('bronwoorden')
                if not span or not valid_source:
                    issues.append({'referentie': ref, 'probleem': 'anker_ontbreekt' if not span else 'bron_verwijzing', 'koppeling': mapping})
                    continue
                if any(overlap(span, other) for other in occupied):
                    issues.append({'referentie': ref, 'probleem': 'overlappend_anker', 'koppeling': mapping})
                occupied.append(span)
                for i in ix:
                    source_uses[i] += 1
                covered.update(ix)
                count['zichtbare_koppelingen'] += 1
            for i, uses in source_uses.items():
                if uses > 1:
                    issues.append({'referentie': ref, 'probleem': 'herhaald_bronvoorkomen', 'grondindex': i})
            count['gekoppelde_grondwoorden'] += len(covered)
            for i, word in enumerate(ground):
                if word.get('strongs') and i not in covered:
                    missing.append({'referentie': ref, 'grondindex': i, **word})
                    count['genummerde_grondwoorden_zonder_koppeling'] += 1
    return {'tellingen': counts, 'technische_problemen': issues, 'ontbrekende_koppelingen': missing}


def immutable(chapters):
    texts, words = {}, Counter()
    for key, data in chapters.items():
        texts[key] = [{k: v for k, v in verse.items() if k not in {'grondtekst', 'woordnummers'}} for verse in data['verses']]
        for verse in data['verses']:
            words.update(json.dumps(w, sort_keys=True, ensure_ascii=False) for w in verse.get('grondtekst', []))
    return texts, words


def run(root=ROOT, write=False):
    chapters, paths, originals = {}, {}, {}
    for book in BOOKS:
        for path in sorted((root / 'data' / book).glob('*.json'), key=lambda p: int(p.stem)):
            key = (book, int(path.stem))
            originals[key] = path.read_text()
            chapters[key] = json.loads(originals[key])
            paths[key] = path
    before = audit(chapters)
    invariant = immutable(chapters)
    changes = []
    split_jubilees(chapters, changes)
    repair_jubilees31(chapters, changes)
    repair_meqabyan(chapters, changes)
    apply_review_plan(chapters, root, changes)
    known = glossary(chapters)
    for (book, chapter), data in chapters.items():
        for verse in data['verses']:
            new = project(verse, book, chapter, known)
            if new:
                verse.setdefault('woordnummers', []).extend(new)
                changes.extend({'type': 'aanvulling', 'referentie': [book, chapter, verse['number']], 'koppeling': m} for m in new)
    after_text, after_words = immutable(chapters)
    for change in changes:
        if change['type'] == 'dubbel_bronfragment_gearchiveerd':
            after_words.update(json.dumps(w, sort_keys=True, ensure_ascii=False) for w in change['grondtekst'])
    assert (after_text, after_words) == invariant, 'Nederlandse tekst of bronobject gewijzigd/verloren'
    after = audit(chapters)
    assert all(i['probleem'] == 'versgrens_controleren' for i in after['technische_problemen']), 'Los ontbrekende/overlappende ankers en bronverwijzingen eerst op'
    report = {
        'versie': VERSION,
        'scope': 'Zes Ethiopische boeken; technische corpuscontrole en conservatieve glosseprojectie. Geen volledige filologische controle van alle woorden of OVG-lemma-identificaties.',
        'voor': before['tellingen'], 'na': after['tellingen'],
        'wijzigingen': changes,
        'technische_problemen': after['technische_problemen'],
        'ontbrekende_koppelingen': after['ontbrekende_koppelingen'],
    }
    if write:
        for key, data in chapters.items():
            if data != json.loads(originals[key]):
                original = originals[key]
                indent = len(re.search(r'\n( +)"', original).group(1))
                paths[key].write_text(json.dumps(data, ensure_ascii=False, indent=indent) + ('\n' if original.endswith('\n') else ''))
        # De terugvallaag moet dezelfde generatie bevatten als de hoofdstukken.
        for book in BOOKS:
            path = root / 'data' / 'woordnummers-inline' / f'{book}.json'
            old = json.loads(path.read_text())
            projection = {str(c): {str(v['number']): v.get('woordnummers', []) for v in d['verses'] if v.get('woordnummers')}
                          for (b, c), d in chapters.items() if b == book}
            if old['chapters'] != projection:
                old['source'] = {'type': 'canonieke-hoofdstukprojectie', 'pipeline_version': VERSION,
                                 'opmerking': 'Exacte kopie van woordnummers in hoofdstuk-JSON; geen onafhankelijke automatische toewijzing.'}
                old['chapters'] = projection
                path.write_text(json.dumps(old, ensure_ascii=False, separators=(',', ':')) + '\n')
    destination = root / 'reviews' / 'geez' / ('controle-2026-11-07.json' if write else 'voorstel-2026-11-07.json')
    destination.parent.mkdir(parents=True, exist_ok=True)
    # Een idempotente tweede run mag het eerste wijzigingslog niet overschrijven.
    if not write or changes or not destination.exists():
        destination.write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n')
        if write:
            summary = {k: v for k, v in report.items() if k not in {'wijzigingen', 'ontbrekende_koppelingen'}}
            summary['aantallen_wijzigingen'] = dict(Counter(c['type'] for c in changes))
            summary['versen_zonder_grondtekst'] = [[b,c,v['number']] for (b,c),d in chapters.items() for v in d['verses'] if not v.get('grondtekst')]
            summary['volledig_inhoudelijk_gecontroleerd'] = False
            summary['vervolg'] = 'Resterende grondwoordvoorkomens inhoudelijk beoordelen, bronmarkeringen oplossen en onjuiste of ontbrekende OVG-lemma-identificaties afzonderlijk controleren. Niet ieder Nederlands woord heeft een apart bronwoord.'
            destination.with_name('overzicht-2026-11-07.json').write_text(json.dumps(summary, ensure_ascii=False, indent=2) + '\n')
    print(json.dumps({'schrijven': write, 'wijzigingen': dict(Counter(c['type'] for c in changes)),
                      'voor': before['tellingen'], 'na': after['tellingen'],
                      'technische_problemen': dict(Counter(i['probleem'] for i in after['technische_problemen'])),
                      'rapport': str(destination)}, ensure_ascii=False, indent=2))
    return report


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--write', action='store_true')
    run(write=parser.parse_args().write)
