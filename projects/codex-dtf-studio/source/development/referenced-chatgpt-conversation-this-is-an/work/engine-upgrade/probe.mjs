import {pathToFileURL} from 'node:url';import {createRequire} from 'node:module';import path from 'node:path';import {writeFile} from 'node:fs/promises';
const root=process.cwd(),require=createRequire(path.join(root,'package.json')),sharp=require('sharp');
const {isolatePrint}=await import(pathToFileURL(path.join(root,'src/photo-extract.mjs')).href),{isolatePrint:old}=await import(pathToFileURL(path.resolve('../../work/engine-upgrade/photo-extract.mjs')).href);
const dir=path.resolve('../../work/engine-upgrade');
const raw=await sharp('../../work/latest-photo/enhanced-opaque.png').ensureAlpha().raw().toBuffer({resolveWithObject:true});const input={data:raw.data,width:raw.info.width,height:raw.info.height},region={x:0,y:0,width:input.width,height:input.height};
const before=old(input,region,28),after=isolatePrint(input,region,28);
await sharp(Buffer.from(after.data),{raw:{width:after.width,height:after.height,channels:4}}).png().toFile('../Mavi-Motor-Guncel-Seffaf.png');
const panel=async(image)=>sharp(Buffer.from(image.data),{raw:{width:image.width,height:image.height,channels:4}}).resize({width:650}).flatten({background:'#182238'}).png().toBuffer();
const b=await panel(before),a=await panel(after),height=(await sharp(a).metadata()).height;
await sharp({create:{width:1320,height:height+48,channels:3,background:'#f3f5f8'}}).composite([{input:b,left:0,top:48},{input:a,left:670,top:48},{input:Buffer.from('<svg width="1320" height="48"><text x="15" y="31" font-family="Arial" font-size="21">?nceki motor</text><text x="685" y="31" font-family="Arial" font-size="21">G?ncel motor ? ayn? kaynak, ayn? ayar</text></svg>'),left:0,top:0}]).png().toFile('../DTF-Motor-Karsilastirma.png');
const measure=im=>{let ink=0,soft=0;for(let p=3;p<im.data.length;p+=4){ink+=im.data[p]>20;soft+=im.data[p]>0&&im.data[p]<50;}return {ink,soft};};
const result={realMavi:{method:after.method,fabric:after.fabric,before:measure(before),after:measure(after)}};
// Known clean target under curved illumination: quantify cloth leakage, not visual opinion.
const width=160,height2=100,data=new Uint8ClampedArray(width*height2*4),truth=new Uint8Array(width*height2);
for(let y=0;y<height2;y++)for(let x=0;x<width;x++){const k=y*width+x,u=x/width-.5,v=y/height2-.5,ink=x>=38&&x<=120&&y>=25&&y<=72&&(x<42||x>116||y<29||y>68);truth[k]=ink?255:0;for(let c=0;c<3;c++)data[k*4+c]=ink?235:125-200*u*u-180*v*v+12*u-8*v+((x*17+y*13)%7-3)*.6+c*2;data[k*4+3]=255;}
const fixture={data,width,height:height2},r={x:0,y:0,width,height:height2};const oldTest=old(fixture,r,8,{contract:false}),newTest=isolatePrint(fixture,r,8,{contract:false});
const score=im=>{let leak=0,lost=0;for(let k=0;k<truth.length;k++){leak+=truth[k]===0&&im.data[k*4+3]>20;lost+=truth[k]>0&&im.data[k*4+3]<220;}return{clothPixels:leak,lostInk:lost};};result.curvedFabric={before:score(oldTest),after:score(newTest)};
await writeFile(path.join(dir,'metrics.json'),JSON.stringify(result,null,2));console.log(JSON.stringify(result));
