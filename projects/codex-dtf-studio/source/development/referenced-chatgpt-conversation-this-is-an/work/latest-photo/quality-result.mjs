import sharp from 'sharp';import {writeFile} from 'node:fs/promises';import {isolatePrint} from './src/photo-extract.mjs';
const image=await sharp('../../work/latest-photo/enhanced-opaque.png').ensureAlpha().raw().toBuffer({resolveWithObject:true});
const result=isolatePrint({data:image.data,width:image.info.width,height:image.info.height},{x:0,y:0,width:image.info.width,height:image.info.height},28,{contract:true});
await sharp(Buffer.from(result.data),{raw:{width:result.width,height:result.height,channels:4}}).png().toFile('../../work/latest-photo/new-full.png');
const b=result.bounds;await sharp('../../work/latest-photo/new-full.png').extract({left:b.x-3,top:b.y-3,width:b.width+6,height:b.height+6}).png().toFile('../Mavi-19-Ekim-Seffaf.png');
await sharp('../Mavi-19-Ekim-Seffaf.png').resize({width:1000}).flatten({background:'#10182a'}).png().toFile('../../work/latest-photo/check-dark.png');
await sharp('../Mavi-19-Ekim-Seffaf.png').resize({width:1000}).flatten({background:'#ffffff'}).png().toFile('../../work/latest-photo/check-white.png');
console.log(JSON.stringify({method:result.method,bounds:b,coverage:result.coverage}));
