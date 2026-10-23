import test from 'node:test';
import assert from 'node:assert/strict';
import {cropPrintRegion,enhancePrintRegion,isolateEnhancedPrint} from '../src/prepare-print.mjs';
import {isolatePrint} from '../src/photo-extract.mjs';

function fixture(){
  const width=80,height=50,data=new Uint8ClampedArray(width*height*4);
  for(let y=0;y<height;y++)for(let x=0;x<width;x++)data.set([30+x*.08,40+y*.05,60,255],(y*width+x)*4);
  const ink=(x,y,a=255)=>data.set([220,224,229,a],(y*width+x)*4);
  for(let y=12;y<=35;y++)for(let x=15;x<=60;x++)if(x===15||x===60||y===12||y===35)ink(x,y);
  ink(66,35);for(let x=20;x<35;x++)ink(x,40);
  return {data,width,height};
}

test('initial crop retains the fabric and source pixels without enhancement or masking',()=>{
  const source=fixture(),copy=new Uint8ClampedArray(source.data),crop=cropPrintRegion(source,{x:5,y:5,width:70,height:40});
  assert.equal(crop.width,70);assert.equal(crop.height,40);assert.deepEqual(source.data,copy);
  assert.deepEqual(crop.source,{x:5,y:5,width:70,height:40});
  for(let y=0;y<40;y++)for(let x=0;x<70;x++)assert.deepEqual(crop.data.subarray((y*70+x)*4,(y*70+x)*4+4),source.data.subarray(((y+5)*80+x+5)*4,((y+5)*80+x+5)*4+4));
  assert.equal(crop.data[3],255);assert.ok(crop.data[0]<100);
});

test('opaque crop is enhanced before masking; detached dots, thin outlines and transparent holes survive',async()=>{
  const source=fixture(),events=[];
  const prepared=await enhancePrintRegion(source,{x:5,y:5,width:70,height:40},async image=>{
    events.push('enhance');for(let i=3;i<image.data.length;i+=4)assert.equal(image.data[i],255);
    const width=image.width*2,height=image.height*2,data=new Uint8ClampedArray(width*height*4);
    for(let y=0;y<height;y++)for(let x=0;x<width;x++)data.set(image.data.subarray((Math.floor(y/2)*image.width+Math.floor(x/2))*4,(Math.floor(y/2)*image.width+Math.floor(x/2))*4+4),(y*width+x)*4);
    return {data,width,height};
  });
  const result=isolateEnhancedPrint(prepared,28,{contract:false});events.push('mask');
  assert.deepEqual(events,['enhance','mask']);assert.equal(result.method,'light-ink');
  assert.deepEqual(result.preparedSource,{x:5,y:5,width:70,height:40});assert.equal(result.scale,2);
  const a=(x,y)=>result.data[((y-5)*2*result.width+(x-5)*2)*4+3];
  assert.equal(a(30,25),0);assert.equal(a(8,8),0);assert.ok(a(15,20)>180);assert.ok(a(66,35)>180);assert.ok(a(25,40)>180);
});

test('thin neutral ink survives default edge contraction without fabric tint',()=>{
  const image=fixture(),result=isolatePrint(image,{x:0,y:0,width:80,height:50},28);
  assert.equal(result.method,'light-ink');assert.ok(result.data[(20*80+15)*4+3]>180);
  const rgb=[...result.data.subarray((20*80+15)*4,(20*80+15)*4+3)];
  assert.ok(Math.min(...rgb)>200);assert.equal(result.data[(25*80+30)*4+3],0);
});

test('light ink removes distant fabric haze while coloured ink keeps its own channels',()=>{
  const image=fixture();for(let y=20;y<28;y++)for(let x=30;x<40;x++){const k=(y*80+x)*4;for(let c=0;c<3;c++)image.data[k+c]+=22;}
  const cleaned=isolatePrint(image,{x:0,y:0,width:80,height:50},28);
  assert.equal(cleaned.data[(24*80+34)*4+3],0);
  const coloured=fixture();for(let k=0;k<80*50;k++)if(coloured.data[k*4]>200)coloured.data.set([20,210,240,255],k*4);
  const out=isolatePrint(coloured,{x:0,y:0,width:80,height:50},28,{contract:false});
  assert.equal(out.method,'colour');assert.ok(out.data[(20*80+15)*4+1]>150);assert.ok(out.data[(20*80+15)*4]<70);
});

test('failed enhancement cannot silently fall through to old low-resolution masking',async()=>{
  await assert.rejects(enhancePrintRegion(fixture(),{x:0,y:0,width:80,height:50},async()=>{throw Error('AI download failed');}),/AI download failed/);
  await assert.rejects(enhancePrintRegion(fixture(),{x:0,y:0,width:80,height:50},async image=>image),/2×/);
});
