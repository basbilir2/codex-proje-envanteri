function sendAdminNotification_(d){
 const s=settings_(),p=props_(),link=s.WebAppURL?s.WebAppURL+'?dekont='+encodeURIComponent(d.DekontID):'',value=Number(d.OkunanTutar||d.BeyanTutar).toFixed(2),text='ELMAS APARTMANI\nYeni dekont yüklendi.\nDaire: '+d.DaireID+'\nTutar: '+value+' TL\nTarih: '+d.YuklemeTarihi+'\nKontrol et: '+(link||'Web App adresini Ayarlar bölümünden kaydedin.');
 let sent=false,problem='';
 try{
  if(s.BildirimKanali==='WHATSAPP'){
   assert_(p.getProperty('WHATSAPP_TOKEN')&&p.getProperty('WHATSAPP_PHONE_ID')&&p.getProperty('WHATSAPP_API_VERSION')&&s.WhatsAppTelefon&&s.WhatsAppTemplate,'WhatsApp kurulumu eksik.');
   const body={messaging_product:'whatsapp',to:s.WhatsAppTelefon,type:'template',template:{name:s.WhatsAppTemplate,language:{code:s.WhatsAppDil||'tr'},components:[{type:'body',parameters:[d.DaireID,value,d.YuklemeTarihi,link].map(x=>({type:'text',text:x}))}]}};
   const r=UrlFetchApp.fetch('https://graph.facebook.com/'+encodeURIComponent(p.getProperty('WHATSAPP_API_VERSION'))+'/'+encodeURIComponent(p.getProperty('WHATSAPP_PHONE_ID'))+'/messages',{method:'post',contentType:'application/json',headers:{Authorization:'Bearer '+p.getProperty('WHATSAPP_TOKEN')},payload:JSON.stringify(body),muteHttpExceptions:true});assert_(r.getResponseCode()<300,'WhatsApp gönderimi başarısız.');sent=true;
  }else if(s.BildirimKanali==='TELEGRAM'){
   assert_(p.getProperty('TELEGRAM_TOKEN')&&s.TelegramChatID,'Telegram kurulumu eksik.');const r=UrlFetchApp.fetch('https://api.telegram.org/bot'+p.getProperty('TELEGRAM_TOKEN')+'/sendMessage',{method:'post',payload:{chat_id:s.TelegramChatID,text:text},muteHttpExceptions:true});assert_(r.getResponseCode()===200&&JSON.parse(r.getContentText()).ok,'Telegram gönderimi başarısız.');sent=true;
  }
 }catch(err){problem=err.message;}
 if(!sent){const email=s.BildirimEmail||rows_('Kullanicilar').filter(u=>u.Rol==='YONETICI'&&active_(u.Aktif)).map(u=>u.Email).join(',');assert_(email,'Bildirim alıcısı tanımlı değil.');MailApp.sendEmail({to:email,subject:'Elmas Apartmanı • Yeni dekont • '+d.DaireID,body:text});return problem?'EMAIL_YEDEK: '+problem:'EMAIL_GONDERILDI';}
 return s.BildirimKanali+'_GONDERILDI';
}
function notifyReceipt_(id){const r=rows_('Dekontlar').find(d=>d.DekontID===id);assert_(r,'Dekont bulunamadı.');if(/GONDERILDI|EMAIL_YEDEK/.test(r.BildirimDurumu))return {status:r.BildirimDurumu};try{r.BildirimDurumu=sendAdminNotification_(r);}catch(err){r.BildirimDurumu='HATA: '+txt_(err.message,250);}put_('Dekontlar',r);return {status:r.BildirimDurumu};}
function retryNotifications_(){return locked_(()=>{rows_('Dekontlar').filter(r=>r.Durum==='BEKLIYOR'&&!/GONDERILDI|EMAIL_YEDEK/.test(r.BildirimDurumu)).slice(0,10).forEach(r=>notifyReceipt_(r.DekontID));});}
