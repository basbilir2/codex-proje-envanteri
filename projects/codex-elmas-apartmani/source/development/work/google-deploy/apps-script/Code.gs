/** Elmas Apartmanı V1. All helpers end in _ and cannot be called via google.script.run. */
const SCHEMA_ = {
 Kullanicilar:['UserID','Email','Rol','DaireID','AdSoyad','Aktif','GoogleSub','SakinLinkToken'],
 Daireler:['DaireID','DaireNo','Malik','Kiraci','Telefon','Email','Aktif','AidatMuaf'],
 Aidatlar:['AidatID','DaireID','Donem','Tutar','Odenen','Kalan','Durum','OlusturmaTarihi','Tur','AciklamaDiger'],
 Odemeler:['OdemeID','DaireID','AidatID','Tarih','Tutar','DekontID','Durum','MakbuzID','OlusturmaTarihi'],
 Dekontlar:['DekontID','DaireID','DosyaURL','DosyaID','DosyaHash','DosyaTipi','DosyaAdi','OkunanTutar','OkunanIBAN','OkunanTarih','OkunanSaat','OkunanBanka','OkunanAlici','OkunanGonderen','OkunanIslemNo','OkunanReferans','OkunanAciklama','BeyanTutar','Durum','RedNedeni','YuklemeTarihi','OnayTarihi','Onaylayan','OkumaYontemi','Uyari','BildirimDurumu'],
 Makbuzlar:['MakbuzID','MakbuzNo','OdemeID','DaireID','Tarih','Tutar','Aciklama','DosyaID'],
 GelirGider:['HareketID','Tarih','Tur','Kategori','Tutar','Aciklama','DosyaID','Silindi'],
 KasaHareketleri:['HareketID','Tarih','Tur','Kategori','Tutar','Aciklama','ReferansID'],
 Duyurular:['DuyuruID','Baslik','Metin','Tarih','Onemli'],
 Belgeler:['BelgeID','Baslik','Kategori','DosyaID','DosyaAdi','DosyaTipi','SakinlereAcik','Tarih'],
 Ayarlar:['Anahtar','Deger'], Loglar:['LogID','Tarih','Kullanici','Islem','ReferansID','EskiDeger','YeniDeger'],
 Islemler:['IslemID','Tarih','Tur','Veri','Uygulandi']
};
function props_(){return PropertiesService.getScriptProperties();}
function id_(){return Utilities.getUuid();}
function now_(){return Utilities.formatDate(new Date(),'Europe/Istanbul',"yyyy-MM-dd'T'HH:mm:ss");}
function today_(){return now_().slice(0,10);}
function active_(x){return x===true||String(x).toUpperCase()==='TRUE';}
function assert_(ok,msg){if(!ok)throw new Error(msg);}
function txt_(s,max){return String(s==null?'':s).trim().slice(0,max||500);}
function amount_(x){const n=Number(x);assert_(Number.isFinite(n)&&n>0&&n<=10000000,'Geçerli bir tutar girin.');return Math.round(n*100)/100;}
function round_(x){return Math.round(Number(x)*100)/100;}
function date_(x){assert_(/^\d{4}-\d{2}-\d{2}$/.test(x)&&!isNaN(Date.parse(x))&&new Date(x).toISOString().slice(0,10)===x,'Geçerli tarih girin.');return x;}
function db_(){const id=props_().getProperty('SPREADSHEET_ID')||CONFIG_SPREADSHEET_ID_;assert_(id&&id!=='REPLACE_SPREADSHEET_ID','Veri tablosu bağlantısı eksik.');return SpreadsheetApp.openById(id);}
function ensureSchema_(){const db=db_();Object.keys(SCHEMA_).forEach(n=>{let sh=db.getSheetByName(n);if(!sh){sh=db.insertSheet(n);sh.setFrozenRows(1);}let current=(sh.getDataRange().getValues()[0]||[]),legacy=n==='Aidatlar'?current.indexOf('SonOdemeTarihi'):-1;if(legacy>=0&&typeof sh.deleteColumn==='function'){sh.deleteColumn(legacy+1);current=(sh.getDataRange().getValues()[0]||[]);}const wanted=SCHEMA_[n];if(wanted.some((h,i)=>current[i]!==h)){const range=sh.getRange(1,1,1,wanted.length);range.setValues([wanted]);range.setBackground('#17584b').setFontColor('#ffffff').setFontWeight('bold');}});const oldSetting=rows_('Ayarlar').find(r=>r.Anahtar==='SonOdemeGunu');if(oldSetting)remove_('Ayarlar','SonOdemeGunu');}
function rows_(name){const sh=db_().getSheetByName(name),v=sh.getDataRange().getValues(),h=v.shift();return v.filter(r=>r[0]!=='').map(r=>Object.fromEntries(h.map((k,i)=>[k,r[i] instanceof Date?Utilities.formatDate(r[i],'Europe/Istanbul',k==='Donem'?'yyyy-MM':'yyyy-MM-dd'):r[i]])));}
function cell_(v){if(v===undefined||v===null)return '';if(typeof v==='string'&&/^[=+@\-]/.test(v))return "'"+v;return v;}
function put_(name,obj){const sh=db_().getSheetByName(name),h=SCHEMA_[name],key=h[0];assert_(obj[key]!==undefined,'Kayıt kimliği eksik.');const found=rows_(name).findIndex(r=>String(r[key])===String(obj[key]));sh.getRange(found<0?sh.getLastRow()+1:found+2,1,1,h.length).setValues([h.map(k=>cell_(obj[k]))]);return obj;}
function remove_(name,id){const sh=db_().getSheetByName(name),values=sh.getDataRange().getValues(),row=values.findIndex((r,i)=>i>0&&String(r[0])===String(id));assert_(row>0,'Kayıt bulunamadı.');sh.deleteRow(row+1);}
function settings_(){return Object.fromEntries(rows_('Ayarlar').map(r=>[r.Anahtar,r.Deger]));}
function locked_(f){const l=LockService.getScriptLock();l.waitLock(30000);try{return f();}finally{l.releaseLock();}}
function ensureTriggers_(){['dailyDues_','retryNotifications_'].forEach(fn=>{if(!ScriptApp.getProjectTriggers().some(t=>t.getHandlerFunction()===fn)){const t=ScriptApp.newTrigger(fn).timeBased();if(fn==='dailyDues_')t.everyDays(1).atHour(7).inTimezone('Europe/Istanbul').create();else t.everyHours(1).create();}});}
function log_(u,action,ref,old,val){put_('Loglar',{LogID:id_(),Tarih:now_(),Kullanici:u.Email||u,Islem:action,ReferansID:ref,EskiDeger:JSON.stringify(old||{}),YeniDeger:JSON.stringify(val||{})});}
function setup(){
 assert_(Session.getActiveUser().getEmail()&&Session.getActiveUser().getEmail()===Session.getEffectiveUser().getEmail(),'Kurulumu proje sahibi Apps Script editöründen çalıştırmalı.');
 return locked_(()=>{
  const p=props_();
  if(!p.getProperty('SPREADSHEET_ID')&&CONFIG_SPREADSHEET_ID_&&CONFIG_SPREADSHEET_ID_!=='REPLACE_SPREADSHEET_ID')p.setProperty('SPREADSHEET_ID',CONFIG_SPREADSHEET_ID_);
  if(!p.getProperty('ROOT_FOLDER_ID')&&CONFIG_ROOT_FOLDER_ID_&&CONFIG_ROOT_FOLDER_ID_!=='REPLACE_ROOT_FOLDER_ID')p.setProperty('ROOT_FOLDER_ID',CONFIG_ROOT_FOLDER_ID_);
  if(!p.getProperty('SPREADSHEET_ID'))p.setProperty('SPREADSHEET_ID',SpreadsheetApp.create('Elmas Apartmanı • Yönetim').getId());
  const db=db_();db.setSpreadsheetTimeZone('Europe/Istanbul');
  ensureSchema_();
  if(!p.getProperty('ROOT_FOLDER_ID'))p.setProperty('ROOT_FOLDER_ID',DriveApp.createFolder('Elmas Apartmani').getId());
  ['Dekontlar','Makbuzlar','Faturalar','Belgeler','Raporlar','Yedekler'].forEach(n=>folder_(n));
  const email=p.getProperty('ADMIN_EMAIL')||Session.getEffectiveUser().getEmail();assert_(email,'ADMIN_EMAIL betik özelliğini girin.');
  if(!rows_('Kullanicilar').length)put_('Kullanicilar',{UserID:id_(),Email:email.toLowerCase(),Rol:'YONETICI',DaireID:'',AdSoyad:'Yönetici',Aktif:true});
  for(let i=1;i<=8;i++)if(!rows_('Daireler').some(r=>r.DaireID==='D'+i))put_('Daireler',{DaireID:'D'+i,DaireNo:i,Malik:'',Kiraci:'',Telefon:'',Email:'',Aktif:true});
  const defaults={ApartmanAdi:'Elmas Apartmanı',AidatTutari:1500,OlusturmaGunu:1,BaslangicTarihi:today_().slice(0,7)+'-01',IBAN:'',AliciAdi:'',BildirimKanali:'EMAIL',BildirimEmail:email,WebAppURL:CONFIG_WEB_APP_URL_,WhatsAppTelefon:'',WhatsAppTemplate:'',WhatsAppDil:'tr',TelegramChatID:''};
  const existing=settings_();Object.keys(defaults).forEach(k=>{if(existing[k]===undefined)put_('Ayarlar',{Anahtar:k,Deger:defaults[k]});});
  ensureTriggers_();
  const links={sheet:db.getUrl(),drive:DriveApp.getFolderById(p.getProperty('ROOT_FOLDER_ID')).getUrl()};console.log(JSON.stringify(links));return links;
 });
}
function authorizeProject(){return {sheet:db_().getName(),drive:DriveApp.getFolderById(props_().getProperty('ROOT_FOLDER_ID')||CONFIG_ROOT_FOLDER_ID_).getName(),mailQuota:MailApp.getRemainingDailyQuota()};}
function doGet(e){
 if(e&&e.parameter&&(e.parameter.code||e.parameter.error))return oauthCallback_(e.parameter);
 const t=HtmlService.createTemplateFromFile('Index');t.boot=JSON.stringify({demo:false,receipt:txt_(e&&e.parameter&&e.parameter.dekont,100),residentLink:txt_(e&&e.parameter&&e.parameter.sakinLink,200)}).replace(/</g,'\\u003c');
 return t.evaluate().setTitle('Elmas Apartmanı').addMetaTag('viewport','width=device-width, initial-scale=1');
}
/** Desktop app pushes its complete local snapshot here. Residents remain read-only. */
function doPost(e){
 try{
  const body=JSON.parse(e&&e.postData&&e.postData.contents||'{}');
  const actual=hash_(Utilities.newBlob(String(body.secret||'')).getBytes());
  assert_(actual==='501d3cb3ff318d133f95c615db13fdef27df20bd13f0f2185b1e519c7066c3a3','Senkronizasyon anahtarı geçersiz.');
  let result;if(body.action==='desktopSync')result=locked_(()=>applyDesktopSync_(body.payload));
  else if(body.action==='desktopDebtPdf')result=locked_(()=>makeDebtPDF_({Email:'MASAUSTU'},txt_(body.payload&&body.payload.DaireID,100)));
  else throw new Error('Geçersiz işlem.');
  return ContentService.createTextOutput(JSON.stringify({ok:true,result:result})).setMimeType(ContentService.MimeType.JSON);
 }catch(error){return ContentService.createTextOutput(JSON.stringify({ok:false,error:error.message})).setMimeType(ContentService.MimeType.JSON);}
}
function applyDesktopSync_(payload){
 assert_(payload&&payload.version===1&&payload.tables,'Senkronizasyon paketi geçersiz.');ensureSchema_();
 const required=['Kullanicilar','Daireler','Aidatlar','Odemeler','Dekontlar','Makbuzlar','GelirGider','KasaHareketleri','Duyurular','Belgeler','Ayarlar','Loglar','Islemler'];
 required.forEach(name=>assert_(Array.isArray(payload.tables[name]),'Eksik tablo: '+name));
 const backup=backup_({Email:'MASAUSTU-SENKRON'});
 required.forEach(name=>replaceRows_(name,payload.tables[name].map(row=>Object.fromEntries(SCHEMA_[name].map(key=>[key,row[key]===undefined?'':row[key]])))));
 put_('Loglar',{LogID:id_(),Tarih:now_(),Kullanici:'MASAUSTU',Islem:'MASAUSTU_SENKRON',ReferansID:'DESKTOP',EskiDeger:'',YeniDeger:JSON.stringify({backup:backup.name})});
 return {syncedAt:now_(),backup:backup.name,apartments:payload.tables.Daireler.length};
}
function include_(name){return HtmlService.createHtmlOutputFromFile(name).getContent();}
function api(token,action,payload){
 payload=payload||{};
 return locked_(()=>{
  const u=auth_(token);
  ensureSchema_();
  if(action==='bootstrap'){generateDues_({Email:'SISTEM'});if(u.Rol==='YONETICI')ensureTriggers_();}
  recover_();
  switch(action){
   case 'bootstrap':return snapshot_(u);
   case 'uploadReceipt':return uploadReceipt_(u,payload);
   case 'getFile':return getFile_(u,payload);
   case 'approve':admin_(u);return approve_(u,payload);
   case 'reject':admin_(u);return reject_(u,payload);
   case 'generateDues':admin_(u);return generateDues_(u);
   case 'saveApartment':admin_(u);return saveApartment_(u,payload);
   case 'deleteApartment':admin_(u);return deleteApartment_(u,payload);
   case 'activateApartment':admin_(u);return activateApartment_(u,payload);
   case 'saveDue':admin_(u);return saveDue_(u,payload);
   case 'markDuePaid':admin_(u);return markDuePaid_(u,payload);
   case 'deleteDue':admin_(u);return deleteDue_(u,payload);
   case 'importLedger':admin_(u);return importLedger_(u,payload);
   case 'saveUser':admin_(u);return saveUser_(u,payload);
   case 'saveSettings':admin_(u);return saveSettings_(u,payload);
   case 'saveMovement':admin_(u);return saveMovement_(u,payload);
   case 'updateMovement':admin_(u);return updateMovement_(u,payload);
   case 'deleteMovement':admin_(u);return deleteMovement_(u,payload);
   case 'saveAnnouncement':admin_(u);return saveAnnouncement_(u,payload);
   case 'saveDocument':admin_(u);return saveDocument_(u,payload);
   case 'backup':admin_(u);return backup_(u);
   case 'retryNotification':admin_(u);return notifyReceipt_(payload.id);
   case 'generateResidentLink':admin_(u);return generateResidentLink_(u,payload);
   case 'makeDebtPDF':admin_(u);return makeDebtPDF_(u,payload.DaireID);
   default:throw new Error('Bilinmeyen işlem.');
  }
 });
}
function snapshot_(u){
 const admin=u.Rol==='YONETICI',own=r=>admin||r.DaireID===u.DaireID,s=settings_();
 const data={user:u,settings:admin?s:Object.fromEntries(['ApartmanAdi','AidatTutari','IBAN','AliciAdi'].map(k=>[k,s[k]])),apartments:admin?rows_('Daireler'):rows_('Daireler').filter(r=>r.DaireID===u.DaireID),dues:rows_('Aidatlar').filter(own),payments:rows_('Odemeler').filter(own),receipts:rows_('Dekontlar').filter(own).map(r=>{if(!admin){delete r.Onaylayan;delete r.BildirimDurumu;delete r.DosyaHash;}return r;}),vouchers:rows_('Makbuzlar').filter(own),announcements:rows_('Duyurular'),documents:rows_('Belgeler').filter(r=>admin||active_(r.SakinlereAcik)),movements:rows_('GelirGider').filter(r=>!active_(r.Silindi)&&(admin||r.Tur==='GIDER')).map(r=>admin?r:{HareketID:r.HareketID,Tarih:r.Tarih,Tur:r.Tur,Kategori:r.Kategori,Tutar:r.Tutar,Aciklama:r.Kategori+' ortak gideri'})};
 if(!admin){
  // Anonim bina toplamları – başka daire kimliği yok
  const allDues=rows_('Aidatlar'),allCash=rows_('KasaHareketleri'),allApts=rows_('Daireler').filter(r=>active_(r.Aktif));
  const inc=allCash.filter(r=>r.Tur==='GELIR').reduce((v,r)=>v+Number(r.Tutar||0),0),exp=allCash.filter(r=>r.Tur==='GIDER').reduce((v,r)=>v+Number(r.Tutar||0),0);
  data.anonymousBuilding={totalDues:allDues.reduce((v,r)=>v+Number(r.Tutar||0),0),totalPaid:allDues.reduce((v,r)=>v+Number(r.Odenen||0),0),totalDebt:allDues.reduce((v,r)=>v+Number(r.Kalan||0),0),cashBalance:Math.round((inc-exp)*100)/100,activeApartments:allApts.length};
 }
 if(admin){data.cash=rows_('KasaHareketleri');data.users=rows_('Kullanicilar');data.logs=rows_('Loglar').slice(-40).reverse();data.links={sheet:db_().getUrl(),drive:DriveApp.getFolderById(props_().getProperty('ROOT_FOLDER_ID')||CONFIG_ROOT_FOLDER_ID_).getUrl()};}
 return data;
}
function saveApartment_(u,p){const all=rows_('Daireler'),old=all.find(r=>r.DaireID===p.DaireID),no=Number(p.DaireNo);assert_(Number.isInteger(no)&&no>0&&no<=999,'Geçerli daire numarası girin.');assert_(!all.some(r=>r.DaireID!==(old&&old.DaireID)&&Number(r.DaireNo)===no),'Bu daire numarası zaten kayıtlı.');const r={DaireID:old?old.DaireID:'D-'+id_(),DaireNo:no,Malik:txt_(p.Malik),Kiraci:txt_(p.Kiraci),Telefon:txt_(p.Telefon,30),Email:txt_(p.Email,150),Aktif:p.Aktif===undefined?true:active_(p.Aktif),AidatMuaf:active_(p.AidatMuaf)};put_('Daireler',r);log_(u,old?'DAIRE_GUNCELLENDI':'DAIRE_EKLENDI',r.DaireID,old,r);return r;}
function deleteApartment_(u,p){const old=rows_('Daireler').find(r=>r.DaireID===p.id);assert_(old,'Daire bulunamadı.');const r=Object.assign({},old,{Aktif:false});put_('Daireler',r);log_(u,'DAIRE_PASIFE_ALINDI',r.DaireID,old,r);return r;}
function saveDue_(u,p){const all=rows_('Aidatlar'),old=all.find(r=>r.AidatID===p.AidatID);assert_(rows_('Daireler').some(r=>r.DaireID===p.DaireID),'Daire bulunamadı.');const period=txt_(p.Donem,7);assert_(/^\d{4}-\d{2}$/.test(period)&&Number(period.slice(5))>=1&&Number(period.slice(5))<=12,'Geçerli dönem seçin.');const total=round_(Number(p.Tutar)),paid=round_(Number(p.Odenen||0));assert_(Number.isFinite(total)&&total>=0&&total<=10000000,'Geçerli borç tutarı girin.');assert_(Number.isFinite(paid)&&paid>=0&&paid<=total,'Ödenen tutar borçtan büyük olamaz.');const dueId=old?old.AidatID:'A-MANUAL-'+id_();const validTur=['Aidat','Apartman ortak gideri','Diğer'];const tur=txt_(p.Tur||'Aidat',50);assert_(validTur.includes(tur),'Geçersiz borç türü seçin.');const aciklamaDiger=txt_(p.AciklamaDiger||'',200);assert_(tur!=='Diğer'||aciklamaDiger,'Diğer türü için açıklama zorunludur.');const remaining=round_(total-paid),r={AidatID:dueId,DaireID:p.DaireID,Donem:period,Tutar:total,Odenen:paid,Kalan:remaining,Durum:remaining===0?'ODENDI':paid>0?'KISMI':'BORCLU',OlusturmaTarihi:old?old.OlusturmaTarihi:now_(),Tur:tur,AciklamaDiger:aciklamaDiger};put_('Aidatlar',r);log_(u,old?'BORC_DUZELTILDI':'BORC_EKLENDI',r.AidatID,old,r);return r;}
function deleteDue_(u,p){const old=rows_('Aidatlar').find(r=>r.AidatID===p.id);assert_(old,'Borç kaydı bulunamadı.');assert_(!rows_('Odemeler').some(r=>String(r.AidatID).split(',').includes(old.AidatID)),'Ödeme bağlı olan borç silinemez; tutarı düzenleyin.');remove_('Aidatlar',old.AidatID);log_(u,'BORC_SILINDI',old.AidatID,old,null);return true;}
function saveUser_(u,p){
 const all=rows_('Kullanicilar'),old=all.find(r=>r.UserID===p.UserID),email=txt_(p.Email,150).toLowerCase();assert_(/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email),'Geçerli e-posta girin.');assert_(['YONETICI','SAKIN'].includes(p.Rol),'Geçersiz rol.');assert_(!all.some(r=>r.Email.toLowerCase()===email&&r.UserID!==p.UserID),'Bu e-posta zaten kayıtlı.');assert_(p.Rol==='YONETICI'||rows_('Daireler').some(r=>r.DaireID===p.DaireID),'Daire seçin.');
  assert_(!(old&&old.Email!==email&&!p.AccessCode),'E-posta değiştiğinde yeni giriş kodu girin.');
  const stored=old&&old.Email===email?old.GoogleSub:'',linkToken=old?old.SakinLinkToken||'':'';
  const credential=p.AccessCode?'CODE:'+hash_(Utilities.newBlob(email+'|'+String(p.AccessCode)+'|'+ACCESS_CODE_PEPPER_).getBytes()):stored;
  assert_(credential||linkToken,'En az 8 karakterli giriş kodu girin.');if(p.AccessCode)assert_(String(p.AccessCode).length>=8,'Giriş kodu en az 8 karakter olmalı.');
  const r={UserID:old?old.UserID:id_(),Email:email,Rol:p.Rol,DaireID:p.Rol==='SAKIN'?p.DaireID:'',AdSoyad:txt_(p.AdSoyad,100),Aktif:active_(p.Aktif),GoogleSub:credential,SakinLinkToken:linkToken};
 assert_(!(old&&old.Rol==='YONETICI'&&active_(old.Aktif)&&(r.Rol!=='YONETICI'||!r.Aktif))||all.some(x=>x.UserID!==r.UserID&&x.Rol==='YONETICI'&&active_(x.Aktif)),'Son yönetici devre dışı bırakılamaz.');put_('Kullanicilar',r);log_(u,'KULLANICI_YETKISI',r.UserID,old,r);return r;
}
function saveSettings_(u,p){
 const old=settings_(),next=Object.assign({},old);Object.keys(old).forEach(k=>{if(p[k]!==undefined)next[k]=txt_(p[k],500);});next.AidatTutari=amount_(next.AidatTutari);
 next.OlusturmaGunu=Number(next.OlusturmaGunu);assert_(Number.isInteger(next.OlusturmaGunu)&&next.OlusturmaGunu>=1&&next.OlusturmaGunu<=28,'Gün 1–28 arasında olmalı.');delete next.SonOdemeGunu;date_(next.BaslangicTarihi);
 next.IBAN=next.IBAN.replace(/\s/g,'').toUpperCase();assert_(!next.IBAN||validIban_(next.IBAN),'Geçerli bir TR IBAN girin.');assert_(['EMAIL','WHATSAPP','TELEGRAM'].includes(next.BildirimKanali),'Bildirim kanalı geçersiz.');
 assert_(!next.WebAppURL||/^https:\/\/script\.google\.com\/macros\/s\/[\w-]+\/exec$/.test(next.WebAppURL),'Web App adresi /exec ile bitmeli.');assert_(!next.BildirimEmail||/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(next.BildirimEmail),'Bildirim e-postası geçersiz.');
 Object.keys(next).forEach(k=>put_('Ayarlar',{Anahtar:k,Deger:next[k]}));log_(u,'AYARLAR_DEGISTI','Ayarlar',old,next);return next;
}
function validIban_(s){if(!/^TR\d{24}$/.test(s))return false;const v=(s.slice(4)+s.slice(0,4)).replace(/[A-Z]/g,c=>String(c.charCodeAt(0)-55));let rem=0;for(const c of v)rem=(rem*10+Number(c))%97;return rem===1;}
function saveAnnouncement_(u,p){assert_(txt_(p.Baslik)&&txt_(p.Metin),'Başlık ve metin girin.');const r={DuyuruID:id_(),Baslik:txt_(p.Baslik,150),Metin:txt_(p.Metin,5000),Tarih:today_(),Onemli:active_(p.Onemli)};put_('Duyurular',r);log_(u,'DUYURU',r.DuyuruID,null,r);return r;}
function activateApartment_(u,p){const old=rows_('Daireler').find(r=>r.DaireID===p.id);assert_(old,'Daire bulunamadı.');const r=Object.assign({},old,{Aktif:true});put_('Daireler',r);log_(u,'DAIRE_AKTIVE_EDILDI',r.DaireID,old,r);return r;}
function generateResidentLink_(u,p){const all=rows_('Kullanicilar'),requested=all.find(r=>r.UserID===p.UserID),daireID=p.DaireID||(requested&&requested.DaireID),apt=rows_('Daireler').find(r=>r.DaireID===daireID);assert_(apt,'Daire bulunamadı.');let resident=requested&&requested.Rol==='SAKIN'?requested:all.find(r=>r.DaireID===apt.DaireID&&r.Rol==='SAKIN'&&active_(r.Aktif));if(!resident)resident={UserID:'LINK-'+apt.DaireID,Email:'',Rol:'SAKIN',DaireID:apt.DaireID,AdSoyad:apt.Kiraci||apt.Malik||('Daire '+apt.DaireNo+' sakini'),Aktif:true,GoogleSub:'',SakinLinkToken:''};all.filter(r=>r.DaireID===apt.DaireID&&r.Rol==='SAKIN'&&r.UserID!==resident.UserID&&r.SakinLinkToken).forEach(r=>put_('Kullanicilar',Object.assign({},r,{SakinLinkToken:''})));const rawToken=id_()+id_(),tokenHash=hash_(Utilities.newBlob(rawToken+'|SAKIN_LINK_SALT').getBytes()),next=Object.assign({},resident,{SakinLinkToken:tokenHash});put_('Kullanicilar',next);log_(u,'SAKIN_LINK_URETILDI',resident.UserID,null,{tokenHash});const base=settings_().WebAppURL||CONFIG_WEB_APP_URL_;assert_(base,'Web uygulaması adresi bulunamadı.');return {url:base+'?sakinLink='+encodeURIComponent(rawToken),expiresNote:'Link kalıcıdır; yeni link üretilince eskisi geçersiz olur.'};}
