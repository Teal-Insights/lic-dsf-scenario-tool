// Run: node tests/next_step_bar.js
// Neutral checks for the step 5 next-step bar (teaching cases), the results order and the scroll/focus rules.
// Real page functions in a vm sandbox with synthetic DOM objects. No browser, network or calculation;
// real scrolling, layout and screen-reader acceptance are separate.
const fs=require('node:fs'),path=require('node:path'),vm=require('node:vm'),assert=require('node:assert/strict');
const html=fs.readFileSync(path.join(__dirname,'../src/lic_dsf/web.html'),'utf8');
for(const match of html.matchAll(/<script\b[^>]*>([\s\S]*?)<\/script\b[^>]*>/gi))new vm.Script(match[1]);
const start=html.indexOf('// Built-in investment teaching cases:');assert(start>=0);
const code=html.slice(start,html.indexOf('</script>',start));
assert(code.includes('// Teaching-case next step:'),'the next-step block must follow the teaching-case block');
const lines=html.split('\n');
const SHA='3a0a0b80c7cbc95ac953f25ecae0b437129d669ceb8aeefb54ab86dc8727ea86';
const cases=['no-investment','earlier-benefit','smaller-benefit'].map(id=>({id,title:id,description:'About '+id,scenario_file:JSON.parse(fs.readFileSync(path.join(__dirname,'../src/lic_dsf/illustrative_cases',id+'.json'),'utf8'))}));
const LABEL={'no-investment':'No investment','earlier-benefit':'Larger assumed benefit','smaller-benefit':'Smaller assumed benefit'};

function setup({calculated=[],stale=[],renamed={},teaching=true,own=false}={}){
 const elements={},calls=[];
 function element(id){return elements[id]??={id,value:'',textContent:'',innerHTML:'',dataset:{},tabIndex:0,classes:new Set(['teachingNext','singleCaseHint'].includes(id)?['hidden']:[]),
  classList:{add:c=>element(id).classes.add(c),remove:c=>element(id).classes.delete(c),toggle:(c,on)=>on?element(id).classes.add(c):element(id).classes.delete(c),contains:c=>element(id).classes.has(c)},
  focus(options){calls.push(['focus',id,options])},scrollIntoView(options){calls.push(['scroll',id,options])},querySelector:q=>q==='h3'?element(id+' h3'):null,
  get firstElementChild(){return id==='chartPair'?element('firstChartPanel'):null}};}
 const scenarios=cases.filter(c=>calculated.includes(c.id)||stale.includes(c.id)).map(c=>({id:'saved-'+c.id,name:LABEL[c.id],share_label:renamed[c.id]??LABEL[c.id],revision:1}));
 if(own)scenarios.push({id:'own',name:'My case',share_label:'My case',revision:1});
 const knownRuns=new Map(scenarios.map(s=>[s.id,{revision:1,current:s.id==='own'||calculated.includes(s.id.slice(6))}]));
 const draft={keep:true},active={id:'saved',revision:3};
 const s={$:element,calls,draft,active,dirty:false,journalDirty:false,contextDirty:false,calculating:false,comparison:{runs:[{},{}]},knownRuns,
  ctx:{inspection:{workbook_sha256:SHA,input_years:Array.from({length:21},(_,i)=>2024+i)},builtin_investment_cases:teaching?structuredClone(cases):undefined,scenarios},
  esc:x=>String(x),structuredClone,act:f=>f(),canSwitch:()=>true,clearComparison(){},renderEditor(){},chooseDriver(){},goTo(id){calls.push(['goTo',id])},status(){},
  openCase:async id=>{calls.push(['openCase',id]);return true},validateScenarioFile(){throw Error('Must not load a case')},request(){throw Error('Must not request')}};
 vm.createContext(s);vm.runInContext(code,s);
 s.renderBuiltinInvestment();if(teaching)s.$('builtinInvestmentCase').value=cases[0].id; // a browser selects the first option
 return s;
}
let count=0;const pending=[];const check=(name,f)=>{const r=f();if(r&&typeof r.then==='function')pending.push(r.then(()=>{count++;},e=>{e.message=name+': '+e.message;throw e;}));else count++;};
const sentence=(ready,next)=>ready+' ready. Next: add '+next+' to compare both investment cases with No investment.';

check('no teaching cases: no bar, no change to other guidance',()=>{
 const s=setup({teaching:false,own:true});s.$('singleCaseHint').classList.remove('hidden');s.$('nextStepText').textContent='Review both charts';
 assert.equal(s.teachingProgress(),null);s.renderTeachingNext();
 assert(s.$('teachingNext').classList.contains('hidden'));assert(!s.$('singleCaseHint').classList.contains('hidden'));assert.equal(s.$('nextStepText').textContent,'Review both charts');
});
check('no teaching case calculated yet: no bar',()=>{const s=setup();s.renderTeachingNext();assert(s.$('teachingNext').classList.contains('hidden'));});
check('one teaching case: names it, offers the next one, replaces the single-case hint and the tracker text',()=>{
 const s=setup({calculated:['no-investment']});s.$('singleCaseHint').classList.remove('hidden');s.$('nextStepText').textContent='Only one case is compared';
 s.renderTeachingNext();
 assert(!s.$('teachingNext').classList.contains('hidden'));
 assert.equal(s.$('teachingNextText').textContent,sentence('No investment','Larger assumed benefit'));
 assert.equal(s.$('teachingNextGo').textContent,'Go to Larger assumed benefit →');assert.equal(s.$('teachingNextGo').dataset.case,'earlier-benefit');
 assert(s.$('singleCaseHint').classList.contains('hidden'),'one next-step message, not two');
 assert.equal(s.$('nextStepText').textContent,sentence('No investment','Larger assumed benefit'));
 assert.doesNotMatch(s.$('teachingNextText').textContent,/download|complete|of GDP/i);
});
check('two teaching cases: joined with "and"',()=>{
 const s=setup({calculated:['no-investment','earlier-benefit']});s.renderTeachingNext();
 assert.equal(s.$('teachingNextText').textContent,sentence('No investment and Larger assumed benefit','Smaller assumed benefit'));
 assert.equal(s.$('teachingNextGo').dataset.case,'smaller-benefit');
});
check('missing comparison case is offered first',()=>{
 const s=setup({calculated:['earlier-benefit','smaller-benefit']});s.renderTeachingNext();
 assert.equal(s.$('teachingNextGo').textContent,'Go to No investment →');
});
check('all three calculated: bar hidden, tracker text left alone',()=>{
 const s=setup({calculated:['no-investment','earlier-benefit','smaller-benefit']});s.$('teachingNext').classList.remove('hidden');s.$('nextStepText').textContent='Review both charts';
 s.renderTeachingNext();assert(s.$('teachingNext').classList.contains('hidden'));assert.equal(s.$('nextStepText').textContent,'Review both charts');
});
check('a saved but not calculated case: the bar says to calculate it and opens it, never offers a reload',async()=>{
 const s=setup({calculated:['no-investment'],stale:['earlier-benefit']});s.renderTeachingNext();
 assert.equal(s.$('teachingNextText').textContent,'No investment ready. Next: Larger assumed benefit is saved but not calculated. Open it, then click Calculate and show results.');
 assert.equal(s.$('teachingNextGo').textContent,'Open Larger assumed benefit →');assert.equal(s.$('teachingNextGo').dataset.open,'saved-earlier-benefit');
 await s.openTeachingNext();assert.deepEqual(s.calls.filter(c=>c[0]==='openCase'),[['openCase','saved-earlier-benefit']]);
 assert(s.calls.some(c=>c[0]==='goTo'&&c[1]==='scenario'),'opening goes to step 3, where Calculate is');
});
check('a renamed legend label is still recognised by its workspace name',()=>{
 const s=setup({calculated:['no-investment','earlier-benefit'],renamed:{'earlier-benefit':'Big payoff'}});s.renderTeachingNext();
 assert.equal(s.$('teachingNextGo').dataset.case,'smaller-benefit');
});
check('tracker text is not overridden while a draft or chart text is pending',()=>{
 for(const key of ['dirty','contextDirty']){const s=setup({calculated:['no-investment']});s[key]=true;s.$('nextStepText').textContent='Click Save scenario';s.renderTeachingNext();assert.equal(s.$('nextStepText').textContent,'Click Save scenario');}
});
check('Go button scrolls to the picker, preselects the case, focuses Load and loads nothing',()=>{
 const s=setup({calculated:['no-investment']});s.renderTeachingNext();s.calls.length=0;
 assert.equal(s.$('builtinInvestmentCase').value,'no-investment');
 s.$('teachingNextGo').onclick();
 assert.equal(s.$('builtinInvestmentCase').value,'earlier-benefit');assert.equal(s.$('builtinInvestmentDescription').textContent,'About earlier-benefit');
 assert.deepEqual(JSON.parse(JSON.stringify(s.calls)),[['scroll','loadBuiltinInvestment',{block:'center',behavior:'auto'}],['focus','loadBuiltinInvestment',{preventScroll:true}]]);
 assert.equal(s.dirty,false);assert.deepEqual(s.draft,{keep:true});assert.equal(s.active.id,'saved');
 s.calls.length=0;s.goToTeachingCase('not-a-case');assert.equal(s.calls.length,0);assert.equal(s.$('builtinInvestmentCase').value,'earlier-benefit');
});
check('after a teaching-case Calculate the picker moves on to the next uncalculated case',()=>{
 let s=setup({calculated:['no-investment']});s.preselectNextTeachingCase('saved-no-investment');assert.equal(s.$('builtinInvestmentCase').value,'earlier-benefit');
 s=setup({calculated:['no-investment','earlier-benefit']});s.preselectNextTeachingCase('saved-earlier-benefit');assert.equal(s.$('builtinInvestmentCase').value,'smaller-benefit');
 s=setup({calculated:['no-investment'],own:true});s.preselectNextTeachingCase('own');assert.equal(s.$('builtinInvestmentCase').value,'no-investment','own cases leave the picker alone');
 s=setup({calculated:['no-investment','earlier-benefit','smaller-benefit']});s.$('builtinInvestmentCase').value='earlier-benefit';s.preselectNextTeachingCase('saved-smaller-benefit');assert.equal(s.$('builtinInvestmentCase').value,'earlier-benefit');
});
check('reveal: next-step bar while teaching cases remain',()=>{
 const s=setup({calculated:['no-investment','earlier-benefit']});s.revealResults();
 assert.deepEqual(JSON.parse(JSON.stringify(s.calls)),[['focus','teachingNextText',{preventScroll:true}],['scroll','teachingNext',{block:'start',behavior:'auto'}]]);
});
check('reveal: first chart once all three are calculated, and for any non-teaching comparison',()=>{
 for(const options of [{calculated:['no-investment','earlier-benefit','smaller-benefit']},{teaching:false,own:true}]){
  const s=setup(options);s.revealResults();
  assert.deepEqual(JSON.parse(JSON.stringify(s.calls)),[['focus','firstChartPanel h3',{preventScroll:true}],['scroll','firstChartPanel',{block:'start',behavior:'auto'}]]);
  assert.equal(s.$('firstChartPanel h3').tabIndex,-1);
 }
});
check('compare() reveals results instead of jumping to the step 5 heading; indicator changes never scroll',()=>{
 const compare=lines.find(l=>l.startsWith('async function compare(){'));assert(compare.endsWith('await previewBoth();revealResults();}'));assert(!compare.includes("goTo('briefing')"));
 const metric=lines.find(l=>l.startsWith("$('chartMetric').onchange="));assert(!/goTo|revealResults|scrollIntoView|focus\(/.test(metric));
 const preview=html.slice(html.indexOf('async function previewBoth(){'),html.indexOf('async function refreshRunStates('));assert(!/goTo|revealResults|scrollIntoView|\.focus\(/.test(preview));
 const calculate=lines.find(l=>l.startsWith("$('calculate').onclick="));assert(calculate.includes("knownRuns.set(scenarioId,{revision,current:true});if(typeof preselectNextTeachingCase==='function')preselectNextTeachingCase(scenarioId);"));
 const workflow=html.slice(html.indexOf('function updateWorkflow(){'),html.indexOf('function adjustmentState('));
 const hook=workflow.indexOf("\n if(typeof renderTeachingNext==='function')renderTeachingNext();\n");assert(hook>0&&hook<workflow.indexOf('\n if(uiBusy)return;'),'bar refresh runs before the busy early return');
});
check('Download stays available but secondary while teaching cases remain',()=>{
 const line=html.slice(html.indexOf('function updateWorkflow(){')).split('\n').find(l=>l.includes("$('packet').classList.toggle('primary',"));
 for(const [progress,primary] of [[{show:true},false],[{show:false},true],[null,true],[undefined,true]]){
  const els={},el=id=>els[id]??=(()=>{const e={disabled:false,classes:new Set()};e.classList={toggle:(c,on)=>on?e.classes.add(c):e.classes.delete(c)};return e;})();
  const s={$:el,has:true,active:{id:'a'},dirty:false,contextDirty:false,calculating:false,currentRun:true,ready:true,selection:new Set(['a']),comparison:{runs:[{},{}]}};
  if(progress!==undefined)s.teachingProgress=()=>progress;
  vm.createContext(s);vm.runInContext(line,s);
  assert.equal(s.$('packet').classes.has('primary'),primary,JSON.stringify(progress));assert.equal(s.$('packet').disabled,false);
 }
});
check('status banner names the next case instead of inviting a download',()=>{
 const line=lines.find(l=>l.includes("'Both chart views are ready. Review them, then download the briefing packet below the charts.'"));
 const a=line.indexOf('status(typeof teachingProgress'),b=line.indexOf("below the charts.');",a)+"below the charts.');".length;assert(a>=0&&b>a);
 const expr=line.slice(a,b);
 const run=(progress,runs)=>{const s={comparison:{runs:Array(runs).fill({})},status(t){s.text=t}};if(progress)s.teachingProgress=()=>progress;vm.createContext(s);if(progress)vm.runInContext(lines.filter(l=>l.startsWith('function teachingNextStep(')).join('\n'),s);vm.runInContext(expr,s);return s.text;};
 const two={show:true,missing:[{label:'Smaller assumed benefit'}]};
 assert.equal(run(two,2),'Both chart views are ready. Next: add Smaller assumed benefit to compare both investment cases with No investment.');
 assert.equal(run({show:false},2),'Both chart views are ready. Review them, then download the briefing packet below the charts.');
 assert.match(run(null,1),/Only one case is compared, so every difference is zero: calculate a second case before downloading\./);
});
check('step 5 order: bar, summaries, policy chart, standard chart, download, collapsed wording form',()=>{
 const a=html.indexOf('<section id="briefing"'),section=html.slice(a,html.indexOf('</section>',a));
 const order=['id="teachingNext"','id="takeaways"','<h3>Policy briefing charts</h3>','<h3>Standard LIC-DSF charts</h3>','id="packet"','id="labelPanel"'].map(x=>{const i=section.indexOf(x);assert(i>=0,x);return i;});
 assert.deepEqual(order,[...order].sort((x,y)=>x-y));
 assert(section.indexOf('<div id="chartPair" class="chart-pair expanded"><article class="chart-panel"><h3>Policy briefing charts</h3>')>=0,'policy chart is the first chart in reading order');
 assert(section.includes('<details class="label-panel" id="labelPanel"><summary>Edit chart heading and legend labels (optional)</summary>'),'wording form is collapsed by default');
 assert(section.includes('>Download the briefing packet (.zip)</button>'));
 const packet=section.slice(section.indexOf('<div class="export-packet">'),section.indexOf('<details id="moreDownloads"'));assert.doesNotMatch(packet,/complete/i);
 assert(section.indexOf('id="teachingNext"')<section.indexOf('id="chartsStatus"'),'the bar is the first thing in step 5');
 assert.doesNotMatch(section,/id="teachingNext"[^>]*\sopen\b/);assert.doesNotMatch(section,/id="labelPanel" open/);
});
Promise.all(pending).then(()=>{console.log(count+' next-step bar checks passed; real page functions, synthetic DOM. Browser scrolling and layout acceptance are separate.');}).catch(e=>{console.error(e);process.exitCode=1;});
