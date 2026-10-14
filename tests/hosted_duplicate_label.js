// Run: node tests/hosted_duplicate_label.js
// S9: saving a case whose legend label is already saved in this visit explains what to do.
// Runs the real checkShareLabel() from the generated hosted page; the desktop page keeps its wording.
const fs=require('node:fs'),path=require('node:path'),vm=require('node:vm'),assert=require('node:assert/strict'),cp=require('node:child_process');
const root=process.env.ROOT||path.join(__dirname,'..');
const generated=cp.spawnSync(process.env.DSF_PYTHON||'python',['-B','-c','from lic_dsf.hosted import hosted_page; import sys; sys.stdout.buffer.write(hosted_page())'],{cwd:root,env:{...process.env,PYTHONPATH:path.join(root,'src')},encoding:'utf8'});
assert.equal(generated.status,0,generated.stderr);
function check(html){
 const code=html.slice(html.indexOf('function checkShareLabel('),html.indexOf('function legendRenames('));
 const s={textLength:v=>[...v].length,invalidInput:(input,message)=>{const e=Error(message);e.input=input;throw e;}};
 vm.createContext(s);vm.runInContext(code,s);return s.checkShareLabel;
}
const hosted=check(generated.stdout),input={id:'shareLabel'};
assert.throws(()=>hosted('No investment',input,[{id:'a',label:'No investment'}]),
 e=>e.message==='No investment is already saved in this visit. Open step 4 to include it in a comparison. To keep a second copy, give it a different legend label.'&&e.input===input);
assert.equal(hosted('No investment (copy)',input,[{id:'a',label:'No investment'}]),'No investment (copy)');
const desktop=check(fs.readFileSync(path.join(root,'src/lic_dsf/web.html'),'utf8'));
assert.throws(()=>desktop('No investment',input,[{id:'a',label:'No investment'}]),/^Error: Another case already uses the legend label/);
console.log('hosted_duplicate_label ok');
