"""Pas een handmatig beoordeeld plan voor de parafrase toe, met tekst- en bronhashes."""
import argparse
from copy import deepcopy
import json
from pathlib import Path
import herstel_ethiopische_koppelingen as h


def prepare(plan, chapter, source):
    result = deepcopy(chapter)
    assert chapter['editie'] == plan['editie'] == 'nl-opv'
    assert chapter['boek'] == plan['boek'] and chapter['hoofdstuk'] == plan['hoofdstuk']
    verses = {v['nummer']:v for v in result['verzen']}
    sources = {v['number']:v for v in source['verses']}
    grouped = {}
    for row in plan['koppelingen']:
        grouped.setdefault(row['vers'],[]).append(row['koppeling'])
    for number, mappings in grouped.items():
        verse = verses[number]; expected = plan['verzen'][str(number)]
        assert h.digest(verse['tekst']) == expected['tekst_sha256'], number
        assert h.digest(sources[number]['grondtekst']) == expected['grondtekst_sha256'], number
        assert not verse.get('woordnummers') or verse['woordnummers'] == mappings, 'Bestaande koppelingen verschillen'
        used, spans = set(), []
        for m in mappings:
            ix = m['herkomst']['grondindices']
            assert not used.intersection(ix); used.update(ix)
            words = [sources[number]['grondtekst'][i] for i in ix]
            assert m['strongs'] == [w['strongs'] for w in words]
            assert m['bronwoorden'] == [w['woord'] for w in words]
            positions = h.spans(verse['tekst'],m['tekst'])
            assert 0 < m['voorkomen'] <= len(positions)
            span = positions[m['voorkomen']-1]
            assert not any(h.overlap(span,s) for s in spans); spans.append(span)
        verse['woordnummers'] = deepcopy(mappings)
    return result


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('plan',type=Path);parser.add_argument('--write',action='store_true');args=parser.parse_args()
    plan=json.loads(args.plan.read_text());path=h.ROOT/'data/vertalingen/nl-opv'/plan['boek']/f"{plan['hoofdstuk']}.json"
    chapter=json.loads(path.read_text());source=json.loads((h.ROOT/'data'/plan['boek']/f"{plan['hoofdstuk']}.json").read_text())
    result=prepare(plan,chapter,source)
    if args.write and result != chapter:path.write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
    print('Gewijzigde hoofdstukken:',int(result != chapter))
