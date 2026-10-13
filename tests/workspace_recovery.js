// Exercise the actual browser recovery functions with neutral DOM/transport objects.
// No server, workbook, numerical engine, browser or deployed-image acceptance.
const fs=require('node:fs'),path=require('node:path'),vm=require('node:vm'),assert=require('node:assert/strict');
const root=path.join(__dirname,'..'),html=fs.readFileSync(path.join(root,'src/lic_dsf/web.html'),'utf8');
const hosted=fs.readFileSync(path.join(root,'src/lic_dsf/hosted.py'),'utf8');
function section(start,end){const a=html.indexOf(start),b=html.indexOf(end,a);assert(a>=0&&b>a);return html.slice(a,b);}
function line(name){const found=html.split('\n').find(value=>value.startsWith('function '+name+'(')||value.startsWith('async function '+name+'('));assert(found,'Missing actual function '+name);return found;}
const functions=section('// Workspace recovery:','// End workspace recovery helpers.')+'\n'+
 ['request','readContext','canSwitch','sourceCurrent','renderWorkspaceHint','refreshRunStates'].map(line).join('\n')+'\n'+
 section('async function refreshBoot(){','function renderWorkspaceHint')+'\n'+section('async function accepted(x){','function renderEditor');
const A='a'.repeat(64),B='b'.repeat(64),C='c'.repeat(64),rows=[11,13,15,17,20,22,24,28,30,32,34,36,38];
function bootData(token='valid-token'){return {token,title:'Neutral test',note:'Illustrative',example_available:true,example_requires_download:false,example_label:'Official illustrative example',illustrative_example:true,workbooks:[{sha:A,label:'Saved workbook'},{sha:B,label:'Another workbook'}]};}
function workbook(sha=B){const definition={delta_paths:Object.fromEntries(rows.map(row=>[String(row),Array(21).fill(0)])),terms:null};return {
 inspection:{workbook_sha256:sha,compatibility:{status:'supported'},first_projection_year:2024,input_years:Array.from({length:21},(_,i)=>2024+i),input_specs:rows.map(row=>({row,name:'Neutral input '+row,units:'test units'})),customization:{terms:{rate:{mode:'formula',value:.08},grace_years:{mode:'value',value:4},maturity_years:{mode:'value',value:9}}}},
 zero:definition,imported:structuredClone(definition),scenarios:[{id:'saved',name:'Saved case',share_label:'Case',revision:1}],
 baseline_preview:[{metric:'ext_pv_gdp',year:2024,units:'percent of GDP',reference_baseline:20}],builtin_investment_cases:[],chart_context:{workbook_sha256:sha,revision:0,label:null}
 };}
const response=(body,status=200)=>({ok:status>=200&&status<300,status,json:async()=>body});
const nonJSON=status=>({ok:status>=200&&status<300,status,json:async()=>{throw SyntaxError('not JSON');}});
function deferred(){let resolve,reject;const promise=new Promise((yes,no)=>{resolve=yes;reject=no;});return {promise,resolve,reject};}
function setup(hostedVisit=true){
 const elements={},calls=[],messages=[],timers=new Set();let responder=()=>response({error:'Unexpected request'},500),confirms=0,consent=true;
 function element(id){return elements[id]??={value:'',textContent:'',innerHTML:'',disabled:false,classes:new Set(),classList:{add(name){element(id).classes.add(name);},remove(name){element(id).classes.delete(name);},toggle(name,on){if(on)element(id).classes.add(name);else element(id).classes.delete(name);}},querySelector:()=>({focus(){}}),scrollIntoView(){}};}
 const $=element,s={JSON,Array,Object,Set,Map,Number,Error,AbortController,structuredClone,encodeURIComponent,$,
  boot:bootData(),ctx:workbook(A),sha:A,active:{id:'saved',revision:1},draft:{neutral:'old draft'},dirty:false,journalDirty:false,contextDirty:false,uiBusy:false,calculating:false,
  selection:new Set(['saved']),comparison:{neutral:'old valid result'},knownRuns:new Map([['saved',{revision:1,current:true}]]),currentRun:true,editorReference:{neutral:'old reference'},contextRecord:{workbook_sha256:A,revision:1,label:'Saved heading'},sourceGeneration:7,baselineAcknowledged:true,sharedNotes:{neutral:'saved note'},
  document:{title:'Old title',getElementById:id=>id==='deleteVisit'&&!hostedVisit?null:element(id)},location:{href:'/app'},
  esc:value=>String(value??''),status:(text,error=false)=>messages.push({text,error}),updateWorkflow(){},
  clearComparison(){s.comparison=null;},renderBuiltinInvestment(){},renderEditor(){},renderCases(){},showBaseline(){},renderContext(){},updatePeriodUnits(){},
  setTimeout(callback){const timer={callback};timers.add(timer);return timer;},clearTimeout(timer){timers.delete(timer);},
  confirm(){confirms++;return consent;},fetch:async(url,options)=>{calls.push({url,options});return responder(url,options);}
 };
 $('title').textContent='Old title';$('workbookSelect').value=A;$('workbookSelect').innerHTML='OLD SAVED OPTIONS';$('workspaceRecovery').classes.add('hidden');$('visitRecoveryEntry').classes.add('hidden');
 vm.createContext(s);vm.runInContext(functions,s);
 return {s,$,calls,messages,timers,setResponder:fn=>{responder=fn;},confirms:()=>confirms,setConsent:value=>{consent=value;},retry:()=>s.retryWorkspaceLoad(),pending:()=>vm.runInContext('pendingWorkspaceRetry',s)};
}
function retained(t){return {boot:t.s.boot,ctx:t.s.ctx,sha:t.s.sha,active:t.s.active,draft:t.s.draft,comparison:t.s.comparison,knownRuns:t.s.knownRuns,selection:t.s.selection,editorReference:t.s.editorReference,contextRecord:t.s.contextRecord,currentRun:t.s.currentRun,baselineAcknowledged:t.s.baselineAcknowledged,sharedNotes:t.s.sharedNotes};}
function preserved(t,before){for(const [key,value] of Object.entries(before))assert.strictEqual(t.s[key],value,key+' must remain unchanged');}
function goodTransport(t,value=workbook()){t.setResponder(url=>url==='/api/boot'?response(bootData('refreshed-token')):url.startsWith('/api/workbook')?response(value):url.startsWith('/api/scenario')?response({scenario:{revision:1},run:{result:{evidence:{calculation:'computed_unverified'}}}}):response({error:'Unexpected'},500));}
(async()=>{
 let checks=0;
 for(const status of [401,429,503]){
  const t=setup(),before=retained(t);t.setResponder(()=>response({error:'Neutral HTTP refusal'},status));
  await assert.rejects(t.s.refreshBoot(),/Neutral HTTP refusal/);preserved(t,before);
  assert.equal(t.$('title').textContent,'Old title');assert.equal(t.$('workbookSelect').innerHTML,'OLD SAVED OPTIONS');assert.equal(t.timers.size,0);
  assert.equal(t.$('visitRecoveryEntry').classes.has('hidden'),status!==401);
  assert.equal(t.$('retryWorkspaceLoad').classes.has('hidden'),status===401);
  assert(t.calls.every(call=>call.options.method==='GET'));checks++;
 }
 const badBoots=[null,{}, {...bootData(),token:null},{...bootData(),token:''},{...bootData(),title:null},{...bootData(),note:null},{...bootData(),example_available:'true'},{...bootData(),example_requires_download:0},{...bootData(),illustrative_example:null},{...bootData(),example_label:null},{...bootData(),workbooks:{}},{...bootData(),workbooks:[{sha:'wrong',label:'Saved'}]},{...bootData(),workbooks:[{sha:A,label:null}]}];
 for(const body of badBoots){const t=setup(),before=retained(t);t.setResponder(()=>response(body));await assert.rejects(t.s.refreshBoot(),/incomplete/);preserved(t,before);assert.equal(t.timers.size,0);checks++;}
 for(const mode of ['transport','nonJSON']){
  const t=setup(),before=retained(t);t.setResponder(()=>mode==='transport'?Promise.reject(TypeError('network lost')):nonJSON(502));
  await assert.rejects(t.s.refreshBoot(),/could not be reached|unreadable/);preserved(t,before);
  goodTransport(t);await t.retry();assert.equal(t.s.boot.token,'refreshed-token');assert.equal(t.s.ctx,before.ctx);assert.equal(t.s.draft,before.draft);assert(t.$('workspaceRecovery').classes.has('hidden'));checks++;
 }
 {
  const t=setup();t.s.boot=undefined;t.setResponder(()=>Promise.reject(TypeError('offline')));
  await assert.rejects(t.s.refreshBoot());await t.s.deleteHostedVisit();assert.equal(t.calls.filter(call=>call.url==='/api/delete').length,0);
  goodTransport(t);await t.retry();assert.equal(t.s.boot.token,'refreshed-token');assert.equal(t.s.sha,A);checks++;
 }
 const corrupt=[()=>null,body=>({...body,inspection:{...body.inspection,workbook_sha256:C}}),body=>({...body,inspection:{...body.inspection,input_years:[2024]}}),body=>({...body,zero:{delta_paths:{},terms:null}}),body=>({...body,scenarios:{}}),body=>({...body,chart_context:{workbook_sha256:C,revision:0,label:null}}),body=>({...body,baseline_preview:[{metric:'neutral',year:2024,units:'ratio',reference_baseline:{wrong:true}}]})];
 for(const mode of ['transport','nonJSON','HTTP',...corrupt]){
  const t=setup(),before=retained(t);t.$('workbookSelect').value=B;
  t.setResponder(()=>typeof mode==='function'?response(mode(workbook())):mode==='transport'?Promise.reject(TypeError('offline')):mode==='nonJSON'?nonJSON(502):response({error:'Read refused'},503));
  await assert.rejects(t.s.loadWorkbook(B));preserved(t,before);assert.equal(t.s.sourceGeneration,8,'failure must not restore old callback generation');assert.equal(t.s.sourceCurrent({sha:A,generation:7}),false);assert.equal(t.$('workbookSelect').value,A);assert.equal(t.pending().sha,B);assert.equal(t.timers.size,0);checks++;
 }
 {
  const t=setup(),before=retained(t),pending=deferred(),body=workbook();t.setResponder(url=>url.startsWith('/api/workbook')?pending.promise:response({scenario:{revision:1},run:null}));
  const loading=t.s.loadWorkbook(B);preserved(t,before);assert.equal(t.s.sourceGeneration,8);assert.equal(t.s.sourceCurrent({sha:A,generation:7}),false);
  pending.resolve(response(body));assert.equal(await loading,true);assert.equal(t.s.sha,B);assert.equal(t.s.ctx,body);assert.equal(t.s.sourceGeneration,8);assert.equal(t.s.sourceCurrent({sha:B,generation:8}),true);assert.notEqual(t.s.draft,body.zero);assert.notEqual(t.s.draft.delta_paths,body.zero.delta_paths);assert.notEqual(t.s.editorReference,t.s.draft);assert.equal(t.s.active,null);assert.equal(t.s.comparison,null);checks++;
 }
 {
  const t=setup(),before=retained(t),pending=deferred();t.setResponder(()=>pending.promise);const loading=t.s.loadWorkbook(B);
  t.s.dirty=true;t.s.draft.neutral='edit while waiting';pending.resolve(response(workbook()));assert.equal(await loading,false);preserved(t,before);assert.equal(t.s.dirty,true);assert.equal(t.s.sourceGeneration,8);assert.equal(t.$('workbookSelect').value,A);checks++;
 }
 {
  const t=setup(),first=deferred(),second=deferred();t.setResponder(url=>url.includes(B)?first.promise:url.includes(C)?second.promise:response({scenario:{revision:1},run:null}));
  const one=t.s.loadWorkbook(B),two=t.s.loadWorkbook(C);assert.equal(t.s.sourceGeneration,9);second.resolve(response(workbook(C)));assert.equal(await two,true);const winner=t.s.ctx;
  first.resolve(response(workbook(B)));assert.equal(await one,false);assert.equal(t.s.sha,C);assert.equal(t.s.ctx,winner);assert.equal(t.s.sourceGeneration,9);assert.equal(t.s.sourceCurrent({sha:C,generation:9}),true);checks++;
 }
 {
  const t=setup(),before=retained(t),first=deferred(),second=deferred();t.setResponder(url=>url.includes(B)?first.promise:second.promise);
  const one=t.s.loadWorkbook(B),two=t.s.loadWorkbook(C);second.resolve(response({error:'latest read failed'},503));await assert.rejects(two,/latest read failed/);
  first.resolve(response(workbook(B)));assert.equal(await one,false);preserved(t,before);assert.equal(t.s.sourceGeneration,9);assert.equal(t.pending().sha,C);assert.equal(t.s.sourceCurrent({sha:A,generation:7}),false);checks++;
 }
 {
  // The first workbook commits, then its saved-run read waits. A newer workbook
  // read fails before that old saved-run response arrives: its retry must survive.
  const t=setup(),runs=deferred(),runStarted=deferred();
  t.setResponder(url=>url.includes(B)?response(workbook(B)):url.includes(C)?response({error:'newer workbook read failed'},503):url.startsWith('/api/scenario')?(runStarted.resolve(),runs.promise):response({error:'Unexpected request'},500));
  const older=t.s.loadWorkbook(B);await runStarted.promise;
  assert.equal(t.s.sha,B);assert.equal(t.s.sourceGeneration,8);const committed=retained(t);
  await assert.rejects(t.s.loadWorkbook(C),/newer workbook read failed/);
  const retry=t.pending(),notice=t.$('workspaceRecoveryText').textContent;
  assert.equal(retry.sha,C);assert.equal(t.s.sourceGeneration,9);assert.equal(t.$('workspaceRecovery').classes.has('hidden'),false);
  runs.resolve(response({scenario:{revision:1},run:{result:{evidence:{calculation:'computed_unverified'}}}}));
  assert.equal(await older,false,'old post-commit completion is stale');preserved(t,committed);
  assert.equal(t.pending(),retry,'old completion must retain the newer retry object');assert.equal(t.pending().sha,C);
  assert.equal(t.$('workspaceRecovery').classes.has('hidden'),false);assert.equal(t.$('workspaceRecoveryText').textContent,notice);assert.equal(t.$('retryWorkspaceLoad').classes.has('hidden'),false);
  assert.equal(t.s.sourceCurrent({sha:B,generation:8}),false);assert.equal(t.timers.size,0);
  goodTransport(t,workbook(C));await t.retry();assert.equal(t.s.sha,C);assert.equal(t.pending(),null);assert.equal(t.$('workspaceRecovery').classes.has('hidden'),true);assert.equal(t.calls.filter(call=>call.options.method==='POST').length,0);checks++;
 }
 {
  const t=setup(),before=retained(t);t.setResponder(()=>response({error:'temporarily unavailable'},503));
  await assert.rejects(t.s.accepted({accepted:true,inspection:{workbook_sha256:B}}));preserved(t,before);assert.equal(t.pending().sha,B);
  await assert.rejects(t.retry());assert.equal(t.pending().sha,B,'failed boot retry retains the requested workbook');
  goodTransport(t);await t.retry();assert.equal(t.s.sha,B);assert.equal(t.s.ctx.scenarios.length,1);assert.equal(t.calls.filter(call=>call.options.method==='POST').length,0,'retry never creates a scenario or re-registers the example');checks++;
 }
 {
  const t=setup();t.setResponder(()=>response({error:'unavailable'},503));await assert.rejects(t.s.loadWorkbook(B));t.s.dirty=true;const n=t.calls.length;await t.retry();assert.equal(t.calls.length,n);assert.equal(t.s.sha,A);assert.equal(t.pending().sha,B);checks++;
 }
 for(const mode of ['HTTP','transport','nonJSON','malformed','contradictory','pendingStatus']){
  const t=setup(),before=retained(t);t.setResponder(()=>mode==='HTTP'?response({error:'Delete refused'},503):mode==='transport'?Promise.reject(TypeError('lost response')):mode==='nonJSON'?nonJSON(200):mode==='contradictory'?response({deleted:true,error:'not confirmed'}):mode==='pendingStatus'?response({deleted:true},202):response({deleted:false}));
  await t.s.deleteHostedVisit();preserved(t,before);assert.equal(t.s.location.href,'/app');assert.equal(t.$('deleteVisit').disabled,false);assert.match(t.messages.at(-1).text,/Deletion was not confirmed/);assert.equal(t.timers.size,0);checks++;
 }
 {
  const t=setup(),before=retained(t),pending=deferred();t.setResponder(()=>pending.promise);
  const deleting=t.s.deleteHostedVisit();await t.s.deleteHostedVisit();assert.equal(t.confirms(),1);assert.equal(t.calls.length,1);assert.equal(t.calls[0].options.method,'POST');assert.equal(t.calls[0].options.headers['X-DSF-Token'],'valid-token');assert.equal(t.$('deleteVisit').disabled,true);preserved(t,before);
  pending.resolve(response({deleted:true}));await deleting;assert.equal(t.s.location.href,'/?deleted=1');assert.equal(t.$('deleteVisit').disabled,true);await t.s.deleteHostedVisit();assert.equal(t.calls.length,1);checks++;
 }
 {
  const t=setup(),before=retained(t);let deleted=false;t.setResponder(()=>{if(!deleted){deleted=true;throw TypeError('response lost after server delete');}return response({error:'Visit expired or unavailable'},401);});
  await t.s.deleteHostedVisit();preserved(t,before);assert.equal(t.s.location.href,'/app');await t.s.deleteHostedVisit();assert.equal(t.s.location.href,'/app');assert.equal(t.$('visitRecoveryEntry').classes.has('hidden'),false);assert.match(t.messages.at(-1).text,/already unavailable or has expired/);assert.match(t.messages.at(-1).text,/Deletion was not confirmed/);assert.equal(t.calls.length,2);checks++;
 }
 {
  const t=setup();t.setConsent(false);await t.s.deleteHostedVisit();assert.equal(t.calls.length,0);assert.equal(t.s.location.href,'/app');checks++;
 }
 {
  const t=setup(),before=retained(t);t.setResponder((url,options)=>new Promise((yes,no)=>options.signal.addEventListener('abort',()=>no(Error('deadline')),{once:true})));
  const loading=t.s.loadWorkbook(B);assert.equal(t.timers.size,1);[...t.timers][0].callback();await assert.rejects(loading,/could not be reached/);preserved(t,before);assert.equal(t.timers.size,0);assert.equal(t.s.sourceGeneration,8);checks++;
 }
 assert(hosted.includes("document.getElementById('deleteVisit').onclick=deleteHostedVisit;"));
 assert(html.includes("$('retryWorkspaceLoad').onclick=()=>attempt(retryWorkspaceLoad);"));
 console.log('PASS '+checks+' workspace recovery behavior cases; neutral VM transport/DOM only, not browser, numerical or deployment acceptance.');
})().catch(error=>{console.error(error);process.exitCode=1;});
