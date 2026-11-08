import copy,json,sys,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'scripts'))
from pas_geez_vervolg_toe import prepare
class CorrectSpeakingFormula(unittest.TestCase):
 def fixture(self):
  plan=json.loads((ROOT/'reviews/geez/baruch3-plan-2026-11-08.json').read_text())
  row=next(x for x in plan['koppelingen'] if x.get('vervang_koppeling'))
  verse=next(v for v in json.loads((ROOT/'data/4baruch/3.json').read_text())['verses'] if v['number']==6)
  verse['woordnummers']=[row['vervang_koppeling']]
  return {'id':plan['id'],'snapshots':{row['ref']:plan['snapshots'][row['ref']]},'koppelingen':[row],'bronmarkeringen_beoordeeld':[]},{('4baruch',3):{'verses':[verse]}}
 def test_replacement_and_idempotence(self):
  p,c=self.fixture();changes=prepare(p,c);self.assertEqual(changes[0]['type'],'inhoudelijke_correctie');self.assertEqual(c['4baruch',3]['verses'][0]['woordnummers'][0]['tekst'],'zeggende');self.assertEqual(prepare(p,c),[])
 def test_changed_existing_mapping_refused(self):
  p,c=self.fixture();c=copy.deepcopy(c);c['4baruch',3]['verses'][0]['woordnummers'][0]['tekst']='anders'
  with self.assertRaises(AssertionError):prepare(p,c)
