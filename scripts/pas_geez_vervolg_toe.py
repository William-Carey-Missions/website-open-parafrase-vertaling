#!/usr/bin/env python3
"""Voer de inhoudelijke vervolgronde uit; standaard alleen een voorstel."""
import argparse
from collections import Counter
from copy import deepcopy
import json
from pathlib import Path
import herstel_ethiopische_koppelingen as h

PLAN = h.ROOT / 'reviews/geez/vervolgplan-2026-11-07.json'


def prepare(plan, chapters):
    original = deepcopy(chapters)
    verses = {f'{b}/{c}/{v["number"]}': v for (b,c),d in chapters.items() for v in d['verses']}
    for ref, expected in plan['snapshots'].items():
        v = verses[ref]
        assert h.digest(v['grondtekst']) == expected['grondtekst_sha256'], ref
        assert h.digest({k:x for k,x in v.items() if k.startswith('text')}) == expected['tekst_sha256'], ref
    changes = []
    for item in plan['koppelingen']:
        ref = item['ref']
        b, c, _ = ref.split('/')
        verse = verses[ref]
        ix, anchor, occurrence = item['indices'], item['tekst'], item['voorkomen']
        mappings = verse.setdefault('woordnummers', [])
        if any(h.indices(m) == ix and m.get('tekst') == anchor and m.get('voorkomen',1) == occurrence for m in mappings):
            continue
        assert not any(set(ix) & set(h.indices(m)) for m in mappings), item
        source = [verse['grondtekst'][i] for i in ix]
        assert all(w.get('strongs') for w in source), item
        mapping = h.mapping_for(verse,b,int(c),ix[0],anchor,source[0].get('betekenis',''),manual=True,occurrence=occurrence)
        mapping.update(strongs=[w['strongs'] for w in source], bronwoorden=[w['woord'] for w in source],
                       transliteraties=[w.get('transliteratie','') for w in source],
                       glossen=[w.get('betekenis','') for w in source])
        mapping['herkomst'].update(versie=plan['id'],grondindices=ix,bronindices=ix,beoordeling=item['reden'])
        span = h.anchor_span(verse,mapping)
        assert span, item
        assert not any(h.visible(m) and h.anchor_span(verse,m) and h.overlap(span,h.anchor_span(verse,m)) for m in mappings), item
        mappings.append(mapping)
        changes.append({'type':'inhoudelijke_aanvulling','ref':ref,'koppeling':mapping})
    known = h.glossary(chapters)
    for review in plan['bronmarkeringen_beoordeeld']:
        ref = review['ref']
        assert ref in plan['snapshots']
        b, c, _ = ref.split('/')
        v = verses[ref]
        new = h.project(v,b,int(c),known,reviewed_boundary=True)
        for m in new:
            m['herkomst'].update(versie=plan['id'],beoordeelde_bronmarkeringen=ref)
            v.setdefault('woordnummers',[]).append(m)
            changes.append({'type':'aanvulling_na_verscontrole','ref':ref,'koppeling':m})
    assert h.immutable(chapters) == h.immutable(original), 'Tekst of grondwoorden gewijzigd'
    return changes


def main(write=False):
    chapters = {(b,int(p.stem)):json.loads(p.read_text()) for b in h.BOOKS for p in (h.ROOT/'data'/b).glob('*.json')}
    before = deepcopy(chapters)
    plan = json.loads(PLAN.read_text())
    changes = prepare(plan,chapters)
    audit = h.audit(chapters)
    reviewed = {tuple([r['ref'].split('/')[0], *map(int,r['ref'].split('/')[1:])]) for r in plan['bronmarkeringen_beoordeeld']}
    unresolved = [i for i in audit['technische_problemen'] if not(i['probleem']=='versgrens_controleren' and tuple(i['referentie']) in reviewed)]
    assert not unresolved, unresolved
    if write and changes:
        for (b,c), data in chapters.items():
            if data != before[b,c]:
                path = h.ROOT/'data'/b/f'{c}.json'
                path.write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n')
        for b in h.BOOKS:
            path = h.ROOT/'data/woordnummers-inline'/f'{b}.json'
            fallback = json.loads(path.read_text())
            projection = {str(c):{str(v['number']):v.get('woordnummers',[]) for v in d['verses'] if v.get('woordnummers')} for (book,c),d in chapters.items() if book==b}
            if fallback['chapters'] != projection:
                fallback['chapters'] = projection
                fallback['source']['pipeline_version'] = plan['id']
                path.write_text(json.dumps(fallback,ensure_ascii=False,separators=(',',':'))+'\n')
        report = {'id':plan['id'], 'wijzigingen':changes, 'tellingen':audit['tellingen'],
                  'inhoudelijk_beoordeelde_bronmarkeringen':plan['bronmarkeringen_beoordeeld'],
                  'technische_problemen_na_beoordeling':unresolved,
                  'beoordeeld_zonder_bronnummer':plan['beoordeeld_zonder_bronnummer'],
                  'volledig_inhoudelijk_gecontroleerd':False}
        (h.ROOT/'reviews/geez/vervolgcontrole-2026-11-07.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
    print(json.dumps({'schrijven':write,'wijzigingen':dict(Counter(x['type'] for x in changes)),
                      'open_grondwoorden':sum(x['genummerde_grondwoorden_zonder_koppeling'] for x in audit['tellingen'].values()),
                      'onopgeloste_technische_problemen':len(unresolved)},ensure_ascii=False))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--write',action='store_true')
    main(parser.parse_args().write)
