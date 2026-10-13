// Hosted-only export waiting. Submit once; automatically retry only safe GETs.
const directHostedRequest=request;
let queuedExportTask=null;
function exportWaitText(text){$('exportWaitStatus').textContent=text;status(text);}
function exportRetryDelay(response){const n=Number(response.headers.get('Retry-After'));return Math.min(10000,Math.max(1000,Number.isFinite(n)&&n>0?n*1000:2000));}
async function cancelExportTask(task){
 if(task.cancelSent||!task.jobId)return;
 task.cancelSent=true;
 const controller=new AbortController(),timer=setTimeout(()=>controller.abort(),5000);
 try{const response=await fetch('/api/export-cancel',{method:'POST',headers:{'X-DSF-Token':boot?.token||'','Content-Type':'application/json'},body:JSON.stringify({job_id:task.jobId}),signal:controller.signal});task.cancelConfirmed=response.ok;}catch{task.cancelConfirmed=false;}finally{clearTimeout(timer);}
}
$('cancelQueuedExport').onclick=()=>{if(queuedExportTask){queuedExportTask.cancelled=true;queuedExportTask.controller.abort();exportWaitText('Cancelling the waiting export…');}};
request=async function(path,data,raw=false){
 if(path!=='/api/export'||data===undefined)return directHostedRequest(path,data,raw);
 if(queuedExportTask)throw Error('An export is already waiting in this tab. Wait or cancel it first.');
 const task={jobId:null,cancelled:false,cancelSent:false,cancelConfirmed:false,controller:new AbortController(),deadline:Date.now()+620000,target:comparisonSnapshot(data)};
 task.timer=setTimeout(()=>{task.cancelled=true;task.controller.abort();},620000);
 queuedExportTask=task;
 $('exportWaitPanel').classList.remove('hidden');$('cancelQueuedExport').disabled=false;$('deleteVisit').disabled=false;
 const pause=ms=>new Promise(resolve=>{const done=()=>{clearTimeout(timer);task.controller.signal.removeEventListener('abort',done);resolve();};const timer=setTimeout(done,ms);task.controller.signal.addEventListener('abort',done,{once:true});});
 function check(){
  if(Date.now()>task.deadline){task.cancelled=true;throw Error('The export wait reached its limit. Your saved scenarios remain available.');}
  if(task.cancelled)throw Error('Export wait cancelled.');
  if(!comparisonCurrent(task.target)){task.cancelled=true;throw Error('The comparison changed. This export was stopped; prepare the current comparison again.');}
 }
 async function read(path){
  while(true){
   check();
   const response=await fetch(path,{method:'GET',headers:{'X-DSF-Token':boot?.token||''},signal:task.controller.signal});
   if(response.status===429||response.status===503){exportWaitText('Waiting for another visitor’s chart export…');await pause(exportRetryDelay(response));continue;}
   if(!response.ok){const value=await response.json();throw Error(value.error||'Export unavailable.');}
   return response;
  }
 }
 try{
  exportWaitText('Joining the chart export queue…');
  const requestKey=crypto.randomUUID();
  try{
   const response=await fetch('/api/export-jobs',{method:'POST',headers:{'X-DSF-Token':boot?.token||'','Content-Type':'application/json'},body:JSON.stringify({...data,request_key:requestKey}),signal:task.controller.signal});
   const submitted=await response.json();if(!response.ok)throw Error(submitted.error||'The export could not be queued.');task.jobId=submitted.job_id;
  }
  catch(error){
   // A lost POST response is recovered by reading our current job, never by resubmitting.
   // Recovery must remain possible when Cancel was pressed during the ambiguous POST.
   let recovered,current;const recoveryController=new AbortController(),recoveryTimer=setTimeout(()=>recoveryController.abort(),10000);
   try{for(let attempt=0;attempt<3;attempt++){
    recovered=await fetch('/api/export-current',{method:'GET',headers:{'X-DSF-Token':boot?.token||''},signal:recoveryController.signal});
    if(![429,503].includes(recovered.status))break;
    await new Promise(resolve=>setTimeout(resolve,exportRetryDelay(recovered)));
   }
   if(!recovered.ok)throw error;
   current=await recovered.json();
   }finally{clearTimeout(recoveryTimer);}
   if(current.request_key!==requestKey||!current.job_id)throw error;
   task.jobId=current.job_id;
  }
  while(true){
   check();
   const response=await read('/api/export-status?id='+encodeURIComponent(task.jobId));
   const state=await response.json();
   if(state.status==='ready'){
    exportWaitText('Receiving your chart or briefing packet…');
    const result=await read('/api/export-result?id='+encodeURIComponent(task.jobId));
    const blob=await result.blob();check();
    return raw?new Response(blob,{status:result.status,headers:result.headers}):JSON.parse(await blob.text());
   }
   if(!['queued','running'].includes(state.status))throw Error(state.message||'Export ended. Your saved scenarios remain available.');
   exportWaitText(state.status==='queued'?'Waiting for another visitor’s chart export'+(state.position?' — position '+state.position:'')+'…':'Preparing your chart or briefing packet…');
   await pause(exportRetryDelay(response));
  }
 }catch(error){
  await cancelExportTask(task);
  if(task.cancelled&&!task.cancelConfirmed)throw Error('Waiting stopped. Server cancellation could not be confirmed; the bounded job will expire. Your saved scenarios remain available.');
  if(task.cancelled)throw Error('Export cancelled. Your saved scenarios remain available.');
  throw error;
 }finally{
  clearTimeout(task.timer);queuedExportTask=null;$('exportWaitPanel').classList.add('hidden');$('cancelQueuedExport').disabled=true;
 }
};
