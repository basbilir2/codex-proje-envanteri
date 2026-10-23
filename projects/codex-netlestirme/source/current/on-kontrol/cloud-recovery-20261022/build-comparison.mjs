import {createRequire} from 'node:module';
import {fileURLToPath} from 'node:url';
const require=createRequire(new URL('../../app/package.json',import.meta.url)),sharp=require('sharp');
const local=name=>fileURLToPath(new URL(name,import.meta.url));
const parts=[];
const titles=['ONAYLADIĞIN REFERANS','BULUTTA YENİ QWEN ÇIKTISI'];
for(let i=0;i<2;i++){
  const path=i?local('result.png'):local('../../outputs/mavi-karsilastirma-20261022/chatgpt-tasarim.png');
  const image=i?sharp(path).extract({left:200,top:120,width:640,height:380}):sharp(path).extract({left:270,top:140,width:1250,height:650});
  parts.push({input:await image.resize(670,350,{fit:'contain',background:'#e5e7eb'}).png().toBuffer(),left:i*700+15,top:65});
  parts.push({input:Buffer.from(`<svg width="700" height="65"><rect width="700" height="65" fill="white"/><text x="18" y="38" font-family="Arial" font-size="23" font-weight="bold">${titles[i]}</text></svg>`),left:i*700,top:0});
}
parts.push({input:Buffer.from('<svg width="1400" height="235"><rect width="1400" height="235" fill="white"/><text x="20" y="30" font-family="Arial" font-size="20">GEÇMEDİ: tasarım ayrıldı; lacivert dolgular kayboldu, EST.1991 yazısı yok.</text><text x="20" y="63" font-family="Arial" font-size="17">Karşılaştırma için yalnız görüntüleme alanları kırpılıp ölçeklendi; model çıktısına rötuş uygulanmadı.</text><text x="20" y="110" font-family="Arial" font-size="18">A40 · 1024×640 · 40 adım · 235,19 saniye</text><text x="20" y="144" font-family="Arial" font-size="18">Görünen bakiye farkı: 0,08 USD · Son bakiye: 10,26 USD</text><text x="20" y="178" font-family="Arial" font-size="18">Gerçek çıkarım yapıldı; model eğitimi henüz yapılmadı.</text><text x="850" y="85" font-family="Arial" font-size="15">RunPod: GPU kapatma kanıtı (ekran kırpımı)</text></svg>'),left:0,top:415});
parts.push({input:await sharp(local('gpu-stopped.png')).extract({left:948,top:570,width:560,height:150}).resize(545,146).png().toBuffer(),left:850,top:504});
await sharp({create:{width:1400,height:650,channels:3,background:'#e5e7eb'}}).composite(parts).png().toFile(local('comparison.png'));
