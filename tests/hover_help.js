// Run: node tests/hover_help.js
// Static markup check: every route control has short hover help that also shows on keyboard focus,
// and the two chart sets carry their agreed names. Visible text stays the primary guidance.
const fs=require('fs'),path=require('path'),assert=require('assert/strict');
const html=fs.readFileSync(path.join(__dirname,'../src/lic_dsf/web.html'),'utf8');
for(const id of ['exampleButton','newZero','loadBuiltinInvestment','save','calculate','compareButton','packet','preview','json'])
 assert(new RegExp(`id="${id}"[^>]*data-hint="[^"]{12,}"`).test(html),'missing hint on #'+id);
assert(/\[data-hint\]:hover::after,\[data-hint\]:focus-visible::after\{/.test(html),'hint CSS must cover keyboard focus');
assert(/@media\(hover:none\)\{\[data-hint\]::after\{display:none!important\}\}/.test(html),'hints stay off touch screens');
assert(/<h3>Standard LIC-DSF charts<\/h3>/.test(html)&&/<h3>Policy briefing charts<\/h3>/.test(html),'chart set names');
// Hints never run off the page: capped by the viewport, and right-edge controls open leftwards.
assert(/max-width:min\(320px,calc\(100vw - 32px\)\)/.test(html),'hint width capped by the viewport');
assert(/#loadBuiltinInvestment\[data-hint\]::after\{left:auto;right:0\}/.test(html),'right-edge hint opens leftwards');
console.log('hover_help ok');
