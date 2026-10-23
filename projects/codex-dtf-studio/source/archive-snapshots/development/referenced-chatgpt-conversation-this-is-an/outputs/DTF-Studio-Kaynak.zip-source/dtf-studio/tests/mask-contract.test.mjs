import test from 'node:test';
import assert from 'node:assert/strict';
import {contractAlpha1px} from '../src/matte.mjs';

test('one source pixel contracts every outer edge without resizing or changing the input',()=>{
  const data=new Uint8ClampedArray(9*9*4);
  for(let y=1;y<=7;y++)for(let x=1;x<=7;x++)data.set([80,150,220,255],(y*9+x)*4);
  const input=new Uint8ClampedArray(data),out=contractAlpha1px({data,width:9,height:9});
  assert.equal(out.width,9);assert.equal(out.height,9);assert.deepEqual(data,input);
  for(let y=0;y<9;y++)for(let x=0;x<9;x++)assert.equal(out.data[(y*9+x)*4+3],x>=2&&x<=6&&y>=2&&y<=6?255:0);
  assert.deepEqual([...out.data.slice((2*9+2)*4,(2*9+2)*4+4)],[80,150,220,255]);
  assert.deepEqual([...out.data.slice((1*9+1)*4,(1*9+1)*4+4)],[0,0,0,0]);
});

test('inner holes contract too and soft alpha values remain soft',()=>{
  const data=new Uint8ClampedArray(9*9*4);
  for(let k=0;k<81;k++)data.set([70,140,210,255],k*4);
  data[(4*9+4)*4+3]=0;data[(1*9+1)*4+3]=128;
  const out=contractAlpha1px({data,width:9,height:9});
  for(let y=3;y<=5;y++)for(let x=3;x<=5;x++)assert.equal(out.data[(y*9+x)*4+3],0);
  assert.equal(out.data[(2*9+2)*4+3],128);
  assert.equal(out.data[(2*9+6)*4+3],255);
});
