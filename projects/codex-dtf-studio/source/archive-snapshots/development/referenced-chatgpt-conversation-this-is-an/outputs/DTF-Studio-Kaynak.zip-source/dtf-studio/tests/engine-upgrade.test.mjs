import test from 'node:test';
import assert from 'node:assert/strict';
import {isolatePrint} from '../src/photo-extract.mjs';
import {refineMaskEdges,refineInkEdges} from '../src/matte.mjs';
import {preserveEnhancement} from '../src/enhance-fidelity.mjs';

export function clothFixture(dark=false){
  const width=160,height=100,data=new Uint8ClampedArray(width*height*4),truth=new Uint8Array(width*height);
  for(let y=0;y<height;y++)for(let x=0;x<width;x++){
    const k=y*width+x,u=x/width-.5,v=y/height-.5;
    const ink=(x>=38&&x<=120&&y>=25&&y<=72&&(x<42||x>116||y<29||y>68))||(x===132&&y>=65&&y<=73);
    const alpha=ink?1:0;truth[k]=alpha*255;
    const shade=(dark?207:125)+(dark?130:-200)*u*u+(dark?105:-180)*v*v+12*u-8*v;
    const noise=((x*17+y*13)%7-3)*.6;
    for(let c=0;c<3;c++)data[k*4+c]=alpha?(dark?12:235):shade+noise+c*2;
    data[k*4+3]=255;
  }
  return {data,width,height,truth};
}
test('curved illuminated cloth is removed while narrow light and dark ink survives',()=>{
  for(const dark of [false,true]){
    const image=clothFixture(dark),result=isolatePrint(image,{x:0,y:0,width:image.width,height:image.height},8,{contract:false});
    assert.equal(result.method,dark?'dark-ink':'light-ink');assert.equal(result.fabric.curved,true);
    let falseInk=0,missed=0;
    for(let k=0;k<image.truth.length;k++){if(!image.truth[k]&&result.data[k*4+3]>20)falseInk++;if(image.truth[k]&&result.data[k*4+3]<220)missed++;}
    assert.equal(falseInk,0);assert.equal(missed,0);
  }
});
test('native edge decontamination removes a white halo without inventing alpha or touching source',()=>{
  const width=11,height=3,data=new Uint8ClampedArray(width*height*4),mask=new Uint8ClampedArray(data.length);
  for(let y=0;y<height;y++)for(let x=0;x<width;x++){
    const a=x<3?0:x===3?.25:x===4?.5:x===5?.75:1,p=(y*width+x)*4;
    for(let c=0;c<3;c++)data[p+c]=Math.round(255*(1-a)+[20,80,120][c]*a);
    data[p+3]=255;mask.set(data.subarray(p,p+4),p);mask[p+3]=Math.round(a*255);
  }
  const source=new Uint8ClampedArray(data),out=refineMaskEdges({data,width,height},{data:mask,width,height});
  assert.deepEqual(data,source);const p=(width+4)*4;
  assert.ok(Math.abs(out.data[p+3]-128)<=1);assert.ok(out.data[p]<mask[p]-60);assert.ok(out.data[p+2]<mask[p+2]-40);
  assert.equal(out.data[3],0);assert.equal(out.data[(width-1)*4+3],255);
  data[p+3]=80;mask[p+3]=40;const transparent=refineMaskEdges({data,width,height},{data:mask,width,height});assert.equal(transparent.data[p+3],40);
});
test('super-resolution rejects colour drift and invalid output, preserving alpha and holes',()=>{
  const width=8,height=3,data=new Uint8ClampedArray(width*height*4),neural=new Float32Array(width*height*3);
  for(let k=0;k<width*height;k++){data.set([20,150,210,k===5?0:k===6?38:255],k*4);neural.set([150,70,250],k*3);}
  const original=new Uint8ClampedArray(data),out=preserveEnhancement({data,width,height},neural);
  assert.deepEqual(data,original);
  for(let k=0;k<width*height;k++){assert.equal(out.data[k*4+3],data[k*4+3]);for(let c=0;c<3;c++)if(data[k*4+3])assert.ok(Math.abs(out.data[k*4+c]-data[k*4+c])<=10);}
  assert.deepEqual([...out.data.subarray(20,24)],[0,0,0,0]);
  neural[0]=NaN;assert.throws(()=>preserveEnhancement({data,width,height},neural),/geçersiz/);
  assert.throws(()=>preserveEnhancement({data,width,height},[]),/boyutu/);
});
test('ink finishing defines soft edges without closing holes, losing faint marks or changing colour',()=>{
  const width=12,height=5,data=new Uint8ClampedArray(width*height*4);
  for(let y=0;y<height;y++)for(let x=3;x<=7;x++)data.set([220,225,230,x===5?210:50],(y*width+x)*4);
  data.set([220,225,230,18],(2*width+10)*4);const copy=new Uint8ClampedArray(data),out=refineInkEdges({data,width,height});
  assert.deepEqual(data,copy);assert.ok(out.data[(2*width+5)*4+3]>210);assert.ok(out.data[(2*width+10)*4+3]>0);
  for(let k=0;k<width*height;k++){if(!data[k*4+3])assert.equal(out.data[k*4+3],0);assert.deepEqual(out.data.subarray(k*4,k*4+3),data.subarray(k*4,k*4+3));}
});
test('large native matte tiles preserve edge refinement across a tile boundary',()=>{
  const width=1100,height=920,data=new Uint8ClampedArray(width*height*4),mask=new Uint8ClampedArray(data.length);
  for(let y=0;y<height;y++)for(let x=0;x<width;x++){const a=x<510?0:x<514?(x-509)/5:1,p=(y*width+x)*4;data.set([255*(1-a)+20*a,255*(1-a)+80*a,255*(1-a)+120*a,255],p);mask.set(data.subarray(p,p+4),p);mask[p+3]=Math.round(a*255);}
  const out=refineMaskEdges({data,width,height},{data:mask,width,height});
  for(const y of [10,511,512,900])assert.deepEqual(out.data.subarray((y*width+510)*4,(y*width+514)*4),out.data.subarray((10*width+510)*4,(10*width+514)*4));
  assert.ok(out.data[(512*width+511)*4]<mask[(512*width+511)*4]-40);
});
