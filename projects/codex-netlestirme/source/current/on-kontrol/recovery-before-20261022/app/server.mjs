import http from 'node:http';
import {readFile,writeFile,mkdir,stat} from 'node:fs/promises';
import {createReadStream} from 'node:fs';
import {fileURLToPath} from 'node:url';
import {join,resolve,extname} from 'node:path';
import {randomUUID,randomBytes} from 'node:crypto';
import {spawn} from 'node:child_process';
import sharp from 'sharp';

const ROOT=fileURLToPath(new URL('.',import.meta.url));
const PORT=17861,ORIGIN=`http://127.0.0.1:${PORT}`,TOKEN=randomBytes(24).toString('hex');
const jobs=new Map();let active=null;
const config=JSON.parse(await readFile(join(ROOT,'runtime-config.json'),'utf8'));
const json=(res,code,value)=>{res.writeHead(code,{'Content-Type':'application/json; charset=utf-8','Cache-Control':'no-store'});res.end(JSON.stringify(value));};
async function body(req,max=25*1024*1024){const parts=[];let size=0;for await(const part of req){size+=part.length;if(size>max)throw Error('Görsel en fazla 25 MB olabilir.');parts.push(part);}return Buffer.concat(parts);}
async function saveJob(job){await writeFile(join(ROOT,'jobs',job.id,'job.json'),JSON.stringify(job,null,2));}
function endJob(job,status,error){job.status=status;if(error)job.error=error;job.finishedAt=new Date().toISOString();if(active?.id===job.id)active=null;return saveJob(job);}
async function enhance(job){
  const dir=join(ROOT,'jobs',job.id),width=job.width,height=job.height;
  const args=[join(ROOT,'qwen_worker.py'),'--exe',join(ROOT,config.runtime||'runtime/sd-cli.exe'),'--input',join(dir,'input.png'),'--output',join(dir,'enhanced.png'),'--width',String(width),'--height',String(height),'--task',job.task,'--timeout','600'];
  if(config.backend==='cpu')args.push('--cpu');
  if(config.lightning===true)args.push('--lightning');
  if(config.backend!=='cpu')args.push('--bounded-vram');
  const child=spawn(config.python,args,{cwd:ROOT,windowsHide:true,shell:false,stdio:['ignore','pipe','pipe']});
  let error='',pending='';
  child.stdout.on('data',chunk=>{
    pending+=chunk.toString();const lines=pending.split('\n');pending=lines.pop();
    for(const line of lines){try{const progress=JSON.parse(line);job.progress=progress;}catch{}}
  });
  child.stderr.on('data',b=>{error=(error+b).slice(-2500);});active={id:job.id,child};
  child.on('error',async e=>{await endJob(job,'failed',e.message);});
  child.on('close',async code=>{
    if(job.status==='cancelled')return;
    try{
      if(code!==0){
        let details='';try{details=(await readFile(join(dir,'enhanced.log'),'utf8')).slice(-6000);}catch{}
        if(/ErrorOutOfDeviceMemory|memory allocation.*failed|out of memory/i.test(details))throw Error('AI için grafik belleği yetersiz kaldı. Önceki sonuç korundu; daha küçük bir alanla deneyebilirsiniz.');
        if(/Timeout|süre sınırı/.test(error))throw Error('AI işlemi bu bilgisayarda süre sınırına ulaştı. Önceki sonuç korundu.');
        throw Error('AI yeniden oluşturma tamamlanamadı. Önceki görüntü korundu; işlem günlüğü kaydedildi.');
      }
      const meta=await sharp(join(dir,'enhanced.png')).metadata();
      if(meta.width!==width||meta.height!==height)throw Error('Çıktı boyutu doğrulanamadı.');
      job.output=`/result/${job.id}/enhanced.png`;job.progress={stage:'Hazır',done:1,total:1};await endJob(job,'completed');
    }catch(e){await endJob(job,'failed',e.message);}
  });
}
const mime={'.html':'text/html; charset=utf-8','.js':'text/javascript','.mjs':'text/javascript','.css':'text/css','.wasm':'application/wasm','.json':'application/json','.png':'image/png','.onnx':'application/octet-stream'};
async function file(res,path){const info=await stat(path);res.writeHead(200,{'Content-Type':mime[extname(path)]||'application/octet-stream','Content-Length':info.size,'X-Content-Type-Options':'nosniff','Cache-Control':path.startsWith(join(ROOT,'web'))?'no-store':'no-cache'});createReadStream(path).pipe(res);}
const server=http.createServer(async(req,res)=>{
  try{
    if(req.headers.host!==`127.0.0.1:${PORT}`)return json(res,403,{error:'Geçersiz adres.'});
    const url=new URL(req.url,ORIGIN),path=url.pathname;
    if(req.method==='POST'&&(req.headers.origin!==ORIGIN||req.headers['x-app-token']!==TOKEN))return json(res,403,{error:'Geçersiz istek.'});
    if(req.method==='GET'&&path==='/'){let html=await readFile(join(ROOT,'web','index.html'),'utf8');res.writeHead(200,{'Content-Type':'text/html; charset=utf-8','Cache-Control':'no-store'});return res.end(html.replace('__APP_TOKEN__',TOKEN));}
    if(req.method==='GET'&&path==='/api/status')return json(res,200,{active:active?.id||null,qualityAccepted:false,enhancementReady:config.enhancementReady===true,trialEnabled:config.trialEnabled===true});
    if(req.method==='POST'&&path==='/api/enhance'){
      const mode=url.searchParams.get('mode')||'ai';
      if(!['quick','ai'].includes(mode))throw Error('Geçersiz işlem.');
      const task=url.searchParams.get('task')||'restore-image';
      if(!['restore-image','extract-design'].includes(task))throw Error('Geçersiz yeniden oluşturma işlemi.');
      if(mode==='ai'&&config.enhancementReady!==true&&config.trialEnabled!==true)return json(res,409,{error:'AI denemesi açık değil.'});
      if(active)return json(res,409,{error:'Devam eden işlemin bitmesini bekleyin.'});
      // Reserve before reading asynchronous upload to prevent simultaneous heavy jobs.
      active={id:'upload'};
      try{
        const input=await body(req),image=sharp(input,{limitInputPixels:16000000}),meta=await image.metadata();
        if(!['png','jpeg','webp'].includes(meta.format)||Math.min(meta.width,meta.height)<32)throw Error('PNG, JPEG veya WebP görsel yükleyin.');
        const id=randomUUID(),dir=join(ROOT,'jobs',id);await mkdir(dir,{recursive:true});
        await writeFile(join(dir,'original.'+meta.format),input);
        const normalized=await image.rotate().png().toBuffer();
        const oriented=await sharp(normalized).metadata();let region=null,selected=normalized;
        if(req.headers['x-region']){
          region=JSON.parse(req.headers['x-region']);
          const {left,top,width,height}=region;
          if(![left,top,width,height].every(Number.isInteger)||left<0||top<0||width<16||height<16||left+width>oriented.width||top+height>oriented.height)throw Error('Tasarım alanı görsel sınırları içinde ve en az 16 × 16 piksel olmalı.');
          selected=await sharp(normalized).extract({left,top,width,height}).png().toBuffer();
        }
        const area=await sharp(selected).metadata();
        let width=area.width,height=area.height;
        if(mode==='ai'){
          const scale=Math.min(1,512/Math.max(width,height));
          width=Math.max(128,Math.round(width*scale/16)*16);height=Math.max(128,Math.round(height*scale/16)*16);
          await sharp(selected).flatten({background:'#fff'}).resize(width,height,{fit:'contain',background:'#fff'}).png().toFile(join(dir,'input.png'));
        }else await writeFile(join(dir,'input.png'),selected);
        const job={id,status:'running',mode,task,createdAt:new Date().toISOString(),width,height,sourceWidth:oriented.width,sourceHeight:oriented.height,region,progress:{stage:'Girdi hazır',done:1,total:3}};
        jobs.set(id,job);await saveJob(job);
        if(mode==='quick'){
          active={id};
          // Fast, same-size finishing. This is explicitly not generative reconstruction.
          (async()=>{try{
            job.progress={stage:'Hızlı netleştirme',done:1,total:3};
            await sharp(selected).sharpen({sigma:0.65,m1:0.45,m2:1.5,x1:2,y2:6,y3:6}).png().toFile(join(dir,'enhanced.pending.png'));
            job.progress={stage:'Çıktı doğrulanıyor',done:2,total:3};
            const check=await sharp(join(dir,'enhanced.pending.png')).metadata();
            if(check.width!==width||check.height!==height)throw Error('Çıktı boyutu doğrulanamadı.');
            const {rename}=await import('node:fs/promises');await rename(join(dir,'enhanced.pending.png'),join(dir,'enhanced.png'));
            job.output=`/result/${id}/enhanced.png`;job.progress={stage:'Hazır',done:3,total:3};await endJob(job,'completed');
          }catch(e){await endJob(job,'failed',e.message);}})();
        }else await enhance(job);
        return json(res,202,job);
      }catch(e){active=null;throw e;}
    }
    const jobMatch=path.match(/^\/api\/jobs\/([0-9a-f-]{36})$/);
    if(req.method==='GET'&&jobMatch){const job=jobs.get(jobMatch[1]);return json(res,job?200:404,job||{error:'İş bulunamadı.'});}
    if(req.method==='POST'&&path==='/api/cancel'){
      const job=jobs.get(active?.id);if(!job)return json(res,200,{cancelled:false});
      const child=active.child;if(!child)return json(res,409,{error:'Kısa işlem tamamlanmak üzere.'});job.status='cancelled';
      if(process.platform==='win32')spawn('taskkill',['/PID',String(child.pid),'/T','/F'],{windowsHide:true,shell:false});else child.kill('SIGTERM');
      await endJob(job,'cancelled');return json(res,200,{cancelled:true});
    }
    const transparent=path.match(/^\/api\/(?:transparent|edited)\/([0-9a-f-]{36})$/);
    if(req.method==='POST'&&transparent){
      const job=jobs.get(transparent[1]);if(!job||job.status!=='completed')return json(res,409,{error:'Önce görseli iyileştirin.'});
      const bytes=await body(req,100*1024*1024),meta=await sharp(bytes).metadata();
      if(meta.format!=='png'||!meta.width||!meta.height||meta.width*meta.height>24e6)throw Error('Düzenlenen çıktı doğrulanamadı.');
      const name=path.startsWith('/api/transparent/')?'transparent':'edited';
      if(name==='transparent'&&!meta.hasAlpha)throw Error('Şeffaf çıktı alpha içermeli.');
      const dest=join(ROOT,'jobs',job.id,name+'.png');await sharp(bytes).png().toFile(dest);job.editedWidth=meta.width;job.editedHeight=meta.height;await saveJob(job);
      return json(res,200,{output:`/result/${job.id}/${name}.png`});
    }
    const result=path.match(/^\/result\/([0-9a-f-]{36})\/(enhanced|transparent|edited)\.png$/);
    if(req.method==='GET'&&result)return await file(res,join(ROOT,'jobs',result[1],result[2]+'.png'));
    if(req.method==='GET'&&(path.startsWith('/web/')||path.startsWith('/vendor/')||path.startsWith('/background-model/'))){
      const base=path.startsWith('/background-model/')?join(ROOT,'background-model'):path.startsWith('/vendor/')?join(ROOT,'vendor'):join(ROOT,'web');
      const relative=decodeURIComponent(path.substring(path.indexOf('/',1)+1)),dest=resolve(base,relative);
      if(!dest.startsWith(base+ (process.platform==='win32'?'\\':'/')))return json(res,403,{error:'Geçersiz dosya.'});
      return await file(res,dest);
    }
    json(res,404,{error:'Bulunamadı.'});
  }catch(e){if(!res.headersSent)json(res,e.code==='ENOENT'?404:400,{error:e.code==='ENOENT'?'Gerekli dosya bulunamadı.':e.message});else res.destroy();}
});
server.listen(PORT,'127.0.0.1',()=>console.log(ORIGIN));
server.on('error',e=>{console.error(e.message);process.exitCode=1;});
