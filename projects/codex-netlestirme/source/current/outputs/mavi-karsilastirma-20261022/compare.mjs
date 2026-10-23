import {createRequire} from 'node:module';
import {readFile,writeFile} from 'node:fs/promises';
import {fileURLToPath} from 'node:url';
const require=createRequire(new URL('../../app/package.json',import.meta.url)),sharp=require('sharp');
const root=new URL('./',import.meta.url);
const source='C:/Users/USER/Downloads/WhatsApp Image 2026-10-19 at 13.34.07.jpeg';
const panels=[
  {path:source,title:'KAYNAK',sub:'Fotoğraftaki tasarım alanı',crop:{left:145,top:495,width:390,height:240}},
  {path:new URL('yazilim-mevcut-sonuc.png',root),title:'YAZILIMIN KAYITLI SONUCU',sub:'Eski fotoğraf restorasyonu · tasarım çıkarılmamış',normalized:true},
  {path:new URL('chatgpt-tasarim.png',root),title:'CHATGPT İLE YENİDEN OLUŞTURMA',sub:'Ayrı tasarım önizlemesi · birebir sadakat kabulü yok',crop:{left:270,top:140,width:1250,height:650}}
];
const W=650,H=530,layers=[];
for(let i=0;i<panels.length;i++){
  const item=panels[i],path=item.path instanceof URL?await readFile(item.path):item.path,meta=await sharp(path).metadata();
  let crop=item.crop;
  if(item.normalized)crop={left:Math.round(145/738*meta.width),top:Math.round(495/1600*meta.height),width:Math.round(390/738*meta.width),height:Math.round(240/1600*meta.height)};
  const input=await sharp(path).extract(crop).resize(W-30,360,{fit:'contain',background:'#e4e7eb'}).png().toBuffer();
  layers.push({input,left:i*W+15,top:90});
  const text=Buffer.from(`<svg width="${W}" height="90"><rect width="${W}" height="90" fill="#fff"/><text x="18" y="32" font-size="21" font-weight="bold" font-family="Arial">${item.title}</text><text x="18" y="59" font-size="15" font-family="Arial" fill="#475569">${item.sub}</text></svg>`);
  layers.push({input:text,left:i*W,top:0});
}
layers.push({input:Buffer.from(`<svg width="1950" height="80"><rect width="1950" height="80" fill="#fff"/><text x="18" y="30" font-size="17" font-family="Arial">Gösterim için alanlar kırpılıp boyutlandı; tasarım pikselleri elle düzeltilmedi. Yazılım yeniden çalıştırılmadı.</text><text x="18" y="58" font-size="17" font-family="Arial">Sağdaki gri zemin opaktır. Harf oranları, küçük tarih yazısı ve gerçek renkler için birebir sadakat doğrulanmadı.</text></svg>`),left:0,top:450});
await sharp({create:{width:W*3,height:H,channels:3,background:'#e4e7eb'}}).composite(layers).png().toFile(fileURLToPath(new URL('karsilastirma.png',root)));
for(const name of ['chatgpt-tasarim.png','seffaf-deneme-onaysiz.png','yazilim-mevcut-sonuc.png']){
  const bytes=await readFile(new URL(name,root)),m=await sharp(bytes).metadata(),s=await sharp(bytes).stats();
  console.log(JSON.stringify({name,width:m.width,height:m.height,alpha:m.hasAlpha===true,containsTransparency:m.hasAlpha===true&&!s.isOpaque}));
}
