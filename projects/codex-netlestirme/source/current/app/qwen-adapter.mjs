import {spawn} from 'node:child_process';
import {readFile} from 'node:fs/promises';
import {join} from 'node:path';
import {planArtwork} from './artwork-plan.mjs';

export function qwenAdapter(root,config){return {async run({dir,task,width,height,signal,progress}){
  signal?.throwIfAborted();
  const artworkPlan=task==='extract-design'?await planArtwork({root,dir,config,signal,progress:p=>progress({stage:p.stage,done:p.done?10:0,total:100})}):null;
  const output=join(dir,'reconstructed.png');
  const args=[join(root,'qwen_worker.py'),'--exe',join(root,config.runtime||'runtime/sd-cli.exe'),'--input',join(dir,'input.png'),'--output',output,'--width',String(width),'--height',String(height),'--task',task,'--timeout',String(config.timeoutSeconds||600)];
  if(artworkPlan)args.push('--instruction-file',join(dir,'artwork-plan.json'));
  if(config.backend==='cpu')args.push('--cpu');
  if(config.lightning===true)args.push('--lightning');
  if(config.backend!=='cpu')args.push('--bounded-vram');
  const child=spawn(config.python,args,{cwd:root,windowsHide:true,shell:false,stdio:['ignore','pipe','pipe']});
  let stderr='',pending='',progressError,stopping;
  const stop=()=>{
    if(stopping)return;
    if(process.platform==='win32')stopping=new Promise(resolve=>{const killer=spawn('taskkill',['/PID',String(child.pid),'/T','/F'],{windowsHide:true,shell:false});killer.on('error',()=>{child.kill();resolve();});killer.on('close',resolve);});
    else {child.kill('SIGTERM');stopping=Promise.resolve();}
  };
  signal?.addEventListener('abort',stop,{once:true});if(signal?.aborted)stop();
  child.stdout.on('data',chunk=>{pending+=chunk.toString();const lines=pending.split('\n');pending=lines.pop();for(const line of lines){let p;try{p=JSON.parse(line);}catch{continue;}try{progress(p);}catch(e){progressError=e;stop();}}});
  child.stderr.on('data',b=>{stderr=(stderr+b).slice(-3000);});
  try{
    const code=await new Promise((resolve,reject)=>{child.once('error',reject);child.once('close',resolve);});
    if(stopping)await stopping;
    signal?.throwIfAborted();if(progressError)throw progressError;
    if(code!==0){
      let log='';try{log=(await readFile(join(dir,'reconstructed.log'),'utf8')).slice(-6000);}catch{}
      if(/ErrorOutOfDeviceMemory|memory allocation.*failed|out of memory/i.test(log))throw Error('AI için grafik belleği yetersiz. Kaynak ve önceki sonuç korundu.');
      if(/Timeout|süre sınırı/.test(stderr))throw Error('AI bu bilgisayarda süre sınırına ulaştı. Kaynak ve önceki sonuç korundu.');
      throw Error('Üretken motor tamamlanamadı. İşlem günlüğü kaydedildi; filtre ile sonuç değiştirilmedi.');
    }
    const record=JSON.parse(await readFile(join(dir,'reconstructed.json'),'utf8'));
    if(record.status!=='completed')throw Error('Motor işlem kaydı tamamlanmış değil.');
    return {kind:'generative-reconstruction',...record,understanding:artworkPlan?{model:artworkPlan.model,source_sha256:artworkPlan.source_sha256,observation:artworkPlan.observation,status:artworkPlan.status}:null};
  }finally{signal?.removeEventListener('abort',stop);}
}};}
