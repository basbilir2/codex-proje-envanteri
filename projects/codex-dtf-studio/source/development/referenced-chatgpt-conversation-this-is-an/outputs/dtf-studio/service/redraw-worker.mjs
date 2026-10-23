import {readFile,mkdir,open,unlink,appendFile} from 'node:fs/promises';import {resolve,join} from 'node:path';import sharp from 'sharp';
import {localRedrawConfig,redrawHealth,redrawLocally} from './local-redraw.mjs';
const config=localRedrawConfig(),privateDir=resolve(config.root,'private');await mkdir(privateDir,{recursive:true});
const credentials=JSON.parse(await readFile(join(privateDir,'wix-worker.json'),'utf8'));
const endpoint='https://izmirdedtf.wixsite.com/dtf-studio/_functions/dtfAi';
if(typeof credentials.workerKey!=='string'||credentials.workerKey.length<32)throw new Error('Wix işçi anahtarı eksik.');
if(!(await redrawHealth(config)).available)throw new Error('Yerel AI model dosyaları eksik.');
let lock;try{lock=await open(join(privateDir,'worker.lock'),'wx');await lock.writeFile(String(process.pid));}catch{throw new Error('Yerel AI işçisi zaten açık veya önceki oturum kapanmamış. worker.lock dosyasını kontrol edin.');}
const log=s=>appendFile(join(privateDir,'worker.log'),new Date().toISOString()+' '+s+'\n','utf8');
const api=async body=>{const res=await fetch(endpoint,{method:'POST',headers:{'Content-Type':'application/json',Authorization:'Bearer '+credentials.workerKey},body:JSON.stringify(body),signal:AbortSignal.timeout(45000)});const data=await res.json();if(!res.ok)throw new Error(data.error||'Wix bağlantısı kurulamadı.');return data;};
let stop=false,active;const quit=()=>{stop=true;active?.abort();};process.on('SIGINT',quit);process.on('SIGTERM',quit);
try{await log('İşçi başladı; dışarıdan bağlantı kabul edilmez.');while(!stop){
  try{const job=await api({op:'claim'});if(!job.id){await new Promise(r=>setTimeout(r,15000));continue;}await log('İş alındı '+job.id.slice(0,8));
    active=new AbortController();let heartbeatBusy=false;const beat=setInterval(async()=>{if(heartbeatBusy)return;heartbeatBusy=true;try{const state=await api({op:'heartbeat',id:job.id,claim:job.claim});if(state.state!=='running')active?.abort();}catch{}finally{heartbeatBusy=false;}},25000);
    try{const bytes=Buffer.from(job.image.split(',')[1],'base64'),output=await redrawLocally(bytes,{text:job.text,signal:active.signal},config);let result=await sharp(output.png).webp({lossless:true}).toBuffer();if(result.length>280000)result=await sharp(output.png).webp({quality:98,effort:5}).toBuffer();if(result.length>280000)throw new Error('AI sonucu aktarım sınırını aşıyor.');await api({op:'finish',id:job.id,claim:job.claim,image:'data:image/webp;base64,'+result.toString('base64')});await log('İş tamamlandı '+job.id.slice(0,8));}
    catch(e){await log('İş başarısız '+job.id.slice(0,8)+' '+e.name);if(!stop)await api({op:'finish',id:job.id,claim:job.claim,error:true});}
    finally{clearInterval(beat);active=null;}
  }catch(e){await log('Bağlantı bekleniyor '+e.name);if(!stop)await new Promise(r=>setTimeout(r,30000));}
}}finally{await lock.close();await unlink(join(privateDir,'worker.lock'));await log('İşçi durdu.');}
