// Build-only reuse of already-installed, pinned dependencies; runtime uses local bundle and weights.
import {createRequire} from 'node:module';
import {fileURLToPath} from 'node:url';
import {join} from 'node:path';
const source='C:/Users/USER/Documents/Codex/2026-10-17/referenced-chatgpt-conversation-this-is-an/outputs/dtf-studio';
const require=createRequire(source+'/package.json');
const {build}=require('esbuild');
const root=fileURLToPath(new URL('.',import.meta.url));
await build({stdin:{resolveDir:source,contents:`
import * as tf from '@tensorflow/tfjs';
import {setWasmPaths} from '@tensorflow/tfjs-backend-wasm';
import Upscaler from 'upscaler';
import model from '@upscalerjs/esrgan-slim/2x';
export async function createEngine(){
  let accelerated=false;
  try{accelerated=await tf.setBackend('webgl');}catch{}
  if(!accelerated){setWasmPaths('/vendor/');await tf.setBackend('wasm');}
  await tf.ready();
  return {tf,upscaler:new Upscaler({model:{...model,path:new URL('/vendor/esrgan-2x/model.json',location.origin).href}})};
}`},bundle:true,minify:true,format:'esm',platform:'browser',define:{'process.env.NODE_ENV':'"production"'},outfile:join(root,'vendor/neural-2x.mjs'),logLevel:'error'});
