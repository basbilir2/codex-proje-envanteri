import {guidedAlpha,cleanMatte,contractAlpha1px} from './matte.mjs';
let model,processor,RawImage;
export async function removeBackground(canvas,progress=()=>{},{contract=true}={}){
  const lib=await import('https://cdn.jsdelivr.net/npm/@huggingface/transformers@3.8.1');
  RawImage=lib.RawImage;
  if(!model||!processor){
    const progress_callback=p=>{if(p.status==='progress')progress(`AI modeli indiriliyor: %${Math.round(p.progress||0)}`);};
    const revision='962e67969ec6acec9c19fab76acee4f5e22e990c';
    model=await lib.AutoModel.from_pretrained('studioludens/birefnet-lite-512',{revision,dtype:'fp32',device:'wasm',progress_callback});
    processor=await lib.AutoProcessor.from_pretrained('studioludens/birefnet-lite-512',{revision});
  }
  progress('Arka plan hesaplanıyor…');
  const image=RawImage.fromCanvas(canvas),{pixel_values}=await processor(image);
  const output=await model({input_image:pixel_values});
  const logits=output.logits||output.output_image||Object.values(output)[0];
  const mask=RawImage.fromTensor(logits[0].sigmoid().mul(255).to('uint8'));
  progress('İnce kenarlar kaynak çözünürlükte işleniyor…');
  const guide=await image.resize(mask.width,mask.height);
  const result=document.createElement('canvas');result.width=canvas.width;result.height=canvas.height;
  const ctx=result.getContext('2d');ctx.drawImage(canvas,0,0);const pixels=ctx.getImageData(0,0,canvas.width,canvas.height);
  const cleaned=cleanMatte(guidedAlpha(pixels,mask,guide),1),refined=contract?contractAlpha1px(cleaned):cleaned;
  if(!refined.data.some((v,i)=>i%4===3&&v>20))throw new Error('AI görünür bir tasarım ayıramadı. Baskı alanını seçerek kumaş temizleme veya silgi kullanın.');
  ctx.putImageData(new ImageData(refined.data,canvas.width,canvas.height),0,0);return result;
}
