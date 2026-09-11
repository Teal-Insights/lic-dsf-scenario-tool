// Pure function checks: no browser, network, workbook or calculation required.
const fs=require('fs'),path=require('path'),vm=require('vm'),assert=require('assert/strict');
const html=fs.readFileSync(path.join(__dirname,'../src/lic_dsf/web.html'),'utf8');
new vm.Script(html.split('<script>')[1].split('</script>')[0]);
const source=html.slice(html.indexOf('const ILLUSTRATIVE_PRESETS='),html.indexOf('function describePreset'));
const context=vm.createContext({});vm.runInContext(source+';globalThis.make=illustrativeDraft;',context);
const rows=[11,13,15,17,20,22,24,28,30,32,34,36,38];
const fixture=(start,rate)=>({input_years:Array.from({length:21},(_,i)=>start+i),input_specs:rows.map(row=>({row})),customization:{terms:{rate:{value:rate},grace_years:{value:4},maturity_years:{value:9}}}});
const make=(key,input)=>JSON.parse(JSON.stringify(context.make(key,input)));
for(const [year,rate] of [[2024,.07982399291786421],[2037,.025]]){
 const input=fixture(year,rate),before=JSON.stringify(input);
 const keys=['growth_center','growth_lower','growth_higher','funding_center','funding_lower','funding_higher','investment_cost','investment_benefit'];
 const cases=Object.fromEntries(keys.map(key=>[key,make(key,input)]));
 for(const [key,c] of Object.entries(cases)){
  assert.equal(c.shareLabel.length<=40,true);
  assert.equal(Object.keys(c.definition.delta_paths).length,13);
  assert(c.years.every((y,i)=>y===year+i));
  for(const [row,values] of Object.entries(c.definition.delta_paths)){
   assert.equal(values.length,21);
   values.forEach((v,i)=>{
    let expected=0;
    if(key.startsWith('growth_')&&row==='20'&&i<3)expected=key==='growth_lower'?-1:key==='growth_higher'?1:0;
    if(key.startsWith('investment_')&&row==='13'&&i<3)expected=1;
    if(key==='investment_benefit'&&row==='20'&&i>=3&&i<8)expected=.25;
    assert.equal(v,expected,`${key} row${row} year${year+i}`);
   });
  }
 }
 const terms=key=>cases[key].definition.terms;
 assert.equal(terms('funding_center').rate,rate);
 assert.equal(terms('funding_lower').rate,rate-.01);
 assert.equal(terms('funding_higher').rate,rate+.01);
 for(const key of keys.filter(k=>k.startsWith('funding'))){assert.equal(terms(key).grace_years,4);assert.equal(terms(key).maturity_years,9);}
 for(const key of keys.filter(k=>!k.startsWith('funding')))assert.equal(terms(key),null);
 assert.equal(JSON.stringify(input),before,'Source inspection is immutable');
 cases.growth_lower.definition.delta_paths['20'][0]=999;
 assert.equal(cases.growth_higher.definition.delta_paths['20'][0],1,'Case arrays are independent');
 assert.match(cases.funding_center.description,/little or no effect/);
 assert.match(cases.investment_benefit.description,/not an estimated return/);
}
assert.throws(()=>make('funding_lower',fixture(2024,.005)),/negative rate/);
assert.equal(make('funding_lower',fixture(2024,.01)).definition.terms.rate,0);
for(const bad of [NaN,Infinity,'0.04',null])assert.throws(()=>make('funding_center',fixture(2024,bad)),/finite supplied terms/);
for(const bad of ['__proto__','toString','growth'])assert.throws(()=>make(bad,fixture(2024,.04)),/Select/);
const malformed=fixture(2024,.04);malformed.input_years[5]=2028;assert.throws(()=>make('growth_center',malformed),/21-year/);
const fractional=fixture(2024,.04);fractional.customization.terms.grace_years.value=2.5;assert.throws(()=>make('funding_center',fractional),/whole-year/);
console.log('PASS: 8 cases across 2 independent calendars/rates; 4,368 exact macro inputs, matched terms, invalid-input rejection, source preservation and script syntax.');
