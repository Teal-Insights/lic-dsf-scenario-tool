// Real page functions, neutral DOM/HTTP substitutes. No browser-download claim.
const fs=require('node:fs'),path=require('node:path'),vm=require('node:vm'),assert=require('node:assert/strict');
const root=path.join(__dirname,'..');
const html=fs.readFileSync(path.join(root,'src/lic_dsf/web.html'),'utf8');
for(const match of html.matchAll(/<script>([\s\S]*?)<\/script>/g))new vm.Script(match[1]);
const generations=html.slice(html.indexOf('function comparisonSnapshot('),html.indexOf('async function compare(){'));
const exp=html.slice(html.indexOf('function interruptedComparison('),html.indexOf("$('chartContextLabel').oninput"));
const workflow=html.slice(html.indexOf('function updateWorkflow(){'),html.indexOf('function adjustmentState('));
const lines=html.split('\n');
const invalidation=['function clearComparison(){','function markContextDirty(){','function markDirty(){'].map(prefix=>lines.find(line=>line.startsWith(prefix))).join('\n');
const bindings=lines.filter(line=>line.startsWith("$('preparedPacketSave').onclick=")||line.startsWith("window.addEventListener('pagehide',")).join('\n');
const queue=fs.readFileSync(path.join(root,'src/lic_dsf/hosted_wait.js'),'utf8');

function setup(queued=false){
 const elements={},requests=[],created=[],revoked=[],downloads=[],timers=[],listeners={};let sequence=0;
 function element(id){
  const classes=new Set(id==='preparedPacketRecovery'?['hidden']:[]),small={textContent:''};
  return {value:id==='comparator'?'case':'ext_pv_gdp',textContent:'',innerHTML:'',dataset:{},disabled:false,checked:false,
   classList:{add:c=>classes.add(c),remove:c=>classes.delete(c),toggle(c,v){if(v)classes.add(c);else classes.delete(c)},contains:c=>classes.has(c)},
   removeAttribute(name){delete this[name]},setAttribute(name,value){this[name]=value},focus(){s.focused=id},querySelector:()=>small,querySelectorAll:()=>[]};
 }
 const blob=new Blob([Uint8Array.from([80,75,3,4,0,255,9,19])]);
 const s={sha:'public-workbook',sourceGeneration:1,comparisonGeneration:0,contextRecord:{revision:2},selection:new Set(['case']),dirty:false,journalDirty:false,contextDirty:false,calculating:false,uiBusy:false,boot:{token:'own',example_available:true},ctx:{scenarios:[{id:'case'}]},active:{id:'case',revision:1,name:'Neutral'},currentRun:true,knownRuns:new Map([['case',{current:true}]]),baselineAcknowledged:true,chartsReady:true,chartError:false,chartURLs:{},exported:false,comparison:{runs:[{result_hash:'unchanged'}]},
  $:id=>elements[id]??=(element(id)),status:(text,error=false)=>{s.lastStatus={text,error}},sourceCurrent:t=>t.sha===s.sha&&t.generation===s.sourceGeneration,
  comparisonRequest:()=>({scenario_ids:[...s.selection],comparator_id:s.$('comparator').value,workbook_sha:s.sha,expected_chart_context_revision:s.contextRecord.revision}),
  contextConflict:async error=>{if(error.message==='context-conflict'){s.clearComparison();return true}return false},clearCharts:()=>{s.chartURLs={};s.chartsReady=false},updateCounters:()=>{},builtinInvestmentChoices:()=>[],
  URL:{createObjectURL(value){const url='blob:packet-'+(++sequence);created.push({url,blob:value});return url},revokeObjectURL:url=>revoked.push(url)},
  document:{querySelectorAll:()=>[],createElement:()=>({click(){downloads.push({url:this.href,name:this.download})}})},
  window:{addEventListener:(name,fn)=>{listeners[name]=fn}},
  setTimeout:(fn,ms)=>{timers.push({fn,ms});return timers.length},clearTimeout:()=>{},AbortController,Response,Blob,crypto:{randomUUID:()=> 'neutral-request'},
  request:async(route,data)=>{requests.push({route,data});if(s.onRequest)await s.onRequest();if(s.error)throw s.error;return {blob:async()=>blob}},
  fetch:async(route,options)=>{requests.push({route,body:options.body});if(route==='/api/export-jobs')return Response.json({job_id:'job'});if(route.startsWith('/api/export-status'))return Response.json({status:'ready'});if(route.startsWith('/api/export-result'))return new Response(blob);if(route==='/api/export-cancel')return Response.json({cancelled:true});throw Error(route)}
 };
 vm.createContext(s);vm.runInContext(generations+'\n'+exp+'\n'+workflow+'\n'+invalidation+'\n'+bindings+(queued?'\n'+queue:''),s);
 function save(){let prevented=false;const a=s.$('preparedPacketSave');a.onclick({preventDefault(){prevented=true}});if(!prevented)downloads.push({url:a.href,name:a.download});return prevented;}
 return {s,blob,requests,created,revoked,downloads,timers,listeners,save};
}

(async()=>{
 for(const queued of [false,true]){
  const t=setup(queued);t.s.updateWorkflow();assert.equal(t.s.$('packet').classList.contains('primary'),true);await t.s.exportFile('zip');
  // The ready packet is saved by a trusted user click: a visible, focused, labelled primary link; the packet button steps back.
  assert.equal(t.s.$('preparedPacketSave').textContent,'Save briefing packet (.zip)');assert.equal(t.s.focused,'preparedPacketSave');
  t.s.updateWorkflow();assert.equal(t.s.$('packet').classList.contains('primary'),false);assert.match(t.s.lastStatus.text,/choose Save briefing packet \(\.zip\)/);
  assert.equal(t.created.length,1);assert.equal(t.downloads.length,1);assert.equal(t.s.$('preparedPacketRecovery').classList.contains('hidden'),false);
  assert.equal(t.s.$('preparedPacketSave').href,t.created[0].url);assert.equal(t.s.$('preparedPacketSave').download,'lic-dsf-briefing-packet.zip');
  assert.deepEqual(Buffer.from(await t.created[0].blob.arrayBuffer()),Buffer.from(await t.blob.arrayBuffer()));
  const before=t.requests.length;assert.equal(t.save(),false);assert.equal(t.save(),false);
  assert.equal(t.requests.length,before);assert.equal(t.created.length,1);assert.equal(t.downloads.length,3);assert.equal(t.downloads[2].url,t.downloads[0].url);assert.equal(t.timers.some(timer=>timer.ms===10000),false);
  t.s.uiBusy=true;assert.equal(t.save(),true);assert.equal(t.downloads.length,3);t.s.uiBusy=false;
  // Replacing a completed packet revokes exactly the previous URL.
  await t.s.exportFile('zip');assert.equal(t.created.length,2);assert.deepEqual(t.revoked,[t.created[0].url]);
  t.listeners.pagehide();assert.deepEqual(t.revoked,[t.created[0].url,t.created[1].url]);assert.equal(t.s.$('preparedPacketSave').href,undefined);
 }
 for(const [label,change] of [
  ['numerical/shared draft',s=>s.markDirty()],['pending chart text',s=>s.markContextDirty()],['clear comparison',s=>s.clearComparison()],
  ['source generation',s=>s.sourceGeneration++],['source identity',s=>s.sha='other-public-workbook'],['selected cases',s=>s.selection.add('other')],
  ['comparator',s=>s.$('comparator').value='other'],['saved chart revision',s=>s.contextRecord.revision++],['new comparison',s=>s.comparison={runs:[]}],['running calculation',s=>s.calculating=true]
 ]){
  const t=setup();await t.s.exportFile('zip');change(t.s);t.s.updateWorkflow();assert.equal(t.s.$('preparedPacketSave').href,undefined,label);assert.equal(t.s.$('preparedPacketRecovery').classList.contains('hidden'),true,label);assert.deepEqual(t.revoked,[t.created[0].url],label);assert.equal(t.save(),true,label);assert.equal(t.downloads.length,1,label);
 }
 const retry=setup();await retry.s.exportFile('zip');const url=retry.s.$('preparedPacketSave').href;retry.s.error=Error('Export service unavailable');await assert.rejects(retry.s.exportFile('zip'),/unavailable/);assert.equal(retry.s.$('preparedPacketSave').href,url);assert.equal(retry.save(),false);assert.equal(retry.created.length,1);
 const stale=setup();stale.s.onRequest=async()=>{stale.s.sourceGeneration++};await stale.s.exportFile('zip');assert.equal(stale.created.length,0);assert.equal(stale.downloads.length,0);
 const conflict=setup();await conflict.s.exportFile('zip');conflict.s.error=Error('context-conflict');await conflict.s.exportFile('zip');assert.equal(conflict.s.$('preparedPacketSave').href,undefined);assert.equal(conflict.created.length,1);
 const independent=setup();await independent.s.exportFile('zip');const retained=independent.s.$('preparedPacketSave').href;await independent.s.exportFile('json');assert.equal(independent.s.$('preparedPacketSave').href,retained);assert.equal(independent.save(),false);assert.equal(independent.timers.at(-1).ms,10000);independent.timers.at(-1).fn();assert.deepEqual(independent.revoked,[independent.created[1].url]);
 console.log('PASS prepared packet recovery: exact returned bytes, ordinary and queued caller reuse without another request, one retained URL, 10 invalidations, busy/stale/refusal/page-close cleanup and unchanged individual-download expiry. Neutral DOM/HTTP tests only; no physical browser download, live, Windows or numerical acceptance.');
})().catch(error=>{console.error(error);process.exitCode=1});
