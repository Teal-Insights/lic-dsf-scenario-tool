// Execute the generated hosted preview/export handlers with neutral UI objects.
// This is not browser or network acceptance.
const fs=require('node:fs'),path=require('node:path'),vm=require('node:vm'),assert=require('node:assert/strict'),cp=require('node:child_process');
const root=path.join(__dirname,'..');
const generated=cp.spawnSync(process.env.DSF_PYTHON||'python',['-B','-c','from lic_dsf.hosted import hosted_page; import sys; sys.stdout.buffer.write(hosted_page())'],{cwd:root,env:{...process.env,PYTHONPATH:path.join(root,'src')},encoding:'utf8'});
assert.equal(generated.status,0,generated.stderr);const html=generated.stdout;
for(const match of html.matchAll(/<script\b[^>]*>([\s\S]*?)<\/script\b[^>]*>/gi))new vm.Script(match[1]);
const preview=html.slice(html.indexOf('async function previewBoth(){'),html.indexOf('async function refreshRunStates('));
const exp=html.slice(html.indexOf('// Retain one prepared packet'),html.indexOf("$('chartContextLabel').oninput"));
function setup(failPreview=false){
 const elements={},sequence=[];let active=0,maxActive=0,downloads=0;
 const s={comparison:{runs:[{result_hash:'fixed'}]},chartURLs:{},chartsReady:false,chartError:false,exported:false,
  $:id=>elements[id]??={value:'ext_pv_gdp',textContent:'',classList:{add(){},remove(){}},focus(){},decode:async()=>{}},
  comparisonRequest:()=>({scenario_ids:['case']}),comparisonTarget:()=>({}),comparisonCurrent:()=>true,
  resultSignature:v=>JSON.stringify(v.runs),clearCharts:()=>{s.chartsReady=false},updateWorkflow:()=>{},status:()=>{},
  clearComparison:()=>{s.comparison=null},contextConflict:async()=>false,
  URL:{createObjectURL:()=> 'blob:synthetic',revokeObjectURL:()=>{}},
  document:{createElement:()=>({click:()=>downloads++})},setTimeout:()=>{},
  request:async(route,data)=>{
   if(route==='/api/compare')return s.comparison;
   active++;maxActive=Math.max(maxActive,active);sequence.push(data.format+':'+(data.view||''));
   await new Promise(resolve=>setImmediate(resolve));active--;
   if(failPreview&&data.format==='svg')throw Error('Chart and individual-download limit reached. Use Download briefing packet for the reserved final slot.');
   return {blob:async()=>({})};
  }};
 vm.createContext(s);vm.runInContext(preview+'\n'+exp,s);
 return {s,sequence,maxActive:()=>maxActive,downloads:()=>downloads};
}
(async()=>{
 let t=setup();await t.s.previewBoth();assert.equal(t.maxActive(),1);assert.deepEqual(t.sequence,['svg:standard','svg:briefing']);assert.equal(t.s.chartsReady,true);
 t=setup(true);const original=t.s.comparison;await assert.rejects(t.s.previewBoth(),/reserved final slot/);assert.equal(t.s.comparison,original);assert.equal(t.s.chartsReady,false);
 assert.match(t.s.$('chartsStatus').textContent,/download the briefing packet instead/);
 await t.s.exportFile('zip');assert.equal(t.downloads(),1);assert.equal(t.s.exported,true);
 console.log('PASS hosted generated-script syntax, sequential preview pair, quota failure preserves comparison, and final ZIP handler remains usable. No browser acceptance.');
})().catch(e=>{console.error(e);process.exitCode=1});
