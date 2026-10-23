// Only copies original imagegen assets, records metadata and makes a review sheet.
// Does not render, distort, retouch or otherwise create training-image pixels.
import {createRequire} from 'node:module';
import {fileURLToPath} from 'node:url';
import {readFile,writeFile,mkdir,copyFile} from 'node:fs/promises';
import {join} from 'node:path';
import {createHash} from 'node:crypto';
const require=createRequire(new URL('../app/package.json',import.meta.url)),sharp=require('sharp');
const root=fileURLToPath(new URL('./',import.meta.url)),dest=join(root,'pilot-20261022');
const generated=join(process.env.USERPROFILE,'.codex','generated_images','01a1621a-e31d-7a01-a856-80dac96d6beb');
const assets=JSON.parse(await readFile(join(root,'pilot-assets.json'),'utf8'));
const instruction='Recover only the complete existing artwork from the photographed surface as clean flat print artwork on a light neutral gray display background. Remove fabric, folds, shadows, glare, perspective and photographic damage. Preserve every visible word, numeral, letter shape, thin line, solid colored fill, internal opening and artwork composition. Retain dark artwork interiors even when the supporting surface has a similar color. Center the complete recovered design with a clear margin. Do not omit small text, invent content or add decorations.';
const hashes=new Set(),records=[],layers=[];
await mkdir(join(dest,'images'),{recursive:true});
for(let i=0;i<assets.length;i++){
  const a=assets[i],record={...a,provenance:'built-in image_gen',visual_review:'screened for matching text, fill identity and main contours; not pixel-aligned ground truth',files:{}};
  for(const role of ['surface','clean']){
    const name=`${a.id}-${role}.png`,out=join(dest,'images',name),bytes=await readFile(join(generated,a[role]));
    const hash=createHash('sha256').update(bytes).digest('hex');
    if(hashes.has(hash))throw Error('Duplicate asset');hashes.add(hash);
    const m=await sharp(bytes).metadata();if(m.format!=='png'||!m.width||!m.height)throw Error('Invalid image');
    await copyFile(join(generated,a[role]),out);
    record.files[role]={path:'images/'+name,sha256:hash,width:m.width,height:m.height};
    // Presentation-only resizing; training metadata references the unmodified files.
    const x=(i%2)*768+(role==='clean'?384:0),y=Math.floor(i/2)*300;
    layers.push({input:Buffer.from(`<svg width="384" height="40"><rect width="384" height="40" fill="white"/><text x="10" y="26" font-family="Arial" font-size="17">${a.split.toUpperCase()} ${a.id} · ${role==='clean'?'TEMİZ HEDEF':'YÜZEYLİ KAYNAK'}</text></svg>`),left:x,top:y});
    layers.push({input:await sharp(bytes).resize(384,256,{fit:'contain',background:'#eee'}).png().toBuffer(),left:x,top:y+40});
  }
  records.push(record);
}
for(const split of ['train','validation']){
  const data=records.filter(a=>a.split===split).map(a=>({image:a.files.clean.path,edit_image:[a.files.surface.path],prompt:instruction}));
  await writeFile(join(dest,split+'.json'),JSON.stringify(data,null,2));
}
await writeFile(join(dest,'manifest.json'),JSON.stringify({schema:1,kind:'small synthetic paired-data pilot; not a general training corpus',training_count:6,validation_count:2,approved_mavi_reference_excluded:true,all_training_pixels_from:'built-in image_gen',pixel_modifications_by_packager:false,instruction,records},null,2));
await sharp({create:{width:1536,height:1200,channels:3,background:'white'}}).composite(layers).png().toFile(join(dest,'review.png'));
console.log(JSON.stringify({train:6,validation:2,unique_files:hashes.size,mavi_in_training:false,review:join(dest,'review.png')}));
