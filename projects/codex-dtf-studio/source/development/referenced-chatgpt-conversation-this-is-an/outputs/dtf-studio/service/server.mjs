import {createServer} from 'node:http';
import {readFile,writeFile,mkdir,rm,readdir,stat} from 'node:fs/promises';
import {resolve,join,extname} from 'node:path';
import {randomBytes,timingSafeEqual} from 'node:crypto';
import {renderSheet} from './render.mjs';
import {sign,verify,hash} from './security.mjs';
import {layout} from '../src/engine.mjs';
const demo=process.env.DTF_DEMO==='true',port=Number(process.env.PORT||4173);
const secret=process.env.DTF_SERVICE_SECRET||(demo?randomBytes(32).toString('hex'):'');
if(secret.length<32)throw new Error('DTF_SERVICE_SECRET en az 32 karakter olmalı. Yerel demo için DTF_DEMO=true kullanın.');
const base=process.env.DTF_PUBLIC_URL||(demo?`http://127.0.0.1:${port}`:'');
if(!demo&&!base.startsWith('https://'))throw new Error('Üretimde HTTPS DTF_PUBLIC_URL gerekir.');
const allowed=new Set((process.env.DTF_ALLOWED_ORIGINS||base).split(',').map(s=>s.trim()));
const storage=resolve(process.env.DTF_STORAGE_DIR||'../../work/dtf-private');await mkdir(storage,{recursive:true});
const pending=new Map(),rates=new Map();let rendering=false;
function admin(req){const value=req.headers.authorization?.replace(/^Bearer /,'')||'';return value.length===secret.length&&timingSafeEqual(Buffer.from(value),Buffer.from(secret));}
function send(res,status,data){res.writeHead(status,{'Content-Type':'application/json; charset=utf-8','Cache-Control':'no-store'});res.end(JSON.stringify(data));}
async function body(req,max=128*1024*1024){const chunks=[];let size=0;for await(const b of req){size+=b.length;if(size>max)throw new Error('Dosyalar toplam yükleme sınırını aşıyor.');chunks.push(b);}return JSON.parse(Buffer.concat(chunks).toString());}
function idCheck(id){if(!/^[a-f0-9]{64}$/.test(id))throw new Error('Geçersiz iş kimliği.');}
function paths(id){idCheck(id);return {meta:join(storage,id+'.json'),png:join(storage,id+'.png'),pdf:join(storage,id+'.pdf')};}
async function meta(id){try{return JSON.parse(await readFile(paths(id).meta,'utf8'));}catch(e){if(e.code==='ENOENT')return null;throw e;}}
async function authorize(data){
  idCheck(data.jobId);layout(data.manifest.designs,data.manifest.settings);
  if(!data.memberId||typeof data.memberId!=='string')throw new Error('Üye kimliği eksik.');
  const current=await meta(data.jobId),fingerprint=hash(data.manifest);
  if(current&&current.fingerprint!==fingerprint)throw new Error('Aynı iş kimliğiyle farklı dizgi gönderilemez.');
  const entry=pending.get(data.jobId);if(entry&&entry.fingerprint!==fingerprint)throw new Error('İş çakışması.');
  const rateKey=hash(data.memberId),rate=rates.get(rateKey)||{hour:Date.now(),count:0};
  if(Date.now()-rate.hour>3600000){rate.hour=Date.now();rate.count=0;}
  if(!entry&&!current&&rate.count>=10)throw new Error('Saatlik hazırlama sınırına ulaşıldı. Daha sonra tekrar deneyin.');
  if(!entry&&!current){rate.count++;rates.set(rateKey,rate);}
  const job={...data,fingerprint,exp:Date.now()+30*60000};pending.set(data.jobId,job);
  return {renderUrl:`${base}/api/jobs/${data.jobId}/render`,token:sign({jobId:data.jobId,fingerprint,kind:'upload',exp:job.exp},secret)};
}
async function finish(jobId){const m=await meta(jobId);if(!m||m.exp<Date.now())throw new Error('Hazır çıktı bulunamadı. Aynı işi tekrar hazırlayın.');const token=sign({jobId,kind:'download',exp:Math.min(m.exp,Date.now()+15*60000)},secret);return {pngUrl:`${base}/api/download/${jobId}.png?token=${encodeURIComponent(token)}`,pdfUrl:`${base}/api/download/${jobId}.pdf?token=${encodeURIComponent(token)}`};}
const server=createServer(async(req,res)=>{
  res.setHeader('X-Content-Type-Options','nosniff');res.setHeader('Referrer-Policy','no-referrer');
  const origin=req.headers.origin;
  if(origin&&!allowed.has(origin)){send(res,403,{error:'Bu site için erişim izni yok.'});return;}
  if(origin){res.setHeader('Access-Control-Allow-Origin',origin);res.setHeader('Vary','Origin');}
  if(req.method==='OPTIONS'){res.writeHead(204,{'Access-Control-Allow-Headers':'Content-Type, Authorization','Access-Control-Allow-Methods':'POST, GET, OPTIONS'});res.end();return;}
  const url=new URL(req.url,base);
  try{
    if(req.method==='GET'&&url.pathname==='/health'){send(res,200,{ok:true,demo});return;}
    if(req.method==='POST'&&url.pathname==='/internal/authorize'){
      if(!admin(req)){send(res,401,{error:'Yetki gerekli.'});return;}
      send(res,200,await authorize(await body(req,100000)));return;
    }
    if(req.method==='POST'&&url.pathname==='/api/demo/authorize'&&demo){const d=await body(req,100000);send(res,200,await authorize({...d,memberId:'local-demo',jobId:hash('local-demo:'+d.requestId)}));return;}
    if(req.method==='POST'&&url.pathname==='/api/demo/finish'&&demo){const d=await body(req,2000);send(res,200,await finish(hash('local-demo:'+d.requestId)));return;}
    const internal=url.pathname.match(/^\/internal\/jobs\/([a-f0-9]{64})\/(status|deliver)$/);
    if(internal){if(!admin(req)){send(res,401,{error:'Yetki gerekli.'});return;}send(res,200,internal[2]==='status'?{ready:Boolean((await meta(internal[1]))?.exp>Date.now())}:await finish(internal[1]));return;}
    const render=url.pathname.match(/^\/api\/jobs\/([a-f0-9]{64})\/render$/);
    if(render&&req.method==='POST'){
      const id=render[1],ticket=verify(req.headers.authorization?.replace(/^Bearer /,''),secret,'upload'),job=pending.get(id);
      if(ticket.jobId!==id||!job||ticket.fingerprint!==job.fingerprint)throw new Error('İş izni eşleşmiyor.');
      const current=await meta(id);if(current&&current.fingerprint===job.fingerprint&&current.exp>Date.now()){req.resume();send(res,200,{ready:true,jobId:id});return;}
      if(rendering){req.resume();send(res,429,{error:'Çıktı sunucusu meşgul. Biraz sonra aynı işi tekrar deneyin.'});return;}
      rendering=true;
      try{const {assets}=await body(req);const output=await renderSheet(job.manifest,assets);const p=paths(id);await writeFile(p.png,output.png);await writeFile(p.pdf,output.pdf);await writeFile(p.meta,JSON.stringify({fingerprint:job.fingerprint,exp:Date.now()+3600000}));send(res,200,{ready:true,jobId:id});}finally{rendering=false;}return;
    }
    const download=url.pathname.match(/^\/api\/download\/([a-f0-9]{64})\.(png|pdf)$/);
    if(download&&req.method==='GET'){
      const ticket=verify(url.searchParams.get('token'),secret,'download'),m=await meta(download[1]);
      if(ticket.jobId!==download[1]||!m||m.exp<Date.now())throw new Error('Dosya süresi doldu.');
      const data=await readFile(paths(download[1])[download[2]]);res.writeHead(200,{'Content-Type':download[2]==='png'?'image/png':'application/pdf','Content-Disposition':`attachment; filename="dtf-sheet.${download[2]}"`,'Cache-Control':'no-store'});res.end(data);return;
    }
    if(req.method==='GET'){
      if(demo&&url.pathname==='/qa'){res.writeHead(200,{'Content-Type':'text/html; charset=utf-8'});res.end(await readFile('tests/qa.html'));return;}
      if(demo&&url.pathname==='/test-fixture.png'){res.writeHead(200,{'Content-Type':'image/png'});res.end(await readFile('../../work/DTF-Test-Tisort.png'));return;}
      const files={'/':'index.html','/dtf-studio.js':'dtf-studio.js'};if(!files[url.pathname]){send(res,404,{error:'Bulunamadı.'});return;}
      const data=await readFile(join(resolve('dist'),files[url.pathname]));res.writeHead(200,{'Content-Type':extname(files[url.pathname])==='.html'?'text/html; charset=utf-8':'text/javascript; charset=utf-8'});res.end(data);return;
    }
    send(res,404,{error:'Bulunamadı.'});
  }catch(e){send(res,400,{error:e.message||'İşlem tamamlanamadı.'});}
});
const cleaner=setInterval(async()=>{try{for(const file of await readdir(storage)){if(!/^[a-f0-9]{64}\.(json|png|pdf)$/.test(file))continue;const path=join(storage,file);if(Date.now()-(await stat(path)).mtimeMs>3600000)await rm(path,{force:true});}for(const [id,job]of pending)if(job.exp<Date.now())pending.delete(id);for(const [id,rate]of rates)if(Date.now()-rate.hour>3600000)rates.delete(id);}catch{console.error('Geçici dosya temizleme tamamlanamadı.');}},60000);cleaner.unref();
server.listen(port,demo?'127.0.0.1':'0.0.0.0',()=>console.log(`DTF Studio: ${base} (${demo?'yerel demo':'güvenli çıktı servisi'})`));
