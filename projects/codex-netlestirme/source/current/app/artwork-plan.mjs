import {spawn} from 'node:child_process';
import {readFile} from 'node:fs/promises';
import {join} from 'node:path';
import {createHash} from 'node:crypto';

export async function planArtwork({root,dir,config,signal,progress=()=>{}}){
  const settings=config.artworkUnderstanding;
  if(!settings?.modelRoot)throw Error('Tasarıma özel görsel analiz motoru henüz kurulmadı. Genel talimatla devam edilmedi.');
  signal?.throwIfAborted();progress({stage:'Tasarımın öğeleri ve kompozisyonu anlaşılıyor',done:0,total:1});
  const source=join(dir,'prepared.png'),output=join(dir,'artwork-plan.json');
  const child=spawn(config.python,[join(root,'artwork_plan.py'),'--input',source,'--output',output,'--model-root',settings.modelRoot,'--device',settings.device||'cpu'],{cwd:root,windowsHide:true,shell:false,stdio:['ignore','ignore','pipe']});
  let stderr='',timedOut=false;
  const stop=()=>{
    if(process.platform==='win32'){const killer=spawn('taskkill',['/PID',String(child.pid),'/T','/F'],{windowsHide:true,shell:false});killer.on('error',()=>child.kill());}
    else child.kill('SIGTERM');
  };
  const timer=setTimeout(()=>{timedOut=true;stop();},(settings.timeoutSeconds||240)*1000);
  signal?.addEventListener('abort',stop,{once:true});if(signal?.aborted)stop();
  child.stderr.on('data',b=>{stderr=(stderr+b).slice(-1500);});
  try{
    const code=await new Promise((resolve,reject)=>{child.once('error',reject);child.once('close',resolve);});
    signal?.throwIfAborted();if(timedOut)throw Error('Tasarım analizi süre sınırına ulaştı.');
    if(code!==0)throw Error('Tasarım analizi tamamlanamadı; genel talimata geçilmedi. '+stderr.slice(-350));
    const plan=JSON.parse(await readFile(output,'utf8'));
    const expected=createHash('sha256').update(await readFile(source)).digest('hex');
    if(plan.schema!==1||plan.source_sha256!==expected||typeof plan.instruction!=='string'||plan.instruction.length<80||plan.instruction.length>24000)throw Error('Tasarım analizi bu kaynakla doğrulanamadı.');
    if(plan.status!=='model_reviewed_not_independently_verified'||plan.review?.decision!=='supported')throw Error('Tasarım gözlemleri kaynakla kontrol edilemedi; yanlış talimatla üretim başlatılmadı.');
    progress({stage:'Tasarıma özel yeniden oluşturma talimatı hazır',done:1,total:1});
    return plan;
  }finally{clearTimeout(timer);signal?.removeEventListener('abort',stop);}
}
