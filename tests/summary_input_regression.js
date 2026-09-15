// Exact candidate summary functions with inert DOM substitutes; no browser claim.
const fs=require('fs'),vm=require('vm'),assert=require('assert/strict'),path=require('path');
const source=fs.readFileSync(path.join(__dirname,'../src/lic_dsf/web.html'),'utf8');
const functions=source.slice(source.indexOf('function adjustmentState('),source.indexOf('const INPUT_HELP='));
function render(values,reference=values){
 const els={};const $=id=>els[id]??={checked:false,innerHTML:'',textContent:'',classList:{toggle(){}},querySelector:()=>null,querySelectorAll:()=>[]};
 const s={$ ,ctx:{inspection:{input_specs:[{row:20,name:'Real GDP growth',units:'percentage points'}],input_years:[2024,2025],customization:{terms:{rate:{value:.08},grace_years:{value:4},maturity_years:{value:9}}}}},draft:{delta_paths:{20:values}},editorReference:{delta_paths:{20:reference}},active:{},esc:String,number:String};
 vm.createContext(s);vm.runInContext(functions,s);s.refreshInputDecorations();return $('changeSummary').innerHTML;
}
const tiny=render([.0001,-.0002]);assert.match(tiny,/1 adjusted input/);assert.match(tiny,/1 input has only small adjustments below 0.001/);assert.match(tiny,/Positive change below 0.001/);assert.match(tiny,/Negative change below 0.001/);assert.doesNotMatch(tiny,/All macro inputs have zero/);
const missing=render(['',0]);assert.match(missing,/1 unfinished values/);assert.match(missing,/Real GDP growth/);assert.doesNotMatch(missing,/All macro inputs have zero/);
const reset=render([0,0],[.2,.2]);assert.match(reset,/2 values edited/);
const resetDriverVisible=reset.includes('data-driver="20"');assert.equal(resetDriverVisible,true,'An input reset to zero must remain available for review');
console.log(JSON.stringify({tinyInputsHonest:true,missingInputsVisible:true,resetToZeroDriverVisible:resetDriverVisible,resetSummary:reset},null,2));
