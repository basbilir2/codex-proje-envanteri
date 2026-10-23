let ready;
async function load(progress){
  if(!ready)ready=(async()=>{
    progress('Ücretsiz AI büyütme motoru indiriliyor…');
    const tf=await import('https://esm.sh/@tensorflow/tfjs@4.11.0');
    const [{default:Upscaler},{default:model}]=await Promise.all([
      import('https://esm.sh/upscaler@1.0.0?deps=@tensorflow/tfjs@4.11.0'),
      import('https://esm.sh/@upscalerjs/esrgan-slim@1.0.0/2x')
    ]);
    let accelerated=false;
    try{accelerated=await tf.setBackend('webgl');}catch{}
    if(!accelerated){
      try{const wasm=await import('https://esm.sh/@tensorflow/tfjs-backend-wasm@4.11.0?deps=@tensorflow/tfjs-core@4.11.0');wasm.setWasmPaths('https://cdn.jsdelivr.net/npm/@tensorflow/tfjs-backend-wasm@4.11.0/dist/');accelerated=await tf.setBackend('wasm');}catch{}
      if(!accelerated)await tf.setBackend('cpu');
    }
    await tf.ready();return {tf,upscaler:new Upscaler({model})};
  })().catch(e=>{ready=null;throw e;});
  return ready;
}

export async function enhanceCanvas(canvas,progress=()=>{},{detail=false}={}){
  if(canvas.width*canvas.height*4>(detail?12e6:24e6))throw new Error(detail?'2. kademe en fazla 12 megapiksel çıktı hazırlayabilir. Önce şeffaf boşlukları kırpın.':'AI 2× işlemi 24 megapiksel çıktı sınırında çalışır. Önce şeffaf boşlukları kırpın.');
  const {tf,upscaler}=await load(progress),w=canvas.width,h=canvas.height;
  const pixels=canvas.getContext('2d').getImageData(0,0,w,h),rgb=new Uint8Array(w*h*3),distance=new Uint8Array(w*h).fill(255),queue=new Int32Array(w*h);let head=0,tail=0;
  for(let k=0;k<w*h;k++){const a=pixels.data[k*4+3];for(let c=0;c<3;c++)rgb[k*3+c]=pixels.data[k*4+c];if(a>32)distance[k]=0;}
  for(let k=0;k<w*h;k++)if(distance[k]===0){const x=k%w;for(const q of [x>0?k-1:-1,x<w-1?k+1:-1,k>=w?k-w:-1,k<w*(h-1)?k+w:-1])if(q>=0&&distance[q]===255){queue[tail++]=k;break;}}
  // Extend edge colours beneath transparency so the network does not introduce a black halo.
  while(head<tail){const k=queue[head++],x=k%w;if(distance[k]>=8)continue;for(const q of [x>0?k-1:-1,x<w-1?k+1:-1,k>=w?k-w:-1,k<w*(h-1)?k+w:-1])if(q>=0&&distance[q]===255){distance[q]=distance[k]+1;for(let c=0;c<3;c++)rgb[q*3+c]=rgb[k*3+c];queue[tail++]=q;}}
  let input,output;
  try{
    input=tf.tensor3d(rgb,[h,w,3],'int32');progress('AI ayrıntıları ve kenarları iyileştiriyor…');
    output=await upscaler.upscale(input,{output:'tensor',patchSize:64,padding:8,awaitNextFrame:true,progress:p=>progress(`AI iyileştirme: %${Math.round(p*100)}`)});
    const values=await output.data(),out=document.createElement('canvas');out.width=w*2;out.height=h*2;
    const ctx=out.getContext('2d');ctx.imageSmoothingEnabled=true;ctx.imageSmoothingQuality='high';ctx.drawImage(canvas,0,0,out.width,out.height);
    const rgba=ctx.getImageData(0,0,out.width,out.height);for(let k=0;k<out.width*out.height;k++)for(let c=0;c<3;c++)rgba.data[k*4+c]=rgba.data[k*4+3]?Math.max(0,Math.min(255,Math.round(values[k*3+c]))):0;
    if(detail){progress('İnce çizgiler ve kenarlar netleştiriliyor…');const {refineDetails}=await import('./detail.mjs');const refined=refineDetails(rgba);ctx.putImageData(new ImageData(refined.data,out.width,out.height),0,0);}
    else ctx.putImageData(rgba,0,0);
    return out;
  }finally{input?.dispose();output?.dispose();}
}
