import test from 'node:test';
import assert from 'node:assert/strict';
import {guidedAlpha} from '../src/matte.mjs';
import {isolatePrint} from '../src/photo-extract.mjs';

test('hard low-resolution mask boundaries are refined instead of enlarged as steps',()=>{
  const data=new Uint8ClampedArray(8*4);for(let i=0;i<8;i++)data.set([120,120,120,255],i*4);
  const out=guidedAlpha({data,width:8,height:1},{width:2,height:1,data:new Uint8Array([0,255])},{channels:3,data:new Uint8Array([120,120,120,120,120,120])});
  const alpha=Array.from({length:8},(_,i)=>out.data[i*4+3]);
  assert.ok(alpha[3]>0&&alpha[3]<128);assert.ok(alpha[4]>128&&alpha[4]<255);
  for(let i=1;i<8;i++)assert.ok(alpha[i]>=alpha[i-1]);
  assert.deepEqual(data.slice(0,4),new Uint8ClampedArray([120,120,120,255]));
});

test('fine one-pixel ink can be retained by disabling contraction',()=>{
  const data=new Uint8ClampedArray(40*30*4);for(let i=0;i<1200;i++)data.set([30,30,30,255],i*4);
  for(let y=8;y<22;y++)data.set([240,240,240,255],(y*40+20)*4);
  const image={data,width:40,height:30},region={x:0,y:0,width:40,height:30};
  assert.throws(()=>isolatePrint(image,region,28,{inkMode:'colour'}),/ayrılamadı/);
  const out=isolatePrint(image,region,28,{contract:false});
  assert.equal(out.bounds.width,1);assert.equal(out.bounds.height,14);assert.equal(out.data[(10*40+20)*4+3],255);assert.equal(out.data[3],0);
});
