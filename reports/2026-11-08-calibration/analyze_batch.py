import json, statistics
from pathlib import Path
from collections import defaultdict
ROOT=Path.cwd(); B=ROOT/'runs/evacuation-calibration-batch-20261108'
outcomes=[]; manifests=[]; metadata=[]
for p in sorted(B.glob('*/manifest.json')):
 m=json.loads(p.read_text());manifests.append({'run':p.parent.name,**m})
 q=p.parent/'outcomes.jsonl'
 if q.exists(): outcomes += [json.loads(x) for x in q.read_text().splitlines()]
 q=p.parent/'calls.jsonl'
 if q.exists():
  metadata += [r for line in q.read_text().splitlines() if (r:=json.loads(line)).get('type')=='provider_metadata']
groups=defaultdict(list)
for r in outcomes:
 s=r['scenario'];groups[(r['study'],r['arm'],s['disaster'],s['accurate'])].append(r)
summary=[]
for key, rs in sorted(groups.items()):
 entry=dict(zip(['study','arm','disaster','accurate'],key));entry['episodes']=len(rs)
 for metric in ['correct_action_rate','missed_evacuation_rate','unnecessary_evacuation_rate','source_selection_rate','total_payoff']:
  vals=[r[metric] for r in rs if r[metric] is not None]
  entry[metric]=statistics.mean(vals) if vals else None
 summary.append(entry)
lookup={(r['study'],r['scenario']['id'],r['arm']):r for r in outcomes}
pairs=[]
for study,control,treatment in [('A','once_fixed','repeated_fixed'),('A','once_chosen','repeated_chosen'),('C','none','remove'),('C','remove','correction'),('C','correction','linked'),('C','correction','broadcast')]:
 for disaster in [False,True]:
  matched=[]
  for (st,sid,arm),r in lookup.items():
   if st!=study or arm!=control or r['scenario']['disaster']!=disaster: continue
   t=lookup.get((st,sid,treatment))
   if t:
    if study=='C': assert r['shared_snapshot_hash']==t['shared_snapshot_hash']
    matched.append(t['correct_action_rate']-r['correct_action_rate'])
  pairs.append({'study':study,'control':control,'treatment':treatment,'disaster':disaster,'matched_pairs':len(matched),'mean_correct_action_difference':statistics.mean(matched) if matched else None})
report={'completed_outcomes':len(outcomes),'manifests':[{k:m.get(k) for k in ['run','status','model_calls','error_type','completed_episodes']} for m in manifests],'cost_usd':sum((r.get('usage') or {}).get('cost',0) or 0 for r in metadata),'provider_calls':len(metadata),'upstream_providers':sorted({r.get('upstream_provider') or 'unreported' for r in metadata}),'cell_summary':summary,'paired_comparisons':pairs}
(B/'summary.json').write_text(json.dumps(report,indent=2))
print(json.dumps(report,indent=2))
