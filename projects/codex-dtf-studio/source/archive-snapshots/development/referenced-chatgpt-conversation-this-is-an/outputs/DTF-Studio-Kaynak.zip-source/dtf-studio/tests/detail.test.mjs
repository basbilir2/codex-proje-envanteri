import test from 'node:test';
import assert from 'node:assert/strict';
import {refineDetails} from '../src/detail.mjs';

test('soft lines become more defined while holes, faint dots, size and source remain intact',()=>{
  const width=21,height=13,data=new Uint8ClampedArray(width*height*4);
  const set=(x,y,a)=>data.set([220,232,240,a],(y*width+x)*4);
  for(let y=2;y<11;y++){set(5,y,30);set(6,y,110);set(7,y,30);set(14,y,255);}
  set(18,3,18);const original=new Uint8ClampedArray(data),out=refineDetails({data,width,height});
  assert.equal(out.width,width);assert.equal(out.height,height);assert.deepEqual(data,original);
  assert.ok(out.data[(6*width+6)*4+3]>110);assert.ok(out.data[(6*width+5)*4+3]<30);
  assert.ok(out.data[(3*width+18)*4+3]>=18);
  for(let i=0;i<width*height;i++)assert.equal(out.data[i*4+3]>0,data[i*4+3]>0);
  assert.equal(out.data[(6*width+10)*4+3],0);assert.equal(out.data[(6*width+14)*4+3],255);
});

test('transparent RGB does not create halos, flat ink colours stay constant and luminance correction is bounded',()=>{
  const width=12,height=7,data=new Uint8ClampedArray(width*height*4);
  for(let y=0;y<height;y++)for(let x=0;x<width;x++)data.set(x<4?[0,0,0,0]:x<9?[20,180,220,255]:[50,210,250,255],(y*width+x)*4);
  const out=refineDetails({data,width,height});
  assert.deepEqual([...out.data.slice((3*width+4)*4,(3*width+4)*4+3)],[20,180,220]);
  for(let k=0;k<width*height;k++)for(let c=0;c<3;c++)assert.ok(Math.abs(out.data[k*4+c]-data[k*4+c])<=12);
  assert.deepEqual([...out.data.slice(0,4)],[0,0,0,0]);
});
