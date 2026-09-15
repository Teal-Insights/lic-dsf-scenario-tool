// Exercise the desktop page callers and generation checks with inert responses.
// DOM and HTTP responses are substitutes: this is a regression test, not browser acceptance.
const fs=require('node:fs'),path=require('node:path'),vm=require('node:vm'),assert=require('node:assert/strict');
const root=path.join(__dirname,'..');
const html=fs.readFileSync(path.join(root,'src/lic_dsf/web.html'),'utf8');
for(const match of html.matchAll(/<script>([\s\S]*?)<\/script>/g))new vm.Script(match[1]);
const generations=html.slice(html.indexOf('function comparisonSnapshot('),html.indexOf('async function compare(){'));
const preview=html.slice(html.indexOf('async function previewBoth(){'),html.indexOf('async function refreshRunStates('));
const exp=html.slice(html.indexOf('function interruptedComparison('),html.indexOf("$('chartContextLabel').oninput"));
function setup(change=false){
 const elements={},calls=[];let downloads=0,created=0;
 const s={sha:'workbook',sourceGeneration:1,comparisonGeneration:0,contextRecord:{revision:2},selection:new Set(['case']),dirty:false,contextDirty:false,boot:{token:'own'},comparison:{runs:[{result_hash:'stable'}]},chartURLs:{},chartsReady:false,chartError:false,exported:false,
 $:id=>elements[id]??={value:id==='comparator'?'case':'ext_pv_gdp',textContent:'',classList:{add(){},remove(){}},decode:async()=>{}},
 sourceCurrent:t=>t.sha===s.sha&&t.generation===s.sourceGeneration,comparisonRequest:()=>({scenario_ids:['case'],comparator_id:'case'}),resultSignature:v=>JSON.stringify(v.runs),clearCharts:()=>{s.chartsReady=false},clearComparison:()=>{s.comparison=null},updateWorkflow:()=>{},status:t=>{s.lastStatus=t},contextConflict:async()=>false,
 URL:{createObjectURL:()=> 'blob:result-'+(++created),revokeObjectURL:()=>{}},document:{createElement:()=>({click:()=>downloads++})},
 setTimeout:(f,ms)=>{const t=setTimeout(f,ms);t.unref();return t},clearTimeout,AbortController,Response,Blob,crypto:{randomUUID:()=> 'request-key'},
 request:async(route,data)=>{calls.push(route);if(route==='/api/compare')return s.comparison;if(route==='/api/export'){if(change){s.comparisonGeneration++;s.lastStatus='A newer comparison owns this page';}return {blob:async()=>({})};}throw Error(route)} };
 vm.createContext(s);vm.runInContext(generations+'\n'+exp+'\n'+preview,s);return {s,calls,downloads:()=>downloads};
}
(async()=>{
 const t=setup();await t.s.previewBoth();assert.equal(t.s.comparisonGeneration,1);assert.equal(t.s.chartsReady,true);assert.match(t.s.$('chart').src,/^blob:/);assert.match(t.s.$('chartBriefing').src,/^blob:/);assert.equal(t.calls.filter(p=>p==='/api/export').length,2);
 await t.s.exportFile('zip');assert.equal(t.s.comparisonGeneration,2);assert.equal(t.downloads(),1);assert.equal(t.s.exported,true);assert.match(t.s.lastStatus,/Download prepared/);
 const stale=setup(true);await stale.s.previewBoth();assert.equal(stale.s.chartsReady,false);assert.equal(stale.s.$('chart').src,undefined);assert.equal(stale.s.lastStatus,'A newer comparison owns this page');assert.equal(stale.downloads(),0);
 const staleZip=setup(true);await staleZip.s.exportFile('zip');assert.equal(staleZip.downloads(),0);assert.equal(staleZip.s.exported,false);assert.equal(staleZip.s.lastStatus,'A newer comparison owns this page');
 console.log('PASS real desktop callers + generation guards: both image src assignments, download click, and stale-result rejection without overwriting newer status. Not browser acceptance.');
})().catch(e=>{console.error(e);process.exitCode=1});
