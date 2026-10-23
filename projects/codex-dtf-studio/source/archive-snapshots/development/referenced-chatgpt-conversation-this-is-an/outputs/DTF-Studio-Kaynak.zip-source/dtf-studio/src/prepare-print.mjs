import {isolatePrint} from './photo-extract.mjs';

export function cropPrintRegion(image,region){
  const x=Math.max(0,Math.min(image.width-1,Math.floor(region.x))),y=Math.max(0,Math.min(image.height-1,Math.floor(region.y)));
  const width=Math.max(1,Math.min(image.width-x,Math.ceil(region.width))),height=Math.max(1,Math.min(image.height-y,Math.ceil(region.height)));
  const data=new Uint8ClampedArray(width*height*4);
  for(let row=0;row<height;row++)data.set(image.data.subarray(((y+row)*image.width+x)*4,((y+row)*image.width+x+width)*4),row*width*4);
  return {data,width,height,source:{x,y,width,height}};
}

export async function enhancePrintRegion(image,region,enhance,progress=()=>{}){
  const {data,width,height,source}=cropPrintRegion(image,region);
  progress('1/2 · Baskı alanı önce AI ile 2× büyütülüyor…');
  const enhanced=await enhance({data,width,height},progress);
  if(enhanced.width!==width*2||enhanced.height!==height*2)throw new Error('AI 2× büyütme tamamlanamadı. Tekrar deneyin.');
  return {image:enhanced,source,scale:2};
}

export function isolateEnhancedPrint(prepared,tolerance,options){
  const image=prepared.image;
  return {...isolatePrint(image,{x:0,y:0,width:image.width,height:image.height},tolerance,options),preparedSource:prepared.source,scale:prepared.scale};
}
