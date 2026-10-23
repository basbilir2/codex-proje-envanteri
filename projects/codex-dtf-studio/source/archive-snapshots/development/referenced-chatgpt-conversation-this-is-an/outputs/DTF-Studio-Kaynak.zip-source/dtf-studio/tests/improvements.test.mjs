import test from 'node:test';
import assert from 'node:assert/strict';
import sharp from 'sharp';
import {writeFile} from 'node:fs/promises';
import {PDFDocument,PDFName} from 'pdf-lib';
import {layout,px} from '../src/engine.mjs';
import {planPngPages,exportInBrowser,zipFiles} from '../src/export.mjs';
import {cleanMatte,guidedAlpha} from '../src/matte.mjs';
const settings={film:570,gap:3,margin:5,dpi:300,mode:'quantity',metres:1,rotate:true,mirror:false};

test('large gang sheet splits only between whole designs; every copy fits a safe canvas',()=>{
  const sheet=layout([{id:'a',widthCm:12,heightCm:12,quantity:100}],settings),pages=planPngPages(sheet);
  assert.ok(pages.length>1);assert.equal(pages.reduce((n,p)=>n+p.count,0),100);
  assert.ok(Math.abs(pages.reduce((n,p)=>n+p.height,0)-sheet.height)<1e-8);
  for(const p of pages){assert.ok(px(p.width,300)*px(p.height,300)<=80e6);assert.ok(px(p.height,300)<=16384);for(const piece of p.placed){assert.ok(piece.y>=-1e-8);assert.ok(piece.y+piece.h<=p.height+1e-8);assert.equal(piece.w,120);assert.equal(piece.h,120);}}
});

test('oversized single design automatically becomes native PDF, with real size and transparency',async()=>{
  const sheet=layout([{id:'a',widthCm:20,heightCm:180,quantity:1}],{...settings,dpi:600,rotate:false,mirror:true});
  assert.equal(planPngPages(sheet),null);
  const png=await sharp({create:{width:20,height:30,channels:4,background:{r:240,g:80,b:30,alpha:.5}}}).png().toBuffer();
  const artifact=await exportInBrowser(sheet,[{id:'a',canvas:{toBlob:fn=>fn(new Blob([png],{type:'image/png'}))}}],'png');
  assert.equal(artifact.extension,'pdf');const bytes=await artifact.blob.arrayBuffer(),doc=await PDFDocument.load(bytes),page=doc.getPage(0),unit=page.node.get(PDFName.of('UserUnit'))?.asNumber()||1;
  assert.ok(Math.abs(page.getWidth()*unit*25.4/72-sheet.width)<1e-6);assert.ok(Math.abs(page.getHeight()*unit*25.4/72-sheet.height)<1e-6);
  await writeFile(new URL('../../../work/export-large-test.pdf',import.meta.url),new Uint8Array(bytes));
});

test('very long PDF uses UserUnit to preserve a 20 metre film without oversized MediaBox',async()=>{
  const sheet=layout([{id:'a',widthCm:20,heightCm:20,quantity:1}],{...settings,mode:'metres',metres:20,film:220});
  const png=await sharp({create:{width:2,height:3,channels:4,background:'red'}}).png().toBuffer();
  const artifact=await exportInBrowser(sheet,[{id:'a',canvas:{toBlob:fn=>fn(new Blob([png]))}}],'pdf'),doc=await PDFDocument.load(await artifact.blob.arrayBuffer()),page=doc.getPage(0),unit=page.node.get(PDFName.of('UserUnit')).asNumber();
  assert.ok(page.getHeight()<=14400);assert.ok(Math.abs(page.getHeight()*unit*25.4/72-20000)<1e-6);
});

test('matte removes faint dust and haze while retaining opaque punctuation and soft ink edges',()=>{
  const data=new Uint8ClampedArray(20*10*4),put=(x,y,a)=>{const k=(y*20+x)*4;data.set([70,150,230,a],k);};
  for(let y=3;y<7;y++)for(let x=5;x<10;x++)put(x,y,255);put(15,3,255);put(1,1,80);put(10,5,45);put(18,8,8);
  const clean=cleanMatte({data,width:20,height:10});
  assert.equal(clean.data[(1*20+1)*4+3],0);assert.equal(clean.data[(3*20+15)*4+3],255);assert.ok(clean.data[(5*20+10)*4+3]>0);assert.equal(clean.data[(8*20+18)*4+3],0);
});

test('guided alpha follows a source colour edge and preserves existing transparency',()=>{
  const data=new Uint8ClampedArray([10,10,10,255,10,10,10,255,240,240,240,255,240,240,240,0]);
  const result=guidedAlpha({data,width:4,height:1},{width:3,height:1,data:new Uint8Array([0,128,255])},{channels:4,data:new Uint8Array([10,10,10,255,10,10,10,255,240,240,240,255])});
  assert.ok(result.data[7]<128);assert.ok(result.data[11]>200);assert.equal(result.data[15],0);
});

test('PNG archive is independently readable as an ordinary ZIP',async()=>{
  const archive=await zipFiles([{name:'DTF-001.png',blob:new Blob([new Uint8Array([137,80,78,71])])},{name:'OKU.txt',blob:new Blob(['Ölçü korunur.'])}]);
  await writeFile(new URL('../../../work/export-test.zip',import.meta.url),new Uint8Array(await archive.arrayBuffer()));
});
