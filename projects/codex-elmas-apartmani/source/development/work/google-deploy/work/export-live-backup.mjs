import fs from 'node:fs';
import path from 'node:path';
const root=path.resolve(import.meta.dirname,'..'),auth=JSON.parse(fs.readFileSync(path.join(root,'.elmas-auth.json'),'utf8')).tokens.default;
const tokenResponse=await fetch('https://oauth2.googleapis.com/token',{method:'POST',headers:{'Content-Type':'application/x-www-form-urlencoded'},body:new URLSearchParams({client_id:auth.client_id,client_secret:auth.client_secret,refresh_token:auth.refresh_token,grant_type:'refresh_token'})});
if(!tokenResponse.ok)throw Error('Google erişim anahtarı yenilenemedi: '+tokenResponse.status);
const access=(await tokenResponse.json()).access_token,spreadsheetId='10V4oTIMWrR9AOsolDmF2586Uj0-mj8d_SFDj0qIOi8s';
const names=['Kullanicilar','Daireler','Aidatlar','Odemeler','Dekontlar','Makbuzlar','GelirGider','KasaHareketleri','Duyurular','Belgeler','Ayarlar','Loglar','Islemler'];
const qs=new URLSearchParams({valueRenderOption:'UNFORMATTED_VALUE',dateTimeRenderOption:'FORMATTED_STRING'});for(const name of names)qs.append('ranges',name);
const response=await fetch(`https://sheets.googleapis.com/v4/spreadsheets/${spreadsheetId}/values:batchGet?${qs}`,{headers:{Authorization:'Bearer '+access}});
if(!response.ok)throw Error('Google Sheets okunamadı: '+response.status+' '+await response.text());
const data=await response.json(),tables={};
for(let i=0;i<names.length;i++){const values=data.valueRanges[i]?.values||[],header=values[0]||[];tables[names[i]]=values.slice(1).filter(r=>r[0]!==undefined&&r[0]!=='').map(row=>Object.fromEntries(header.map((key,j)=>[key,row[j]??''])));}
const files=[],ids=new Set();for(const [table,key] of [['Dekontlar','DosyaID'],['Makbuzlar','DosyaID'],['Belgeler','DosyaID'],['GelirGider','DosyaID']])for(const row of tables[table]||[])if(row[key])ids.add(String(row[key]));
for(const id of ids){try{const metaResponse=await fetch(`https://www.googleapis.com/drive/v3/files/${encodeURIComponent(id)}?fields=id,name,mimeType`,{headers:{Authorization:'Bearer '+access}});if(!metaResponse.ok)continue;const meta=await metaResponse.json(),fileResponse=await fetch(`https://www.googleapis.com/drive/v3/files/${encodeURIComponent(id)}?alt=media`,{headers:{Authorization:'Bearer '+access}});if(!fileResponse.ok)continue;files.push({id,name:meta.name||id,type:meta.mimeType||'application/octet-stream',data:Buffer.from(await fileResponse.arrayBuffer()).toString('base64')});}catch{}}
const out={version:1,created:new Date().toISOString(),tables,files};
const apartments=tables.Daireler.length,debt=tables.Aidatlar.reduce((v,x)=>v+Number(x.Kalan||0),0),cash=tables.KasaHareketleri.reduce((v,x)=>v+(x.Tur==='GELIR'?1:-1)*Number(x.Tutar||0),0);
if(apartments!==9||Math.round(debt*100)/100!==15400||Math.round(cash*100)/100!==-5720)throw Error(`Canlı veri mutabakatı başarısız: daire=${apartments} borç=${debt} kasa=${cash}`);
const target=process.argv[2];if(!target)throw Error('Çıktı yolu eksik.');fs.writeFileSync(target,JSON.stringify(out));console.log(JSON.stringify({apartments,debt,cash,files:files.length,output:target}));
