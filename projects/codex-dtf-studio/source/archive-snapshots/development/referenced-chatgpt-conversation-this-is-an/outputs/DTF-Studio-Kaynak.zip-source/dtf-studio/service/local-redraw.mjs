import {spawn} from 'node:child_process';
import {mkdir,mkdtemp,readFile,writeFile,access,rm} from 'node:fs/promises';
import {resolve,join} from 'node:path';
import {setPriority,constants as osConstants} from 'node:os';
import sharp from 'sharp';

export const REDRAW_MODEL='FLUX.2-klein-4B-Q4_0';
export function localRedrawConfig(home=process.env.DTF_REDRAW_HOME){
  if(!home)throw new Error('Yerel AI motorunun klasörü henüz bağlanmadı.');
  const root=resolve(home);
  return {root,exe:join(root,'runtime-cpu','sd-cli.exe'),diffusion:join(root,'flux2-klein-4b-Q4_0.gguf'),text:join(root,'qwen3-4b-Q4_K_M.gguf'),vae:join(root,'flux2-vae.safetensors'),jobs:join(root,'jobs'),width:512,timeoutMs:15*60000};
}
export async function redrawHealth(config){
  try{await Promise.all([config.exe,config.diffusion,config.text,config.vae].map(p=>access(p)));return {available:true,model:REDRAW_MODEL,feePerCall:0};}
  catch{return {available:false,model:REDRAW_MODEL,feePerCall:0};}
}
export function redrawPrompt(text=''){
  if(typeof text!=='string'||text.length>300)throw new Error('Yazı notu en fazla 300 karakter olabilir.');
  const lettering=text.trim()?` Preserve this exact lettering: ${JSON.stringify(text.trim())}.`:' Preserve any existing lettering; do not add new words.';
  return 'Recreate ONLY the printed artwork in the reference as crisp, clean, high-resolution standalone print-ready graphic art. Preserve its composition, letter shapes, illustration, colours, shading and complete layout. Restore sharp edges and clear small details.'+lettering+' Keep the complete artwork fully visible and centred with a modest empty margin. Use a uniform pure solid magenta background (#FF00FF) for later background removal, including empty spaces between and inside letters. Magenta is only the removable backdrop, not part of the artwork. No shirt, fabric, person, mockup, photo texture or additional ornaments. This is faithful graphic reconstruction, not a new design.';
}
export async function validateRedrawInput(bytes,text=''){
  if(!(bytes instanceof Uint8Array)||bytes.length<16||bytes.length>3*1024*1024)throw new Error('AI girdisi en fazla 3 MB görsel olabilir.');
  redrawPrompt(text);
  const meta=await sharp(bytes,{limitInputPixels:4e6}).metadata();
  if(!['png','jpeg','webp'].includes(meta.format)||!meta.width||!meta.height||meta.width<16||meta.height<16||meta.width*meta.height>4e6)throw new Error('AI için 16 pikselden büyük ve en fazla 4 megapiksel bir tasarım alanı seçin.');
  if(Math.max(meta.width/meta.height,meta.height/meta.width)>4)throw new Error('Çok dar tasarım alanını çevresinde biraz boşluk bırakarak genişletin.');
  return meta;
}
// Internal worker adapter: no server, inbound port, API charge or shell command.
// All file paths come from local configuration and an internally created job dir.
export async function redrawLocally(bytes,{text='',signal,progress=()=>{}}={},config=localRedrawConfig()){
  const meta=await validateRedrawInput(bytes,text);
  if(!(await redrawHealth(config)).available)throw new Error('Yerel AI model dosyaları hazır değil.');
  signal?.throwIfAborted();await mkdir(config.jobs,{recursive:true});const dir=await mkdtemp(join(config.jobs,'job-'));
  try{
    const input=join(dir,'reference.png'),output=join(dir,'result.png');
    await sharp(bytes,{limitInputPixels:4e6}).rotate().resize({width:768,height:768,fit:'inside',withoutEnlargement:true}).flatten({background:'#ffffff'}).png().toFile(input);
    const aspect=meta.width/meta.height,max=config.width||512,width=aspect>=1?max:Math.max(128,Math.round(max*aspect/16)*16),height=aspect>=1?Math.max(128,Math.round(max/aspect/16)*16):max;
    const args=['--backend','cpu','--diffusion-model',config.diffusion,'--llm',config.text,'--vae',config.vae,'--vae-format','flux2','-r',input,'-p',redrawPrompt(text),'--cfg-scale','1.0','--steps','4','--sampling-method','euler','--seed','42','--width',String(width),'--height',String(height),'--threads','8','--diffusion-fa','--vae-tiling','-o',output];
    progress('Ücretsiz yerel AI tasarımı yeniden oluşturuyor…');
    await new Promise((resolveDone,reject)=>{
      let finished=false,last='',timer;const child=spawn(config.exe,args,{windowsHide:true,shell:false,stdio:['ignore','pipe','pipe']});
      child.on('spawn',()=>{try{setPriority(child.pid,osConstants.priority.PRIORITY_BELOW_NORMAL);}catch{}});
      const end=error=>{if(finished)return;finished=true;clearTimeout(timer);signal?.removeEventListener('abort',abort);error?reject(error):resolveDone();};
      const abort=()=>{child.kill();end(new DOMException('AI işlemi iptal edildi.','AbortError'));};
      const consume=chunk=>{last=(last+chunk.toString()).slice(-3000);for(const line of chunk.toString().split(/[\r\n]/)){const step=line.match(/([1-4])\/4\b/);if(step)progress(`AI yeniden oluşturma: ${step[1]}/4`);}};
      child.stdout.on('data',consume);child.stderr.on('data',consume);child.on('error',e=>end(e));child.on('exit',code=>end(code===0?null:new Error('Yerel AI tamamlanamadı: '+last.split(/[\r\n]/).filter(Boolean).slice(-2).join(' ').slice(0,240))));
      timer=setTimeout(()=>{child.kill();end(new Error('Yerel AI süre sınırına ulaştı. Orijinali koru modunu kullanabilirsiniz.'));},config.timeoutMs||15*60000);
      signal?.addEventListener('abort',abort,{once:true});if(signal?.aborted)abort();
    });
    const result=await readFile(output),check=await sharp(result,{limitInputPixels:2e6}).metadata();
    if(check.width!==width||check.height!==height)throw new Error('AI sonucu beklenen boyutla eşleşmedi.');
    return {png:result,width,height,sourceWidth:meta.width,sourceHeight:meta.height,model:REDRAW_MODEL,background:'#FF00FF',reconstructed:true};
  }finally{await rm(dir,{recursive:true,force:true});}
}
