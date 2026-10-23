import {Permissions,webMethod} from 'wix-web-module';
import {currentMember} from 'wix-members-backend';
import {orders} from 'wix-pricing-plans-backend';
import wixData from 'wix-data';
import {secrets} from 'wix-secrets-backend.v2';
import {elevate} from 'wix-auth';
import {fetch} from 'wix-fetch';
import {createHash} from 'crypto';
import {claimSlot,paidBuckets} from 'backend/quota-core.js';
import {layout} from 'public/engine.js';
const read={suppressAuth:true,consistentRead:true},write={suppressAuth:true};
const digest=s=>createHash('sha256').update(s).digest('hex');
const store={
  async get(id){return wixData.get('DtfUsage',id,read);},
  async insert(item){return wixData.insert('DtfUsage',item,write);},
};
async function identity(){const m=await currentMember.getMember();if(!m?._id||m.status!=='APPROVED')throw new Error('Onaylı üye hesabıyla giriş yapın.');return m._id;}
async function config(){const c=await wixData.get('DtfConfig','settings',read);if(!c||c.enabled!==true)throw new Error('Studio kurulumu tamamlanıyor. Çıktı henüz açılmadı.');if(!c.rendererUrl?.startsWith('https://'))throw new Error('Güvenli çıktı servisi bağlı değil.');return c;}
async function entitlement(memberId,c){
  const list=[];let skip=0;
  do{const page=await orders.listCurrentMemberOrders({orderStatuses:['ACTIVE']},{},{limit:100,skip});list.push(...page);if(page.length<100)break;skip+=100;if(skip>=1000)throw new Error('Üyelik sayısı için destek gerekiyor.');}while(true);
  const buckets=[{bucket:'trial:lifetime',limit:1,label:'İlk kullanım ücretsiz'},...paidBuckets(list,c.plans||{})];
  const used=await wixData.query('DtfUsage').eq('memberId',memberId).hasSome('bucket',buckets.map(x=>x.bucket)).limit(1000).find(read);
  for(const b of buckets)b.remaining=Math.max(0,b.limit-used.items.filter(x=>x.bucket===b.bucket).length);
  return buckets;
}
async function service(c,path,method='GET',data){
  const {value}=await elevate(secrets.getSecretValue)('DTF_SERVICE_SECRET');
  const res=await fetch(c.rendererUrl.replace(/\/$/,'')+path,{method,headers:{Authorization:`Bearer ${value}`,'Content-Type':'application/json'},...(data?{body:JSON.stringify(data)}:{})});
  const result=await res.json();if(!res.ok)throw new Error(result.error||'Çıktı servisi yanıt vermedi.');return result;
}
function jobId(memberId,requestId){if(!/^[a-f0-9-]{36}$/.test(requestId))throw new Error('Geçersiz işlem kimliği.');return digest(memberId+':'+requestId);}
async function previous(memberId,id){const q=await wixData.query('DtfUsage').eq('memberId',memberId).eq('jobId',id).limit(1).find(read);return q.items[0];}
export const getAccount=webMethod(Permissions.SiteMember,async()=>{
  const memberId=await identity(),c=await config(),buckets=await entitlement(memberId,c),remaining=buckets.reduce((a,b)=>a+b.remaining,0);
  return {remaining,label:remaining?`${remaining} çıktı hakkı`:'Paket seçin'};
});
export const authorizeExport=webMethod(Permissions.SiteMember,async({requestId,manifest})=>{
  const memberId=await identity(),c=await config(),id=jobId(memberId,requestId);
  // Discard all unsupported client fields and validate before allowing a render.
  const clean={designs:manifest.designs.map(d=>({id:String(d.id),widthCm:Number(d.widthCm),heightCm:Number(d.heightCm),quantity:Number(d.quantity)})),settings:layout(manifest.designs,manifest.settings).settings};
  if(new Set(clean.designs.map(d=>d.id)).size!==clean.designs.length||clean.designs.some(d=>!/^[-a-f0-9]{36}$/.test(d.id)))throw new Error('Geçersiz tasarım kimliği.');
  const old=await previous(memberId,id),buckets=await entitlement(memberId,c);
  if(!old&&!buckets.some(b=>b.remaining>0))throw new Error('Ücretsiz hakkınız veya paket hakkınız kalmadı. Paket seçin.');
  // Bind each request ID permanently to its manifest in CMS, across renderer restarts.
  const fingerprint=digest(JSON.stringify(clean));
  const existing=await wixData.get('DtfJobs',id.slice(0,36),read);
  if(existing&&existing.fingerprint!==fingerprint)throw new Error('İş içeriği değişti. Yeniden dizgi oluşturun.');
  if(!existing){try{await wixData.insert('DtfJobs',{_id:id.slice(0,36),memberId,jobId:id,fingerprint},write);}catch(error){const winner=await wixData.get('DtfJobs',id.slice(0,36),read);if(!winner||winner.fingerprint!==fingerprint)throw error;}}
  return service(c,'/internal/authorize','POST',{jobId:id,memberId,manifest:clean});
});
export const finishExport=webMethod(Permissions.SiteMember,async({requestId})=>{
  const memberId=await identity(),c=await config(),id=jobId(memberId,requestId),old=await previous(memberId,id);
  const state=await service(c,`/internal/jobs/${id}/status`);
  if(!state.ready)throw new Error('Çıktı hazır değil; kullanım hakkı düşülmedi.');
  if(!old){
    const buckets=await entitlement(memberId,c);let claimed;
    for(const b of buckets){claimed=await claimSlot(store,digest,{memberId,bucket:b.bucket,limit:b.limit,jobId:id});if(claimed)break;}
    if(!claimed)throw new Error('Bu sırada kullanım hakkınız tükendi. Paket seçin.');
  }
  return service(c,`/internal/jobs/${id}/deliver`);
});
