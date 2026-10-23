// Dependency-injected store: insert is create-only; get always uses primary/consistent reads.
export async function claimSlot(store,hash,{memberId,bucket,limit,jobId}){
  if(!Number.isInteger(limit)||limit<1||limit>500)throw new Error('Geçersiz paket limiti.');
  const offset=parseInt(hash(jobId).slice(0,8),16)%limit;
  for(let n=0;n<limit;n++){
    const slot=(offset+n)%limit,_id=hash(`${memberId}|${bucket}|${slot}`).slice(0,36);
    const existing=await store.get(_id);
    if(existing){if(existing.jobId===jobId)return existing;continue;}
    const entry={_id,memberId,bucket,slot,jobId,completedAt:new Date()};
    try{return await store.insert(entry);}catch(error){
      // Only a verified competing insert can be treated as a collision.
      const winner=await store.get(_id);
      if(!winner)throw error;
      if(winner.jobId===jobId)return winner;
    }
  }
  return null;
}
export function paidBuckets(orders,plans,now=Date.now()){
  return orders.flatMap(order=>{
    const config=plans[order.planId],cycle=order.currentCycle;
    if(!config||order.status!=='ACTIVE'||order.lastPaymentStatus!=='PAID'||order.type!=='ONLINE'||!cycle||!Number.isInteger(cycle.index)||cycle.index<1)return [];
    const start=Date.parse(cycle.startedDate),end=Date.parse(cycle.endedDate);
    if(!Number.isFinite(start)||start>now||!Number.isFinite(end)||end<=now)return [];
    const limit=Number(config.jobs);
    if(!Number.isInteger(limit)||limit<1||limit>500)return [];
    return [{bucket:`order:${order._id}:cycle:${cycle.index}`,limit,label:config.label||'Ücretli üyelik',end}];
  });
}
