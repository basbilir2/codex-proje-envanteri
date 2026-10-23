import {response} from 'wix-http-functions';
import wixData from 'wix-data';
import {getSecret} from 'wix-secrets-backend';
import {createRedrawQueue,QueueError} from 'backend/redraw-queue';
const collection='DtfAiQueue',opt={suppressAuth:true,consistentRead:true};
const origins=new Set(['https://izmirdedtf.wixsite.com','https://a247a575-abde-46de-ab59-a36dc6357d3d.filesusr.com']);
const store={
  async get(id){try{return await wixData.get(collection,id,opt);}catch(e){if(e.code==='WDE0073')return null;throw e;}},
  async insert(item){try{await wixData.insert(collection,item,opt);return true;}catch(e){if(e.code==='WDE0074'||String(e.message).includes('already exists'))return false;throw e;}},
  put:item=>wixData.save(collection,item,opt),
  async jobs(states,time){return (await wixData.query(collection).eq('kind','job').hasSome('state',states).gt('expiresAt',time).ascending('created').limit(10).find(opt)).items;},
  async cleanup(time){const old=await wixData.query(collection).lt('expiresAt',time).limit(100).find(opt);for(const item of old.items)await wixData.remove(collection,item._id,opt);}
};
function send(request,status,data){const origin=request.headers.origin;return response({status,headers:{'Content-Type':'application/json','Cache-Control':'no-store',...(origins.has(origin)?{'Access-Control-Allow-Origin':origin,'Vary':'Origin'}:{}),'Access-Control-Allow-Headers':'Content-Type, Authorization','Access-Control-Allow-Methods':'GET, POST, OPTIONS'},body:JSON.stringify(data)});}
export function options_dtfAi(request){return send(request,204,null);}
async function queue(){let workerKey='';try{workerKey=await getSecret('DTF_REDRAW_WORKER_KEY');}catch{}return createRedrawQueue(store,{workerKey});}
export async function get_dtfAi(request){try{return send(request,200,await(await queue()).health());}catch{return send(request,503,{available:false});}}
export async function post_dtfAi(request){
  if(request.headers.origin&&!origins.has(request.headers.origin))return send(request,403,{error:'Bu siteye izin verilmiyor.'});
  try{const raw=await request.body.text();if(raw.length>400000)throw new QueueError('İstek çok büyük.',413);return send(request,200,await(await queue()).handle(JSON.parse(raw),String(request.headers.authorization||'').replace(/^Bearer /,'')));}
  catch(e){return send(request,e instanceof QueueError?e.status:503,{error:e instanceof QueueError?e.message:'Yerel AI bağlantısı henüz hazır değil.'});}
}
