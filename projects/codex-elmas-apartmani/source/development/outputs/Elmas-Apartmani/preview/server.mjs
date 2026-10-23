import http from 'node:http';
import fs from 'node:fs';
import path from 'node:path';
import {fileURLToPath} from 'node:url';
import {createRuntime} from './runtime.mjs';
const root=path.resolve(path.dirname(fileURLToPath(import.meta.url)),'..','apps-script'),runtime=createRuntime();
const port=Number(process.env.PORT||4173);
http.createServer(async(req,res)=>{
 try{
  if(req.method==='POST'&&req.url==='/rpc'){
   if(req.headers.origin&&req.headers.origin!==`http://127.0.0.1:${port}`&&req.headers.origin!==`http://localhost:${port}`)throw Error('Geçersiz istek kaynağı.');
   let data='';for await(const chunk of req){data+=chunk;if(data.length>8000000)throw Error('Dosya çok büyük.');}
   const {fn,args}=JSON.parse(data);if(!['api','logout'].includes(fn))throw Error('Önizlemede Google girişi kullanılmaz.');const result=runtime.invoke(fn,...args);res.writeHead(200,{'Content-Type':'application/json; charset=utf-8'});return res.end(JSON.stringify({result}));
  }
  if(req.method==='GET'&&(req.url==='/'||req.url.startsWith('/?'))){const html=fs.readFileSync(path.join(root,'Index.html'),'utf8').replace(/<\?!= include_\('([^']+)'\); \?>/g,(_,name)=>fs.readFileSync(path.join(root,name+'.html'),'utf8')).replace('<?!= boot ?>',JSON.stringify({demo:true}));res.writeHead(200,{'Content-Type':'text/html; charset=utf-8','Cache-Control':'no-store'});return res.end(html);}
  res.writeHead(404);res.end('Bulunamadı');
 }catch(e){res.writeHead(400,{'Content-Type':'application/json; charset=utf-8'});res.end(JSON.stringify({error:e.message}));}
}).listen(port,'127.0.0.1',()=>console.log(`Elmas önizleme: http://127.0.0.1:${port}`));
