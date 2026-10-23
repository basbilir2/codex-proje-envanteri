import {createRequire} from 'node:module';
import {writeFile} from 'node:fs/promises';
import {detectPrint,isolatePrint} from '../outputs/dtf-studio/src/photo-extract.mjs';
const require=createRequire(new URL('../outputs/dtf-studio/package.json',import.meta.url)),sharp=require('sharp');
const path='C:/Users/USER/Downloads/WhatsApp Image 2026-10-05 at 09.47.53.jpeg';
const small=await sharp(path).resize({width:400,height:800,fit:'inside'}).ensureAlpha().raw().toBuffer({resolveWithObject:true});
const detection=detectPrint({data:small.data,width:small.info.width,height:small.info.height});
const full=await sharp(path).ensureAlpha().raw().toBuffer({resolveWithObject:true});
console.log(JSON.stringify(detection));
if(detection.region){const sx=full.info.width/small.info.width,sy=full.info.height/small.info.height,r=detection.region,region={x:r.x*sx,y:r.y*sy,width:r.width*sx,height:r.height*sy};const extracted=isolatePrint({data:full.data,width:full.info.width,height:full.info.height},region);await sharp(Buffer.from(extracted.data),{raw:{width:extracted.width,height:extracted.height,channels:4}}).png().toFile('outputs/MAVI-Fotograftan-Ayrilan.png');console.log(JSON.stringify({region,coverage:extracted.coverage,bounds:extracted.bounds}));await writeFile('work/photo-qa.json',JSON.stringify({detection,region,coverage:extracted.coverage,bounds:extracted.bounds},null,2));}
