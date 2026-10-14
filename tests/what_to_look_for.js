// Run: node tests/what_to_look_for.js
// S10: the actual describeBuiltinInvestment shows one "What to look for" line for the selected teaching case.
const fs=require('node:fs'),vm=require('node:vm'),assert=require('node:assert/strict'),path=require('node:path');
const html=fs.readFileSync(path.join(__dirname,'../src/lic_dsf/web.html'),'utf8');
const start=html.indexOf('// Built-in investment teaching cases:');assert(start>=0);
const code=html.slice(start,html.indexOf('</script>',start));
const ids=['no-investment','earlier-benefit','smaller-benefit'];
const elements={},$=id=>elements[id]??={value:'',textContent:'',innerHTML:'',classList:{toggle(){}}};
const s={$,Object,JSON,Array,esc:x=>String(x).replace(/[&<>"']/g,c=>'&#'+c.charCodeAt(0)+';'),act:f=>f(),
 ctx:{inspection:{workbook_sha256:'3a0a0b80c7cbc95ac953f25ecae0b437129d669ceb8aeefb54ab86dc8727ea86',input_years:Array.from({length:21},(_,i)=>2024+i)},builtin_investment_cases:ids.map(id=>({id,title:id,description:'Description of '+id}))}};
vm.createContext(s);vm.runInContext(code,s);
const seen=new Set();
for(const id of ids){
 s.$('builtinInvestmentCase').value=id;s.describeBuiltinInvestment();
 assert.equal(s.$('builtinInvestmentDescription').textContent,'Description of '+id,'description unchanged');
 const line=s.$('builtinInvestmentLook').innerHTML;
 assert.match(line,/^<strong>What to look for:<\/strong> [A-Z]/,id);
 assert.doesNotMatch(line,/lower|higher|better|worse|reduc|improv/i,'no outcome claims: '+id);
 seen.add(line);
}
assert.equal(seen.size,3,'each case has its own line');
assert.match(elements.builtinInvestmentLook.innerHTML,/No investment/);
s.$('builtinInvestmentCase').value='unknown';s.describeBuiltinInvestment();assert.equal(s.$('builtinInvestmentLook').innerHTML,'');
s.ctx=null;s.describeBuiltinInvestment();assert.equal(s.$('builtinInvestmentLook').innerHTML,'');
assert.match(html,/<p id="builtinInvestmentDescription" aria-live="polite"><\/p><p id="builtinInvestmentLook"><\/p>/);
assert.match(html,/aria-describedby="builtinInvestmentDescription builtinInvestmentLook"/);
console.log('what_to_look_for ok: one line per teaching case, cleared when no case applies');
