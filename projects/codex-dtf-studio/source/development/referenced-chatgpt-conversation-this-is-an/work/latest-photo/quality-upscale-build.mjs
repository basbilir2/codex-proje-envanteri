import {createRequire} from 'node:module';
import {fileURLToPath} from 'node:url';
const require=createRequire(new URL('./package.json',import.meta.url));
const {build}=require('esbuild');
const entry=`import * as tf from '@tensorflow/tfjs';import Upscaler from 'upscaler';import model from '@upscalerjs/esrgan-slim/2x';import sharp from 'sharp';import {readFile,writeFile} from 'node:fs/promises';import path from 'node:path';
const root=${JSON.stringify(process.cwd())},prefix='/@upscalerjs/esrgan-slim@1.0.0/',fetchOriginal=globalThis.fetch;
globalThis.fetch=async(url,options)=>{const text=String(url),at=text.indexOf(prefix);if(at<0)return fetchOriginal(url,options);const buffer=await readFile(path.join(root,'node_modules/@upscalerjs/esrgan-slim',text.slice(at+prefix.length).split('?')[0]));return new Response(buffer,{status:200});};
(async()=>{await tf.setBackend('cpu');await tf.ready();const crop=await sharp('../../work/latest-photo/crop.png').removeAlpha().raw().toBuffer({resolveWithObject:true});const input=tf.tensor3d(new Uint8Array(crop.data),[crop.info.height,crop.info.width,3],'int32'),upscaler=new Upscaler({model}),start=Date.now();const output=await upscaler.upscale(input,{output:'tensor',patchSize:64,padding:8});const values=await output.data(),data=Buffer.from(Uint8Array.from(values,v=>Math.max(0,Math.min(255,Math.round(v)))));await sharp(data,{raw:{width:crop.info.width*2,height:crop.info.height*2,channels:3}}).png().toFile('../../work/latest-photo/enhanced-opaque.png');console.log(JSON.stringify({shape:output.shape,milliseconds:Date.now()-start}));input.dispose();output.dispose();await upscaler.dispose();})().catch(e=>{console.error(e);process.exitCode=1;});`;
await build({stdin:{contents:entry,resolveDir:process.cwd()},bundle:true,platform:'node',format:'cjs',external:['sharp'],outfile:'../../work/latest-photo/upscale.cjs',logLevel:'error'});

