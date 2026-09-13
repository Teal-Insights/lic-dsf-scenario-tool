const fs=require('fs'),vm=require('vm'),assert=require('node:assert/strict');
const html=fs.readFileSync(require('node:path').join(__dirname,'../src/lic_dsf/web.html'),'utf8');
const elements={};const s={Number,Object,Math,Set,boot:{workbooks:[]},metricTitles:{m:'Debt ratio'},metricUnitPhrase:{m:'of GDP'},$:id=>elements[id]??={textContent:''}};vm.createContext(s);
for(const name of ['displayMagnitude','differenceText','takeaways','fixed','renderWorkspaceHint']){const line=html.split('\n').find(x=>x.startsWith('function '+name+'('));assert(line,name);vm.runInContext(line,s);}
const compare=d=>({comparator_id:'control',runs:[{scenario_id:'control',share_label:'Control',result:{evidence:{calculation:'computed_unverified'},points:[{metric:'m',year:2044,scenario:0}]}},{scenario_id:'case',share_label:'Case',result:{evidence:{calculation:'computed_unverified'},points:[{metric:'m',year:2044,scenario:d}]}}]});
for(const [d,text] of [[-.254683,'−0.25 pp'],[.125,'+0.13 pp'],[0,'0.00 pp'],[.0049,'≈0.00 pp'],[-.0049,'≈0.00 pp'],[.005,'+0.01 pp'],[-.005,'−0.01 pp']])assert(s.takeaways(compare(d))[0].includes(text),String(d));
assert.equal(s.fixed(.125),'0.13');assert.equal(s.fixed(-.125),'−0.13');assert.equal(s.fixed(-.0001),'0.00');
s.renderWorkspaceHint();assert(s.$('workspaceHint').textContent.startsWith('No saved workbooks'));
s.boot.workbooks=[{}];s.renderWorkspaceHint();assert(s.$('workspaceHint').textContent.startsWith('1 saved workbook in'));assert(s.$('workspaceHint').textContent.includes('do not need to upload it again'));
s.boot.workbooks=[{},{}];s.renderWorkspaceHint();assert(s.$('workspaceHint').textContent.startsWith('2 saved workbooks'));
assert(html.includes('Choose or reopen a workbook in step 1 to see its saved scenarios.'));
assert(html.includes('No saved scenarios for this workbook yet.'));
assert(html.includes('A gap from the reference baseline is not itself a policy effect.'));
const reviewed=compare(.2);reviewed.runs[1].result.evidence.calculation='review_required';assert(s.takeaways(reviewed)[0].includes('needs numerical review'));
assert.equal(s.fixed(1e26),'1.00e+26');assert.equal(s.fixed(-1e26),'−1.00e+26');assert.equal(s.fixed(Number.MAX_VALUE),'1.80e+308');
console.log('Comparison precision, zero, evidence and recovery-message checks passed.');

for(const name of ['compactAdjustment','pathSegments'])vm.runInContext(html.split('\n').find(x=>x.startsWith('function '+name+'(')),s);
s.adjustmentState=v=>({kind:v===''?'empty':'value'});s.sameInput=(a,b)=>a===b;s.ctx={inspection:{input_years:[2024,2025,2026,2027,2028]}};
assert.equal(s.compactAdjustment(0),'0');assert(s.compactAdjustment(-.00001).includes('Negative'));assert(s.compactAdjustment(.00001).includes('below 0.001'));
const precise=[.000000000001,.100002,.200003,.300004,.400005],snapshot=JSON.stringify(precise);
assert(s.pathSegments(precise).includes('2 more periods'));assert.equal(JSON.stringify(precise),snapshot);

const changing=compare(-.2);changing.runs.forEach((r,i)=>r.result.points.unshift({metric:'m',year:2030,scenario:i?1:0}));changing.runs.push({scenario_id:'third',share_label:'Another case',result:{evidence:{calculation:'computed_unverified'},points:[{metric:'m',year:2030,scenario:null},{metric:'m',year:2044,scenario:2}]}});
const facts=Array.from(s.takeaways(changing));assert.equal(facts.length,2);assert(facts[0].includes('Another case'));assert(facts[0].includes('Coverage: 1 of 2'));assert(facts[1].includes('Both higher and lower'));assert(facts[1].includes('−0.20 to +1.00'));changing.runs.reverse();assert.deepEqual(Array.from(s.takeaways(changing)),facts);
