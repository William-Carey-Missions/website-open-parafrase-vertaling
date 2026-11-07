const fs=require('fs'),path=require('path');
const {JSDOM}=require('jsdom');
// Vereist jsdom, bijvoorbeeld via NODE_PATH naar een tijdelijke npm-installatie.
const root=process.argv[2] || path.resolve(__dirname, '..');
const dom=new JSDOM('',{runScripts:'outside-only'});
dom.window.eval(fs.readFileSync(path.join(root,'js/woordnummers.js'),'utf8'));
const api=dom.window.OVWoordnummers;
let verses=0,links=0,failures=[];
for(const book of ['henoch','jubileeen','1meqabyan','2meqabyan','3meqabyan','4baruch']){
 for(const name of fs.readdirSync(path.join(root,'data',book))){
  if(!/^\d+\.json$/.test(name))continue;
  const data=JSON.parse(fs.readFileSync(path.join(root,'data',book,name)));
  for(const v of data.verses){
   const mappings=v.woordnummers||[];
   const expected=mappings.filter(m=>!m.reviewstatus||['handmatig_gecontroleerd','automatisch_hoog_vertrouwen'].includes(m.reviewstatus)).reduce((n,m)=>n+m.strongs.length,0);
   const out=api.renderInline(v.text2026_html||v.text2026,mappings);
   const wrap=dom.window.document.createElement('div');wrap.innerHTML=out;
   const actual=wrap.querySelectorAll('button.strongs-inline').length;
   if(actual!==expected)failures.push([book,data.number,v.number,expected,actual]);
   wrap.querySelectorAll('button.strongs-inline').forEach(b=>b.remove());
   const original=dom.window.document.createElement('div');original.innerHTML=v.text2026_html||v.text2026;
   if(wrap.textContent!==original.textContent)failures.push([book,data.number,v.number,'text changed']);
   verses++;links+=actual;
  }
 }
}
console.log(JSON.stringify({verses,links,failures},null,2));
process.exitCode=failures.length?1:0;
