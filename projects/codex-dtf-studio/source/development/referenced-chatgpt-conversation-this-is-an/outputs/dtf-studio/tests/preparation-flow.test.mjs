import test from 'node:test';
import assert from 'node:assert/strict';
import vm from 'node:vm';
import {fileURLToPath} from 'node:url';
import {build} from 'esbuild';

const bundle=await build({entryPoints:[fileURLToPath(new URL('../src/studio.mjs',import.meta.url))],bundle:true,format:'iife',write:false,external:['https://*']});
const registry=new Map();
class Element{
  attachShadow(){this.shadowRoot={querySelector:()=>null};}
  setAttribute(name,value){(this.attributes??={})[name]=value;}
}
vm.runInNewContext(bundle.outputFiles[0].text,{HTMLElement:Element,customElements:{get:n=>registry.get(n),define:(n,c)=>registry.set(n,c)},URL,Blob,clearTimeout,setTimeout,TextEncoder,TextDecoder});
const Studio=registry.get('dtf-studio');

test('unapproved artwork cannot start packing or export',async()=>{
  const studio=new Studio();let calculations=0;
  studio.calculateLayout=()=>{calculations++;throw new Error('Packing started too early');};
  studio.syncPreparation=()=>{};
  studio.scheduleArrange();await studio.arrange();
  assert.equal(calculations,0);assert.equal(studio.autoPending,false);
  await assert.rejects(studio.export(),/Dizgiye geç/);
});

test('returning to image preparation invalidates the existing layout and download',()=>{
  const studio=new Studio(),elements=new Map();
  for(const id of ['prepare','prepare-note','preview-title','export','arrange','refresh','export-note','count','length','util','film-summary','preview'])elements.set('#'+id,{classList:{toggle(){}},replaceChildren(){this.innerHTML='';}});
  studio.$=id=>elements.get(id);studio.drawPreparation=()=>{};
  studio.prepared=true;studio.result={count:20};studio.exportRequest='old-export';studio.downloadUrl='blob:old-download';studio.designs=[{}];
  let cancelled=0;studio.calculateLayout.cancel=()=>{cancelled++;};
  studio.beginPreparation();
  assert.equal(studio.prepared,false);assert.equal(studio.result,null);assert.equal(studio.downloadUrl,null);assert.equal(studio.exportRequest,null);assert.equal(cancelled,1);
  assert.equal(elements.get('#export').disabled,true);assert.equal(elements.get('#arrange').disabled,true);
  assert.equal(elements.get('#prepare').textContent,'Görseli hazırla →');assert.equal(studio.attributes['data-stage'],'prepare');
});
