/** Imports the apartment ledger JSON. Schema v1.1: Tur+AciklamaDiger on dues, SakinLinkToken on users. No contact info migration. */
function replaceRows_(name,records){
 const sh=db_().getSheetByName(name),h=SCHEMA_[name],last=Math.max(sh.getLastRow(),1);
 sh.getRange(1,1,1,h.length).setValues([h]);
 if(last>1)sh.getRange(2,1,last-1,h.length).clearContent();
 if(records.length)sh.getRange(2,1,records.length,h.length).setValues(records.map(r=>h.map(k=>cell_(r[k]))));
}
function periods_(start,end){const out=[];let y=Number(start.slice(0,4)),m=Number(start.slice(5));while(true){const p=y+'-'+String(m).padStart(2,'0');out.push(p);if(p===end)break;if(++m===13){m=1;y++;}}return out;}
function embeddedLedger_(){
 // Daireler 1-9; eski iletişim bilgisi taşınmıyor (Malik/Kiraci/Telefon/Email boş bırakılır)
 const through={'1':'','2':'2025-12','3':'2026-01','4':'2026-04','5':'2025-08','6':'2026-08','7':'2026-09','8':'2026-03','9':''},apartments={};
 Object.keys(through).forEach(no=>{
  const monthly_dues={},exempt=no==='1';
  periods_('2025-02','2026-09').forEach(period=>{
   const due=exempt?0:(period==='2025-02'?150:250),paid=!exempt&&through[no]&&period<=through[no]?due:0;
   monthly_dues[period]={due:due,paid:paid};
  });
  apartments[no]={monthly_dues_exempt:exempt,monthly_dues:monthly_dues,dues_total_paid:Object.values(monthly_dues).reduce((v,x)=>v+x.paid,0)};
 });
 return {schema_version:'1.0',building:{apartment_count:9},apartments:apartments,expenses:{recurring:[{period_start:'2025-02',period_end:'2025-12',monthly_amount:1150,certainty:'kesin',note:'2025 Şubat ayında aylık 1.150 TL ile başladı.'},{period_start:'2026-01',period_end:'2026-09',monthly_amount:1600,certainty:'kesin',note:'2026 Ocak ayından itibaren 1.600 TL.'},{period_start:'2025-02',period_end:'2026-09',monthly_amount_estimate:100,certainty:'tahmini',note:'Gerçek faturalar yok; aylık ortalama 100 TL.'}]}};
}
function importLedger_(u,p){
 let d;if(p.json){try{d=JSON.parse(String(p.json));}catch(e){throw new Error('JSON dosyası okunamadı.');}}else d=embeddedLedger_();
 assert_(d&&d.schema_version==='1.0'&&d.building&&d.apartments,'Apartman veri biçimi geçersiz.');
 assert_(Number(d.building.apartment_count)===9&&Object.keys(d.apartments).length===9,'Dosyada 9 daire bulunmalı.');
 const duePeriods=periods_('2025-02','2026-09'),now=now_(),oldApts=rows_('Daireler');let accrued=0,paid=0;
 // İletişim bilgisi taşınmıyor – yalnız DaireID/DaireNo/Aktif/AidatMuaf güncelleniyor
 const apartments=Object.keys(d.apartments).map(no=>{
  const source=d.apartments[no];
  return {DaireID:'D'+no,DaireNo:Number(no),Malik:'',Kiraci:'',Telefon:'',Email:'',Aktif:true,AidatMuaf:active_(source.monthly_dues_exempt)};
 });
 const importedDues=[];
 Object.keys(d.apartments).forEach(no=>duePeriods.forEach(period=>{
  const x=d.apartments[no].monthly_dues&&d.apartments[no].monthly_dues[period];
  assert_(x&&Number.isFinite(Number(x.due))&&Number.isFinite(Number(x.paid)),'Eksik aidat kaydı: Daire '+no+' '+period);
  const total=round_(x.due),amountPaid=round_(x.paid);
  assert_(amountPaid>=0&&amountPaid<=total,'Geçersiz aidat ödemesi: Daire '+no+' '+period);
  if(total===0)return;
  accrued=round_(accrued+total);paid=round_(paid+amountPaid);
  const remaining=round_(total-amountPaid);
  importedDues.push({AidatID:'A-D'+no+'-'+period,DaireID:'D'+no,Donem:period,Tutar:total,Odenen:amountPaid,Kalan:remaining,Durum:remaining===0?'ODENDI':amountPaid>0?'KISMI':'BORCLU',OlusturmaTarihi:now,Tur:'Aidat',AciklamaDiger:''});
 }));
 assert_(accrued===39200&&paid===23800&&round_(accrued-paid)===15400,'Aidat toplamları kaynak dosyayla uyuşmuyor.');
 const duesKeep=rows_('Aidatlar').filter(r=>!(duePeriods.includes(String(r.Donem))&&/^D(?:[1-9])$/.test(String(r.DaireID))));
 const paymentsKeep=rows_('Odemeler').filter(r=>!String(r.OdemeID).startsWith('IMP-HIST-'));
 const historicalPayments=Object.keys(d.apartments).filter(no=>Number(d.apartments[no].dues_total_paid)>0).map(no=>({OdemeID:'IMP-HIST-D'+no,DaireID:'D'+no,AidatID:importedDues.filter(a=>a.DaireID==='D'+no&&Number(a.Odenen)>0).map(a=>a.AidatID).join(','),Tarih:'',Tutar:Number(d.apartments[no].dues_total_paid),DekontID:'',Durum:'ONAYLANDI',MakbuzID:'',OlusturmaTarihi:now}));
 const movements=[];
 const add=(id,date,type,category,amount,note)=>movements.push({HareketID:'IMP-LEDGER-'+id,Tarih:date,Tur:type,Kategori:category,Tutar:round_(amount),Aciklama:note,DosyaID:'',Silindi:false});
 add('AIDAT-TAHSILAT','2026-09-13','GELIR','Aidat',paid,'Şubat 2025–Eylül 2026 tarihleri bilinmeyen aidat tahsilatlarının toplu aktarımı.');
 add('DEVIR-2025-04','2025-04-01','GELIR','Diğer',280,'Nisan 2025 devir bakiyesi; kaynakta gün belirtilmedi.');
 add('OZEL-ELEKTRIK-TAHSILAT','2025-03-01','GELIR','Elektrik',5000,'Daire 1–8 ortak elektrik tahsilatı; ay biliniyor, gün bilinmiyor.');
 add('CATI-TAHSILAT','2026-09-13','GELIR','Tamirat',65250,'Çatı için 9 daireden 7.250 TL tahsilat; gerçek tarih bilinmediğinden aktarım tarihi kullanıldı.');
 d.expenses.recurring.forEach(x=>periods_(x.period_start,x.period_end).forEach(period=>{
  const estimate=x.certainty==='tahmini',amount=Number(x.monthly_amount||x.monthly_amount_estimate);
  add((estimate?'ELEKTRIK':'TEMIZLIK')+'-'+period,period+'-01','GIDER',estimate?'Elektrik':'Temizlik',amount,(estimate?'Tahmini elektrik':'Temizlik')+' • '+period+'; ay bazlı kayıt, ödeme günü bilinmiyor. '+x.note);
 }));
 add('OZEL-ELEKTRIK-GIDER','2025-03-01','GIDER','Elektrik',5000,'Özel elektrik gideri; ay biliniyor, gün bilinmiyor. Daire 9 katılmadı.');
 add('ILACLAMA','2025-05-10','GIDER','Diğer',1000,'İlaçlama gideri.');
 add('CATI-GIDER','2026-09-13','GIDER','Tamirat',65000,'Çatı gideri; gerçek tarih bilinmediğinden aktarım tarihi kullanıldı.');
 assert_(movements.length===47,'Gider/kasa kayıt sayısı uyuşmuyor.');
 const moveKeep=rows_('GelirGider').filter(r=>!String(r.HareketID).startsWith('IMP-LEDGER-')),cashKeep=rows_('KasaHareketleri').filter(r=>!String(r.HareketID).startsWith('IMP-LEDGER-')),cashRows=movements.map(r=>({HareketID:r.HareketID,Tarih:r.Tarih,Tur:r.Tur,Kategori:r.Kategori,Tutar:r.Tutar,Aciklama:r.Aciklama,ReferansID:r.HareketID}));
 const net=movements.reduce((v,r)=>round_(v+(r.Tur==='GELIR'?r.Tutar:-r.Tutar)),0);assert_(net===-5720,'Kasa mutabakatı kaynakla uyuşmuyor.');
 const backup=backup_(u);
 replaceRows_('Daireler',apartments);replaceRows_('Aidatlar',duesKeep.concat(importedDues));replaceRows_('Odemeler',paymentsKeep.concat(historicalPayments));replaceRows_('GelirGider',moveKeep.concat(movements));replaceRows_('KasaHareketleri',cashKeep.concat(cashRows));
 put_('Ayarlar',{Anahtar:'AidatTutari',Deger:250});put_('Ayarlar',{Anahtar:'BaslangicTarihi',Deger:'2025-02-10'});
 log_(u,'DETAYLI_JSON_AKTARILDI','2025-02/2026-09',null,{daire:9,aidat:importedDues.length,odemeOzeti:historicalPayments.length,hareket:movements.length,borc:15400,kasa:net,yedek:backup.name});
 return {apartments:9,dues:importedDues.length,payments:historicalPayments.length,movements:movements.length,receivable:15400,cash:net,backup:backup.name};
}
