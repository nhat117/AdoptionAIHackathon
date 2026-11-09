import json,sys,tempfile,unittest
from pathlib import Path
from types import SimpleNamespace
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import adaption_dataset as integration
class Status:
 status='awaiting_input';row_count=32
 def model_dump(self,**kwargs):return {'status':self.status,'row_count':self.row_count}
class FakeDatasets:
 def __init__(self):self.uploads=[];self.adaptations=[]
 def upload_file(self,path):self.uploads.append(path);return SimpleNamespace(dataset_id='test-dataset')
 def get_status(self,dataset_id):return Status()
 def adapt(self,dataset_id,**kwargs):
  self.adaptations.append(kwargs)
  return SimpleNamespace(model_dump=lambda **kw:{'estimated_credits_consumed':1})
class IntegrationTests(unittest.TestCase):
 def test_prepare_and_resume_upload_estimate_only(self):
  with tempfile.TemporaryDirectory() as temp:
   out=Path(temp);manifest=integration.prepare(out)
   self.assertEqual(manifest['development_rows'],32)
   self.assertEqual(manifest['development_source_trials'],64)
   self.assertEqual(manifest['evaluation_local_only_rows'],1200)
   rows=[json.loads(x) for x in (out/manifest['upload_file']).read_text().splitlines()]
   self.assertTrue(all(r['split']=='development' for r in rows))
   self.assertTrue(all('evaluation-' not in r['task_id'] for r in rows))
   self.assertTrue(all(len(r['instruction'])==3 and json.loads(r['response'])['task_id']==r['task_id'] for r in rows))
   fake=FakeDatasets();client=SimpleNamespace(datasets=fake)
   integration.workflow(client,out,estimate=True)
   integration.workflow(client,out,estimate=False)
   self.assertEqual(len(fake.uploads),1)
   self.assertEqual(len(fake.adaptations),1)
   self.assertTrue(fake.adaptations[0]['estimate'])
   self.assertFalse(fake.adaptations[0]['recipe_specification']['recipes']['prompt_rephrase'])
 def test_tampered_export_rejected(self):
  with tempfile.TemporaryDirectory() as temp:
   out=Path(temp);m=integration.prepare(out)
   (out/m['upload_file']).write_text('{}\n')
   fake=FakeDatasets()
   with self.assertRaises(AssertionError):integration.workflow(SimpleNamespace(datasets=fake),out)
   self.assertEqual(fake.uploads,[])
if __name__=='__main__':unittest.main()
