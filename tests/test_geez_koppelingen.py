"""Voorkom foutieve automatische links en verlies bij herstel van versgrenzen."""
from copy import deepcopy
import json
from pathlib import Path
import unittest

from scripts import herstel_ethiopische_koppelingen as h


def word(gloss, number='OVG1', form='ቃለ'):
    return {'woord': form, 'strongs': number, 'betekenis': gloss}


def verse(text, words, number=1):
    return {'number': number, 'text2026': text, 'grondtekst': words}


class ProjectionTests(unittest.TestCase):
    def project(self, text, words):
        return h.project(verse(text, words), 'henoch', 1, {})

    def test_content_word_from_grammatical_gloss(self):
        mappings = self.project('De hand rustte daar.', [word('zijn hand')])
        self.assertEqual(mappings[0]['tekst'], 'hand')
        self.assertEqual(mappings[0]['herkomst']['grondindices'], [0])

    def test_no_function_word_or_negation_projection(self):
        self.assertEqual(self.project('En in zijn hand.', [word('en'), word('in')]), [])
        self.assertEqual(self.project('Hij zag haar.', [word('hij zag niet')]), [])

    def test_repeated_words_and_competing_source_are_ambiguous(self):
        self.assertEqual(self.project('God sprak tot God.', [word('God')]), [])
        self.assertEqual(self.project('De hand.', [word('hand'), word('zijn hand', 'OVG2')]), [])
        self.assertEqual(self.project('De hand.', [word('hand'), {'woord':'ander', 'betekenis':'hand'}]), [])

    def test_repeated_alternative_cannot_be_evaded(self):
        # Een unieke Heere mag de twee mogelijke God-plaatsen niet verbergen.
        self.assertEqual(self.project('De Heere God sprak tot God.', [word('God/Heere')]), [])

    def test_no_number_is_invented_and_unknown_boundaries_are_skipped(self):
        self.assertEqual(self.project('De hand.', [{'woord':'ቃለ','betekenis':'hand'}]), [])
        self.assertEqual(self.project('De hand.', [{'woord':'1:2'}, word('hand')]), [])

    def test_gloss_reuse_requires_same_form_number_and_unambiguous_gloss(self):
        known = h.glossary({('henoch',1):{'verses':[verse('hand', [word('hand')])]}})
        self.assertEqual(h.gloss_for({'woord':'ቃለ', 'strongs':'OVG1'}, known)[0], 'hand')
        self.assertEqual(h.gloss_for({'woord':'ቃለ', 'strongs':'OVG2'}, known)[0], '')
        known[('ቃለ','OVG1')]['woord'] = ['henoch',2,1,0]
        self.assertEqual(h.gloss_for({'woord':'ቃለ', 'strongs':'OVG1'}, known)[0], '')

    def test_existing_anchor_and_source_are_not_reused(self):
        v = verse('De hand.', [word('hand')])
        v['woordnummers'] = [h.mapping_for(v,'henoch',1,0,'hand','hand')]
        self.assertEqual(h.project(v,'henoch',1,{}), [])

    def test_visible_text_ignores_notes_and_obeys_word_boundaries(self):
        v = {'text2026_html':'Een <i>hand</i><sup>hand</sup> en handel.'}
        self.assertEqual(h.plain(v), 'Een hand en handel.')
        self.assertEqual(len(h.spans(h.plain(v), 'hand')), 1)

    def test_split_preserves_every_source_object_and_reindexes_mapping(self):
        words = [word('hand'), {'woord':'4'}, word('stad','OVG2','ከተማ')]
        v = verse('hand', words, 3)
        v['woordnummers'] = [h.mapping_for(v,'jubileeen',11,2,'stad','stad')]
        chapters = {('jubileeen',11):{'verses':[v,verse('stad',[],4)]}}
        invariant = h.immutable(chapters)
        changes = []
        h.split_jubilees(chapters, changes)
        self.assertEqual(h.immutable(chapters), invariant)
        target = chapters['jubileeen',11]['verses'][1]
        self.assertEqual(h.indices(target['woordnummers'][0]), [1])
        self.assertEqual(target['grondtekst'][1]['woord'], 'ከተማ')
        snapshot = deepcopy(chapters)
        h.split_jubilees(chapters, [])
        self.assertEqual(chapters, snapshot)

    def test_split_refuses_to_overwrite_existing_source(self):
        chapters = {('jubileeen',11):{'verses':[
            verse('hand',[word('hand'),{'woord':'4'},word('stad')],3),
            verse('stad',[word('stad')],4)]}}
        with self.assertRaises(AssertionError):
            h.split_jubilees(chapters, [])


class CorpusTests(unittest.TestCase):
    def test_all_visible_anchors_and_provenance_and_fallback_match(self):
        chapters = {}
        for book in h.BOOKS:
            fallback = json.loads((h.ROOT/'data'/'woordnummers-inline'/f'{book}.json').read_text())
            for path in (h.ROOT/'data'/book).glob('*.json'):
                data = json.loads(path.read_text())
                chapters[book,int(path.stem)] = data
                for v in data['verses']:
                    self.assertEqual(v.get('woordnummers',[]), fallback['chapters'][path.stem].get(str(v['number']),[]))
        issues = h.audit(chapters)['technische_problemen']
        self.assertEqual([i for i in issues if i['probleem'] != 'versgrens_controleren'], [])


if __name__ == '__main__':
    unittest.main()
