import asyncio, json, sys, time
from pathlib import Path
from datetime import datetime, timezone
ROOT=Path.cwd()
OUT=ROOT/'runs/evacuation-calibration-batch-20261108'
OUT.mkdir(exist_ok=False)
rows=[json.loads(x) for x in (ROOT/'data/evacuation/scenarios.jsonl').read_text().splitlines() if json.loads(x)['split']=='calibration']
jobs=[(study,row['id']) for study in ['A','C'] for row in rows if study=='A' or not row['accurate']]
plan={'model':'openai/gpt-4.1-mini','provider':'openrouter','seeds':5,'planned_A_episodes':80,'planned_C_continuations':50,'max_parallel_scenarios':6,'reported_cost_stop_usd':2,'max_seconds':1200,'started_at':datetime.now(timezone.utc).isoformat(),'jobs':jobs,'status':'running','interpretation':'calibration; no confirmatory inference'}
(OUT/'plan.json').write_text(json.dumps(plan,indent=2))
active=set(); stop=asyncio.Event(); sem=asyncio.Semaphore(6); results=[]
def cost():
 total=0
 for path in OUT.glob('*/calls.jsonl'):
  for line in path.read_text().splitlines():
   try:
    row=json.loads(line)
    if row.get('type')=='provider_metadata': total+=(row.get('usage') or {}).get('cost',0) or 0
   except json.JSONDecodeError: pass
 return total
async def job(study, sid):
 async with sem:
  if stop.is_set():
   results.append({'study':study,'scenario':sid,'status':'not_started_budget_or_time'})
   return
  dest=OUT/f'{study}-{sid}'
  log=(OUT/f'{study}-{sid}.log').open('w')
  cmd=[str(ROOT/'.venv/bin/python'),'-m','swarm_lab.evacuation','run','--study',study,'--scenario-id',sid,'--mode','live','--provider','openrouter','--config','examples/evacuation-openrouter.json','--max-calls','250','--output',str(dest)]
  p=await asyncio.create_subprocess_exec(*cmd,stdout=log,stderr=log)
  active.add(p)
  rc=await p.wait(); active.discard(p); log.close()
  result={'study':study,'scenario':sid,'returncode':rc,'status':'completed' if rc==0 else 'failed_or_interrupted'}
  results.append(result)
  (OUT/'jobs.json').write_text(json.dumps(results,indent=2))
  print(f'{len(results)}/{len(jobs)} {study} {sid}: {result["status"]}; reported cost ${cost():.4f}',flush=True)
async def monitor(tasks):
 started=time.monotonic()
 while not all(t.done() for t in tasks):
  if cost()>=2 or time.monotonic()-started>=1200:
   stop.set()
   for p in list(active):
    if p.returncode is None: p.terminate()
   break
  await asyncio.sleep(3)
async def main():
 tasks=[asyncio.create_task(job(*j)) for j in jobs]
 await asyncio.gather(*tasks,monitor(tasks))
 plan.update(status='stopped' if stop.is_set() else 'finished',reported_cost_usd=cost(),finished_at=datetime.now(timezone.utc).isoformat(),jobs_finished=len(results))
 (OUT/'plan.json').write_text(json.dumps(plan,indent=2))
 (OUT/'jobs.json').write_text(json.dumps(results,indent=2))
 print(json.dumps({k:plan[k] for k in ['status','reported_cost_usd','jobs_finished']}),flush=True)
asyncio.run(main())
