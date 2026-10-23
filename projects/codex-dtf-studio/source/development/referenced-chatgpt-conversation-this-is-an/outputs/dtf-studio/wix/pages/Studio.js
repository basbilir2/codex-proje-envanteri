import {authentication} from 'wix-members-frontend';
import wixLocationFrontend from 'wix-location-frontend';
import {getAccount,authorizeExport,finishExport} from 'backend/dtf.web';
$w.onReady(()=>{
  $w('#dtfStudio').on('studio-request',async event=>{
    const {id,action,payload}=event.detail||{};
    if(typeof id!=='string')return;
    try{
      if(!authentication.loggedIn())await authentication.promptLogin();
      let data;
      if(action==='account')data=await getAccount();
      else if(action==='authorize')data=await authorizeExport(payload);
      else if(action==='finish')data=await finishExport(payload);
      else if(action==='plans'){wixLocationFrontend.to('/paketler');data={ok:true};}
      else throw new Error('Bilinmeyen işlem.');
      $w('#dtfStudio').setAttribute('response',JSON.stringify({id,data}));
    }catch(error){$w('#dtfStudio').setAttribute('response',JSON.stringify({id,error:error.message||'İşlem tamamlanamadı.'}));}
  });
});
