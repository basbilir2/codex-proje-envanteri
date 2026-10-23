/** A durable journal commit is the financial source of truth. Projections are idempotent. */
function commit_(type,records){const event={IslemID:id_(),Tarih:now_(),Tur:type,Veri:JSON.stringify(records),Uygulandi:false};assert_(event.Veri.length<45000,'İşlem boyutu sınırı aşıldı.');put_('Islemler',event);SpreadsheetApp.flush();applyEvent_(event);return event.IslemID;}
function applyEvent_(e){const records=JSON.parse(e.Veri);records.forEach(r=>put_(r.table,r.data));SpreadsheetApp.flush();e.Uygulandi=true;put_('Islemler',e);SpreadsheetApp.flush();}
function recover_(){rows_('Islemler').filter(e=>!active_(e.Uygulandi)).forEach(applyEvent_);}
function logRecord_(u,action,ref,old,data){return {table:'Loglar',data:{LogID:id_(),Tarih:now_(),Kullanici:u.Email||u,Islem:action,ReferansID:ref,EskiDeger:JSON.stringify(old||{}),YeniDeger:JSON.stringify(data||{})}};}
function dailyDues_(){return locked_(()=>{recover_();return generateDues_({Email:'SISTEM'});});}
function generateDues_(u){
 const s=settings_(),current=today_(),start=s.BaslangicTarihi,existing=rows_('Aidatlar'),apartments=rows_('Daireler').filter(r=>active_(r.Aktif)&&!active_(r.AidatMuaf));let count=0;
 let year=Number(start.slice(0,4)),month=Number(start.slice(5,7));assert_(year>=2020&&year<=2100,'Başlangıç tarihi 2020–2100 aralığında olmalı.');
 while(true){const period=year+'-'+String(month).padStart(2,'0'),created=period+'-'+String(s.OlusturmaGunu).padStart(2,'0');if(created>current)break;
  if(period>=start.slice(0,7))apartments.forEach(a=>{const aid='A-'+a.DaireID+'-'+period;if(!existing.some(x=>x.AidatID===aid)){const r={AidatID:aid,DaireID:a.DaireID,Donem:period,Tutar:amount_(s.AidatTutari),Odenen:0,Kalan:amount_(s.AidatTutari),Durum:'BORCLU',OlusturmaTarihi:now_(),Tur:'Aidat',AciklamaDiger:''};commit_('AIDAT',[{table:'Aidatlar',data:r},logRecord_(u,'AIDAT_OLUSTURULDU',aid,null,r)]);count++;}});
  month++;if(month===13){month=1;year++;}
 }return {count:count};
}
function allocate_(dues,total){let cents=Math.round(total*100);const updates=[],ids=[];dues.filter(r=>Number(r.Kalan)>0).sort((a,b)=>a.Donem.localeCompare(b.Donem)).forEach(r=>{if(!cents)return;const take=Math.min(cents,Math.round(r.Kalan*100));cents-=take;const next=Object.assign({},r,{Odenen:round_(Number(r.Odenen)+take/100),Kalan:round_(Number(r.Kalan)-take/100)});next.Durum=next.Kalan===0?'ODENDI':'KISMI';updates.push({table:'Aidatlar',data:next});ids.push(r.AidatID);});assert_(cents===0,'Ödeme toplam borcu aşıyor. Tutarı kontrol edin.');return {updates:updates,ids:ids};}
function markDuePaid_(u,p){
 const old=rows_('Aidatlar').find(r=>r.AidatID===p.id);assert_(old,'Borç kaydı bulunamadı.');const value=round_(Number(old.Kalan||0));assert_(value>0,'Bu borç zaten ödenmiş.');
 const tur=old.Tur||'Aidat',next=Object.assign({},old,{Odenen:round_(Number(old.Tutar||0)),Kalan:0,Durum:'ODENDI',Tur:tur}),payId='O-MANUEL-'+id_(),payment={OdemeID:payId,DaireID:old.DaireID,AidatID:old.AidatID,Tarih:today_(),Tutar:value,DekontID:'',Durum:'ONAYLANDI',MakbuzID:'',OlusturmaTarihi:now_()},label=(tur==='Diğer'&&old.AciklamaDiger)||tur;
 commit_('TEK_TIK_TAHSILAT',[{table:'Aidatlar',data:next},{table:'Odemeler',data:payment},{table:'KasaHareketleri',data:{HareketID:payId,Tarih:today_(),Tur:'GELIR',Kategori:tur,Tutar:value,Aciklama:old.DaireID+' • '+old.Donem+' • '+label+' tek tıkla ödendi',ReferansID:payId}},logRecord_(u,'BORC_ODENDI',old.AidatID,old,next)]);return {amount:value};
}
function approve_(u,p){
 const all=rows_('Dekontlar'),d=all.find(r=>r.DekontID===p.id);assert_(d,'Dekont bulunamadı.');if(d.Durum==='ONAYLANDI')return {already:true};assert_(d.Durum==='BEKLIYOR','Sadece bekleyen dekont onaylanabilir.');
 const value=amount_(p.Tutar),date=date_(p.Tarih),txn=txt_(p.IslemNo,100),ref=txt_(p.Referans,100);
 assert_(!all.some(x=>x.DekontID!==d.DekontID&&x.Durum==='ONAYLANDI'&&(x.DosyaHash===d.DosyaHash||(txn&&String(x.OkunanIslemNo)===txn)||(ref&&String(x.OkunanReferans)===ref))),'Bu dosya / işlem / referans daha önce onaylandı.');
 const alloc=allocate_(rows_('Aidatlar').filter(a=>a.DaireID===d.DaireID),value),payId='O-'+d.DekontID,makId='M-'+d.DekontID;
 const year=date.slice(0,4),prefix='ELM-'+year+'-',last=rows_('Makbuzlar').filter(r=>r.MakbuzNo.startsWith(prefix)).reduce((max,r)=>Math.max(max,Number(r.MakbuzNo.slice(prefix.length))),0),number=prefix+String(last+1).padStart(4,'0');
 const voucher={MakbuzID:makId,MakbuzNo:number,OdemeID:payId,DaireID:d.DaireID,Tarih:date,Tutar:value,Aciklama:txt_(p.Aciklama)||'Aidat tahsilatı',DosyaID:''};
 voucher.DosyaID=makeVoucher_(voucher,txn);
 const next=Object.assign({},d,{Durum:'ONAYLANDI',OnayTarihi:now_(),Onaylayan:u.Email,OkunanIslemNo:txn,OkunanReferans:ref});
 const payment={OdemeID:payId,DaireID:d.DaireID,AidatID:alloc.ids.join(','),Tarih:date,Tutar:value,DekontID:d.DekontID,Durum:'ONAYLANDI',MakbuzID:makId,OlusturmaTarihi:now_()};
 commit_('ODEME_ONAYI',alloc.updates.concat([{table:'Dekontlar',data:next},{table:'Odemeler',data:payment},{table:'Makbuzlar',data:voucher},{table:'KasaHareketleri',data:{HareketID:payId,Tarih:date,Tur:'GELIR',Kategori:'Aidat',Tutar:value,Aciklama:d.DaireID+' • '+voucher.Aciklama,ReferansID:payId}},logRecord_(u,'ODEME_ONAYLANDI',d.DekontID,d,{payment:payment,voucher:voucher})]));
 return {number:number};
}
function reject_(u,p){const d=rows_('Dekontlar').find(r=>r.DekontID===p.id);assert_(d&&d.Durum==='BEKLIYOR','Dekont bekleyen durumda değil.');assert_(['Yanlış tutar','Yanlış dekont','Yanlış IBAN','Okunamıyor','Mükerrer işlem','Diğer'].includes(p.Neden),'Red nedeni seçin.');const next=Object.assign({},d,{Durum:'REDDEDILDI',RedNedeni:p.Neden+(p.Aciklama?' • '+txt_(p.Aciklama):''),Onaylayan:u.Email,OnayTarihi:now_()});commit_('DEKONT_RED',[{table:'Dekontlar',data:next},logRecord_(u,'ODEME_REDDEDILDI',d.DekontID,d,next)]);return next;}
function saveMovement_(u,p){
 assert_(['GELIR','GIDER'].includes(p.Tur),'Tür seçin.');
 const validKategori=['Aidat','Elektrik','Su','Temizlik','Asansör','Tamirat','Bakım','Sigorta','Apartman ortak gideri','Diğer'];
 assert_(validKategori.includes(p.Kategori),'Kategori seçin.');
 assert_(p.Kategori!=='Aidat'||p.Tur==='GELIR','Aidat kategorisi yalnız gelir olarak eklenebilir.');
 const id='G-'+txt_(p.requestId,100);assert_(/^G-[a-zA-Z0-9-]{16,100}$/.test(id),'İşlem kimliği eksik.');if(rows_('GelirGider').some(r=>r.HareketID===id))return {already:true};
 const r={HareketID:id,Tarih:date_(p.Tarih),Tur:p.Tur,Kategori:p.Kategori,Tutar:amount_(p.Tutar),Aciklama:txt_(p.Aciklama),DosyaID:p.file?saveFile_(p.file,'Faturalar').id:'',Silindi:false};
 commit_('GELIR_GIDER',[{table:'GelirGider',data:r},{table:'KasaHareketleri',data:Object.assign({},r,{ReferansID:r.HareketID})},logRecord_(u,'GELIR_GIDER_EKLENDI',r.HareketID,null,r)]);return r;
}
function updateMovement_(u,p){
 const old=rows_('GelirGider').find(r=>r.HareketID===p.HareketID&&!active_(r.Silindi));assert_(old,'Hareket bulunamadı.');
 assert_(['GELIR','GIDER'].includes(p.Tur),'Tür seçin.');const validKategori=['Aidat','Elektrik','Su','Temizlik','Asansör','Tamirat','Bakım','Sigorta','Apartman ortak gideri','Diğer'];assert_(validKategori.includes(p.Kategori),'Kategori seçin.');assert_(p.Kategori!=='Aidat'||p.Tur==='GELIR','Aidat kategorisi yalnız gelir olarak kullanılabilir.');
 const next=Object.assign({},old,{Tarih:date_(p.Tarih),Tur:p.Tur,Kategori:p.Kategori,Tutar:amount_(p.Tutar),Aciklama:txt_(p.Aciklama)}),cash={HareketID:old.HareketID,Tarih:next.Tarih,Tur:next.Tur,Kategori:next.Kategori,Tutar:next.Tutar,Aciklama:next.Aciklama,ReferansID:old.HareketID};
 commit_('GELIR_GIDER_DUZELTME',[{table:'GelirGider',data:next},{table:'KasaHareketleri',data:cash},logRecord_(u,'GELIR_GIDER_DUZELTILDI',old.HareketID,old,next)]);return next;
}
function deleteMovement_(u,p){const r=rows_('GelirGider').find(x=>x.HareketID===p.id);assert_(r,'Hareket bulunamadı.');if(active_(r.Silindi))return {already:true};const next=Object.assign({},r,{Silindi:true});commit_('HAREKET_IPTAL',[{table:'GelirGider',data:next},{table:'KasaHareketleri',data:{HareketID:'IPTAL-'+r.HareketID,Tarih:today_(),Tur:r.Tur==='GELIR'?'GIDER':'GELIR',Kategori:r.Kategori,Tutar:r.Tutar,Aciklama:'İptal: '+r.Aciklama,ReferansID:r.HareketID}},logRecord_(u,'GIDER_GELIR_IPTAL',r.HareketID,r,next)]);return next;}
