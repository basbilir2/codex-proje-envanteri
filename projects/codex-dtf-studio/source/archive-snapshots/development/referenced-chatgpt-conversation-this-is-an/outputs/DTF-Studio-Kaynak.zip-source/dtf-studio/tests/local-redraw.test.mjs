import test from 'node:test';import assert from 'node:assert/strict';import sharp from 'sharp';
import {redrawPrompt,validateRedrawInput,redrawHealth,localRedrawConfig} from '../service/local-redraw.mjs';
test('redraw accepts a bounded photo and literal lettering, rejecting invalid or oversized inputs before launching a model',async()=>{
  const png=await sharp({create:{width:64,height:48,channels:3,background:'#172035'}}).png().toBuffer();
  assert.equal((await validateRedrawInput(png,'Mavi / EST.1991')).width,64);
  assert.ok(redrawPrompt('EST.1991 " & test').includes(JSON.stringify('EST.1991 " & test')));
  assert.throws(()=>redrawPrompt('x'.repeat(301)),/300/);
  await assert.rejects(validateRedrawInput(Buffer.from('not an image')),/3 MB/);
  await assert.rejects(validateRedrawInput(new Uint8Array(3*1024*1024+1)),/3 MB/);
});
test('missing local compute is reported honestly and cannot appear as a configured reconstruction engine',async()=>{
  const state=await redrawHealth(localRedrawConfig('C:/DTF-nonexistent-quality-fixture'));
  assert.equal(state.available,false);assert.equal(state.feePerCall,0);assert.equal(state.model,'FLUX.2-klein-4B-Q4_0');
});
