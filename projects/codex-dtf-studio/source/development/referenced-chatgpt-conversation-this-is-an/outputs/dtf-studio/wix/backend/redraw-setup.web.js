import {Permissions,webMethod} from 'wix-web-module';
import {collections} from 'wix-data.v2';import {elevate} from 'wix-auth';
export const initializeRedraw=webMethod(Permissions.Admin,async()=>{
  const found=await elevate(collections.listDataCollections)({paging:{limit:100}});let collection=found.collections.find(c=>c._id==='DtfAiQueue');
  if(!collection)collection=await elevate(collections.createDataCollection)({_id:'DtfAiQueue',displayName:'DTF ücretsiz AI iş sırası',permissions:{read:'ADMIN',insert:'ADMIN',update:'ADMIN',remove:'ADMIN'},fields:Object.entries({kind:'TEXT',seen:'NUMBER',expiresAt:'NUMBER',created:'NUMBER',state:'TEXT',ticketHash:'TEXT',claimHash:'TEXT',image:'TEXT',output:'TEXT',text:'TEXT',error:'TEXT',started:'NUMBER',completed:'NUMBER'}).map(([key,type])=>({key,displayName:key,type}))});
  for(const key of ['read','insert','update','remove'])if(collection.permissions[key]!=='ADMIN')throw new Error('Özel iş sırası izinleri doğru değil.');return {ok:true,permissions:collection.permissions};
});
