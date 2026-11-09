const {test}=require('node:test');
const assert=require('node:assert/strict');
const fs=require('node:fs'),path=require('node:path');
const {JSDOM}=require('jsdom');
const root=path.resolve(__dirname,'..');
function runtime(){const d=new JSDOM('',{url:'https://open-parafrase-weergave.nl',runScripts:'outside-only'});for(const p of ['js/teksteditie.js','js/woordnummers.js'])d.window.eval(fs.readFileSync(path.join(root,p),'utf8'));return d;}
for (const [chapterNumber, expected] of [[1,132],[2,119],[3,88]]) test(`de parafrase geeft eigen koppelingen door in hoofdstuk ${chapterNumber}`,()=>{
 const d=runtime(),chapter=JSON.parse(fs.readFileSync(path.join(root,`data/vertalingen/nl-opv/4baruch/${chapterNumber}.json`)));
 const reader=d.window.TekstEditie.chapterToReaderData(chapter,{code:'nl-opv'});let total=0;
 for(const verse of reader.verses){
  const el=d.window.document.createElement('div');el.innerHTML=d.window.OVWoordnummers.renderInline(verse.text2026_html,verse.woordnummers);
  const buttons=el.querySelectorAll('button.strongs-inline');
  assert.equal(buttons.length,verse.woordnummers.reduce((n,m)=>n+m.strongs.length,0));total+=buttons.length;buttons.forEach(b=>b.remove());assert.equal(el.textContent,verse.text2026);
 }
 assert.equal(total,expected);
 if(chapterNumber===3){ const six=reader.verses.find(v=>v.number===6);const said=six.woordnummers.find(m=>m.strongs.includes('OVG3760'));assert.equal(said.tekst,'zei');assert.equal(said.voorkomen,1); }
 d.window.close();
});
test('de parafrase neemt geen koppelingen uit een andere teksteditie over',()=>{
 const d=runtime();const chapter={hoofdstuk:1,verzen:[{nummer:1,tekst:'Een eigen formulering.'}]};
 const result=d.window.TekstEditie.chapterToReaderData(chapter,{code:'nl-opv'});assert.equal(result.verses[0].woordnummers.length,0);d.window.close();
});
