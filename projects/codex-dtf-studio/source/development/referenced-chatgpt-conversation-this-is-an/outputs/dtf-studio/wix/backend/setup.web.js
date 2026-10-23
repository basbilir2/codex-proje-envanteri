import {Permissions,webMethod} from 'wix-web-module';
import {collections} from 'wix-data.v2';
import {elevate} from 'wix-auth';
import wixData from 'wix-data';
const schemas={
  DtfConfig:{enabled:'BOOLEAN',rendererUrl:'TEXT',plans:'OBJECT'},
  DtfUsage:{memberId:'TEXT',bucket:'TEXT',slot:'NUMBER',jobId:'TEXT',completedAt:'DATETIME'},
  DtfJobs:{memberId:'TEXT',jobId:'TEXT',fingerprint:'TEXT'},
};
export const initializeStudio=webMethod(Permissions.Admin,async()=>{
  const result=[];
  const existing=await elevate(collections.listDataCollections)({paging:{limit:100}});
  for(const [_id,fields]of Object.entries(schemas)){
    let collection=existing.collections.find(c=>c._id===_id);
    if(!collection){collection=await elevate(collections.createDataCollection)({_id,displayName:_id,permissions:{read:'ADMIN',insert:'ADMIN',update:'ADMIN',remove:'ADMIN'},fields:Object.entries(fields).map(([key,type])=>({key,displayName:key,type}))});}
    for(const key of ['read','insert','update','remove'])if(collection.permissions[key]!=='ADMIN')throw new Error(_id+' yönetici izinleri doğrulanamadı.');
    result.push({id:_id,permissions:collection.permissions});
  }
  const old=await wixData.get('DtfConfig','settings',{suppressAuth:true,consistentRead:true});
  if(!old)await wixData.insert('DtfConfig',{_id:'settings',enabled:false,rendererUrl:'',plans:{}},{suppressAuth:true});
  return {ok:true,collections:result,enabled:false};
});
