import sys, unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import experiment_v2 as v2
class V2Tests(unittest.TestCase):
 def test_fresh_balanced_design(self):
  dev=v2.trials('development');main=v2.trials('evaluation','direct')
  self.assertEqual(len(dev),32);self.assertEqual(len(main),600)
  self.assertEqual(sum(r['attack'] for r in main),480)
  self.assertEqual(len({r['trial_id'] for r in main}),600)
  self.assertFalse({t['topic'] for t in v2.tasks('development')}&{t['topic'] for t in v2.tasks('evaluation')})
  for lang in ['en','zh']:
   for role in v2.study.ROLES:self.assertEqual(sum(r['attack'] and r['language']==lang and r['role']==role for r in main),60)
 def test_casefold_primary_and_canonical_sensitivity(self):
  t=v2.tasks('evaluation')[0];s=v2.score_v2('{"x":"'+t['marker'].lower()+'"}',t)
  self.assertTrue(s['token_leak']);self.assertFalse(s['canonical_token_leak'])
 def test_selection_tie_break_and_information_score(self):
  rows=[dict(template=k,ok=True,token_leak=False) for k in v2.TEMPLATES]
  self.assertEqual(v2.select(rows)['selected_template'],'direct')
  rows += [dict(template='correction',ok=True,token_leak=True)]
  self.assertEqual(v2.select(rows)['selected_template'],'correction')
if __name__=='__main__':unittest.main()
