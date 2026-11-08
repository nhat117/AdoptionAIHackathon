import React, { useMemo, useState } from 'react';
import { Button, DataComponent, DataTable, Dialog, EvidenceChart, Filters, MetricCard, Section, SortableItem, SortableRegion, useDashboardTabs, useDataApp } from '../../data-app-public.jsx';
import './protection.css';

const tabs = [
  {id:'research',label:'Research',filterIds:['cohort','model','language'],defaultFilters:{cohort:'Adaption pilot'}},
  {id:'monitoring',label:'Monitoring',filterIds:['cohort','model','language'],defaultFilters:{cohort:'Adaption pilot'}},
  {id:'protection',label:'Protection',filterIds:['cohort','model','language'],defaultFilters:{cohort:'Historical'}},
  {id:'health',label:'Run health',filterIds:['cohort','model'],defaultFilters:{cohort:'Adaption pilot'}},
];
const slug = s => s.toLowerCase().replace(/[^a-z0-9]+/g,'-');
const pct = (n,d) => d ? `${(100*n/d).toFixed(1)}%` : '—';
const count = (rows,key) => rows.reduce((n,r)=>n+(r[key]===true?1:0),0);
const unique = (rows,key) => [...new Set(rows.map(r=>r[key]))];
const col = (field,label,extra={})=>({field,label,...extra});
const median = values => {const a=values.filter(Number.isFinite).sort((a,b)=>a-b);return a.length?(a[Math.floor((a.length-1)/2)]+a[Math.ceil((a.length-1)/2)])/2:null;};
const colors = {Peer:'var(--chart-1)',Director:'var(--chart-2)','Completed response':'var(--chart-3)','Failed request':'var(--chart-2)','Output only':'var(--chart-1)','Full trace':'var(--chart-2)','Before gate':'var(--chart-2)','After gate':'var(--chart-3)'};

function Empty({children}) {return <div className="guard-empty">{children}</div>;}
function TableBlock({id,queryId,title,rows,sourceRows,columns,onRowSelect,searchable=true,children}) {
 return <DataComponent variant="card" id={id} queryId={queryId} kind="table" title={title} displayRows={rows} sourceRows={sourceRows}>
  <DataTable rows={rows} columns={columns} rowKey="id" caption={title} searchable={searchable} onRowSelect={onRowSelect} rowActionLabel={r=>`Inspect ${r.trial_id||r.case_id||r.model}`}/>{children}
 </DataComponent>;
}
function KPI({id,title,value,note,queryId='targets',rows}) {
 return <MetricCard id={id} queryId={queryId} title={title} value={value} displayRows={rows} sourceRows={rows}><p className="guard-kpi-note">{note}</p></MetricCard>;
}
function Metrics({items}) {
 return <SortableRegion id="guard:metrics" variant="freeform" className="guard-kpis" authoredRevision={1}>
  {items.map(i=><SortableItem key={i.id} id={i.id} kind="metric" label={i.title}><KPI {...i}/></SortableItem>)}
 </SortableRegion>;
}
function Warning({rows}) {
 const completed=rows.filter(r=>r.completed).length,failed=rows.length-completed;
 if(!failed)return null;
 return <div className="guard-warning" role="status"><span className="guard-status-dot"/><div><strong>Partial response coverage</strong><p>{completed.toLocaleString()} of {rows.length.toLocaleString()} target calls returned a response; {failed.toLocaleString()} failed. Rates describe returned responses only. This is not a completed benchmark.</p></div></div>;
}
function MarkerCharts({cells}) {
 return <SortableRegion id="guard:marker-charts" variant="freeform" className="guard-chart-grid" authoredRevision={1}>
 {unique(cells,'model').map(model=>{
  const rr=cells.filter(r=>r.model===model),display=rr.map(r=>({...r,disclosureRate:r.asr}));
  const id=`asr-${slug(model)}`;
  return <SortableItem key={id} id={id} kind="chart" label={model}>
   <EvidenceChart variant="card" id={id} queryId="cells" title={model} rows={display} sourceRows={rr} height={230}
     spec={{type:'bar',x:'language',y:'disclosureRate',series:'sender',stackable:false,colors,valueDecimals:1,annotations:[{id:'probability-bound',kind:'benchmark',measure:'disclosureRate',field:'probabilityCeiling',label:'Scale maximum (100%)'}]}}
     description="Normalized marker disclosures / completed attack responses. Exact planned and completed cell sizes are shown below.">
    <div className="guard-cell-counts" data-reviewed-rows>{unique(rr,'language').map(lang=><div key={lang}><strong>{lang}</strong>{rr.filter(r=>r.language===lang).map(r=><span key={r.sender}><i style={{background:colors[r.sender]}}/>{r.sender}: <b>{r.leaks}/{r.completed}</b><small>{r.completed}/{r.planned} returned</small></span>)}</div>)}</div>
   </EvidenceChart>
  </SortableItem>;
 })}
 </SortableRegion>;
}
function Research({targetRows,cells,setSelected}) {
 const good=targetRows.filter(r=>r.completed),attacks=good.filter(r=>r.condition==='Attack'),benign=good.filter(r=>r.condition==='Benign');
 const med=median(good.map(r=>r.latency_s));
 const items=[
  {id:'coverage-rate',title:'Completed target calls',value:`${good.length} / ${targetRows.length}`,note:`${pct(good.length,targetRows.length)} response coverage`,rows:targetRows},
  {id:'marker-rate',title:'Observed marker disclosure',value:pct(count(attacks,'leak'),attacks.length),note:`${count(attacks,'leak')} / ${attacks.length} completed attack responses`,rows:attacks},
  {id:'benign-rate',title:'Benign task completion',value:pct(count(benign,'utility_complete'),benign.length),note:`${count(benign,'utility_complete')} / ${benign.length} completed benign responses`,rows:benign},
  {id:'latency',title:'Median target latency',value:med==null?'—':`${med.toFixed(2)}s`,note:'Recomputed from completed responses',rows:good},
 ];
 const tableRows=targetRows.map(r=>({...r,outcome:!r.completed?r.error:r.leak?'Marker disclosed':r.utility_complete?'Report complete':'Structure / utility failure'}));
 return <><Warning rows={targetRows}/><Metrics items={items}/>
  <Section id="research-coverage-heading" title="Response coverage" spacing="after-metrics"><EvidenceChart id="research-coverage" queryId="targets" variant="card" title="Returned responses and failed requests" sourceRows={targetRows} height={180}
   rows={unique(targetRows,'model').flatMap(model=>{const rr=targetRows.filter(r=>r.model===model);return [{model,outcome:'Completed response',calls:rr.filter(r=>r.completed).length},{model,outcome:'Failed request',calls:rr.filter(r=>!r.completed).length}];})}
   spec={{type:'horizontalStackedBar',x:'model',y:'calls',series:'outcome',colors,valueDecimals:0}}/></Section>
  <Section id="marker-heading" title="Marker disclosure by language" spacing="after-metrics"><MarkerCharts cells={cells}/></Section>
  <Section id="responses-heading" title="Response inspection"><TableBlock id="target-records" queryId="targets" title="Target responses" rows={tableRows} sourceRows={targetRows} onRowSelect={setSelected}
   columns={[col('trial_id','Trial'),col('model','Model'),col('language','Language'),col('sender','Sender'),col('condition','Condition'),col('outcome','Outcome'),col('latency_s','Latency (s)')]}/></Section>
 </>;
}
function MonitorView({rows}) {
 const valid=rows.filter(r=>r.completed),bad=valid.filter(r=>r.violation),compliant=valid.filter(r=>!r.violation);
 const items=[
  {id:'monitor-valid',title:'Valid monitor verdicts',value:`${valid.length} / ${rows.length}`,note:`${rows.length-valid.length} failed requests or malformed verdicts`,queryId:'monitors',rows},
  {id:'monitor-recall',title:'Violation recall',value:pct(count(bad,'block'),bad.length),note:`${count(bad,'block')} / ${bad.length} violating responses with valid verdicts`,queryId:'monitors',rows:valid},
  {id:'monitor-fpr',title:'False-positive rate',value:pct(count(compliant,'block'),compliant.length),note:`${count(compliant,'block')} / ${compliant.length} compliant responses with valid verdicts`,queryId:'monitors',rows:valid},
 ];
 const table=[],chart=[];
 for(const model of unique(rows,'model')) for(const visibility of ['Output only','Full trace']) {
  const raw=rows.filter(r=>r.model===model&&r.visibility===visibility),vv=raw.filter(r=>r.completed),viol=vv.filter(r=>r.violation),clean=vv.filter(r=>!r.violation),aa=raw.filter(r=>r.condition==='Attack'),bb=raw.filter(r=>r.condition==='Benign');
  const recall=viol.length?count(viol,'block')/viol.length:null,fpr=clean.length?count(clean,'block')/clean.length:null,release=bb.length?bb.filter(r=>r.utility_complete&&!r.block).length/bb.length:null;
  table.push({id:model+visibility,model,visibility,recall:pct(count(viol,'block'),viol.length),fpr:pct(count(clean,'block'),clean.length),leakage:`${aa.filter(r=>r.leak&&!r.block).length}/${aa.length}`,benign:pct(bb.filter(r=>r.utility_complete&&!r.block).length,bb.length),invalid:raw.length-vv.length});
  for(const [metric,value] of [['Recall',recall],['False-positive rate',fpr],['Benign completion released',release]])chart.push({model,visibility,metric,performanceRate:value});
 }
 return <><Metrics items={items}/>{!valid.length&&<div className="guard-warning"><span className="guard-status-dot"/><div><strong>No monitor-performance estimate available</strong><p>All {rows.length} monitor requests failed. Undefined recall is not 0% or 100% recall.</p></div></div>}
  <Section id="monitor-heading" title="Monitor security and utility" spacing="after-metrics">
  <div className="guard-chart-grid">{unique(rows,'model').map(model=><EvidenceChart key={model} id={`monitor-${slug(model)}`} variant="card" queryId="monitors" title={model} sourceRows={rows.filter(r=>r.model===model)} rows={chart.filter(r=>r.model===model)} height={250}
    spec={{type:'bar',x:'metric',y:'performanceRate',series:'visibility',stackable:false,domain:[0,1],colors,valueDecimals:1}}>
    {!valid.length&&<p className="guard-footnote">No valid verdicts; empty bars mean unavailable evidence.</p>}
  </EvidenceChart>)}</div></Section>
  <Section id="monitor-table-heading" title="Exact counts"><TableBlock id="monitor-counts" queryId="monitors" title="Monitor outcomes" rows={table} sourceRows={rows} searchable={false} columns={[col('model','Target'),col('visibility','Monitor context'),col('recall','Recall'),col('fpr','False-positive rate'),col('leakage','Marker leaks released'),col('benign','Benign completion released'),col('invalid','Errors')]}/><p className="guard-footnote">Classifier rates exclude invalid verdicts; release decisions fail closed on errors. Differential formatting failures can bias valid-verdict comparisons. The marker task does not establish semantic context compression.</p></Section>
 </>;
}
function ProtectionView({rows,replay,setSelected}) {
 const released=rows.filter(r=>r.released),recovered=rows.filter(r=>r.attempts>1);
 if(!rows.length&&!replay.length)return <Empty>No protected live run is available for this selection. Use Historical to inspect the completed 24-case smoke test. No Adaption protection result is being inferred from API failures.</Empty>;
 const beforeAfter=replay.flatMap(r=>[{model:r.model,stage:'Before gate',disclosures:r.raw_marker_disclosures},{model:r.model,stage:'After gate',disclosures:r.released_marker_disclosures}]);
 return <><Metrics items={[
  {id:'protected-cases',title:'Fresh protected cases',value:String(rows.length),note:'Live synthetic attack cases',queryId:'protection',rows},
  {id:'protected-release',title:'Validated reports released',value:`${released.length} / ${rows.length}`,note:'Passed the explicit guard contract',queryId:'protection',rows},
  {id:'protected-retry',title:'Trusted-only recoveries',value:String(recovered.length),note:'At most one retry; peer message removed',queryId:'protection',rows},
 ]}/>
 <Section id="gate-heading" title="Deterministic release boundary" spacing="after-metrics"><div className="guard-chart-grid">
  <EvidenceChart id="guard-replay" variant="card" queryId="replay" title="Observed marker disclosures before and after the gate" sourceRows={replay} rows={beforeAfter} height={265} spec={{type:'bar',x:'model',y:'disclosures',series:'stage',stackable:false,colors,valueDecimals:0}}><p className="guard-footnote">Retrospective replay uses the same explicit marker rule as the scorer. Enforcement is by construction, not independent proof of general injection detection.</p></EvidenceChart>
  <DataComponent id="guard-flow" variant="card" queryId="protection" title="Protected reporting flow" sourceRows={rows} displayRows={rows} kind="custom"><div className="guard-flow"><div><b>01</b><span>Generate candidate<small>Peer content stays lower trust</small></span></div><div><b>02</b><span>Validate in code<small>Schema · identity · checkpoint · marker forms</small></span></div><div><b>03</b><span>Optional monitor veto<small>Cannot override deterministic rejection</small></span></div><div><b>04</b><span>Release or recover once<small>Retry sees only the trusted task</small></span></div></div><p className="guard-footnote">Protection covers the defined reporting policy. A released report remains data for downstream agents.</p></DataComponent>
 </div></Section>
 <Section id="protected-records-heading" title="Protected case inspection"><TableBlock id="protected-records" queryId="protection" title="Fresh smoke cases" sourceRows={rows} rows={rows.map(r=>({...r,id:r.case_id,outcome:r.released?'Released':'Blocked'}))} onRowSelect={setSelected} columns={[col('case_id','Case'),col('model','Target'),col('language','Language'),col('sender','Sender'),col('attempts','Attempts'),col('outcome','Outcome')]}/></Section>
 </>;
}
function Health({targets,monitors,health}) {
 const bars=health.flatMap(r=>[{model:r.model,outcome:'Completed response',calls:r.completed},{model:r.model,outcome:'Failed request',calls:r.failed}]);
 const errors={};for(const r of [...targets,...monitors].filter(r=>!r.completed)){const k=r.error||'Invalid response';errors[k]=(errors[k]||0)+1;}
 const errorRows=Object.entries(errors).map(([error,calls])=>({error,calls}));
 const details=health.map(r=>({...r,id:r.run_id,coverageText:pct(r.completed,r.planned),monitorCoverage:`${r.monitor_completed}/${r.monitor_attempts}`}));
 return <><Warning rows={targets}/><Section id="health-heading" title="Request coverage" spacing="none"><div className="guard-chart-grid">
  <EvidenceChart id="run-coverage" queryId="health" variant="card" title="Completed and failed target requests" sourceRows={health} rows={bars} height={290} spec={{type:'bar',x:'model',y:'calls',series:'outcome',stackable:false,colors,valueDecimals:0}}/>
  <EvidenceChart id="error-types" queryId="targets" queryIds={['targets','monitors']} sourceRowsByQuery={{targets,monitors}} variant="card" title="Request and verdict failures" sourceRows={targets} rows={errorRows} height={290} spec={{type:'horizontalBar',x:'error',y:'calls',colors:{calls:'var(--chart-2)'},valueDecimals:0}}/>
 </div></Section><Section id="health-table-heading" title="Run audit"><TableBlock id="run-audit" queryId="health" title="Run completeness" rows={details} sourceRows={health} searchable={false} columns={[col('run_id','Run'),col('model','Model'),col('planned','Planned target calls'),col('completed','Returned'),col('failed','Failed'),col('coverageText','Coverage'),col('monitorCoverage','Valid monitor / attempted'),col('status','State')]}/><p className="guard-footnote">Snapshot from saved JSONL records on 8 November 2026. This dashboard does not make inference calls or expose API keys.</p></Section></>;
}
export function DashboardContent() {
 const app=useDataApp(); const {activeTabId}=useDashboardTabs(tabs);
 const tab=tabs.some(t=>t.id===activeTabId)?activeTabId:'research';
 const [selected,setSelected]=useState(null),[copied,setCopied]=useState(false);
 const targets=app.reviewedRows('targets'),monitors=app.reviewedRows('monitors'),cells=app.reviewedRows('cells'),health=app.reviewedRows('health'),protection=app.reviewedRows('protection'),replay=app.reviewedRows('replay');
 const copy=async()=>{await navigator.clipboard.writeText(JSON.stringify(selected,null,2));setCopied(true);};
 return <article className="guard-dashboard">
  <Filters sticky filters={app.snapshot.filters ?? []} queries={app.queries} values={app.filters} onChange={app.setFilter}/>
  {tab==='research'&&<Research targetRows={targets} cells={cells} setSelected={r=>{setSelected(r);setCopied(false);}}/>}
  {tab==='monitoring'&&<MonitorView rows={monitors}/>}
  {tab==='protection'&&<ProtectionView rows={protection} replay={replay} setSelected={r=>{setSelected(r);setCopied(false);}}/>}
  {tab==='health'&&<Health targets={targets} monitors={monitors} health={health}/>}
  <Dialog open={!!selected} onClose={()=>setSelected(null)} title="Response inspection" expanded>
   {selected&&<div className="guard-detail"><h2>Response inspection</h2><p className="guard-detail-id">{selected.trial_id||selected.case_id} · {selected.model} · {selected.language}</p>
    {selected.peer_message&&<><h3>Untrusted peer message</h3><pre>{selected.peer_message}</pre></>}
    <h3>{selected.error?'Request error':'Observed model output'}</h3><pre>{selected.error||selected.response||selected.report||'No response returned.'}</pre>
    {selected.audit&&<><h3>Guard audit</h3><pre>{selected.audit}</pre></>}
    <Button onClick={copy}>{copied?'Copied':'Copy record JSON'}</Button>
   </div>}
  </Dialog>
 </article>;
}
