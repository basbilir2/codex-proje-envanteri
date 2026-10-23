from pathlib import Path
import subprocess,time,json,zipfile
root=Path(__file__).resolve().parent
runtime=root/'runtime-cpu'
runtime.mkdir(exist_ok=True)
with zipfile.ZipFile(root/'sd-win-cpu.zip') as z:
 for m in z.infolist():
  if not (runtime/m.filename).resolve().is_relative_to(runtime):raise RuntimeError('Unsafe archive path')
 z.extractall(runtime)
models=[root/'flux2-klein-4b-Q4_0.gguf',root/'qwen3-4b-Q4_K_M.gguf',root/'flux2-vae.safetensors']
print('Waiting for hash-verified model files.',flush=True)
start=time.time()
while not all(p.exists() for p in models):
 if time.time()-start>2400:raise TimeoutError('Model download did not finish')
 time.sleep(5)
exe=next(runtime.rglob('sd-cli.exe'))
source=root.parent/'latest-photo'/'crop.png';output=root/'mavi-redraw.png'
prompt='Recreate ONLY the printed artwork in the reference as crisp, clean, high-resolution print-ready graphic art. Preserve the exact handwritten word Mavi, its flowing letter shapes, the long sweeping underline, and the small text EST.1991. Navy blue letter interiors and bright white outlines, matching the reference design. Restore sharp edges and legible small text. Keep the complete design centered and fully visible with a modest empty margin. Uniform pure solid magenta background (#FF00FF), including every empty space between and inside the letters. The magenta is only a removable backdrop and must not appear inside the actual navy and white ink strokes. No shirt, no fabric, no person, no photograph texture, no mockup, no new words, no additional ornaments. This is a faithful graphic restoration of the existing print, not a new logo design.'
args=[str(exe),'--backend','cpu','--diffusion-model',str(models[0]),'--llm',str(models[1]),'--vae',str(models[2]),'--vae-format','flux2','-r',str(source),'-p',prompt,'--cfg-scale','1.0','--steps','4','--sampling-method','euler','--seed','42','--width','512','--height','336','--threads','8','--diffusion-fa','--vae-tiling','-o',str(output)]
(root/'mavi-request.json').write_text(json.dumps({'model':'FLUX.2-klein-4B-Q4_0','prompt':prompt,'reference':str(source),'output':str(output),'width':512,'height':336,'steps':4,'seed':42},indent=2),encoding='utf-8')
print('Starting genuine reference-image reconstruction on CPU.',flush=True);start=time.time()
with (root/'mavi-inference.log').open('w',encoding='utf-8') as log:
 result=subprocess.run(args,stdout=log,stderr=subprocess.STDOUT,creationflags=subprocess.CREATE_NO_WINDOW|subprocess.BELOW_NORMAL_PRIORITY_CLASS,timeout=2400)
metrics={'returncode':result.returncode,'seconds':round(time.time()-start,1),'exists':output.exists(),'output':str(output)}
(root/'mavi-inference.json').write_text(json.dumps(metrics,indent=2),encoding='utf-8');print(json.dumps(metrics),flush=True)
if result.returncode:
 print('\n'.join((root/'mavi-inference.log').read_text(encoding='utf-8',errors='replace').splitlines()[-12:]),flush=True)
