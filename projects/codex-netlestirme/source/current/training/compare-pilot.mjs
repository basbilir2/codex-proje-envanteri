// Presentation only: unchanged result images fitted into labeled columns.
import {createRequire} from 'node:module';
import {readFile, mkdir} from 'node:fs/promises';
import {fileURLToPath} from 'node:url';
import {dirname, join} from 'node:path';
const root=dirname(fileURLToPath(import.meta.url));
const require=createRequire(new URL('../app/package.json',import.meta.url));
const sharp=require('sharp');
const folder=join(root,'pilot-20261022','validation-20261022');
const rows=[
  ['Mavi — eğitimde yok',join(root,'../outputs/mavi-karsilastirma-20261022/chatgpt-tasarim.png'),'mavi','ChatGPT referansı'],
  ['SOLAR — eğitimde yok',join(root,'pilot-20261022/images/07-clean.png'),'heldout07','Ayrılmış temiz hedef'],
];
const layers=[];
function label(text,left,top,width=600,height=40,size=20){
  const escaped=text.replaceAll('&','&amp;').replaceAll('<','&lt;');
  layers.push({input:Buffer.from(`<svg width="${width}" height="${height}"><rect width="100%" height="100%" fill="white"/><text x="12" y="28" font-family="Arial" font-size="${size}" fill="#17212b">${escaped}</text></svg>`),left,top});
}
label('Aynı model, talimat, seed ve 40 adım — yalnız LoRA değişiyor',0,0,1800,44,24);
for(let row=0;row<rows.length;row++){
  const [name,target,id,targetLabel]=rows[row],top=48+row*450;
  label(name,0,top,1800,40,23);
  const files=[target,join(folder,'evaluation',id+'-base.png'),join(folder,'evaluation',id+'-lora.png')];
  const titles=[targetLabel,'Eğitim öncesi','48 adım LoRA sonrası'];
  for(let col=0;col<3;col++){
    label(titles[col],col*600,top+40);
    let bytes;
    try { bytes=await readFile(files[col]); }
    catch(error) {
      if(error.code!=='ENOENT') throw error;
      label('Çıktı yerelde yok — doğrulanmadı',col*600+10,top+210,580,44,23);
      continue;
    }
    layers.push({input:await sharp(bytes).resize(580,350,{fit:'contain',background:'#e9e9e9'}).png().toBuffer(),left:col*600+10,top:top+80});
  }
}
label('Görüntüler yalnız karşılaştırma için ölçeklendirildi; rötuş veya metin düzeltmesi yok.',0,950,1800,40,20);
await mkdir(folder,{recursive:true});
await sharp({create:{width:1800,height:995,channels:3,background:'white'}}).composite(layers).png().toFile(join(folder,'comparison.png'));
console.log('Comparison saved.');
