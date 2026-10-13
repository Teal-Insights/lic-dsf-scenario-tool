// Run: node tests/more_downloads.js
// Static markup check: one visible primary packet download with its save link; every other download sits in one closed disclosure.
const fs=require('fs'),path=require('path'),assert=require('assert/strict');
const html=fs.readFileSync(path.join(__dirname,'../src/lic_dsf/web.html'),'utf8');
const briefing=html.slice(html.indexOf('<section id="briefing"'),html.indexOf('</section>',html.indexOf('<section id="briefing"')));
const start=briefing.indexOf('<details id="moreDownloads"'),end=briefing.indexOf('</details>',start);
assert(start>0,'missing More download options disclosure');
const more=briefing.slice(start,end);
assert.match(more,/^<details id="moreDownloads" class="help"><summary>More download options<\/summary>/);
for(const id of ['excelTables','json','pdf','png'])assert(more.includes(`id="${id}"`),'#'+id+' must be inside More download options');
for(const view of ['standard','briefing'])for(const format of ['pdf','png','svg'])assert(more.includes(`data-format="${format}" data-view="${view}"`),format+' '+view+' must be inside More download options');
const outside=briefing.slice(0,start)+briefing.slice(end);
assert.equal((outside.match(/data-format=/g)||[]).length,1,'only the packet download stays outside the disclosure');
assert.match(outside,/<button id="packet" class="primary" data-format="zip">Download briefing packet \(\.zip\)<\/button><div id="preparedPacketRecovery" class="hidden">/);
assert(start>briefing.indexOf('id="preparedPacketRecovery"'),'disclosure follows the packet toolbar');
assert.equal((html.match(/>Download SVG</g)||[]).length,0,'SVG buttons name their chart set');
console.log('more_downloads ok');
