// Web app runs as owner. Never trust Session.getActiveUser() for residents.
function beginLogin(secretHash){
 assert_(/^[a-f0-9]{64}$/.test(secretHash),'Geçersiz giriş isteği.');const p=props_(),s=settings_(),client=p.getProperty('GOOGLE_CLIENT_ID'),url=s.WebAppURL;
 assert_(client&&p.getProperty('GOOGLE_CLIENT_SECRET')&&url,'Google girişi henüz kurulmadı. Kurulum rehberindeki OAuth adımını tamamlayın.');
 const id=id_(),nonce=id_();CacheService.getScriptCache().put('login:'+id,JSON.stringify({hash:secretHash,nonce:nonce}),600);
 const args={client_id:client,redirect_uri:url,response_type:'code',scope:'openid email profile',state:id,nonce:nonce,prompt:'select_account'};
 return {id:id,url:'https://accounts.google.com/o/oauth2/v2/auth?'+Object.keys(args).map(k=>k+'='+encodeURIComponent(args[k])).join('&')};
}
function oauthCallback_(p){
 let message='Giriş tamamlandı. Bu pencereyi kapatıp Elmas Apartmanı ekranına dönebilirsiniz.';
 try{locked_(()=>{
  const cache=CacheService.getScriptCache(),key='login:'+txt_(p.state,100),raw=cache.get(key);assert_(raw,'Giriş isteği süresi doldu. Yeniden giriş yapın.');const pending=JSON.parse(raw);assert_(!pending.used,'Bu giriş isteği kullanıldı.');pending.used=true;cache.put(key,JSON.stringify(pending),600);
  assert_(!p.error,'Google girişi iptal edildi.');
  const response=UrlFetchApp.fetch('https://oauth2.googleapis.com/token',{method:'post',payload:{code:p.code,client_id:props_().getProperty('GOOGLE_CLIENT_ID'),client_secret:props_().getProperty('GOOGLE_CLIENT_SECRET'),redirect_uri:settings_().WebAppURL,grant_type:'authorization_code'},muteHttpExceptions:true});assert_(response.getResponseCode()===200,'Google kimliği doğrulanamadı.');
  const token=JSON.parse(response.getContentText());
  // ID token arrives directly from Google's HTTPS token endpoint, never from a browser.
  const claims=JSON.parse(Utilities.newBlob(Utilities.base64DecodeWebSafe(token.id_token.split('.')[1])).getDataAsString());
  assert_(claims.aud===props_().getProperty('GOOGLE_CLIENT_ID')&&['accounts.google.com','https://accounts.google.com'].includes(claims.iss)&&Number(claims.exp)>Date.now()/1000&&claims.nonce===pending.nonce,'Google doğrulama bilgisi geçersiz.');
  const res=UrlFetchApp.fetch('https://openidconnect.googleapis.com/v1/userinfo',{headers:{Authorization:'Bearer '+token.access_token},muteHttpExceptions:true});assert_(res.getResponseCode()===200,'Google hesabı okunamadı.');const profile=JSON.parse(res.getContentText());assert_(profile.email_verified===true&&profile.sub===claims.sub,'E-posta doğrulanmamış.');
  const user=rows_('Kullanicilar').find(r=>r.Email.toLowerCase()===profile.email.toLowerCase()&&active_(r.Aktif));assert_(user,'Bu Google hesabına erişim verilmemiş. Yöneticinizle görüşün.');assert_(!user.GoogleSub||user.GoogleSub===profile.sub,'Google hesap kimliği eşleşmiyor.');if(!user.GoogleSub){user.GoogleSub=profile.sub;put_('Kullanicilar',user);}
  pending.userId=user.UserID;cache.put(key,JSON.stringify(pending),600);
 });}catch(err){message=err.message;const c=CacheService.getScriptCache(),key='login:'+txt_(p.state,100),raw=c.get(key);if(raw){const item=JSON.parse(raw);item.error=message;c.put(key,JSON.stringify(item),600);}}
 return HtmlService.createHtmlOutput('<html><meta name="viewport" content="width=device-width, initial-scale=1"><body style="font:18px system-ui;padding:48px;background:#f5f7f3;color:#183f36"><h2>Elmas Apartmanı</h2><p>'+escapeHtml_(message)+'</p></body></html>');
}
function finishLogin(id,secret){
 return locked_(()=>{const c=CacheService.getScriptCache(),key='login:'+txt_(id,100),raw=c.get(key);assert_(raw,'Giriş süresi doldu. Yeniden deneyin.');const r=JSON.parse(raw);assert_(hash_(Utilities.newBlob(String(secret)).getBytes())===r.hash,'Giriş isteği eşleşmiyor.');assert_(!r.error,r.error);if(!r.userId)return {pending:true};c.remove(key);const token=id_()+id_();c.put('session:'+hash_(Utilities.newBlob(token).getBytes()),JSON.stringify({userId:r.userId,expires:Date.now()+21600000}),21600);return {token:token};});
}
function loginWithCode(email,code){
 return locked_(()=>{
  email=txt_(email,150).toLowerCase();code=String(code||'');assert_(/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email)&&code.length>=8,'E-posta veya giriş kodu geçersiz.');
  const cache=CacheService.getScriptCache(),failKey='codefail:'+email,fail=Number(cache.get(failKey)||0);assert_(fail<5,'Çok fazla hatalı deneme. 15 dakika sonra yeniden deneyin.');
  const user=rows_('Kullanicilar').find(r=>String(r.Email).toLowerCase()===email&&active_(r.Aktif));
  const expected=user&&String(user.GoogleSub||'').startsWith('CODE:')?String(user.GoogleSub).slice(5):'';
  const actual=hash_(Utilities.newBlob(email+'|'+code+'|'+ACCESS_CODE_PEPPER_).getBytes());
  if(!expected||expected!==actual){cache.put(failKey,String(fail+1),900);throw new Error('E-posta veya giriş kodu hatalı.');}
  cache.remove(failKey);const token=id_()+id_();cache.put('session:'+hash_(Utilities.newBlob(token).getBytes()),JSON.stringify({userId:user.UserID,expires:Date.now()+21600000}),21600);return {token:token};
 });
}
function createInitialAdminPassword(email,password,confirmation){
 return locked_(()=>{
  email=txt_(email,150).toLowerCase();password=String(password||'');confirmation=String(confirmation||'');
  assert_(/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email),'Geçerli e-posta adresi girin.');assert_(password.length>=8,'Şifre en az 8 karakter olmalı.');assert_(password===confirmation,'Şifreler eşleşmiyor.');
  const user=rows_('Kullanicilar').find(r=>String(r.Email).toLowerCase()===email&&r.Rol==='YONETICI'&&active_(r.Aktif));assert_(user,'Bu e-posta için aktif yönetici kaydı bulunamadı.');assert_(!user.GoogleSub,'Bu yönetici şifresini daha önce oluşturmuş. Normal giriş ekranını kullanın.');
  const next=Object.assign({},user,{GoogleSub:'CODE:'+hash_(Utilities.newBlob(email+'|'+password+'|'+ACCESS_CODE_PEPPER_).getBytes())});put_('Kullanicilar',next);log_(user,'ILK_YONETICI_SIFRESI_OLUSTURULDU',user.UserID,null,{Olusturuldu:true});
  const token=id_()+id_();CacheService.getScriptCache().put('session:'+hash_(Utilities.newBlob(token).getBytes()),JSON.stringify({userId:user.UserID,expires:Date.now()+21600000}),21600);return {token:token};
 });
}
function auth_(token){assert_(typeof token==='string'&&token.length<200,'Lütfen giriş yapın.');const raw=CacheService.getScriptCache().get('session:'+hash_(Utilities.newBlob(token).getBytes()));assert_(raw,'Oturum süresi doldu. Yeniden giriş yapın.');const s=JSON.parse(raw),u=rows_('Kullanicilar').find(r=>r.UserID===s.userId&&active_(r.Aktif));assert_(u&&s.expires>Date.now(),'Oturum geçersiz.');assert_(u.Rol==='YONETICI'||(u.Rol==='SAKIN'&&rows_('Daireler').some(r=>r.DaireID===u.DaireID&&active_(r.Aktif))),'Daire erişiminiz kapalı.');return u;}
function logout(token){CacheService.getScriptCache().remove('session:'+hash_(Utilities.newBlob(String(token)).getBytes()));return true;}
function admin_(u){assert_(u.Rol==='YONETICI','Bu işlem yalnızca yöneticiye açıktır.');}
function own_(u,apartment){assert_(u.Rol==='YONETICI'||u.DaireID===apartment,'Bu daireye erişiminiz yok.');}
/** Sakin link ile salt-okunur snapshot döner; başka daire kimliği yok */
function residentLinkSnapshot_(rawToken){
 const tokenHash=hash_(Utilities.newBlob(String(rawToken)+'|SAKIN_LINK_SALT').getBytes());
 const user=rows_('Kullanicilar').find(r=>r.SakinLinkToken===tokenHash&&active_(r.Aktif)&&r.Rol==='SAKIN');
 assert_(user,'Sakin linki geçersiz veya süresi dolmuş.');
 assert_(rows_('Daireler').some(r=>r.DaireID===user.DaireID&&active_(r.Aktif)),'Daire erişiminiz kapalı.');
 const s=settings_(),own=r=>r.DaireID===user.DaireID,allDues=rows_('Aidatlar'),allCash=rows_('KasaHareketleri');
 const inc=allCash.filter(r=>r.Tur==='GELIR').reduce((v,r)=>v+Number(r.Tutar||0),0),exp=allCash.filter(r=>r.Tur==='GIDER').reduce((v,r)=>v+Number(r.Tutar||0),0);
 return {
 readonly:true,
  user:{AdSoyad:user.AdSoyad,DaireID:user.DaireID,Rol:'SAKIN'},
  settings:Object.fromEntries(['ApartmanAdi','AidatTutari','IBAN','AliciAdi'].map(k=>[k,s[k]])),
  apartments:rows_('Daireler').filter(own),
  dues:allDues.filter(own),
  payments:rows_('Odemeler').filter(own),
  receipts:rows_('Dekontlar').filter(own).map(r=>({DaireID:r.DaireID,BeyanTutar:r.BeyanTutar,Durum:r.Durum,YuklemeTarihi:r.YuklemeTarihi})),
  vouchers:rows_('Makbuzlar').filter(own),
  announcements:rows_('Duyurular'),
  documents:rows_('Belgeler').filter(r=>active_(r.SakinlereAcik)),
  movements:rows_('GelirGider').filter(r=>!active_(r.Silindi)&&r.Tur==='GIDER').map(r=>({HareketID:r.HareketID,Tarih:r.Tarih,Kategori:r.Kategori,Tutar:r.Tutar,Aciklama:r.Kategori+' ortak gideri'})),
  anonymousBuilding:{totalDues:allDues.reduce((v,r)=>v+Number(r.Tutar||0),0),totalPaid:allDues.reduce((v,r)=>v+Number(r.Odenen||0),0),totalDebt:allDues.reduce((v,r)=>v+Number(r.Kalan||0),0),cashBalance:Math.round((inc-exp)*100)/100}
 };
}
function residentLinkSnapshot(rawToken){return locked_(()=>residentLinkSnapshot_(rawToken));}
