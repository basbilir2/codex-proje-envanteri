import test from 'node:test';
import assert from 'node:assert/strict';
import {mkdtemp,writeFile,readFile,rm,mkdir} from 'node:fs/promises';
import {tmpdir} from 'node:os';
import {join,resolve} from 'node:path';
import {fileURLToPath} from 'node:url';
import {randomUUID} from 'node:crypto';
import {spawn,spawnSync} from 'node:child_process';
import sharp from 'sharp';
import {validateQuad,rectify} from '../geometry.mjs';
import {inspectSource,recover,exportPNG,modelSize} from '../pipeline.mjs';
import {qwenAdapter} from '../qwen-adapter.mjs';

async function workspace(t){const dir=await mkdtemp(join(tmpdir(),'artwork-recovery-test-'));t.after(async()=>{if(!resolve(dir).startsWith(resolve(tmpdir())+'\\')&&process.platform==='win32')throw Error('Unsafe test cleanup');await rm(dir,{recursive:true,force:true});});return dir;}
async function fixture(width=240,height=160){
  const rgb=Buffer.alloc(width*height*3);
  for(let y=0;y<height;y++)for(let x=0;x<width;x++){const k=(y*width+x)*3;rgb[k]=Math.round(x/(width-1)*255);rgb[k+1]=Math.round(y/(height-1)*255);rgb[k+2]=((x>>3)+(y>>3))%2?220:30;}
  return sharp(rgb,{raw:{width,height,channels:3}}).png().toBuffer();
}
// Deliberately a transport double, NEVER evidence of model quality.
function transportDouble(calls){return {async run(ctx){calls.push(ctx);ctx.progress({stage:'TEST SAMPLE',done:4,total:4});ctx.progress({stage:'TEST DECODE'});await writeFile(join(ctx.dir,'reconstructed.png'),await readFile(join(ctx.dir,'input.png')));return {kind:'generative-reconstruction',model:'TEST-TRANSPORT-DOUBLE',status:'completed',seconds:0};}};}
test('browser modules parse before serving the editor',()=>{for(const file of ['app.mjs','layout.mjs','editor.mjs']){const check=spawnSync(process.execPath,['--check',fileURLToPath(new URL('../web/'+file,import.meta.url))],{encoding:'utf8',windowsHide:true});assert.equal(check.status,0,check.stderr);}});
test('EXIF orientation and source bytes are preserved independently',async()=>{
  const input=await sharp(await fixture(80,40)).jpeg().withMetadata({orientation:6}).toBuffer(),before=Buffer.from(input);
  const result=await inspectSource(input);assert.equal(result.source.width,40);assert.equal(result.source.height,80);assert.deepEqual(input,before);assert.match(result.source.sha256,/^[0-9a-f]{64}$/);
});
test('four-point homography samples the correct original coordinates',async()=>{
  const source=await fixture(120,100),points=[{x:20,y:10},{x:100,y:20},{x:90,y:90},{x:10,y:80}],out=await rectify(source,points);
  const a=await sharp(source).raw().toBuffer(),b=await sharp(out.buffer).raw().toBuffer();
  for(const [i,[x,y]] of [[0,[0,0]],[1,[out.width-1,0]],[2,[out.width-1,out.height-1]],[3,[0,out.height-1]]])for(let c=0;c<3;c++)assert.ok(Math.abs(b[(y*out.width+x)*3+c]-a[(points[i].y*120+points[i].x)*3+c])<=1);
});
test('crossed, reversed, degenerate and out-of-bounds quads fail',()=>{
  for(const p of [[{x:0,y:0},{x:90,y:90},{x:90,y:0},{x:0,y:90}],[{x:0,y:0},{x:0,y:90},{x:90,y:90},{x:90,y:0}],[{x:0,y:0},{x:3,y:0},{x:3,y:3},{x:0,y:3}],[{x:0,y:0},{x:100,y:0},{x:90,y:90},{x:0,y:90}]])assert.throws(()=>validateQuad(p,100,100));
});
test('thin aspect ratios use padding rather than stretching',()=>{
  const s=modelSize(100,3000);assert.equal(s.height,512);assert.equal(s.width,128);assert.ok(s.contentWidth<20);assert.ok(Math.abs(s.contentWidth/s.contentHeight-1/30)<.002);assert.ok(s.left>0);
});
test('recovery routes flat artwork to its adapter and never accepts semantic quality',async t=>{
  const dir=await workspace(t),bytes=await fixture(),input=await inspectSource(bytes),calls=[],progress=[];
  const report=await recover({dir,...input,task:'repair-artwork',engine:transportDouble(calls),progress:p=>progress.push(p.done)});
  assert.equal(calls.length,1);assert.equal(calls[0].task,'repair-artwork');assert.equal(report.quality.printReady,false);assert.equal(report.quality.status,'unverified');assert.equal(report.output.width/report.output.height,1.5);assert.deepEqual(await readFile(join(dir,'prepared.png')),input.normalized);assert.equal(progress.at(-1),100);assert.ok(progress.every((v,i)=>!i||v>=progress[i-1]));
  const saved=JSON.parse(await readFile(join(dir,'recovery.json')));assert.equal(saved.reconstruction.model,'TEST-TRANSPORT-DOUBLE');assert.equal(saved.steps.at(-1).surfaceRemoval,'not-verified');
});
test('crop and perspective are mutually exclusive and failed records stay explicit',async t=>{
  const dir=await workspace(t),input=await inspectSource(await fixture());let ran=false;
  await assert.rejects(recover({dir,...input,region:{left:0,top:0,width:80,height:80},quad:[],engine:{run(){ran=true;}}}),/aynı anda/);assert.equal(ran,false);assert.equal(JSON.parse(await readFile(join(dir,'recovery.json'))).status,'failed');
});
test('source region is cropped before generation',async t=>{
  const dir=await workspace(t),input=await inspectSource(await fixture()),calls=[];
  const report=await recover({dir,...input,region:{left:40,top:20,width:120,height:80},engine:transportDouble(calls)});
  assert.deepEqual(report.selection.region,{left:40,top:20,width:120,height:80});const m=await sharp(join(dir,'prepared.png')).metadata();assert.equal(m.width,120);assert.equal(m.height,80);
});
test('blank and wrong-sized outputs cannot become successful recovery',async t=>{
  const input=await inspectSource(await fixture());
  for(const bad of ['blank','size']){const dir=await workspace(t);await assert.rejects(recover({dir,...input,engine:{async run(ctx){await sharp({create:{width:bad==='size'?16:ctx.width,height:ctx.height,channels:3,background:'#fff'}}).png().toFile(join(dir,'reconstructed.png'));return {kind:'generative-reconstruction',model:'TEST-INVALID'};}}}));assert.equal(JSON.parse(await readFile(join(dir,'recovery.json'))).status,'failed');await assert.rejects(readFile(join(dir,'enhanced.png')));}
});
test('engine failure has no sharpening/upscale fallback',async t=>{
  const dir=await workspace(t),input=await inspectSource(await fixture());await assert.rejects(recover({dir,...input,engine:{async run(){throw Error('TEST MOTOR ERROR');}}}),/TEST MOTOR ERROR/);await assert.rejects(readFile(join(dir,'enhanced.png')));
});
test('pre-cancelled recovery never starts the engine',async t=>{
  const dir=await workspace(t),input=await inspectSource(await fixture()),controller=new AbortController();controller.abort();let ran=false;await assert.rejects(recover({dir,...input,signal:controller.signal,engine:{run(){ran=true;}}}));assert.equal(ran,false);assert.equal(JSON.parse(await readFile(join(dir,'recovery.json'))).status,'cancelled');
});
test('PNG export preserves soft alpha and records enlargement separately',async t=>{
  const dir=await workspace(t),rgba=Buffer.alloc(80*40*4);for(let i=0;i<80*40;i++){rgba[i*4]=80;rgba[i*4+1]=120;rgba[i*4+2]=200;rgba[i*4+3]=i%80<10?0:i%80<20?128:255;}
  await sharp(rgba,{raw:{width:80,height:40,channels:4}}).png().toFile(join(dir,'edited.png'));
  const out=await exportPNG({dir,input:'edited',longEdge:2048,dpi:300}),meta=await sharp(join(dir,'export.png')).metadata();assert.equal(out.width,2048);assert.equal(out.height,1024);assert.equal(meta.density,300);assert.equal(meta.hasAlpha,true);assert.equal(out.containsTransparency,true);assert.equal(out.printReady,false);assert.equal(out.realDetailVerified,false);assert.equal(out.resampling,'Lanczos3');
  await assert.rejects(exportPNG({dir,input:'edited',longEdge:8192}),/24 megapiksel/);
});
test('adapter cancellation reaps both worker and its subprocess (no model)',{timeout:15000},async t=>{
  const dir=await workspace(t);await mkdir(join(dir,'job'));
  await writeFile(join(dir,'qwen_worker.py'),"import subprocess,sys,json,time\np=subprocess.Popen([sys.executable,'-c','import time;time.sleep(60)'])\nprint(json.dumps({'stage':'TEST-PROCESS','pid':p.pid}),flush=True)\ntime.sleep(60)\n");
  const controller=new AbortController();let pid;
  const adapter=qwenAdapter(dir,{python:process.env.RECOVERY_TEST_PYTHON||'python'});
  await assert.rejects(adapter.run({dir:join(dir,'job'),task:'extract-design',width:128,height:128,signal:controller.signal,progress:p=>{pid=p.pid;controller.abort();}}));
  assert.ok(pid);assert.throws(()=>process.kill(pid,0));
});
test('HTTP service rejects filter fallback and saves/exports persisted PNG without inference',{timeout:15000},async()=>{
  const root=fileURLToPath(new URL('..',import.meta.url)),port=17862,base=`http://127.0.0.1:${port}`,child=spawn(process.execPath,['server.mjs'],{cwd:root,env:{...process.env,RECOVERY_PORT:String(port)},windowsHide:true,stdio:['ignore','pipe','pipe']});
  const id=randomUUID(),dir=join(root,'jobs',id);assert.equal(resolve(dir),resolve(root,'jobs',id));await mkdir(dir,{recursive:true});
  try{
    await new Promise((resolve,reject)=>{child.once('error',reject);child.once('exit',code=>reject(Error('Server exit '+code)));child.stdout.once('data',resolve);});
    const html=await (await fetch(base)).text(),token=html.match(/APP_TOKEN="([^"]+)"/)[1];
    assert.equal((await (await fetch(base+'/api/status')).json()).purpose,'artwork-reconstruction');
    assert.equal((await fetch(base+'/api/recover',{method:'POST',body:'x'})).status,403);
    const headers={Origin:base,'X-App-Token':token};
    const quick=await fetch(base+'/api/enhance?mode=quick',{method:'POST',headers,body:'x'});assert.equal(quick.status,400);assert.match((await quick.json()).error,/kaldırıldı/);
    assert.equal((await fetch(base+'/api/recover',{method:'POST',headers,body:'not-an-image'})).status,400);
    assert.equal((await (await fetch(base+'/api/status')).json()).active,null);
    assert.equal((await fetch(base+'/web/%2e%2e%2fserver.mjs')).status,403);
    // This fixture verifies persistence/export transport, not a generated result.
    await writeFile(join(dir,'job.json'),JSON.stringify({id,status:'completed',testFixture:true}));
    const rgba=await sharp(await fixture(160,80)).ensureAlpha(.5).png().toBuffer();
    assert.equal((await fetch(base+'/api/edited/'+id,{method:'POST',headers,body:rgba})).status,200);
    const exported=await fetch(base+'/api/export/'+id,{method:'POST',headers,body:JSON.stringify({input:'edited',longEdge:2048,dpi:300})});assert.equal(exported.status,200);
    const data=await exported.json(),download=await fetch(base+data.output);assert.equal(download.status,200);const meta=await sharp(Buffer.from(await download.arrayBuffer())).metadata();assert.equal(meta.width,2048);assert.equal(meta.hasAlpha,true);
    const report=await (await fetch(base+data.report)).json();assert.equal(report.printReady,false);assert.equal(report.containsTransparency,true);
    assert.equal((await fetch(base+'/result/'+id+'/input.png')).status,404);
  }finally{const closed=new Promise(resolve=>child.once('close',resolve));child.kill();await closed;if(resolve(dir)===resolve(root,'jobs',id))await rm(dir,{recursive:true,force:true});}
});
