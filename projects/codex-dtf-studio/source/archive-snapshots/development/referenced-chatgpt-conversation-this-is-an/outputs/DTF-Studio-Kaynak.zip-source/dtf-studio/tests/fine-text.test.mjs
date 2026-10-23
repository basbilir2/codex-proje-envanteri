import test from 'node:test';import assert from 'node:assert/strict';
import {strengthenFineText} from '../src/fine-text.mjs';
test('local text deblurring steepens soft strokes; holes, RGB, size, source and pixels outside selection remain intact',()=>{
  const width=44,height=23,data=new Uint8ClampedArray(width*height*4);
  for(let y=3;y<20;y++)for(let x=4;x<40;x++)data.set([220,224,232,x===20?140:x===19||x===21?45:0],(y*width+x)*4);
  const copy=new Uint8ClampedArray(data),roi={x:15,y:1,width:12,height:21},out=strengthenFineText({data,width,height},roi);
  assert.deepEqual(data,copy);assert.equal(out.width,width);assert.equal(out.height,height);assert.ok(out.data[(10*width+20)*4+3]>140);assert.ok(out.data[(10*width+19)*4+3]<45);
  for(let y=0;y<height;y++)for(let x=0;x<width;x++){const p=(y*width+x)*4;assert.deepEqual(out.data.subarray(p,p+3),data.subarray(p,p+3));if(!data[p+3])assert.equal(out.data[p+3],0);if(x<15||x>=27||y<1||y>=22)assert.deepEqual(out.data.subarray(p,p+4),data.subarray(p,p+4));}
});
test('opaque/unprepared images and accidentally tiny selections fail without changing the source',()=>{
  const image={width:10,height:10,data:new Uint8ClampedArray(400).fill(255)},copy=new Uint8ClampedArray(image.data);
  assert.throws(()=>strengthenFineText(image,{x:0,y:0,width:10,height:10}),/arka planı/);assert.throws(()=>strengthenFineText(image,{x:3,y:3,width:1,height:1}),/geniş/);assert.deepEqual(image.data,copy);
});
