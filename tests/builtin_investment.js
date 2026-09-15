const fs=require('node:fs'),vm=require('node:vm'),assert=require('node:assert/strict'),path=require('node:path');
const html=fs.readFileSync(path.join(__dirname,'../src/lic_dsf/web.html'),'utf8');
const validation=html.slice(html.indexOf('function validateScenarioFile('),html.indexOf('function scenarioFileFromSaved('));
const start=html.indexOf('// Built-in investment teaching cases:');assert(start>=0);
const code=html.slice(start,html.indexOf('</script>',start));
const inspection={workbook_sha256:'3a0a0b80c7cbc95ac953f25ecae0b437129d669ceb8aeefb54ab86dc8727ea86',input_years:Array.from({length:21},(_,i)=>2024+i)};
const cases=['no-investment','earlier-benefit','smaller-benefit'].map(id=>({id,title:id,description:'Illustrative',scenario_file:JSON.parse(fs.readFileSync(path.join(__dirname,'../src/lic_dsf/illustrative_cases',id+'.json'),'utf8'))}));
function setup(){
 const elements={};const $=id=>elements[id]??={value:'',textContent:'',innerHTML:'',classList:{toggle:(name,value)=>{s.hidden=value}}};
 const zero=structuredClone(cases[0].scenario_file.definition);zero.terms=null;
 const s={structuredClone,JSON,Array,Object,Number,Error,$,ctx:{inspection:structuredClone(inspection),zero,scenarios:[{id:'saved',name:'Existing'}],builtin_investment_cases:structuredClone(cases)},active:{id:'saved',revision:3},dirty:false,journalDirty:false,contextDirty:false,calculating:false,currentRun:true,draft:{keep:true},sharedNotes:{},editorReference:{},comparison:{old:true},esc:x=>String(x),act:f=>f(),canSwitch:()=>!s.dirty&&!s.journalDirty&&!s.contextDirty,clearComparison:()=>{s.comparison=null},renderEditor:()=>{},chooseDriver:()=>{},goTo:()=>{},status:()=>{},request:()=>{throw Error('Must not save, import or calculate automatically')}};
 vm.createContext(s);vm.runInContext(validation+code,s);s.$('builtinInvestmentCase').value='earlier-benefit';return s;
}
let count=0;
function check(name,f){f();count++;}
check('actual button loads all prepared inputs without a file object or request',()=>{
 const s=setup(),original=structuredClone(s.ctx.builtin_investment_cases),saved=structuredClone(s.ctx.scenarios);
 Object.defineProperty(s.$('scenarioFile'),'files',{get(){throw Error('File input must not be accessed')}});
 s.$('loadBuiltinInvestment').onclick();
 assert.deepEqual(s.draft,cases[1].scenario_file.definition);assert.deepEqual(s.sharedNotes,cases[1].scenario_file.shared_rationale);
 assert.equal(s.active,null);assert.equal(s.currentRun,false);assert(s.dirty);assert.equal(s.comparison,null);
 assert.equal(s.$('shareLabel').value,'Larger assumed benefit');assert.match(s.$('calcState').textContent,/save and calculate/);
 assert.deepEqual(s.ctx.scenarios,saved);s.draft.delta_paths['20'][6]=99;s.sharedNotes['20']='Edited';assert.deepEqual(s.ctx.builtin_investment_cases,original);
});
for(const key of ['dirty','journalDirty','contextDirty','calculating'])check('preserve '+key,()=>{
 const s=setup();s[key]=true;s.$('loadBuiltinInvestment').onclick();assert.equal(s.active.id,'saved');assert.deepEqual(s.draft,{keep:true});assert.equal(s.currentRun,true);
});
for(const mutate of [s=>s.ctx.inspection.workbook_sha256='a'.repeat(64),s=>s.ctx.inspection.input_years.reverse(),s=>s.ctx.inspection.input_years.pop(),s=>s.ctx.builtin_investment_cases=null])check('wrong context has no available choices',()=>{
 const s=setup();mutate(s);assert.equal(s.builtinInvestmentChoices(s.ctx).length,0);assert.throws(()=>s.loadBuiltinInvestment(),/official illustrative/);assert.equal(s.active.id,'saved');s.renderBuiltinInvestment();assert.equal(s.hidden,true);
});
check('tampered package cannot replace draft',()=>{const s=setup();s.ctx.builtin_investment_cases[1].scenario_file.workbook_sha256='b'.repeat(64);assert.throws(()=>s.loadBuiltinInvestment(),/different workbook/);assert.equal(s.active.id,'saved');});
check('selector determines each distinct original case',()=>{for(const item of cases){const s=setup();s.$('builtinInvestmentCase').value=item.id;s.loadBuiltinInvestment();assert.deepEqual(s.draft,item.scenario_file.definition);assert.equal(s.$('name').value,item.scenario_file.share_label)}});
check('source wiring and illustrative disclosures remain present',()=>{
 assert.match(html,/ctx=loaded;renderBuiltinInvestment\(\)/);assert.match(html,/ctx=null;renderBuiltinInvestment\(\)/);
 assert.match(html,/A teaching example, not real investment modeling/);assert.match(html,/No scenario file is needed/);
 assert.match(html,/First use downloads the official example from the World Bank/);
});
check('entry guidance offers the illustrative example without an upload',()=>{
 const s=setup();s.boot={workbooks:[]};vm.runInContext(html.split('\n').find(line=>line.startsWith('function renderWorkspaceHint()')),s);s.renderWorkspaceHint();assert.match(s.$('workspaceHint').textContent,/Try the official illustrative example or upload/);
 assert.match(html,/id="editorEmpty"[^>]*>Choose the official illustrative example or upload/);
});
check('transient draft notice is cleared on editor transitions and settled state',()=>{
 assert.match(html,/function renderEditor\(\)\{\$\('builtinInvestmentStatus'\)\.textContent='';/);
 const s=setup();s.dirty=false;s.$('builtinInvestmentStatus').textContent='Loaded as a new unsaved draft';
 const resetLine=html.slice(html.indexOf('function updateWorkflow(){')).split('\n')[1];vm.runInContext(resetLine,s);assert.equal(s.$('builtinInvestmentStatus').textContent,'');
});
console.log(count+' built-in investment UI checks passed; actual button handlers, no file import or implicit calculation. Browser acceptance is separate.');
