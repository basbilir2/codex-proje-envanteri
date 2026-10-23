import {createRequire} from 'node:module';
import {fileURLToPath} from 'node:url';
import {join} from 'node:path';
const root=fileURLToPath(new URL('..',import.meta.url));
const sharp=createRequire(join(root,'app/package.json'))('sharp');
const items=[['app/inputs/portrait-original.png','Orijinal'],['app/inputs/portrait-degraded.jpeg','Bozuk girdi'],['on-kontrol/gpu-portrait.png','Qwen · 40 adım'],['on-kontrol/gpu-portrait-fast.png','Qwen · 4 adım']];
const composite=[];
for(let i=0;i<items.length;i++){
  composite.push({input:await sharp(join(root,items[i][0])).resize(384,384,{fit:'contain'}).png().toBuffer(),left:i*384,top:40});
  const title=Buffer.from(`<svg width="384" height="40"><rect width="384" height="40" fill="white"/><text x="15" y="27" font-family="Arial" font-size="19">${items[i][1]}</text></svg>`);
  composite.push({input:title,left:i*384,top:0});
}
await sharp({create:{width:1536,height:424,channels:3,background:'white'}}).composite(composite).png().toFile(join(root,'on-kontrol/portre-karsilastirma.png'));
