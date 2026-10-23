import {guidedAlpha,cleanMatte,contractAlpha1px,refineMaskEdges} from './matte.mjs';
let ready;
async function load(progress){
  if(!ready)ready=(async()=>{
    const lib=await import('/vendor/transformers.min.js');
    lib.env.allowRemoteModels=false;
    lib.env.allowLocalModels=true;
    lib.env.localModelPath='/background-model/';
    lib.env.backends.onnx.wasm.wasmPaths='/vendor/';
    lib.env.backends.onnx.wasm.numThreads=1;
    const progress_callback=p=>{if(p.status==='progress')progress(`Arka plan modeli yükleniyor: %${Math.round(p.progress||0)}`);};
    const revision='962e67969ec6acec9c19fab76acee4f5e22e990c';
    const model=await lib.AutoModel.from_pretrained('studioludens/birefnet-lite-512',{revision,dtype:'fp32',device:'wasm',progress_callback});
    try{
      const processor=await lib.AutoProcessor.from_pretrained('studioludens/birefnet-lite-512',{revision});
      return {model,processor,RawImage:lib.RawImage};
    }catch(e){await model.dispose();throw e;}
  })().catch(e=>{ready=null;throw e;});
  return ready;
}
export async function removeBackground(canvas,progress=()=>{},{contract=true}={}){
  const {model,processor,RawImage}=await load(progress);
  progress('Arka plan hesaplanıyor…');
  const image=RawImage.fromCanvas(canvas),{pixel_values}=await processor(image);
  let output;
  try{
    output=await model({input_image:pixel_values});
    const logits=output.logits||output.output_image||Object.values(output)[0];
    const mask=RawImage.fromTensor(logits[0].sigmoid().mul(255).to('uint8'));
    progress('İnce kenarlar kaynak çözünürlükte işleniyor…');
    const guide=await image.resize(mask.width,mask.height);
    const result=document.createElement('canvas');result.width=canvas.width;result.height=canvas.height;
    const ctx=result.getContext('2d');ctx.drawImage(canvas,0,0);const pixels=ctx.getImageData(0,0,canvas.width,canvas.height);
    const cleaned=cleanMatte(refineMaskEdges(pixels,guidedAlpha(pixels,mask,guide)),1),refined=contract?contractAlpha1px(cleaned):cleaned;
    if(!refined.data.some((v,i)=>i%4===3&&v>20))throw new Error('Görseldeki konu arka plandan ayrılamadı. İyileştirilmiş görüntü korundu.');
    ctx.putImageData(new ImageData(refined.data,canvas.width,canvas.height),0,0);return result;
  }finally{
    pixel_values.dispose?.();
    for(const tensor of Object.values(output||{}))tensor?.dispose?.();
  }
}
