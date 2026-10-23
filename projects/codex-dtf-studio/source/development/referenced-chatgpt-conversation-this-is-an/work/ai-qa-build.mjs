import {createRequire} from 'node:module';
import {fileURLToPath} from 'node:url';
const require=createRequire(new URL('../outputs/dtf-studio/package.json',import.meta.url));
const {build}=require('esbuild');
const project=fileURLToPath(new URL('../outputs/dtf-studio/',import.meta.url));
const entry=`
import * as tf from '@tensorflow/tfjs';
import Upscaler from 'upscaler';
import model from '@upscalerjs/esrgan-slim/2x';
import {readFile,writeFile} from 'node:fs/promises';
import path from 'node:path';
const prefix='/@upscalerjs/esrgan-slim@1.0.0/',base=${JSON.stringify(project)};
const fetchOriginal=globalThis.fetch;
globalThis.fetch=async(url,options)=>{const text=String(url),at=text.indexOf(prefix);if(at<0)return fetchOriginal(url,options);const relative=text.slice(at+prefix.length).split('?')[0],buffer=await readFile(path.join(base,'node_modules/@upscalerjs/esrgan-slim',relative));return new Response(buffer,{status:200,headers:{'Content-Type':relative.endsWith('.json')?'application/json':'application/octet-stream'}});};
(async()=>{await tf.setBackend('cpu');await tf.ready();const input=tf.tensor3d(Array.from({length:32*32*3},(_,i)=>(i*17+Math.floor(i/7)*41)%256),[32,32,3],'int32'),upscaler=new Upscaler({model}),start=Date.now();const result=await upscaler.upscale(input.clone(),{output:'tensor',patchSize:16,padding:4}),scaled=tf.image.resizeBilinear(input,[64,64]),error=await tf.mean(tf.abs(tf.sub(result,scaled))).data();if(result.shape.join(',')!=='64,64,3'||error[0]<.1)throw new Error('AI inference output failed');const report={shape:result.shape,meanDifferenceFromBilinear:error[0],milliseconds:Date.now()-start,model:'ESRGAN Slim 2x 1.0.0',backend:tf.getBackend()};await writeFile(${JSON.stringify(fileURLToPath(new URL('./ai-qa-result.json',import.meta.url)))},JSON.stringify(report,null,2));console.log(JSON.stringify(report));result.dispose();scaled.dispose();input.dispose();await upscaler.dispose();})().catch(e=>{console.error(e);process.exitCode=1;});
`;
await build({stdin:{contents:entry,resolveDir:project,sourcefile:'ai-qa.mjs'},bundle:true,platform:'node',format:'cjs',outfile:fileURLToPath(new URL('./ai-qa.cjs',import.meta.url)),logLevel:'error'});
