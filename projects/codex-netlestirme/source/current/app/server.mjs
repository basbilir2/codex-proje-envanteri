import http from 'node:http';
import {readFile,writeFile,mkdir,stat,rename} from 'node:fs/promises';
import {createReadStream} from 'node:fs';
import {fileURLToPath} from 'node:url';
import {join,resolve,extname} from 'node:path';
import {randomUUID,randomBytes} from 'node:crypto';
import sharp from 'sharp';
import {TASKS,inspectSource,recover,exportPNG,atomicJSON} from './pipeline.mjs';
import {qwenAdapter} from './qwen-adapter.mjs';
const ROOT=fileURLToPath(new URL('.',import.meta.url));
const PORT=Number(process.env.RECOVERY_PORT||17861),ORIGIN=`http://127.0.0.1:${PORT}`,TOKEN=randomBytes(24).toString('hex');
const jobs=new Map(),editing=new Set();let active=null;
const config=JSON.parse(await readFile(join(ROOT,'runtime-config.json'),'utf8'));
const engine=qwenAdapter(ROOT,config);
const json=(res,code,value)=>{res.writeHead(code,{'Content-Type':'application/json; charset=utf-8','Cache-Control':'no-store'});res.end(JSON.stringify(value));};
async function body(req,max=25*1024*1024){const parts=[];let size=0;for await(const part of req){size+=part.length;if(size>max)throw Error('Dosya boyutu sınırı aşıldı.');parts.push(part);}return Buffer.concat(parts);}
const dirOf=id=>join(ROOT,'jobs',id);
async function saveJob(job){await atomicJSON(join(dirOf(job.id),'job.json'),job);}
async function getJob(id){
  if(jobs.has(id))return jobs.get(id);
  try{const job=JSON.parse(await readFile(join(dirOf(id),'job.json'),'utf8'));
    if(job.status==='running'){job.status='failed';job.error='Önceki uygulama oturumu kesildi; çıktı kabul edilmedi.';await saveJob(job);}
    jobs.set(id,job);return job;
  }catch(e){if(e.code==='ENOENT')return null;throw e;}
}
async function runJob(job,input,controller){
  try{
    const report=await recover({dir:dirOf(job.id),...input,task:job.task,region:job.region,quad:job.quad,engine,maxEdge:config.maxModelEdge||512,signal:controller.signal,progress:p=>{job.progress=p;}});
    job.width=report.output.width;job.height=report.output.height;job.output=`/result/${job.id}/enhanced.png`;job.report=`/report/${job.id}/recovery.json`;job.quality=report.quality;job.status='completed';
  }catch(e){job.status=controller.signal.aborted?'cancelled':'failed';job.error=job.status==='cancelled'?'İşlem iptal edildi.':e.message;}
  finally{job.finishedAt=new Date().toISOString();try{await saveJob(job);}finally{if(active?.id===job.id)active=null;}}
}
const mime={'.html':'text/html; charset=utf-8','.js':'text/javascript','.mjs':'text/javascript','.css':'text/css','.wasm':'application/wasm','.json':'application/json','.png':'image/png','.onnx':'application/octet-stream'};
async function file(res,path){const info=await stat(path);res.writeHead(200,{'Content-Type':mime[extname(path)]||'application/octet-stream','Content-Length':info.size,'X-Content-Type-Options':'nosniff','Cache-Control':path.startsWith(join(ROOT,'web'))?'no-store':'no-cache'});createReadStream(path).on('error',()=>res.destroy()).pipe(res);}
const server=http.createServer(async(req,res)=>{
  try{
    if(req.headers.host!==`127.0.0.1:${PORT}`)return json(res,403,{error:'Geçersiz adres.'});
    const url=new URL(req.url,ORIGIN),path=url.pathname;
    if(req.method==='POST'&&(req.headers.origin!==ORIGIN||req.headers['x-app-token']!==TOKEN))return json(res,403,{error:'Geçersiz istek.'});
    if(req.method==='GET'&&path==='/'){let html=await readFile(join(ROOT,'web','index.html'),'utf8');res.writeHead(200,{'Content-Type':'text/html; charset=utf-8','Cache-Control':'no-store'});return res.end(html.replace('__APP_TOKEN__',TOKEN));}
    if(req.method==='GET'&&path==='/api/status')return json(res,200,{active:active?.id||null,purpose:'artwork-reconstruction',qualityAccepted:false,enhancementReady:config.enhancementReady===true,trialEnabled:config.trialEnabled===true,tasks:TASKS,maxModelEdge:config.maxModelEdge||512});
    if(req.method==='POST'&&['/api/recover','/api/enhance'].includes(path)){
      if(url.searchParams.has('mode')&&url.searchParams.get('mode')!=='ai')throw Error('Keskinleştirme kurtarma motoru değildir; bu yol kaldırıldı.');
      const task=url.searchParams.get('task')||'extract-design';
      if(!TASKS.includes(task))throw Error('Geçersiz kurtarma işlemi.');
      if(config.enhancementReady!==true&&config.trialEnabled!==true)return json(res,409,{error:'Üretken motor denemesi açık değil.'});
      if(active)return json(res,409,{error:'Devam eden işlemin bitmesini bekleyin.'});
      const reservation={id:'upload'};active=reservation;
      try{
        const bytes=await body(req),input=await inspectSource(bytes);
        const region=req.headers['x-region']?JSON.parse(req.headers['x-region']):null,quad=req.headers['x-quad']?JSON.parse(req.headers['x-quad']):null;
        const id=randomUUID(),dir=dirOf(id);await mkdir(dir,{recursive:true});await writeFile(join(dir,'original.'+input.source.format),bytes);
        const job={id,status:'running',mode:'recovery',task,createdAt:new Date().toISOString(),sourceWidth:input.source.width,sourceHeight:input.source.height,region,quad,progress:{stage:'Kaynak alındı',done:0,total:100}};
        jobs.set(id,job);await saveJob(job);const controller=new AbortController();active={id,controller};
        runJob(job,input,controller).catch(error=>console.error('İş kaydı yazılamadı:',error.message));
        return json(res,202,job);
      }catch(e){if(active===reservation)active=null;throw e;}
    }
    const jobMatch=path.match(/^\/api\/jobs\/([0-9a-f-]{36})$/);
    if(req.method==='GET'&&jobMatch){const job=await getJob(jobMatch[1]);return json(res,job?200:404,job||{error:'İş bulunamadı.'});}
    if(req.method==='POST'&&path==='/api/cancel'){
      if(!active)return json(res,200,{cancelled:false});
      if(!active.controller)return json(res,409,{error:'Görsel alınıyor; kısa süre sonra iptal edebilirsiniz.'});
      active.controller.abort();return json(res,202,{cancelling:true});
    }
    const mutation=path.match(/^\/api\/(transparent|edited|export)\/([0-9a-f-]{36})$/);
    if(req.method==='POST'&&mutation){
      const [,name,id]=mutation,job=await getJob(id);
      if(!job||job.status!=='completed')return json(res,409,{error:'Önce kurtarma çıktısı oluşturun.'});
      if(editing.has(id))return json(res,409,{error:'Bu çıktı kaydediliyor; bitmesini bekleyin.'});editing.add(id);
      try{
        if(name==='export'){
          const options=JSON.parse((await body(req,4096)).toString());
          const report=await exportPNG({dir:dirOf(id),input:options.input,longEdge:options.longEdge,dpi:options.dpi});
          return json(res,200,{output:`/result/${id}/export.png`,report:`/report/${id}/export.json`,details:report});
        }
        const bytes=await body(req,100*1024*1024),meta=await sharp(bytes,{limitInputPixels:24e6}).metadata();
        if(meta.format!=='png'||!meta.width||!meta.height||meta.width*meta.height>24e6)throw Error('Düzenlenen çıktı doğrulanamadı.');
        if(name==='transparent'&&!meta.hasAlpha)throw Error('Şeffaf çıktı alpha içermeli.');
        const dest=join(dirOf(id),name+'.png');await sharp(bytes).png().toFile(dest+'.pending');await rename(dest+'.pending',dest);
        job.editedWidth=meta.width;job.editedHeight=meta.height;job.manualOrAuxiliaryEdits=true;await saveJob(job);
        return json(res,200,{output:`/result/${id}/${name}.png`});
      }finally{editing.delete(id);}
    }
    const result=path.match(/^\/result\/([0-9a-f-]{36})\/(enhanced|transparent|edited|export)\.png$/);
    if(req.method==='GET'&&result){const job=await getJob(result[1]);if(!job||job.status!=='completed')return json(res,404,{error:'Tamamlanmış çıktı bulunamadı.'});return await file(res,join(dirOf(result[1]),result[2]+'.png'));}
    const report=path.match(/^\/report\/([0-9a-f-]{36})\/(recovery|export)\.json$/);
    if(req.method==='GET'&&report)return await file(res,join(dirOf(report[1]),report[2]+'.json'));
    if(req.method==='GET'&&(path.startsWith('/web/')||path.startsWith('/vendor/')||path.startsWith('/background-model/'))){
      const base=path.startsWith('/background-model/')?join(ROOT,'background-model'):path.startsWith('/vendor/')?join(ROOT,'vendor'):join(ROOT,'web');
      const relative=decodeURIComponent(path.substring(path.indexOf('/',1)+1)),dest=resolve(base,relative);
      if(!dest.startsWith(base+(process.platform==='win32'?'\\':'/')))return json(res,403,{error:'Geçersiz dosya.'});return await file(res,dest);
    }
    json(res,404,{error:'Bulunamadı.'});
  }catch(e){if(!res.headersSent)json(res,e.code==='ENOENT'?404:400,{error:e.code==='ENOENT'?'Gerekli dosya bulunamadı.':e.message});else res.destroy();}
});
server.listen(PORT,'127.0.0.1',()=>console.log(ORIGIN));
server.on('error',e=>{console.error(e.message);process.exitCode=1;});
