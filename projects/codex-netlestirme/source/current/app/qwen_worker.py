"""Same pinned Qwen artifacts on development GPU and local CPU. No network calls."""
import argparse, json, pathlib, subprocess, time, threading, re
ROOT = pathlib.Path(__file__).resolve().parent
PROMPTS = {'restore-image': ('Reconstruct a clean, high-quality version of this exact image using its visible content as the reference. '
          'Rebuild damaged contours and fine details coherently rather than merely increasing edge sharpness. Reduce blur, noise and compression artifacts. '
          'Preserve the entire original scene, subject identity, facial structure, expression, all existing text and letter shapes, '
          'objects, illustration style, colors, geometry, composition and background. Keep every existing element in its original position. '
          'Do not invent text, objects or decorations. Do not crop, change the viewpoint or replace the background. '
          'Produce a clean, sharp and faithful high-quality version of the same image.'),
          'extract-design': ('Extract and faithfully reconstruct the printed or applied artwork visible in this reference as a standalone, flat, front-facing design. '
          'Understand the artwork independently of the photographed surface. Remove the garment or supporting object, fabric weave, fibers, seams, folds, wrinkles, '
          'perspective distortion, cast shadows, lighting gradients and photographic glare. Rebuild clear, continuous artwork contours and details distorted by that surface. '
          'Preserve the actual artwork: its original words and letter shapes, illustrations, colors, solid fills, internal holes, line weights, layout and relative proportions. '
          'Do not invent or replace words, symbols, decorations or missing design elements. Do not turn solid artwork fills into holes. '
          'Output only the recovered artwork on a uniform light neutral gray display background so that white artwork contours remain visible, '
          'without a person, clothing, mockup, fabric texture, lighting gradient, shadow or distressed residue. '
          'Center and fit the complete recovered artwork on the output canvas with a small clear margin. '
          'Preserve the composition within the artwork, not its position within the original photograph. '
          'This is reconstruction of the existing artwork, not a sharpening filter or a new design.'),
          'repair-artwork': ('Recover this existing flat artwork, not a photograph of a garment. '
          'Reconstruct compression-damaged and blurred contours, continuous linework and solid fills. '
          'Preserve every word, numeral, letter shape, logo geometry, illustration, face identity, pattern, spacing, composition and artwork color. '
          'Do not relight the design, change its perspective, replace its background, invent missing text or add embellishments. '
          'Retain the exact layout and content bounds, including input padding. Output clean flat artwork, not a redesigned illustration.')}

def run(args):
    manifest = json.loads((ROOT / 'models.json').read_text(encoding='utf-8'))
    files = {f['role']:ROOT/'models'/f['name'] for f in manifest['files']}
    for path in [args.input, *files.values()]:
        if not pathlib.Path(path).is_file():
            raise FileNotFoundError(str(path))
    # Reuse the hash receipt only while size/mtime and pinned manifest still match.
    # Never re-hash ~19 GB on every inference or silently accept changed weights.
    for item in manifest['files'] + ([manifest['accelerator']] if args.lightning else []):
        path = ROOT / 'models' / item['name']
        receipt = path.with_suffix(path.suffix + '.verified.json')
        if not path.is_file() or not receipt.is_file():
            raise RuntimeError('Model doğrulama kaydı eksik; hazırlama adımı gerekli: ' + item['name'])
        info = json.loads(receipt.read_text(encoding='utf-8'))
        details = path.stat()
        if info.get('sha256') != item['sha256'] or info.get('size') != details.st_size or info.get('mtime_ns') != details.st_mtime_ns or details.st_size != item['size']:
            raise RuntimeError('Model dosyası doğrulama kaydından farklı; tekrar doğrulama gerekli: ' + item['name'])
    args.output.parent.mkdir(parents=True, exist_ok=True)
    pending = args.output.with_name(args.output.stem + '.pending.png')
    instruction=PROMPTS[args.task]
    if args.task=='extract-design':
        if not args.instruction_file:
            raise RuntimeError('Tasarima ozel gorsel analiz/talimat kaydi gerekli; genel prompt kullanilmadi.')
        plan=json.loads(args.instruction_file.read_text(encoding='utf-8'))
        if plan.get('schema')!=1 or not isinstance(plan.get('instruction'),str) or not 80<=len(plan['instruction'])<=24000:
            raise RuntimeError('Gecersiz tasarim talimati')
        instruction=plan['instruction']
    prompt=instruction
    cfg=2.5
    if args.lightning:
        accelerator=manifest['accelerator']
        if not (ROOT/'models'/accelerator['name']).is_file():
            raise FileNotFoundError('Doğrulanmış Lightning ağırlığı bulunamadı.')
        args.steps=accelerator['steps'];cfg=accelerator['cfg']
        prompt+=f" <lora:{pathlib.Path(accelerator['name']).stem}:1>"
    command = [str(args.exe), '--diffusion-model',str(files['diffusion']), '--llm',str(files['text']),
               '--llm_vision',str(files['vision']), '--vae',str(files['vae']), '-r',str(args.input), '-p',prompt,
               '--model-args','qwen_image_zero_cond_t=true','--cfg-scale',str(cfg),'--sampling-method','euler',
               '--flow-shift','3','--steps',str(args.steps),'--seed','42','--width',str(args.width),
               '--height',str(args.height),'--threads','8','--diffusion-fa','--vae-tiling','-o',str(pending)]
    if args.cpu:
        command += ['--backend','cpu']
    elif args.bounded_vram:
        command += ['--backend','diffusion=Vulkan0,te=cpu,vae=cpu','--params-backend','cpu','--max-vram','1.2','--disable-prefetch']
    if args.lightning:
        command += ['--lora-model-dir',str(ROOT/'models'),'--lora-apply-mode','at_runtime']
    start = time.monotonic()
    record = {'model':manifest['model'],'task':args.task,'runtime':manifest['runtime']['revision'],'weights':[{'role':f['role'],'sha256':f['sha256'],'revision':f['revision']} for f in manifest['files']],'parameters':{'steps':args.steps,'cfg':cfg,'seed':42,'width':args.width,'height':args.height},'prompt':instruction,'accelerator':manifest['accelerator'] if args.lightning else None,'status':'running'}
    report = args.output.with_suffix('.json')
    report.write_text(json.dumps(record,ensure_ascii=False,indent=2),encoding='utf-8')
    def progress(stage, **extra):
        print(json.dumps({'stage':stage,**extra},ensure_ascii=True),flush=True)
    progress('Model hazırlanıyor')
    try:
        with args.output.with_suffix('.log').open('w',encoding='utf-8') as log:
            child=subprocess.Popen(command,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,text=True,encoding='utf-8',errors='replace',bufsize=1,
                                   creationflags=subprocess.CREATE_NO_WINDOW if hasattr(subprocess,'CREATE_NO_WINDOW') else 0)
            expired=threading.Event()
            def stop():
                expired.set();child.kill()
            timer=threading.Timer(args.timeout,stop);timer.daemon=True;timer.start()
            sampling=False
            try:
                for line in child.stdout:
                    log.write(line);log.flush()
                    if 'get_learned_condition completed' in line: progress('Görsel ve talimat hazır')
                    if 'qwen_image build cached graph' in line: sampling=True;progress('Görsel yeniden oluşturuluyor',done=0,total=args.steps)
                    match=re.search(r'\|\s*(\d+)/(\d+)\s*-\s*[\d.]+s/it',line)
                    if sampling and match and int(match[2])==args.steps:
                        progress('Görsel yeniden oluşturuluyor',done=int(match[1]),total=args.steps)
                    if 'decoding' in line.lower(): sampling=False;progress('Çıktı hazırlanıyor')
                code=child.wait()
                if expired.is_set(): raise TimeoutError('AI süre sınırına ulaştı.')
                if code: raise RuntimeError('AI motoru tamamlanamadı; ayrıntı işlem günlüğünde.')
            finally:
                timer.cancel()
                if child.poll() is None: child.kill();child.wait()
        if not pending.is_file() or pending.stat().st_size < 100:
            raise RuntimeError('Motor görüntü üretmedi.')
        pending.replace(args.output)
        record['status']='completed'
        progress('Hazır',done=1,total=1)
    except Exception as error:
        record.update(status='failed',error=str(error))
        raise
    finally:
        record['seconds']=round(time.monotonic()-start,2)
        report.write_text(json.dumps(record,ensure_ascii=False,indent=2),encoding='utf-8')

if __name__ == '__main__':
    p=argparse.ArgumentParser()
    p.add_argument('--exe',type=pathlib.Path,required=True)
    p.add_argument('--input',type=pathlib.Path,required=True)
    p.add_argument('--output',type=pathlib.Path,required=True)
    p.add_argument('--width',type=int,required=True)
    p.add_argument('--height',type=int,required=True)
    p.add_argument('--steps',type=int,default=40)
    p.add_argument('--timeout',type=int,default=1800)
    p.add_argument('--cpu',action='store_true')
    p.add_argument('--lightning',action='store_true')
    p.add_argument('--bounded-vram',action='store_true')
    p.add_argument('--task',choices=tuple(PROMPTS),default='restore-image')
    p.add_argument('--instruction-file',type=pathlib.Path)
    args=p.parse_args()
    if min(args.width,args.height)<128 or args.width%16 or args.height%16 or args.width*args.height>1536*1536:
        p.error('Geçersiz çıktı boyutu.')
    run(args)
