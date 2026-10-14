// Run: node tests/hover_help_stacking.js
// S8: a hovered or focused hint host is lifted above its neighbours (button:hover{filter} and
// button:disabled{opacity} make the host its own stacking context, trapping its ::after), and
// summaries no longer carry a hint that only restates the summary. Static markup check.
const fs=require('node:fs'),path=require('node:path'),assert=require('node:assert/strict');
const root=process.env.ROOT||path.join(__dirname,'..');
const html=fs.readFileSync(path.join(root,'src/lic_dsf/web.html'),'utf8');
assert(/button:hover\{filter:/.test(html),'premise: hovered buttons create a stacking context');
assert(/\[data-hint\]:hover,\[data-hint\]:focus-visible\{z-index:30\}/.test(html),'hovered or focused hint host must sit above its neighbours');
const restated=['Share or reuse a scenario file','What is included, and can I change it?','About this input: units, sign and meaning',
 'What should I write, and who will see it?','Review or edit every year and input','What do these financing controls change?',
 'What should I explain about financing?','Review explanations for sharing','What is the comparison case?',
 'How are these summaries calculated?','What is in the packet, and which file should I open?',
 'Which assumptions differ from the comparison case?','Review shared explanations before exporting'];
const esc=s=>s.replace(/[.*+?^${}()|[\]\\]/g,'\\$&');
for(const s of restated){
 assert(html.includes('<summary>'+s+'</summary>'),'summary still present without hint: '+s);
 assert(!new RegExp('<summary data-hint="[^"]*">'+esc(s)+'</summary>').test(html),'restating hint kept on: '+s);
}
// Hints that add the answer stay.
for(const s of ['What is different about the two chart styles?','How do changes differ from levels?'])
 assert(new RegExp('<summary data-hint="[^"]{20,}">'+esc(s)+'</summary>').test(html),'keep answering hint on: '+s);
console.log('hover_help_stacking ok');
