import http from 'node:http';
import fs from 'node:fs';
import path from 'node:path';
import crypto from 'node:crypto';
import {fileURLToPath} from 'node:url';
import {createRuntime} from '../preview/runtime.mjs';

const projectRoot=path.resolve(path.dirname(fileURLToPath(import.meta.url)),'..');
const webRoot=path.join(projectRoot,'apps-script');
const mutating=new Set(['approve','reject','generateDues','saveApartment','deleteApartment','activateApartment','saveDue','markDuePaid','deleteDue','importLedger','saveUser','saveSettings','saveMovement','updateMovement','deleteMovement','saveAnnouncement','saveDocument','generateResidentLink']);

function readJson(file){try{return JSON.parse(fs.readFileSync(file,'utf8'));}catch{return null;}}
function normalizeBackup(raw){
 if(!raw||!raw.tables)return raw;
 const probe=createRuntime(false),tables={};
 for(const [name,records] of Object.entries(raw.tables)){
  if(Array.isArray(records)&&Array.isArray(records[0])){tables[name]=records;continue;}
  const header=(probe.tables[name]&&probe.tables[name][0])||[];
  tables[name]=[header,...(records||[]).map(row=>header.map(key=>row[key]??''))];
 }
 return {version:2,tables,props:raw.props||{},files:raw.files||[]};
}
function backupObject(runtime){const tables={};for(const name of Object.keys(runtime.tables))tables[name]=runtime.invoke('rows_',name);return {version:1,created:new Date().toISOString(),tables};}

export async function startDesktopServer({dataDir,initialData='',syncConfig={}}){
 fs.mkdirSync(dataDir,{recursive:true});
 const dbFile=path.join(dataDir,'elmas-veri.json'),configFile=path.join(dataDir,'senkronizasyon.json'),statusFile=path.join(dataDir,'senkronizasyon-durumu.json');
 if(!fs.existsSync(configFile))fs.writeFileSync(configFile,JSON.stringify(syncConfig,null,2),'utf8');
 let restored=readJson(dbFile);
 if(!restored&&initialData&&fs.existsSync(initialData))restored=normalizeBackup(readJson(initialData));
 const runtime=createRuntime(false,restored);
 const admin=runtime.invoke('rows_','Kullanicilar').find(x=>x.Rol==='YONETICI')||runtime.invoke('rows_','Kullanicilar')[0];
 const token='desktop-admin',key='session:'+crypto.createHash('sha256').update(token).digest('hex');
 runtime.cache.set(key,JSON.stringify({userId:admin.UserID,expires:Date.now()+315360000000}));
 const persist=()=>{const temp=dbFile+'.tmp';fs.writeFileSync(temp,JSON.stringify(runtime.serialize()),'utf8');fs.renameSync(temp,dbFile);};
 persist();
 let syncing=false,pending=false;
 async function remoteAction(action,payload){
  const cfg=Object.assign({},readJson(configFile)||{},syncConfig||{}),url=String(cfg.webAppUrl||''),secret=String(cfg.secret||'');
  if(!url||!secret)throw Error('Senkronizasyon yapılandırılmadı.');
  const response=await fetch(url,{method:'POST',headers:{'Content-Type':'text/plain;charset=utf-8'},body:JSON.stringify({action,secret,payload}),redirect:'follow'});
  const text=await response.text();let body;try{body=JSON.parse(text);}catch{throw Error('Çevrimiçi servis geçersiz yanıt verdi.');}
  if(!response.ok||!body.ok)throw Error(body.error||('HTTP '+response.status));return body.result;
 }
 async function syncNow(){
  if(syncing){pending=true;return {queued:true};}
  const cfg=Object.assign({},readJson(configFile)||{},syncConfig||{}),url=String(cfg.webAppUrl||''),secret=String(cfg.secret||'');
  if(!url||!secret){const status={ok:false,at:new Date().toISOString(),message:'Senkronizasyon yapılandırılmadı.'};fs.writeFileSync(statusFile,JSON.stringify(status,null,2));return status;}
  syncing=true;
  try{
   const response=await fetch(url,{method:'POST',headers:{'Content-Type':'text/plain;charset=utf-8'},body:JSON.stringify({action:'desktopSync',secret,payload:backupObject(runtime)}),redirect:'follow'});
   const text=await response.text();let body;try{body=JSON.parse(text);}catch{throw Error('Çevrimiçi servis geçersiz yanıt verdi.');}
   if(!response.ok||!body.ok)throw Error(body.error||('HTTP '+response.status));
   const status={ok:true,at:new Date().toISOString(),message:'Google Sheets ve sakin ekranı güncellendi.'};fs.writeFileSync(statusFile,JSON.stringify(status,null,2));return status;
  }catch(error){const status={ok:false,at:new Date().toISOString(),message:error.message};fs.writeFileSync(statusFile,JSON.stringify(status,null,2));return status;}
  finally{syncing=false;if(pending){pending=false;setTimeout(()=>syncNow(),250);}}
 }
 const server=http.createServer(async(req,res)=>{
  try{
   if(req.method==='POST'&&req.url==='/rpc'){
    if(req.headers.origin&&!/^http:\/\/127\.0\.0\.1:\d+$/.test(req.headers.origin))throw Error('Geçersiz istek kaynağı.');
    let data='';for await(const chunk of req){data+=chunk;if(data.length>12000000)throw Error('İstek çok büyük.');}
    const {fn,args=[]}=JSON.parse(data);let result;
    if(fn==='api'){
     const action=args[1],payload=args[2]||{};
     if(action==='makeDebtPDF'){
      const status=await syncNow();if(!status.ok)throw Error(status.message);result=await remoteAction('desktopDebtPdf',payload);
     }else{
      result=runtime.invoke('api',token,action,payload);persist();
      if(mutating.has(action)){const task=syncNow();if(action==='generateResidentLink'){const status=await task;if(!status.ok)throw Error(status.message);}}
     }
    }else if(fn==='desktopImportBackup'){
     const incoming=normalizeBackup(JSON.parse(String(args[0]||'')));if(!incoming||!incoming.tables)throw Error('Yedek dosyası geçersiz.');
     const safety=path.join(dataDir,'otomatik-yedek-'+new Date().toISOString().replace(/[:.]/g,'-')+'.json');fs.copyFileSync(dbFile,safety);
     for(const [name,rows] of Object.entries(incoming.tables))runtime.tables[name]=structuredClone(rows);persist();syncNow();result={ok:true,safety};
    }else if(fn==='desktopSync')result=await syncNow();
    else if(fn==='desktopStatus')result=readJson(statusFile)||{ok:false,message:'Henüz eşitlenmedi.'};
    else if(fn==='logout')result=true;
    else throw Error('Bilinmeyen masaüstü işlemi.');
    res.writeHead(200,{'Content-Type':'application/json; charset=utf-8','Cache-Control':'no-store'});return res.end(JSON.stringify({result}));
   }
   if(req.method==='GET'&&(req.url==='/'||req.url.startsWith('/?'))){
    const html=fs.readFileSync(path.join(webRoot,'Index.html'),'utf8').replace(/<\?!= include_\('([^']+)'\); \?>/g,(_,name)=>fs.readFileSync(path.join(webRoot,name+'.html'),'utf8')).replace('<?!= boot ?>',JSON.stringify({demo:true,desktop:true}));
    res.writeHead(200,{'Content-Type':'text/html; charset=utf-8','Cache-Control':'no-store'});return res.end(html);
   }
   res.writeHead(404);res.end('Bulunamadı');
  }catch(error){res.writeHead(400,{'Content-Type':'application/json; charset=utf-8'});res.end(JSON.stringify({error:error.message}));}
 });
 await new Promise((resolve,reject)=>{server.once('error',reject);server.listen(0,'127.0.0.1',resolve);});
 const port=server.address().port;
 return {url:`http://127.0.0.1:${port}`,close:()=>new Promise(resolve=>server.close(resolve)),dataDir,dbFile,syncNow};
}
