import {createHash,randomBytes,timingSafeEqual} from 'crypto';
const digest=v=>createHash('sha256').update(v).digest('hex');
const token=()=>randomBytes(32).toString('hex');
const idPattern=/^[a-f0-9]{64}$/;
export class QueueError extends Error{constructor(message,status=400){super(message);this.status=status;}}
// Store must enforce unique _id inserts. No browser can read the collection.
export function createRedrawQueue(store,{workerKey,now=()=>Date.now()}={}){
  const requireWorker=key=>{if(typeof workerKey!=='string'||workerKey.length<32)throw new QueueError('Yerel AI bağlantısı henüz kurulmadı.',503);const a=Buffer.from(digest(String(key||''))),b=Buffer.from(digest(workerKey));if(!timingSafeEqual(a,b))throw new QueueError('Yetki gerekli.',401);};
  const getJob=async(id,ticket)=>{if(!idPattern.test(id||'')||!idPattern.test(ticket||''))throw new QueueError('İş izni geçersiz.',404);const job=await store.get(id);if(!job||job.kind!=='job'||job.ticketHash!==digest(ticket)||job.expiresAt<=now())throw new QueueError('İş bulunamadı veya süresi doldu.',404);return job;};
  const heartbeat=async()=>{const old=await store.get('worker');await store.put({_id:'worker',kind:'worker',seen:now(),expiresAt:now()+86400000,...(old?.active?{active:old.active}:{})});};
  const health=async()=>{const w=await store.get('worker');return {available:Boolean(w&&w.seen>now()-90000&&workerKey?.length>=32),feePerCall:0};};
  return {health,async handle(body={},key=''){
    if(body.op==='heartbeat'){requireWorker(key);await heartbeat();if(body.id){if(!idPattern.test(body.id||'')||!idPattern.test(body.claim||''))throw new QueueError('İş izni geçersiz.');const lease=await store.get('lease-'+body.id),job=await store.get(body.id);if(!lease||lease.claimHash!==digest(body.claim)||!job)throw new QueueError('İş izni geçersiz.',404);return {ok:true,state:job.state};}return {ok:true};}
    if(body.op==='create'){
      if(!(await health()).available)throw new QueueError('Ücretsiz yerel AI bilgisayarı bağlı değil. Orijinali koru modunu kullanabilirsiniz.',503);
      if(typeof body.image!=='string'||body.image.length>180000||!/^data:image\/(jpeg|png|webp);base64,[A-Za-z0-9+/]+=*$/.test(body.image)||typeof body.text!=='string'||body.text.length>300)throw new QueueError('Tasarım alanı veya yazı notu geçersiz.');
      const active=await store.jobs(['queued','running'],now());if(active.length>=2)throw new QueueError('AI sırası dolu. Birkaç dakika sonra tekrar deneyin.',429);
      const bucket=Math.floor(now()/3600000);let slot=false;
      for(let i=0;i<4;i++)if(await store.insert({_id:`rate-${bucket}-${i}`,kind:'rate',expiresAt:now()+7200000})){slot=true;break;}
      if(!slot)throw new QueueError('Ücretsiz AI saatlik kapasitesine ulaşıldı.',429);
      const id=token(),ticket=token();await store.insert({_id:id,kind:'job',ticketHash:digest(ticket),image:body.image,text:body.text,state:'queued',created:now(),expiresAt:now()+3600000});return {id,ticket,state:'queued'};
    }
    if(body.op==='status'){const job=await getJob(body.id,body.ticket);return {state:job.state,...(job.state==='done'?{image:job.output}:{}),...(job.state==='error'?{error:job.error}:{})};}
    if(body.op==='cancel'){const job=await getJob(body.id,body.ticket);if(['queued','running'].includes(job.state))await store.put({...job,state:'cancelled',image:null,output:null});return {state:'cancelled'};}
    if(body.op==='claim'){
      requireWorker(key);await heartbeat();await store.cleanup(now());
      const stalled=await store.jobs(['running'],now());for(const old of stalled)if(old.started<now()-20*60000)await store.put({...old,state:'error',image:null,error:'Yerel AI işlemi yarım kaldı. Yeniden deneyin.'});
      const jobs=await store.jobs(['queued'],now());for(const job of jobs){const claim=token();if(!await store.insert({_id:'lease-'+job._id,kind:'lease',claimHash:digest(claim),expiresAt:job.expiresAt}))continue;
        const current=await store.get(job._id);if(current.state!=='queued')continue;await store.put({...current,state:'running',started:now()});return {id:job._id,claim,image:job.image,text:job.text};
      }return {idle:true};
    }
    if(body.op==='finish'){
      requireWorker(key);if(!idPattern.test(body.id||'')||!idPattern.test(body.claim||''))throw new QueueError('İş izni geçersiz.');const lease=await store.get('lease-'+body.id),job=await store.get(body.id);if(!lease||lease.claimHash!==digest(body.claim)||!job||job.expiresAt<=now())throw new QueueError('İş izni geçersiz.',404);
      if(job.state!=='running')return {state:job.state};
      if(body.error){await store.put({...job,state:'error',error:'AI işlemi tamamlanamadı. Orijinali koru modunu kullanın.',image:null});return {state:'error'};}
      if(typeof body.image!=='string'||body.image.length>380000||!/^data:image\/webp;base64,[A-Za-z0-9+/]+=*$/.test(body.image))throw new QueueError('AI sonucu geçersiz.');
      await store.put({...job,state:'done',image:null,output:body.image,completed:now()});return {state:'done'};
    }
    throw new QueueError('İşlem bulunamadı.',404);
  }};
}
