function hash_(bytes){return Utilities.computeDigest(Utilities.DigestAlgorithm.SHA_256,bytes).map(b=>(b<0?b+256:b).toString(16).padStart(2,'0')).join('');}
function escapeHtml_(s){return String(s==null?'':s).replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));}
function folder_(path){const root=props_().getProperty('ROOT_FOLDER_ID')||CONFIG_ROOT_FOLDER_ID_;assert_(root&&root!=='REPLACE_ROOT_FOLDER_ID','Drive klasörü bağlantısı eksik.');let parent=DriveApp.getFolderById(root);path.split('/').filter(Boolean).forEach(n=>{const it=parent.getFoldersByName(n);parent=it.hasNext()?it.next():parent.createFolder(n);});return parent;}
function fileBlob_(f){
 assert_(f&&typeof f.data==='string'&&f.data.length<=7000000,'Dosya en fazla 5 MB olabilir.');assert_(['application/pdf','image/jpeg','image/png'].includes(f.type),'Yalnız PDF, JPG ve PNG yükleyin.');
 const bytes=Utilities.base64Decode(f.data);assert_(bytes.length<=5*1024*1024&&bytes.length>8,'Dosya boyutu geçersiz.');const b=bytes.map(x=>x&255),valid=f.type==='application/pdf'?String.fromCharCode.apply(null,b.slice(0,5))==='%PDF-':f.type==='image/png'?b.slice(0,8).join(',')==='137,80,78,71,13,10,26,10':b[0]===255&&b[1]===216&&b[2]===255;assert_(valid,'Dosya içeriği seçilen formatla uyuşmuyor.');return Utilities.newBlob(bytes,f.type,txt_(f.name,150).replace(/[\\/]/g,'_'));
}
function saveFile_(f,path){const blob=fileBlob_(f),file=folder_(path).createFile(blob);return {id:file.getId(),hash:hash_(blob.getBytes()),blob:blob};}
function parseReceipt_(text){
 const s=String(text||''),get=re=>{const m=s.match(re);return m?m[1].trim():'';};
 const money=get(/(?:işlem\s*tutar[ıi]|gönderilen\s*tutar|tutar|amount)\s*[:\-]?\s*(?:TRY|TL|₺)?\s*([\d.]+(?:,\d{2})?)/i);
 let value='';if(money){value=Number(money.replace(/\./g,'').replace(',','.'));if(!Number.isFinite(value)||value<=0)value='';}
 const day=get(/(?:tarih|date)\s*[:\-]?\s*(\d{2}[./-]\d{2}[./-]\d{4}|\d{4}-\d{2}-\d{2})/i);let date='';if(day){const parts=day.split(/[./-]/);date=parts[0].length===4?day:parts[2]+'-'+parts[1]+'-'+parts[0];}
 return {OkunanTutar:value,OkunanIBAN:get(/(?:alıcı\s*(?:hesap\s*)?iban|alici\s*iban|alıcı\s*hesap\s*(?:no|numarası))\s*[:\-]?\s*(TR(?:\s*\d){24})/i).replace(/\s/g,''),OkunanTarih:date,OkunanSaat:get(/\b(\d{2}:\d{2}(?::\d{2})?)\b/),OkunanBanka:get(/\b(Ziraat Bankası|İş Bankası|Garanti BBVA|Akbank|Yapı Kredi|Halkbank|VakıfBank|QNB|DenizBank|TEB|Enpara)\b/i),OkunanAlici:get(/(?:alıcı\s*adı(?:\s*soyadı)?|alici\s*adi)\s*[:\-]\s*([^\n]+)/i),OkunanGonderen:get(/(?:gönderen(?:\s*adı\s*soyadı)?|gonderen)\s*[:\-]\s*([^\n]+)/i),OkunanIslemNo:get(/(?:işlem\s*(?:no|numarası)|islem\s*no)\s*[:\-]?\s*([\w-]+)/i),OkunanReferans:get(/(?:referans\s*(?:no|numarası))\s*[:\-]?\s*([\w-]+)/i),OkunanAciklama:get(/(?:açıklama|aciklama)\s*[:\-]\s*([^\n]+)/i)};
}
function uploadReceipt_(u,p){
 const apt=u.Rol==='SAKIN'?u.DaireID:p.DaireID;own_(u,apt);assert_(rows_('Daireler').some(r=>r.DaireID===apt&&active_(r.Aktif)),'Daire seçin.');
 const blob=fileBlob_(p.file),hash=hash_(blob.getBytes()),all=rows_('Dekontlar');assert_(!all.some(r=>r.DosyaHash===hash&&r.Durum!=='REDDEDILDI'),'Bu dosya zaten yüklenmiş. Dekontlarınızı kontrol edin.');
 const stored=folder_('Dekontlar/'+today_().slice(0,4)+'/'+today_().slice(5,7)).createFile(blob);
 let text='',method='MANUEL',warning='';
 // Browser PDF.js extracts text locally. This is untrusted assistance, never payment evidence.
 if(p.file.type==='application/pdf'&&txt_(p.text,25000).replace(/\s/g,'').length>=20){text=txt_(p.text,25000);method='PDF_METIN';}
 else {let converted;try{converted=Drive.Files.create({name:'OCR-'+id_(),mimeType:'application/vnd.google-apps.document',parents:[folder_('Dekontlar').getId()]},blob,{ocrLanguage:'tr',fields:'id'});text=DocumentApp.openById(converted.id).getBody().getText();method='TEK_OCR';}catch(e){warning='Metin okunamadı. Yönetici asıl dosyayı kontrol ederek alanları doldurmalı.';}finally{if(converted)try{DriveApp.getFileById(converted.id).setTrashed(true);}catch(ignore){}}}
 const fields=parseReceipt_(text),duplicate=all.some(r=>r.Durum!=='REDDEDILDI'&&((fields.OkunanIslemNo&&r.OkunanIslemNo===fields.OkunanIslemNo)||(fields.OkunanReferans&&r.OkunanReferans===fields.OkunanReferans)||(fields.OkunanTutar&&fields.OkunanTarih&&Number(r.OkunanTutar)===fields.OkunanTutar&&r.OkunanTarih===fields.OkunanTarih)));
 if(duplicate)warning+=' Olası mükerrer: işlem/referans veya tarih ve tutar eşleşiyor.';
 const row=Object.assign({DekontID:id_(),DaireID:apt,DosyaURL:stored.getUrl(),DosyaID:stored.getId(),DosyaHash:hash,DosyaTipi:p.file.type,DosyaAdi:blob.getName(),BeyanTutar:amount_(p.Tutar),Durum:'BEKLIYOR',YuklemeTarihi:now_(),OkumaYontemi:method,Uyari:warning,BildirimDurumu:'BEKLIYOR'},fields);
 put_('Dekontlar',row);log_(u,'DEKONT_YUKLENDI',row.DekontID,null,{DaireID:apt});
 // Persisted before notification: channel outages cannot hide the receipt.
 notifyReceipt_(row.DekontID);return {id:row.DekontID};
}
function getFile_(u,p){
 let record,fileId;
 if(p.kind==='receipt'){record=rows_('Dekontlar').find(r=>r.DekontID===p.id);assert_(record,'Dosya bulunamadı.');own_(u,record.DaireID);fileId=record.DosyaID;}
 else if(p.kind==='voucher'){record=rows_('Makbuzlar').find(r=>r.MakbuzID===p.id);assert_(record,'Makbuz bulunamadı.');own_(u,record.DaireID);fileId=record.DosyaID;}
 else if(p.kind==='document'){record=rows_('Belgeler').find(r=>r.BelgeID===p.id);assert_(record&&(u.Rol==='YONETICI'||active_(record.SakinlereAcik)),'Belgeye erişiminiz yok.');fileId=record.DosyaID;}
 else if(p.kind==='movement'){admin_(u);record=rows_('GelirGider').find(r=>r.HareketID===p.id);assert_(record,'Hareket bulunamadı.');fileId=record.DosyaID;}
 else throw new Error('Dosya türü geçersiz.');
 assert_(fileId,'Bu kayıtta dosya yok.');const f=DriveApp.getFileById(fileId),b=f.getBlob();return {name:f.getName(),type:b.getContentType(),data:Utilities.base64Encode(b.getBytes())};
}
function makeVoucher_(r,txn){
 const name=settings_().ApartmanAdi,doc=DocumentApp.create(r.MakbuzNo),body=doc.getBody();
 try{body.appendParagraph(name.toUpperCase()).setHeading(DocumentApp.ParagraphHeading.HEADING1);body.appendParagraph('TAHSİLAT MAKBUZU').setHeading(DocumentApp.ParagraphHeading.HEADING2);body.appendTable([['Makbuz No',r.MakbuzNo],['Daire',r.DaireID.replace('D','')],['Ödeme',r.Aciklama],['Tutar',Number(r.Tutar).toFixed(2)+' TL'],['Tarih',r.Tarih],['Ödeme Yöntemi','Havale / EFT'],['İşlem No',txn||'Belirtilmedi']]);body.appendParagraph('Elmas Apartmanı yönetimi tarafından düzenlenmiştir.');doc.saveAndClose();return folder_('Makbuzlar/'+r.Tarih.slice(0,4)+'/'+r.Tarih.slice(5,7)).createFile(DriveApp.getFileById(doc.getId()).getAs(MimeType.PDF).setName(r.MakbuzNo+'.pdf')).getId();}finally{DriveApp.getFileById(doc.getId()).setTrashed(true);}
}
function saveDocument_(u,p){assert_(txt_(p.Baslik),'Belge başlığı girin.');const file=saveFile_(p.file,'Belgeler'),r={BelgeID:id_(),Baslik:txt_(p.Baslik,150),Kategori:txt_(p.Kategori,60),DosyaID:file.id,DosyaAdi:txt_(p.file.name,150),DosyaTipi:p.file.type,SakinlereAcik:active_(p.SakinlereAcik),Tarih:today_()};put_('Belgeler',r);log_(u,'BELGE_EKLENDI',r.BelgeID,null,r);return r;}
function backup_(u){const data={version:1,created:now_(),tables:{}};Object.keys(SCHEMA_).forEach(n=>data.tables[n]=rows_(n));const json=JSON.stringify(data,null,2),f=folder_('Yedekler').createFile('elmas-'+now_().replace(/:/g,'-')+'.json',json,MimeType.PLAIN_TEXT);log_(u,'YEDEK',f.getId(),null,{name:f.getName()});return {name:f.getName(),json:json,url:f.getUrl()};}
function pdfCall_(obj,method){try{if(obj&&typeof obj[method]==='function')return obj[method].apply(obj,[].slice.call(arguments,2));}catch(ignore){}return obj;}
function pdfTextStyle_(element,size,color,bold){try{const text=element.editAsText();if(size)text.setFontSize(size);if(color)text.setForegroundColor(color);text.setFontFamily('Arial');if(bold!==undefined)text.setBold(bold);}catch(ignore){}return element;}
function pdfMoney_(value){const p=Number(value||0).toFixed(2).split('.');return p[0].replace(/\B(?=(\d{3})+(?!\d))/g,'.')+','+p[1]+' TL';}
function pdfTableStyle_(table,headerColor){try{table.setBorderColor('#DDE5DE').setBorderWidth(1);const header=table.getRow(0);for(let i=0;i<header.getNumCells();i++){const cell=header.getCell(i);cell.setBackgroundColor(headerColor||'#17584B');pdfTextStyle_(cell,9,'#FFFFFF',true);}for(let r=1;r<table.getNumRows();r++){const row=table.getRow(r);for(let c=0;c<row.getNumCells();c++){const cell=row.getCell(c);if(r%2===0)cell.setBackgroundColor('#F4F7F2');pdfTextStyle_(cell,9,c===row.getNumCells()-1?'#17584B':'#243D36',c===row.getNumCells()-1);}}}catch(ignore){}return table;}
function makeDebtPDF_(u,daireID){
 const apt=rows_('Daireler').find(r=>r.DaireID===daireID);assert_(apt,'Daire bulunamadı.');
 const dues=rows_('Aidatlar').filter(r=>r.DaireID===daireID&&Number(r.Kalan)>0).sort((a,b)=>String(a.Donem).localeCompare(String(b.Donem)));
 const totalDebt=dues.reduce((v,r)=>v+Number(r.Kalan||0),0),s=settings_(),name=s.ApartmanAdi||'Elmas Apartmanı';
 const docName='Borc-Bildirimi-Daire-'+apt.DaireNo+'-'+today_(),doc=DocumentApp.create(docName),body=doc.getBody(),green='#17584B',ink='#243D36',muted='#6F7C75',light='#EEF4E8';
 try{
  pdfCall_(body,'setMarginTop',34);pdfCall_(body,'setMarginBottom',34);pdfCall_(body,'setMarginLeft',40);pdfCall_(body,'setMarginRight',40);
  const brand=body.appendTable([['◇  '+name.toUpperCase()],['BORÇ DURUM BİLDİRİMİ']]);
  try{brand.setBorderWidth(0);brand.getRow(0).getCell(0).setBackgroundColor(green);brand.getRow(1).getCell(0).setBackgroundColor('#123E35');pdfTextStyle_(brand.getRow(0).getCell(0),18,'#FFFFFF',true);pdfTextStyle_(brand.getRow(1).getCell(0),10,'#DDEBC1',true);}catch(ignore){}
  pdfCall_(body.appendParagraph(''),'setSpacingAfter',4);
  const greeting=body.appendParagraph('Değerli '+name+' sakini,');pdfTextStyle_(greeting,12,ink,true);pdfCall_(greeting,'setSpacingAfter',10);
  const intro=body.appendParagraph('Daire '+apt.DaireNo+' için güncel borç durumunuz aşağıda bilgilerinize sunulmuştur.');pdfTextStyle_(intro,10,muted,false);pdfCall_(intro,'setLineSpacing',1.25);pdfCall_(intro,'setSpacingAfter',14);
  const summary=body.appendTable([['DAİRE','GÜNCEL TOPLAM BORÇ'],['Daire '+apt.DaireNo,pdfMoney_(totalDebt)]]);
  try{summary.setBorderWidth(0);for(let c=0;c<2;c++){summary.getRow(0).getCell(c).setBackgroundColor(light);pdfTextStyle_(summary.getRow(0).getCell(c),9,green,true);summary.getRow(1).getCell(c).setBackgroundColor('#F8FAF6');pdfTextStyle_(summary.getRow(1).getCell(c),c===1?18:13,c===1?'#AB4444':ink,true);}}catch(ignore){}
  pdfCall_(body.appendParagraph(''),'setSpacingAfter',2);
  const detailTitle=body.appendParagraph('BORÇ KALEMLERİ');pdfTextStyle_(detailTitle,10,green,true);pdfCall_(detailTitle,'setSpacingBefore',8);pdfCall_(detailTitle,'setSpacingAfter',7);
  const tableData=[['DÖNEM','TÜR','BORÇ','ÖDENEN','KALAN']];
  dues.forEach(r=>tableData.push([String(r.Donem),r.Tur==='Diğer'&&r.AciklamaDiger?r.AciklamaDiger:(r.Tur||'Aidat'),pdfMoney_(r.Tutar),pdfMoney_(r.Odenen),pdfMoney_(r.Kalan)]));
  pdfTableStyle_(body.appendTable(tableData),green);
  pdfCall_(body.appendParagraph(''),'setSpacingAfter',2);
  const paymentTitle=body.appendParagraph('ÖDEME BİLGİLERİ');pdfTextStyle_(paymentTitle,10,green,true);pdfCall_(paymentTitle,'setSpacingBefore',8);pdfCall_(paymentTitle,'setSpacingAfter',7);
  const payment=body.appendTable([['IBAN',s.IBAN||'Henüz tanımlanmadı'],['Hesap sahibi',s.AliciAdi||name+' Yönetimi'],['Ödeme açıklaması','ELMAS DAİRE '+apt.DaireNo]]);
  try{payment.setBorderColor('#DDE5DE').setBorderWidth(1);for(let r=0;r<payment.getNumRows();r++){payment.getRow(r).getCell(0).setBackgroundColor(light);pdfTextStyle_(payment.getRow(r).getCell(0),9,green,true);pdfTextStyle_(payment.getRow(r).getCell(1),9,ink,r===0);}}catch(ignore){}
  const note=body.appendParagraph('Ödeme yaptıysanız dekontunuzu yönetim panelinden iletebilirsiniz. Kayıtlar yönetici onayından sonra güncellenir.');pdfTextStyle_(note,9,muted,false);pdfCall_(note,'setLineSpacing',1.2);pdfCall_(note,'setSpacingBefore',12);pdfCall_(note,'setSpacingAfter',14);
  const footer=body.appendParagraph('Belge tarihi: '+today_().split('-').reverse().join('.')+'   •   '+name+' Yönetimi');pdfTextStyle_(footer,8,muted,false);if(DocumentApp.HorizontalAlignment)pdfCall_(footer,'setAlignment',DocumentApp.HorizontalAlignment.CENTER);
  doc.saveAndClose();
  const pdfBlob=DriveApp.getFileById(doc.getId()).getAs(MimeType.PDF).setName(docName+'.pdf'),f=folder_('Raporlar/'+today_().slice(0,4)).createFile(pdfBlob);
  log_(u,'BORC_PDF_OLUSTURULDU',daireID,null,{file:f.getName(),debt:totalDebt});return {fileId:f.getId(),url:f.getUrl(),debt:totalDebt,name:f.getName(),type:MimeType.PDF,data:Utilities.base64Encode(pdfBlob.getBytes())};
 }finally{try{DriveApp.getFileById(doc.getId()).setTrashed(true);}catch(ignore){}}
}
