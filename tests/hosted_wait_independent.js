const fs=require('node:fs'),vm=require('node:vm'),assert=require('node:assert/strict');
const source=fs.readFileSync(require('node:path').join(__dirname,'../src/lic_dsf/hosted_wait.js'),'utf8');
function setup(mode){
 const calls=[],elements={},state={now:0,current:true,statuses:0,paused:false};
 const $=id=>elements[id]??={textContent:'',disabled:false,classList:{add(){},remove(){}}};
 const response=(value,status=200)=>({ok:status>=200&&status<300,status,headers:{get:()=> '2'},json:async()=>value,blob:async()=>Buffer.from('result')});
 const s={$ ,AbortController,Response,JSON,Number,Math,Error,Date:{now:()=>state.now},crypto:{randomUUID:()=> 'request-key'},boot:{token:'own-token'},comparisonSnapshot:()=>({generation:1}),comparisonCurrent:()=>state.current,status:()=>{},encodeURIComponent,
  setTimeout:(f,ms)=>{if(ms===620000)state.timeout=f;if(ms>=5000){const t=setTimeout(f,ms);t.unref();return t;}return setTimeout(()=>{state.now+=ms;if(mode==='cancel-wait'&&!state.paused){state.paused=true;$('cancelQueuedExport').onclick();}f();},0);},clearTimeout,
  request:async(path,data,raw)=>{calls.push({method:'POST',path,data});return {passthrough:true};},
  fetch:async(path,options)=>{
   calls.push({method:options.method,path,data:options.body?JSON.parse(options.body):undefined});
   if(path==='/api/export-jobs'){
    if(mode==='source-change')state.current=false;
    if(mode==='cancel-lost'||mode==='cancel-unconfirmed'){$('cancelQueuedExport').onclick();throw Error('Lost submit response');}
    if(mode==='lost'||mode==='wrong-current')throw Error('Lost submit response');
    return response({job_id:'own-job'});
   }
   if(path==='/api/export-cancel')return response({cancelled:true});
   if(path==='/api/export-current')return mode==='cancel-unconfirmed'?response({},503):response({job_id:'own-job',request_key:mode==='wrong-current'?'other-key':'request-key'});
   if(path.startsWith('/api/export-status')){
    state.statuses++;
    if(mode==='throttle'&&state.statuses===1)return response({},429);
    if(mode==='throttle'&&state.statuses===2)return response({},503);
    if(mode==='expired')return response({status:'expired',message:'Export ended'});
    if(mode==='cancel-wait')return response({status:'queued',position:2});
    return response({status:state.statuses<3?'queued':'ready',position:2});
   }
   if(path.startsWith('/api/export-result')){if(mode==='stalled-body'){const r=response({result:true});r.blob=()=>new Promise((resolve,reject)=>{options.signal.addEventListener('abort',()=>reject(Error('stalled body aborted')),{once:true});setImmediate(()=>{state.now+=620000;state.timeout();});});return r;}return response({result:true});}
   throw Error('Unexpected '+path);
  }};
 vm.createContext(s);vm.runInContext(source,s);return {s,calls,state,$};
}
(async()=>{
 let checks=0;
 for(const mode of ['normal','throttle','lost']){
  const t=setup(mode),r=await t.s.request('/api/export',{format:'zip'},true);
  assert((await r.blob()).size>0 || Buffer.isBuffer(await r.blob()));assert.equal(t.calls.filter(x=>x.path==='/api/export-jobs').length,1);
  assert.equal(t.calls.filter(x=>x.path==='/api/export-cancel').length,0);
  assert(t.calls.filter(x=>x.path.startsWith('/api/export-status')).every(x=>x.method==='GET'));checks++;
 }
 for(const mode of ['cancel-lost','cancel-wait','source-change','expired','stalled-body']){
  const t=setup(mode);await assert.rejects(t.s.request('/api/export',{format:'zip'},true));
  assert.equal(t.calls.filter(x=>x.path==='/api/export-jobs').length,1);
  assert.equal(t.calls.filter(x=>x.path==='/api/export-cancel').length,1);
  assert.equal(t.calls.filter(x=>x.path.startsWith('/api/export-result')).length,mode==='stalled-body'?1:0);checks++;
 }
 {
  const t=setup('cancel-unconfirmed');await assert.rejects(t.s.request('/api/export',{format:'zip'},true),/could not be confirmed/);
  assert.equal(t.calls.filter(x=>x.path==='/api/export-jobs').length,1);assert.equal(t.calls.filter(x=>x.path==='/api/export-current').length,3);
  assert.equal(t.calls.filter(x=>x.path==='/api/export-cancel').length,0);checks++;
 }
 {
  const t=setup('wrong-current');await assert.rejects(t.s.request('/api/export',{format:'zip'},true),/Lost submit/);
  assert.equal(t.calls.filter(x=>x.path==='/api/export-cancel').length,0);checks++;
 }
 {
  const t=setup('normal');assert.equal((await t.s.request('/api/save',{})).passthrough,true);checks++;
 }
 console.log(checks+' independent actual hosted_wait.js control checks passed; stubbed DOM/transport/timers, not browser acceptance.');
})().catch(e=>{console.error(e);process.exitCode=1});
