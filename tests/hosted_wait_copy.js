// Run: node tests/hosted_wait_copy.js
// S7: the wait panel names the work (charts, briefing packet, download), shows the queue position,
// and never says "export". Stubbed DOM/transport/timers; not browser acceptance.
const fs=require('node:fs'),path=require('node:path'),vm=require('node:vm'),assert=require('node:assert/strict');
const root=process.env.ROOT||path.join(__dirname,'..');
const source=fs.readFileSync(path.join(root,'src/lic_dsf/hosted_wait.js'),'utf8');
function setup(mode){
 const texts=[],elements={},state={now:0,statuses:0};
 const $=id=>elements[id]??={textContent:'',disabled:false,classList:{add(){},remove(){}}};
 const response=(value,status=200)=>({ok:status>=200&&status<300,status,headers:{get:()=> '2'},json:async()=>value,blob:async()=>Buffer.from('result')});
 const s={$,AbortController,Response,JSON,Number,Math,Error,Date:{now:()=>state.now},crypto:{randomUUID:()=> 'request-key'},boot:{token:'own-token'},
  comparisonSnapshot:()=>({}),comparisonCurrent:()=>true,status:t=>texts.push(t),encodeURIComponent,clearTimeout,
  setTimeout:(f,ms)=>{if(ms>=5000){const t=setTimeout(f,ms);t.unref();return t;}return setTimeout(()=>{state.now+=ms;if(mode==='cancel'&&state.statuses===1&&!state.clicked){state.clicked=true;$('cancelQueuedExport').onclick();}f();},0);},
  request:async()=>({passthrough:true}),
  fetch:async(route)=>{
   if(route==='/api/export-jobs')return response({job_id:'own-job'});
   if(route==='/api/export-cancel')return response({cancelled:true});
   if(route.startsWith('/api/export-status')){state.statuses++;if(mode==='busy'&&state.statuses===1)return response({},429);return response(mode==='cancel'||state.statuses<3?{status:'queued',position:2}:{status:'ready'});}
   if(route.startsWith('/api/export-result'))return response({});
   throw Error('Unexpected '+route);
  }};
 vm.createContext(s);vm.runInContext(source,s);return {s,texts,$};
}
(async()=>{
 const zip=setup('normal');await zip.s.request('/api/export',{format:'zip'},true);
 assert.equal(zip.texts[0],'Preparing your briefing packet…');assert(zip.texts.includes('Queued: position 2'));
 const charts=setup('normal');await charts.s.request('/api/export',{format:'svg',view:'standard'},true,'charts');
 assert.equal(charts.texts[0],'Drawing the charts…');assert.equal(charts.texts.at(-1),'Drawing the charts…');
 const single=setup('normal');await single.s.request('/api/export',{format:'svg',view:'standard'},true);
 assert.equal(single.texts[0],'Preparing your download…');
 const busy=setup('busy');await busy.s.request('/api/export',{format:'zip'},true);
 assert(busy.texts.includes('The service is busy. Trying again…'));
 const cancel=setup('cancel');await assert.rejects(cancel.s.request('/api/export',{format:'zip'},true),{message:'Cancelled. Your saved and calculated cases are kept.'});
 assert(cancel.texts.includes('Cancelling…'));
 for(const t of [...zip.texts,...charts.texts,...single.texts,...busy.texts,...cancel.texts])assert(!/export/i.test(t),'wait text says export: '+t);
 console.log('hosted_wait_copy ok');
})().catch(e=>{console.error(e);process.exitCode=1});
